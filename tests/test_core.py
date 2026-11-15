"""
Unit Tests for Core Layer (`tests/test_core.py`):
- BaseModel (UUIDv4 primary key, created_at, updated_at, is_deleted, soft_delete, restore)
- BaseRepository (create, get_by_id, filter_active, update, soft_delete, ResourceNotFoundException)
- Custom Exceptions & Exception Mapping (Validation, BusinessLogic, AccessDenied, NotFound)
- Standardized JSON APIResponse (success, created, error)
"""
from decimal import Decimal
import uuid
import pytest
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from apps.finance.models import Wallet
from core.base_models import BaseModel, TimeStampedSoftDeleteModel
from core.base_repositories import BaseRepository
from core.exceptions import (
    AccessDeniedException,
    BudgetExceededException,
    BusinessLogicException,
    DomainValidationException,
    ErrorCode,
    InsufficientBalanceException,
    ResourceNotFoundException,
    custom_exception_handler,
)
from core.responses import APIResponse


class DummyWalletRepo(BaseRepository[Wallet]):
    model_class = Wallet


@pytest.mark.django_db
class TestCoreFoundation:
    def test_base_model_uuid_timestamps_and_soft_delete(self, student_user):
        assert issubclass(Wallet, BaseModel)
        assert BaseModel is TimeStampedSoftDeleteModel

        wallet = Wallet.objects.create(
            user=student_user,
            name="Ví Kiểm Thử Core",
            wallet_type=Wallet.WalletType.CASH,
            balance=Decimal("100000.00"),
        )
        assert isinstance(wallet.id, uuid.UUID)
        assert wallet.created_at is not None
        assert wallet.updated_at is not None
        assert wallet.is_deleted is False

        # Soft delete hides record from default manager `objects`, keeps in `all_objects`
        wallet.soft_delete()
        assert wallet.is_deleted is True
        assert Wallet.objects.filter(id=wallet.id).count() == 0
        assert Wallet.all_objects.filter(id=wallet.id).count() == 1

        # Restore brings record back to active queryset
        wallet.restore()
        assert wallet.is_deleted is False
        assert Wallet.objects.filter(id=wallet.id).count() == 1

    def test_base_repository_crud_and_not_found(self, student_user):
        repo = DummyWalletRepo()
        created = repo.create(
            user=student_user,
            name="Ví Repo Test",
            wallet_type=Wallet.WalletType.MOMO,
            balance=Decimal("250000.00"),
        )
        fetched = repo.get_by_id(created.id)
        assert fetched.id == created.id

        updated = repo.update(fetched, name="Ví Repo Đã Sửa")
        assert updated.name == "Ví Repo Đã Sửa"
        assert repo.filter_active(user=student_user).count() >= 1

        repo.soft_delete(updated)
        with pytest.raises(ResourceNotFoundException):
            repo.get_by_id(created.id)

    def test_exception_mapping_for_all_four_categories(self):
        # 1. Validation Error (Django & Domain)
        dj_val_res = custom_exception_handler(
            DjangoValidationError({"email": ["Email không hợp lệ."]}), {}
        )
        assert dj_val_res.status_code == status.HTTP_400_BAD_REQUEST
        assert dj_val_res.data["success"] is False
        assert dj_val_res.data["error_code"] == ErrorCode.VALIDATION_ERROR

        dom_val_res = custom_exception_handler(
            DomainValidationException("Số tiền phải dương."), {}
        )
        assert dom_val_res.status_code == status.HTTP_400_BAD_REQUEST
        assert dom_val_res.data["error"]["code"] == ErrorCode.VALIDATION_ERROR

        # 2. Business Logic / Insufficient Balance / Budget Exceeded
        ins_res = custom_exception_handler(InsufficientBalanceException(), {})
        assert ins_res.status_code == status.HTTP_400_BAD_REQUEST
        assert ins_res.data["error_code"] == ErrorCode.INSUFFICIENT_BALANCE

        bud_res = custom_exception_handler(BudgetExceededException(), {})
        assert bud_res.status_code == status.HTTP_400_BAD_REQUEST
        assert bud_res.data["error_code"] == ErrorCode.BUDGET_EXCEEDED

        # 3. Permission / Access Denied
        perm_res = custom_exception_handler(AccessDeniedException(), {})
        assert perm_res.status_code == status.HTTP_403_FORBIDDEN
        assert perm_res.data["error_code"] == ErrorCode.PERMISSION_DENIED

        # 4. Not Found
        nf_res = custom_exception_handler(ResourceNotFoundException(), {})
        assert nf_res.status_code == status.HTTP_404_NOT_FOUND
        assert nf_res.data["error_code"] == ErrorCode.RESOURCE_NOT_FOUND

    def test_standardized_api_response_helper(self):
        ok_res = APIResponse.success(data={"balance": 50000}, message="Thành công")
        assert ok_res.status_code == status.HTTP_200_OK
        assert ok_res.data["success"] is True
        assert ok_res.data["status"] == "success"
        assert ok_res.data["data"]["balance"] == 50000

        err_res = APIResponse.error(
            message="Lỗi nghiệp vụ",
            error_code=ErrorCode.BUSINESS_LOGIC_ERROR,
        )
        assert err_res.status_code == status.HTTP_400_BAD_REQUEST
        assert err_res.data["success"] is False
        assert err_res.data["error_code"] == ErrorCode.BUSINESS_LOGIC_ERROR
