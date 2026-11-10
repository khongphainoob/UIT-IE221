"""
Transaction Repository (Data Access Layer).
Handles optimized queries with `select_related`, advanced filtering, and DataFrame extraction.
"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID
from django.db.models import Q, QuerySet, Sum
from apps.finance.models import ExpenseTransaction
from core.repositories import BaseRepository


class TransactionRepository(BaseRepository[ExpenseTransaction]):
    """Data Access Layer for ExpenseTransaction model."""

    model_class = ExpenseTransaction

    def get_user_transactions(
        self,
        user_id: UUID | str,
        wallet_id: Optional[UUID | str] = None,
        category_id: Optional[UUID | str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime | str] = None,
        end_date: Optional[datetime | str] = None,
        min_amount: Optional[Decimal | float | str] = None,
        max_amount: Optional[Decimal | float | str] = None,
        is_anomaly: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> QuerySet[ExpenseTransaction]:
        """Return optimized queryset with `select_related` and advanced multi-criteria filtering."""
        qs = (
            self.get_queryset()
            .select_related("wallet", "category")
            .filter(user_id=user_id)
        )
        if wallet_id:
            qs = qs.filter(wallet_id=wallet_id)
        if category_id:
            qs = qs.filter(category_id=category_id)
        if transaction_type:
            qs = qs.filter(transaction_type=transaction_type)
        if start_date:
            qs = qs.filter(transaction_date__gte=start_date)
        if end_date:
            qs = qs.filter(transaction_date__lte=end_date)
        if min_amount is not None and min_amount != "":
            qs = qs.filter(amount__gte=Decimal(str(min_amount)))
        if max_amount is not None and max_amount != "":
            qs = qs.filter(amount__lte=Decimal(str(max_amount)))
        if is_anomaly is not None:
            qs = qs.filter(is_anomaly=is_anomaly)
        if search:
            qs = qs.filter(
                Q(note__icontains=search) | Q(category__name__icontains=search)
            )
        return qs.order_by("-transaction_date", "-created_at")

    def get_expense_records_for_analytics(
        self,
        user_id: UUID | str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch flat dictionaries of EXPENSE transactions for Pandas Analytics Engines.
        """
        qs = self.get_user_transactions(
            user_id=user_id,
            transaction_type=ExpenseTransaction.TransactionType.EXPENSE,
            start_date=start_date,
            end_date=end_date,
        )
        return list(
            qs.values(
                "id",
                "amount",
                "transaction_date",
                "category_id",
                "category__name",
                "category__is_essential",
                "wallet_id",
                "wallet__name",
                "note",
                "is_anomaly",
                "anomaly_score",
            )
        )

    def get_monthly_expense_sum(
        self,
        user_id: UUID | str,
        month: int,
        year: int,
        category_id: Optional[UUID | str] = None,
    ) -> Decimal:
        """Aggregate total expense amount for a given user, month, year, and optional category."""
        qs = self.get_queryset().filter(
            user_id=user_id,
            transaction_type=ExpenseTransaction.TransactionType.EXPENSE,
            transaction_date__month=month,
            transaction_date__year=year,
        )
        if category_id:
            qs = qs.filter(category_id=category_id)
        result = qs.aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")
