# 스테이블코인 관련 사업모델 사례

확인일은 2026-11-22다. [사례 CSV](cases.csv)의 규제 의존도는 각 상품의 기능을 [규제 매트릭스](../regulation/matrix.csv)와 대조한 정성 판단이다. 출시일은 아래에 표시한 최초 발표, 기관 고객 이용 개시 또는 실거래 개시를 뜻한다. `UNDISCLOSED`는 열람한 공식 자료에서 해당 상품에 귀속되는 금액·조건을 확인하지 못했다는 뜻이다. 규모의 단위와 기준일은 사례마다 다르다. 근거 문서는 [출처 대장](../sources/sources.csv)에서 ID로 찾을 수 있다.

## 비교표

| ID | 사례군 · 관할권 | 제품 | 출시·개시일 | 공개 규모 | 선정 이유 |
|---|---|---|---|---|---|
| C01 | 순수 발행사 · US | USDC | 2018-09-26 | USDC 유통량 USD 75.3 billion (2025-12-31, CASE-S01). | 준비자산 수익과 플랫폼 유통비가 공시된 발행사 사례. |
| C02 | 핀테크·결제사 · US | PayPal USD (PYUSD) | 2023-08-07 | 발행잔액 USD 570,851,729 (2024-10-31, Paxos 비감사 자체 공시, CASE-S04). | 인가 발행사와 소비자 결제 플랫폼의 분업을 보여 준다. |
| C03 | 핀테크·결제사 · US | Stablecoin payments for subscriptions (표준 결제 요율 1.5%, 구독 프리뷰 개별 계약 요율 UNDISCLOSED, CASE-S06·07) | 2025-10-14 | 지원 지갑 400개 초과 (2025-10-14 회사 발표, 호환 범위). 상품 자체 결제액 UNDISCLOSED (CASE-S06). | 가맹점의 법정화폐 정산과 구독 결제 통합을 보여 준다. |
| C04 | 은행·전통 금융기관 · US | JPM Coin (JPMD) USD 예금 토큰 | 2025-11-12 | JPMD 단독 발행잔액·거래액 UNDISCLOSED (CASE-S08, CASE-S09). | 은행 예금이 공개 블록체인에서 결제에 쓰이는 비교 사례. |
| C05 | 은행·전통 금융기관 · EU | EUR CoinVertible (EURCV) | 2023-04-20 | EURCV 유통잔액 EUR 169,866,718.22 (2026-11-22, 기업 동적 공시, CASE-S13). | 은행 계열 발행사가 MiCA에 맞춰 기존 상품을 재구성한 사례. |
| C06 | 아시아·홍콩 · HK | HSBC RedCoin (RCHKD) | 2026-10-23 | 유통 액면총액 HKD 592,765,358.81 (2026-11-21, 기업 동적 공시, CASE-S15). | 홍콩 인가 은행이 기존 소매 앱으로 유통한 사례. |
| C07 | 아시아·한국 · KR | 프로젝트 한강 1차 예금 토큰 실거래 | 2025-04-01 | 참가은행 7개, 이용자 최대 10만 명 범위 (2025-04~06 1차 파일럿, 최대치는 실참가자 수가 아님, CASE-S16). | 국내 은행 예금 토큰이 실제 결제에 쓰인 공식 실증 사례. |

## C01. Circle · USDC

Circle은 USDC를 공개하고 거래소·지갑 생태계로 유통을 넓혔다 (CASE-S01, CASE-S02). FY2025 공시에서 준비자산 이자·배당은 USDC·EURC를 합친 Circle 연결 계속사업 수익의 96.0%였으며, USDC 유통잔액은 별도 지표다 (CASE-S01). **규제 연관 가설** — `reserve_requirements`, `redemption`은 보유자 자산 보호와 민감한 준비자산 운용 범위를 좌우할 수 있으며, 회사 공시에서도 분리 준비금과 금리 민감성을 확인할 수 있다 (CASE-S01, US-01). USDC 출시와 현재의 수익 구조는 GENIUS Act 시행 전의 관찰이다 (CASE-S02, US-01, US-02).

> source_quote (CASE-S01): “We earn interest and dividends on assets held in reserve accounts”  
> 번역 — 준비계좌에 보유한 자산에서 이자와 배당을 얻는다.

## C02. PayPal·Paxos · PYUSD

PayPal은 2023-08-07 PYUSD 출시를 발표했고, 출시 당시 NYDFS 감독을 받는 Paxos가 발행을 맡았다 (CASE-S03). PayPal과 Venmo는 지인 송금 등을 제공했으며, 준비자산 수익의 PayPal 귀속 비중은 확인되지 않았다 (CASE-S03, CASE-S04, CASE-S05). PYUSD 발행잔액 USD 570,851,729는 2024-10-31 기준 Paxos의 비감사 자체 공시 수치다 (CASE-S04). **규제 연관 가설** — `issuer_eligibility`, `reserve_requirements`, `redemption`에서 보듯 발행 파트너가 준비금과 상환에 대응하고 PayPal이 결제 접점을 제공하는 분업이 가능하다 (CASE-S03, US-01). 출시 당시 근거는 NYDFS 체계이며 GENIUS Act는 이후 제정된 비교 기준이다 (CASE-S03, US-01, US-02).

> source_quote (CASE-S03): “PayPal USD is redeemable 1:1 for U.S. dollars”  
> 번역 — PayPal USD는 미국 달러로 1대1 상환할 수 있다.

## C03. Stripe · 스테이블코인 구독 결제

Stripe는 2025-10-14 미국 사업자 대상 비공개 프리뷰에서 Base·Polygon의 USDC 구독 결제를 소개했다 (CASE-S06). 구매자는 지갑으로 결제하고 가맹점에는 법정화폐로 정산된다. 공개된 표준 스테이블코인 결제 요금표는 구독 프리뷰의 개별 계약 요율과 구분된다 (CASE-S06, CASE-S07). **규제 연관 가설** — `issuer_eligibility`, `reserve_requirements`가 기초 토큰 발행인에 적용되는 구조에서는 Stripe가 결제 통합과 정산에 집중할 수 있으며, 공식 요금표의 AML 심사는 `aml_travel_rule`의 개별 거래 적용 여부와 별도 확인이 필요하다 (CASE-S06, CASE-S07, US-01, US-10).

> source_quote (CASE-S06): “Let customers use their crypto wallets to pay for subscriptions, which then settle directly in fiat”  
> 번역 — 고객은 암호자산 지갑으로 구독료를 내고, 대금은 법정화폐로 직접 정산된다.

## C04. J.P. Morgan · JPMD

J.P. Morgan은 2025-11-12 Base의 JPMD를 기관 고객에게 제공한다고 발표했고, 개념검증에는 B2C2·Coinbase·Mastercard가 참여했다 (CASE-S08). JPMD는 은행 인프라 안에서 현금과 전환되는 예금 토큰이며, JPMD 단독 발행잔액과 거래액은 확인되지 않았다 (CASE-S08, CASE-S09). **규제 연관 가설** — `bank_role`, `issuer_eligibility`에서 은행 예금 경로가 별도 비교 대상이 되는 것은 GENIUS Act가 분산원장에 기록된 예금을 결제용 스테이블코인 정의에서 제외하기 때문이다 (US-01). J.P. Morgan이 이 법 때문에 설계를 선택했다는 근거는 확인되지 않았다 (CASE-S08, CASE-S09).

> source_quote (CASE-S09): “Your funds stay within J.P. Morgan’s banking infrastructure at every stage.”  
> 번역 — 모든 단계에서 자금은 J.P. Morgan의 은행 인프라 안에 남는다.

## C05. Société Générale–FORGE · EURCV

SG-FORGE는 2023-04-20 EURCV를 공개했고, 2024-07-01에는 MiCA에 맞춘 상품 변경과 프랑스 ACPR의 EMI 인가를 발표했다 (CASE-S10, CASE-S11). 백서는 전자화폐토큰 분류, 발행사 분리계좌 및 Bitstamp·Bullish 경로를 기술하고, 유통잔액은 별도 공식 페이지가 공시한다 (CASE-S12, CASE-S13). **규제 연관 가설** — `issuer_eligibility`, `reserve_requirements`, `redemption`, `licensing_status`가 기존 EURCV의 상품 조건과 유통 계획에 영향을 주었을 가능성이 있다. 회사가 MiCA 준수와 유통 확대를 함께 언급했으나, 재구성이 유통량을 얼마나 바꿨는지는 이 자료로 확인할 수 없다 (CASE-S11, CASE-S12, EU-01).

> source_quote (CASE-S11): “in compliance with the European Markets in Crypto-assets (MiCA) regulation”  
> 번역 — 유럽 암호자산시장규정(MiCA)을 준수하는 방식으로.

## C06. HSBC Hong Kong · RedCoin

HSBC는 홍콩 스테이블코인 발행 인가를 받은 뒤 2026-10-23 PayMe에서 RedCoin을 출시했고, 2026-11-19 HSBC HK 앱에서 토큰화 펀드 접근 기능을 발표했다 (HK-06, CASE-S14, CASE-S18). 공식 상품 페이지는 조건부 1대1 상환, 전환 무료, 예금보호 제외를 명시한다 (CASE-S15). **규제 연관 가설** — `issuer_eligibility`, `reserve_requirements`, `redemption`, `aml_travel_rule`이 발행·고객 통제 설계와 연결됐을 가능성이 있다. HSBC는 출시 발표에서 조례상 금융범죄 통제를 언급하는 동시에 기존 앱 접근성과 빠른 결제를 출시 설계에 반영했다고 설명했다 (CASE-S14, HK-01, HK-03, HK-04).

> source_quote (CASE-S15): “It's redeemable 1:1 for HKD, subject to applicable terms and conditions.”  
> 번역 — 적용 약관에 따라 홍콩달러로 1대1 상환할 수 있다.

## C07. 한국은행·참가은행 · 프로젝트 한강

공식 실시 계획은 2025-04-01을 실거래 개시일로 제시했고, 한국은행 연차보고서는 2025년 4~6월 참가은행 전자지갑과 가맹점·바우처를 통한 파일럿을 확인한다. 이때 최대 10만 명은 파일럿의 참여 상한이며 실제 참여자 수는 별도 지표다 (CASE-S16, CASE-S19). 이용자는 참가은행 예금과 예금 토큰 사이를 전환했으며, 한국은행은 기관용 디지털화폐와 은행 예금 토큰을 2계층 구조로 설명한다 (CASE-S16, CASE-S17). **규제 연관 가설** — `bank_role`, `supervisor`, `licensing_status` 관점에서 은행과 중앙은행을 잇는 파일럿은 예금 기반 지급수단을 시험하는 경로로 볼 수 있다. 현행 시행령의 요건부 가상자산 제외 규정과 미확정 스테이블코인 의원안은 적용 범위가 다르며, 파일럿 범위가 상용화 조건을 확정하지는 않는다 (KR-02, KR-06, KR-07, CASE-S16).

## 확인 한계

- PayPal 출시일과 유통·수수료 설명, Paxos의 2024-10-31 잔액은 공식 웹 원문에서 확인했다. 해당 자료 세 건(CASE-S03·04·05)의 로컬 텍스트는 미확보다. Paxos 잔액은 당시의 비감사 수치다.
- 동적 유통잔액은 기업 페이지가 표시한 날짜에 해당한다 (CASE-S13, CASE-S15). Stripe 지원 지갑 수와 프로젝트 한강의 참여 상한은 실제 이용 실적과 구분한다 (CASE-S06, CASE-S16).

