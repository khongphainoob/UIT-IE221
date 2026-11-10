"""
Budget, RecurringBill, and AlertLog Serializers (DRF JSON Template Layer).
"""
from rest_framework import serializers
from apps.finance.models import BudgetAlertLog, MonthlyBudget, RecurringBill


class MonthlyBudgetSerializer(serializers.ModelSerializer):
    """Serializer cho Ngân sách định mức hàng tháng."""

    category_name = serializers.CharField(
        source="category.name", read_only=True, default="Tổng chi tiêu tháng"
    )
    usage_percentage = serializers.FloatField(read_only=True)
    remaining_amount = serializers.DecimalField(
        max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = MonthlyBudget
        fields = [
            "id",
            "category",
            "category_name",
            "month",
            "year",
            "allocated_amount",
            "spent_amount",
            "remaining_amount",
            "alert_threshold_pct",
            "usage_percentage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "spent_amount",
            "remaining_amount",
            "usage_percentage",
            "created_at",
            "updated_at",
        ]


class RecurringBillSerializer(serializers.ModelSerializer):
    """Serializer cho Hóa đơn định kỳ (KTX, 4G, Điện nước)."""

    wallet_name = serializers.CharField(
        source="wallet.name", read_only=True, default=None
    )
    category_name = serializers.CharField(
        source="category.name", read_only=True, default=None
    )

    class Meta:
        model = RecurringBill
        fields = [
            "id",
            "wallet",
            "wallet_name",
            "category",
            "category_name",
            "title",
            "amount",
            "due_day",
            "frequency",
            "auto_deduct",
            "status",
            "last_paid_at",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "last_paid_at", "created_at"]


class BudgetAlertLogSerializer(serializers.ModelSerializer):
    """Serializer cho Nhật ký cảnh báo ngân sách & bất thường."""

    class Meta:
        model = BudgetAlertLog
        fields = [
            "id",
            "budget",
            "transaction",
            "alert_type",
            "message",
            "predicted_exhaustion_date",
            "is_read",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "budget",
            "transaction",
            "alert_type",
            "message",
            "predicted_exhaustion_date",
            "created_at",
        ]
