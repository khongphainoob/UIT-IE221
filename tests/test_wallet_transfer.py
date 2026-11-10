"""
Tests for Module 2 (wallet_mgmt): Wallet CRUD and Atomic Internal Transfers (4 tests).
"""
from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestWalletTransfer:
    def test_create_and_list_wallets(self, auth_client):
        payload = {
            "name": "Tài khoản TPBank",
            "wallet_type": "BANK",
            "balance": "2000000.00",
        }
        create_res = auth_client.post(
            reverse("wallet-list-create"), payload, format="json"
        )
        assert create_res.status_code == status.HTTP_201_CREATED
        assert create_res.data["data"]["wallet_name"] == "Tài khoản TPBank"

        list_res = auth_client.get(reverse("wallet-list-create"))
        assert list_res.status_code == status.HTTP_200_OK
        assert len(list_res.data["data"]) >= 1

    def test_update_and_soft_delete_wallet(self, auth_client, sample_wallets):
        cash, _ = sample_wallets
        update_res = auth_client.put(
            reverse("wallet-detail", kwargs={"wallet_id": cash.id}),
            {"name": "Ví Tiền Mặt Cá Nhân"},
            format="json",
        )
        assert update_res.status_code == status.HTTP_200_OK
        assert update_res.data["data"]["name"] == "Ví Tiền Mặt Cá Nhân"

        del_res = auth_client.delete(
            reverse("wallet-detail", kwargs={"wallet_id": cash.id})
        )
        assert del_res.status_code == status.HTTP_200_OK

    def test_atomic_transfer_between_wallets_success(self, auth_client, sample_wallets):
        cash, momo = sample_wallets
        payload = {
            "source_wallet_id": str(cash.id),
            "target_wallet_id": str(momo.id),
            "amount": "250000.00",
            "note": "Nạp tiền vào MoMo",
        }
        response = auth_client.post(reverse("wallet-transfer"), payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        cash.refresh_from_db()
        momo.refresh_from_db()
        assert cash.balance == Decimal("750000.00")
        assert momo.balance == Decimal("750000.00")

    def test_transfer_insufficient_balance_rolls_back(
        self, auth_client, sample_wallets
    ):
        cash, momo = sample_wallets
        payload = {
            "source_wallet_id": str(cash.id),
            "target_wallet_id": str(momo.id),
            "amount": "5000000.00",
            "note": "Chuyển vượt quá số dư",
        }
        response = auth_client.post(reverse("wallet-transfer"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"]["code"] == "insufficient_balance"
        cash.refresh_from_db()
        momo.refresh_from_db()
        assert cash.balance == Decimal("1000000.00")
        assert momo.balance == Decimal("500000.00")
