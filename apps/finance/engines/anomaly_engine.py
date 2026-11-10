"""
2. Anomaly Detection Engine (Phát hiện giao dịch chi tiêu bất thường).
Combines Scikit-learn `IsolationForest` with statistical Z-Score (mu + 2.5*sigma) and IQR.
Inherits from BaseFinancialAnalyzer(ABC).
"""
from decimal import Decimal
from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from apps.finance.engines.base_analyzer import BaseFinancialAnalyzer


class AnomalyDetectionEngine(BaseFinancialAnalyzer):
    """
    Module Ăn Điểm 2: Spending Anomaly Detector (`AnomalyDetectionEngine` / `SpendingAnomalyDetector`).
    Kết hợp:
    - Scikit-learn `IsolationForest`
    - Kiểm định thống kê Z-Score (`z_score >= 2.5`)
    - Khoảng tứ phân vị IQR (`amount > Q3 + 1.5 * IQR`)
    """

    def __init__(
        self,
        raw_transactions: List[Dict[str, Any]],
        z_threshold: float = 2.5,
        iqr_multiplier: float = 1.5,
    ):
        super().__init__(raw_transactions)
        self._z_threshold: float = z_threshold
        self._iqr_multiplier: float = iqr_multiplier

    def preprocess(self) -> pd.DataFrame:
        if not self._raw_data:
            self._dataframe = pd.DataFrame(
                columns=["id", "amount", "transaction_date", "category__name", "note"]
            )
            self._is_preprocessed = True
            return self._dataframe

        df = pd.DataFrame(self._raw_data)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        if "transaction_date" in df.columns:
            df["transaction_date"] = pd.to_datetime(df["transaction_date"], utc=True)
        self._dataframe = df
        self._is_preprocessed = True
        return self._dataframe

    def execute_analysis(self) -> Dict[str, Any]:
        df = self._dataframe.copy()
        if df.empty or len(df) < 3:
            return {
                "total_analyzed": len(df),
                "anomaly_count": 0,
                "statistics": {
                    "mean": 0.0,
                    "std": 0.0,
                    "q1": 0.0,
                    "q3": 0.0,
                    "iqr": 0.0,
                    "iqr_upper_bound": 0.0,
                },
                "anomalies": [],
            }

        amounts = df["amount"].values.astype(float)
        mean_val = float(np.mean(amounts))
        std_val = float(np.std(amounts))
        q1 = float(np.percentile(amounts, 25))
        q3 = float(np.percentile(amounts, 75))
        iqr = q3 - q1
        iqr_upper_bound = q3 + self._iqr_multiplier * iqr

        if std_val > 0:
            df["z_score"] = (df["amount"] - mean_val) / std_val
        else:
            df["z_score"] = 0.0

        # IsolationForest inference when sample size >= 10
        if len(df) >= 10:
            iforest = IsolationForest(
                n_estimators=50, contamination=0.05, random_state=221
            )
            preds = iforest.fit_predict(amounts.reshape(-1, 1))
            df["is_iforest_anomaly"] = (preds == -1) & (df["amount"] > mean_val)
        else:
            df["is_iforest_anomaly"] = False

        df["is_z_anomaly"] = df["z_score"] >= self._z_threshold
        df["is_iqr_anomaly"] = (iqr > 0) & (df["amount"] > iqr_upper_bound)
        df["detected_anomaly"] = df["is_z_anomaly"] | df["is_iqr_anomaly"]

        anomalies_df = df[df["detected_anomaly"]].sort_values(
            by="amount", ascending=False
        )

        anomalies_list = [
            {
                "id": str(row.get("id", "")),
                "amount": round(float(row["amount"]), 2),
                "z_score": round(float(row["z_score"]), 2),
                "category": row.get("category__name") or "Chưa phân loại",
                "note": row.get("note", ""),
                "transaction_date": (
                    row["transaction_date"].isoformat()
                    if pd.notnull(row.get("transaction_date"))
                    else None
                ),
            }
            for _, row in anomalies_df.iterrows()
        ]

        return {
            "total_analyzed": int(len(df)),
            "anomaly_count": int(len(anomalies_list)),
            "statistics": {
                "mean": round(mean_val, 2),
                "std": round(std_val, 2),
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "iqr": round(iqr, 2),
                "iqr_upper_bound": round(iqr_upper_bound, 2),
            },
            "anomalies": anomalies_list,
        }

    def evaluate_single_transaction(
        self, candidate_amount: Decimal | float
    ) -> Tuple[bool, float]:
        """
        Đánh giá thời gian thực (Real-time Inference) cho 1 giao dịch mới phát sinh.
        """
        if not self._is_preprocessed:
            self.preprocess()

        amount_val = float(candidate_amount)
        if self._dataframe.empty or len(self._dataframe) < 5:
            return False, 0.0

        historical = self._dataframe["amount"].values.astype(float)
        mean_val = float(np.mean(historical))
        std_val = float(np.std(historical))
        q1 = float(np.percentile(historical, 25))
        q3 = float(np.percentile(historical, 75))
        iqr = q3 - q1
        iqr_upper = q3 + self._iqr_multiplier * iqr

        z_score = (amount_val - mean_val) / std_val if std_val > 0 else 0.0
        is_anomaly = (z_score >= self._z_threshold) or (
            iqr > 0 and amount_val > iqr_upper
        )
        return bool(is_anomaly), round(float(z_score), 2)


# Aliases khớp 1:1 với Sơ đồ lớp StarUML & Báo cáo
SpendingAnomalyDetector = AnomalyDetectionEngine
AnomalyDetector = AnomalyDetectionEngine
