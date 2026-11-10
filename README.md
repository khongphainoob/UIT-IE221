# XÂY DỰNG HỆ THỐNG BACKEND RESTFUL API QUẢN LÝ VÀ PHÂN TÍCH DỰ BÁO CHI TIÊU SINH VIÊN

> **Môn học**: IE221 - Kỹ thuật lập trình Python (Trường Đại học Công nghệ Thông tin - ĐHQG TP.HCM)  
> **Cơ sở áp dụng**: Django Framework, Django REST Framework, Mô hình MVT kết hợp Service-Repository Pattern, PostgreSQL Server, Pandas, Scikit-learn  
> **GitHub Repository**: https://github.com/khongphainoob/UIT-IE221.git

---

## 1. Bản Mô tả Đồ án Chuẩn (Mục 1 Báo cáo: 10 dòng - 2 đoạn)

**Đoạn 1 (Làm gì - Công cụ/Giải pháp - Kết quả đạt được):**  
Đề tài tập trung xây dựng hệ thống Backend RESTful API phục vụ quản lý ngân sách, theo dõi dòng tiền và phân tích dự báo chi tiêu cá nhân dành cho sinh viên, bao gồm các nghiệp vụ từ thiết lập hạn mức theo danh mục, ghi nhận giao dịch thu chi, quản lý hóa đơn định kỳ tại ký túc xá đến cảnh báo vượt ngưỡng tài chính. Để giải quyết bài toán, nhóm sử dụng ngôn ngữ Python với nền tảng Django và Django REST Framework, nâng cấp kiến trúc MVT truyền thống bằng mô hình phân tầng Service-Repository kết hợp nguyên lý lập trình hướng đối tượng (OOP), hệ quản trị cơ sở dữ liệu quan hệ máy chủ PostgreSQL và thư viện Pandas, Scikit-learn để xử lý chuỗi thời gian. Kết quả thực hiện, nhóm đã hoàn thiện hệ thống gồm 7 bảng cơ sở dữ liệu chuẩn hóa 3NF, 22 chức năng nghiệp vụ phân quyền cho 2 nhóm người dùng (Admin và Sinh viên) cùng 30 RESTful APIs được tài liệu hóa trên Swagger UI và kiểm thử tự động bằng Pytest.

**Đoạn 2 (Cam kết tính minh bạch đề tài - Bắt buộc để không bị trừ điểm):**  
Trong đề tài này, chúng tôi tự phân tích yêu cầu, thiết kế sơ đồ lớp (Class Diagram), lược đồ cơ sở dữ liệu và trực tiếp phát triển toàn bộ mã nguồn xử lý nghiệp vụ dựa trên kiến thức môn Kỹ thuật lập trình Python mà không sao chép từ bất kỳ đồ án hay dự án mẫu có sẵn nào. Các thư viện mã nguồn mở của Python bao gồm Django, Django REST Framework, Pandas và Scikit-learn được sử dụng đúng theo tài liệu hướng dẫn chính thức được trích dẫn tại mục Tài liệu tham khảo [1], [2].

---

## 2. Kiến trúc Kỹ thuật: Chuẩn Mô hình MVT Kết hợp Mở rộng Module

- **M - Model & Domain Layer (`models/`, `repositories/`, `services/`, `engines/`)**:
  - `models/`: Định nghĩa 7 bảng CSDL chuẩn 3NF kế thừa từ `BaseModel` (`TimeStampedSoftDeleteModel`).
  - `repositories/`: Đóng gói các câu lệnh truy vấn ORM (`select_related`, `select_for_update`, `aggregate`).
  - `services/`: Xử lý nghiệp vụ giao dịch thu/chi, chuyển tiền nội bộ, kiểm tra hạn mức ngân sách và bảo toàn ACID bằng `@transaction.atomic`.
  - `engines/`: Module độc lập chuyển dữ liệu sang Pandas DataFrame để chạy 3 bài toán ML Serving (`BurnRateForecaster`, `SpendingAnomalyDetector`, `RiskClassifier`) cùng `MLModelRegistry` (Singleton Pattern).
- **V - View Layer (`views/`, `urls.py`)**:
  - Tiếp nhận HTTP Request từ bộ định tuyến URL, kiểm tra quyền truy cập RBAC (`IsAdmin`, `IsStudentOwner`), ủy quyền cho tầng `Service`/`Engine` và trả kết quả.
- **T - Template & Representation Layer (`templates/`, `serializers/`)**:
  - `templates/finance/dashboard.html`: Giao diện HTML nhúng Chart.js trực quan hóa dòng tiền & dự báo Burn-rate.
  - `serializers/`: Định dạng cấu trúc JSON chuẩn trả về cho 30 RESTful APIs.

### Cấu trúc Thư mục Dự án (Phẳng & Chuẩn Git Root)
```text
UIT-IE221/ (Thư mục gốc ĐỒ ÁN)
├── .github/
│   ├── copilot-instructions.md     # Quy chuẩn Coding Conventions & Architecture Guardrails
│   ├── PULL_REQUEST_TEMPLATE.md    # Mẫu tạo Pull Request nghiệm thu task
│   └── ISSUE_TEMPLATE/
│       └── feature_task.md         # Mẫu giao Task phát triển tính năng/API
├── .agents/
│   └── skills/
│       ├── ie221-project-conventions/SKILL.md       # Skill giữ chuẩn kiến trúc 5 tầng & chống trừ điểm
│       └── ie221-feature-workflow-git-testing/SKILL.md # Skill SOP từ Pull, Branch, Code, Test đến Đóng Task
├── Dockerfile                      # Đóng gói container Django REST API
├── docker-compose.yml              # Khởi động PostgreSQL 16 (cổng 5433) & Backend API (cổng 8000)
├── manage.py
├── pytest.ini
├── requirements.txt
├── .env                            # Cấu hình kết nối PostgreSQL 16 (student_expense_db)
├── artifacts/                      # Nơi lưu trữ các model ML đóng gói (*.joblib)
├── config/                         # Cấu hình dự án (settings.py, urls.py, wsgi.py, asgi.py)
├── core/                           # Tầng cơ sở (models.py, repositories.py, exceptions.py, permissions.py)
├── apps/
│   └── finance/
│       ├── models/                 # [M] 7 bảng CSDL chuẩn 3NF
│       ├── repositories/           # [M] Data Access Layer (WalletRepo, TransactionRepo, BudgetRepo)
│       ├── services/               # [M] Business Logic Layer (@transaction.atomic)
│       ├── engines/                # [M] Module Ăn Điểm ML Serving & Strategy Pattern
│       │   ├── base_analyzer.py        # BaseFinancialAnalyzer(ABC)
│       │   ├── model_registry.py       # MLModelRegistry (Singleton Pattern)
│       │   ├── burn_rate_engine.py     # HuberRegressor + LinearRegression + Rolling 7D
│       │   ├── anomaly_engine.py       # IsolationForest + Z-Score + IQR
│       │   ├── risk_classifier.py      # RandomForestClassifier + SavingStrategy
│       │   └── exporters.py            # CSVReportExporter & ExcelReportExporter
│       ├── serializers/            # [T] DRF Serializers (Template JSON)
│       ├── templates/finance/      # [T] HTML Dashboard (dashboard.html + Chart.js)
│       ├── views/                  # [V] 30+ RESTful APIViews & Hybrid MVT TemplateView
│       └── management/commands/seed_data.py # Seed 200 giao dịch mẫu trong 60 ngày
├── postman/                        # Bộ Postman Collection 30 APIs & Environment
├── docs/                           # ERD, StarUML Class Diagram, Bản nháp Báo cáo Word & Kịch bản Demo
└── tests/                          # 20 kịch bản kiểm thử tự động bằng Pytest
```

---

## 3. Thiết kế Cơ sở Dữ liệu (7 Bảng - Chuẩn 3NF)

| STT | Tên Bảng (Model) | Vai trò & Các trường cốt lõi | Quan hệ (Relationships) |
| :-: | :--- | :--- | :--- |
| 1 | **`UserAccount`** | Tài khoản người dùng (`id`, `email`, `student_code`, `full_name`, `role`: ADMIN/STUDENT, `monthly_income_limit`, `dorm_area`) | 1-N với `Wallet`, `MonthlyBudget`, `RecurringBill`, `ExpenseTransaction`, `BudgetAlertLog` |
| 2 | **`Wallet`** | Ví/Nguồn tiền của sinh viên (`id`, `user_id`, `name`/`wallet_name`: Tiền mặt/MoMo/Ngân hàng, `balance`/`current_balance`, `currency`, `is_active`) | N-1 với `UserAccount`, 1-N với `ExpenseTransaction` |
| 3 | **`ExpenseCategory`** | Danh mục thu/chi (`id`, `name`: Ăn uống, Tiền KTX, Học phí, Giải trí, `category_type`: INCOME/EXPENSE, `is_essential`: Boolean) | 1-N với `ExpenseTransaction`, `MonthlyBudget`, `RecurringBill` |
| 4 | **`MonthlyBudget`** | Hạn mức ngân sách theo tháng (`id`, `user_id`, `category_id`, `month`, `year`, `allocated_amount`, `spent_amount`, `alert_threshold_pct`) | N-1 với `UserAccount` và `ExpenseCategory` |
| 5 | **`ExpenseTransaction`** | Giao dịch thu/chi chi tiết (`id`, `wallet_id`, `category_id`, `transaction_type`, `amount`, `transaction_date`, `note`, `is_anomaly`, `anomaly_score`) | N-1 với `Wallet` và `ExpenseCategory` |
| 6 | **`RecurringBill`** | Hóa đơn cố định hàng tháng (`id`, `user_id`, `wallet_id`, `category_id`, `title`: Tiền phòng KTX/4G, `amount`, `due_day`, `auto_deduct`, `status`) | N-1 với `UserAccount`, `Wallet` và `ExpenseCategory` |
| 7 | **`BudgetAlertLog`** | Nhật ký cảnh báo & Dự báo (`id`, `user_id`, `budget_id`, `transaction_id`, `alert_type`: WARNING_80/CRITICAL/ANOMALY/BURN_RATE, `message`, `predicted_exhaustion_date`, `is_read`) | N-1 với `UserAccount`, `MonthlyBudget`, `ExpenseTransaction` |

---

## 4. Kiến trúc 3 Bài toán ML Serving (`apps/finance/engines/`)

| Bài toán ML / Thống kê | Thuật toán & Thư viện | Cơ chế Serving & Đầu ra (JSON Output) |
| :--- | :--- | :--- |
| **1. Dự báo Tốc độ Đốt tiền & Ngày Cạn Ví (`BurnRateForecaster`)** | Pandas (`.resample('D').sum()`, `.rolling(7).mean()`) + Scikit-learn (`HuberRegressor` kháng nhiễu các khoản chi lớn đầu tháng như tiền phòng KTX) | Tính chính xác `daily_burn_rate`, `days_until_exhaustion`, `predicted_exhaustion_date` (ngày ví về 0đ) và `safe_daily_allowance` / `recommended_daily_limit`. |
| **2. Phát hiện Giao dịch Bất thường (`SpendingAnomalyDetector`)** | Scikit-learn (`IsolationForest`) kết hợp kiểm định thống kê Z-Score ($\mu + 2.5\sigma$) & IQR | Chạy inference ngay khi gọi API tạo giao dịch hoặc quét định kỳ; tự động gắn cờ `is_anomaly = True` và lưu vào `BudgetAlertLog`. |
| **3. Phân loại Rủi ro Vỡ Ngân sách Cuối tháng (`RiskClassifier`)** | Scikit-learn (`RandomForestClassifier`) đóng gói qua `joblib` (`artifacts/risk_rf_classifier.joblib`) | Nạp model 1 lần duy nhất lên RAM qua `MLModelRegistry` (Singleton Pattern); trả về nhãn `SAFE` / `WARNING` / `HIGH_RISK_BROKE` kèm xác suất `predict_proba()`, `financial_health_score` (0-100) và `SavingStrategy`. |

---

## 5. Phân bổ 5 Module - 22 Chức năng - 30 RESTful APIs

### Module 1: `auth_iam` (Xác thực & Quản trị Người dùng - 6 APIs)
1. `POST /api/v1/auth/register/` — Đăng ký tài khoản sinh viên UIT (`@gm.uit.edu.vn` / `@uit.edu.vn`).
2. `POST /api/v1/auth/login/` — Đăng nhập nhận cặp JWT (`access`, `refresh`).
3. `POST /api/v1/auth/token/refresh/` — Làm mới Access Token.
4. `GET, PATCH /api/v1/users/me/` — Xem & cập nhật thông tin hồ sơ cá nhân.
5. `PATCH /api/v1/users/me/allowance/` — Cập nhật trợ cấp tháng (`monthly_income_limit`) & khu vực KTX (`dorm_area`).
6. `GET /api/v1/admin/users/` & `PATCH /api/v1/admin/users/{user_id}/toggle-status/` — Admin xem danh sách, thống kê hệ thống & khóa/mở tài khoản.

### Module 2: `wallet_mgmt` (Quản lý Ví & Chuyển tiền Nội bộ - 6 APIs)
7. `POST /api/v1/wallets/` — Tạo ví mới (`CASH`, `MOMO`, `BANK`).
8. `GET /api/v1/wallets/` — Danh sách ví của sinh viên.
9. `GET /api/v1/wallets/{wallet_id}/` — Xem chi tiết số dư & biến động ví.
10. `PUT /api/v1/wallets/{wallet_id}/` — Cập nhật tên/trạng thái ví.
11. `DELETE /api/v1/wallets/{wallet_id}/` — Xóa mềm ví (`Soft Delete`).
12. `POST /api/v1/wallets/transfer/` — Chuyển tiền nội bộ giữa 2 ví bọc trong `@transaction.atomic`.

### Module 3: `transaction` (Quản lý Danh mục, Giao dịch & Hóa đơn KTX - 9 APIs)
13. `GET /api/v1/categories/` — Danh sách danh mục thu/chi.
14. `POST /api/v1/categories/` — Thêm danh mục thu/chi mới.
15. `PUT, DELETE /api/v1/categories/{category_id}/` — Cập nhật / Xóa mềm danh mục cá nhân.
16. `POST /api/v1/transactions/` — Ghi nhận giao dịch mới (trừ tiền ví + cộng dồn ngân sách + chấm điểm Anomaly).
17. `GET /api/v1/transactions/` — Lọc lịch sử giao dịch nâng cao (theo ngày, danh mục, khoảng tiền, cờ bất thường, từ khóa).
18. `PUT /api/v1/transactions/{transaction_id}/` — Sửa giao dịch & đồng bộ lại số dư ví.
19. `DELETE /api/v1/transactions/{transaction_id}/` — Xóa mềm giao dịch & hoàn trả số dư ví.
20. `GET, POST /api/v1/recurring-bills/` — Danh sách & tạo hóa đơn cố định KTX (Tiền phòng, Điện nước, 4G).
21. `POST /api/v1/recurring-bills/{bill_id}/pay/` — Thanh toán tự động hóa đơn định kỳ KTX.

### Module 4: `budget_alert` (Thiết lập Ngân sách & Cảnh báo Tự động - 5 APIs)
22. `POST /api/v1/budgets/` — Thiết lập hạn mức ngân sách tháng.
23. `GET /api/v1/budgets/` — Xem hạn mức & tiến độ sử dụng ngân sách tháng.
24. `PUT, DELETE /api/v1/budgets/{budget_id}/` — Điều chỉnh / Xóa mềm hạn mức ngân sách.
25. `POST /api/v1/budgets/clone-previous/` — Sao chép hạn mức tháng trước sang tháng hiện tại.
26. `GET /api/v1/alerts/` & `PATCH /api/v1/alerts/{alert_id}/read/` — Danh sách cảnh báo (`WARNING_80`, `CRITICAL`, `ANOMALY`, `BURN_RATE`) & đánh dấu đã đọc.

### Module 5: `analytics_engine` (Module Ăn Điểm ML Serving & Xuất Báo cáo - 5 APIs)
27. `GET /api/v1/analytics/burn-rate-forecast/` (alias `/api/v1/analytics/cashflow-forecast/`) — Chạy `HuberRegressor` dự báo tốc độ tiêu tiền và ngày cạn ví.
28. `POST /api/v1/analytics/detect-anomalies/` & `GET /api/v1/analytics/anomalies/` — Chạy `IsolationForest` + `Z-Score` quét và đánh dấu các giao dịch đột biến.
29. `GET /api/v1/analytics/financial-health/` — Chạy `RandomForestClassifier` dự đoán xác suất vỡ ngân sách cuối tháng, chấm điểm sức khỏe tài chính (thang 100) và gợi ý `SavingStrategy`.
30. `GET /api/v1/analytics/spending-structure/` — Thống kê tỷ trọng chi tiêu `Essential` vs `Non-essential` bằng Pandas.
31. `GET /api/v1/analytics/export/?export_format=csv|xlsx` — Dùng Strategy Pattern xuất báo cáo tổng hợp ra file `.xlsx` / `.csv`.

---

## 6. Hướng dẫn Khởi động Nhanh (Docker PostgreSQL 16 + `.venv`)

### Cách 1: Khởi động PostgreSQL 16 bằng Docker & chạy Django trên `.venv`
```powershell
# 1. Khởi động container PostgreSQL 16 (student_expense_db trên cổng 5433)
docker compose up -d db

# 2. Chạy Migration, Seed 200 giao dịch mẫu & Run Server ngay tại thư mục gốc
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_data
.\.venv\Scripts\python.exe manage.py runserver
```

### Cách 2: Chạy trực tiếp ngay lập tức (Tự động dùng SQLite nếu chưa bật Docker Desktop)
```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_data
.\.venv\Scripts\python.exe manage.py runserver
```

### Kiểm thử Tự động (20 Kịch bản Pytest)
```powershell
.\.venv\Scripts\pytest.exe -v
```

### Các Đường dẫn Truy cập khi Server chạy:
- **Swagger UI (30+ RESTful APIs)**: http://127.0.0.1:8000/api/schema/swagger/
- **Hybrid MVT Web Dashboard (Chart.js)**: http://127.0.0.1:8000/dashboard/
- **ReDoc**: http://127.0.0.1:8000/api/schema/redoc/
- **Tài khoản Demo sau khi chạy `seed_data`**:
  - Sinh viên UIT: `22520001@gm.uit.edu.vn` / Mật khẩu: `Student@123`
  - Quản trị viên (Admin): `admin@uit.edu.vn` / Mật khẩu: `Admin@123`

---

## 7. Phân công Nhiệm vụ 3 Thành viên (Khớp Phụ lục Phân công)

| Thành viên | Vai trò chính | Module & Đầu việc cụ thể |
| :--- | :--- | :--- |
| **Thành viên 1 (Trưởng nhóm - Trương Huy Hoàng)** | System Architect & ML Serving Engine | • Thiết lập khung dự án Headless Django + DRF, kết nối PostgreSQL Server, cấu hình `core/` (`BaseModel`, `BaseRepository`, `CustomExceptionHandler`).<br>• Xây dựng Module 5 (`analytics_engine`): `BaseFinancialAnalyzer(ABC)`, `MLModelRegistry` (Singleton), `BurnRateForecaster`, `SpendingAnomalyDetector`, `RiskClassifier`.<br>• Viết Unit Test `pytest` cho tầng Engine và tổng hợp Báo cáo Word chuẩn `Template_IE221_New.docx`. |
| **Thành viên 2** | Backend Core Developer (Wallet & Transaction) | • Hiện thực Models, Serializers, Repositories và Services cho Module 2 (`wallet_mgmt`) và Module 3 (`transaction`) (15 APIs).<br>• Xử lý đồng bộ số dư ví và ngân sách bằng `@transaction.atomic`.<br>• Viết script `seed_data.py` sinh tự động 200 giao dịch mẫu trong 60 ngày và vẽ sơ đồ ERD + StarUML Class Diagram. |
| **Thành viên 3** | Backend Security, Budget & QA/Postman | • Hiện thực Module 1 (`auth_iam`) (SimpleJWT, RBAC Permissions `IsAdmin`, `IsStudentOwner`) và Module 4 (`budget_alert`) (11 APIs).<br>• Cấu hình `drf-spectacular` (Swagger UI), đóng gói bộ Postman Collection 30 APIs kèm Environment & Test Scripts tự động.<br>• Thiết kế `Slide.pptx` (tối đa 12 trang) và chuẩn bị kịch bản Demo 8+8 phút. |

