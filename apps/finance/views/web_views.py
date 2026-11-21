"""
Hybrid MVT Presentation Layer (`web_views.py`):
Renders `templates/finance/dashboard.html` with Chart.js visualizations
for Student Expense Burn-Rate & Anomaly Analytics.
"""
from django.views.generic import TemplateView
from apps.finance.engines import AnomalyDetectionEngine, BurnRateAnalyzer, RiskClassifier
from apps.finance.models import UserAccount
from apps.finance.repositories import TransactionRepository, WalletRepository


class StudentDashboardTemplateView(TemplateView):
    """
    [V - VIEW / T - TEMPLATE HTML] Render trang Web Dashboard trực quan (Chart.js)
    minh họa chuẩn mô hình Hybrid MVT của Django cho buổi bảo vệ Đồ án IE221.
    Hỗ trợ chọn sinh viên qua query `?student=24520001` (mặc định ưu tiên 24520001@gm.uit.edu.vn).
    """

    template_name = "finance/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requested_code = self.request.GET.get("student", "").strip()
        student = None
        if requested_code:
            student = (
                UserAccount.objects.filter(student_code=requested_code).first()
                or UserAccount.objects.filter(email=requested_code).first()
            )
        if not student:
            student = (
                UserAccount.objects.filter(email="24520001@gm.uit.edu.vn").first()
                or UserAccount.objects.filter(role=UserAccount.Role.STUDENT)
                .order_by("email")
                .first()
                or UserAccount.objects.order_by("email").first()
            )
        if not student:
            context["has_data"] = False
            return context

        wallet_repo = WalletRepository()
        tx_repo = TransactionRepository()
        total_balance = wallet_repo.get_total_balance(user_id=student.id)
        expense_records = tx_repo.get_expense_records_for_analytics(user_id=student.id)

        burn_report = BurnRateAnalyzer(
            raw_transactions=expense_records, current_balance=total_balance
        ).run_inference()
        anomaly_report = AnomalyDetectionEngine(
            raw_transactions=expense_records
        ).run_inference()
        health_report = RiskClassifier(
            raw_transactions=expense_records,
            current_balance=total_balance,
            monthly_budget_limit=student.monthly_income_limit,
        ).run_inference()

        context.update(
            {
                "has_data": True,
                "student": student,
                "wallets": wallet_repo.get_user_wallets(user_id=student.id),
                "burn_report": burn_report,
                "anomaly_report": anomaly_report,
                "health_report": health_report,
            }
        )
        return context
