# DefiLlama 스테이블코인 데이터

확인일은 2026-11-22(서울 기준)다. 시계열 날짜는 API의 Unix 초를 UTC 일자로 변환했다. [출처 대장](../sources/sources.csv), [실행 순서](../analysis/README.md), [수집 기록](../data/raw/defillama/2026-11-22/manifest.json), [실행 통계](../data/processed/stablecoin_collection_summary.json).

## 원본과 엔드포인트

DefiLlama의 무료 API 문서에서 코인 목록, 코인 상세, 차트, 과거 가격 경로를 확인했다. 문서에 적힌 `api.llama.fi`의 해당 무료 경로는 직접 조회 시 HTTP 404를 반환했다. 응답 스키마와 수치는 무료 스테이블코인 전용 호스트 `https://stablecoins.llama.fi`에서 확인했다. [공식 무료 API 문서](https://github.com/DefiLlama/api-docs/blob/main/llms-free.txt#stablecoins)

| source_id | 경로 | 확인한 응답 필드 |
|---|---|---|
| DATA-LLAMA-05 | `/stablecoins?includePrices=true` | `peggedAssets[]`의 `id`, `name`, `symbol`, `pegType`, `pegMechanism`, `chains`, `gecko_id` 등 |
| DATA-LLAMA-02 | `/stablecoin/{id}` | 코인 전체 `tokens[]`와 체인별 `chainBalances[chain].tokens[]`. 시점별 `date`, `circulating`과 일부 발행·미유통·브리지 항목 |
| DATA-LLAMA-03 | `/stablecoincharts/all?stablecoin={id}` | `date`, 페그 코드별 `totalCirculating`, `totalCirculatingUSD` |
| DATA-LLAMA-04 | `/stablecoinprices` | `date`, 공급자 가격 키별 `prices` |

> source_quote (DATA-LLAMA-01): “Get historical mcap and historical chain distribution of a stablecoin”  
> 번역 — 스테이블코인의 과거 시가총액과 체인별 분포 이력을 조회한다.

JSON 본문은 HTTP 전송 압축이 있으면 해제한 뒤 재직렬화 없이 저장했다. 목록에 있는 ID를 그대로 수집 대상으로 삼았다. 목록이 제공하는 폐지·지원 중단 플래그는 원본에 유지했다.

## 정제 필드와 집계

- `stablecoin_circulation.csv`의 열은 `date, coin, issuer, peg_type, chain, circulating_usd`다. `coin`은 심볼이며, 목록에서 충돌하는 심볼에는 DefiLlama ID를 붙인다.
- `chain=ALL`은 코인별 차트의 `totalCirculatingUSD[pegType]`이며, 당시 유통량을 달러로 평가한 공급자 값이다. 순위는 가장 최근의 전체 관측일에 USD 값이 있는 코인의 `ALL` 행만 사용한다. 목록의 실시간 가격·수량과 갱신 시점이 다를 수 있다 (DATA-LLAMA-03, DATA-LLAMA-05).
- 개별 체인의 `circulating_usd`는 API의 USD 필드가 있으면 그대로 쓰고, 없으면 `circulating[pegType]`의 수량에 동일 UTC 일자 및 일치하는 `gecko_id`의 USD 가격을 곱한다. 원본 유통량은 별도로 보관한다. 유통량은 온체인 공급 지표이며 준비금, 예금, 누적 이전액과 구분한다 (DATA-LLAMA-02, DATA-LLAMA-04).
- `stablecoin_catalog.csv`에 API ID·이름·심볼·페그 코드·유형·기준 통화·형태·체인을 보존했다. `peggedUSD`는 `USD`, `peggedEUR`는 `EUR`, 다른 인식 가능한 페그는 `OTHER`로 표기한다. 기준 통화 열은 API 코드의 통화 접미사를 사용하며, 브라질 헤알에 쓰인 `peggedREAL`은 `BRL`로 표준화한다. `peggedVAR`는 `OTHER`에 넣고 단일 기준 통화는 `UNVERIFIED`로 둔다. 미인식 코드는 추정하지 않는다 (DATA-LLAMA-05).
- API에 구조화된 발행사명이 있으면 사용한다. 없으면 기존 자료에서 토큰과 연결된 Circle(USDC), Paxos(PYUSD), SG-FORGE(EURCV)만 채우고 나머지는 `UNVERIFIED`로 남긴다. 카탈로그에 그 근거 ID를 적었다. 발행사 이름은 관할권별 법인이나 시점별 발행 주체 변경까지 재구성한 값으로 해석하기 어렵다 (CASE-S01, CASE-S03, CASE-S12).

## 결측과 이상치

- 각 코인·체인 시계열에서 최초·최종 제공 관측일 사이의 누락 날짜는 빈 값으로 표시한다. 첫 관측 전과 마지막 관측 후는 결측 분모에서 제외한다. 정제가 가능한 날짜가 없는 시계열은 행을 만들지 않고 실행 통계에 기록한다.
- 유효하지 않은 Unix 시간과 기준일 이후 기록은 제외한다. UTC 날짜에 관측이 여럿 있으면 가장 늦은 원본 타임스탬프를 적용한다. 동일한 최종 타임스탬프에 충돌하는 값은 빈 값으로 둔다.
- 음수·비유한 금액, 비수치 금액, 가격이 필요한데 같은 날의 양의 가격이 없는 값은 빈 값으로 남긴다. API가 기록한 실제 0은 보존한다. 가격을 1달러로 치환하거나 보간하지 않으며, 큰 양수와 급변은 임의 삭제하지 않는다.
- 결측률은 각 그룹에서 빈 `circulating_usd` 행을 전체 생성 행으로 나눈 비율이다. 발행사와 기준 통화의 미확인은 별도 집계한다.

## 알려진 한계

- DefiLlama 유통량은 API의 토큰·체인·시점 정의를 따른다. 발행사 공시와 비교할 때 준비금과 유통량, 보고 기준일, 미유통 토큰 및 브리지 처리 범위가 일치하는지 확인해야 한다 (DATA-LLAMA-02, DATA-LLAMA-03, CASE-S01, CASE-S04).
- API 페그 코드는 공급자의 분류다. 분류 오류, 목표 통화 변경, 실제 디페그 여부는 별도 검증이 필요하다. `peggedVAR`를 특정 통화로 해석하지 않는다 (DATA-LLAMA-05).
- 개별 체인에는 브리지 유입과 원체인에서 생성된 수량이 함께 나타날 수 있다. 체인별 수량을 단순 합산하면 경제적으로 같은 토큰을 중복 집계할 수 있다. 전체 체인 합계에는 공급자의 `ALL` 차트를 사용하며 `ALL`과 개별 체인 행을 함께 더하지 않는다 (DATA-LLAMA-02, DATA-LLAMA-03).
