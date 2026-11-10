"""
Module 5 (analytics_engine): Burn-Rate Forecaster, Anomaly Detector,
RiskClassifier (Financial Health Score), Spending Structure, and Report Export (CSV/Excel).
"""
from django.http import HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.finance.engines import (
    AnomalyDetectionEngine,
    BurnRateAnalyzer,
    CSVReportExporter,
    ExcelReportExporter,
    RiskClassifier,
)
from apps.finance.models import BudgetAlertLog, ExpenseTransaction
from apps.finance.repositories import (
    BudgetRepository,
    TransactionRepository,
    WalletRepository,
)
from apps.finance.serializers import (
    AnomalyReportResponseSerializer,
    BurnRateResponseSerializer,
    FinancialHealthResponseSerializer,
)
from core.permissions import IsStudentOwner


class BurnRateForecastAPIView(APIView):
    """
    API 27 (Module Ăn Điểm 1): Dự báo tốc độ tiêu tiền & ngày cạn ví (`BurnRateForecaster`).
    Uses Pandas `.resample('D').sum()`, 7-day rolling moving average, and Scikit-learn `HuberRegressor`.
    """

    permission_classes = [IsStudentOwner]
    transaction_repo = TransactionRepository()
    wallet_repo = WalletRepository()

    @extend_schema(
        responses={200: BurnRateResponseSerializer},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Dự báo tốc độ tiêu tiền & Ngày cạn ví (Pandas + HuberRegressor)",
    )
    def get(self, request):
        user_id = request.user.id
        total_balance = self.wallet_repo.get_total_balance(user_id=user_id)
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user_id
        )

        analyzer = BurnRateAnalyzer(
            raw_transactions=expense_records,
            current_balance=total_balance,
        )
        report = analyzer.run_inference()
        return Response({"success": True, "data": report})


class AnomalyDetectionAPIView(APIView):
    """
    API 28 (Module Ăn Điểm 2): Quét & Phát hiện giao dịch bất thường (`IsolationForest` + `Z-Score` + `IQR`).
    Supports both GET (read-only scan) and POST (scan + persist `is_anomaly=True` & `BudgetAlertLog`).
    """

    permission_classes = [IsStudentOwner]
    transaction_repo = TransactionRepository()
    budget_repo = BudgetRepository()

    @extend_schema(
        responses={200: AnomalyReportResponseSerializer},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Xem báo cáo các giao dịch chi tiêu bất thường (Z-Score / IQR / IsolationForest)",
    )
    def get(self, request):
        user_id = request.user.id
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user_id
        )
        engine = AnomalyDetectionEngine(raw_transactions=expense_records)
        report = engine.run_inference()
        return Response({"success": True, "data": report})

    @extend_schema(
        request=None,
        responses={200: AnomalyReportResponseSerializer},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Kích hoạt quét ML (IsolationForest + Z-Score) & tự động gắn cờ is_anomaly vào CSDL",
    )
    def post(self, request):
        user_id = request.user.id
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user_id
        )
        engine = AnomalyDetectionEngine(raw_transactions=expense_records)
        report = engine.run_inference()

        anomaly_ids = [item["id"] for item in report["anomalies"] if item.get("id")]
        if anomaly_ids:
            ExpenseTransaction.objects.filter(
                user_id=user_id, id__in=anomaly_ids
            ).update(is_anomaly=True)
            self.budget_repo.create_alert(
                user_id=user_id,
                alert_type=BudgetAlertLog.AlertType.ANOMALY,
                message=(
                    f"[QUÉT ML ANOMALY] Phát hiện {len(anomaly_ids)} giao dịch bất thường "
                    f"vượt ngưỡng Z-Score/IsolationForest."
                ),
            )

        return Response({"success": True, "data": report})


class FinancialHealthScoreAPIView(APIView):
    """
    API 29 (Module Ăn Điểm 3): Chấm điểm sức khỏe tài chính (thang 100) & Phân loại rủi ro vỡ ngân sách
    bằng `RandomForestClassifier` nạp qua `MLModelRegistry` (Singleton) + `SavingStrategy` (Strategy Pattern).
    """

    permission_classes = [IsStudentOwner]
    transaction_repo = TransactionRepository()
    wallet_repo = WalletRepository()

    @extend_schema(
        responses={200: FinancialHealthResponseSerializer},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Chấm điểm Sức khỏe Tài chính (0-100) & Dự báo rủi ro vỡ ngân sách (RandomForestClassifier)",
    )
    def get(self, request):
        user = request.user
        total_balance = self.wallet_repo.get_total_balance(user_id=user.id)
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user.id
        )

        classifier = RiskClassifier(
            raw_transactions=expense_records,
            current_balance=total_balance,
            monthly_budget_limit=getattr(user, "monthly_income_limit", 4500000),
        )
        report = classifier.run_inference()
        return Response({"success": True, "data": report})


class SpendingStructureAPIView(APIView):
    """
    API 30: Thống kê tỷ trọng chi tiêu Thiết yếu (Essential) vs Không thiết yếu (Non-essential)
    và phân rã theo từng danh mục bằng Pandas.
    """

    permission_classes = [IsStudentOwner]
    transaction_repo = TransactionRepository()
    wallet_repo = WalletRepository()

    @extend_schema(
        responses={200: OpenApiTypes.OBJECT},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Thống kê tỷ trọng chi tiêu Essential vs Non-essential theo Danh mục (Pandas)",
    )
    def get(self, request):
        user = request.user
        total_balance = self.wallet_repo.get_total_balance(user_id=user.id)
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user.id
        )
        classifier = RiskClassifier(
            raw_transactions=expense_records,
            current_balance=total_balance,
            monthly_budget_limit=getattr(user, "monthly_income_limit", 4500000),
        )
        health_report = classifier.run_inference()
        return Response(
            {
                "success": True,
                "data": health_report["spending_structure"],
            }
        )


class ReportExportAPIView(APIView):
    """
    API 31: Xuất báo cáo tổng hợp chi tiêu tháng ra file `.csv` hoặc `.xlsx`
    áp dụng Strategy Pattern (`CSVReportExporter` / `ExcelReportExporter`).
    """

    permission_classes = [IsStudentOwner]
    transaction_repo = TransactionRepository()
    wallet_repo = WalletRepository()

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="export_format",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Định dạng xuất báo cáo: `csv` (mặc định) hoặc `xlsx`",
            )
        ],
        responses={200: OpenApiTypes.BINARY},
        tags=["5. Analytics & ML Serving Engine"],
        summary="Xuất báo cáo chi tiêu ra file CSV hoặc Excel (Strategy Pattern)",
    )
    def get(self, request):
        export_format = request.query_params.get("export_format", "csv").lower()
        user_id = request.user.id
        expense_records = self.transaction_repo.get_expense_records_for_analytics(
            user_id=user_id
        )
        total_balance = self.wallet_repo.get_total_balance(user_id=user_id)

        exporter_cls = (
            ExcelReportExporter if export_format in ("xlsx", "excel") else CSVReportExporter
        )
        exporter = exporter_cls(
            transactions=expense_records,
            summary={"current_balance": float(total_balance)},
        )
        file_bytes = exporter.generate()

        filename = f"uit_student_expense_report.{exporter.file_extension}"
        response = HttpResponse(file_bytes, content_type=exporter.content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
