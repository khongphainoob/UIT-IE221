"""
4. MonthlyBudget Model (id, user_id, category_id, month, year, allocated_amount, spent_amount, alert_threshold_pct).
"""
from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from core.models import BaseModel


class MonthlyBudget(BaseModel):
    """
    Bảng 4: MonthlyBudget - Hạn mức ngân sách theo tháng của sinh viên.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_budgets",
    )
    category = models.ForeignKey(
        "finance.ExpenseCategory",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="budgets",
        help_text="Danh mục áp dụng ngân sách (Null = Ngân sách tổng cả tháng)",
    )
    month = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Tháng áp dụng (1 - 12)",
    )
    year = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(2020), MaxValueValidator(2100)],
        help_text="Năm áp dụng (VD: 2026)",
    )
    allocated_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Hạn mức ngân sách được cấp/đặt ra trong tháng",
    )
    spent_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Số tiền đã chi tiêu lũy kế trong tháng",
    )
    alert_threshold_pct = models.PositiveSmallIntegerField(
        default=80,
        validators=[MinValueValidator(10), MaxValueValidator(100)],
        help_text="Ngưỡng phần trăm cảnh báo ngân sách (mặc định 80%)",
    )

    class Meta:
        db_table = "finance_monthly_budget"
        verbose_name = "Ngân sách tháng"
        verbose_name_plural = "Danh sách ngân sách tháng"
        unique_together = ("user", "category", "month", "year")

    @property
    def usage_percentage(self) -> float:
        """Tỷ lệ phần trăm ngân sách đã sử dụng."""
        if not self.allocated_amount or self.allocated_amount <= 0:
            return 0.0
        return round(float((self.spent_amount / self.allocated_amount) * Decimal("100.0")), 2)

    @property
    def remaining_amount(self) -> Decimal:
        """Số dư ngân sách còn lại trong tháng."""
        return max(self.allocated_amount - self.spent_amount, Decimal("0.00"))

    def __str__(self) -> str:
        cat_name = self.category.name if self.category else "Tổng tháng"
        return f"Budget {self.month}/{self.year} [{cat_name}]: {self.spent_amount:,.0f}/{self.allocated_amount:,.0f}"
