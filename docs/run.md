# 분석 재현

## 준비

프로젝트 루트에서 명령을 실행한다. 과제 ZIP의 입력이 이미 `data/`에 풀려 있다. 데이터 준비가 다시 필요하면 같은 ZIP의 `transactions.csv`와 `images/`가 이 경로에 오도록 압축을 푼다. [데이터 구성과 출처](data.md)

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m jupyterlab notebooks/analysis_report.ipynb
```

`requirements.txt`의 버전은 Python 3.14.5에서 노트북 전체를 다시 실행해 확인한 조합이다. pandas 3은 Python 3.11 이상이 필요하다.

노트북에서 방금 만든 환경의 Python 커널을 선택하고 **Restart Kernel and Run All Cells**를 실행한다. 위에서부터 데이터 탐색, 이미지 피처·결측 대치, 고객 집계와 이상치, 시각화, 세그먼트 분석, 첫 구매월별 재구매율 순서로 결과를 확인한다. Plotly는 보너스 차트에만 사용한다. 9절 실행 후 프로젝트의 `docs/segments.html` 파일을 더블클릭하면 기본 브라우저에서 고객 한 명당 점 하나로 표시된 고객군 분포를 살펴볼 수 있다. 차트 라이브러리는 CDN에서 불러오므로 인터넷 연결이 필요하다. [인터랙티브 고객군 차트](segments.html)

## 파이프라인 사용

프로젝트 루트에서 Python을 열어 아래 코드를 실행한다.

```python
from src.pipeline import DataAnalyzer

analysis = DataAnalyzer("data/transactions.csv")
transactions = analysis.load_data()
analysis.add_features()
analysis.handle_missing_values(group_col="product_category", strategy="median")
customers = analysis.calculate_rfm()
print(analysis.summarize(customers, ["recency", "frequency", "monetary"]))
outliers, lower, upper = analysis.detect_outliers(customers["monetary"], multiplier=1.5)
print(outliers.sum(), lower, upper)
cohort_counts, retention = analysis.purchase_cohorts()
print(cohort_counts.iloc[:3, :4], retention.iloc[:3, :4])
```

`pixel_mean`과 `pixel_std`는 고유 사진의 실제 측정값이다. `_filled` 열은 같은 대분류에서 관측한 고유 사진의 중앙값으로 채운 분석용 값이며, `image_missing`이 추정 여부를 나타낸다. 이미지를 결합하기 전후의 거래 수는 같아야 한다.

코호트 표의 행은 첫 관측 온라인 구매월, 열은 첫 구매 후 경과월이다. 노트북 8절을 실행하면 고유 구매자 수·재구매율, 가중 M1 집계, 월별 히트맵을 확인할 수 있다. [코호트 정의와 결과](cohort.md) · [전체 월차 히트맵](cohort-heatmap.png)

가입월 기준 유지율을 산출하려면 가입일과 고객 ID가 필요하다. 현재 입력에는 주문일이 있어 고객별 첫 관측 온라인 구매월을 기준으로 계산했다.
