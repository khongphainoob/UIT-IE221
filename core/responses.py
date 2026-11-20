"""
Standardized JSON Response Helper (`APIResponse`) for all 30 RESTful APIs.
Ensures consistent `success` / `error` envelope across all modules.
"""
from typing import Any, Optional
from rest_framework import status
from rest_framework.response import Response
from core.exceptions import ErrorCode


class APIResponse:
    """
    Tiện ích chuẩn hóa cấu trúc JSON trả về từ tầng View (`APIView`):
    - Thành công: `{"success": True, "status": "success", "message": "...", "data": ...}`
    - Thất bại:   `{"success": False, "status": "error", "error_code": "...", "message": "...", "error": {...}}`
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "Thao tác thành công.",
        status_code: int = status.HTTP_200_OK,
    ) -> Response:
        payload = {
            "success": True,
            "status": "success",
            "message": message,
            "data": data,
        }
        return Response(payload, status=status_code)

    @staticmethod
    def created(
        data: Any = None,
        message: str = "Khởi tạo bản ghi thành công.",
    ) -> Response:
        return APIResponse.success(
            data=data, message=message, status_code=status.HTTP_201_CREATED
        )

    @staticmethod
    def error(
        message: str = "Yêu cầu không hợp lệ.",
        error_code: str = ErrorCode.BUSINESS_LOGIC_ERROR,
        details: Optional[Any] = None,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> Response:
        payload = {
            "success": False,
            "status": "error",
            "error_code": error_code,
            "message": message,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            },
        }
        return Response(payload, status=status_code)
