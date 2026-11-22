"""Download DefiLlama stablecoin JSON without reserializing responses."""

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://stablecoins.llama.fi"


def fetch(root, path, endpoint, expected_type):
    target = root / path
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".part")
    try:
        subprocess.run(
            [
                "curl", "--fail", "--silent", "--show-error", "--location",
                "--compressed", "--max-time", "50", "--retry", "3",
                "--retry-max-time", "120", "--output", str(temporary),
                BASE_URL + endpoint,
            ],
            check=True, capture_output=True, text=True,
        )
        with temporary.open("rb") as stream:
            payload = json.load(stream)
        if not isinstance(payload, expected_type):
            raise ValueError(f"unexpected JSON type for {endpoint}")
        temporary.replace(target)
        return target
    except subprocess.CalledProcessError as error:
        raise ValueError(error.stderr.strip()) from error
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-date", type=date.fromisoformat, required=True)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")

    root = ROOT / "data" / "raw" / "defillama" / args.snapshot_date.isoformat()
    catalog_path = fetch(root, "stablecoins.json", "/stablecoins?includePrices=true", dict)
    assets = json.loads(catalog_path.read_bytes())["peggedAssets"]
    ids = sorted({str(asset["id"]) for asset in assets}, key=int)
    if not ids or len(ids) != len(assets) or any(not id.isdecimal() for id in ids):
        raise ValueError("catalog contains missing, invalid or duplicate asset IDs")
    print(f"Catalog: {len(ids)} coins", flush=True)

    requests = [("stablecoinprices.json", "/stablecoinprices", list)]
    requests += [
        (f"stablecoin/{id}.json", f"/stablecoin/{id}", dict) for id in ids
    ]
    requests += [
        (f"chart/{id}.json", f"/stablecoincharts/all?stablecoin={id}", list)
        for id in ids
    ]
    failures = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(fetch, root, *request): request for request in requests
        }
        for count, future in enumerate(as_completed(futures), start=1):
            path, endpoint, _ = futures[future]
            try:
                future.result()
            except (ValueError, OSError) as error:
                failures[path] = {"endpoint": endpoint, "error": str(error)}
                print(f"Failed {endpoint}: {error}", flush=True)
            if count % 50 == 0 or count == len(requests):
                print(f"Checked {count}/{len(requests)} responses", flush=True)

    manifest = {
        "base_url": BASE_URL,
        "snapshot_date": args.snapshot_date.isoformat(),
        "collection_finished_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_coins": len(ids),
        "detail_responses": sum((root / f"stablecoin/{id}.json").is_file() for id in ids),
        "chart_responses": sum((root / f"chart/{id}.json").is_file() for id in ids),
        "failures": failures,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False), flush=True)
    if failures:
        raise SystemExit("Collection incomplete. Re-run to retry absent responses.")


if __name__ == "__main__":
    main()
