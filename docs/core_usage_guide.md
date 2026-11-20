# Tài Liệu Hướng Dẫn Sử Dụng Tầng Nền Tảng `core/` (Dành cho 3 Thành Viên Nhóm IE221)

Tài liệu này quy định chuẩn thống nhất về **Tên trường, Kiểu khóa chính (`UUIDv4`), Cách kế thừa `BaseModel`, `BaseRepository`, `Custom Exceptions` và Chuẩn hóa JSON Response** để Thành viên 2 và Thành viên 3 import trực tiếp mà không tự viết riêng từng kiểu.

---

## 1. Quy chuẩn Tên Trường & Kiểu ID Dùng Chung (`core/base_models.py` & `core/models.py`)

Mọi bảng trong `apps/finance/models/` **bắt buộc** kế thừa từ `BaseModel` (hoặc bí danh `TimeStampedSoftDeleteModel`). Khi kế thừa, bảng sẽ tự động có sẵn **4 trường chuẩn** sau (không được khai báo lặp lại):

| Tên trường | Kiểu dữ liệu Django | Đặc tính | Ý nghĩa |
| :--- | :--- | :--- | :--- |
| `id` | `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)` | PK | Khóa chính kiểu UUIDv4 thống nhất toàn bộ 7 bảng |
| `created_at` | `DateTimeField(auto_now_add=True, db_index=True)` | Indexed | Thời điểm tạo bản ghi |
| `updated_at` | `DateTimeField(auto_now=True)` | Auto | Thời điểm cập nhật bản ghi gần nhất |
| `is_deleted` | `BooleanField(default=False, db_index=True)` | Soft Delete | Cờ đánh dấu xóa mềm (`False` = đang hoạt động, `True` = đã xóa) |

### Ví dụ 1: Cách Thành viên 2 khai báo Model kế thừa `BaseModel`
```python
from decimal import Decimal
from django.db import models
from core.base_models import BaseModel


class Wallet(BaseModel):
    user = models.ForeignKey("finance.UserAccount", on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
```
- Truy vấn mặc định `Wallet.objects.all()` chỉ trả về các bản ghi `is_deleted=False`.
- Xóa mềm: `wallet.soft_delete()` (không dùng `wallet.delete()` vật lý).
- Khôi phục: `wallet.restore()`.

---

## 2. Cách Kế Thừa `BaseRepository` (`core/base_repositories.py` & `core/repositories.py`)

`BaseRepository[T]` cung cấp sẵn các hàm:
- `get_queryset()`: Lấy QuerySet các bản ghi chưa xóa mềm (`is_deleted=False`).
- `list_all(**filters)` / `filter_active(**filters)`: Lọc danh sách theo điều kiện.
- `get_by_id(record_id, **extra_filters)`: Lấy 1 bản ghi theo UUID; nếu không có sẽ tự động ném `ResourceNotFoundException` (HTTP 404).
- `find_by_id(record_id, **extra_filters)`: Lấy 1 bản ghi hoặc trả về `None`.
- `create(**data)`: Khởi tạo, gọi `full_clean()` và lưu vào DB.
- `update(instance, **data)`: Cập nhật các thuộc tính, gọi `full_clean()` và lưu DB.
- `soft_delete(instance)`: Đánh dấu xóa mềm `is_deleted=True`.

### Ví dụ 2: Cách tạo Repository cho từng Module
```python
from uuid import UUID
from django.db.models import QuerySet
from apps.finance.models import Wallet
from core.base_repositories import BaseRepository


class WalletRepository(BaseRepository[Wallet]):
    model_class = Wallet

    def get_user_wallets(self, user_id: UUID | str) -> QuerySet[Wallet]:
        return self.filter_active(user_id=user_id).order_by("created_at")
```

---

## 3. Cách Ném Ngoại Lệ Nghiệp Vụ & Phân Quyền (`core/exceptions.py`)

Hệ thống cung cấp sẵn 4 nhóm Exception tự động ánh xạ sang HTTP Status Code và mã lỗi chuẩn `ErrorCode`:

| Nhóm lỗi | Class Exception cần import | HTTP Status | `error_code` trả về |
| :--- | :--- | :---: | :--- |
| **1. Lỗi Validation** | `DomainValidationException` | `400 Bad Request` | `validation_error` |
| **2. Lỗi Nghiệp vụ chung** | `BusinessLogicException` | `400 Bad Request` | `business_logic_error` |
| **2a. Không đủ số dư ví** | `InsufficientBalanceException` | `400 Bad Request` | `insufficient_balance` |
| **2b. Vượt ngân sách** | `BudgetExceededException` | `400 Bad Request` | `budget_exceeded` |
| **3. Trái quyền truy cập** | `AccessDeniedException` | `403 Forbidden` | `permission_denied` |
| **4. Không tìm thấy dữ liệu** | `ResourceNotFoundException` | `404 Not Found` | `resource_not_found` |

### Ví dụ 3: Cách dùng Exception trong tầng `services/`
```python
from decimal import Decimal
from django.db import transaction
from core.exceptions import BusinessLogicException, InsufficientBalanceException


class WalletService:
    @transaction.atomic
    def deduct_balance(self, wallet, amount: Decimal):
        if amount <= Decimal("0.00"):
            raise BusinessLogicException("Số tiền giao dịch phải lớn hơn 0.")
        if wallet.balance < amount:
            raise InsufficientBalanceException("Số dư ví không đủ để chi tiêu.")
        wallet.balance -= amount
        wallet.save(update_fields=["balance", "updated_at"])
```

---

## 4. Cách Chuẩn Hóa JSON Response Trong `views/` (`core/responses.py`)

Mọi API đều trả về định dạng JSON thống nhất qua `APIResponse` hoặc `custom_exception_handler`:

### Format JSON khi Thành công (`200 OK` / `201 Created`):
```json
{
  "success": true,
  "status": "success",
  "message": "Thao tác thành công.",
  "data": { ... }
}
```

### Format JSON khi Lỗi (`400` / `401` / `403` / `404`):
```json
{
  "success": false,
  "status": "error",
  "error_code": "insufficient_balance",
  "message": "Số dư ví không đủ để thực hiện giao dịch này.",
  "error": {
    "code": "insufficient_balance",
    "message": "Số dư ví không đủ để thực hiện giao dịch này.",
    "details": null
  }
}
```

### Ví dụ 4: Cách viết `APIView` gọn sạch sử dụng `APIResponse` và `IsStudentOwner`
```python
from rest_framework.views import APIView
from core.permissions import IsStudentOwner
from core.responses import APIResponse
from apps.finance.serializers import WalletSerializer
from apps.finance.services import WalletService


class WalletListCreateAPIView(APIView):
    permission_classes = [IsStudentOwner]
    wallet_service = WalletService()

    def get(self, request):
        wallets = self.wallet_service.list_user_wallets(user_id=request.user.id)
        return APIResponse.success(data=WalletSerializer(wallets, many=True).data)

    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = self.wallet_service.create_wallet(
            user_id=request.user.id, validated_data=serializer.validated_data
        )
        return APIResponse.created(data=WalletSerializer(wallet).data)
```
