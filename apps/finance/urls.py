"""
URL Routing for `apps.finance` mounted under `/api/v1/` (30+ RESTful API operations across 5 Modules).
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.finance.views import (
    AdminUserManagementAPIView,
    AdminUserToggleStatusAPIView,
    AnomalyDetectionAPIView,
    BudgetAlertListAPIView,
    BudgetAlertMarkReadAPIView,
    BudgetClonePreviousMonthAPIView,
    BudgetDetailAPIView,
    BudgetListCreateAPIView,
    BurnRateForecastAPIView,
    CategoryDetailAPIView,
    CategoryListCreateAPIView,
    FinancialHealthScoreAPIView,
    RecurringBillDetailAPIView,
    RecurringBillListCreateAPIView,
    RecurringBillPayAPIView,
    ReportExportAPIView,
    SpendingStructureAPIView,
    StudentRegistrationAPIView,
    TransactionDetailAPIView,
    TransactionListCreateAPIView,
    UserAllowanceUpdateAPIView,
    UserProfileAPIView,
    WalletDetailAPIView,
    WalletListCreateAPIView,
    WalletTransferAPIView,
)

urlpatterns = [
    # =========================================================================
    # MODULE 1: auth_iam (Authentication, User Profile, Allowance & Admin - 6+ APIs)
    # =========================================================================
    path("auth/register/", StudentRegistrationAPIView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("users/me/", UserProfileAPIView.as_view(), name="users-me"),
    path("auth/me/", UserProfileAPIView.as_view(), name="auth-me"),
    path(
        "users/me/allowance/",
        UserAllowanceUpdateAPIView.as_view(),
        name="users-me-allowance",
    ),
    path("admin/users/", AdminUserManagementAPIView.as_view(), name="admin-users"),
    path(
        "admin/users/<uuid:user_id>/toggle-status/",
        AdminUserToggleStatusAPIView.as_view(),
        name="admin-users-toggle-status",
    ),
    # =========================================================================
    # MODULE 2: wallet_mgmt (Wallets CRUD & Atomic Internal Transfers - 6 APIs)
    # =========================================================================
    path("wallets/", WalletListCreateAPIView.as_view(), name="wallet-list-create"),
    path("wallets/transfer/", WalletTransferAPIView.as_view(), name="wallet-transfer"),
    path(
        "wallets/<uuid:wallet_id>/",
        WalletDetailAPIView.as_view(),
        name="wallet-detail",
    ),
    # =========================================================================
    # MODULE 3: transaction (Categories, Transactions & Recurring Bills KTX - 9+ APIs)
    # =========================================================================
    path(
        "categories/",
        CategoryListCreateAPIView.as_view(),
        name="category-list-create",
    ),
    path(
        "categories/<uuid:category_id>/",
        CategoryDetailAPIView.as_view(),
        name="category-detail",
    ),
    path(
        "transactions/",
        TransactionListCreateAPIView.as_view(),
        name="transaction-list-create",
    ),
    path(
        "transactions/<uuid:transaction_id>/",
        TransactionDetailAPIView.as_view(),
        name="transaction-detail",
    ),
    path(
        "recurring-bills/",
        RecurringBillListCreateAPIView.as_view(),
        name="recurring-bill-list-create",
    ),
    path(
        "recurring-bills/<uuid:bill_id>/",
        RecurringBillDetailAPIView.as_view(),
        name="recurring-bill-detail",
    ),
    path(
        "recurring-bills/<uuid:bill_id>/pay/",
        RecurringBillPayAPIView.as_view(),
        name="recurring-bill-pay",
    ),
    # =========================================================================
    # MODULE 4: budget_alert (Monthly Budgets, Clone & Alert Logs - 5+ APIs)
    # =========================================================================
    path("budgets/", BudgetListCreateAPIView.as_view(), name="budget-list-create"),
    path(
        "budgets/clone-previous/",
        BudgetClonePreviousMonthAPIView.as_view(),
        name="budget-clone-previous",
    ),
    path(
        "budgets/<uuid:budget_id>/",
        BudgetDetailAPIView.as_view(),
        name="budget-detail",
    ),
    path("alerts/", BudgetAlertListAPIView.as_view(), name="alerts-list"),
    path("budgets/alerts/", BudgetAlertListAPIView.as_view(), name="budget-alerts"),
    path(
        "alerts/<uuid:alert_id>/read/",
        BudgetAlertMarkReadAPIView.as_view(),
        name="alerts-mark-read",
    ),
    # =========================================================================
    # MODULE 5: analytics_engine (ML Serving: Burn-Rate, Anomaly, Health Score, Export - 5+ APIs)
    # =========================================================================
    path(
        "analytics/burn-rate-forecast/",
        BurnRateForecastAPIView.as_view(),
        name="analytics-burn-rate-forecast",
    ),
    path(
        "analytics/cashflow-forecast/",
        BurnRateForecastAPIView.as_view(),
        name="analytics-cashflow-forecast",
    ),
    path(
        "analytics/burn-rate/",
        BurnRateForecastAPIView.as_view(),
        name="analytics-burn-rate",
    ),
    path(
        "analytics/detect-anomalies/",
        AnomalyDetectionAPIView.as_view(),
        name="analytics-detect-anomalies",
    ),
    path(
        "analytics/anomalies/",
        AnomalyDetectionAPIView.as_view(),
        name="analytics-anomalies",
    ),
    path(
        "analytics/financial-health/",
        FinancialHealthScoreAPIView.as_view(),
        name="analytics-financial-health",
    ),
    path(
        "analytics/spending-structure/",
        SpendingStructureAPIView.as_view(),
        name="analytics-spending-structure",
    ),
    path(
        "analytics/export/",
        ReportExportAPIView.as_view(),
        name="analytics-export",
    ),
]
