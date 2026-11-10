"""
2. Wallet Model (id, user_id, name/wallet_name: Tiền mặt/MoMo/Ngân hàng, balance/current_balance, currency).
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from core.models import BaseModel


class Wallet(BaseModel):
    """
    Bảng 2: Wallet - Ví/Nguồn tiền của sinh viên (Tiền mặt, MoMo, Ngân hàng).
    Ràng buộc toàn vẹn: balance >= 0.
    """

    class WalletType(models.TextChoices):
        CASH = "CASH", "Tiền mặt"
        MOMO = "MOMO", "Ví MoMo"
        BANK = "BANK", "Tài khoản Ngân hàng"
        OTHER = "OTHER", "Ví khác"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wallets",
        help_text="Chủ sở hữu ví",
    )
    name = models.CharField(
        max_length=100,
        help_text="Tên hiển thị của ví (VD: Tiền mặt, Ví MoMo, Vietcombank)",
    )
    wallet_type = models.CharField(
        max_length=20,
        choices=WalletType.choices,
        default=WalletType.CASH,
    )
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Số dư hiện tại (VNĐ), luôn >= 0",
    )
    currency = models.CharField(max_length=10, default="VND")
    is_active = models.BooleanField(default=True, help_text="Trạng thái kích hoạt ví")

    class Meta:
        db_table = "finance_wallet"
        verbose_name = "Ví tiền"
        verbose_name_plural = "Danh sách ví tiền"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=Decimal("0.00")),
                name="check_wallet_balance_non_negative",
            )
        ]

    @property
    def wallet_name(self) -> str:
        """Alias tương thích 1:1 với đặc tả ERD (`wallet_name`)."""
        return self.name

    @property
    def current_balance(self) -> Decimal:
        """Alias tương thích 1:1 với đặc tả ERD (`current_balance`)."""
        return self.balance

    def __str__(self) -> str:
        return f"{self.name} ({self.get_wallet_type_display()}): {self.balance:,.0f} {self.currency}"
