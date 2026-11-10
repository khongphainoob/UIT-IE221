"""
Pytest Configuration & Shared Fixtures for Student Expense Analytics API.
Automatically switches test database to in-memory SQLite so tests run fast and isolated.
"""
from datetime import timedelta
from decimal import Decimal
import pytest
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient
from apps.finance.models import (
    ExpenseCategory,
    ExpenseTransaction,
    UserAccount,
    Wallet,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def student_user(db) -> UserAccount:
    return UserAccount.objects.create_user(
        email="22520999@gm.uit.edu.vn",
        password="Password@123",
        student_code="22520999",
        full_name="Trần Sinh Viên UIT",
        role=UserAccount.Role.STUDENT,
    )


@pytest.fixture
def auth_client(api_client: APIClient, student_user: UserAccount) -> APIClient:
    api_client.force_authenticate(user=student_user)
    return api_client


@pytest.fixture
def sample_wallets(student_user: UserAccount):
    cash = Wallet.objects.create(
        user=student_user,
        name="Ví Tiền Mặt",
        wallet_type=Wallet.WalletType.CASH,
        balance=Decimal("1000000.00"),
    )
    momo = Wallet.objects.create(
        user=student_user,
        name="Ví MoMo",
        wallet_type=Wallet.WalletType.MOMO,
        balance=Decimal("500000.00"),
    )
    return cash, momo


@pytest.fixture
def food_category(db) -> ExpenseCategory:
    return ExpenseCategory.objects.create(
        name="Ăn uống căn tin",
        category_type=ExpenseCategory.CategoryType.EXPENSE,
        is_essential=True,
    )


@pytest.fixture
def historical_transactions(
    student_user: UserAccount, sample_wallets, food_category: ExpenseCategory
):
    cash, _ = sample_wallets
    now = timezone.now()
    tx_list = []
    for day in range(14):
        tx_list.append(
            ExpenseTransaction(
                user=student_user,
                wallet=cash,
                category=food_category,
                transaction_type=ExpenseTransaction.TransactionType.EXPENSE,
                amount=Decimal("40000.00") + Decimal(str((day % 3) * 5000)),
                transaction_date=now - timedelta(days=day),
                note=f"Cơm trưa ngày {day}",
            )
        )
    return ExpenseTransaction.objects.bulk_create(tx_list)

