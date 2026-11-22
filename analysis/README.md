# 데이터 수집·정제 실행 순서

저장소 루트에서 Python 3.10 이상과 `curl`을 사용한다. DefiLlama 무료 API는 키가 필요 없다.

```powershell
python analysis/01_collect.py --snapshot-date 2026-11-22
python analysis/02_clean.py --snapshot-date 2026-11-22
```

첫 스크립트는 같은 스냅샷 폴더에서 이미 저장된 응답을 재사용하므로, 중단 후 같은 명령으로 누락 응답을 다시 받을 수 있다. 다른 날의 데이터를 수집할 때는 해당 날짜를 두 명령에 동일하게 지정한다. `--snapshot-date`는 파일 구분과 정제 기준일로 쓰이며, API를 특정 과거 시점으로 되돌리지 않는다. 두 번째 스크립트는 명시적으로 `--allow-partial`을 지정한 경우에만 일부 응답이 없는 스냅샷을 정제한다.

정제 결과는 `data/processed/`에 저장된다. 필드 정의와 결측 분모는 [데이터 노트](../research/docs/data_notes.md)에 있다.

## Step 4-b 시계열 재실행

`pandas`와 `matplotlib`이 설치된 Python에서 저장소 루트 기준으로 아래 순서대로 실행한다.

```powershell
python analysis/03_concentration.py
python analysis/04_nonusd.py
```

첫 명령은 집중도 PNG를 만들고, 두 번째 명령은 두 분석을 합친 `analysis/results.md`를 만든다. 페그별 PNG도 재생성하려면 두 번째 명령에 `--render-figure`를 추가한다. 입력은 Step 4-a 정제 CSV, 범위 문서, 출처 대장과 `data/issuer_map.csv`다. 발행사 매핑은 최신 관측일 상위 15개와 일치해야 한다. 새 스냅샷을 분석할 때는 공식 출처를 등록하고 이 매핑을 갱신한다. 전체 체인 시총을 분모로 발행사 확인 비율을 계산하며, 잔여 미확인 코인은 분리 시나리오에서 개별 그룹으로 둔다. 페그 정정은 `04_nonusd.py`의 출처 연결 분류를 적용한다. Windows에서는 맑은 고딕을 사용한다. 한글 폰트 자동 검색이 적용되지 않는 환경에서는 `STABLECOIN_KOREAN_FONT` 환경 변수에 한글 폰트 파일 경로를 지정한다.
