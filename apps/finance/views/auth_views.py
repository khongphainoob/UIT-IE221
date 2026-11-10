"""
Module 1 (auth_iam): Authentication, Student Profile, Allowance Config & Admin User Management APIViews.
"""
from django.db.models import Count, Sum
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance.models import ExpenseTransaction, UserAccount, Wallet
from apps.finance.serializers import (
    StudentRegistrationSerializer,
    UserAllowanceUpdateSerializer,
    UserProfileSerializer,
)
from core.exceptions import ResourceNotFoundException
from core.permissions import IsAdmin


class StudentRegistrationAPIView(APIView):
    """API 1: Đăng ký tài khoản sinh viên UIT (@gm.uit.edu.vn / @uit.edu.vn)."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=StudentRegistrationSerializer,
        responses={201: StudentRegistrationSerializer},
        tags=["1. Auth & User Management"],
        summary="Đăng ký tài khoản sinh viên UIT",
    )
    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "success": True,
                "data": StudentRegistrationSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileAPIView(APIView):
    """API 4: Xem và cập nhật thông tin hồ sơ cá nhân của sinh viên đang đăng nhập."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: UserProfileSerializer},
        tags=["1. Auth & User Management"],
        summary="Xem hồ sơ người dùng hiện tại",
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        tags=["1. Auth & User Management"],
        summary="Cập nhật hồ sơ cá nhân",
    )
    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})


class UserAllowanceUpdateAPIView(APIView):
    """API 5: Cập nhật trợ cấp tháng (`monthly_income_limit`) và khu vực KTX (`dorm_area`)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=UserAllowanceUpdateSerializer,
        responses={200: UserProfileSerializer},
        tags=["1. Auth & User Management"],
        summary="Cập nhật trợ cấp hàng tháng & khu vực KTX",
    )
    def patch(self, request):
        serializer = UserAllowanceUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": True, "data": UserProfileSerializer(user).data},
            status=status.HTTP_200_OK,
        )


class AdminUserManagementAPIView(APIView):
    """API 6: Admin xem danh sách sinh viên và thống kê toàn hệ thống."""

    permission_classes = [IsAdmin]

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["1. Auth & User Management"],
        summary="[ADMIN] Danh sách người dùng & thống kê toàn hệ thống",
    )
    def get(self, request):
        users = UserAccount.objects.all().order_by("-created_at")
        system_stats = {
            "total_users": users.count(),
            "total_students": users.filter(role=UserAccount.Role.STUDENT).count(),
            "total_wallets": Wallet.objects.count(),
            "total_transactions": ExpenseTransaction.objects.count(),
            "total_anomaly_transactions": ExpenseTransaction.objects.filter(
                is_anomaly=True
            ).count(),
            "total_system_balance": float(
                Wallet.objects.aggregate(s=Sum("balance"))["s"] or 0.0
            ),
        }
        return Response(
            {
                "success": True,
                "data": {
                    "system_statistics": system_stats,
                    "users": UserProfileSerializer(users, many=True).data,
                },
            }
        )


class AdminUserToggleStatusAPIView(APIView):
    """API phụ trợ Admin: Khóa / Mở khóa tài khoản sinh viên."""

    permission_classes = [IsAdmin]

    @extend_schema(
        request=None,
        responses={200: UserProfileSerializer},
        tags=["1. Auth & User Management"],
        summary="[ADMIN] Khóa hoặc mở khóa tài khoản sinh viên",
    )
    def patch(self, request, user_id):
        target_user = UserAccount.objects.filter(id=user_id).first()
        if not target_user:
            raise ResourceNotFoundException(
                f"Không tìm thấy người dùng với ID={user_id}."
            )
        target_user.is_active = not target_user.is_active
        target_user.save(update_fields=["is_active", "updated_at"])
        return Response(
            {"success": True, "data": UserProfileSerializer(target_user).data}
        )
