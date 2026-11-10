"""
Budget & Alert Repository (Data Access Layer).
Handles ORM queries for MonthlyBudget, ExpenseCategory, RecurringBill, and BudgetAlertLog.
"""
from typing import Optional
from uuid import UUID
from django.db.models import Q, QuerySet
from apps.finance.models import (
    BudgetAlertLog,
    ExpenseCategory,
    MonthlyBudget,
    RecurringBill,
)
from core.repositories import BaseRepository


class BudgetRepository(BaseRepository[MonthlyBudget]):
    """Data Access Layer for MonthlyBudget and related budget entities."""

    model_class = MonthlyBudget

    def get_user_budgets(
        self,
        user_id: UUID | str,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> QuerySet[MonthlyBudget]:
        qs = self.get_queryset().select_related("category").filter(user_id=user_id)
        if month:
            qs = qs.filter(month=month)
        if year:
            qs = qs.filter(year=year)
        return qs.order_by("-year", "-month")

    def find_matching_budgets(
        self, user_id: UUID | str, month: int, year: int, category_id: Optional[UUID | str] = None
    ) -> QuerySet[MonthlyBudget]:
        """
        Find both the overall monthly budget (category=None) and the specific category budget
        for a given (user, month, year).
        """
        condition = Q(category__isnull=True)
        if category_id:
            condition |= Q(category_id=category_id)
        return (
            self.get_queryset()
            .select_for_update()
            .filter(user_id=user_id, month=month, year=year)
            .filter(condition)
        )

    def get_available_categories(self, user_id: UUID | str) -> QuerySet[ExpenseCategory]:
        """Return system-wide categories (user=None) plus custom categories of this student."""
        return ExpenseCategory.objects.filter(
            Q(user__isnull=True) | Q(user_id=user_id),
            is_deleted=False,
        ).order_by("category_type", "name")

    def get_user_alerts(self, user_id: UUID | str) -> QuerySet[BudgetAlertLog]:
        """Return budget and anomaly alerts for the student."""
        return (
            BudgetAlertLog.objects.select_related("budget", "transaction")
            .filter(user_id=user_id, is_deleted=False)
            .order_by("-created_at")
        )

    def create_alert(
        self,
        user_id: UUID | str,
        alert_type: str,
        message: str,
        budget_id: Optional[UUID | str] = None,
        transaction_id: Optional[UUID | str] = None,
    ) -> BudgetAlertLog:
        """Create a new BudgetAlertLog entry."""
        return BudgetAlertLog.objects.create(
            user_id=user_id,
            alert_type=alert_type,
            message=message,
            budget_id=budget_id,
            transaction_id=transaction_id,
        )

    def get_active_recurring_bills(self, user_id: UUID | str) -> QuerySet[RecurringBill]:
        """Return active recurring bills for the student."""
        return RecurringBill.objects.select_related("wallet", "category").filter(
            user_id=user_id, is_active=True, is_deleted=False
        )

