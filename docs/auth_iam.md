# W2.03 — Auth/IAM

Module dùng `UserAccount` làm định danh chung cho năm phân hệ. Đăng ký chỉ tạo `STUDENT`; tài khoản `ADMIN` được tạo qua công cụ quản trị. MSSV gồm đúng 8 chữ số, email phải thuộc `@gm.uit.edu.vn` hoặc `@uit.edu.vn`, mật khẩu qua bộ validator của Django. Các trường `id`, `email`, `student_code`, `role`, `is_active` và `created_at` không thể sửa qua API hồ sơ.

| Endpoint | Quyền | Công dụng |
| --- | --- | --- |
| `POST /api/v1/auth/register/` | Công khai | Tạo tài khoản Student |
| `POST /api/v1/auth/login/` | Công khai | Nhận `access` và `refresh` JWT |
| `POST /api/v1/auth/token/refresh/` | Công khai, cần refresh token hợp lệ | Nhận access token mới |
| `GET/PATCH /api/v1/users/me/` | JWT | Xem/sửa hồ sơ của chính người dùng từ token |
| `PATCH /api/v1/users/me/allowance/` | JWT | Sửa trợ cấp và khu vực ở |
| `GET /api/v1/admin/users/` | Admin | Danh sách và thống kê hệ thống |
| `PATCH /api/v1/admin/users/{user_id}/toggle-status/` | Admin | Chỉ khóa/mở tài khoản Student |

Access token có hạn 2 giờ, refresh token 7 ngày theo `config/settings.py`; header là `Authorization: Bearer <access>`. Login sai thông tin, access token hết hạn, hoặc tài khoản bị khóa trả 401. Student gọi API Admin hoặc Admin thử khóa tài khoản Admin trả 403. UUID không tồn tại ở API toggle trả 404. Các lỗi do `core.exceptions.custom_exception_handler` trả về với `success: false`, `error_code`, `message` và `error`.

Kiểm tra bằng `python -m pytest tests/test_auth.py tests/test_auth_schema.py -v`, `python manage.py check`, và `python manage.py spectacular --validate --fail-on-warn`. Swagger UI ở `/api/schema/swagger/` có nhóm `1. Auth & User Management` để thử đăng ký, login, refresh, hồ sơ và Admin.
