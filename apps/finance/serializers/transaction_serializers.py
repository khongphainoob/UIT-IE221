"""
Transaction & Expense Category Serializers (DRF JSON Template Layer).
"""
from rest_framework import serializers
from apps.finance.models import ExpenseCategory, ExpenseTransaction


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer cho Danh mục Thu / Chi."""

    class Meta:
        model = ExpenseCategory
        fields = [
            "id",
            "name",
            "category_type",
            "is_essential",
            "description",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ExpenseTransactionSerializer(serializers.ModelSerializer):
    """Serializer hiển thị và tạo mới Giao dịch tài chính."""

    wallet_name = serializers.CharField(source="wallet.name", read_only=True)
    category_name = serializers.CharField(
        source="category.name", read_only=True, default=None
    )

    class Meta:
        model = ExpenseTransaction
        fields = [
            "id",
            "wallet",
            "wallet_name",
            "category",
            "category_name",
            "transaction_type",
            "amount",
            "transaction_date",
            "note",
            "is_anomaly",
            "anomaly_score",
            "created_at",
        ]
        read_only_fields = ["id", "is_anomaly", "anomaly_score", "created_at"]

