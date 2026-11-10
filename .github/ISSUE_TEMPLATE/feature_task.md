---
name: "Task / Feature Đồ án IE221"
about: "Mẫu tạo Task phát triển tính năng hoặc API theo chuẩn 5 Module (22 chức năng - 30 APIs)"
title: "[M1-M5] Feat: <Tên chức năng hoặc API>"
labels: ["enhancement", "ie221"]
---

## 1. Mục tiêu Task
- **Phân hệ**: `M1 (auth_iam)` / `M2 (wallet_mgmt)` / `M3 (transaction)` / `M4 (budget_alert)` / `M5 (analytics_engine)`
- **Thành viên phụ trách**: 
- **Endpoint API liên quan**: `METHOD /api/v1/...`

## 2. Các bước thực hiện theo 5 tầng MVT
- [ ] **Bước 1 (Model)**: Kiểm tra/cập nhật model trong `apps/finance/models/` (nếu cần).
- [ ] **Bước 2 (Repository)**: Viết hàm truy vấn ORM trong `apps/finance/repositories/`.
- [ ] **Bước 3 (Service / Engine)**: Viết xử lý nghiệp vụ (`@transaction.atomic`) hoặc thuật toán ML (`BaseFinancialAnalyzer`).
- [ ] **Bước 4 (Serializer)**: Viết Serializer validate đầu vào & chuẩn hóa JSON đầu ra.
- [ ] **Bước 5 (View & URL)**: Viết `APIView` có gắn `@extend_schema` và khai báo route trong `apps/finance/urls.py`.

## 3. Tiêu chí Nghiệm thu Đóng Task (Definition of Done)
- [ ] Có ít nhất 2 kịch bản test trong `tests/` (Happy Path + Error/Rollback Path).
- [ ] Chạy `pytest -v` xanh 100%.
- [ ] Chạy `python manage.py spectacular --validate --fail-on-warn` đạt 0 lỗi, 0 cảnh báo.
- [ ] Cập nhật `postman/IE221_Collection.json`.
- [ ] Tạo PR đúng chuẩn `[M<1-5>-<Module>] Feat: ...` và được merge vào `main`.

