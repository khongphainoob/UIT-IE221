# Kịch Bản Bảo Vệ Đồ Án 8 Phút Trình Bày + 8 Phút Vấn Đáp & Bố Cục 12 Trang Slide (IE221)

> [!CAUTION]
> **Checklist 5 phút trước khi lên bục báo cáo**:
> 1. **Trang bìa Slide**: Tuyệt đối **KHÔNG** ghi tên Giảng viên hướng dẫn (GVHD).
> 2. **VS Code**: Chuyển sang **Light Mode (Nền sáng)** (`Ctrl+K Ctrl+T` -> chọn `Light Modern`).
> 3. **Terminal 1**: Chạy sẵn server (`cd student_expense_api && .\.venv\Scripts\python.exe manage.py runserver`).
> 4. **Terminal 2**: Để sẵn lệnh `.\.venv\Scripts\pytest.exe -v` chờ bấm Enter khi thầy yêu cầu chạy test.
> 5. **Trình duyệt**: Mở sẵn 2 tab:
>    - Tab 1: Swagger UI (`http://127.0.0.1:8000/api/schema/swagger/`)
>    - Tab 2: Hybrid MVT Dashboard (`http://127.0.0.1:8000/dashboard/`)
> 6. **Postman**: Mở sẵn Collection `IE221 - Student Expense Analytics API (30 RESTful APIs)` và chọn Environment `IE221_Student_Expense_API_Local`.

---

## 1. Bố Cục Chuẩn 12 Trang Slide (`Slide.pptx` - Tối đa 12 trang)

| Trang | Tiêu đề Slide | Nội dung cốt lõi cần hiển thị | Thời lượng |
| :-: | :--- | :--- | :---: |
| **1** | **Trang Bìa** | Tên đề tài (3 dòng in hoa), Tên 3 thành viên + MSSV. *(Không ghi tên GVHD)* | 15s |
| **2** | **Bài Toán Thực Tế & Mục Tiêu** | Nỗi đau sinh viên KTX cuối tháng cạn tiền do thiếu dự báo tốc độ tiêu (Burn-rate); mục tiêu xây dựng 22 chức năng - 30 RESTful APIs. | 30s |
| **3** | **Kiến Trúc Hybrid MVT Mở Rộng** | Sơ đồ 5 tầng: `View (APIView/TemplateView)` $\rightarrow$ `Serializer/Template` $\rightarrow$ `Service (@transaction.atomic)` $\rightarrow$ `Repository (ORM)` $\rightarrow$ `Model (7 bảng 3NF)` & `Engine (ML)`. | 45s |
| **4** | **Thiết Kế CSDL (7 Bảng Chuẩn 3NF)** | Hình ERD 7 bảng (`UserAccount`, `Wallet`, `ExpenseCategory`, `MonthlyBudget`, `ExpenseTransaction`, `RecurringBill`, `BudgetAlertLog`). | 45s |
| **5** | **Thiết Kế OOP & Design Patterns (StarUML)** | Hình Class Diagram: `BaseModel`, `BaseFinancialAnalyzer(ABC)`, `MLModelRegistry` (Singleton), `SavingStrategy` & `BaseReportExporter` (Strategy Pattern). | 60s |
| **6** | **Module Ăn Điểm 1: Burn-Rate Forecaster** | Quy trình Pandas `.resample('D').sum()`, trung bình trượt 7 ngày và lý do chọn `HuberRegressor` kháng nhiễu tiền phòng KTX đầu tháng. | 60s |
| **7** | **Module Ăn Điểm 2 & 3: Anomaly & RiskClassifier** | Kết hợp `IsolationForest` + Z-Score ($\mu + 2.5\sigma$) phát hiện chi tiêu đột biến & `RandomForestClassifier` chấm điểm sức khỏe tài chính thang 100. | 45s |
| **8** | **Bảo Toàn Tiền Tệ ACID (`@transaction.atomic`)** | Sequence Diagram luồng ghi nhận giao dịch: khóa dòng `select_for_update()` $\rightarrow$ chấm Anomaly $\rightarrow$ trừ ví $\rightarrow$ đồng bộ `MonthlyBudget` & sinh cảnh báo `WARNING_80`. | 45s |
| **9** | **Tổng Hợp 5 Phân Hệ - 30 RESTful APIs** | Bảng tổng hợp 5 Module (Auth 6 APIs, Wallet 6 APIs, Transaction & KTX 9 APIs, Budget 5 APIs, Analytics ML 5 APIs). | 30s |
| **10** | **Kết Quả Kiểm Thử Tự Động (`Pytest` & Postman)** | Kết quả 20 kịch bản Unit/Integration Test xanh 100% + Postman Runner 30/30 requests. | 30s |
| **11** | **Demo Trực Tiếp Hệ Thống** | Chuyển sang màn hình Live Demo (Swagger UI, Postman Runner, `pytest -v`, Xuất file Excel). | 3 phút |
| **12** | **Kết Luận & Hạn Chế** | Tóm tắt kết quả đạt được và 2 hạn chế thực tế. | 15s |

---

## 2. Bộ Câu Hỏi Phản Biện Thường Gặp Của Thầy & Câu Trả Lời Điểm 10

### Câu hỏi 1: *"Tại sao nhóm không viết thẳng truy vấn ORM vào trong `views.py` như hướng dẫn cơ bản của Django mà lại tách thêm `services/`, `repositories/` và `engines/`?"*
- **Trả lời**:
  - Trong chuẩn **MVT (Model - View - Template)** của Django, tầng **M (Model)** đại diện cho toàn bộ dữ liệu và quy tắc nghiệp vụ lõi chứ không chỉ là các class khai báo bảng.
  - Nếu dồn cả truy vấn ORM, logic kiểm tra số dư ví, tính ngân sách và thuật toán Pandas/Scikit-learn vào `views.py` sẽ dẫn đến **"Fat Views"**, vi phạm nguyên lý **Single Responsibility (SRP)** và không thể viết Unit Test độc lập cho thuật toán.
  - Vì vậy, nhóm phân rã bên trong tầng **M** thành: `models/` (cấu trúc 7 bảng 3NF), `repositories/` (đóng gói `select_related`, `select_for_update`), `services/` (điều phối giao dịch nguyên tử `@transaction.atomic`), và `engines/` (xử lý ML/Pandas). Nhờ đó `views/` giữ đúng vai trò điều phối HTTP mỏng gọn của tầng **V**.

### Câu hỏi 2: *"Tại sao trong bài toán dự báo ngày cạn tiền (`BurnRateAnalyzer`), nhóm lại dùng `HuberRegressor` thay vì chỉ dùng trung bình cộng hoặc `LinearRegression` thông thường?"*
- **Trả lời**:
  - Chi tiêu của sinh viên ở KTX có đặc thù là vào các ngày đầu tháng (ngày 1–10) thường xuất hiện các khoản chi cố định lớn (như đóng tiền phòng KTX 450.000đ, mua giáo trình, đóng tiền điện nước), sau đó các ngày trong tháng chỉ tiêu ăn uống căn tin khoảng 40.000đ–60.000đ/ngày.
  - Nếu dùng `LinearRegression` (bình phương tối thiểu OLS), các điểm dị biệt (outliers) đầu tháng sẽ kéo lệch hệ số góc hồi quy, làm dự báo ngày cạn ví bị sai lệch.
  - `HuberRegressor` áp dụng hàm mất mát tuyến tính cho các mẫu có phần dư lớn hơn ngưỡng $\epsilon = 1.35$, giúp kháng nhiễu (robust to outliers), kết hợp với trung bình trượt 7 ngày (`.rolling(7).mean()`) cho ra tốc độ đốt tiền sát thực tế nhất.

### Câu hỏi 3: *"Làm sao hệ thống đảm bảo khi 2 request trừ tiền cùng lúc hoặc khi đang chuyển tiền giữa 2 ví mà gặp lỗi thì sinh viên không bị mất tiền oan?"*
- **Trả lời**:
  - Ở tầng CSDL (`Wallet`), nhóm thiết lập ràng buộc `CheckConstraint(condition=Q(balance__gte=0))` ngay dưới PostgreSQL.
  - Ở tầng `WalletService` và `TransactionService`, mọi hàm biến động số dư đều được bọc trong `@transaction.atomic` kết hợp `select_for_update()` để khóa dòng (row-level locking) bản ghi ví cho đến khi transaction hoàn tất. Nếu số dư không đủ, hệ thống ném `InsufficientBalanceException` và tự động rollback 100%.

### Câu hỏi 4: *"4 tính chất OOP và các Design Pattern được thể hiện ở file nào trong source code của nhóm?"*
- **Trả lời**:
  1. **Trừu tượng (Abstraction)**: Lớp `BaseFinancialAnalyzer(ABC)` tại `apps/finance/engines/base_analyzer.py` với `@abstractmethod preprocess()` và `execute_analysis()`.
  2. **Kế thừa (Inheritance)**: 7 bảng CSDL kế thừa `BaseModel` (`core/models.py`); 3 bộ máy `BurnRateAnalyzer`, `AnomalyDetectionEngine`, `RiskClassifier` kế thừa `BaseFinancialAnalyzer`.
  3. **Đóng gói (Encapsulation)**: Các thuộc tính nội bộ `_raw_data`, `_dataframe`, `_daily_burn_rate`, `_safety_threshold` được đóng gói và truy xuất qua `@property`.
  4. **Đa hình (Polymorphism / Strategy Pattern & Singleton Pattern)**:
     - **Strategy Pattern**: `SavingStrategy` (`BalancedEarlyMonthStrategy` vs `EmergencyEndOfMonthStrategy` tại `risk_classifier.py`) và `BaseReportExporter` (`CSVReportExporter` vs `ExcelReportExporter` tại `exporters.py` cùng ghi đè hàm `generate()`).
     - **Singleton Pattern**: `MLModelRegistry` (`model_registry.py`) đảm bảo các model `.joblib` chỉ nạp lên RAM đúng 1 lần duy nhất.
