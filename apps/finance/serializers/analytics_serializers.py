"""
Analytics & Machine Learning Response Serializers (OpenAPI 3 / Swagger Documentation).
"""
from rest_framework import serializers


class DailyBurnTrendItemSerializer(serializers.Serializer):
    date = serializers.CharField()
    daily_spent = serializers.FloatField()
    rolling_7d_avg = serializers.FloatField()


class BurnRateResponseSerializer(serializers.Serializer):
    """Schema JSON cho kết quả dự báo ngày cạn tiền (Burn-Rate Forecaster)."""

    current_balance = serializers.FloatField()
    daily_burn_rate = serializers.FloatField()
    average_daily_burn = serializers.FloatField()
    rolling_7d_burn_rate = serializers.FloatField()
    regression_daily_slope = serializers.FloatField()
    effective_daily_burn = serializers.FloatField(required=False)
    days_until_exhaustion = serializers.IntegerField(allow_null=True)
    predicted_exhaustion_date = serializers.CharField(allow_null=True)
    safe_daily_allowance = serializers.FloatField()
    recommended_daily_limit = serializers.FloatField()
    remaining_days_in_month = serializers.IntegerField(required=False)
    is_burn_rate_critical = serializers.BooleanField()
    daily_trend = DailyBurnTrendItemSerializer(many=True)


class AnomalyStatisticsSerializer(serializers.Serializer):
    mean = serializers.FloatField()
    std = serializers.FloatField()
    q1 = serializers.FloatField()
    q3 = serializers.FloatField()
    iqr = serializers.FloatField()
    iqr_upper_bound = serializers.FloatField()


class AnomalyItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    amount = serializers.FloatField()
    z_score = serializers.FloatField()
    category = serializers.CharField()
    note = serializers.CharField()
    transaction_date = serializers.CharField(allow_null=True)


class AnomalyReportResponseSerializer(serializers.Serializer):
    """Schema JSON cho kết quả phát hiện bất thường (Anomaly Detection Engine)."""

    total_analyzed = serializers.IntegerField()
    anomaly_count = serializers.IntegerField()
    statistics = AnomalyStatisticsSerializer()
    anomalies = AnomalyItemSerializer(many=True)


class FinancialHealthResponseSerializer(serializers.Serializer):
    """Schema JSON cho kết quả phân loại rủi ro vỡ ngân sách & chấm điểm sức khỏe tài chính."""

    financial_health_score = serializers.IntegerField()
    risk_level = serializers.CharField()
    risk_probabilities = serializers.DictField(child=serializers.FloatField())
    spending_structure = serializers.DictField()
    saving_recommendation = serializers.DictField()
