# 스테이블코인 규제 비교 연구

미국·EU·홍콩·한국의 스테이블코인 규제 설계와 발행·유통 구조를 비교하고, 한국 은행과 핀테크의 사업 선택지를 검토한다. [최종 리포트](report/report.md)의 규제 정보 기준일은 **2026-11-22**다. 문서별 확인일은 출처 대장의 `retrieved_date`에 기록했다.

## 폴더 구조

| 경로 | 내용 |
|---|---|
| `report/` | 최종 리포트와 시사점 원문 |
| `regulation/`, `cases/` | 규제 매트릭스와 사업모델 사례 |
| `sources/`, `logs/` | 출처 대장과 감사 기록 |
| `data/` | 정제 결과와 발행사 매핑 |
| `analysis/`, `figures/` | 수집·정제·분석 코드, 결과표, 차트 |
| `docs/` | 연구 범위와 데이터 정의 |

## 재현 순서

저장소 루트에서 Python 3.10 이상, `curl`, [분석 의존성](requirements.txt)을 사용한다. 배포된 정제 CSV로 리포트의 분석과 차트를 재현하려면 다음을 실행한다.

```powershell
python -m pip install -r requirements.txt
python analysis/03_concentration.py
python analysis/04_nonusd.py --render-figure
```

원자료 합계가 50MB를 초과하므로 `data/raw/`는 배포 대상에서 제외한다. DefiLlama API에서 다시 수집할 때는 아래 날짜를 **실제 수집일**로 통일한다. 2026-11-22 원본이 별도로 보관돼 있다면 해당 디렉터리와 매니페스트를 복원하고 원래 날짜로 정제할 수 있다.

```powershell
$snapshotDate = Get-Date -Format yyyy-MM-dd
python analysis/01_collect.py --snapshot-date $snapshotDate
python analysis/02_clean.py --snapshot-date $snapshotDate
```

날짜 인자는 API를 과거 시점으로 되돌리지 않는다. 재수집은 기존 정제 결과를 갱신할 수 있으므로 보존이 필요하면 별도 체크아웃에서 진행한다. 새 스냅샷은 발행사 매핑을 공식 근거와 대조해 갱신한 뒤 분석한다. [상세 재현 절차](analysis/README.md)

## 데이터 출처와 한계

규제·사례는 [출처 대장](sources/sources.csv)의 법령, 감독기관 문서와 기업 공시 등에 근거한다. 각 문서는 대장 URL에서 확인할 수 있다. `sources/raw/`는 저작권과 용량을 고려해 배포 대상에서 제외한다. 시장 분석은 DefiLlama API의 전체 체인 시총을 사용한다. 페그 통화는 보유자나 발행사의 소재지를 나타내지 않으며, 누락·개정·환율 및 과거 발행사 매핑의 한계가 있다. 이벤트 전후 비교는 관찰 결과다. [DATA-LLAMA-02, DATA-LLAMA-03, DATA-LLAMA-04, DATA-LLAMA-05] [데이터 정의](docs/data_notes.md) · [분석 한계](analysis/limitations.md)
