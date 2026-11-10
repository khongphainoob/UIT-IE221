"""
Transaction Service (Business Logic Layer).
Coordinates atomic balance deduction/addition, AnomalyDetectionEngine evaluation,
Budget threshold synchronization, transaction updates/soft-deletes, and RecurringBill payments.
"""
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID
from django.db import transaction
from django.utils import timezone
from apps.finance.engines.anomaly_engine import AnomalyDetectionEngine
from apps.finance.models import BudgetAlertLog, ExpenseTransaction, RecurringBill
from apps.finance.repositories.budget_repo import BudgetRepository
from apps.finance.repositories.transaction_repo import TransactionRepository
from apps.finance.repositories.wallet_repo import WalletRepository
from apps.finance.services.budget_service import BudgetService
from core.exceptions import (
    BusinessLogicException,
    InsufficientBalanceException,
    ResourceNotFoundException,
)


class TransactionService:
    """
    Business Logic Service for ExpenseTransaction & RecurringBill payment execution.
    Ensures ACID financial consistency via `@transaction.atomic`.
    """

    def __init__(
        self,
        transaction_repo: TransactionRepository | None = None,
        wallet_repo: WalletRepository | None = None,
        budget_repo: BudgetRepository | None = None,
        budget_service: BudgetService | None = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository()
        self.wallet_repo = wallet_repo or WalletRepository()
        self.budget_repo = budget_repo or BudgetRepository()
        self.budget_service = budget_service or BudgetService(
            budget_repo=self.budget_repo, transaction_repo=self.transaction_repo
        )

    def list_user_transactions(self, user_id: UUID | str, **filters: Any):
        return self.transaction_repo.get_user_transactions(user_id=user_id, **filters)

    @transaction.atomic
    def record_transaction(
        self, user_id: UUID | str, validated_data: Dict[str, Any]
    ) -> ExpenseTransaction:
        """
        Ghi nhận một giao dịch mới (EXPENSE hoặc INCOME):
        1. Khóa bản ghi Ví (`select_for_update`) và kiểm tra/cập nhật số dư.
        2. Chạy `AnomalyDetectionEngine` nếu là khoản chi (`EXPENSE`) để gắn cờ `is_anomaly`.
        3. Lưu giao dịch vào Database.
        4. Đồng bộ `MonthlyBudget` và tạo `BudgetAlertLog` nếu phát hiện bất thường hoặc vượt ngân sách.
        """
        wallet_obj = validated_data["wallet"]
        tx_type = validated_data.get(
            "transaction_type", ExpenseTransaction.TransactionType.EXPENSE
        )
        amount: Decimal = validated_data["amount"]
        tx_date = validated_data.get("transaction_date") or timezone.now()
        category = validated_data.get("category")
        note = validated_data.get("note", "")

        locked_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=wallet_obj.id, for_update=True
        )

        is_anomaly = False
        anomaly_score = 0.0

        if tx_type == ExpenseTransaction.TransactionType.EXPENSE:
            if locked_wallet.balance < amount:
                raise InsufficientBalanceException(
                    f"Số dư ví '{locked_wallet.name}' ({locked_wallet.balance:,.0f} VNĐ) "
                    f"không đủ để chi tiêu {amount:,.0f} VNĐ."
                )
            historical_records = self.transaction_repo.get_expense_records_for_analytics(
                user_id=user_id
            )
            anomaly_engine = AnomalyDetectionEngine(raw_transactions=historical_records)
            is_anomaly, anomaly_score = anomaly_engine.evaluate_single_transaction(
                candidate_amount=amount
            )
            locked_wallet.balance -= amount
        elif tx_type == ExpenseTransaction.TransactionType.INCOME:
            locked_wallet.balance += amount

        locked_wallet.save(update_fields=["balance", "updated_at"])

        tx_instance = self.transaction_repo.create(
            user_id=user_id,
            wallet=locked_wallet,
            category=category,
            transaction_type=tx_type,
            amount=amount,
            transaction_date=tx_date,
            note=note,
            is_anomaly=is_anomaly,
            anomaly_score=anomaly_score,
        )

        if tx_type == ExpenseTransaction.TransactionType.EXPENSE:
            self.budget_service.sync_budgets_on_expense(expense_tx=tx_instance)
            if is_anomaly:
                self.budget_repo.create_alert(
                    user_id=user_id,
                    transaction_id=tx_instance.id,
                    alert_type=BudgetAlertLog.AlertType.ANOMALY,
                    message=(
                        f"[PHÁT HIỆN BẤT THƯỜNG] Khoản chi {amount:,.0f} VNĐ ({note or 'Không ghi chú'}) "
                        f"vượt ngưỡng phân phối lịch sử (Z-Score={anomaly_score:.2f})."
                    ),
                )

        return tx_instance

    @transaction.atomic
    def update_transaction(
        self,
        user_id: UUID | str,
        transaction_id: UUID | str,
        validated_data: Dict[str, Any],
    ) -> ExpenseTransaction:
        """
        Cập nhật số tiền / ghi chú / danh mục giao dịch và đồng bộ lại số dư ví một cách nguyên tử.
        """
        tx_instance = self.transaction_repo.get_by_id(
            record_id=transaction_id, user_id=user_id
        )
        locked_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=tx_instance.wallet_id, for_update=True
        )

        old_amount = tx_instance.amount
        new_amount = validated_data.get("amount", old_amount)
        diff = new_amount - old_amount

        if diff != Decimal("0.00"):
            if tx_instance.transaction_type == ExpenseTransaction.TransactionType.EXPENSE:
                if diff > Decimal("0.00") and locked_wallet.balance < diff:
                    raise InsufficientBalanceException(
                        "Số dư ví không đủ để tăng giá trị khoản chi tiêu này."
                    )
                locked_wallet.balance -= diff
            elif tx_instance.transaction_type == ExpenseTransaction.TransactionType.INCOME:
                if diff < Decimal("0.00") and locked_wallet.balance < abs(diff):
                    raise InsufficientBalanceException(
                        "Số dư ví hiện tại không đủ để giảm khoản thu này."
                    )
                locked_wallet.balance += diff
            locked_wallet.save(update_fields=["balance", "updated_at"])

        for field in ("amount", "note", "category", "transaction_date"):
            if field in validated_data:
                setattr(tx_instance, field, validated_data[field])
        tx_instance.save()
        return tx_instance

    @transaction.atomic
    def delete_transaction(self, user_id: UUID | str, transaction_id: UUID | str) -> None:
        """
        Xóa mềm (Soft Delete) giao dịch và hoàn trả lại số dư ví tương ứng.
        """
        tx_instance = self.transaction_repo.get_by_id(
            record_id=transaction_id, user_id=user_id
        )
        locked_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=tx_instance.wallet_id, for_update=True
        )

        if tx_instance.transaction_type == ExpenseTransaction.TransactionType.EXPENSE:
            locked_wallet.balance += tx_instance.amount
        elif tx_instance.transaction_type == ExpenseTransaction.TransactionType.INCOME:
            if locked_wallet.balance < tx_instance.amount:
                raise InsufficientBalanceException(
                    "Không thể xóa khoản thu vì số dư ví hiện tại thấp hơn số tiền thu hồi."
                )
            locked_wallet.balance -= tx_instance.amount

        locked_wallet.save(update_fields=["balance", "updated_at"])
        self.transaction_repo.soft_delete(tx_instance)

    @transaction.atomic
    def pay_recurring_bill(
        self,
        user_id: UUID | str,
        bill_id: UUID | str,
        wallet_id: Optional[UUID | str] = None,
    ) -> Dict[str, Any]:
        """
        Kích hoạt thanh toán hóa đơn định kỳ KTX (Tiền phòng, Điện nước, 4G):
        - Trừ số dư ví được chọn (hoặc ví mặc định của hóa đơn)
        - Ghi nhận giao dịch `ExpenseTransaction`
        - Cập nhật trạng thái `RecurringBill.status = PAID` & `last_paid_at`
        """
        bill = (
            RecurringBill.objects.select_for_update()
            .filter(id=bill_id, user_id=user_id, is_deleted=False)
            .first()
        )
        if not bill:
            raise ResourceNotFoundException(
                f"Không tìm thấy hóa đơn định kỳ với ID={bill_id}."
            )

        target_wallet_id = wallet_id or bill.wallet_id
        if not target_wallet_id:
            raise BusinessLogicException(
                "Hóa đơn chưa gắn ví mặc định, vui lòng truyền `wallet_id` để thanh toán."
            )

        target_wallet = self.wallet_repo.get_user_wallet_by_id(
            user_id=user_id, wallet_id=target_wallet_id
        )

        tx = self.record_transaction(
            user_id=user_id,
            validated_data={
                "wallet": target_wallet,
                "category": bill.category,
                "transaction_type": ExpenseTransaction.TransactionType.EXPENSE,
                "amount": bill.amount,
                "transaction_date": timezone.now(),
                "note": f"[Thanh toán hóa đơn định kỳ] {bill.title}",
            },
        )

        bill.status = RecurringBill.BillStatus.PAID
        bill.last_paid_at = timezone.now()
        bill.save(update_fields=["status", "last_paid_at", "updated_at"])

        return {"bill": bill, "transaction": tx}
