"""
Wallet Repository (Data Access Layer).
Handles ORM queries, aggregations, and row-level locking (`select_for_update`) for Wallet.
"""
from decimal import Decimal
from uuid import UUID
from django.db.models import QuerySet, Sum
from apps.finance.models import Wallet
from core.exceptions import ResourceNotFoundException
from core.repositories import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    """Data Access Layer for Wallet model."""

    model_class = Wallet

    def get_user_wallets(self, user_id: UUID | str) -> QuerySet[Wallet]:
        """Return all active wallets belonging to a student."""
        return self.get_queryset().filter(user_id=user_id).order_by("created_at")

    def get_user_wallet_by_id(
        self, user_id: UUID | str, wallet_id: UUID | str, for_update: bool = False
    ) -> Wallet:
        """
        Retrieve a specific wallet owned by `user_id`.
        Uses `select_for_update()` when `for_update=True` inside `@transaction.atomic`.
        """
        qs = self.get_queryset().filter(user_id=user_id, id=wallet_id)
        if for_update:
            qs = qs.select_for_update()
        wallet = qs.first()
        if not wallet:
            raise ResourceNotFoundException(
                f"Không tìm thấy Ví (ID={wallet_id}) thuộc quyền sở hữu của bạn."
            )
        return wallet

    def get_total_balance(self, user_id: UUID | str) -> Decimal:
        """Aggregate total balance across all active wallets of a student."""
        result = self.get_user_wallets(user_id).aggregate(total=Sum("balance"))
        return result["total"] or Decimal("0.00")

