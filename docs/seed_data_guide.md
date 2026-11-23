# Hướng Dẫn Sinh Dữ Liệu Demo (`manage.py seed_data`) & Bộ Dataset Khóa 2024 (`2452xxxx`)

Tài liệu này mô tả kết quả khảo sát các bộ dữ liệu chi tiêu công khai (Kaggle / GitHub), cấu trúc bộ dataset chuẩn hóa **[`data/uit_student_expenses_dataset.csv`](../data/uit_student_expenses_dataset.csv)** (~1.025 giao dịch của 6 sinh viên Khóa 2024 UIT `24520001`..`24520006`) và cách vận hành lệnh `python manage.py seed_data` **có thể tái lập 100%, an toàn khi chạy lặp lại (idempotent)** trên cả 7 bảng 3NF.

---

## 1. Kết Quả Khảo Sát Dữ Liệu Công Khai & Sự Kết Hợp (Hướng A + Hướng B)

Nhóm đã khảo sát 3 nguồn dữ liệu công khai trên Kaggle và GitHub trước khi xây dựng bộ dataset cho đồ án:

| Nguồn tham khảo | Cấu trúc dữ liệu | Đánh giá & Cách nhóm kế thừa |
| :--- | :--- | :--- |
| **Kaggle — *Student Spending Habits Dataset***<br>*(mirror GitHub: `Priyanshi1004/student-spending-dashboard`, `data/student_spending.csv`)* | 1.000 bản ghi sinh viên đại học gồm thu nhập tháng, trợ cấp và tổng chi theo từng nhóm (`housing`, `food`, `transportation`, `books_supplies`, `entertainment`, `technology`, `health_wellness`...) bằng **USD**. | Kế thừa **hệ thống phân nhóm 12 danh mục** và **tỷ trọng chi tiêu theo nhóm sinh viên**, chuyển từ bảng tổng tháng sang chuỗi giao dịch từng ngày bằng **VNĐ**. |
| **Kaggle — *Daily Household Transactions*** | Log giao dịch theo ngày gồm `Date`, `Mode`, `Category`, `Subcategory`, `Note`, `Amount`, `Income/Expense`, `Currency`. | Kế thừa cấu trúc **log giao dịch theo ngày + phương thức thanh toán (`CASH`, `MOMO`, `BANK`)** và quy đổi sang ngữ cảnh sinh viên UIT – Làng Đại học Thủ Đức trong **60 ngày gần nhất**. |
| **GitHub Sample CSVs**<br>*(`Apress/personal-finance-with-python` `purchases.csv`, `sumitc27/SoM_MonthlyExpense`)* | File CSV giao dịch mẫu và biến động chi phí ký túc xá hàng tháng. | Bổ sung đầy đủ liên kết khóa ngoại FK tới `Wallet`, `ExpenseCategory`, `MonthlyBudget`, `RecurringBill` và nhãn `scenario_tag` (`INTENTIONAL_ANOMALY`, `EDGE_MIN_AMOUNT`, `FIXED_KTX_BILL`). |

**Giải pháp kết hợp cả 2 hướng của dự án**:
- **Hướng A (Đa dạng hóa thực tế trong [`seed_data.py`](../apps/finance/management/commands/seed_data.py))**: Tạo **6 sinh viên Khóa 2024 (`24520001`..`24520006`)** đại diện cho 6 khoa của UIT và 3 hồ sơ rủi ro (`SAFE`, `WARNING`, `HIGH_RISK_BROKE`), **12 danh mục Thu/Chi**, **18 ví tiền**, **14 hóa đơn KTX**, và bộ từ điển **85+ giao dịch đời thực tại Làng Đại học Thủ Đức**.
- **Hướng B (Dataset CSV chuẩn hóa [`data/uit_student_expenses_dataset.csv`](../data/uit_student_expenses_dataset.csv))**: Lưu trữ trọn vẹn **1.025 dòng giao dịch** (200 giao dịch cho sinh viên chính `24520001@gm.uit.edu.vn` + 165 giao dịch cho mỗi sinh viên `24520002`..`24520006`) để có thể mở xem trực tiếp bằng Excel/Pandas và nạp tự động vào Database qua `python manage.py seed_data`.

---

## 2. Danh Sách 6 Hồ Sơ Sinh Viên Khóa 2024 UIT (`2452xxxx`) & Tài Khoản Admin

| MSSV | Email đăng nhập | Họ và tên | Khoa / Khu vực ở | Trợ cấp tháng | Hồ sơ tài chính & Kịch bản Demo | Số giao dịch |
| :---: | :--- | :--- | :--- | :---: | :--- | :---: |
| **`24520001`** | `24520001@gm.uit.edu.vn` | **Trương Huy Hoàng** *(SV Demo chính)* | Công nghệ Phần mềm (SE) — KTX Khu B (BA4) | `4.500.000 VNĐ` | **`BALANCED_ANOMALY_DEMO`**: Đầy đủ `INCOME`, `TRANSFER`, tiền KTX đầu tháng, 3 edge cases nhỏ & 5 anomaly lớn | **`200`** *(mặc định `--count`)* |
| **`24520002`** | `24520002@gm.uit.edu.vn` | **Nguyễn Minh Anh** | Khoa học Máy tính (CS) — KTX Khu A (A12) | `5.000.000 VNĐ` | **`SAFE_DISCIPLINED`**: Chi tiêu kỷ luật 50/30/20, có thêm thu nhập trợ giảng Python | `165` |
| **`24520003`** | `24520003@gm.uit.edu.vn` | **Lê Hoàng Nam** | Kỹ thuật Máy tính (CE) — KTX Khu B (BB2) | `4.200.000 VNĐ` | **`WARNING_TECH_SPENDER`**: Chi mua phụ kiện công nghệ & học tập chạm ngưỡng cảnh báo 80% | `165` |
| **`24520004`** | `24520004@gm.uit.edu.vn` | **Phạm Ngọc Hân** | Hệ thống Thông tin (IS) — Trọ Làng ĐH | `5.200.000 VNĐ` | **`HIGH_RISK_BROKE`**: Chi trà sữa, giải trí & mua sắm Shopee vượt ngân sách, nguy cơ cạn ví sớm | `165` |
| **`24520005`** | `24520005@gm.uit.edu.vn` | **Võ Quốc Bảo** | Mạng Máy tính & TT (NC) — KTX Khu B (BC1) | `4.400.000 VNĐ` | **`WARNING_FOOD_SOCIAL`**: Tần suất ăn uống & giao lưu CLB cao | `165` |
| **`24520006`** | `24520006@gm.uit.edu.vn` | **Đặng Thùy Trang** | KH & Kỹ thuật Thông tin (DS) — KTX Khu A (A08) | `4.800.000 VNĐ` | **`SAFE_SCHOLARSHIP`**: Tiết kiệm ổn định, số dư ví dồi dào | `165` |
| **Admin** | `admin@uit.edu.vn` | **Giảng viên / Quản trị viên IE221** | Quản trị hệ thống (`role=ADMIN`) | — | Xem thống kê toàn hệ thống (7 users, 1.025 giao dịch) & khóa/mở tài khoản | — |

---

## 3. Tổng Hợp Khối Lượng Dữ Liệu Trên 7 Bảng 3NF Sau Khi Chạy `seed_data`

| Bảng CSDL (3NF) | Số lượng bản ghi | Chi tiết dữ liệu |
| :--- | :---: | :--- |
| **`UserAccount`** | **`7`** | 1 Admin (`admin@uit.edu.vn`) + 6 Sinh viên Khóa 2024 (`24520001@gm.uit.edu.vn` → `24520006@gm.uit.edu.vn`) |
| **`Wallet`** | **`18`** | Mỗi sinh viên có đủ 3 ví (`CASH`, `MOMO`, `BANK`) với số dư thực tế theo từng hồ sơ rủi ro |
| **`ExpenseCategory`** | **`12`** | 9 danh mục `EXPENSE` (6 thiết yếu + 3 không thiết yếu) & 3 danh mục `INCOME` (Trợ cấp, Làm thêm/Gia sư, Giải thưởng) |
| **`RecurringBill`** | **`14`** | 4 hóa đơn KTX cho `24520001` (Tiền phòng KTX, Điện nước, 4G Viettel, Vé tháng Xe buýt/Metro) + 2 hóa đơn KTX/SV cho 5 sinh viên còn lại |
| **`ExpenseTransaction`** | **`1.025`** | **`200` giao dịch** cho SV chính `24520001` + **`825` giao dịch** cho 5 SV còn lại trải đều 60 ngày (`INCOME`, `TRANSFER`, `EXPENSE`, tiền phòng KTX đầu tháng, edge cases `5k–10k` và intentional anomalies `980k–1.65M`) |
| **`MonthlyBudget`** | **`30`** | Mỗi sinh viên có 2 ngân sách tháng trước (test `clone-previous`) + 3 ngân sách tháng hiện tại (Tổng tháng, Ăn uống `WARNING_80`, Giải trí `CRITICAL`) |
| **`BudgetAlertLog`** | **`35+`** | Tự động gắn FK `transaction` & `budget` thật cho cảnh báo `ANOMALY`, `WARNING_80`, `CRITICAL` và dự báo `BURN_RATE` kèm `predicted_exhaustion_date` |

---

## 4. Cách Chạy & Các Tùy Chọn CLI

```powershell
# 1. Chạy trên DB mới (mặc định idempotent — nếu đã có dữ liệu sẽ bỏ qua an toàn)
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_data

# 2. Xóa sạch dữ liệu demo cũ và tái tạo lại toàn bộ 1.025 giao dịch + cập nhật file CSV
.\.venv\Scripts\python.exe manage.py seed_data --reset

# 3. Tùy chỉnh số lượng giao dịch của SV chính 24520001 và khoảng ngày
.\.venv\Scripts\python.exe manage.py seed_data --reset --days 45 --count 150 --seed 221
```

> **Mẹo xem Dashboard theo từng sinh viên**:
> - Mặc định `http://127.0.0.1:8000/dashboard/` hiển thị sinh viên chính `24520001` (**Trương Huy Hoàng**).
> - Có thể đổi nhanh sang sinh viên khác bằng query param:
>   - Hồ sơ an toàn (`SAFE`): `http://127.0.0.1:8000/dashboard/?student=24520002`
>   - Hồ sơ nguy cơ cháy túi (`HIGH_RISK_BROKE`): `http://127.0.0.1:8000/dashboard/?student=24520004`

---

## 5. Thông Tin Đăng Nhập Demo Nội Bộ & Lưu Ý Bảo Mật

- **Sinh viên chính (`STUDENT`)**: `24520001@gm.uit.edu.vn` (hoặc `24520002` → `24520006@gm.uit.edu.vn`) / Mật khẩu mặc định: `Student@123`
- **Quản trị viên (`ADMIN`)**: `admin@uit.edu.vn` / Mật khẩu mặc định: `Admin@123`
- **Không commit secrets**: Lệnh `seed_data` ưu tiên đọc biến môi trường `SEED_DEMO_ADMIN_PASSWORD` và `SEED_DEMO_STUDENT_PASSWORD`. Không commit file `.env` cá nhân chứa mật khẩu hoặc khóa bí mật thật lên Git (`.env` đã nằm trong `.gitignore`).
