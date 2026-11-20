# Giải Thích Chi Tiết Cấu Trúc Thư Mục, Ưu/Nhược Điểm & Cẩm Nang Trả Lời Vấn Đáp (Đồ Án IE221)

Tài liệu này được biên soạn riêng để cả 3 thành viên nắm vững **"Tại sao lại tổ chức từng thư mục, từng file như vậy?"**, phân tích rõ **Ưu điểm – Nhược điểm (Trade-offs)** và chuẩn bị sẵn câu trả lời sắc bén khi giảng viên hỏi xoáy trong buổi bảo vệ đồ án.

---

## 1. Tại Sao Không Giữ Cấu Trúc Mặc Định Của Django (`django-admin startapp`)?

Khi chạy lệnh mặc định `python manage.py startapp finance`, Django chỉ tạo ra các file đơn lẻ:
```text
finance/
├── models.py        # Nhét cả 7 bảng vào chung 1 file
├── views.py         # Nhét cả 30 APIs + ORM query + tính toán tiền + ML vào chung 1 file
└── serializers.py   # Nhét cả chục Serializer vào chung 1 file
```

### Vấn đề xảy ra nếu giữ cấu trúc mặc định ("Fat Views / God Files"):
1. **File dài hàng nghìn dòng & Xung đột Git (Merge Conflict)**: Khi 3 thành viên cùng sửa chung 1 file `views.py` hoặc `models.py`, lúc `git merge` chắc chắn sẽ đụng độ (conflict) liên tục.
2. **Vi phạm nguyên lý Single Responsibility (SRP - SOLID)**: Một hàm trong `views.py` vừa nhận HTTP Request, vừa kiểm tra số dư ví, vừa gọi ORM `filter/aggregate`, vừa chạy thuật toán Pandas/Scikit-learn $\rightarrow$ Khi sai số liệu thì không biết lỗi ở tầng giao diện, tầng CSDL hay tầng thuật toán.
3. **Không thể tái sử dụng logic (Code Duplication)**: Ví dụ thao tác *"Trừ tiền ví + Cộng dồn ngân sách + Chấm điểm bất thường"* vừa dùng khi sinh viên thêm giao dịch tay (`POST /transactions/`), vừa dùng khi thanh toán tự động hóa đơn KTX (`POST /recurring-bills/{id}/pay/`). Nếu viết trong `views.py` thì phải copy-paste code ở 2 nơi.
4. **Rất khó viết Unit Test (`pytest`)**: Muốn test riêng thuật toán dự báo ngày cạn ví (`BurnRateAnalyzer`) mà code thuật toán nằm dính trong `views.py` thì bắt buộc phải giả lập cả HTTP Request, Token xác thực và Database.

---

## 2. Bản Chất Mô Hình MVT Của Dự Án (Câu Trả Lời Khi Thầy Hỏi *"Đây Là MVT Hay Service-Repository?"*)

> [!IMPORTANT]
> **Câu trả lời chuẩn để ghi điểm tuyệt đối với thầy**:
> *"Dạ thưa thầy, dự án của nhóm tuân thủ đúng chuẩn lý thuyết **MVT (Model - View - Template)** của Django cho cả luồng Web lẫn REST API, **đồng thời mở rộng thêm 3 tầng trung gian (`services/`, `repositories/`, `engines/`) nằm giữa `View [V]` và `Model [M]`**. Nhóm **không gộp** `Service`, `Repository` hay `ML Engine` vào `Model [M]`: `Model` giữ đúng vai trò định nghĩa cấu trúc CSDL & ORM, `View` làm trung tâm điều phối (Controller), `Template / Serializer (.data)` chỉ trình bày đầu ra, còn các tầng mở rộng giúp tách nghiệp vụ phức tạp ra khỏi View để tránh phình to `views.py` (Fat Views)."*

Cụ thể sự ánh xạ chuẩn xác từng thành phần như sau:

| Thành phần Kiến trúc | Thư mục tương ứng trong Dự án | Vai trò đúng chuẩn lý thuyết Django MVT & Clean Architecture |
| :--- | :--- | :--- |
| **M — Model Layer**<br>*(Thuần Dữ liệu & ORM)* | `apps/finance/models/`<br>`core/models.py` | Đúng chuẩn MVT: **chỉ định nghĩa cấu trúc dữ liệu (7 bảng 3NF)**, trường/kiểu dữ liệu, khóa ngoại FK, ràng buộc toàn vẹn (`CheckConstraint`, `UniqueConstraint`) và lớp giao tiếp Django ORM kế thừa `BaseModel`. **Không chứa** Service nghiệp vụ hay ML Engine. |
| **V — View Layer**<br>*(Trung tâm Điều phối — giống Controller trong MVC)* | `apps/finance/views/`<br>`config/urls.py`<br>`apps/finance/urls.py`<br>`core/permissions.py` | Tiếp nhận HTTP Request từ `urls.py`, kiểm tra quyền RBAC (`IsAdmin`, `IsStudentOwner`), lọc & kiểm tra đầu vào API bằng `Serializer.is_valid()`, ủy quyền xử lý sang Tầng Mở Rộng (`Service`) để tương tác với `Model [M]`, nhận đối tượng Python trả về rồi đẩy sang **Template / Serializer (`[T]`)** tạo HTTP Response. |
| **T — Template Layer**<br>*(Tầng Hiển thị / Biểu diễn đầu ra)* | `templates/finance/`<br>`serializers/` *(chiều `.data` + `JSONRenderer`)* | Quyết định cách dữ liệu được trình bày cho người dùng cuối ở **Chiều RA**:<br>• **Với Web MVT (`/dashboard/`)**: File `templates/finance/dashboard.html` kết hợp HTML + Django Template Language (DTL) + Chart.js kết xuất trang web.<br>• **Với REST API (`/api/v1/...`)**: DRF thay HTML Template bằng `Serializer.data` + `JSONRenderer` để kết xuất đối tượng Python thành chuỗi JSON. |
| **Tầng Mở Rộng (Extended Layers)**<br>*(Nằm giữa `[V]` và `[M]`, tách biệt để chống Fat Views)* | `apps/finance/services/`<br>`apps/finance/repositories/`<br>`apps/finance/engines/` | Tách khỏi `View [V]` và giữ tách biệt hoàn toàn với `Model [M]`:<br>• `services/`: Xử lý nghiệp vụ tài chính & giao dịch nguyên tử `@transaction.atomic`.<br>• `repositories/`: Đóng gói câu lệnh ORM truy xuất `Model [M]` (`select_related`, `select_for_update`).<br>• `engines/`: Phân tích chuỗi thời gian Pandas & suy luận ML/DL nạp sẵn từ `.joblib` (`MLModelRegistry` Singleton). |

### Phân biệt nhanh: Tại sao `Service`, `Repository`, `Engine` KHÔNG phải `View`/`Controller` và KHÔNG gộp vào `Model`?
- **Logic điều phối HTTP (Controller / Presentation Logic → thuộc `View [V]`)**: Chỉ xử lý các việc gắn với giao thức Web/HTTP như nhận `HttpRequest`, kiểm tra RBAC (`IsStudentOwner`, `IsAdmin`), lọc payload (`Serializer.is_valid()`), quyết định HTTP status (`200/201/400/403/404`), rồi chuyển dữ liệu sang `[T]` (`Template` hoặc `Serializer.data`).
- **Logic nghiệp vụ, tính toán AI & truy xuất dữ liệu (Business / AI / ORM Logic → thuộc `Service`, `Engine`, `Repository`)**: Hoàn toàn **độc lập với HTTP** (không nhận `HttpRequest`, không trả `HttpResponse` — dùng chung được cho REST API, Web View, lệnh CLI `manage.py` hay Unit Test `pytest`). Xem minh họa trực quan kèm 7 sơ đồ chi tiết tại [`class_diagram_business_walkthrough.md`](class_diagram_business_walkthrough.md).

---

## 3. Giải Thích Chi Tiết Từng Thư Mục & Từng File Trong Dự Án

### 3.1. Thư mục `config/` — Cấu hình Trung tâm của Django Project
- **`config/settings.py`**: Chứa cấu hình toàn cục: danh sách `INSTALLED_APPS`, cấu hình kết nối PostgreSQL 16 (kèm cơ chế tự động kiểm tra kết nối `_can_connect_postgres()` để fallback an toàn sang SQLite khi demo), cấu hình JWT (`SIMPLE_JWT`), cấu hình DRF (`REST_FRAMEWORK`) và cấu hình tài liệu hóa OpenAPI 3 (`SPECTACULAR_SETTINGS`).
- **`config/urls.py`**: Cổng định tuyến gốc (Root URL Dispatcher) chia luồng:
  - `/admin/` $\rightarrow$ Trang quản trị hệ thống của Django.
  - `/dashboard/` $\rightarrow$ Giao diện Web Dashboard trực quan (minh họa Template HTML trong MVT).
  - `/api/v1/` $\rightarrow$ Toàn bộ 30 RESTful APIs của phân hệ tài chính.
  - `/api/schema/swagger/` $\rightarrow$ Giao diện tài liệu tương tác Swagger UI.
- **`config/wsgi.py` & `config/asgi.py`**: Cổng giao tiếp chuẩn giữa Web Server (Gunicorn/Uvicorn) và ứng dụng Django.

---

### 3.2. Thư mục `core/` — Tầng Nền Tảng Dùng Chung (Shared Kernel)
**Lý do tách riêng thư mục `core/`**: Để 3 thành viên khi code 5 phân hệ khác nhau đều kế thừa chung một chuẩn khóa chính `UUIDv4`, chung cơ chế xóa mềm (`Soft Delete`), chung một format JSON trả về và chung một bảng mã lỗi, tránh việc mỗi người tự viết một kiểu.

- **`core/models.py` (và `core/base_models.py`)**:
  - Chứa `BaseModel` (`TimeStampedSoftDeleteModel`) là lớp trừu tượng (`abstract = True`) cung cấp sẵn 4 trường cho cả 7 bảng: `id` (UUIDv4), `created_at`, `updated_at`, `is_deleted`.
  - Chứa `ActiveRecordManager` giúp mọi lệnh `.objects.all()` tự động lọc bỏ các bản ghi đã xóa mềm (`is_deleted=False`), bảo toàn lịch sử tài chính khi sinh viên bấm xóa nhầm.
- **`core/repositories.py` (và `core/base_repositories.py`)**:
  - Chứa `BaseRepository[T]` áp dụng **Generic Programming** (`TypeVar`), viết sẵn các hàm `get_by_id`, `filter_active`, `create`, `update`, `soft_delete` để các Repository con không phải viết lặp lại.
- **`core/exceptions.py`**:
  - Định nghĩa bảng mã lỗi chuẩn `ErrorCode` và 4 nhóm ngoại lệ nghiệp vụ: `DomainValidationException` (400), `BusinessLogicException` / `InsufficientBalanceException` / `BudgetExceededException` (400), `AccessDeniedException` (403), `ResourceNotFoundException` (404).
  - Hàm `custom_exception_handler`: Bắt mọi lỗi phát sinh và ép về đúng một khung JSON chuẩn duy nhất (`{"success": false, "status": "error", "error_code": "...", "message": "..."}`).
- **`core/responses.py`**:
  - Chứa lớp tiện ích `APIResponse.success()`, `APIResponse.created()`, `APIResponse.error()` giúp tầng View trả về JSON đồng nhất.
- **`core/permissions.py`**:
  - Chứa 2 lớp phân quyền RBAC: `IsAdmin` (chỉ cho phép `role == 'ADMIN'`) và `IsStudentOwner` (sinh viên nào chỉ được xem/sửa đúng ví, giao dịch và ngân sách của chính sinh viên đó).

---

### 3.3. Thư mục `apps/finance/` — Phân Hệ Nghiệp Vụ Tài Chính & Phân Tích Thông Minh

Tại sao đặt `finance` bên trong thư mục `apps/`?
$\rightarrow$ Để tách bạch các ứng dụng nghiệp vụ (`apps/...`) khỏi thư mục cấu hình hệ thống (`config/`, `core/`, `tests/`, `docs/`). Nếu sau này hệ thống mở rộng thêm app `notifications` hay `scholarships` thì chỉ cần đặt vào `apps/` mà thư mục gốc vẫn cực kỳ gọn gàng.

Bên trong `apps/finance/` được chia thành 7 thư mục con tương ứng với từng trách nhiệm:

1. **`apps/finance/models/` (Tách thành 7 file độc lập tương ứng 7 bảng 3NF)**:
   - Tại sao tách thành 7 file (`user.py`, `wallet.py`, `category.py`, `budget.py`, `transaction.py`, `recurring_bill.py`, `alert_log.py`) rồi gom qua `models/__init__.py`?
   - **Trả lời**: Mỗi bảng có các `TextChoices` (Enum), `RegexValidator` (kiểm tra email `@gm.uit.edu.vn`), `CheckConstraint` (`balance >= 0`) và các `@property` riêng. Tách 7 file giúp Thành viên 2 sửa bảng `Wallet` không bao giờ đụng chạm vào file `MonthlyBudget` của Thành viên 3. Và nhờ export trong `models/__init__.py`, Django Migrations vẫn nhận diện đầy đủ như một `models.py` chuẩn.

2. **`apps/finance/repositories/` (`wallet_repo.py`, `transaction_repo.py`, `budget_repo.py`)**:
   - **Vai trò**: Chứa toàn bộ các câu lệnh truy vấn ORM chuyên sâu.
   - **Điểm ăn điểm kỹ thuật**:
     - Trong `wallet_repo.py`: Dùng `select_for_update()` để khóa dòng bản ghi ví khi đang giao dịch, chống lỗi Race Condition (2 request trừ tiền cùng lúc).
     - Trong `transaction_repo.py`: Dùng `select_related("wallet", "category")` để lấy thông tin ví và danh mục chỉ trong 1 câu lệnh `SQL JOIN`, triệt tiêu hoàn toàn lỗi $N+1$ queries.

3. **`apps/finance/services/` (`wallet_service.py`, `transaction_service.py`, `budget_service.py`)**:
   - **Vai trò**: Trái tim xử lý nghiệp vụ tài chính.
   - **Điểm ăn điểm kỹ thuật**: Mọi hàm làm thay đổi tiền bạc (`transfer_between_wallets`, `record_transaction`, `delete_transaction`, `pay_recurring_bill`) đều được gắn `@transaction.atomic`. Nếu bước 1 (trừ tiền ví nguồn) thành công nhưng bước 2 (cộng tiền ví đích hoặc lưu lịch sử giao dịch) gặp lỗi, PostgreSQL tự động **Rollback 100%**, không bao giờ làm sai lệch số dư của sinh viên.

4. **`apps/finance/engines/` (Module Ăn Điểm — OOP, Design Patterns & Machine Learning Serving)**:
   - **`base_analyzer.py`**: Lớp trừu tượng `BaseFinancialAnalyzer(ABC)` thể hiện tính **Trừu tượng (Abstraction)** và **Đóng gói (Encapsulation)** với `_raw_data`, `_dataframe` và Template Method `run_inference()`.
   - **`model_registry.py`**: Lớp `MLModelRegistry` áp dụng **Singleton Pattern** nạp các file mô hình học máy từ thư mục `artifacts/*.joblib` lên RAM đúng 1 lần duy nhất, giúp API phản hồi trong vài mili-giây thay vì phải đọc lại file từ ổ cứng ở mỗi request.
   - **`burn_rate_engine.py`**: Dùng Pandas `.resample('D').sum()`, trung bình trượt 7 ngày (`.rolling(7).mean()`) và `HuberRegressor` của Scikit-learn (kháng nhiễu khoản tiền trọ KTX đầu tháng) để dự báo ngày cạn ví (`predicted_exhaustion_date`) và hạn mức chi tiêu an toàn mỗi ngày (`safe_daily_allowance`).
   - **`anomaly_engine.py`**: Kết hợp `IsolationForest`, kiểm định thống kê `Z-Score` ($\mu + 2.5\sigma$) và `IQR` để tự động bắt các khoản chi tiêu vung tay quá trán.
   - **`risk_classifier.py`**: Dùng `RandomForestClassifier` dự báo xác suất vỡ ngân sách cuối tháng (`SAFE` / `WARNING` / `HIGH_RISK_BROKE`), chấm điểm sức khỏe tài chính thang 0–100 và áp dụng **Strategy Pattern (`SavingStrategy`)** để đưa ra lời khuyên phù hợp.
   - **`exporters.py`**: Áp dụng **Strategy Pattern (`BaseReportExporter`)** với 2 lớp con `CSVReportExporter` và `ExcelReportExporter` cùng ghi đè phương thức đa hình `generate()`.

5. **`apps/finance/serializers/` (5 file theo đúng 5 phân hệ)**:
   - Thực hiện 2 nhiệm vụ tách biệt theo 2 chiều Request–Response của DRF:
     - **Chiều VÀO (`is_valid()`)**: Hỗ trợ `View [V]` kiểm tra tính hợp lệ của dữ liệu đầu vào từ Client (số tiền $> 0$, đúng định dạng UUID).
     - **Chiều RA (`.data`)**: Thay thế HTML Template (`T`) trong kiến trúc REST API để chuyển đổi đối tượng Python (`Model` / `dict`) sang JSON trả về cho Client.

6. **`apps/finance/views/` (5 file `*_views.py` cho 30+ APIs + 1 file `web_views.py` cho Web Dashboard)**:
   - Các lớp `View` / `APIView` cực kỳ ngắn gọn, làm đúng vai trò điều phối (Controller trong MVT): nhận HTTP Request từ `urls.py` → kiểm tra input (`Serializer.is_valid()`) → ủy quyền Tầng Mở Rộng (`Service` / `Engine`) lấy/xử lý dữ liệu từ `Model` → truyền đối tượng qua `Serializer.data` hoặc `templates/finance/dashboard.html` → trả HTTP Response.
   - Gắn đầy đủ `@extend_schema` để tự động sinh tài liệu OpenAPI 3 / Swagger UI chuẩn xác.

7. **`apps/finance/management/commands/seed_data.py`**:
   - Lệnh CLI tùy chỉnh `python manage.py seed_data` giúp giảng viên hoặc thành viên nhóm khi vừa clone code về chỉ cần gõ 1 lệnh là có ngay 2 tài khoản, 3 ví, 6 danh mục, 4 hóa đơn KTX, 200 giao dịch mẫu trải đều 60 ngày và 3 file `.joblib` để demo biểu đồ dự báo ngay lập tức.

---

### 3.4. Các Thư Mục Phụ Trợ Ở Cấp Gốc (`artifacts/`, `tests/`, `postman/`, `docs/`, `.github/`, `.agents/`)
- **`artifacts/`**: Chứa 3 mô hình học máy đã huấn luyện và đóng gói bằng `joblib` (`burn_rate_huber.joblib`, `anomaly_iforest.joblib`, `risk_rf_classifier.joblib`). Tách riêng thư mục này để chứng minh kỹ thuật **ML Model Serialization & Serving** thực thụ.
- **`tests/`**: Chứa `conftest.py` (khởi tạo dữ liệu mẫu bằng Pytest Fixtures) và 5 file test (`test_core.py`, `test_auth.py`, `test_wallet_transfer.py`, `test_transactions.py`, `test_analytics_engine.py`) gồm **24 kịch bản kiểm thử tự động**.
- **`postman/`**: Chứa bộ `IE221_Collection.json` (30 requests) và `IE221_Environment.json` tích hợp sẵn script tự động lưu Token JWT khi bấm **Run Collection**.
- **`.github/` & `.agents/skills/`**: Lưu quy chuẩn Coding Conventions, mẫu Pull Request và SOP làm việc nhóm để đảm bảo code đồng nhất.

---

## 4. Phân Tích Ưu Điểm & Nhược Điểm Của Kiến Trúc Này (Dùng Để Trả Lời Khi Thầy Hỏi Về Trade-offs)

Trong kỹ thuật phần mềm (Software Engineering), không có kiến trúc nào chỉ có ưu điểm mà không có sự đánh đổi (trade-off). Khi thầy hỏi: *"Làm kiến trúc phân tầng nhiều thư mục như vậy có ưu điểm gì và nhược điểm gì?"*, bạn hãy trả lời thẳng thắn cả 2 mặt sau (thầy sẽ đánh giá rất cao tư duy kiến trúc của nhóm):

### 4.1. Năm Ưu Điểm Lớn (Pros)
1. **Phân tách trách nhiệm rõ ràng (High Cohesion, Low Coupling)**:
   - Sửa câu lệnh truy vấn SQL/ORM thì chỉ mở `repositories/`.
   - Sửa công thức tính ngân sách hay quy tắc chuyển tiền thì chỉ mở `services/`.
   - Thay đổi thuật toán học máy từ `LinearRegression` sang `HuberRegressor` thì chỉ mở `engines/`.
   - Các tầng khác hoàn toàn không bị ảnh hưởng.
2. **Làm việc nhóm 3 người song song không bị đụng code (Zero Merge Conflicts)**:
   - Thành viên 1 làm trong `core/` và `engines/`.
   - Thành viên 2 làm trong `wallet_*` và `transaction_*`.
   - Thành viên 3 làm trong `auth_*` và `budget_*`.
   - Mỗi người làm trên những file độc lập, ghép nhánh Git (`git merge`) cực kỳ trơn tru.
3. **Kiểm thử tự động dễ dàng và nhanh chóng (High Testability)**:
   - Có thể viết Unit Test trực tiếp cho `BurnRateAnalyzer`, `AnomalyDetectionEngine` hoặc `BaseRepository` chỉ bằng một mảng dữ liệu Python thuần mà không cần dựng Web Server hay gửi HTTP Request.
4. **Tái sử dụng nghiệp vụ an toàn (Reusability & ACID Consistency)**:
   - Hàm `TransactionService.record_transaction()` được gọi chung bởi cả API thêm giao dịch thủ công lẫn API thanh toán hóa đơn định kỳ KTX, đảm bảo mọi nơi đều được kiểm tra số dư, khóa dòng `select_for_update()` và chấm điểm Anomaly như nhau.
5. **Khớp 1:1 với Sơ đồ Lớp (StarUML Class Diagram)**:
   - Thể hiện trọn vẹn 4 tính chất OOP (Đóng gói, Kế thừa, Trừu tượng, Đa hình) và 4 Design Patterns (Repository, Service Layer, Singleton, Strategy) — đáp ứng đúng tiêu chí mốc điểm 9.5–10.0 của môn IE221.

---

### 4.2. Ba Nhược Điểm / Sự Đánh Đổi (Cons / Trade-offs) & Cách Nhóm Khắc Phục
1. **Số lượng file nhiều hơn và tốn công viết khung ban đầu (Boilerplate Code)**:
   - *Nhược điểm*: Với một API CRUD đơn giản (ví dụ đổi tên danh mục), thay vì viết 5 dòng bằng `ModelViewSet` trong 1 file, ta phải đi qua `View -> Service -> Repository -> Model`, làm tăng số lượng file cần tạo ban đầu.
   - *Cách nhóm khắc phục*: Nhóm đã xây dựng lớp `BaseModel` và `BaseRepository[T]` (Generic CRUD) ở tầng `core/`. Nhờ đó các thao tác cơ bản (`get_by_id`, `create`, `update`, `soft_delete`) đều được kế thừa tự động, giảm 70% lượng code lặp lại.
2. **Đường cong học tập (Learning Curve) cho thành viên mới**:
   - *Nhược điểm*: Thành viên mới nhìn vào 5 tầng có thể bối rối không biết nên đặt hàm mới ở `Repository`, `Service` hay `Engine`.
   - *Cách nhóm khắc phục*: Nhóm đã viết sẵn tài liệu hướng dẫn `docs/core_usage_guide.md` và bộ quy trình 5 bước trong `.agents/skills/ie221-feature-workflow-git-testing/SKILL.md` quy định rõ từng bước từ trong ra ngoài.
3. **Chi phí gọi qua nhiều lớp trung gian (Indirection Overhead)**:
   - *Nhược điểm*: Mỗi request đi qua thêm 1–2 lời gọi hàm Python giữa `View -> Service -> Repository`.
   - *Đánh giá thực tế*: Trong Python, chi phí gọi hàm (function call overhead) chỉ tính bằng nano-giây, hoàn toàn không đáng kể so với thời gian truy vấn CSDL hay mạng I/O. Ngược lại, nhờ tầng `Repository` gom gọn `select_related("wallet", "category")` và tầng `MLModelRegistry` (Singleton) giữ model trên RAM, hiệu năng tổng thể của API lại **nhanh hơn rất nhiều** so với việc viết ORM rời rạc trong View.
