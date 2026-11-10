# Khu vực Tài liệu Thiết kế (Design & UML Placeholders) - Đồ án IE221 UIT

Thư mục này được chừa sẵn để bạn gửi các bản thiết kế của mình vào tích hợp:

1. **Database Schema / ERD (`docs/erd_schema.md` hoặc ảnh/SQL/DBML)**:
   - Hiện tại 7 Models chuẩn 3NF trong `apps/finance/models/` (`UserAccount`, `Wallet`, `ExpenseCategory`, `MonthlyBudget`, `ExpenseTransaction`, `RecurringBill`, `BudgetAlertLog`) đã có đánh dấu `# [DESIGN HOOK - ERD / CLASS DIAGRAM]`.
   - Khi bạn gửi ERD / Schema chi tiết của bạn, tôi sẽ ánh xạ (map) chính xác từng trường, kiểu dữ liệu, khoá ngoại và ràng buộc vào Models & Migrations.

2. **Biểu đồ UML (`docs/uml/`)**:
   - **Use Case Diagram**: Phân quyền `STUDENT` vs `ADMIN`.
   - **Class Diagram**: Thể hiện tính Kế thừa (`BaseModel`, `BaseFinancialAnalyzer(ABC)`), Đóng gói (`_raw_data`, `_dataframe`), Đa hình (`BurnRateAnalyzer`, `AnomalyDetectionEngine`).
   - **Sequence Diagram**: Luồng `@transaction.atomic` khi Ghi nhận chi tiêu -> Chấm điểm Anomaly -> Trừ số dư ví -> Cập nhật `MonthlyBudget` -> Tạo `BudgetAlertLog`.

3. **Đặc tả Công thức Toán / ML (`docs/analytics_spec.md`)**:
   - Nếu bạn muốn tuỳ chỉnh ngưỡng Z-Score / IQR hoặc công thức tính `safe_daily_allowance` và `predicted_exhaustion_date`, hãy gửi công thức để gắn trực tiếp vào `apps/finance/engines/`.

