"""
5. ExpenseTransaction Model (amount, is_anomaly).
[DESIGN HOOK - ERD / CLASS DIAGRAM]: Gửi thiết kế chi tiết bảng ExpenseTransaction của bạn để tinh chỉnh thêm nếu cần.
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class ExpenseTransaction(BaseModel):
    """
    Model lưu trữ từng giao dịch thu/chi của sinh viên.
    Tích hợp cờ `is_anomaly` phục vụ Anomaly Detection Engine (Z-Score / IQR).
    """

    class TransactionType(models.TextChoices):
        EXPENSE = "EXPENSE", "Chi tiêu"
        INCOME = "INCOME", "Thu nhập"
        TRANSFER = "TRANSFER", "Chuyển khoản nội bộ"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    wallet = models.ForeignKey(
        "finance.Wallet",
        on_delete=models.CASCADE,
        related_name="transactions",
        help_text="Ví nguồn thực hiện giao dịch",
    )
    category = models.ForeignKey(
        "finance.ExpenseCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.EXPENSE,
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Số tiền giao dịch (> 0)",
    )
    transaction_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Thời điểm phát sinh giao dịch",
    )
    note = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Ghi chú chi tiết giao dịch (VD: Cơm trưa Làng Đại học)",
    )
    is_anomaly = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Cờ đánh dấu giao dịch bất thường bởi AnomalyEngine (Z-Score / IQR)",
    )
    anomaly_score = models.FloatField(
        default=0.0,
        help_text="Điểm số bất thường (Z-Score hoặc độ lệch IQR)",
    )

    class Meta:
        db_table = "finance_expense_transaction"
        verbose_name = "Giao dịch tài chính"
        verbose_name_plural = "Danh sách giao dịch"
        ordering = ["-transaction_date", "-created_at"]

    def __str__(self) -> str:
        flag = " [ANOMALY]" if self.is_anomaly else ""
        return f"{self.transaction_type} - {self.amount:,.0f} VND ({self.transaction_date:%Y-%m-%d}){flag}"

