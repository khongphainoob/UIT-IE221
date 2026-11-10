"""
Wallet Service (Business Logic Layer).
Enforces @transaction.atomic for all wallet balance mutations, CRUD, and internal transfers.
"""
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from apps.finance.models import ExpenseTransaction, Wallet
from apps.finance.repositories.transaction_repo import TransactionRepository
from apps.finance.repositories.wallet_repo import WalletRepository
from core.exceptions import BusinessLogicException, InsufficientBalanceException


class WalletService:
    """Business Logic Service for Wallet operations and atomic internal transfers."""

    def __init__(
        self,
        wallet_repo: WalletRepository | None = None,
        transaction_repo: TransactionRepository | None = None,
    ):
        self.wallet_repo = wallet_repo or WalletRepository()
        self.transaction_repo = transaction_repo or TransactionRepository()

    def list_user_wallets(self, user_id: UUID | str):
        return self.wallet_repo.get_user_wallets(user_id=user_id)

    def get_wallet_detail(self, user_id: UUID | str, wallet_id: UUID | str) -> Wallet:
        return self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=wallet_id
        )

    @transaction.atomic
    def create_wallet(
        self, user_id: UUID | str, validated_data: Dict[str, Any]
    ) -> Wallet:
        return self.wallet_repo.create(user_id=user_id, **validated_data)

    @transaction.atomic
    def update_wallet(
        self,
        user_id: UUID | str,
        wallet_id: UUID | str,
        validated_data: Dict[str, Any],
    ) -> Wallet:
        wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=wallet_id, for_update=True
        )
        return self.wallet_repo.update(wallet, **validated_data)

    @transaction.atomic
    def delete_wallet(self, user_id: UUID | str, wallet_id: UUID | str) -> None:
        wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=wallet_id, for_update=True
        )
        self.wallet_repo.soft_delete(wallet)

    @transaction.atomic
    def transfer_between_wallets(
        self,
        user_id: UUID | str,
        source_wallet_id: UUID | str,
        target_wallet_id: UUID | str,
        amount: Decimal,
        note: str = "",
    ) -> Dict[str, Any]:
        """
        Thực hiện chuyển tiền nội bộ giữa 2 ví của sinh viên (VD: Ngân hàng -> MoMo/Tiền mặt).
        Sử dụng `@transaction.atomic` và `select_for_update()` để chống Race Condition.
        """
        if str(source_wallet_id) == str(target_wallet_id):
            raise BusinessLogicException("Ví nguồn và ví đích không được trùng nhau.")

        if amount <= Decimal("0.00"):
            raise BusinessLogicException("Số tiền chuyển khoản phải lớn hơn 0.")

        source_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=source_wallet_id, for_update=True
        )
        target_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=target_wallet_id, for_update=True
        )

        if source_wallet.balance < amount:
            raise InsufficientBalanceException(
                f"Số dư ví nguồn '{source_wallet.name}' ({source_wallet.balance:,.0f} VNĐ) "
                f"không đủ để chuyển {amount:,.0f} VNĐ."
            )

        source_wallet.balance -= amount
        target_wallet.balance += amount
        source_wallet.save(update_fields=["balance", "updated_at"])
        target_wallet.save(update_fields=["balance", "updated_at"])

        transfer_note = (
            note or f"Chuyển tiền từ {source_wallet.name} sang {target_wallet.name}"
        )
        tx_record = self.transaction_repo.create(
            user_id=user_id,
            wallet=source_wallet,
            transaction_type=ExpenseTransaction.TransactionType.TRANSFER,
            amount=amount,
            transaction_date=timezone.now(),
            note=transfer_note,
        )

        return {
            "transaction": tx_record,
            "source_wallet": source_wallet,
            "target_wallet": target_wallet,
        }
