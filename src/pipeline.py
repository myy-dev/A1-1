"""AdventureWorks 온라인 주문 분석"""

from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.image import imread


class DataAnalyzer:
    """상품 특성 추출과 고객별 구매 분석"""

    def __init__(self, data_path):
        self.data_path = Path(data_path)
        self.df = None

    def _require(self, columns, step):
        """선행 단계 누락 시 원인을 알려 주는 오류"""
        if self.df is None:
            raise RuntimeError("load_data()를 먼저 호출해야 합니다.")
        missing = [column for column in columns if column not in self.df.columns]
        if missing:
            raise RuntimeError(f"{step}를 먼저 호출해야 합니다. 없는 열: {', '.join(missing)}")

    def load_data(self):
        """거래 CSV 로드와 식별자·거래일 자료형 설정"""
        self.df = pd.read_csv(
            self.data_path,
            dtype={key: "string" for key in ("customer_id", "order_id", "product_id")},
            parse_dates=["order_date"],
        )
        return self.df

    def add_features(self):
        """상품명 길이와 전체 RGB 값 기반 사진별 통계·히스토그램 비율"""
        self._require(["product_name", "image_path"], "load_data()")
        df = self.df
        df["name_length"] = df["product_name"].str.len()
        paths = df["image_path"].dropna().unique()

        # 파일별 RGB 배열 로드와 알파 채널 제외
        pixels = [
            imread(self.data_path.parent / path)[..., :3].astype(np.float32).ravel()
            for path in paths
        ]
        # 서로 다른 사진 크기를 위한 결측 패딩 및 사진 단위 벡터 연산
        max_size = max(map(len, pixels))
        batch = np.stack([
            np.pad(row, (0, max_size - row.size), constant_values=np.nan)
            for row in pixels
        ])
        counts = np.isfinite(batch).sum(axis=1)
        features = pd.DataFrame({
            "pixel_mean": np.nanmean(batch, axis=1),
            "pixel_std": np.nanstd(batch, axis=1),
            "dark_share": ((batch >= 0) & (batch < 64)).sum(axis=1) / counts,
            "mid_share": ((batch >= 64) & (batch < 192)).sum(axis=1) / counts,
            "bright_share": (batch >= 192).sum(axis=1) / counts,
        }, index=paths)
        for column in features:
            df[column] = df["image_path"].map(features[column])
        return df

    def handle_missing_values(self, group_col="product_category", strategy="median"):
        """고유 사진의 그룹별 통계로 분석용 이미지 피처 대치"""
        if strategy not in {"median", "mean"}:
            raise ValueError("strategy는 median 또는 mean이어야 합니다.")
        self._require([group_col, "image_path", "pixel_mean", "pixel_std"], "add_features()")
        df = self.df
        observed = df.dropna(subset=["image_path"]).drop_duplicates([group_col, "image_path"])
        columns = ["pixel_mean", "pixel_std"]
        estimates = observed.groupby(group_col)[columns].agg(strategy)
        df["image_missing"] = df["image_path"].isna()
        for column in columns:
            df[column + "_filled"] = df[column].fillna(df[group_col].map(estimates[column]))
        return df

    @staticmethod
    def detect_outliers(values, multiplier=1.5):
        """IQR 경계와 범위 밖 관측값 마스크"""
        if multiplier < 0:
            raise ValueError("이상치 임계 배수는 0 이상이어야 합니다.")
        q1, q3 = values.quantile([0.25, 0.75])
        margin = multiplier * (q3 - q1)
        lower, upper = q1 - margin, q3 + margin
        return (values < lower) | (values > upper), lower, upper

    @staticmethod
    def summarize(frame, columns):
        """수치 변수별 평균·중앙값·표준편차·사분위수"""
        return frame[columns].describe().T

    def calculate_rfm(self, reference_date=None):
        """고객별 최근성·빈도·구매액 점수와 상호 배타적 고객군"""
        self._require(["customer_id", "order_id", "order_date", "line_amount"], "load_data()")
        df = self.df
        last_date = df["order_date"].max()
        reference = last_date if reference_date is None else pd.Timestamp(reference_date)
        if reference < last_date:
            raise ValueError("기준일은 마지막 거래일 이후이거나 같은 날이어야 합니다.")
        rfm = df.groupby("customer_id").agg(
            last_purchase=("order_date", "max"),
            frequency=("order_id", "nunique"),
            monetary=("line_amount", "sum"),
        )
        rfm["recency"] = (reference - rfm["last_purchase"]).dt.days
        rfm["r_score"] = np.where(rfm["recency"] <= rfm["recency"].median(), 2, 1)
        rfm["f_score"] = rfm["frequency"].clip(upper=3)
        rfm["m_score"] = np.where(rfm["monetary"] >= rfm["monetary"].median(), 2, 1)
        repeat = rfm["f_score"] >= 2
        rfm["segment"] = np.select(
            [repeat & (rfm["m_score"] == 2), repeat, rfm["r_score"] == 2],
            ["High-value repeat", "Lower-value repeat", "Recent single"],
            default="Older single",
        )
        return rfm

    def purchase_cohorts(self):
        """첫 관측 구매월별 경과월 고유 구매자 수와 재구매율"""
        self._require(["customer_id", "order_date"], "load_data()")
        purchases = self.df[["customer_id", "order_date"]].copy()
        purchases["month"] = purchases.pop("order_date").dt.to_period("M")
        purchases = purchases.drop_duplicates()
        purchases["cohort"] = purchases.groupby("customer_id")["month"].transform("min")
        purchases["age"] = purchases["month"].astype("int64") - purchases["cohort"].astype("int64")

        counts = purchases.groupby(["cohort", "age"]).size().unstack()
        last_month = purchases["month"].max().ordinal
        observed_months = last_month - counts.index.asi8
        ages = np.arange(observed_months.max() + 1)
        counts = counts.reindex(columns=ages).fillna(0)
        counts = counts.where(ages[None, :] <= observed_months[:, None])
        rates = counts.div(counts[0], axis=0)
        return counts, rates
