"""
7. BudgetAlertLog Model (id, user_id, budget_id, transaction_id, alert_type, message, predicted_exhaustion_date, is_read).
"""
from django.conf import settings
from django.db import models
from core.models import BaseModel


class BudgetAlertLog(BaseModel):
    """
    Bảng 7: BudgetAlertLog - Nhật ký cảnh báo & Dự báo rủi ro tài chính:
    - WARNING_80: Chạm ngưỡng cảnh báo (mặc định 80% ngân sách)
    - CRITICAL / EXCEEDED: Vượt 100% hạn mức ngân sách
    - ANOMALY: Giao dịch chi tiêu bất thường (IsolationForest / Z-Score / IQR)
    - BURN_RATE / BURN_RATE_RISK: Tốc độ đốt tiền nguy cơ cạn ví trước cuối tháng
    """

    class AlertType(models.TextChoices):
        WARNING_80 = "WARNING_80", "Cảnh báo chạm ngưỡng 80% ngân sách"
        CRITICAL = "CRITICAL", "Báo động vượt 100% ngân sách"
        EXCEEDED = "EXCEEDED", "Vượt hạn mức ngân sách"
        ANOMALY = "ANOMALY", "Cảnh báo giao dịch chi tiêu bất thường"
        BURN_RATE = "BURN_RATE", "Cảnh báo tốc độ đốt tiền (Nguy cơ cạn ví sớm)"
        BURN_RATE_RISK = "BURN_RATE_RISK", "Rủi ro cháy túi cuối tháng"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="alert_logs",
    )
    budget = models.ForeignKey(
        "finance.MonthlyBudget",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alert_logs",
    )
    transaction = models.ForeignKey(
        "finance.ExpenseTransaction",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alert_logs",
    )
    alert_type = models.CharField(
        max_length=25,
        choices=AlertType.choices,
        db_index=True,
    )
    message = models.TextField(help_text="Nội dung cảnh báo chi tiết gửi cho sinh viên")
    predicted_exhaustion_date = models.DateField(
        null=True,
        blank=True,
        help_text="Ngày dự kiến cạn ngân sách/ví (nếu là cảnh báo BURN_RATE)",
    )
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = "finance_budget_alert_log"
        verbose_name = "Nhật ký cảnh báo ngân sách"
        verbose_name_plural = "Danh sách cảnh báo ngân sách"

    def __str__(self) -> str:
        return f"[{self.alert_type}] {self.user.email}: {self.message[:50]}"
