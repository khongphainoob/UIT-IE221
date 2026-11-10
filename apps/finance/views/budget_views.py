"""
Module 4 (budget_alert): MonthlyBudget (CRUD + Clone Previous Month),
RecurringBill CRUD, and BudgetAlertLog APIViews.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance.models import RecurringBill
from apps.finance.serializers import (
    BudgetAlertLogSerializer,
    MonthlyBudgetSerializer,
    RecurringBillSerializer,
)
from apps.finance.services import BudgetService
from core.exceptions import ResourceNotFoundException
from core.permissions import IsStudentOwner


class BudgetListCreateAPIView(APIView):
    """API 22 & 23: Xem danh sách ngân sách tháng và thiết lập hạn mức ngân sách."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        responses={200: MonthlyBudgetSerializer(many=True)},
        tags=["4. Budgets & Alerts"],
        summary="Danh sách hạn mức & tiến độ sử dụng ngân sách tháng",
    )
    def get(self, request):
        month = request.query_params.get("month")
        year = request.query_params.get("year")
        budgets = self.budget_service.list_user_budgets(
            user_id=request.user.id,
            month=int(month) if month else None,
            year=int(year) if year else None,
        )
        serializer = MonthlyBudgetSerializer(budgets, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=MonthlyBudgetSerializer,
        responses={201: MonthlyBudgetSerializer},
        tags=["4. Budgets & Alerts"],
        summary="Thiết lập hoặc cập nhật ngân sách tháng",
    )
    def post(self, request):
        serializer = MonthlyBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        budget = self.budget_service.create_or_update_budget(
            user_id=request.user.id, validated_data=serializer.validated_data
        )
        return Response(
            {"success": True, "data": MonthlyBudgetSerializer(budget).data},
            status=status.HTTP_201_CREATED,
        )


class BudgetDetailAPIView(APIView):
    """API 24: Điều chỉnh hạn mức hoặc xóa mềm ngân sách tháng."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        request=MonthlyBudgetSerializer,
        responses={200: MonthlyBudgetSerializer},
        tags=["4. Budgets & Alerts"],
        summary="Điều chỉnh hạn mức ngân sách tháng",
    )
    def put(self, request, budget_id):
        serializer = MonthlyBudgetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        budget = self.budget_service.update_budget_by_id(
            user_id=request.user.id,
            budget_id=budget_id,
            validated_data=serializer.validated_data,
        )
        return Response({"success": True, "data": MonthlyBudgetSerializer(budget).data})

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["4. Budgets & Alerts"],
        summary="Xóa mềm hạn mức ngân sách tháng",
    )
    def delete(self, request, budget_id):
        self.budget_service.delete_budget_by_id(
            user_id=request.user.id, budget_id=budget_id
        )
        return Response({"success": True, "message": "Đã xóa ngân sách thành công."})


class BudgetClonePreviousMonthAPIView(APIView):
    """API 25: Sao chép cấu hình hạn mức ngân sách tháng trước sang tháng hiện tại."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={201: MonthlyBudgetSerializer(many=True)},
        tags=["4. Budgets & Alerts"],
        summary="Sao chép hạn mức ngân sách tháng trước sang tháng mới",
    )
    def post(self, request):
        month = request.data.get("month") if isinstance(request.data, dict) else None
        year = request.data.get("year") if isinstance(request.data, dict) else None
        cloned = self.budget_service.clone_previous_month_budgets(
            user_id=request.user.id,
            target_month=int(month) if month else None,
            target_year=int(year) if year else None,
        )
        return Response(
            {"success": True, "data": MonthlyBudgetSerializer(cloned, many=True).data},
            status=status.HTTP_201_CREATED,
        )


class BudgetAlertListAPIView(APIView):
    """API 26: Danh sách cảnh báo vượt 80%, 100%, Anomaly và Burn-rate."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        responses={200: BudgetAlertLogSerializer(many=True)},
        tags=["4. Budgets & Alerts"],
        summary="Lấy danh sách cảnh báo tài chính của sinh viên",
    )
    def get(self, request):
        alerts = self.budget_service.list_user_alerts(user_id=request.user.id)
        serializer = BudgetAlertLogSerializer(alerts, many=True)
        return Response({"success": True, "data": serializer.data})


class BudgetAlertMarkReadAPIView(APIView):
    """Đánh dấu đã đọc một cảnh báo ngân sách."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        request=None,
        responses={200: BudgetAlertLogSerializer},
        tags=["4. Budgets & Alerts"],
        summary="Đánh dấu đã đọc cảnh báo tài chính",
    )
    def patch(self, request, alert_id):
        alert = self.budget_service.mark_alert_as_read(
            user_id=request.user.id, alert_id=alert_id
        )
        return Response(
            {"success": True, "data": BudgetAlertLogSerializer(alert).data}
        )


class RecurringBillListCreateAPIView(APIView):
    """API 19 & 20: Quản lý các khoản hóa đơn định kỳ KTX (Tiền phòng KTX, 4G, điện nước)."""

    permission_classes = [IsStudentOwner]
    budget_service = BudgetService()

    @extend_schema(
        responses={200: RecurringBillSerializer(many=True)},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Danh sách hóa đơn định kỳ (KTX, 4G, Điện nước)",
    )
    def get(self, request):
        bills = self.budget_service.budget_repo.get_active_recurring_bills(
            user_id=request.user.id
        )
        return Response(
            {"success": True, "data": RecurringBillSerializer(bills, many=True).data}
        )

    @extend_schema(
        request=RecurringBillSerializer,
        responses={201: RecurringBillSerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Thêm hóa đơn định kỳ mới",
    )
    def post(self, request):
        serializer = RecurringBillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bill = serializer.save(user=request.user)
        return Response(
            {"success": True, "data": RecurringBillSerializer(bill).data},
            status=status.HTTP_201_CREATED,
        )


class RecurringBillDetailAPIView(APIView):
    """Cập nhật hoặc xóa mềm hóa đơn định kỳ KTX."""

    permission_classes = [IsStudentOwner]

    @extend_schema(
        request=RecurringBillSerializer,
        responses={200: RecurringBillSerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Cập nhật hóa đơn định kỳ KTX",
    )
    def put(self, request, bill_id):
        bill = RecurringBill.objects.filter(
            id=bill_id, user=request.user, is_deleted=False
        ).first()
        if not bill:
            raise ResourceNotFoundException(
                f"Không tìm thấy hóa đơn định kỳ với ID={bill_id}."
            )
        serializer = RecurringBillSerializer(bill, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Xóa mềm hóa đơn định kỳ KTX",
    )
    def delete(self, request, bill_id):
        bill = RecurringBill.objects.filter(
            id=bill_id, user=request.user, is_deleted=False
        ).first()
        if not bill:
            raise ResourceNotFoundException(
                f"Không tìm thấy hóa đơn định kỳ với ID={bill_id}."
            )
        bill.soft_delete()
        return Response({"success": True, "message": "Đã xóa hóa đơn định kỳ."})
