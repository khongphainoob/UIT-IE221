---
name: ie221-project-conventions
description: Quy chuẩn kiến trúc, Coding Conventions, phân rã 5 Module (22 chức năng - 30 RESTful APIs), 3 bài toán ML Serving và quy tắc chống trừ điểm báo cáo cho Đồ án IE221 (Kỹ thuật lập trình Python - UIT). Đọc skill này trước khi thêm/sửa bất kỳ tính năng hay tài liệu nào trong dự án.
---

# IE221 Project Architecture & Coding Conventions Skill

## 1. Mục tiêu của Skill
Đảm bảo mọi đoạn code, sơ đồ StarUML, kịch bản kiểm thử `pytest` và tài liệu báo cáo của đồ án **XÂY DỰNG HỆ THỐNG BACKEND RESTFUL API QUẢN LÝ VÀ PHÂN TÍCH DỰ BÁO CHI TIÊU SINH VIÊN** luôn thống nhất 100%, không dư thừa code, không sai lệch tên lớp/phương thức và đạt mốc điểm **9.5 – 10.0**.

---

## 2. Quy tắc Kiến trúc 5 Tầng (Hybrid MVT + Service-Repository + ML Engine)

```text
HTTP Request -> urls.py -> View (APIView/TemplateView)
                             ├── Serializer (Validate Input / Format JSON Output)
                             └── Service (@transaction.atomic)
                                   ├── Repository (ORM: select_related, select_for_update, aggregate)
                                   │     └── Model (7 bảng chuẩn 3NF kế thừa BaseModel)
                                   └── Engine (BaseFinancialAnalyzer ABC + MLModelRegistry Singleton)
```

### Quy tắc Cấm (Anti-Patterns):
1. **CẤM** gọi `Model.objects...` trực tiếp bên trong `views/` (trừ các view quản trị đơn giản hoặc phải đi qua `Repository`/`Service`).
2. **CẤM** cộng/trừ `wallet.balance` mà không có `@transaction.atomic` và `select_for_update()`.
3. **CẤM** dùng kiểu `float` khi cộng/trừ tiền trong `services/` (phải dùng `Decimal`).
4. **CẤM** tạo thêm bảng CSDL vượt quá **7 bảng chuẩn 3NF** đã thiết kế:
   - `UserAccount`, `Wallet`, `ExpenseCategory`, `MonthlyBudget`, `ExpenseTransaction`, `RecurringBill`, `BudgetAlertLog`.

---

## 3. Ánh xạ 1:1 giữa Code OOP và StarUML Class Diagram

| Tính chất OOP / Pattern | Lớp / Giao diện trong Code | Phương thức / Thuộc tính bắt buộc |
| :--- | :--- | :--- |
| **Abstraction** | `BaseFinancialAnalyzer(ABC)` (`engines/base_analyzer.py`) | `@abstractmethod preprocess()`, `@abstractmethod execute_analysis()`, `analyze()`, `export_report()`, `run_inference()` |
| **Inheritance (Models)** | `BaseModel` / `TimeStampedSoftDeleteModel` (`core/models.py`) | `id` (UUIDv4), `created_at`, `updated_at`, `is_deleted`, `soft_delete()`, `restore()` |
| **Inheritance (Engines)** | `BurnRateAnalyzer` (`BurnRateForecaster`), `AnomalyDetectionEngine` (`SpendingAnomalyDetector`), `RiskClassifier` | Kế thừa `BaseFinancialAnalyzer` |
| **Polymorphism (Strategy 1)** | `SavingStrategy(ABC)` (`engines/risk_classifier.py`) | `BalancedEarlyMonthStrategy`, `EmergencyEndOfMonthStrategy` ghi đè `build_recommendation()` |
| **Polymorphism (Strategy 2)** | `BaseReportExporter(ABC)` (`engines/exporters.py`) | `CSVReportExporter`, `ExcelReportExporter` ghi đè `generate()` |
| **Encapsulation** | Thuộc tính protected/private có tiền tố `_` | `_raw_data`, `_dataframe`, `_daily_burn_rate`, `_safety_threshold` + `@property` |
| **Singleton Pattern** | `MLModelRegistry` (`engines/model_registry.py`) | `_instance`, `get_instance()`, `get_model()` nạp `artifacts/*.joblib` lên RAM 1 lần |

---

## 4. Ba Bài toán Machine Learning Serving (`apps/finance/engines/`)

1. **Burn-Rate Forecaster (`burn_rate_engine.py`)**:
   - **Xử lý chuỗi thời gian**: Pandas `.resample('D').sum()`, trung bình trượt 7 ngày `.rolling(window=7, min_periods=1).mean()`.
   - **Mô hình**: Scikit-learn `HuberRegressor` (kháng nhiễu khoản chi lớn đầu tháng như tiền phòng KTX) kết hợp `LinearRegression`.
   - **Đầu ra**: `daily_burn_rate`, `days_until_exhaustion`, `predicted_exhaustion_date`, `safe_daily_allowance`, `recommended_daily_limit`.
2. **Spending Anomaly Detector (`anomaly_engine.py`)**:
   - **Mô hình**: Scikit-learn `IsolationForest` kết hợp kiểm định thống kê Z-Score ($\mu + 2.5\sigma$) và IQR ($Q_3 + 1.5 \times \text{IQR}$).
   - **Đầu ra**: Tự động gắn cờ `is_anomaly = True`, tính `anomaly_score` và ghi nhận `BudgetAlertLog`.
3. **Risk Classifier & Financial Health Score (`risk_classifier.py`)**:
   - **Mô hình**: Scikit-learn `RandomForestClassifier` nạp qua `MLModelRegistry` (Singleton) từ `artifacts/risk_rf_classifier.joblib`.
   - **Đầu ra**: Nhãn `SAFE` / `WARNING` / `HIGH_RISK_BROKE`, xác suất `predict_proba()`, điểm sức khỏe tài chính thang 0–100 (`financial_health_score`) và khuyến nghị từ `SavingStrategy`.

---

## 5. Quy tắc Chống Trừ Điểm Báo cáo Word & Slide Bảo vệ
- **Trang bìa**: Tuyệt đối **KHÔNG** ghi tên Giảng viên hướng dẫn (GVHD) trên cả Báo cáo Word và Slide.
- **Mục 1 (Giới thiệu)**: Đúng **10 dòng, chia 2 đoạn văn** (Đoạn 1: Làm gì - Công cụ - Kết quả; Đoạn 2: Cam kết minh bạch học thuật).
- **Nội dung chính (Mục 1 -> Mục 5)**: Từ **5 đến tối đa 10 trang** (không có lời cảm ơn, tóm tắt, mục lục).
- **Cấm chèn Code / Ảnh chụp màn hình vào phần ruột (Mục 1–5)**: Toàn bộ ảnh chụp Swagger/Postman/Pytest và đoạn code phải đẩy xuống **4 Phụ lục bắt buộc** (Phụ lục Phân công nhiệm vụ, Phụ lục Tóm tắt kết quả, Phụ lục Hình, Phụ lục Code).
- **Demo trên lớp (8 phút trình bày + 8 phút vấn đáp)**: Chuyển VS Code sang **Light Mode (Nền sáng)** trước khi lên bảng.

---

## 6. Liên kết Quy trình Phát triển Tính năng, Git Workflow, Testing & Đóng Task
Khi bắt đầu code một tính năng mới, sửa lỗi, chạy kiểm thử hoặc tạo Commit/Pull Request, hãy đọc thêm Skill:
- [`ie221-feature-workflow-git-testing`](../ie221-feature-workflow-git-testing/SKILL.md)
- Mẫu Pull Request: [`.github/PULL_REQUEST_TEMPLATE.md`](../../../.github/PULL_REQUEST_TEMPLATE.md)
- Mẫu Issue/Task: [`.github/ISSUE_TEMPLATE/feature_task.md`](../../../.github/ISSUE_TEMPLATE/feature_task.md)

