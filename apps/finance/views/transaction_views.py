"""
Module 3 (transaction): Categories, Transactions (CRUD + Advanced Filter),
and Recurring Bills KTX (CRUD + Auto-Pay) APIViews (9+ APIs).
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance.models import ExpenseCategory, RecurringBill
from apps.finance.repositories import BudgetRepository
from apps.finance.serializers import (
    ExpenseCategorySerializer,
    ExpenseTransactionSerializer,
    RecurringBillSerializer,
)
from apps.finance.services import TransactionService
from core.exceptions import ResourceNotFoundException
from core.permissions import IsStudentOwner


class CategoryListCreateAPIView(APIView):
    """API 13 & 14: Liệt kê và tạo danh mục thu/chi."""

    permission_classes = [IsStudentOwner]
    budget_repo = BudgetRepository()

    @extend_schema(
        responses={200: ExpenseCategorySerializer(many=True)},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Danh sách danh mục Thu / Chi",
    )
    def get(self, request):
        categories = self.budget_repo.get_available_categories(user_id=request.user.id)
        serializer = ExpenseCategorySerializer(categories, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=ExpenseCategorySerializer,
        responses={201: ExpenseCategorySerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Tạo danh mục Thu / Chi mới",
    )
    def post(self, request):
        serializer = ExpenseCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save(user=request.user)
        return Response(
            {"success": True, "data": ExpenseCategorySerializer(category).data},
            status=status.HTTP_201_CREATED,
        )


class CategoryDetailAPIView(APIView):
    """Cập nhật hoặc xóa mềm danh mục chi tiêu cá nhân."""

    permission_classes = [IsStudentOwner]

    @extend_schema(
        request=ExpenseCategorySerializer,
        responses={200: ExpenseCategorySerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Cập nhật danh mục chi tiêu",
    )
    def put(self, request, category_id):
        cat = ExpenseCategory.objects.filter(
            id=category_id, user=request.user, is_deleted=False
        ).first()
        if not cat:
            raise ResourceNotFoundException(
                f"Không tìm thấy danh mục cá nhân với ID={category_id}."
            )
        serializer = ExpenseCategorySerializer(cat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Xóa mềm danh mục chi tiêu",
    )
    def delete(self, request, category_id):
        cat = ExpenseCategory.objects.filter(
            id=category_id, user=request.user, is_deleted=False
        ).first()
        if not cat:
            raise ResourceNotFoundException(
                f"Không tìm thấy danh mục cá nhân với ID={category_id}."
            )
        cat.soft_delete()
        return Response({"success": True, "message": "Đã xóa danh mục thành công."})


class TransactionListCreateAPIView(APIView):
    """API 15 & 16: Lọc lịch sử giao dịch nâng cao và ghi nhận giao dịch mới (kèm Anomaly Detection)."""

    permission_classes = [IsStudentOwner]
    transaction_service = TransactionService()

    @extend_schema(
        responses={200: ExpenseTransactionSerializer(many=True)},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Lọc lịch sử giao dịch (theo ngày, danh mục, khoảng tiền, cờ bất thường, từ khóa)",
    )
    def get(self, request):
        wallet_id = request.query_params.get("wallet_id")
        category_id = request.query_params.get("category_id")
        tx_type = request.query_params.get("transaction_type")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        min_amount = request.query_params.get("min_amount")
        max_amount = request.query_params.get("max_amount")
        is_anomaly_param = request.query_params.get("is_anomaly")
        search = request.query_params.get("search")

        is_anomaly = None
        if is_anomaly_param is not None and is_anomaly_param != "":
            is_anomaly = is_anomaly_param.lower() in ("true", "1", "yes")

        transactions = self.transaction_service.list_user_transactions(
            user_id=request.user.id,
            wallet_id=wallet_id,
            category_id=category_id,
            transaction_type=tx_type,
            start_date=start_date,
            end_date=end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            is_anomaly=is_anomaly,
            search=search,
        )
        serializer = ExpenseTransactionSerializer(transactions, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=ExpenseTransactionSerializer,
        responses={201: ExpenseTransactionSerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Ghi nhận giao dịch Thu / Chi mới (Trừ tiền ví + Cộng ngân sách + Chấm điểm Anomaly)",
    )
    def post(self, request):
        serializer = ExpenseTransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tx = self.transaction_service.record_transaction(
            user_id=request.user.id, validated_data=serializer.validated_data
        )
        return Response(
            {"success": True, "data": ExpenseTransactionSerializer(tx).data},
            status=status.HTTP_201_CREATED,
        )


class TransactionDetailAPIView(APIView):
    """API 17 & 18: Sửa giao dịch hoặc Xóa mềm giao dịch & hoàn trả số dư ví."""

    permission_classes = [IsStudentOwner]
    transaction_service = TransactionService()

    @extend_schema(
        request=ExpenseTransactionSerializer,
        responses={200: ExpenseTransactionSerializer},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Cập nhật giao dịch & đồng bộ lại số dư ví",
    )
    def put(self, request, transaction_id):
        serializer = ExpenseTransactionSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        tx = self.transaction_service.update_transaction(
            user_id=request.user.id,
            transaction_id=transaction_id,
            validated_data=serializer.validated_data,
        )
        return Response(
            {"success": True, "data": ExpenseTransactionSerializer(tx).data}
        )

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Xóa mềm giao dịch (Soft Delete) & hoàn trả số dư ví",
    )
    def delete(self, request, transaction_id):
        self.transaction_service.delete_transaction(
            user_id=request.user.id, transaction_id=transaction_id
        )
        return Response(
            {"success": True, "message": "Đã xóa giao dịch và hoàn lại số dư ví."},
            status=status.HTTP_200_OK,
        )


class RecurringBillPayAPIView(APIView):
    """API 21: Thanh toán tự động hóa đơn định kỳ KTX (trừ tiền ví & ghi giao dịch)."""

    permission_classes = [IsStudentOwner]
    transaction_service = TransactionService()

    @extend_schema(
        request=OpenApiTypes.OBJECT,
        responses={200: OpenApiTypes.OBJECT},
        tags=["3. Categories, Transactions & Recurring Bills"],
        summary="Kích hoạt thanh toán hóa đơn định kỳ KTX (Tiền phòng, Điện nước, 4G)",
    )
    def post(self, request, bill_id):
        wallet_id = request.data.get("wallet_id") if isinstance(request.data, dict) else None
        result = self.transaction_service.pay_recurring_bill(
            user_id=request.user.id, bill_id=bill_id, wallet_id=wallet_id
        )
        return Response(
            {
                "success": True,
                "data": {
                    "bill": RecurringBillSerializer(result["bill"]).data,
                    "transaction": ExpenseTransactionSerializer(
                        result["transaction"]
                    ).data,
                },
            },
            status=status.HTTP_200_OK,
        )
