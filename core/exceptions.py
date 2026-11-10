"""
Standardized JSON Exception Handler and Domain Exceptions for RESTful API.
"""
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler


class BusinessLogicException(APIException):
    """Base exception for domain/service business rule violations."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Vi phạm quy tắc nghiệp vụ hệ thống."
    default_code = "business_logic_error"


class InsufficientBalanceException(BusinessLogicException):
    """Raised when a wallet balance is insufficient for an expense or transfer."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Số dư ví không đủ để thực hiện giao dịch này."
    default_code = "insufficient_balance"


class ResourceNotFoundException(APIException):
    """Raised when a requested entity does not exist or was soft-deleted."""

    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Tài nguyên yêu cầu không tồn tại."
    default_code = "resource_not_found"


def custom_exception_handler(exc, context):
    """
    Custom DRF Exception Handler returning a unified JSON envelope:
    {
        "success": false,
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
                "error": {
                    "code": "validation_error",
                    "message": "Dữ liệu đầu vào không hợp lệ.",
                    "details": details,
                },
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    response = exception_handler(exc, context)

    if response is not None:
        error_code = getattr(exc, "default_code", "api_error")
        if isinstance(response.data, dict) and "detail" in response.data:
            message = str(response.data["detail"])
            details = None
        else:
            message = "Yêu cầu không hợp lệ hoặc gặp lỗi xử lý."
            details = response.data

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
            },
        }

    return response

