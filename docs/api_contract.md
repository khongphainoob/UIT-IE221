# Quy ước API contract (W1.07)

Tất cả endpoint nghiệp vụ đặt dưới `/api/v1/`. OpenAPI ở `/api/schema/`, giao diện thử API ở `/api/schema/swagger/`. Năm nhóm nghiệp vụ trong Swagger là Auth & User Management, Wallets, Categories/Transactions/Recurring Bills, Budgets/Alerts, và Analytics/ML Serving Engine. Tên tag được định nghĩa tập trung trong `config/settings.py` và phải dùng thống nhất trong `@extend_schema`.

## Request và xác thực

Body JSON dùng `Content-Type: application/json`; các tham số định danh trong URL là UUID. Các API được bảo vệ dùng JWT access token trong header `Authorization: Bearer <access>`. `POST /api/v1/auth/register/`, `POST /api/v1/auth/login/` và các endpoint làm mới token không cần token. Các API còn lại mặc định cần xác thực; một số API quản trị còn cần quyền Admin. Token login/refresh là phản hồi chuẩn của SimpleJWT (`access`, `refresh`), không dùng lớp bọc nghiệp vụ.

## Response và lỗi

API nghiệp vụ thành công trả HTTP 200 hoặc 201 với `{ "success": true, "data": ... }`. Một số thao tác dùng thêm `message`; các helper trong `core/responses.py` có thể trả thêm `status` và `message`. Không suy diễn rằng mọi endpoint hiện tại có cùng một bộ trường tùy chọn.

Lỗi do `core.exceptions.custom_exception_handler` xử lý có cấu trúc `{ "success": false, "status": "error", "error_code": "...", "message": "...", "error": { "code": "...", "message": "...", "details": null } }`. `details` có thể là đối tượng hoặc danh sách khi validation thất bại. Các mã HTTP cần mô tả trong schema theo từng endpoint: 400 (dữ liệu hoặc nghiệp vụ không hợp lệ), 401 (thiếu/sai JWT), 403 (không đủ quyền), 404 (không tìm thấy tài nguyên). Mã 400 không mặc nhiên áp dụng cho endpoint chỉ đọc; mã 404 chỉ áp dụng khi có tài nguyên định danh.

## Mẫu kiểm chứng

`GET /api/v1/wallets/` yêu cầu JWT và trả danh sách trong `data`; Swagger mô tả cả trường ví và lỗi 401. `POST /api/v1/wallets/` mô tả request bằng `WalletSerializer`, response 201 trong lớp bọc `success/data`, và lỗi 400/401. Khi thêm API, dùng cùng quy ước cho request, response, tags, summary, và chỉ khai báo status code thực sự có thể xảy ra.

Chạy `python manage.py spectacular --validate --fail-on-warn` để kiểm tra schema, sau đó chạy `pytest` để kiểm tra cả đường dẫn Swagger, JWT security scheme và endpoint mẫu.
