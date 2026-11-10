# Bản Nháp Nội Dung Báo Cáo Chuẩn `Template_IE221_New.docx` (Chống Bẫy Trừ Điểm)

> [!IMPORTANT]
> **Quy tắc bắt buộc khi copy sang `Template_IE221_New.docx`**:
> 1. **Trang bìa**: Ghi đúng tên đề tài (tối đa 3 dòng in hoa), tên các thành viên + MSSV. **TUYỆT ĐỐI KHÔNG GHI TÊN GIẢNG VIÊN HƯỚNG DẪN (GVHD)**.
> 2. **Độ dài phần nội dung chính (Mục 1 -> Mục 5)**: Từ **5 đến tối đa 10 trang** (Không có lời cảm ơn, không có mục lục, không có danh mục hình/bảng).
> 3. **Không chèn Code hoặc Ảnh chụp màn hình** vào Mục 1 -> Mục 5 (Đẩy toàn bộ ảnh chụp Swagger/Postman/Pytest và đoạn code xuống 4 Phụ lục ở cuối file).

---

## MỤC 1. GIỚI THIỆU ĐỀ TÀI (Đúng 10 dòng - 2 đoạn văn)

Đề tài tập trung xây dựng hệ thống Backend RESTful API phục vụ quản lý ngân sách, theo dõi dòng tiền và phân tích dự báo chi tiêu cá nhân dành cho sinh viên, bao gồm các nghiệp vụ từ thiết lập hạn mức theo danh mục, ghi nhận giao dịch thu chi, quản lý hóa đơn định kỳ tại ký túc xá đến cảnh báo vượt ngưỡng tài chính. Để giải quyết bài toán, nhóm sử dụng ngôn ngữ Python với nền tảng Django và Django REST Framework, nâng cấp kiến trúc MVT truyền thống bằng mô hình phân tầng Service-Repository kết hợp nguyên lý lập trình hướng đối tượng (OOP), hệ quản trị cơ sở dữ liệu quan hệ máy chủ PostgreSQL và thư viện Pandas, Scikit-learn để xử lý chuỗi thời gian. Kết quả thực hiện, nhóm đã hoàn thiện hệ thống gồm 7 bảng cơ sở dữ liệu chuẩn hóa 3NF, 22 chức năng nghiệp vụ phân quyền cho 2 nhóm người dùng (Admin và Sinh viên) cùng 30 RESTful APIs được tài liệu hóa trên Swagger UI và kiểm thử tự động bằng Pytest.

Trong đề tài này, chúng tôi tự phân tích yêu cầu, thiết kế sơ đồ lớp (Class Diagram), lược đồ cơ sở dữ liệu và trực tiếp phát triển toàn bộ mã nguồn xử lý nghiệp vụ dựa trên kiến thức môn Kỹ thuật lập trình Python mà không sao chép từ bất kỳ đồ án hay dự án mẫu có sẵn nào. Các thư viện mã nguồn mở của Python bao gồm Django, Django REST Framework, Pandas và Scikit-learn được sử dụng đúng theo tài liệu hướng dẫn chính thức được trích dẫn tại mục Tài liệu tham khảo [1], [2].

---

## MỤC 2. MÔ TẢ CƠ SỞ DỮ LIỆU (7 Bảng Chuẩn Hóa 3NF)

**Câu dẫn trước hình (Bắt buộc)**: *Lược đồ cơ sở dữ liệu quan hệ của hệ thống quản lý và phân tích chi tiêu sinh viên gồm 7 thực thể đạt chuẩn 3NF được trình bày tại Hình 2.1 dưới đây.*

*(Chèn hình ERD 7 bảng từ `docs/uml_templates.md` vào đây)*

Hệ thống sử dụng hệ quản trị cơ sở dữ liệu PostgreSQL 16 với 7 bảng kế thừa từ lớp trừu tượng `BaseModel` (`id` kiểu `UUIDv4`, `created_at`, `updated_at`, `is_deleted` hỗ trợ xóa mềm):
1. **`UserAccount` (`finance_user_account`)**: Lưu trữ thông tin định danh người dùng với ràng buộc email thuộc tên miền trường (`@gm.uit.edu.vn` hoặc `@uit.edu.vn`), mã số sinh viên (`student_code`), vai trò phân quyền (`ADMIN`, `STUDENT`), hạn mức trợ cấp tháng (`monthly_income_limit`) và khu vực nội trú (`dorm_area`).
2. **`Wallet` (`finance_wallet`)**: Quản lý các nguồn tiền của sinh viên (Tiền mặt, Ví điện tử MoMo, Tài khoản Ngân hàng) với ràng buộc toàn vẹn `CheckConstraint` đảm bảo số dư (`balance`) luôn lớn hơn hoặc bằng 0.
3. **`ExpenseCategory` (`finance_expense_category`)**: Phân loại danh mục thu nhập (`INCOME`) và chi tiêu (`EXPENSE`), kèm cờ `is_essential` giúp phân tách chi tiêu thiết yếu (ăn uống, học tập, KTX) và chi tiêu giải trí.
4. **`MonthlyBudget` (`finance_monthly_budget`)**: Lưu trữ hạn mức ngân sách được phân bổ (`allocated_amount`), số tiền đã chi lũy kế (`spent_amount`) và ngưỡng cảnh báo (`alert_threshold_pct`, mặc định 80%) theo từng cặp `(user, category, month, year)`.
5. **`ExpenseTransaction` (`finance_expense_transaction`)**: Ghi nhận chi tiết từng giao dịch thu, chi hoặc chuyển khoản nội bộ, tích hợp trường `is_anomaly` và `anomaly_score` phục vụ bộ máy phát hiện giao dịch bất thường.
6. **`RecurringBill` (`finance_recurring_bill`)**: Quản lý các khoản hóa đơn cố định định kỳ hàng tháng tại ký túc xá (tiền phòng KTX, điện nước, gói cước 4G) với ngày đến hạn (`due_day`) và trạng thái thanh toán (`PENDING`, `PAID`, `OVERDUE`).
7. **`BudgetAlertLog` (`finance_budget_alert_log`)**: Lưu nhật ký cảnh báo tự động khi chi tiêu chạm ngưỡng 80% (`WARNING_80`), vượt 100% (`CRITICAL`), phát hiện giao dịch đột biến (`ANOMALY`) hoặc nguy cơ cạn ví sớm (`BURN_RATE`).

---

## MỤC 3 & 4. THIẾT KẾ HỆ THỐNG, KIẾN TRÚC MVT MỞ RỘNG & GIẢI PHÁP KỸ THUẬT

### 3.1. Kiến trúc Phân tầng Hybrid MVT kết hợp Service - Repository & ML Serving Engine
Hệ thống tuân thủ mô hình MVT (Model - View - Template) của Django nhưng được phân lớp rõ ràng để đảm bảo nguyên lý Single Responsibility:
- **Tầng View (`views/`, `urls.py`)**: Tiếp nhận HTTP Request, kiểm tra phân quyền RBAC (`IsAdmin`, `IsStudentOwner`), xác thực dữ liệu đầu vào qua Serializer và điều phối xuống tầng Service/Engine.
- **Tầng Template & Representation (`serializers/`, `templates/`)**: Sử dụng DRF Serializers để chuẩn hóa cấu trúc JSON cho 30 RESTful APIs và kết hợp `dashboard.html` hiển thị biểu đồ trực quan.
- **Tầng Model & Domain (`models/`, `repositories/`, `services/`, `engines/`)**: Tách biệt hoàn toàn truy vấn ORM trong `repositories/`, xử lý giao dịch nguyên tử `@transaction.atomic` kèm khóa dòng `select_for_update()` trong `services/`, và thực thi 3 mô hình học máy trong `engines/`.

### 3.2. Thiết kế Hướng đối tượng (OOP) & Design Patterns
**Câu dẫn trước hình**: *Sơ đồ lớp (Class Diagram) thể hiện mối quan hệ kế thừa, đóng gói và đa hình giữa các tầng kiến trúc được minh họa tại Hình 3.1.*

*(Chèn hình StarUML Class Diagram từ `docs/uml_templates.md` vào đây)*

- **Tính Trừu tượng (Abstraction)**: Lớp cơ sở trừu tượng `BaseFinancialAnalyzer(ABC)` định nghĩa khung phân tích chuẩn thông qua các phương thức trừu tượng `@abstractmethod preprocess()` và `execute_analysis()`, đồng thời cung cấp phương thức khuôn mẫu (Template Method) `run_inference()`.
- **Tính Kế thừa (Inheritance)**: Toàn bộ 7 thực thể CSDL kế thừa từ `BaseModel` (`TimeStampedSoftDeleteModel`). Ba bộ máy phân tích `BurnRateAnalyzer`, `AnomalyDetectionEngine` và `RiskClassifier` kế thừa từ `BaseFinancialAnalyzer`.
- **Tính Đóng gói (Encapsulation)**: Các thuộc tính tính toán nội bộ (`_raw_data`, `_dataframe`, `_daily_burn_rate`, `_safety_threshold`) được bảo vệ bằng tiền tố `_` và chỉ truy xuất an toàn qua `@property`.
- **Tính Đa hình (Polymorphism) & Strategy Pattern / Singleton Pattern**:
  - **Singleton Pattern (`MLModelRegistry`)**: Đảm bảo các mô hình học máy đã đóng gói (`artifacts/*.joblib`) chỉ nạp lên bộ nhớ RAM đúng một lần duy nhất trong suốt vòng đời ứng dụng.
  - **Strategy Pattern (`SavingStrategy` & `BaseReportExporter`)**: Linh hoạt chuyển đổi thuật toán khuyến nghị chi tiêu (`BalancedEarlyMonthStrategy` so với `EmergencyEndOfMonthStrategy`) và định dạng xuất báo cáo (`CSVReportExporter` so với `ExcelReportExporter`).

### 3.3. Giải pháp Kỹ thuật cho Module Tâm đắc nhất: Smart Burn-Rate Forecaster & Anomaly Serving Engine
1. **Chuẩn hóa chuỗi thời gian bằng Pandas**: Lịch sử chi tiêu 60 ngày của sinh viên được trích xuất qua `TransactionRepository` và nạp vào Pandas DataFrame. Hệ thống thực hiện `.resample('D').sum()` để điền đầy các ngày không phát sinh giao dịch bằng giá trị `0.0`, sau đó tính trung bình trượt 7 ngày (`.rolling(window=7, min_periods=1).mean()`) nhằm làm mượt biến động ngắn hạn cuối tuần.
2. **Dự báo ngày cạn ví bằng Hồi quy Kháng nhiễu (`HuberRegressor`)**: Do chi tiêu sinh viên thường xuất hiện các khoản chi cố định lớn vào đầu tháng (như tiền phòng KTX, học phí), hồi quy bình phương tối thiểu thông thường (`LinearRegression`) dễ bị kéo lệch hệ số góc. Nhóm sử dụng `HuberRegressor` của thư viện Scikit-learn trên chuỗi chi tiêu lũy kế để ước lượng tốc độ tiêu tiền thực tế $\hat{\beta}_1$, kết hợp trọng số với trung bình trượt 7 ngày:
   $$B_{\text{effective}} = 0.6 \cdot \hat{\beta}_1 + 0.4 \cdot \overline{E}_{7d}$$
   Từ đó dự báo chính xác số ngày còn trụ được $D_{\text{left}} = \lfloor \text{Balance} / B_{\text{effective}} \rfloor$, ngày dự kiến cạn ví (`predicted_exhaustion_date`) và hạn mức chi tiêu an toàn mỗi ngày (`safe_daily_allowance`).
3. **Phát hiện bất thường kết hợp `IsolationForest`, Z-Score và IQR**: Mỗi khi sinh viên ghi nhận khoản chi mới, hệ thống tính điểm chuẩn hóa $Z = (x - \mu)/\sigma$ và ngưỡng tứ phân vị $Q_3 + 1.5 \times \text{IQR}$ kết hợp mô hình `IsolationForest`. Nếu $Z \ge 2.5$ hoặc vượt ngưỡng IQR, giao dịch lập tức được gắn cờ `is_anomaly = True` và sinh cảnh báo vào bảng `BudgetAlertLog`.

---

## MỤC 5. KẾT LUẬN (Đúng 10 dòng - Tóm tắt kết quả & Hạn chế, KHÔNG ghi hướng phát triển)

Đồ án đã hoàn thành trọn vẹn mục tiêu xây dựng hệ thống Backend RESTful API quản lý ngân sách và phân tích dự báo chi tiêu dành cho sinh viên trường Đại học Công nghệ Thông tin trên nền tảng Django và Django REST Framework. Về mặt kiến trúc phần mềm, hệ thống đã áp dụng chặt chẽ mô hình MVT mở rộng kết hợp mẫu thiết kế Service-Repository, Singleton và Strategy Pattern trên cơ sở dữ liệu PostgreSQL gồm 7 bảng đạt chuẩn 3NF. Nhóm đã hiện thực hóa đầy đủ 5 phân hệ với 22 chức năng nghiệp vụ và 30 RESTful APIs, đảm bảo tính toàn vẹn giao dịch tiền tệ bằng cơ chế khóa dòng nguyên tử và phân quyền truy cập rõ ràng giữa Quản trị viên và Sinh viên. Đặc biệt, module phân tích thông minh sử dụng Pandas và Scikit-learn đã giải quyết hiệu quả bài toán dự báo ngày cạn ngân sách bằng hồi quy kháng nhiễu HuberRegressor, phát hiện chi tiêu đột biến bằng IsolationForest kết hợp kiểm định Z-Score và chấm điểm sức khỏe tài chính bằng RandomForestClassifier. Toàn bộ 30 APIs đã được chuẩn hóa tài liệu trên giao diện Swagger UI, đóng gói kịch bản kiểm thử Postman Collection và vượt qua 100% các kịch bản kiểm thử tự động bằng công cụ Pytest. Bên cạnh các kết quả đạt được, hệ thống hiện vẫn còn hạn chế là dữ liệu giao dịch thu chi cần sinh viên nhập thủ công hoặc kích hoạt từ hóa đơn định kỳ chứ chưa đồng bộ trực tiếp theo thời gian thực với cổng thông báo biến động số dư của các ngân hàng thương mại. Ngoài ra, các mô hình học máy dự báo chuỗi thời gian hiện mới xét đến biến động lịch sử chi tiêu cá nhân mà chưa tích hợp thêm các biến ngoại sinh như lịch thi học kỳ hay biến động giá cả sinh hoạt tại khu vực Làng Đại học.

---

## TÀI LIỆU THAM KHẢO

[1] Django Software Foundation, *Django 5.1 Official Documentation*, https://docs.djangoproject.com/en/5.1/, truy cập năm 2026.  
[2] Encode OSS Ltd., *Django REST Framework Official Guide*, https://www.django-rest-framework.org/, truy cập năm 2026.  
[3] Wes McKinney & Pandas Development Team, *pandas: powerful Python data analysis toolkit*, https://pandas.pydata.org/docs/, truy cập năm 2026.  
[4] F. Pedregosa et al., *Scikit-learn: Machine Learning in Python*, Journal of Machine Learning Research (JMLR), vol. 12, pp. 2825–2830, https://scikit-learn.org/stable/, truy cập năm 2026.

---

## 4 PHỤ LỤC BẮT BUỘC (ĐẶT Ở CUỐI FILE WORD)

### PHỤ LỤC 1: BẢNG PHÂN CÔNG NHIỆM VỤ CÁC THÀNH VIÊN

| STT | Họ và Tên | MSSV | Vai trò | Nhiệm vụ cụ thể | Tỷ lệ hoàn thành |
| :-: | :--- | :---: | :--- | :--- | :---: |
| 1 | **Trương Huy Hoàng** | *(Điền MSSV)* | Trưởng nhóm / System Architect & ML Engine | Thiết lập kiến trúc Hybrid MVT, `core/` (`BaseModel`, `BaseRepository`, `CustomExceptionHandler`), kết nối PostgreSQL 16; hiện thực Module 5 (`analytics_engine`: `BaseFinancialAnalyzer`, `MLModelRegistry`, `BurnRateAnalyzer`, `AnomalyDetectionEngine`, `RiskClassifier`, `BaseReportExporter`); viết Unit Test Engine và tổng hợp Báo cáo Word. | 100% |
| 2 | **Thành viên 2** | *(Điền MSSV)* | Backend Core Developer | Hiện thực Models, Repositories, Services (`@transaction.atomic`) và Serializers cho Module 2 (`wallet_mgmt`) và Module 3 (`transaction` & `RecurringBill` KTX) gồm 15 RESTful APIs; viết script `seed_data.py` (200 giao dịch mẫu) và vẽ sơ đồ ERD 7 bảng + StarUML Class Diagram. | 100% |
| 3 | **Thành viên 3** | *(Điền MSSV)* | Backend Security, Budget & QA | Hiện thực Module 1 (`auth_iam`: SimpleJWT, RBAC `IsAdmin`, `IsStudentOwner`) và Module 4 (`budget_alert`: hạn mức tháng, clone ngân sách, cảnh báo `WARNING_80`/`CRITICAL`) gồm 11 RESTful APIs; cấu hình Swagger UI (`drf-spectacular`), đóng gói Postman Collection 30 APIs và chuẩn bị Slide bảo vệ. | 100% |

---

### PHỤ LỤC 2: BẢNG TÓM TẮT KẾT QUẢ THỰC HIỆN (22 CHỨC NĂNG - 30 RESTFUL APIS)

| STT | Phân hệ | Tên Chức năng Nghiệp vụ | HTTP Method & RESTful Endpoint | Phân quyền | Trạng thái |
| :-: | :--- | :--- | :--- | :---: | :---: |
| 1 | **M1. Auth & IAM** | 1. Đăng ký tài khoản email UIT | `POST /api/v1/auth/register/` | Public | Hoàn thành |
| 2 | **M1. Auth & IAM** | 2. Đăng nhập cấp phát JWT | `POST /api/v1/auth/login/` | Public | Hoàn thành |
| 3 | **M1. Auth & IAM** | 3. Làm mới Access Token | `POST /api/v1/auth/token/refresh/` | Public | Hoàn thành |
| 4 | **M1. Auth & IAM** | 4. Xem & cập nhật hồ sơ cá nhân | `GET, PATCH /api/v1/users/me/` | Student/Admin | Hoàn thành |
| 5 | **M1. Auth & IAM** | 5. Cập nhật trợ cấp tháng & khu vực KTX | `PATCH /api/v1/users/me/allowance/` | Student | Hoàn thành |
| 6 | **M1. Auth & IAM** | 6. Admin thống kê & khóa/mở tài khoản | `GET /api/v1/admin/users/`, `PATCH .../toggle-status/` | Admin | Hoàn thành |
| 7 | **M2. Wallets** | 7. Tạo ví mới & Liệt kê danh sách ví | `POST, GET /api/v1/wallets/` | Student | Hoàn thành |
| 8 | **M2. Wallets** | 8. Xem chi tiết & Cập nhật thông tin ví | `GET, PUT /api/v1/wallets/{wallet_id}/` | Student | Hoàn thành |
| 9 | **M2. Wallets** | 9. Xóa mềm ví tiền (`Soft Delete`) | `DELETE /api/v1/wallets/{wallet_id}/` | Student | Hoàn thành |
| 10 | **M2. Wallets** | 10. Chuyển tiền nội bộ nguyên tử giữa 2 ví | `POST /api/v1/wallets/transfer/` | Student | Hoàn thành |
| 11 | **M3. Transactions** | 11. Quản lý danh mục Thu/Chi & Thiết yếu | `GET, POST /api/v1/categories/`, `PUT, DELETE .../{id}/` | Student | Hoàn thành |
| 12 | **M3. Transactions** | 12. Ghi nhận giao dịch Thu/Chi & Chấm Anomaly | `POST /api/v1/transactions/` | Student | Hoàn thành |
| 13 | **M3. Transactions** | 13. Tra cứu & Lọc giao dịch đa tiêu chí | `GET /api/v1/transactions/` | Student | Hoàn thành |
| 14 | **M3. Transactions** | 14. Sửa/Xóa mềm giao dịch & Hoàn tiền ví | `PUT, DELETE /api/v1/transactions/{transaction_id}/` | Student | Hoàn thành |
| 15 | **M3. Transactions** | 15. Quản lý hóa đơn định kỳ KTX (Phòng, 4G) | `GET, POST /api/v1/recurring-bills/` | Student | Hoàn thành |
| 16 | **M3. Transactions** | 16. Thanh toán tự động hóa đơn định kỳ KTX | `POST /api/v1/recurring-bills/{bill_id}/pay/` | Student | Hoàn thành |
| 17 | **M4. Budgets** | 17. Thiết lập & Theo dõi ngân sách tháng | `POST, GET /api/v1/budgets/` | Student | Hoàn thành |
| 18 | **M4. Budgets** | 18. Điều chỉnh / Xóa mềm hạn mức ngân sách | `PUT, DELETE /api/v1/budgets/{budget_id}/` | Student | Hoàn thành |
| 19 | **M4. Budgets** | 19. Sao chép cấu hình ngân sách tháng trước | `POST /api/v1/budgets/clone-previous/` | Student | Hoàn thành |
| 20 | **M4. Budgets** | 20. Xem cảnh báo & Đánh dấu đã đọc | `GET /api/v1/alerts/`, `PATCH /api/v1/alerts/{id}/read/` | Student | Hoàn thành |
| 21 | **M5. ML Engine** | 21. Dự báo tốc độ đốt tiền & Ngày cạn ví | `GET /api/v1/analytics/burn-rate-forecast/` | Student | Hoàn thành |
| 22 | **M5. ML Engine** | 22. Quét Anomaly, Chấm điểm Sức khỏe & Xuất Excel | `POST /api/v1/analytics/detect-anomalies/`, `GET .../financial-health/`, `GET .../export/` | Student | Hoàn thành |

---

### PHỤ LỤC 3: DANH MỤC HÌNH CHỤP MINH CHỨNG (ĐẶT TẠI PHỤ LỤC HÌNH)

1. **Hình P3.1**: Giao diện tài liệu hóa 30 RESTful APIs trên Swagger UI (`http://127.0.0.1:8000/api/schema/swagger/`).
2. **Hình P3.2**: Kết quả thực thi API Dự báo tốc độ đốt tiền & ngày cạn ví (`GET /api/v1/analytics/burn-rate-forecast/`).
3. **Hình P3.3**: Kết quả thực thi API Chấm điểm sức khỏe tài chính & `RiskClassifier` (`GET /api/v1/analytics/financial-health/`).
4. **Hình P3.4**: Giao diện Web Dashboard trực quan Hybrid MVT (`http://127.0.0.1:8000/dashboard/`).
5. **Hình P3.5**: Kết quả chạy tự động 20 kịch bản kiểm thử bằng `pytest -v` (20 passed in 11s).
6. **Hình P3.6**: Kết quả chạy Postman Collection Runner vượt qua toàn bộ 30 requests.

---

### PHỤ LỤC 4: CÁC ĐOẠN MÃ NGUỒN CỐT LÕI (ĐẶT TẠI PHỤ LỤC CODE)

- Trích dẫn 4 đoạn code tiêu biểu:
  1. Lớp trừu tượng `BaseFinancialAnalyzer(ABC)` trong `apps/finance/engines/base_analyzer.py`.
  2. Lớp `MLModelRegistry` (Singleton Pattern) trong `apps/finance/engines/model_registry.py`.
  3. Lớp `BurnRateAnalyzer` (`HuberRegressor` + Pandas `.resample('D').sum()`) trong `apps/finance/engines/burn_rate_engine.py`.
  4. Phương thức `record_transaction` bọc `@transaction.atomic` + `select_for_update()` trong `apps/finance/services/transaction_service.py`.

