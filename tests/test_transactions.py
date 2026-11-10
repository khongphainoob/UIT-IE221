"""
Tests for Module 3 & 4 (transaction & budget_alert):
ExpenseTransaction CRUD, Soft Delete refund, Anomaly flagging, RecurringBill auto-pay,
Budget cloning, and Alert mark-read (5 tests).
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from apps.finance.models import BudgetAlertLog, MonthlyBudget, RecurringBill


@pytest.mark.django_db
class TestTransactionsAndBudgets:
    def test_record_normal_expense_deducts_wallet_and_updates_budget(
        self, auth_client, student_user, sample_wallets, food_category
    ):
        cash, _ = sample_wallets
        now = timezone.now()
        budget = MonthlyBudget.objects.create(
            user=student_user,
            category=food_category,
            month=now.month,
            year=now.year,
            allocated_amount=Decimal("500000.00"),
            spent_amount=Decimal("380000.00"),
        )

        payload = {
            "wallet": str(cash.id),
            "category": str(food_category.id),
            "transaction_type": "EXPENSE",
            "amount": "50000.00",
            "note": "Cơm trưa căn tin",
        }
        response = auth_client.post(
            reverse("transaction-list-create"), payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        cash.refresh_from_db()
        budget.refresh_from_db()
        assert cash.balance == Decimal("950000.00")
        assert budget.spent_amount == Decimal("430000.00")

        alerts = BudgetAlertLog.objects.filter(
            user=student_user, alert_type=BudgetAlertLog.AlertType.WARNING_80
        )
        assert alerts.exists()

    def test_record_outlier_expense_triggers_anomaly_flag(
        self,
        auth_client,
        student_user,
        sample_wallets,
        food_category,
        historical_transactions,
    ):
        cash, _ = sample_wallets
        payload = {
            "wallet": str(cash.id),
            "category": str(food_category.id),
            "transaction_type": "EXPENSE",
            "amount": "850000.00",
            "note": "Chi tiêu đột biến",
        }
        response = auth_client.post(
            reverse("transaction-list-create"), payload, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["data"]["is_anomaly"] is True
        assert response.data["data"]["anomaly_score"] > 2.5

    def test_soft_delete_transaction_refunds_wallet_balance(
        self, auth_client, sample_wallets, food_category
    ):
        cash, _ = sample_wallets
        create_res = auth_client.post(
            reverse("transaction-list-create"),
            {
                "wallet": str(cash.id),
                "category": str(food_category.id),
                "transaction_type": "EXPENSE",
                "amount": "100000.00",
                "note": "Mua sách",
            },
            format="json",
        )
        tx_id = create_res.data["data"]["id"]
        cash.refresh_from_db()
        assert cash.balance == Decimal("900000.00")

        del_res = auth_client.delete(
            reverse("transaction-detail", kwargs={"transaction_id": tx_id})
        )
        assert del_res.status_code == status.HTTP_200_OK
        cash.refresh_from_db()
        assert cash.balance == Decimal("1000000.00")

    def test_pay_recurring_bill_ktx(
        self, auth_client, student_user, sample_wallets, food_category
    ):
        cash, _ = sample_wallets
        bill = RecurringBill.objects.create(
            user=student_user,
            wallet=cash,
            category=food_category,
            title="Tiền phòng KTX Khu B",
            amount=Decimal("450000.00"),
            due_day=5,
        )
        res = auth_client.post(
            reverse("recurring-bill-pay", kwargs={"bill_id": bill.id}),
            {},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        assert res.data["data"]["bill"]["status"] == "PAID"
        cash.refresh_from_db()
        assert cash.balance == Decimal("550000.00")

    def test_clone_previous_month_budget_and_mark_alert_read(
        self, auth_client, student_user, food_category
    ):
        now = timezone.now()
        prev_month = 12 if now.month == 1 else now.month - 1
        prev_year = now.year - 1 if now.month == 1 else now.year
        MonthlyBudget.objects.create(
            user=student_user,
            category=food_category,
            month=prev_month,
            year=prev_year,
            allocated_amount=Decimal("1800000.00"),
        )
        clone_res = auth_client.post(
            reverse("budget-clone-previous"),
            {"month": now.month, "year": now.year},
            format="json",
        )
        assert clone_res.status_code == status.HTTP_201_CREATED
        assert len(clone_res.data["data"]) >= 1

        alert = BudgetAlertLog.objects.create(
            user=student_user,
            alert_type=BudgetAlertLog.AlertType.WARNING_80,
            message="Cảnh báo mẫu",
        )
        read_res = auth_client.patch(
            reverse("alerts-mark-read", kwargs={"alert_id": alert.id})
        )
        assert read_res.status_code == status.HTTP_200_OK
        assert read_res.data["data"]["is_read"] is True
