## 1. Thông tin Task & Phân hệ (Module)
- **Mã Phân hệ**: [ ] M1 (`auth_iam`) | [ ] M2 (`wallet_mgmt`) | [ ] M3 (`transaction`) | [ ] M4 (`budget_alert`) | [ ] M5 (`analytics_engine`) | [ ] Docs/UML
- **Người thực hiện**: 
- **Mô tả ngắn gọn tính năng / thay đổi**:
  - 

---

## 2. Danh sách API / Class đã thêm hoặc chỉnh sửa
| Tầng Kiến trúc | File / Class / Method | Mô tả thay đổi |
| :--- | :--- | :--- |
| **Model (3NF)** | `apps/finance/models/...` | |
| **Repository** | `apps/finance/repositories/...` | |
| **Service / Engine** | `apps/finance/services/...` / `engines/...` | |
| **Serializer** | `apps/finance/serializers/...` | |
| **View / URL** | `apps/finance/views/...` | |

---

## 3. Kiểm tra Quy chuẩn Kiến trúc & OOP (Architecture Guardrails)
- [ ] **Tách tầng MVT nghiêm ngặt**: Không viết câu lệnh ORM hay tính toán tiền tệ trực tiếp trong `views/`.
- [ ] **Bảo toàn giao dịch tiền tệ**: Mọi thao tác cộng/trừ `Wallet.balance` hoặc cập nhật `MonthlyBudget.spent_amount` đều bọc trong `@transaction.atomic` và khóa dòng bằng `select_for_update()`.
- [ ] **Chuẩn OOP & StarUML 1:1**: Giữ nguyên tên lớp kế thừa (`BaseModel`, `BaseFinancialAnalyzer(ABC)`, `MLModelRegistry`, `SavingStrategy`, `BaseReportExporter`) và tiền tố đóng gói `_`.
- [ ] **Không vượt quá 7 bảng CSDL chuẩn 3NF**.

---

## 4. Cổng Kiểm Soát Chất Lượng & Testing (Bắt buộc trước khi Merge & Đóng Task)
- [ ] Chạy `python manage.py check` -> `System check identified no issues`.
- [ ] Chạy `python manage.py spectacular --validate --fail-on-warn` -> `0 errors, 0 warnings`.
- [ ] Chạy `pytest -v` -> **100% PASSED** (Đính kèm kết quả bên dưới).
- [ ] Đã cập nhật request tương ứng vào `student_expense_api/postman/IE221_Collection.json` (nếu có thêm/sửa API).

### Kết quả chạy `pytest -v`:
```text
Dán kết quả chạy pytest -v tại đây...
```

