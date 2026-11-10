"""
Custom Role-Based and Object-Level Permissions for Student Expense Analytics API.
"""
from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """
    Allows access only to users with role == 'ADMIN' or Django superuser status.
    """

    message = "Chỉ Quản trị viên (ADMIN) mới có quyền truy cập tài nguyên này."

    def has_permission(self, request, view) -> bool:
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (getattr(user, "role", None) == "ADMIN" or user.is_superuser)
        )


class IsStudentOwner(BasePermission):
    """
    Allows access only to authenticated students who own the target resource,
    or ADMIN users.
    """

    message = "Bạn không có quyền truy cập hoặc chỉnh sửa dữ liệu của sinh viên khác."

    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        if getattr(user, "role", None) == "ADMIN" or user.is_superuser:
            return True
        owner = getattr(obj, "user", None)
        if owner is not None:
            return owner.id == user.id
        return obj.id == user.id

