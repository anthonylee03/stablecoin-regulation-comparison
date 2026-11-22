"""Build daily USD circulation tables and print data-quality checks."""

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, DecimalException
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNVERIFIED = "UNVERIFIED"
# IDs and entities independently documented in the project's source ledger.
ISSUERS = {
    "2": ("usd-coin", "Circle", "CASE-S01"),
    "120": ("paypal-usd", "Paxos", "CASE-S03"),
    "254": ("societe-generale-forge-eurcv", "Société Générale–FORGE", "CASE-S12"),
}
FIAT_CODES = set(
    "AED ARS AUD BRL CAD CHF CLP CNY COP EUR GBP GHS HKD IDR JPY KES KRW "
    "MXN MYR NGN PEN PHP RUB SGD TRY UAH USD XOF ZAR".split()
)


def read_json(path):
    return json.loads(path.read_bytes(), parse_float=Decimal)


def day(value, cutoff):
    try:
        stamp = int(value)
        if not 0 < stamp < 10**11:
            return None
        observed = datetime.fromtimestamp(stamp, timezone.utc).date()
        return (observed, stamp) if observed <= cutoff else None
    except (ValueError, TypeError, OverflowError, OSError):
        return None


def number(value, *, price=False):
    if not isinstance(value, (int, Decimal)) or isinstance(value, bool):
        return None
    if not Decimal(value).is_finite() or value < 0 or (price and value == 0):
        return None
    return Decimal(value)


def amount(record, field, peg):
    values = record.get(field)
    return number(values.get(peg)) if isinstance(values, dict) else None


def normalize_series(records, extract, cutoff, quality):
    daily = {}
    for record in records:
        stamped = day(record.get("date"), cutoff)
        if stamped is None:
            quality["invalid_or_future_dates"] += 1
            continue
        observed, stamp = stamped
        value = extract(record)
        prior = daily.get(observed)
        if prior is None or stamp > prior[0]:
            daily[observed] = (stamp, {value})
        elif stamp == prior[0]:
            prior[1].add(value)
        if prior is not None:
            quality["duplicate_observations"] += 1
    clean = {}
    for observed, (_, values) in daily.items():
        if len(values) == 1:
            clean[observed] = next(iter(values))
        else:
            quality["conflicting_duplicate_days"] += 1
            clean[observed] = None
    return clean


def peg_metadata(peg):
    suffix = peg.removeprefix("pegged") if isinstance(peg, str) else ""
    currency = {"REAL": "BRL"}.get(suffix, suffix)
    if currency not in FIAT_CODES:
        return ("OTHER" if suffix == "VAR" else UNVERIFIED), UNVERIFIED
    return (currency if currency in {"USD", "EUR"} else "OTHER"), currency


def identify_issuer(asset, detail, sources):
    explicit = detail.get("issuer") or asset.get("issuer")
    if isinstance(explicit, str) and explicit.strip():
        return explicit, "DATA-LLAMA-02"
    verified = ISSUERS.get(str(asset["id"]))
    if verified and asset.get("gecko_id") == verified[0] and verified[2] in sources:
        return verified[1], verified[2]
    return UNVERIFIED, UNVERIFIED


def usd_on_chain(record, peg, prices, price_keys, cutoff):
    supplied = amount(record, "circulatingUSD", peg)
    if supplied is not None:
        return supplied
    quantity = amount(record, "circulating", peg)
    if quantity is None or quantity == 0:
        return quantity
    observed, _ = day(record.get("date"), cutoff)
    day_prices = prices.get(observed) or {}
    for key in price_keys:
        unit_price = number(day_prices.get(key), price=True)
        if unit_price is not None:
            try:
                return number(quantity * unit_price)
            except DecimalException:
                return None
    return None


def write_series(writer, values, coin, issuer, peg_type, chain, statistics):
    if not values:
        statistics["empty_series"] += 1
        return
    start, end = min(values), max(values)
    for offset in range((end - start).days + 1):
        observed = start + timedelta(days=offset)
        value = values.get(observed)
        statistics["rows"] += 1
        statistics["missing"] += value is None
        statistics["absent_days"] += observed not in values
        writer.writerow((observed.isoformat(), coin, issuer, peg_type, chain,
                         "" if value is None else str(value)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    parser.add_argument("--allow-partial", action="store_true")
    args = parser.parse_args()
    cutoff = args.snapshot_date
    raw = ROOT / "data" / "raw" / "defillama" / cutoff.isoformat()
    output = ROOT / "data" / "processed"
    output.mkdir(parents=True, exist_ok=True)
    manifest = read_json(raw / "manifest.json")
    if manifest["failures"] and not args.allow_partial:
        raise SystemExit("Raw collection incomplete. Retry collection or use --allow-partial.")
    assets = read_json(raw / "stablecoins.json")["peggedAssets"]
    with (ROOT / "sources" / "sources.csv").open(encoding="utf-8-sig", newline="") as stream:
        source_ids = {row["source_id"] for row in csv.DictReader(stream)}
    price_path = raw / "stablecoinprices.json"
    price_records = read_json(price_path) if price_path.is_file() else []
    prices = {}
    for record in price_records:
        stamped = day(record.get("date"), cutoff)
        if stamped and isinstance(record.get("prices"), dict):
            prices[stamped[0]] = record["prices"]

    labels = Counter(asset.get("symbol") for asset in assets)
    stats = {"ALL": Counter(), "chain": Counter()}
    quality = Counter()
    unverified = {"issuer": [], "peg_currency": []}
    empty_details = []
    empty_charts = []
    global_start = global_end = None
    last_values = {}
    names = {}
    csv_path = output / "stablecoin_circulation.csv"
    catalog_path = output / "stablecoin_catalog.csv"
    with csv_path.with_suffix(".tmp").open("w", newline="", encoding="utf-8-sig") as series_file, \
         catalog_path.with_suffix(".tmp").open("w", newline="", encoding="utf-8-sig") as catalog_file:
        writer, catalog = csv.writer(series_file), csv.writer(catalog_file)
        writer.writerow(("date", "coin", "issuer", "peg_type", "chain", "circulating_usd"))
        catalog.writerow(("coin_id", "coin", "name", "symbol", "issuer", "issuer_source_id",
                          "peg_type", "peg_currency", "api_peg_type", "peg_mechanism", "chains"))
        for asset in assets:
            id = str(asset["id"])
            symbol = asset.get("symbol")
            coin = symbol if symbol and labels[symbol] == 1 else f"{symbol or 'asset'} [{id}]"
            names[coin] = asset.get("name") or UNVERIFIED
            detail_path, chart_path = raw / f"stablecoin/{id}.json", raw / f"chart/{id}.json"
            detail = read_json(detail_path) if detail_path.is_file() else {}
            chart = read_json(chart_path) if chart_path.is_file() else []
            peg = asset.get("pegType")
            peg_type, currency = peg_metadata(peg)
            issuer, issuer_source = identify_issuer(asset, detail, source_ids)
            if issuer == UNVERIFIED:
                unverified["issuer"].append(coin)
            if currency == UNVERIFIED:
                unverified["peg_currency"].append(coin)
            balances = detail.get("chainBalances") or {}
            chains = sorted(set(asset.get("chains") or ()) | set(balances))
            catalog.writerow((id, coin, names[coin], symbol or UNVERIFIED, issuer,
                              issuer_source, peg_type, currency, peg or UNVERIFIED,
                              asset.get("pegMechanism") or UNVERIFIED, ";".join(chains)))
            totals = normalize_series(
                chart, lambda row: amount(row, "totalCirculatingUSD", peg), cutoff, quality
            )
            # If a chart is missing or empty, preserve detail observation dates as missing USD.
            if not totals:
                empty_charts.append(coin)
                totals = normalize_series(detail.get("tokens") or (), lambda row: None, cutoff, quality)
            write_series(writer, totals, coin, issuer, peg_type, "ALL", stats["ALL"])
            if totals:
                global_start = min(min(totals), global_start or min(totals))
                global_end = max(max(totals), global_end or max(totals))
                has_value = [observed for observed, value in totals.items() if value is not None]
                if has_value:
                    latest = max(has_value)
                    last_values[coin] = (latest, totals[latest])
            if not detail.get("tokens"):
                empty_details.append(coin)
            price_keys = [asset["gecko_id"]] if asset.get("gecko_id") else []
            for chain, balance in sorted(balances.items()):
                values = normalize_series(
                    balance.get("tokens") or (),
                    lambda row: usd_on_chain(row, peg, prices, price_keys, cutoff),
                    cutoff, quality,
                )
                write_series(writer, values, coin, issuer, peg_type, chain, stats["chain"])
    csv_path.with_suffix(".tmp").replace(csv_path)
    catalog_path.with_suffix(".tmp").replace(catalog_path)

    ranking = sorted(
        ((coin, value) for coin, (observed, value) in last_values.items() if observed == global_end),
        key=lambda item: (-item[1], item[0]),
    )
    stats["all_rows"] = stats["ALL"] + stats["chain"]
    summary = {
        "source_ids": [f"DATA-LLAMA-{index:02d}" for index in range(1, 6)],
        "snapshot_date": cutoff.isoformat(),
        "catalog_coins": len(assets),
        "detail_responses": manifest["detail_responses"],
        "chart_responses": manifest["chart_responses"],
        "global_date_range_utc": [str(global_start), str(global_end)],
        "ranking_date_utc": str(global_end),
        "ranking_eligible_coins": len(ranking),
        "top_10": [
            {"coin": coin, "name": names[coin], "circulating_usd": str(value)}
            for coin, value in ranking[:10]
        ],
        "missing_values": {
            group: {**count, "missing_pct": 100 * count["missing"] / count["rows"] if count["rows"] else None}
            for group, count in stats.items()
        },
        "quality": quality,
        "empty_details": empty_details,
        "empty_global_charts": empty_charts,
        "unverified": unverified,
    }
    summary_path = output / "stablecoin_collection_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "unverified"},
                     indent=2, ensure_ascii=True))
    print("UNVERIFIED:", {key: len(value) for key, value in unverified.items()})


if __name__ == "__main__":
    main()
