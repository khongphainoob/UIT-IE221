"""
Django Admin registration for all 7 normalized (3NF) models in `apps.finance`.
"""
from django.contrib import admin
from apps.finance.models import (
    BudgetAlertLog,
    ExpenseCategory,
    ExpenseTransaction,
    MonthlyBudget,
    RecurringBill,
    UserAccount,
    Wallet,
)


@admin.register(UserAccount)
class UserAccountAdmin(admin.ModelAdmin):
    list_display = ("email", "student_code", "full_name", "role", "is_active", "created_at")
    search_fields = ("email", "student_code", "full_name")
    list_filter = ("role", "is_active")


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "wallet_type", "balance", "currency", "created_at")
    list_filter = ("wallet_type", "currency")
    search_fields = ("name", "user__email")


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category_type", "is_essential", "user", "created_at")
    list_filter = ("category_type", "is_essential")
    search_fields = ("name",)


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "category", "month", "year", "allocated_amount", "spent_amount")
    list_filter = ("year", "month")
    search_fields = ("user__email",)


@admin.register(ExpenseTransaction)
class ExpenseTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_type",
        "amount",
        "wallet",
        "category",
        "user",
        "is_anomaly",
        "anomaly_score",
        "transaction_date",
    )
    list_filter = ("transaction_type", "is_anomaly")
    search_fields = ("note", "user__email")


@admin.register(RecurringBill)
class RecurringBillAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "amount", "due_day", "frequency", "is_active")
    list_filter = ("frequency", "is_active")


@admin.register(BudgetAlertLog)
class BudgetAlertLogAdmin(admin.ModelAdmin):
    list_display = ("alert_type", "user", "is_read", "created_at")
    list_filter = ("alert_type", "is_read")

