---
name: ie221-feature-workflow-git-testing
description: Quy trình chuẩn (SOP) phát triển 1 tính năng từ lúc Pull code, Setup môi trường, Checkout nhánh, Code theo 5 tầng MVT, Viết Unit Test Pytest, Quy tắc đặt tên Branch/Commit/Pull Request (PR) đến Quy tắc Đóng Task (Definition of Done) cho Đồ án IE221 (UIT). Kích hoạt skill này bất cứ khi nào làm tính năng mới, fix bug, chạy test, tạo commit/PR hoặc nghiệm thu đóng task.
---

# Quy Trình Phát Triển Tính Năng, Git Workflow, Testing & Đóng Task (IE221 SOP)

Skill này quy định quy trình làm việc chuẩn Software Engineering từ đầu đến cuối cho 3 thành viên nhóm Đồ án IE221 (**XÂY DỰNG HỆ THỐNG BACKEND RESTFUL API QUẢN LÝ VÀ PHÂN TÍCH DỰ BÁO CHI TIÊU SINH VIÊN**).

---

## GIAI ĐOẠN 1: PULL CODE & SETUP MÔI TRƯỜNG (TRƯỚC KHI CODE)

Mỗi khi bắt đầu ca làm việc hoặc nhận task mới, bắt buộc thực hiện đúng thứ tự 4 bước sau:

### 1.1. Đồng bộ code mới nhất từ GitHub
```powershell
git checkout main
git pull origin main
```

### 1.2. Kích hoạt Virtual Environment (`.venv`) & Cài đặt thư viện mới (nếu có)
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 1.3. Khởi động Database (Docker PostgreSQL 16 hoặc SQLite Fallback)
- **Nếu dùng Docker PostgreSQL 16**:
  ```powershell
  docker compose up -d db
  ```
- **Nếu máy chưa bật Docker Desktop**: Hệ thống tự động fallback sang `db.sqlite3` nhờ cờ `AUTO_FALLBACK_SQLITE=True` trong `.env`.

### 1.4. Đồng bộ Migration & Kiểm tra sức khỏe hệ thống trước khi code
```powershell
python manage.py migrate
python manage.py check
pytest -v
```
> **Nguyên tắc**: Chỉ bắt đầu tạo nhánh mới khi nhánh `main` hiện tại đang chạy `pytest -v` **PASSED 100%**.

---

## GIAI ĐOẠN 2: QUY TẮC ĐẶT TÊN NHÁNH (GIT BRANCH NAMING)

Tuyệt đối **KHÔNG** code trực tiếp trên nhánh `main`. Mọi task phải tạo nhánh riêng theo cú pháp:

```text
<type>/m<module_number>-<short-slug>
```

### Bảng Tiền tố Nhánh (`<type>`) & Mã Phân hệ (`m1` -> `m5`):
- **Phân hệ (`<module_number>`)**:
  - `m1`: Module 1 (`auth_iam` — Xác thực, Hồ sơ, Admin)
  - `m2`: Module 2 (`wallet_mgmt` — Quản lý Ví, Chuyển tiền nội bộ)
  - `m3`: Module 3 (`transaction` — Danh mục, Giao dịch, Hóa đơn KTX)
  - `m4`: Module 4 (`budget_alert` — Ngân sách tháng, Cảnh báo)
  - `m5`: Module 5 (`analytics_engine` — Burn-Rate, Anomaly, RiskClassifier, Export)
- **Loại nhánh (`<type>`)**:
  - `feat/`: Thêm tính năng hoặc API mới (VD: `git checkout -b feat/m2-wallet-atomic-transfer`)
  - `fix/`: Sửa lỗi logic hoặc bug API (VD: `git checkout -b fix/m4-budget-threshold-80`)
  - `test/`: Bổ sung kịch bản kiểm thử Pytest / Postman (VD: `git checkout -b test/m5-huber-burn-rate`)
  - `docs/`: Cập nhật ERD, StarUML, README, Báo cáo Word (VD: `git checkout -b docs/m0-staruml-class-diagram`)
  - `refactor/`: Tối ưu code không làm đổi hành vi API (VD: `git checkout -b refactor/m3-transaction-repo-select-related`)

---

## GIAI ĐOẠN 3: QUY TRÌNH 5 BƯỚC CODE 1 TÍNH NĂNG MỚI (5-LAYER MVT SOP)

Khi code bất kỳ tính năng hay API nào, bắt buộc đi từ tầng trong ra tầng ngoài theo đúng 5 bước để không bị lỗi import vòng (circular import) hoặc viết nhầm logic vào View:

### Bước 1: Tầng `models/` (`apps/finance/models/`)
- Kiểm tra xem tính năng có cần thêm trường vào **7 bảng chuẩn 3NF** hay không.
- **Lưu ý cứng**: Tuyệt đối không tạo quá 7 bảng CSDL đã đăng ký. Mọi Model phải kế thừa `BaseModel` (`TimeStampedSoftDeleteModel`).
- Nếu có sửa trường Model, chạy ngay:
  ```powershell
  python manage.py makemigrations finance
  python manage.py migrate
  ```

### Bước 2: Tầng `repositories/` (`apps/finance/repositories/`)
- Viết hàm truy vấn ORM kế thừa từ `BaseRepository`.
- **Bắt buộc**:
  - Dùng `.select_related("wallet", "category")` khi lấy danh sách để chống lỗi $N+1$ queries.
  - Dùng `.select_for_update()` khi lấy bản ghi Ví/Ngân sách chuẩn bị cộng/trừ tiền.
  - Dùng `.aggregate(total=Sum("..."))` khi tính tổng trên Database.

### Bước 3: Tầng `services/` hoặc `engines/`
- **Nếu là nghiệp vụ CRUD / Tiền tệ (`apps/finance/services/`)**:
  - Bọc hàm thay đổi dữ liệu trong `@transaction.atomic`.
  - Dùng kiểu `Decimal` cho mọi phép tính tiền tệ (không dùng `float`).
  - Ném ngoại lệ chuẩn từ `core/exceptions.py` (`InsufficientBalanceException`, `BusinessLogicException`, `ResourceNotFoundException`).
- **Nếu là thuật toán Phân tích / Học máy (`apps/finance/engines/`)**:
  - Kế thừa `BaseFinancialAnalyzer(ABC)`, đặt tên thuộc tính nội bộ có dấu gạch dưới `_` (`_dataframe`, `_daily_burn_rate`).
  - Hiện thực đầy đủ `preprocess()` và `execute_analysis()`.
  - Nếu dùng model học máy đóng gói `.joblib`, phải gọi qua `MLModelRegistry.get_instance().get_model(...)` (Singleton Pattern).

### Bước 4: Tầng `serializers/` (`apps/finance/serializers/`)
- Định nghĩa Serializer kiểm tra dữ liệu đầu vào (`min_value=Decimal("0.01")`, kiểm tra định dạng UUID/Email) và định dạng JSON đầu ra.
- Khai báo rõ `read_only_fields` cho các trường hệ thống tự tính (`id`, `is_anomaly`, `anomaly_score`, `spent_amount`, `created_at`).

### Bước 5: Tầng `views/` & `urls.py` (`apps/finance/views/` & `apps/finance/urls.py`)
- Viết `APIView` gọn nhẹ:
  1. Khai báo `permission_classes = [IsStudentOwner]` (hoặc `[IsAdmin]`, `[AllowAny]`).
  2. Gắn decorator `@extend_schema(request=..., responses=..., tags=[...], summary=...)` để Swagger UI tự động sinh tài liệu.
  3. Trong thân hàm `get`/`post`/`put`/`patch`/`delete`: chỉ gọi `serializer.is_valid(raise_exception=True)` -> gọi `service` / `engine` -> trả về `Response({"success": True, "data": ...})`.
- Đăng ký đường dẫn vào `apps/finance/urls.py` theo chuẩn RESTful (`/api/v1/...`).

---

## GIAI ĐOẠN 4: QUY TẮC KIỂM THỬ (TESTING SOP) TRƯỚC KHI COMMIT

Không một dòng code nào được phép commit nếu chưa vượt qua **3 Cổng Kiểm Soát Chất Lượng (Quality Gates)** dưới đây:

### 4.1. Viết Unit Test & API Test trong `tests/`
Mỗi tính năng/API mới phải có ít nhất **2 test cases** trong file `tests/test_<module>.py` tương ứng:
1. **Test Happy Path (200/201)**: Dữ liệu hợp lệ, kiểm tra cả `response.status_code` lẫn dữ liệu thực tế trong DB sau khi gọi (`wallet.refresh_from_db()`).
2. **Test Edge Case / Error Case (400/403/404)**: Kiểm tra số dư không đủ (`insufficient_balance`), sai định dạng email UIT, hoặc truy cập trái quyền (`403 Forbidden`), đảm bảo `@transaction.atomic` rollback toàn bộ số dư.

### 4.2. Chạy Bộ 3 Lệnh Kiểm Tra Bắt Buộc
```powershell
# 1. Kiểm tra cấu hình hệ thống Django
.\.venv\Scripts\python.exe manage.py check

# 2. Kiểm tra OpenAPI 3 / Swagger Schema (Bắt buộc 0 errors, 0 warnings)
.\.venv\Scripts\python.exe manage.py spectacular --validate --fail-on-warn

# 3. Chạy toàn bộ test suite Pytest (Bắt buộc xanh 100%, 0 warnings)
.\.venv\Scripts\pytest.exe -v
```

---

## GIAI ĐOẠN 5: QUY TẮC COMMIT & TẠO PULL REQUEST (PR CONVENTIONS)

### 5.1. Quy tắc viết Commit Message (Conventional Commits)
Cú pháp bắt buộc:
```text
<type>(m<1-5>-<scope>): <mô tả ngắn gọn bằng tiếng Anh hoặc tiếng Việt dưới 72 ký tự>
```
**Ví dụ chuẩn**:
- `feat(m2-wallet): implement atomic transfer between student wallets`
- `feat(m5-engine): add HuberRegressor burn-rate forecast and RiskClassifier`
- `fix(m3-transaction): refund wallet balance when soft-deleting expense`
- `test(m1-auth): add RBAC permission tests for admin user management`
- `docs(uml): update StarUML class diagram to match SavingStrategy`

**Tuyệt đối cấm** các commit mơ hồ như: `update`, `fix bug`, `code xong`, `asdf`, `final`.

### 5.2. Quy tắc đặt tên Pull Request (PR Title)
Cú pháp bắt buộc:
```text
[M<1-5>-<Tên Module>] <Feat/Fix/Test/Docs>: <Mô tả rõ đầu việc đã hoàn thành>
```
**Ví dụ chuẩn**:
- `[M2-Wallet] Feat: Hoàn thiện 6 APIs Quản lý Ví & Chuyển tiền nội bộ (@transaction.atomic)`
- `[M5-Analytics] Feat: Tích hợp MLModelRegistry Singleton & 3 bài toán ML Serving`

---

## GIAI ĐOẠN 6: QUY TẮC NGHIỆM THU & ĐÓNG TASK (DEFINITION OF DONE - DoD)

Một Task chỉ được phép chuyển trạng thái sang **`DONE` (Đóng Task)** trên bảng phân công (Notion / GitHub / Google Sheets) khi thỏa mãn **ĐỦ 7 TIÊU CHÍ** sau:

- [ ] **1. Đúng Kiến trúc 5 Tầng**: Không có ORM query hay tính toán tiền tệ nằm trực tiếp trong `views/`; mọi thay đổi số dư đều bọc `@transaction.atomic` + `select_for_update()`.
- [ ] **2. Khớp 1:1 với Sơ đồ Thiết kế**: Tên Class, thuộc tính (`_` prefix) và phương thức trong code khớp 100% với ERD 7 bảng và StarUML Class Diagram trong `docs/uml_templates.md`.
- [ ] **3. Swagger UI Xanh & Đầy đủ**: Đã gắn `@extend_schema`, chạy `python manage.py spectacular --validate --fail-on-warn` đạt **0 lỗi, 0 cảnh báo**.
- [ ] **4. Pytest Xanh 100%**: Đã viết Unit/API Test cho tính năng đó và chạy `pytest -v` toàn dự án đạt **100% PASSED**.
- [ ] **5. Postman Collection Cập nhật**: Request mới đã được thêm vào `postman/IE221_Collection.json` và chạy thử thành công trên `seed_data`.
- [ ] **6. Không có File Rác / Code Thừa**: Không commit file `.env` cá nhân, `db.sqlite3`, `__pycache__/`, hoặc các đoạn code `print()` / comment nháp.
- [ ] **7. PR đã được Review & Merge**: Nhánh tính năng đã tạo Pull Request theo đúng mẫu `.github/PULL_REQUEST_TEMPLATE.md` và merge sạch vào `main`.

