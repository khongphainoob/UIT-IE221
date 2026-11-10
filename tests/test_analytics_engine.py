"""
Tests for Module 5 (analytics_engine):
BurnRateForecaster (Pandas + HuberRegressor), AnomalyDetectionEngine (IsolationForest + Z-Score),
MLModelRegistry (Singleton), RiskClassifier (RandomForestClassifier + SavingStrategy),
and Report Export (CSV / Excel Strategy Pattern) (5 tests -> Total 20 tests across suite).
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status
from apps.finance.engines import (
    AnomalyDetectionEngine,
    MLModelRegistry,
    RiskClassifier,
)


@pytest.mark.django_db
class TestAnalyticsEngines:
    def test_burn_rate_analyzer_predictions(self, auth_client, historical_transactions):
        response = auth_client.get(reverse("analytics-burn-rate-forecast"))
        assert response.status_code == status.HTTP_200_OK
        data = response.data["data"]
        assert data["current_balance"] == 1500000.0
        assert data["daily_burn_rate"] > 0
        assert data["rolling_7d_burn_rate"] > 0
        assert data["safe_daily_allowance"] > 0
        assert data["recommended_daily_limit"] > 0
        assert data["predicted_exhaustion_date"] is not None
        assert len(data["daily_trend"]) > 0

    def test_anomaly_detection_engine_identifies_outliers(self):
        raw_data = [
            {"id": str(i), "amount": Decimal("40000.00"), "note": "Bình thường"}
            for i in range(15)
        ]
        raw_data.append(
            {"id": "999", "amount": Decimal("950000.00"), "note": "Mua tai nghe"}
        )

        engine = AnomalyDetectionEngine(raw_transactions=raw_data)
        report = engine.run_inference()

        assert report["total_analyzed"] == 16
        assert report["anomaly_count"] == 1
        assert report["anomalies"][0]["id"] == "999"
        assert report["anomalies"][0]["z_score"] > 2.5

    def test_ml_model_registry_singleton_pattern(self):
        reg1 = MLModelRegistry.get_instance()
        reg2 = MLModelRegistry()
        assert reg1 is reg2
        rf_model = reg1.get_model("risk_rf_classifier")
        assert rf_model is not None

    def test_financial_health_score_and_risk_classifier_endpoint(
        self, auth_client, historical_transactions
    ):
        res = auth_client.get(reverse("analytics-financial-health"))
        assert res.status_code == status.HTTP_200_OK
        data = res.data["data"]
        assert 0 <= data["financial_health_score"] <= 100
        assert data["risk_level"] in ("SAFE", "WARNING", "HIGH_RISK_BROKE")
        assert "SAFE" in data["risk_probabilities"]
        assert "strategy_mode" in data["saving_recommendation"]

    def test_export_report_csv_and_xlsx_strategy_pattern(
        self, auth_client, historical_transactions
    ):
        csv_res = auth_client.get(reverse("analytics-export") + "?export_format=csv")
        assert csv_res.status_code == status.HTTP_200_OK
        assert "text/csv" in csv_res["Content-Type"]

        xlsx_res = auth_client.get(reverse("analytics-export") + "?export_format=xlsx")
        assert xlsx_res.status_code == status.HTTP_200_OK
        assert "spreadsheetml" in xlsx_res["Content-Type"]
