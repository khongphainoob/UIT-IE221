"""Export all Presentation/Controller APIViews and Hybrid MVT TemplateViews."""
from apps.finance.views.analytics_views import (
    AnomalyDetectionAPIView,
    BurnRateForecastAPIView,
    FinancialHealthScoreAPIView,
    ReportExportAPIView,
    SpendingStructureAPIView,
)
from apps.finance.views.auth_views import (
    AdminUserManagementAPIView,
    AdminUserToggleStatusAPIView,
    StudentRegistrationAPIView,
    UserAllowanceUpdateAPIView,
    UserProfileAPIView,
)
from apps.finance.views.budget_views import (
    BudgetAlertListAPIView,
    BudgetAlertMarkReadAPIView,
    BudgetClonePreviousMonthAPIView,
    BudgetDetailAPIView,
    BudgetListCreateAPIView,
    RecurringBillDetailAPIView,
    RecurringBillListCreateAPIView,
)
from apps.finance.views.transaction_views import (
    CategoryDetailAPIView,
    CategoryListCreateAPIView,
    RecurringBillPayAPIView,
    TransactionDetailAPIView,
    TransactionListCreateAPIView,
)
from apps.finance.views.wallet_views import (
    WalletDetailAPIView,
    WalletListCreateAPIView,
    WalletTransferAPIView,
)
from apps.finance.views.web_views import StudentDashboardTemplateView

__all__ = [
    "StudentRegistrationAPIView",
    "UserProfileAPIView",
    "UserAllowanceUpdateAPIView",
    "AdminUserManagementAPIView",
    "AdminUserToggleStatusAPIView",
    "WalletListCreateAPIView",
    "WalletDetailAPIView",
    "WalletTransferAPIView",
    "CategoryListCreateAPIView",
    "CategoryDetailAPIView",
    "TransactionListCreateAPIView",
    "TransactionDetailAPIView",
    "RecurringBillListCreateAPIView",
    "RecurringBillDetailAPIView",
    "RecurringBillPayAPIView",
    "BudgetListCreateAPIView",
    "BudgetDetailAPIView",
    "BudgetClonePreviousMonthAPIView",
    "BudgetAlertListAPIView",
    "BudgetAlertMarkReadAPIView",
    "BurnRateForecastAPIView",
    "AnomalyDetectionAPIView",
    "FinancialHealthScoreAPIView",
    "SpendingStructureAPIView",
    "ReportExportAPIView",
    "StudentDashboardTemplateView",
]
