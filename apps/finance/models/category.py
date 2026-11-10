"""
3. ExpenseCategory Model (EXPENSE/INCOME, is_essential).
[DESIGN HOOK - ERD / CLASS DIAGRAM]: Có thể bổ sung icon, color_code hoặc parent_category theo thiết kế của bạn.
"""
from django.conf import settings
from django.db import models
from core.models import BaseModel


class ExpenseCategory(BaseModel):
    """
    Model phân loại danh mục Thu / Chi (VD: Ăn uống căn tin, Tiền trọ KTX, Học phí, Học bổng).
    """

    class CategoryType(models.TextChoices):
        EXPENSE = "EXPENSE", "Khoản chi"
        INCOME = "INCOME", "Khoản thu"

    name = models.CharField(max_length=100, help_text="Tên danh mục (VD: Ăn uống, Di chuyển, Học bổng)")
    category_type = models.CharField(
        max_length=20,
        choices=CategoryType.choices,
        default=CategoryType.EXPENSE,
        db_index=True,
    )
    is_essential = models.BooleanField(
        default=True,
        help_text="Phân loại chi tiêu thiết yếu (True) hay giải trí/không thiết yếu (False)",
    )
    description = models.TextField(blank=True, default="")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories",
        help_text="Null nếu là danh mục mặc định toàn hệ thống, hoặc gắn với sinh viên tạo riêng",
    )

    class Meta:
        db_table = "finance_expense_category"
        verbose_name = "Danh mục thu chi"
        verbose_name_plural = "Danh sách danh mục"

    def __str__(self) -> str:
        return f"{self.name} ({self.category_type})"

