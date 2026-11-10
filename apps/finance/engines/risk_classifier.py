"""
3. RiskClassifier & Financial Health Scoring Engine + SavingStrategy (Polymorphism / Strategy Pattern).
Uses `MLModelRegistry` (Singleton) to run `RandomForestClassifier.predict_proba()`.
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List
import numpy as np
import pandas as pd
from apps.finance.engines.base_analyzer import BaseFinancialAnalyzer
from apps.finance.engines.burn_rate_engine import BurnRateAnalyzer
from apps.finance.engines.model_registry import MLModelRegistry


class SavingStrategy(ABC):
    """
    Strategy Pattern (Đa hình - Polymorphism) cho Khuyến nghị & Cảnh báo chi tiêu sinh viên.
    """

    @abstractmethod
    def build_recommendation(
        self, safe_daily_allowance: float, non_essential_pct: float
    ) -> Dict[str, Any]:
        raise NotImplementedError


class BalancedEarlyMonthStrategy(SavingStrategy):
    """Chiến lược Chi tiêu cân bằng (khi ngân sách và tốc độ đốt tiền đang trong ngưỡng an toàn)."""

    def build_recommendation(
        self, safe_daily_allowance: float, non_essential_pct: float
    ) -> Dict[str, Any]:
        return {
            "strategy_mode": "BALANCED_ALLOCATION",
            "title": "Chế độ Chi tiêu Cân bằng (Quy tắc 50/30/20 Sinh viên)",
            "recommended_daily_cap": round(safe_daily_allowance, 2),
            "action_items": [
                f"Duy trì hạn mức chi tiêu dưới {safe_daily_allowance:,.0f} VNĐ/ngày.",
                f"Tỷ trọng giải trí/không thiết yếu hiện tại là {non_essential_pct:.1f}% (Mức khuyến nghị < 30%).",
                "Ưu tiên trích trước khoản tiền phòng KTX và gói cước 4G đầu tháng.",
            ],
        }


class EmergencyEndOfMonthStrategy(SavingStrategy):
    """Chiến lược Tiết kiệm khẩn cấp cuối tháng (khi nguy cơ vỡ ngân sách / cháy túi cao)."""

    def build_recommendation(
        self, safe_daily_allowance: float, non_essential_pct: float
    ) -> Dict[str, Any]:
        strict_cap = round(safe_daily_allowance * 0.75, 2)
        return {
            "strategy_mode": "EMERGENCY_SURVIVAL",
            "title": "Chế độ Tiết kiệm Khẩn cấp Cuối tháng (Cắt giảm 100% khoản không thiết yếu)",
            "recommended_daily_cap": strict_cap,
            "action_items": [
                f"Giới hạn nghiêm ngặt chi tiêu ăn uống cơ bản tối đa {strict_cap:,.0f} VNĐ/ngày (Căn tin UIT / Tự nấu).",
                f"Tạm dừng toàn bộ chi tiêu Giải trí/Trà sữa (đang chiếm {non_essential_pct:.1f}% tổng chi).",
                "Sử dụng xe buýt/Metro thay vì đặt xe công nghệ để bảo toàn số dư ví đến cuối tháng.",
            ],
        }


class RiskClassifier(BaseFinancialAnalyzer):
    """
    Module Ăn Điểm 3: Phân loại Rủi ro Vỡ Ngân sách Cuối tháng (`RiskClassifier`).
    - Nạp `RandomForestClassifier` 1 lần qua `MLModelRegistry` (Singleton Pattern).
    - Dự báo nhãn: `SAFE`, `WARNING`, `HIGH_RISK_BROKE` kèm xác suất `predict_proba()`.
    - Chấm điểm sức khỏe tài chính sinh viên (`financial_health_score` trên thang 0 - 100).
    - Áp dụng Strategy Pattern (`SavingStrategy`) để sinh khuyến nghị hành động.
    """

    RISK_LABELS = {
        0: "SAFE",
        1: "WARNING",
        2: "HIGH_RISK_BROKE",
    }

    def __init__(
        self,
        raw_transactions: List[Dict[str, Any]],
        current_balance: Decimal | float,
        monthly_budget_limit: Decimal | float = Decimal("4500000.00"),
    ):
        super().__init__(raw_transactions)
        self._current_balance: float = float(current_balance)
        self._monthly_budget_limit: float = max(float(monthly_budget_limit), 1.0)

    def preprocess(self) -> pd.DataFrame:
        if not self._raw_data:
            self._dataframe = pd.DataFrame(
                columns=[
                    "amount",
                    "transaction_date",
                    "category__is_essential",
                    "is_anomaly",
                ]
            )
            self._is_preprocessed = True
            return self._dataframe

        df = pd.DataFrame(self._raw_data)
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
        if "category__is_essential" not in df.columns:
            df["category__is_essential"] = True
        else:
            df["category__is_essential"] = df["category__is_essential"].fillna(True)
        if "is_anomaly" not in df.columns:
            df["is_anomaly"] = False
        self._dataframe = df
        self._is_preprocessed = True
        return self._dataframe

    def execute_analysis(self) -> Dict[str, Any]:
        burn_analyzer = BurnRateAnalyzer(
            raw_transactions=self._raw_data,
            current_balance=self._current_balance,
        )
        burn_report = burn_analyzer.run()

        df = self._dataframe
        total_spent = float(df["amount"].sum()) if not df.empty else 0.0
        essential_spent = (
            float(df[df["category__is_essential"] == True]["amount"].sum())  # noqa: E712
            if not df.empty
            else 0.0
        )
        non_essential_spent = max(total_spent - essential_spent, 0.0)

        essential_pct = (
            round((essential_spent / total_spent) * 100.0, 2)
            if total_spent > 0
            else 100.0
        )
        non_essential_pct = (
            round((non_essential_spent / total_spent) * 100.0, 2)
            if total_spent > 0
            else 0.0
        )

        budget_usage_ratio = total_spent / self._monthly_budget_limit
        safe_allowance = max(float(burn_report["safe_daily_allowance"]), 1.0)
        burn_to_allowance_ratio = float(burn_report["daily_burn_rate"]) / safe_allowance
        non_essential_ratio = non_essential_spent / max(total_spent, 1.0)
        anomaly_ratio = (
            float(df["is_anomaly"].sum()) / len(df) if not df.empty else 0.0
        )

        # Inference qua Singleton MLModelRegistry (RandomForestClassifier)
        registry = MLModelRegistry.get_instance()
        rf_model = registry.get_model("risk_rf_classifier")
        feature_vector = np.array(
            [
                [
                    budget_usage_ratio,
                    burn_to_allowance_ratio,
                    non_essential_ratio,
                    anomaly_ratio,
                ]
            ],
            dtype=float,
        )
        pred_class = int(rf_model.predict(feature_vector)[0])
        proba = rf_model.predict_proba(feature_vector)[0]
        risk_label = self.RISK_LABELS.get(pred_class, "WARNING")

        # Tính điểm sức khỏe tài chính (Financial Health Score: 0 - 100)
        raw_score = (
            100.0
            - min(budget_usage_ratio * 35.0, 45.0)
            - min(max(burn_to_allowance_ratio - 0.8, 0.0) * 25.0, 30.0)
            - min(non_essential_ratio * 20.0, 15.0)
            - min(anomaly_ratio * 50.0, 10.0)
        )
        health_score = int(np.clip(round(raw_score), 0, 100))

        # Chọn SavingStrategy (Polymorphism) dựa trên mức độ rủi ro
        strategy: SavingStrategy = (
            EmergencyEndOfMonthStrategy()
            if risk_label in ("WARNING", "HIGH_RISK_BROKE") or health_score < 60
            else BalancedEarlyMonthStrategy()
        )
        recommendation = strategy.build_recommendation(
            safe_daily_allowance=float(burn_report["safe_daily_allowance"]),
            non_essential_pct=non_essential_pct,
        )

        return {
            "financial_health_score": health_score,
            "risk_level": risk_label,
            "risk_probabilities": {
                "SAFE": round(float(proba[0]), 4),
                "WARNING": round(float(proba[1]), 4),
                "HIGH_RISK_BROKE": round(float(proba[2]), 4),
            },
            "spending_structure": {
                "total_spent": round(total_spent, 2),
                "essential_spent": round(essential_spent, 2),
                "non_essential_spent": round(non_essential_spent, 2),
                "essential_percentage": essential_pct,
                "non_essential_percentage": non_essential_pct,
            },
            "saving_recommendation": recommendation,
        }

