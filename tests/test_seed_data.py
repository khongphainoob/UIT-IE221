"""
Tests for `python manage.py seed_data`:
Covers fresh-DB seeding across all 7 3NF tables for the 2452xxxx UIT cohort (6 students + 1 Admin),
CSV dataset export (`data/uit_student_expenses_dataset.csv`), idempotency, `--reset`/`--days`/`--count`/`--seed`,
intentional anomaly & edge-case transactions, and end-to-end compatibility with ML engines and `/dashboard/`.
"""
from decimal import Decimal
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.finance.engines import AnomalyDetectionEngine, BurnRateAnalyzer, RiskClassifier
from apps.finance.management.commands.seed_data import DEFAULT_CSV_PATH
from apps.finance.models import (
    BudgetAlertLog,
    ExpenseCategory,
    ExpenseTransaction,
    MonthlyBudget,
    RecurringBill,
    UserAccount,
    Wallet,
)
from apps.finance.repositories import TransactionRepository, WalletRepository


@pytest.mark.django_db
class TestSeedDataCommand:
    def test_seed_data_populates_linked_7_tables_on_fresh_db(self):
        out = StringIO()
        call_command("seed_data", stdout=out)

        admin = UserAccount.objects.get(email="admin@uit.edu.vn")
        student = UserAccount.objects.get(email="24520001@gm.uit.edu.vn")
        assert admin.role == UserAccount.Role.ADMIN
        assert admin.check_password("Admin@123")
        assert student.role == UserAccount.Role.STUDENT
        assert student.student_code == "24520001"
        assert student.check_password("Student@123")

        # 6 sinh viên khóa 2024 (24520001..24520006) + 1 Admin = 7 users
        assert UserAccount.objects.filter(role=UserAccount.Role.STUDENT).count() == 6
        assert Wallet.objects.count() == 18
        assert Wallet.objects.filter(user=student).count() == 3
        assert ExpenseCategory.objects.filter(user=None).count() == 12
        assert RecurringBill.objects.filter(user=student).count() == 4
        assert RecurringBill.objects.count() == 14
        assert DEFAULT_CSV_PATH.exists()

        tx_qs = ExpenseTransaction.objects.filter(user=student)
        assert tx_qs.count() == 200
        assert ExpenseTransaction.objects.count() == 1025
        assert tx_qs.filter(transaction_type=ExpenseTransaction.TransactionType.INCOME).count() == 3
        assert tx_qs.filter(transaction_type=ExpenseTransaction.TransactionType.TRANSFER).count() == 2

        expenses = tx_qs.filter(transaction_type=ExpenseTransaction.TransactionType.EXPENSE)
        assert expenses.filter(is_anomaly=True, anomaly_score__gt=0).count() >= 5
        assert expenses.filter(amount__lte=Decimal("10000.00")).count() >= 3

        dates = list(expenses.values_list("transaction_date", flat=True))
        span_days = (max(dates) - min(dates)).days
        assert 50 <= span_days <= 62

        budgets = MonthlyBudget.objects.filter(user=student)
        assert budgets.count() == 5
        now = timezone.now()
        curr_budgets = budgets.filter(month=now.month, year=now.year)
        assert curr_budgets.count() == 3
        assert any(b.usage_percentage >= 100.0 for b in curr_budgets)

        alerts = BudgetAlertLog.objects.filter(user=student)
        assert alerts.filter(alert_type=BudgetAlertLog.AlertType.ANOMALY, transaction__isnull=False).exists()
        assert alerts.filter(alert_type=BudgetAlertLog.AlertType.BURN_RATE, budget__isnull=False).exists()
        assert "Hoàn tất seed dữ liệu Khóa 2024 UIT" in out.getvalue()

    def test_seed_data_is_idempotent_without_reset(self):
        call_command("seed_data", stdout=StringIO())
        snapshot = (
            UserAccount.objects.count(),
            Wallet.objects.count(),
            ExpenseCategory.objects.count(),
            RecurringBill.objects.count(),
            ExpenseTransaction.objects.count(),
            MonthlyBudget.objects.count(),
            BudgetAlertLog.objects.count(),
        )

        second_out = StringIO()
        call_command("seed_data", stdout=second_out)
        after = (
            UserAccount.objects.count(),
            Wallet.objects.count(),
            ExpenseCategory.objects.count(),
            RecurringBill.objects.count(),
            ExpenseTransaction.objects.count(),
            MonthlyBudget.objects.count(),
            BudgetAlertLog.objects.count(),
        )
        assert after == snapshot
        assert "Idempotent" in second_out.getvalue()

    def test_seed_data_reset_with_custom_count_and_days(self):
        call_command("seed_data", stdout=StringIO())
        call_command("seed_data", reset=True, count=140, days=45, seed=221, stdout=StringIO())

        student = UserAccount.objects.get(email="24520001@gm.uit.edu.vn")
        assert Wallet.objects.filter(user=student).count() == 3
        tx_qs = ExpenseTransaction.objects.filter(user=student)
        assert tx_qs.count() == 140

        dates = list(tx_qs.values_list("transaction_date", flat=True))
        span_days = (max(dates) - min(dates)).days
        assert 40 <= span_days <= 46
        assert tx_qs.filter(is_anomaly=True).count() >= 5

    def test_seeded_data_powers_analytics_engines_and_dashboard(self, client):
        call_command("seed_data", stdout=StringIO())
        student = UserAccount.objects.get(email="24520001@gm.uit.edu.vn")

        wallet_repo = WalletRepository()
        tx_repo = TransactionRepository()
        total_balance = wallet_repo.get_total_balance(user_id=student.id)
        expense_records = tx_repo.get_expense_records_for_analytics(user_id=student.id)

        burn = BurnRateAnalyzer(
            raw_transactions=expense_records, current_balance=total_balance
        ).run_inference()
        assert burn["daily_burn_rate"] > 0
        assert burn["rolling_7d_burn_rate"] > 0
        assert burn["predicted_exhaustion_date"] is not None
        assert len(burn["daily_trend"]) >= 14

        anom = AnomalyDetectionEngine(raw_transactions=expense_records).run_inference()
        assert anom["total_analyzed"] >= 190
        assert anom["anomaly_count"] >= 5

        risk = RiskClassifier(
            raw_transactions=expense_records,
            current_balance=total_balance,
            monthly_budget_limit=student.monthly_income_limit,
        ).run_inference()
        assert 0 <= risk["financial_health_score"] <= 100
        assert risk["risk_level"] in ("SAFE", "WARNING", "HIGH_RISK_BROKE")

        dash_res = client.get("/dashboard/")
        assert dash_res.status_code == 200
        html_body = dash_res.content.decode("utf-8")
        assert student.full_name in html_body or student.email in html_body

        # Hỗ trợ đổi sinh viên trên Dashboard qua ?student=24520004
        dash_stu4 = client.get("/dashboard/?student=24520004")
        assert dash_stu4.status_code == 200
        assert "Phạm Ngọc Hân" in dash_stu4.content.decode("utf-8")
