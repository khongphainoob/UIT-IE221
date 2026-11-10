"""
6. RecurringBill Model (id, user_id, wallet_id, category_id, title: Tiền phòng KTX/Internet, amount, due_day, auto_deduct, status).
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from core.models import BaseModel


class RecurringBill(BaseModel):
    """
    Bảng 6: RecurringBill - Hóa đơn cố định hàng tháng tại KTX (Tiền phòng KTX, Điện nước, Internet/4G).
    """

    class Frequency(models.TextChoices):
        MONTHLY = "MONTHLY", "Hàng tháng"
        QUARTERLY = "QUARTERLY", "Hàng quý"
        SEMESTER = "SEMESTER", "Theo học kỳ"

    class BillStatus(models.TextChoices):
        PENDING = "PENDING", "Chờ thanh toán"
        PAID = "PAID", "Đã thanh toán kỳ này"
        OVERDUE = "OVERDUE", "Quá hạn thanh toán"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_bills",
    )
    wallet = models.ForeignKey(
        "finance.Wallet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_bills",
        help_text="Ví mặc định dùng để thanh toán hóa đơn",
    )
    category = models.ForeignKey(
        "finance.ExpenseCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recurring_bills",
    )
    title = models.CharField(
        max_length=120,
        help_text="Tên hóa đơn định kỳ (VD: Tiền phòng KTX Khu B, Gói 4G Viettel)",
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    due_day = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Ngày đến hạn thanh toán hàng tháng (1 - 31)",
    )
    frequency = models.CharField(
        max_length=20,
        choices=Frequency.choices,
        default=Frequency.MONTHLY,
    )
    auto_deduct = models.BooleanField(
        default=False,
        help_text="Tự động khấu trừ vào ví khi đến hạn thanh toán",
    )
    status = models.CharField(
        max_length=20,
        choices=BillStatus.choices,
        default=BillStatus.PENDING,
        db_index=True,
    )
    last_paid_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "finance_recurring_bill"
        verbose_name = "Hóa đơn định kỳ"
        verbose_name_plural = "Danh sách hóa đơn định kỳ"

    def __str__(self) -> str:
        return f"{self.title} - {self.amount:,.0f} VND (Ngày {self.due_day} - {self.status})"
