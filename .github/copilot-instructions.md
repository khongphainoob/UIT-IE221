# Coding Conventions & Architecture Guardrails - Đồ án IE221 (UIT)

## 1. Thông tin Đề tài
- **Tên đề tài đăng ký**: XÂY DỰNG HỆ THỐNG BACKEND RESTFUL API QUẢN LÝ VÀ PHÂN TÍCH DỰ BÁO CHI TIÊU SINH VIÊN
- **Tech Stack**: Python 3.12+, Django 5.x, Django REST Framework (DRF), SimpleJWT, drf-spectacular (Swagger UI), PostgreSQL 16 (`student_expense_db`), Pandas, NumPy, Scikit-learn, Joblib, OpenPyXL, Pytest.
- **Repository**: `https://github.com/khongphainoob/UIT-IE221.git`

---

## 2. Nguyên lý Kiến trúc Bắt buộc (Hybrid MVT + Service-Repository + ML Serving Engine)

1. **Tách biệt trách nhiệm tuyệt đối theo chuẩn MVT mở rộng**:
   - **M - Model & Domain Layer (`models/`, `repositories/`, `services/`, `engines/`)**:
     - `models/`: Chỉ định nghĩa đúng **7 bảng chuẩn 3NF** kế thừa từ `BaseModel` (`TimeStampedSoftDeleteModel`). Tuyệt đối không vượt quá 10 bảng theo quy định của giảng viên.
     - `repositories/`: Đóng gói toàn bộ câu lệnh ORM (`select_related`, `aggregate`, `select_for_update`). Kế thừa từ `BaseRepository`.
     - `services/`: Chứa toàn bộ quy tắc nghiệp vụ tài chính. Mọi thao tác cộng/trừ số dư ví (`Wallet.balance`), chuyển tiền nội bộ, thanh toán hóa đơn KTX hoặc cập nhật `MonthlyBudget.spent_amount` **bắt buộc** bọc trong `@transaction.atomic`.
     - `engines/`: Chứa các lớp phân tích dữ liệu & Machine Learning Serving kế thừa từ `BaseFinancialAnalyzer(ABC)`.
   - **V - View Layer (`views/`, `urls.py`)**:
     - Tuyệt đối **KHÔNG** viết truy vấn ORM phức tạp hay logic tính toán tiền bạc trực tiếp trong `views/`.
     - View chỉ nhận Request, kiểm tra Permission (`IsAdmin`, `IsStudentOwner`), gọi Serializer kiểm tra dữ liệu đầu vào, ủy quyền cho `Service` / `Engine` xử lý và trả về JSON chuẩn `{"success": True, "data": ...}`.
   - **T - Template & Representation Layer (`serializers/`, `templates/`)**:
     - `serializers/`: Định dạng JSON đầu ra/đầu vào cho 30 RESTful APIs.
     - `templates/finance/dashboard.html`: Giao diện Dashboard trực quan nhúng Chart.js minh họa kiến trúc Hybrid MVT.

2. **Áp dụng 4 Tính chất OOP & Design Patterns (Khớp 1:1 với StarUML Class Diagram)**:
   - **Trừu tượng (Abstraction)**: `BaseFinancialAnalyzer(ABC)` có `@abstractmethod` cho `preprocess()` và `execute_analysis()`, cung cấp `analyze()`, `export_report()`, `run_inference()`.
   - **Kế thừa (Inheritance)**: 7 Models kế thừa `BaseModel` (`TimeStampedSoftDeleteModel`). `BurnRateAnalyzer` (`BurnRateForecaster`), `AnomalyDetectionEngine` (`SpendingAnomalyDetector`), và `RiskClassifier` kế thừa `BaseFinancialAnalyzer`.
   - **Đa hình (Polymorphism / Strategy Pattern)**:
     - `SavingStrategy(ABC)` -> `BalancedEarlyMonthStrategy` vs `EmergencyEndOfMonthStrategy`.
     - `BaseReportExporter(ABC)` -> `CSVReportExporter` vs `ExcelReportExporter` cùng ghi đè `generate()`.
   - **Đóng gói (Encapsulation) & Singleton Pattern**:
     - Thuộc tính nội bộ trong Engine có tiền tố `_` (`_raw_data`, `_dataframe`, `_daily_burn_rate`, `_safety_threshold`) và truy xuất qua `@property`.
     - `MLModelRegistry` áp dụng **Singleton Pattern** nạp model `.joblib` (`HuberRegressor`, `IsolationForest`, `RandomForestClassifier`) lên RAM đúng 1 lần.

---

## 3. Quy ước Đặt tên & Chất lượng Code (Coding Standards)
- **Không viết code dư thừa / dead code**: Mọi hàm/class tạo ra phải gắn với đúng 1 trong 5 phân hệ (22 chức năng / 30 APIs).
- **Kiểu dữ liệu tiền tệ**: Luôn dùng `decimal.Decimal` trong tầng `models/`, `repositories/`, `services/` để tránh sai số dấu phẩy động; chỉ ép kiểu `float` bên trong `engines/` khi đưa vào ma trận NumPy / Pandas / Scikit-learn.
- **Chuẩn hóa mã lỗi JSON**: Mọi ngoại lệ nghiệp vụ phải kế thừa `BusinessLogicException`, `InsufficientBalanceException`, hoặc `ResourceNotFoundException` trong `core/exceptions.py`.
- **Kiểm thử tự động**: Sau mọi thay đổi, bắt buộc chạy `pytest -v` (tối thiểu 20 test cases xanh 100%) và `python manage.py spectacular --validate --fail-on-warn` (0 warnings, 0 errors).

---

## 4. Quy trình Git Workflow, Đặt tên Branch / Commit / PR & Đóng Task (DoD)
Chi tiết đầy đủ nằm trong Skill [`.agents/skills/ie221-feature-workflow-git-testing/SKILL.md`](../.agents/skills/ie221-feature-workflow-git-testing/SKILL.md):
1. **Trước khi code (Pull & Setup)**:
   - `git checkout main && git pull origin main`
   - Kích hoạt `.venv`, chạy `python manage.py migrate`, `python manage.py check` và `pytest -v` đảm bảo nhánh gốc xanh 100%.
2. **Đặt tên Nhánh (Branch Naming)**:
   - Cú pháp: `<type>/m<1-5>-<short-slug>` (VD: `feat/m2-wallet-atomic-transfer`, `fix/m4-budget-alert-80`, `test/m5-burn-rate-huber`, `docs/m0-staruml-diagram`).
3. **Đặt tên Commit (Conventional Commits)**:
   - Cú pháp: `<type>(m<1-5>-<scope>): <mô tả ngắn gọn dưới 72 ký tự>` (VD: `feat(m3-transaction): auto-flag anomaly on expense creation`).
4. **Đặt tên Pull Request (PR Title)**:
   - Cú pháp: `[M<1-5>-<Module>] <Feat/Fix/Test/Docs>: <Mô tả đầu việc>` và điền đầy đủ checklist trong `.github/PULL_REQUEST_TEMPLATE.md`.
5. **Quy tắc Đóng Task (Definition of Done - DoD)**:
   - Chỉ được đóng task khi: (1) Đúng kiến trúc 5 tầng MVT, (2) Khớp 1:1 với StarUML & ERD 7 bảng, (3) `spectacular --validate --fail-on-warn` 0 lỗi, (4) `pytest -v` xanh 100%, (5) Đã cập nhật Postman Collection, (6) Không dính file rác (`.env`, `db.sqlite3`), (7) PR đã merge sạch vào `main`.

