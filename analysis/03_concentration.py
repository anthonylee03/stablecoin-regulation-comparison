"""Compute concentration scenarios from DefiLlama ALL-chain observations."""

import csv
import os
from pathlib import Path
import re

import matplotlib
matplotlib.use("Agg")
from matplotlib import dates as mdates, font_manager, pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
WINDOWS = (60, 90, 180)
UNVERIFIED = "UNVERIFIED"
EVENT_TYPES = {"제정", "서명", "발효", "부분 적용", "일반 적용", "시행",
               "시행 예정", "법정 경과기간 종료", "인가 발효"}
COLORS = {"미국": "#9E4942", "EU": "#23758A", "홍콩": "#9C6B22", "한국": "#745198"}


def load_inputs():
    catalog = pd.read_csv(PROCESSED / "stablecoin_catalog.csv", dtype=str, keep_default_na=False)
    chunks = pd.read_csv(
        PROCESSED / "stablecoin_circulation.csv",
        usecols=["date", "coin", "chain", "circulating_usd"], chunksize=200_000,
    )
    data = pd.concat(chunk.loc[chunk.chain.eq("ALL")] for chunk in chunks)
    data["date"] = pd.to_datetime(data.date, format="%Y-%m-%d")
    daily = data.pivot(index="date", columns="coin", values="circulating_usd").sort_index()
    daily = daily.asfreq("D")
    meta = catalog.set_index("coin")
    if not meta.index.is_unique:
        raise ValueError("Duplicate coin in catalog")
    meta = meta.loc[daily.columns]
    if (daily < 0).any().any():
        raise ValueError("Unexpected negative USD observations")
    return daily, meta


def load_sources():
    with (ROOT / "sources" / "sources.csv").open(encoding="utf-8-sig", newline="") as file:
        return {row["source_id"]: row for row in csv.DictReader(file)}


def apply_issuer_map(daily, meta):
    mapping = pd.read_csv(ROOT / "data" / "issuer_map.csv", keep_default_na=False).set_index("coin")
    top = daily.dropna(how="all").iloc[-1].nlargest(15).index
    if not mapping.index.is_unique or set(mapping.index) != set(top):
        raise ValueError("Issuer map must match the latest top 15 coins")
    sources = load_sources()
    for row in mapping.itertuples():
        if row.issuer != UNVERIFIED and any(
            sources.get(source, {}).get("tier") not in {"1", "2"}
            for source in row.source_id.split(";")
        ):
            raise ValueError(f"Issuer lacks primary provenance: {row.Index}")
    updated = meta.copy()
    updated.loc[mapping.index, "issuer"] = mapping.issuer
    updated.loc[mapping.index, "issuer_source_id"] = mapping.source_id
    return updated


def load_events():
    sources = load_sources()
    scope = (ROOT / "docs" / "scope.md").read_text(encoding="utf-8")
    section = scope.split("## 규제 이벤트 날짜 후보", 1)[1].split("\n## ", 1)[0]
    events = []
    for line in section.splitlines():
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 5 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[1]):
            continue
        jurisdiction, date, kind, label, source = cells
        if kind not in EVENT_TYPES or not source:
            continue
        ids = source.split(", ")
        if any(s not in sources for s in ids):
            raise ValueError(f"Unregistered event: {date} {source}")
        if any(sources[s]["tier"] not in {"1", "2"} for s in ids):
            raise ValueError(f"Event lacks primary provenance: {date} {source}")
        events.append((jurisdiction, pd.Timestamp(date), kind, label, source))
    if not events:
        raise ValueError("No sourced events in scope.md")
    return sorted(events, key=lambda event: event[1])


def concentration(daily, meta):
    total = daily.sum(axis=1, min_count=1).replace(0, float("nan"))
    verified = meta.issuer.ne(UNVERIFIED)
    known = daily.loc[:, verified].T.groupby(meta.loc[verified, "issuer"]).sum(min_count=1).T
    unknown = daily.loc[:, ~verified]
    residual = unknown.sum(axis=1, min_count=1)
    separate = pd.concat([known, unknown.add_prefix("unknown:")], axis=1)
    shares = separate.div(total, axis=0)
    known_shares = known.div(total, axis=0)
    confirmed_total = known.sum(axis=1, min_count=1)
    largest = known.fillna(0).max(axis=1)
    upper = (known.fillna(0).pow(2).sum(axis=1) - largest.pow(2)
             + (largest + residual.fillna(0)).pow(2)).div(total.pow(2)) * 10_000
    metrics = pd.DataFrame({
        "proxy_hhi": shares.pow(2).sum(axis=1, min_count=1) * 10_000,
        "merged_hhi": upper,
        "proxy_top2": shares.apply(lambda row: row.nlargest(2).sum(min_count=1), axis=1) * 100,
        "proxy_top5": shares.apply(lambda row: row.nlargest(5).sum(min_count=1), axis=1) * 100,
        "known_coverage": confirmed_total.div(total) * 100,
    })
    return metrics, known_shares.mul(100).assign(UNVERIFIED=residual.div(total).mul(100))


def window_means(series, event, width):
    index = pd.date_range(event - pd.Timedelta(days=width), event + pd.Timedelta(days=width))
    before = series.reindex(index[:width])
    after = series.reindex(index[width + 1:])
    n_before = int(before.count())
    n_after = int(after.count())
    if min(n_before, n_after) < width:
        return None, None, n_before, n_after
    return float(before.mean()), float(after.mean()), n_before, n_after


def number(value, digits=2):
    return UNVERIFIED if pd.isna(value) else f"{value:,.{digits}f}"


def font_setup():
    path = Path(os.environ.get("STABLECOIN_KOREAN_FONT", "C:/Windows/Fonts/malgun.ttf"))
    if path.is_file():
        font_manager.fontManager.addfont(str(path))
        name = font_manager.FontProperties(fname=str(path)).get_name()
    else:
        available = {font.name for font in font_manager.fontManager.ttflist}
        name = next((name for name in ("Noto Sans CJK KR", "Apple SD Gothic Neo", "NanumGothic")
                     if name in available), None)
        if name is None:
            raise RuntimeError("Set STABLECOIN_KOREAN_FONT to a Korean font file.")
    plt.rcParams.update({"font.family": name, "axes.unicode_minus": False, "font.size": 10})


def plot_events(ax, events, start, finish):
    for jurisdiction, date, _, _, _ in events:
        if start <= date <= finish:
            ax.axvline(date, color=COLORS[jurisdiction], linewidth=1, alpha=.45, linestyle="--")
    ax.set_xlim(start, finish)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlabel("관측일 (UTC)")
    ax.grid(axis="y", alpha=.18)


def render_concentration(monthly, shares, events):
    font_setup()
    start = min(event[1] for event in events) - pd.DateOffset(months=6)
    finish = monthly.index.max()
    view = monthly.loc[start:]
    fig, axes = plt.subplots(3, 1, figsize=(12, 11), layout="constrained")
    axes[0].plot(view.index, view.proxy_hhi, label="미확인 코인별 분리", color="#267386")
    axes[0].plot(view.index, view.merged_hhi, label="미확인 잔액을 최대 확인 발행사에 합산", color="#972F43")
    axes[0].set_ylabel("HHI (0–10,000)")
    axes[1].plot(view.index, view.proxy_top2, label="상위 2그룹", color="#235E91")
    axes[1].plot(view.index, view.proxy_top5, label="상위 5그룹", color="#748A32")
    axes[1].set_ylabel("점유율 (%)")
    displayed = shares.drop(columns=UNVERIFIED).iloc[-1].nlargest(5).index.tolist()
    for issuer, values in shares.loc[start:, displayed + [UNVERIFIED]].items():
        axes[2].plot(values.index, values, label=issuer if issuer != UNVERIFIED else "미확인 발행사 잔액")
    axes[2].set_ylabel("시장 점유율 (%)")
    for ax in axes:
        plot_events(ax, events, start, finish)
        ax.legend(loc="best", ncols=2)
    fig.suptitle("월별 스테이블코인 발행사 집중도 시나리오 | 월 마지막 관측일\n"
                 f"{finish.date()} 발행사 확인 비율 {number(monthly.known_coverage.iloc[-1])}%\n"
                 "수직선: 미국 적색 · EU 청록 · 홍콩 황토 · 한국 보라")
    fig.supxlabel("출처: DefiLlama DATA-LLAMA-03 · data/issuer_map.csv · 이벤트 docs/scope.md")
    fig.savefig(ROOT / "figures" / "issuer_concentration.png", dpi=160)
    plt.close(fig)


def concentration_section(daily, meta, events, render=False):
    baseline, _ = concentration(daily, meta)
    metrics, shares = concentration(daily, apply_issuer_map(daily, meta))
    month_last = metrics.loc[metrics.proxy_hhi.notna()].groupby(metrics.loc[metrics.proxy_hhi.notna()].index.to_period("M")).tail(1)
    month_shares = shares.loc[month_last.index]
    if render:
        render_concentration(month_last, month_shares, events)
    latest = month_last.iloc[-1]
    as_of = str(latest.name.date())
    lines = [
        "## 시장 집중도", "",
        "전체 발행사 기준 HHI와 상위 2·5개 점유율은 UNVERIFIED다. "
        "공개 근거가 있는 발행사만 합치고 미확인 코인은 개별 그룹으로 둔 분리 시나리오와, "
        "미확인 잔액을 확인 그룹 중 가장 큰 발행사에 합친 합산 시나리오를 제시한다. "
        "점유율 분모는 그날의 관측 전체 시총이다. 수정 전은 Step 4-a 카탈로그의 발행사를 사용했다. "
        "수정 후는 [상위 코인 발행사 맵](../data/issuer_map.csv)을 적용했다. "
        "DAI와 USDS는 Sky Protocol로 합산했다. PYUSD와 USDG는 발행 법인 범위가 달라 개별 그룹으로 뒀다. "
        "맵의 확인값은 동일 코인의 과거 관측에도 적용했다. [DATA-LLAMA-03, CASE-S01, CASE-S03, CASE-S12, ISS-04, ISS-05, ISS-08, ISS-09, ISS-10]", "",
        "| 최근 월 관측일 UTC | 확인 발행사 커버리지 % | 분리 HHI | 합산 HHI | 분리 상위 2 % | 분리 상위 5 % |",
        "|---|---:|---:|---:|---:|---:|",
        f"| {as_of} | {number(latest.known_coverage)} | {number(latest.proxy_hhi)} | "
        f"{number(latest.merged_hhi)} | {number(latest.proxy_top2)} | {number(latest.proxy_top5)} |", "",
    ]
    fields = ["known_coverage", "proxy_hhi", "proxy_top2", "proxy_top5"]
    previous = baseline.loc[latest.name, fields]
    current = latest[fields]
    lines += [
        f"### {as_of} 수정 전후 비교", "",
        "| 매핑 | 발행사 확인 비율 % | 분리 HHI | 상위 2 % | 상위 5 % |",
        "|---|---:|---:|---:|---:|",
        "| 수정 전 | " + " | ".join(number(value) for value in previous) + " |",
        "| 수정 후 | " + " | ".join(number(value) for value in current) + " |",
        "| 차이 (%p / HHI 점) | " + " | ".join(f"{value:+,.2f}" for value in current - previous) + " |", "",
        "### 이벤트 창별 일평균 비교", "",
        "각 셀은 전→후이며, 분리 HHI와 분리 상위 2·5개 점유율을 함께 표시한다. "
        "비교군은 비달러 분석의 USD 페그 시장이다. 이 표의 시나리오 지수에는 독립적 발행사 대조군을 설정하지 않았다. [DATA-LLAMA-03]", "",
        "| 관할권 · 이벤트 | 창 | 분리 HHI | 합산 HHI | 상위 2 % | 상위 5 % | 유효일 전/후 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for jurisdiction, date, kind, _, source in events:
        for width in WINDOWS:
            values = [window_means(metrics[col], date, width)
                      for col in ("proxy_hhi", "merged_hhi", "proxy_top2", "proxy_top5")]
            pairs = [f"{number(a)} → {number(b)}" if a is not None else UNVERIFIED
                     for a, b, _, _ in values]
            _, _, n_pre, n_post = values[0]
            lines.append(f"| {jurisdiction} {date.date()} {kind} ({source}) | ±{width} | "
                         f"{' | '.join(pairs)} | {n_pre}/{n_post} |")
    for jurisdiction, date, kind, label, source in events:
        if jurisdiction == "미국" and kind == "제정":
            shifts = [window_means(metrics.proxy_hhi, date, width) for width in WINDOWS]
            if all(value[0] is not None for value in shifts):
                deltas = ", ".join(f"±{width}일 {after-before:+,.2f}"
                                   for width, (before, after, _, _) in zip(WINDOWS, shifts))
                changes = [after - before for before, after, _, _ in shifts]
                direction = ("창에 따라 증가·감소 방향이 달라진다." if min(changes) < 0 < max(changes)
                             else "비교 창을 바꿔도 증가·감소 방향은 바뀌지 않는다.")
                lines += ["", f"{label} 전후 분리 HHI의 변동 폭은 {deltas}점으로 관찰된다. "
                          f"{direction} "
                          "대형 토큰의 잔액 변화나 토큰 간 발행사 중복도 이 차이를 설명할 수 있다. "
                          f"[{source}, DATA-LLAMA-03]"]
    lines += ["", "<details><summary>월별 점유율 및 집중도 전체 표</summary>", "",
              "| 관측일 UTC | " + " | ".join(month_shares.columns) + " | 분리 HHI | 합산 HHI | 상위 2 % | 상위 5 % |",
              "|---|" + "---:|" * (len(month_shares.columns) + 4)]
    for observed, values in month_shares.iterrows():
        metrics_row = month_last.loc[observed]
        cells = [number(value) for value in values] + [
            number(metrics_row[col]) for col in ("proxy_hhi", "merged_hhi", "proxy_top2", "proxy_top5")]
        lines.append(f"| {observed.date()} | " + " | ".join(cells) + " |")
    lines += ["", "</details>", "", "[집중도 차트](../figures/issuer_concentration.png)", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    daily, meta = load_inputs()
    concentration_section(daily, meta, load_events(), render=True)
    print("Wrote figures/issuer_concentration.png")
