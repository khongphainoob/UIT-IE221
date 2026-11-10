"""
Budget Service (Business Logic Layer).
Handles monthly budget allocation, cloning previous month's budgets,
threshold checks (WARNING_80, CRITICAL/EXCEEDED), and alert management.
"""
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from apps.finance.models import BudgetAlertLog, ExpenseTransaction, MonthlyBudget
from apps.finance.repositories.budget_repo import BudgetRepository
from apps.finance.repositories.transaction_repo import TransactionRepository
from core.exceptions import BusinessLogicException, ResourceNotFoundException


class BudgetService:
    """Business Logic Service for MonthlyBudget and BudgetAlertLog."""

    def __init__(
        self,
        budget_repo: BudgetRepository | None = None,
        transaction_repo: TransactionRepository | None = None,
    ):
        self.budget_repo = budget_repo or BudgetRepository()
        self.transaction_repo = transaction_repo or TransactionRepository()

    def list_user_budgets(
        self,
        user_id: UUID | str,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ):
        return self.budget_repo.get_user_budgets(
            user_id=user_id, month=month, year=year
        )

    def list_user_alerts(self, user_id: UUID | str):
        return self.budget_repo.get_user_alerts(user_id=user_id)

    @transaction.atomic
    def mark_alert_as_read(
        self, user_id: UUID | str, alert_id: UUID | str
    ) -> BudgetAlertLog:
        alert = (
            BudgetAlertLog.objects.filter(
                id=alert_id, user_id=user_id, is_deleted=False
            )
            .first()
        )
        if not alert:
            raise ResourceNotFoundException(
                f"Không tìm thấy cảnh báo với ID={alert_id}."
            )
        alert.is_read = True
        alert.save(update_fields=["is_read", "updated_at"])
        return alert

    @transaction.atomic
    def create_or_update_budget(
        self, user_id: UUID | str, validated_data: Dict[str, Any]
    ) -> MonthlyBudget:
        month = validated_data["month"]
        year = validated_data["year"]
        category = validated_data.get("category")
        allocated_amount = validated_data["allocated_amount"]
        alert_threshold_pct = validated_data.get("alert_threshold_pct", 80)

        category_id = category.id if category else None
        existing = (
            self.budget_repo.get_queryset()
            .filter(user_id=user_id, month=month, year=year, category_id=category_id)
            .first()
        )

        current_spent = self.transaction_repo.get_monthly_expense_sum(
            user_id=user_id, month=month, year=year, category_id=category_id
        )

        if existing:
            budget = self.budget_repo.update(
                existing,
                allocated_amount=allocated_amount,
                spent_amount=current_spent,
                alert_threshold_pct=alert_threshold_pct,
            )
        else:
            budget = self.budget_repo.create(
                user_id=user_id,
                category=category,
                month=month,
                year=year,
                allocated_amount=allocated_amount,
                spent_amount=current_spent,
                alert_threshold_pct=alert_threshold_pct,
            )

        self.evaluate_budget_thresholds(budget=budget)
        return budget

    @transaction.atomic
    def update_budget_by_id(
        self,
        user_id: UUID | str,
        budget_id: UUID | str,
        validated_data: Dict[str, Any],
    ) -> MonthlyBudget:
        budget = self.budget_repo.get_by_id(record_id=budget_id, user_id=user_id)
        budget = self.budget_repo.update(budget, **validated_data)
        self.evaluate_budget_thresholds(budget=budget)
        return budget

    @transaction.atomic
    def delete_budget_by_id(self, user_id: UUID | str, budget_id: UUID | str) -> None:
        budget = self.budget_repo.get_by_id(record_id=budget_id, user_id=user_id)
        self.budget_repo.soft_delete(budget)

    @transaction.atomic
    def clone_previous_month_budgets(
        self,
        user_id: UUID | str,
        target_month: Optional[int] = None,
        target_year: Optional[int] = None,
    ) -> List[MonthlyBudget]:
        """
        Sao chép cấu hình hạn mức ngân sách của tháng trước sang tháng mới (`target_month`/`target_year`).
        """
        now = timezone.now()
        t_month = target_month or now.month
        t_year = target_year or now.year

        if t_month == 1:
            prev_month, prev_year = 12, t_year - 1
        else:
            prev_month, prev_year = t_month - 1, t_year

        prev_budgets = list(
            self.budget_repo.get_user_budgets(
                user_id=user_id, month=prev_month, year=prev_year
            )
        )
        if not prev_budgets:
            raise BusinessLogicException(
                f"Không tìm thấy cấu hình ngân sách tháng {prev_month}/{prev_year} để sao chép."
            )

        cloned: List[MonthlyBudget] = []
        for pb in prev_budgets:
            budget = self.create_or_update_budget(
                user_id=user_id,
                validated_data={
                    "category": pb.category,
                    "month": t_month,
                    "year": t_year,
                    "allocated_amount": pb.allocated_amount,
                    "alert_threshold_pct": pb.alert_threshold_pct,
                },
            )
            cloned.append(budget)
        return cloned

    @transaction.atomic
    def sync_budgets_on_expense(
        self, expense_tx: ExpenseTransaction
    ) -> List[BudgetAlertLog]:
        tx_date = expense_tx.transaction_date
        matching_budgets = self.budget_repo.find_matching_budgets(
            user_id=expense_tx.user_id,
            month=tx_date.month,
            year=tx_date.year,
            category_id=expense_tx.category_id,
        )

        generated_alerts: List[BudgetAlertLog] = []
        for budget in matching_budgets:
            budget.spent_amount += expense_tx.amount
            budget.save(update_fields=["spent_amount", "updated_at"])
            alert = self.evaluate_budget_thresholds(
                budget=budget, transaction_id=expense_tx.id
            )
            if alert:
                generated_alerts.append(alert)

        return generated_alerts

    def evaluate_budget_thresholds(
        self, budget: MonthlyBudget, transaction_id: Optional[UUID | str] = None
    ) -> Optional[BudgetAlertLog]:
        usage_pct = budget.usage_percentage
        threshold = float(budget.alert_threshold_pct or 80)
        cat_label = budget.category.name if budget.category else "Tổng chi tiêu tháng"

        if usage_pct >= 100.0:
            return self.budget_repo.create_alert(
                user_id=budget.user_id,
                budget_id=budget.id,
                transaction_id=transaction_id,
                alert_type=BudgetAlertLog.AlertType.CRITICAL,
                message=(
                    f"[BÁO ĐỘNG ĐỎ] Ngân sách '{cat_label}' ({budget.month}/{budget.year}) "
                    f"đã vượt hạn mức: {budget.spent_amount:,.0f}/{budget.allocated_amount:,.0f} VNĐ ({usage_pct:.1f}%)."
                ),
            )
        if usage_pct >= threshold:
            return self.budget_repo.create_alert(
                user_id=budget.user_id,
                budget_id=budget.id,
                transaction_id=transaction_id,
                alert_type=BudgetAlertLog.AlertType.WARNING_80,
                message=(
                    f"[CẢNH BÁO {int(threshold)}%] Ngân sách '{cat_label}' ({budget.month}/{budget.year}) "
                    f"đã chạm ngưỡng {usage_pct:.1f}% ({budget.spent_amount:,.0f}/{budget.allocated_amount:,.0f} VNĐ)."
                ),
            )
        return None
