"""
Management command `python manage.py seed_data`:
Creates:
- 2 UserAccounts (1 Admin `admin@uit.edu.vn`, 1 Student `22520001@gm.uit.edu.vn`)
- 3 Wallets (Tiền mặt, Ví MoMo, Ngân hàng Vietcombank)
- 6 ExpenseCategories (5 EXPENSE + 1 INCOME)
- 4 RecurringBills KTX (Tiền phòng KTX Khu B, Điện nước KTX, Gói cước 4G Viettel, Vé tháng Xe buýt/Metro)
- MonthlyBudgets (tháng trước & tháng hiện tại)
- 200 realistic student transactions over 60 days (including anomalies)
- Serialized ML models in `artifacts/*.joblib` via `MLModelRegistry`
"""
import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.finance.engines import MLModelRegistry
from apps.finance.models import (
    BudgetAlertLog,
    ExpenseCategory,
    ExpenseTransaction,
    MonthlyBudget,
    RecurringBill,
    UserAccount,
    Wallet,
)


class Command(BaseCommand):
    help = "Seed 200 giao dịch mẫu của sinh viên UIT trong 60 ngày + 4 hóa đơn KTX + ML Artifacts."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.WARNING("Đang khởi tạo dữ liệu mẫu (Seed Data 200 giao dịch) cho IE221...")
        )

        # 0. Warm-up MLModelRegistry Singleton để lưu 3 file .joblib vào artifacts/
        registry = MLModelRegistry.get_instance()
        registry.get_model("burn_rate_huber")
        registry.get_model("anomaly_iforest")
        registry.get_model("risk_rf_classifier")

        # 1. Tạo 2 tài khoản: 1 Admin & 1 Student UIT
        admin_user, _ = UserAccount.objects.get_or_create(
            email="admin@uit.edu.vn",
            defaults={
                "full_name": "Giảng viên / Quản trị viên IE221",
                "role": UserAccount.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("Admin@123")
        admin_user.save()

        student_user, _ = UserAccount.objects.get_or_create(
            email="22520001@gm.uit.edu.vn",
            defaults={
                "student_code": "22520001",
                "full_name": "Trương Huy Hoàng",
                "role": UserAccount.Role.STUDENT,
                "monthly_income_limit": Decimal("4500000.00"),
                "dorm_area": "KTX Khu B - ĐHQG TP.HCM",
            },
        )
        student_user.set_password("Student@123")
        student_user.save()

        # Xóa dữ liệu cũ của student_user nếu chạy lại seed_data
        ExpenseTransaction.all_objects.filter(user=student_user).delete()
        BudgetAlertLog.all_objects.filter(user=student_user).delete()
        MonthlyBudget.all_objects.filter(user=student_user).delete()
        RecurringBill.all_objects.filter(user=student_user).delete()
        Wallet.all_objects.filter(user=student_user).delete()

        # 2. Tạo 3 Ví tiền cho sinh viên
        wallet_cash = Wallet.objects.create(
            user=student_user,
            name="Ví Tiền Mặt",
            wallet_type=Wallet.WalletType.CASH,
            balance=Decimal("1200000.00"),
        )
        wallet_momo = Wallet.objects.create(
            user=student_user,
            name="Ví Điện Tử MoMo",
            wallet_type=Wallet.WalletType.MOMO,
            balance=Decimal("2300000.00"),
        )
        wallet_bank = Wallet.objects.create(
            user=student_user,
            name="Ngân Hàng Vietcombank",
            wallet_type=Wallet.WalletType.BANK,
            balance=Decimal("4500000.00"),
        )
        wallets = [wallet_cash, wallet_momo, wallet_bank]

        # 3. Tạo 6 Danh mục Thu / Chi chuẩn sinh viên
        cat_food, _ = ExpenseCategory.objects.get_or_create(
            name="Ăn uống Làng Đại học",
            category_type=ExpenseCategory.CategoryType.EXPENSE,
            defaults={"is_essential": True, "description": "Cơm trưa căn tin UIT, bún bò, trà đá"},
        )
        cat_transport, _ = ExpenseCategory.objects.get_or_create(
            name="Di chuyển & Xe buýt",
            category_type=ExpenseCategory.CategoryType.EXPENSE,
            defaults={"is_essential": True, "description": "Vé xe buýt số 8, tuyến Metro, xăng xe"},
        )
        cat_dorm, _ = ExpenseCategory.objects.get_or_create(
            name="Tiền phòng KTX & Điện nước",
            category_type=ExpenseCategory.CategoryType.EXPENSE,
            defaults={"is_essential": True, "description": "Phí nội trú KTX Khu B ĐHQG"},
        )
        cat_study, _ = ExpenseCategory.objects.get_or_create(
            name="Học phí & Giáo trình",
            category_type=ExpenseCategory.CategoryType.EXPENSE,
            defaults={"is_essential": True, "description": "In tài liệu, mua sách Python, khóa học"},
        )
        cat_entertainment, _ = ExpenseCategory.objects.get_or_create(
            name="Giải trí & Trà sữa",
            category_type=ExpenseCategory.CategoryType.EXPENSE,
            defaults={"is_essential": False, "description": "Xem phim, trà sữa, tụ tập bạn bè"},
        )
        cat_allowance, _ = ExpenseCategory.objects.get_or_create(
            name="Trợ cấp gia đình & Học bổng",
            category_type=ExpenseCategory.CategoryType.INCOME,
            defaults={"is_essential": True, "description": "Tiền gia đình gửi hàng tháng & học bổng UIT"},
        )

        # 4. Tạo 4 Hóa đơn định kỳ KTX (RecurringBill)
        RecurringBill.objects.create(
            user=student_user,
            wallet=wallet_bank,
            category=cat_dorm,
            title="Tiền phòng KTX Khu B ĐHQG",
            amount=Decimal("450000.00"),
            due_day=5,
            auto_deduct=True,
            status=RecurringBill.BillStatus.PENDING,
        )
        RecurringBill.objects.create(
            user=student_user,
            wallet=wallet_momo,
            category=cat_dorm,
            title="Tiền điện nước & Internet KTX",
            amount=Decimal("150000.00"),
            due_day=8,
            auto_deduct=False,
            status=RecurringBill.BillStatus.PENDING,
        )
        RecurringBill.objects.create(
            user=student_user,
            wallet=wallet_momo,
            category=cat_study,
            title="Gói cước 4G Viettel Sinh Viên",
            amount=Decimal("90000.00"),
            due_day=10,
            auto_deduct=True,
            status=RecurringBill.BillStatus.PENDING,
        )
        RecurringBill.objects.create(
            user=student_user,
            wallet=wallet_cash,
            category=cat_transport,
            title="Vé tháng Xe buýt & Metro Suối Tiên",
            amount=Decimal("120000.00"),
            due_day=1,
            auto_deduct=False,
            status=RecurringBill.BillStatus.PAID,
        )

        # 5. Sinh 200 giao dịch trong 60 ngày gần nhất
        rng = random.Random(221)
        now = timezone.now()
        expense_templates = [
            (cat_food, (25000, 55000), ["Cơm sườn căn tin UIT", "Bún bò Làng ĐH", "Bánh mì sáng", "Cơm tấm đêm"]),
            (cat_transport, (7000, 50000), ["Đổ xăng xe máy", "Gửi xe nhà xe UIT", "Vé xe buýt"]),
            (cat_study, (15000, 120000), ["Photocopy đề cương IE221", "Mua vở ghi chép", "Sách lập trình Python"]),
            (cat_entertainment, (35000, 95000), ["Trà sữa Phúc Long", "Cà phê chạy deadline đồ án", "Xem phim cuối tuần"]),
        ]

        created_txs = []
        current_month_spent = Decimal("0.00")

        for i in range(200):
            days_ago = int((i / 200.0) * 60)
            tx_time = now - timedelta(
                days=days_ago, hours=rng.randint(7, 21), minutes=rng.randint(0, 59)
            )

            # 5 giao dịch bất thường (Anomaly) để demo AnomalyDetector
            if i in (12, 48, 95, 130, 175):
                category = cat_entertainment
                amount = Decimal(str(rng.choice([850000, 1200000, 950000, 1500000, 1100000])))
                note = "Chi tiêu đột biến: Mua bàn phím cơ / Liên hoan nhóm đồ án"
                is_anomaly = True
                anomaly_score = 4.25
            else:
                category, (low, high), notes = rng.choice(expense_templates)
                raw_amt = rng.randrange(low, high + 1, 1000)
                amount = Decimal(str(raw_amt))
                note = rng.choice(notes)
                is_anomaly = False
                anomaly_score = 0.35

            tx = ExpenseTransaction(
                user=student_user,
                wallet=rng.choice(wallets),
                category=category,
                transaction_type=ExpenseTransaction.TransactionType.EXPENSE,
                amount=amount,
                transaction_date=tx_time,
                note=note,
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
            )
            created_txs.append(tx)

            if tx_time.month == now.month and tx_time.year == now.year:
                current_month_spent += amount

        ExpenseTransaction.objects.bulk_create(created_txs)

        # 6. Tạo Ngân sách tháng trước (để test API clone-previous) và tháng hiện tại
        prev_month = 12 if now.month == 1 else now.month - 1
        prev_year = now.year - 1 if now.month == 1 else now.year
        MonthlyBudget.objects.create(
            user=student_user,
            category=cat_food,
            month=prev_month,
            year=prev_year,
            allocated_amount=Decimal("2000000.00"),
            spent_amount=Decimal("1850000.00"),
            alert_threshold_pct=80,
        )

        monthly_budget = MonthlyBudget.objects.create(
            user=student_user,
            category=None,
            month=now.month,
            year=now.year,
            allocated_amount=Decimal("4500000.00"),
            spent_amount=current_month_spent,
            alert_threshold_pct=80,
        )

        BudgetAlertLog.objects.create(
            user=student_user,
            budget=monthly_budget,
            alert_type=BudgetAlertLog.AlertType.ANOMALY,
            message="[DEMO ANOMALY] Phát hiện 5 giao dịch chi tiêu đột biến vượt ngưỡng 2.5-Sigma & IsolationForest trong 60 ngày qua.",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Hoàn tất seed dữ liệu! Đã tạo 2 tài khoản, 3 ví, 6 danh mục, 4 hóa đơn KTX, "
                f"200 giao dịch mẫu cho sinh viên {student_user.email} (Mật khẩu: Student@123)."
            )
        )
