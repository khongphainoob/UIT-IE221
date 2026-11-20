"""
1. Burn-Rate Forecasting Engine (Dự báo tốc độ đốt tiền & ngày cạn ví).
Uses Pandas `.resample('D').sum()` and 7-day rolling moving average (`rolling(7).mean()`)
for feature extraction, then runs real-time inference via pre-trained `burn_rate_huber`
loaded from `MLModelRegistry` (Singleton Pattern).
"""
import calendar
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from apps.finance.engines.base_analyzer import BaseFinancialAnalyzer
from apps.finance.engines.model_registry import MLModelRegistry


class BurnRateAnalyzer(BaseFinancialAnalyzer):
    """
    Module Ăn Điểm 1: Smart Burn-Rate Forecaster (`BurnRateAnalyzer` / `BurnRateForecaster`).
    Đóng gói thuộc tính nội bộ: `_daily_burn_rate`, `_safety_threshold`, `_current_balance`.
    Chỉ thực hiện Feature Extraction (Pandas) + Real-time Inference (`.predict()`) qua `MLModelRegistry`.
    """

    def __init__(
        self,
        raw_transactions: List[Dict[str, Any]],
        current_balance: Decimal | float,
        reference_date: Optional[date] = None,
        safety_threshold: float = 50000.0,
    ):
        super().__init__(raw_transactions)
        self._current_balance: float = float(current_balance)
        self._reference_date: date = reference_date or date.today()
        self._safety_threshold: float = float(safety_threshold)
        self._daily_burn_rate: float = 0.0
        self._daily_series: pd.DataFrame = pd.DataFrame()

    @property
    def daily_burn_rate(self) -> float:
        """Read-only property trả về tốc độ tiêu tiền trung bình/ngày đã suy luận."""
        return round(self._daily_burn_rate, 2)

    @property
    def safety_threshold(self) -> float:
        """Read-only property trả về ngưỡng an toàn tối thiểu/ngày."""
        return round(self._safety_threshold, 2)

    def preprocess(self) -> pd.DataFrame:
        """
        Chuẩn hóa danh sách giao dịch sang chuỗi thời gian theo ngày (`.resample('D').sum()`)
        và trích xuất đặc trưng trung bình trượt 7 ngày (`rolling_7d_avg`).
        """
        if not self._raw_data:
            self._dataframe = pd.DataFrame(
                columns=["transaction_date", "amount", "rolling_7d_avg"]
            )
            self._is_preprocessed = True
            return self._dataframe

        df = pd.DataFrame(self._raw_data)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        df["transaction_date"] = pd.to_datetime(
            df["transaction_date"], utc=True
        ).dt.tz_localize(None)

        daily_df = (
            df.set_index("transaction_date")[["amount"]]
            .resample("D")
            .sum()
            .fillna(0.0)
        )

        daily_df["rolling_7d_avg"] = (
            daily_df["amount"].rolling(window=7, min_periods=1).mean()
        )
        daily_df["cumulative_spent"] = daily_df["amount"].cumsum()

        self._daily_series = daily_df
        self._dataframe = daily_df.reset_index()
        self._is_preprocessed = True
        return self._dataframe

    def _calculate_remaining_days_in_month(self) -> int:
        _, last_day = calendar.monthrange(
            self._reference_date.year, self._reference_date.month
        )
        remaining = last_day - self._reference_date.day + 1
        return max(remaining, 1)

    def execute_analysis(self) -> Dict[str, Any]:
        """
        Suy luận thời gian thực (Real-time Inference):
        Nạp pre-trained `burn_rate_huber` từ `MLModelRegistry` (Singleton) và gọi `.predict()`
        trên vector đặc trưng `[avg_daily_burn, rolling_7d_burn]` để dự báo:
        - `daily_burn_rate`
        - `predicted_exhaustion_date`
        - `days_until_exhaustion`
        - `safe_daily_allowance` / `recommended_daily_limit`
        """
        remaining_days_in_month = self._calculate_remaining_days_in_month()
        safe_daily_allowance = round(
            max(self._current_balance, 0.0) / remaining_days_in_month, 2
        )

        if self._daily_series.empty or self._current_balance <= 0:
            exhaustion_date = (
                self._reference_date.isoformat()
                if self._current_balance <= 0
                else None
            )
            self._daily_burn_rate = 0.0
            return {
                "current_balance": round(self._current_balance, 2),
                "daily_burn_rate": 0.0,
                "average_daily_burn": 0.0,
                "rolling_7d_burn_rate": 0.0,
                "regression_daily_slope": 0.0,
                "effective_daily_burn": 0.0,
                "days_until_exhaustion": 0 if self._current_balance <= 0 else None,
                "predicted_exhaustion_date": exhaustion_date,
                "safe_daily_allowance": safe_daily_allowance,
                "recommended_daily_limit": safe_daily_allowance,
                "remaining_days_in_month": remaining_days_in_month,
                "is_burn_rate_critical": self._current_balance <= 0,
                "daily_trend": [],
            }

        avg_daily_burn = float(self._daily_series["amount"].mean())
        rolling_7d_burn = float(self._daily_series["rolling_7d_avg"].iloc[-1])

        # Load pre-trained HuberRegressor via Singleton MLModelRegistry & run inference (.predict)
        huber_model = MLModelRegistry.get_instance().get_model("burn_rate_huber")
        feature_vector = np.array([[avg_daily_burn, rolling_7d_burn]], dtype=float)
        predicted_burn = float(max(huber_model.predict(feature_vector)[0], 0.0))

        effective_daily_burn = (
            predicted_burn if predicted_burn > 0 else avg_daily_burn
        )
        self._daily_burn_rate = effective_daily_burn

        if effective_daily_burn > 0:
            days_left = int(np.floor(self._current_balance / effective_daily_burn))
            predicted_date = (
                self._reference_date + timedelta(days=days_left)
            ).isoformat()
            is_critical = days_left < remaining_days_in_month
        else:
            days_left = None
            predicted_date = None
            is_critical = False

        recent_df = self._daily_series.tail(14).reset_index()
        daily_trend = [
            {
                "date": row["transaction_date"].strftime("%Y-%m-%d"),
                "daily_spent": round(float(row["amount"]), 2),
                "rolling_7d_avg": round(float(row["rolling_7d_avg"]), 2),
            }
            for _, row in recent_df.iterrows()
        ]

        return {
            "current_balance": round(self._current_balance, 2),
            "daily_burn_rate": round(effective_daily_burn, 2),
            "average_daily_burn": round(avg_daily_burn, 2),
            "rolling_7d_burn_rate": round(rolling_7d_burn, 2),
            "regression_daily_slope": round(predicted_burn, 2),
            "effective_daily_burn": round(effective_daily_burn, 2),
            "days_until_exhaustion": days_left,
            "predicted_exhaustion_date": predicted_date,
            "safe_daily_allowance": safe_daily_allowance,
            "recommended_daily_limit": safe_daily_allowance,
            "remaining_days_in_month": remaining_days_in_month,
            "is_burn_rate_critical": is_critical,
            "daily_trend": daily_trend,
        }


# Aliases khớp 1:1 với Sơ đồ lớp StarUML & Báo cáo
BurnRateForecaster = BurnRateAnalyzer
BurnRatePredictor = BurnRateAnalyzer
