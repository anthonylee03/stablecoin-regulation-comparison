"""Compare peg groups and write the combined Step 4-b report."""

import argparse
from pathlib import Path
import runpy

import pandas as pd

shared = runpy.run_path(str(Path(__file__).with_name("03_concentration.py")))
ROOT = shared["ROOT"]
WINDOWS = shared["WINDOWS"]
number = shared["number"]
UNVERIFIED = shared["UNVERIFIED"]
plt = shared["plt"]
JURISDICTION_PEGS = {"EU": "EUR", "홍콩": "HKD", "한국": "KRW"}

PEG_EVIDENCE = {
    "A7A5": ("RUB", "PEG-01"), "DCHF": ("CHF", "PEG-02"),
    "FPI": ("VAR", "PEG-03"), "RAI": ("VAR", "PEG-04"), "HAI": ("VAR", "PEG-05"),
    "JPYSC": ("JPY", "PEG-06"), "JPYC": ("JPY", "PEG-07"), "BRLA": ("BRL", "PEG-08"),
    "ZCHF": ("CHF", "PEG-09"), "EURI": ("EUR", "PEG-10"), "EURE": ("EUR", "PEG-11"),
    "tGBP": ("GBP", "PEG-12"), "REUR": ("EUR", "PEG-13"), "EUROP": ("EUR", "PEG-14"),
    "EURR [239]": ("EUR", "PEG-15"), "EURR [436]": ("EUR", "PEG-16"),
    "HKDAP": ("HKD", "PEG-17"), "DDSC": ("AED", "PEG-18"), "XSGD": ("SGD", "PEG-19"),
    "WARS": ("ARS", "PEG-20"), "WBRL": ("BRL", "PEG-20"), "WCLP": ("CLP", "PEG-20"),
    "WCOP": ("COP", "PEG-20"), "WMXN": ("MXN", "PEG-20"), "WPEN": ("PEN", "PEG-20"),
    "AUDD": ("AUD", "PEG-21"), "CADD": ("CAD", "PEG-22"), "AUDF": ("AUD", "PEG-23"),
    "COPM": ("COP", "PEG-24"), "iTRY": ("TRY", "PEG-25"), "AUDM": ("AUD", "PEG-26"),
    "GYEN": ("JPY", "PEG-27"), "CADC": ("CAD", "PEG-28"), "PAR": ("EUR", "PEG-29"),
    "GBPA": ("GBP", "PEG-30"), "dEURO": ("EUR", "PEG-31"), "MXNT": ("MXN", "PEG-32"),
    "JPYdf": ("JPY", "PEG-33"), "XCHF": ("CHF", "PEG-34"), "EURAU": ("EUR", "PEG-35"),
    "MYRT": ("MYR", "PEG-36"), "KRWQ": ("KRW", "PEG-37"), "KRW1": ("KRW", "PEG-38"),
    "EURm": ("EUR", "PEG-39"), "BRLm": ("BRL", "PEG-39"), "PHPm": ("PHP", "PEG-39"),
    "JPYm": ("JPY", "PEG-39"), "CHFm": ("CHF", "PEG-39"), "KESm": ("KES", "PEG-39"),
    "GHSm": ("GHS", "PEG-39"), "COPm": ("COP", "PEG-39"),
    "EURC": ("EUR", "ISS-02"), "EURCV": ("EUR", "CASE-S12"),
    "EURS": ("EUR", "PEG-40"), "EURQ": ("EUR", "PEG-41"), "PHT": ("PHP", "PEG-42"),
    "BRL1": ("BRL", "PEG-43"), "VCHF": ("CHF", "PEG-44"), "VGBP": ("GBP", "PEG-44"),
    "XIDR": ("IDR", "PEG-45"),
}


def currency_labels(meta):
    return meta.peg_currency.mask(meta.peg_currency.eq(UNVERIFIED)
                                  & meta.api_peg_type.eq("peggedVAR"), "VAR")


def apply_peg_evidence(meta):
    sources = shared["load_sources"]()
    updated = meta.copy()
    for coin, (currency, source) in PEG_EVIDENCE.items():
        if coin not in updated.index:
            continue
        if sources.get(source, {}).get("tier") not in {"1", "2"}:
            raise ValueError(f"Peg lacks primary provenance: {coin}")
        updated.loc[coin, "peg_type"] = currency if currency in {"USD", "EUR"} else "OTHER"
        if currency != "VAR":
            updated.loc[coin, "peg_currency"] = currency
    return updated


def composition_section(daily, original, corrected, market):
    observed = daily.dropna(how="all").iloc[-1]
    original_labels = currency_labels(original)
    labels = currency_labels(corrected)
    nonusd = corrected.peg_type.ne("USD")
    selected = observed.loc[nonusd]
    before = peg_groups(daily, original).loc[observed.name, "nonusd"]
    after = market.loc[observed.name, "nonusd"]
    coverage = 100 * selected[selected.index.isin(PEG_EVIDENCE)].sum() / after
    for_display = selected.groupby(labels.loc[nonusd]).sum(min_count=1).sort_values(ascending=False)
    unavailable = selected.index.difference(PEG_EVIDENCE)
    lines = [
        "### 최신 비달러 시총 구성과 공식 페그 대조", "",
        f"{observed.name.date()} UTC 기준 공식 근거 확인 범위는 비달러 관측 시총의 {number(coverage)}%다. "
        f"공식 근거 미확인 {len(unavailable)}개는 DefiLlama 분류를 유지한다. "
        "VAR는 공급자 변동형 버킷이며, 아래 코인별 표에서 공식 확인 여부를 구분한다. "
        "[DATA-LLAMA-03, DATA-LLAMA-05]", "",
        "| 페그 유형 | 통화·분류 | 시총 (USD) | 비달러 대비 % |",
        "|---|---|---:|---:|",
    ]
    for currency, cap in for_display.items():
        group = "EUR" if currency == "EUR" else "OTHER"
        lines.append(f"| {group} | {currency} | {number(cap)} | {number(100 * cap / after)} |")
    lines += ["", f"페그 대조 후 최신 전체 비달러 시총 변화는 {number(after - before)} USD다.", ""]
    for coin in original_labels.index.intersection(PEG_EVIDENCE):
        currency, source = PEG_EVIDENCE[coin]
        old = original_labels.loc[coin]
        if old != currency:
            lines.append(f"- {coin}의 분류를 {old}에서 {currency}로 정정했다. "
                         f"최신 관측 시총 {number(observed.loc[coin])} USD, "
                         f"과거 일별 재분류 시총 최대 {number(daily[coin].max())} USD다. "
                         f"[{source}, DATA-LLAMA-03, DATA-LLAMA-05]")
    lines += ["- A7A5는 공식 문서와 카탈로그 모두 RUB 페그로 표시한다. [PEG-01, DATA-LLAMA-05]",
              "", "<details><summary>비달러 코인별 공식 페그 대조</summary>", "",
              "| 코인 | 원래 분류 | 적용 분류 | 최신 시총 USD | 공식 출처·확인 상태 |",
              "|---|---|---|---:|---|"]
    for coin, cap in selected.sort_values(ascending=False).items():
        evidence = PEG_EVIDENCE.get(coin, (None, "UNVERIFIED · 공식 근거 미확인"))[1]
        lines.append(f"| {coin} | {original_labels.loc[coin]} | {labels.loc[coin]} | "
                     f"{number(cap)} | {evidence} |")
    return "\n".join(lines + ["", "</details>", ""])


def peg_groups(daily, meta):
    by_type = daily.T.groupby(meta.peg_type).sum(min_count=1).T
    by_currency = daily.T.groupby(meta.peg_currency).sum(min_count=1).T
    total = daily.sum(axis=1, min_count=1)
    nonusd = by_type[["EUR", "OTHER"]].sum(axis=1, min_count=1)
    output = by_type.assign(nonusd=nonusd, nonusd_share=100 * nonusd.div(total.where(total > 0)))
    for currency in ("HKD", "KRW"):
        output[currency] = by_currency.reindex(columns=[currency])[currency]
    return output


def render_pegs(market, events):
    shared["font_setup"]()
    start = min(event[1] for event in events) - pd.DateOffset(months=6)
    finish = market.index.max()
    view = market.loc[start:]
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), layout="constrained")
    palette = {"USD": "#265483", "EUR": "#18766E", "OTHER": "#A25932",
               "HKD": "#9C6B22", "KRW": "#745198"}
    for key in ("USD", "EUR", "OTHER"):
        axes[0].plot(view.index, view[key] / 1e9, color=palette[key], label=key)
    axes[0].set_ylabel("관측 시총 (십억 USD)")
    axes[1].plot(view.index, view.nonusd_share, color="#9E4942", label="EUR 및 기타 페그")
    axes[1].set_ylabel("전체 대비 비달러 비중 (%)")
    for key in ("EUR", "HKD", "KRW"):
        axes[2].plot(view.index, view[key] / 1e6, color=palette[key], label=key)
    axes[2].set_ylabel("통화별 관측 시총 (백만 USD)")
    for ax in axes:
        shared["plot_events"](ax, events, start, finish)
        ax.legend(loc="best", ncols=3)
    fig.suptitle("페그 유형별 시총과 비달러 비중 | 코인 전체 체인 차트\n"
                 "수직선: 미국 적색 · EU 청록 · 홍콩 황토 · 한국 보라")
    fig.supxlabel("출처: DefiLlama DATA-LLAMA-03/05 · 이벤트 research/docs/scope.md")
    fig.savefig(ROOT / "assets" / "figures" / "nonusd_stablecoins.png", dpi=160)
    plt.close(fig)


def percent_change(before, after):
    return 100 * (after / before - 1) if before is not None and before > 0 else None


def nonusd_section(market, events):
    last = market.loc[market.nonusd_share.notna()].iloc[-1]
    lines = [
        "## 비달러 스테이블코인", "",
        "시총은 USD·EUR·OTHER 공급자 페그 그룹의 관측값을 합산했다. "
        "비달러는 EUR와 OTHER를 더했으며, OTHER에는 단일 통화 미확인 VAR도 포함된다. "
        "EUR·HKD·KRW는 카탈로그 기준 통화별 글로벌 관측값이다. "
        "코인 보유자 소재지나 규제 대상 범위는 이 통화 분류로 알 수 없다. [DATA-LLAMA-03, DATA-LLAMA-05]", "",
        "| 최신 날짜 UTC | USD (백만 USD) | EUR (백만 USD) | OTHER (백만 USD) | 비달러 (백만 USD) | 비달러 비중 % |",
        "|---|---:|---:|---:|---:|---:|",
        f"| {last.name.date()} | {number(last.USD / 1e6)} | {number(last.EUR / 1e6)} | "
        f"{number(last.OTHER / 1e6)} | {number(last.nonusd / 1e6)} | {number(last.nonusd_share)} |", "",
        "### 통화별 이벤트 전후 비교", "",
        "같은 기간 USD 페그 시총을 비교군으로 두어 전체 시장 움직임을 함께 본다. "
        "USD 구성에는 다국적 발행·유통과 규제 영향을 함께 받는 토큰이 있으며, "
        "두 시장이 같은 추세를 따르거나 비교군이 규제에 노출되지 않는다는 가정을 두지 않는다. "
        "성장률 차이는 통화군 변동률에서 USD 변동률을 뺀 기술적 비교값이다. [DATA-LLAMA-03, DATA-LLAMA-05]", "",
        "| 관할권 · 이벤트 | 페그 | 창 | 통화 시총 전→후 (백만 USD) | USD 비교군 전→후 (십억 USD) | 통화 변동 % | USD 변동 % | 차이 %p | 유효일 전/후 (통화 · USD) |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    sensitivity = []
    for jurisdiction, date, kind, label, source in events:
        currency = JURISDICTION_PEGS.get(jurisdiction)
        if currency is None:
            continue
        results = {}
        for width in WINDOWS:
            a, b, pre, post = shared["window_means"](market[currency], date, width)
            x, y, c_pre, c_post = shared["window_means"](market.USD, date, width)
            treated, control = percent_change(a, b), percent_change(x, y)
            difference = treated - control if treated is not None and control is not None else None
            results[width] = difference
            treated_pair = f"{number(a / 1e6)} → {number(b / 1e6)}" if a is not None else UNVERIFIED
            control_pair = f"{number(x / 1e9)} → {number(y / 1e9)}" if x is not None else UNVERIFIED
            lines.append(f"| {jurisdiction} {date.date()} {kind} ({source}) | {currency} | ±{width} | "
                         f"{treated_pair} | {control_pair} | {number(treated)} | {number(control)} | "
                         f"{number(difference)} | {pre}/{post} · {c_pre}/{c_post} |")
        if any(value is not None for value in results.values()):
            text = ", ".join(f"±{width}일 {number(results[width])}" for width in WINDOWS)
            available = [value for value in results.values() if value is not None]
            if len(available) == 1:
                direction = "한 창만 비교 가능해 창 민감도는 UNVERIFIED다."
            elif min(available) < 0 < max(available):
                direction = "비교 가능한 창 사이에서 차이의 부호가 바뀐다."
            else:
                direction = "비교 가능한 창 사이에서 차이의 부호는 바뀌지 않는다."
            sensitivity.append(f"- {jurisdiction} {label} 전후 {currency}와 USD의 변동률 차이는 "
                               f"{text}%p로 관찰된다. {direction} [{source}, DATA-LLAMA-03]")
    lines += ["", "### 관찰과 대안 해석", "", *sensitivity, "",
              "통화군과 비교군의 차이는 이벤트 시기와의 동행으로 해석한다. "
              "EUR·HKD·KRW에서 달러 환산 환율, 신규 발행 또는 상장, 초기 시장의 작은 잔액이 "
              "같은 방향의 변화와 시기적으로 일치할 수 있다. [DATA-LLAMA-03, DATA-LLAMA-05]", "",
              "유효일이 창 길이에 미달하면 비교값을 UNVERIFIED로 둔다. 전 구간 평균이 0이면 "
              "전·후 수준은 표시하고 변동률과 차이는 UNVERIFIED로 둔다. 한국 이벤트는 일반 "
              "가상자산 법령의 시점과 대조하는 참고 사례다. [KR-12, KR-03, DATA-LLAMA-03]", "",
              "[페그별 시계열 차트](../assets/figures/nonusd_stablecoins.png)", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render-figure", action="store_true", help="Regenerate the peg figure")
    args = parser.parse_args()
    daily, meta = shared["load_inputs"]()
    events = shared["load_events"]()
    corrected = apply_peg_evidence(meta)
    market = peg_groups(daily, corrected)
    if args.render_figure:
        render_pegs(market, events)
    header = (
        "# Step 4-b 시계열 관찰\n\n"
        "DefiLlama의 코인별 전체 체인 시총을 사용했다. 월별 관측치는 UTC 월의 "
        "마지막 유효일이다. 마지막 월은 관측 시점까지의 값이다. 이벤트는 "
        "[범위 문서](../research/docs/scope.md)의 출처가 연결된 제정·서명·발효·적용·시행·"
        "법정 경과 종료·인가 발효에서 가져왔다. 미래 시행 예정일은 표에 두고 "
        "관측 기간 밖의 수직선은 생략했다. 이벤트 당일은 전후 평균에서 제외했다. "
        "기본 창은 ±90일이며 ±60·180일을 함께 대조했다. 창의 모든 날짜에서 "
        "해당 지표의 값이 필요하다. 검정은 수행하지 않았다. "
        "[DATA-LLAMA-03, DATA-LLAMA-05]\n\n"
    )
    concentration = shared["concentration_section"](daily, meta, events)
    report = header + concentration + "\n" + nonusd_section(market, events) + "\n"
    report += composition_section(daily, meta, corrected, market)
    (ROOT / "analysis" / "results.md").write_text(
        report + "\n[식별 한계](limitations.md)\n", encoding="utf-8"
    )
    print("Wrote analysis/results.md")


if __name__ == "__main__":
    main()
