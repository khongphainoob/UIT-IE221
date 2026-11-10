"""
Module 2 (wallet_mgmt): Wallet CRUD & Atomic Internal Transfer APIViews (6 APIs).
Strictly delegates all business logic and ORM access to `WalletService`.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance.serializers import WalletSerializer, WalletTransferSerializer
from apps.finance.services import WalletService
from core.permissions import IsStudentOwner


class WalletListCreateAPIView(APIView):
    """API 7 & 8: Liệt kê danh sách ví và tạo ví mới cho sinh viên."""

    permission_classes = [IsStudentOwner]
    wallet_service = WalletService()

    @extend_schema(
        responses={200: WalletSerializer(many=True)},
        tags=["2. Wallets"],
        summary="Danh sách ví tiền của sinh viên",
    )
    def get(self, request):
        wallets = self.wallet_service.list_user_wallets(user_id=request.user.id)
        serializer = WalletSerializer(wallets, many=True)
        return Response({"success": True, "data": serializer.data})

    @extend_schema(
        request=WalletSerializer,
        responses={201: WalletSerializer},
        tags=["2. Wallets"],
        summary="Tạo ví tiền mới (Tiền mặt, MoMo, Ngân hàng)",
    )
    def post(self, request):
        serializer = WalletSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = self.wallet_service.create_wallet(
            user_id=request.user.id, validated_data=serializer.validated_data
        )
        return Response(
            {"success": True, "data": WalletSerializer(wallet).data},
            status=status.HTTP_201_CREATED,
        )


class WalletDetailAPIView(APIView):
    """API 9, 10 & 11: Xem chi tiết, cập nhật tên/trạng thái, và xóa mềm ví tiền."""

    permission_classes = [IsStudentOwner]
    wallet_service = WalletService()

    @extend_schema(
        responses={200: WalletSerializer},
        tags=["2. Wallets"],
        summary="Xem chi tiết số dư & biến động ví",
    )
    def get(self, request, wallet_id):
        wallet = self.wallet_service.get_wallet_detail(
            user_id=request.user.id, wallet_id=wallet_id
        )
        return Response({"success": True, "data": WalletSerializer(wallet).data})

    @extend_schema(
        request=WalletSerializer,
        responses={200: WalletSerializer},
        tags=["2. Wallets"],
        summary="Cập nhật tên hoặc trạng thái ví",
    )
    def put(self, request, wallet_id):
        serializer = WalletSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        wallet = self.wallet_service.update_wallet(
            user_id=request.user.id,
            wallet_id=wallet_id,
            validated_data=serializer.validated_data,
        )
        return Response({"success": True, "data": WalletSerializer(wallet).data})

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["2. Wallets"],
        summary="Xóa mềm ví tiền (Soft Delete)",
    )
    def delete(self, request, wallet_id):
        self.wallet_service.delete_wallet(
            user_id=request.user.id, wallet_id=wallet_id
        )
        return Response(
            {"success": True, "message": "Đã xóa mềm ví tiền thành công."},
            status=status.HTTP_200_OK,
        )


class WalletTransferAPIView(APIView):
    """API 12: Chuyển tiền nội bộ an toàn giữa 2 ví bằng @transaction.atomic."""

    permission_classes = [IsStudentOwner]
    wallet_service = WalletService()

    @extend_schema(
        request=WalletTransferSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["2. Wallets"],
        summary="Chuyển tiền nội bộ giữa 2 ví (@transaction.atomic)",
    )
    def post(self, request):
        serializer = WalletTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = self.wallet_service.transfer_between_wallets(
            user_id=request.user.id,
            source_wallet_id=data["source_wallet_id"],
            target_wallet_id=data["target_wallet_id"],
            amount=data["amount"],
            note=data.get("note", ""),
        )
        return Response(
            {
                "success": True,
                "data": {
                    "transaction_id": str(result["transaction"].id),
                    "source_wallet": WalletSerializer(result["source_wallet"]).data,
                    "target_wallet": WalletSerializer(result["target_wallet"]).data,
                },
            },
            status=status.HTTP_200_OK,
        )
