# Đặc Tả Yêu Cầu Chức Năng (Functional Requirements) & Phạm Vi Đề Tài Tinh Gọn (SRS - Đồ Án IE221)

Tài liệu này định nghĩa **Phạm vi Giới hạn Đề tài**, **2 Tác nhân (Actors)** và **5 Phân hệ Chức năng** theo hướng **gọn gàng ở phần CRUD cơ bản nhưng nổi bật ở Module AI / Machine Learning & Deep Learning Serving** để nhóm dễ dàng làm chủ và đạt điểm 9.5–10.0.

---

## 1. Giới Hạn Phạm Vi Đề Tài (Scope Boundary — Tập Trung Vào Core Backend & AI/DL Serving)

Để đồ án không bị dàn trải sang các phần râu ria ngoài môn học mà tập trung sâu vào **Kiến trúc MVT mở rộng + AI / Deep Learning Serving**:

| Hạng mục | Phạm vi Đồ án THỰC HIỆN (Điểm nhấn lấy 9.5 - 10 điểm) | Phạm vi Đồ án GIỚI HẠN LẠI (Không ôm đồm phần râu ria) |
| :--- | :--- | :--- |
| **1. Nghiệp vụ Ví & Tiền tệ** | Quản lý số dư đa ví (Tiền mặt, MoMo, Ngân hàng) và chuyển tiền nội bộ nguyên tử (`@transaction.atomic` + `select_for_update()`). | **Không** tích hợp cổng thanh toán ngân hàng thật hay quét QR thật; chỉ sử dụng 1 đơn vị tiền tệ chuẩn là `VNĐ`. |
| **2. Giao dịch & Hóa đơn KTX** | Ghi nhận thu/chi, tự động đồng bộ hạn mức ngân sách tháng và kích hoạt thanh toán hóa đơn cố định KTX qua API `/pay/`. | **Không** dựng hệ thống Message Queue / Cronjob chạy ngầm phức tạp (thanh toán được kích hoạt trực tiếp qua REST API). |
| **3. AI / Machine Learning & Deep Learning Serving** | **CÓ ứng dụng đầy đủ 3 bài toán AI / ML & Deep Learning**:<br>1. **Burn-Rate Forecaster**: Pandas Time-Series + `HuberRegressor` dự báo ngày cạn ví.<br>2. **Anomaly Detector**: `IsolationForest` + `Z-Score` ($\mu + 2.5\sigma$) phát hiện chi tiêu đột biến.<br>3. **Deep Learning & Ensemble Risk Classifier**: Kết hợp **Mạng Nơ-ron Đa tầng (`MLPClassifier` - Deep Neural Network 2 tầng ẩn `64x32 ReLU`, tối ưu `Adam`)** và `RandomForestClassifier` nạp qua `MLModelRegistry` (**Singleton Pattern**) để dự báo xác suất vỡ ngân sách và chấm điểm sức khỏe tài chính. | Huấn luyện và suy luận trên tập đặc trưng tài chính dạng bảng (Tabular & Time-Series Data) đóng gói gọn trong `artifacts/*.joblib`, không cần GPU rời cồng kềnh. |
| **4. Giao diện** | Hệ thống **Backend RESTful API** tài liệu hóa trên Swagger UI (`/api/schema/swagger/`) + 1 trang Dashboard trực quan (`/dashboard/`). | **Không** làm ứng dụng Mobile hay SPA Frontend tách rời. |

---

## 2. Phân Định 2 Tác Nhân Hệ Thống (Actors)

1. **Sinh viên UIT (`STUDENT`)**: Đăng ký bằng email trường (`@gm.uit.edu.vn` / `@uit.edu.vn`), quản lý ví, danh mục, giao dịch thu/chi, hóa đơn KTX, ngân sách tháng, nhận cảnh báo tự động, chạy các mô hình AI/Deep Learning dự báo chi tiêu và xuất báo cáo CSV/Excel.
2. **Quản trị viên (`ADMIN`)**: Xem thống kê toàn hệ thống và khóa/mở khóa (`is_active`) tài khoản sinh viên.

---

## 3. Danh Mục 5 Phân Hệ - 22 Chức Năng Tinh Gọn (`FR-01` $\rightarrow$ `FR-22`)

### Phân hệ 1: Xác thực & Quản trị Người dùng (`Module 1: auth_iam` — 4 Chức năng / 6 APIs)
- **`FR-01` — Đăng ký tài khoản sinh viên UIT** (`POST /api/v1/auth/register/`): Kiểm tra Regex email UIT, băm mật khẩu và khởi tạo tài khoản `STUDENT`.
- **`FR-02` — Đăng nhập & Làm mới JWT Token** (`POST /api/v1/auth/login/`, `POST /api/v1/auth/token/refresh/`): Cấp phát cặp `access` và `refresh` token.
- **`FR-03` — Quản lý hồ sơ, trợ cấp tháng & khu KTX** (`GET, PATCH /api/v1/users/me/`, `PATCH /api/v1/users/me/allowance/`): Xem và cập nhật hạn mức trợ cấp tháng (`monthly_income_limit`) và khu vực ở (`dorm_area`).
- **`FR-04` — Admin thống kê & Khóa/Mở tài khoản** (`GET /api/v1/admin/users/`, `PATCH /api/v1/admin/users/{id}/toggle-status/`): Phân quyền `IsAdmin`.

### Phân hệ 2: Quản lý Ví tiền & Danh mục (`Module 2: wallet_mgmt` — 4 Chức năng / 6 APIs)
- **`FR-05` — Tạo, xem & cập nhật Ví tiền** (`GET, POST /api/v1/wallets/`, `GET, PUT /api/v1/wallets/{id}/`): Quản lý ví Tiền mặt, MoMo, Ngân hàng (`balance >= 0`).
- **`FR-06` — Xóa mềm Ví tiền** (`DELETE /api/v1/wallets/{id}/`): Đặt `is_deleted = True` bảo toàn lịch sử giao dịch.
- **`FR-07` — Chuyển tiền nội bộ nguyên tử giữa 2 ví** (`POST /api/v1/wallets/transfer/`): Khấu trừ ví nguồn, cộng ví đích và ghi biên lai `TRANSFER` trong `@transaction.atomic`.
- **`FR-08` — Quản lý Danh mục Thu/Chi & Thiết yếu** (`GET, POST /api/v1/categories/`, `PUT, DELETE /api/v1/categories/{id}/`): Phân loại khoản thu/chi và gắn cờ `is_essential`.

### Phân hệ 3: Giao dịch Thu/Chi & Hóa đơn Định kỳ KTX (`Module 3: transaction` — 5 Chức năng / 9 APIs)
- **`FR-09` — Ghi nhận Thu/Chi & Chấm điểm AI Anomaly thời gian thực** (`POST /api/v1/transactions/`): Khóa dòng ví, trừ/cộng số dư, gọi `AnomalyDetectionEngine` gắn cờ `is_anomaly`, đồng bộ `MonthlyBudget` và sinh cảnh báo.
- **`FR-10` — Sửa giao dịch & Bù trừ số dư ví** (`PUT /api/v1/transactions/{id}/`): Tự động tính chênh lệch và cập nhật lại số dư ví.
- **`FR-11` — Xóa mềm giao dịch & Hoàn tiền tự động** (`DELETE /api/v1/transactions/{id}/`): Xóa mềm giao dịch và hoàn lại tiền vào ví.
- **`FR-12` — Tra cứu & Lọc giao dịch đa tiêu chí** (`GET /api/v1/transactions/`): Lọc theo ngày, danh mục, khoảng tiền, cờ bất thường `is_anomaly` và từ khóa.
- **`FR-13` — Quản lý & Thanh toán Hóa đơn định kỳ KTX** (`GET, POST /api/v1/recurring-bills/`, `PUT, DELETE /api/v1/recurring-bills/{id}/`, `POST /api/v1/recurring-bills/{id}/pay/`): Quản lý tiền phòng KTX, điện nước, 4G và bấm thanh toán tự động trừ ví.

### Phân hệ 4: Ngân sách Tháng & Cảnh báo Tự động (`Module 4: budget_alert` — 4 Chức năng / 5 APIs)
- **`FR-14` — Thiết lập & Điều chỉnh ngân sách tháng** (`POST /api/v1/budgets/`, `PUT, DELETE /api/v1/budgets/{id}/`): Đặt hạn mức chi tiêu theo tháng/danh mục.
- **`FR-15` — Sao chép ngân sách tháng trước** (`POST /api/v1/budgets/clone-previous/`): Tự động chép hạn mức tháng trước sang tháng hiện tại.
- **`FR-16` — Theo dõi tiến độ & Cảnh báo ngưỡng 80% / 100%** (`GET /api/v1/budgets/`): Tính `%` đã tiêu và tự động tạo cảnh báo `WARNING_80` hoặc `CRITICAL`.
- **`FR-17` — Xem hộp thư cảnh báo & Đánh dấu đã đọc** (`GET /api/v1/alerts/`, `PATCH /api/v1/alerts/{id}/read/`).

### Phân hệ 5: AI / Machine Learning & Deep Learning Serving Engine (`Module 5: analytics_engine` — 5 Chức năng / 5 APIs)
- **`FR-18` — Dự báo tốc độ đốt tiền & Ngày cạn ví (`BurnRateAnalyzer`)** (`GET /api/v1/analytics/burn-rate-forecast/`): Chuẩn hóa chuỗi thời gian Pandas `.resample('D').sum()`, trung bình trượt 7 ngày và hồi quy kháng nhiễu `HuberRegressor` dự báo ngày ví về 0đ (`predicted_exhaustion_date`) cùng hạn mức an toàn mỗi ngày (`safe_daily_allowance`).
- **`FR-19` — Quét & Phát hiện giao dịch bất thường (`AnomalyDetectionEngine`)** (`GET /api/v1/analytics/anomalies/`, `POST /api/v1/analytics/detect-anomalies/`): Kết hợp mô hình `IsolationForest` + kiểm định `Z-Score` ($\mu + 2.5\sigma$) và `IQR`.
- **`FR-20` — Chấm điểm Sức khỏe Tài chính & Dự báo Rủi ro bằng Deep Learning MLP + RandomForest (`RiskClassifier`)** (`GET /api/v1/analytics/financial-health/`):
  - Sử dụng `MLModelRegistry` (**Singleton Pattern**) nạp mô hình **Deep Neural Network `MLPClassifier(hidden_layer_sizes=(64, 32), activation='relu', solver='adam')`** (`artifacts/deep_mlp_risk.joblib`) kết hợp Ensemble với `RandomForestClassifier` (`artifacts/risk_rf_classifier.joblib`).
  - Dự báo xác suất `predict_proba()` cho 3 trạng thái `SAFE` / `WARNING` / `HIGH_RISK_BROKE`, tính điểm `financial_health_score` ($0..100$) và chọn chiến lược tiết kiệm đa hình `SavingStrategy` (**Strategy Pattern**).
- **`FR-21` — Thống kê tỷ trọng Thiết yếu vs Giải trí & Web Dashboard** (`GET /api/v1/analytics/spending-structure/`, `GET /dashboard/`).
- **`FR-22` — Xuất báo cáo CSV / Excel đa hình (`BaseReportExporter`)** (`GET /api/v1/analytics/export/?export_format=csv|xlsx`): Áp dụng **Strategy Pattern** qua `CSVReportExporter` và `ExcelReportExporter`.
