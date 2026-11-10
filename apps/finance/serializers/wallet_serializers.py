"""
Wallet & Internal Transfer Serializers (DRF JSON Template Layer).
"""
from decimal import Decimal
from rest_framework import serializers
from apps.finance.models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Serializer cho thông tin Ví tiền sinh viên."""

    wallet_type_display = serializers.CharField(
        source="get_wallet_type_display", read_only=True
    )
    wallet_name = serializers.CharField(source="name", read_only=True)
    current_balance = serializers.DecimalField(
        source="balance", max_digits=15, decimal_places=2, read_only=True
    )

    class Meta:
        model = Wallet
        fields = [
            "id",
            "name",
            "wallet_name",
            "wallet_type",
            "wallet_type_display",
            "balance",
            "current_balance",
            "currency",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "wallet_name",
            "current_balance",
            "created_at",
            "updated_at",
        ]


class WalletTransferSerializer(serializers.Serializer):
    """Serializer kiểm tra dữ liệu đầu vào khi chuyển tiền giữa 2 ví."""

    source_wallet_id = serializers.UUIDField(help_text="UUID của ví nguồn")
    target_wallet_id = serializers.UUIDField(help_text="UUID của ví đích")
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.01"),
        help_text="Số tiền cần chuyển (> 0)",
    )
    note = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        default="",
        help_text="Ghi chú chuyển khoản",
    )
