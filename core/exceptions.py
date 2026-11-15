"""
Standardized JSON Exception Handler, Error Codes, and Domain Exceptions for RESTful API.
Covers all 4 required categories:
1. Validation Error (`DomainValidationException`)
2. Business Logic Error (`BusinessLogicException`, `InsufficientBalanceException`, `BudgetExceededException`)
3. Access / Permission Denied (`AccessDeniedException`)
4. Resource Not Found (`ResourceNotFoundException`)
"""
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError as DRFValidationError,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ErrorCode:
    """Chuẩn hóa bảng mã lỗi (Error Codes) thống nhất toàn hệ thống."""

    VALIDATION_ERROR = "validation_error"
    BUSINESS_LOGIC_ERROR = "business_logic_error"
    INSUFFICIENT_BALANCE = "insufficient_balance"
    BUDGET_EXCEEDED = "budget_exceeded"
    PERMISSION_DENIED = "permission_denied"
    AUTHENTICATION_FAILED = "authentication_failed"
    RESOURCE_NOT_FOUND = "resource_not_found"
    INTERNAL_ERROR = "internal_server_error"


class DomainValidationException(APIException):
    """1. Ngoại lệ cho lỗi kiểm tra dữ liệu đầu vào ở tầng Domain/Service."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Dữ liệu đầu vào không hợp lệ."
    default_code = ErrorCode.VALIDATION_ERROR


class BusinessLogicException(APIException):
    """2. Ngoại lệ cơ sở cho các vi phạm quy tắc nghiệp vụ tài chính."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Vi phạm quy tắc nghiệp vụ hệ thống."
    default_code = ErrorCode.BUSINESS_LOGIC_ERROR


class InsufficientBalanceException(BusinessLogicException):
    """2a. Ngoại lệ khi số dư ví không đủ để chi tiêu hoặc chuyển khoản."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Số dư ví không đủ để thực hiện giao dịch này."
    default_code = ErrorCode.INSUFFICIENT_BALANCE


class BudgetExceededException(BusinessLogicException):
    """2b. Ngoại lệ khi thao tác vượt quá hạn mức ngân sách cứng cho phép."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Khoản chi vượt quá hạn mức ngân sách cho phép."
    default_code = ErrorCode.BUDGET_EXCEEDED


class AccessDeniedException(APIException):
    """3. Ngoại lệ khi người dùng truy cập trái quyền (RBAC / Object Ownership)."""

    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "Bạn không có quyền thực hiện thao tác trên tài nguyên này."
    default_code = ErrorCode.PERMISSION_DENIED


class ResourceNotFoundException(APIException):
    """4. Ngoại lệ khi không tìm thấy bản ghi hoặc bản ghi đã bị xóa mềm (`is_deleted=True`)."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tài nguyên yêu cầu không tồn tại hoặc đã bị xóa."
    default_code = ErrorCode.RESOURCE_NOT_FOUND


def custom_exception_handler(exc, context):
    """
    Custom DRF Exception Handler trả về cấu trúc JSON lỗi đồng nhất cho cả 30 APIs:
    {
        "success": false,
        "status": "error",
        "error_code": "<error_code>",
        "message": "<human_readable_summary>",
        "error": {
            "code": "<error_code>",
            "message": "<human_readable_summary>",
            "details": { ... }
        }
    }
    """
    if isinstance(exc, DjangoValidationError):
        details = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
        return Response(
            {
                "success": False,
                "status": "error",
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "Dữ liệu đầu vào không hợp lệ.",
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": "Dữ liệu đầu vào không hợp lệ.",
                    "details": details,
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, Http404):
        exc = ResourceNotFoundException()
    elif isinstance(exc, DjangoPermissionDenied):
        exc = AccessDeniedException()

    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, DRFValidationError):
            error_code = ErrorCode.VALIDATION_ERROR
            message = "Dữ liệu đầu vào không hợp lệ."
            details = response.data
        elif isinstance(exc, (PermissionDenied, AccessDeniedException)):
            error_code = ErrorCode.PERMISSION_DENIED
            message = str(getattr(exc, "detail", AccessDeniedException.default_detail))
            details = None
        elif isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
            error_code = ErrorCode.AUTHENTICATION_FAILED
            message = str(getattr(exc, "detail", "Chưa xác thực hoặc token không hợp lệ."))
            details = None
        else:
            error_code = getattr(exc, "default_code", ErrorCode.BUSINESS_LOGIC_ERROR)
            if isinstance(response.data, dict) and "detail" in response.data:
                message = str(response.data["detail"])
                details = None
            else:
                message = "Yêu cầu không hợp lệ hoặc gặp lỗi xử lý."
                details = response.data

        response.data = {
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

    return response
