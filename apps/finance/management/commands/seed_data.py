"""
Management command `python manage.py seed_data`:
Kết hợp cả 2 hướng:
- Hướng A: Đa dạng hóa dữ liệu thực tế cho Khóa 2024 UIT (`24520001` .. `24520006` + `admin@uit.edu.vn`)
  gồm 6 khoa (CNPM, KHMT, KTMT, HTTT, MMT&TT, KTTT), 3 hồ sơ rủi ro (`SAFE`, `WARNING`, `HIGH_RISK_BROKE`),
  12 danh mục Thu/Chi, 18 ví tiền, 16 hóa đơn định kỳ KTX và bộ từ điển 85+ giao dịch thực tế tại Làng Đại học Thủ Đức.
- Hướng B: Xuất & nạp từ bộ Dataset CSV chuẩn hóa `data/uit_student_expenses_dataset.csv` (~1.025 giao dịch
  trong 60 ngày cho 6 sinh viên, trong đó sinh viên chính `24520001@gm.uit.edu.vn` có 200 giao dịch mặc định),
  kết hợp hiệu chỉnh tỷ trọng từ Kaggle Student Spending Habits & Daily Household Transactions quy đổi sang VNĐ.
- Hỗ trợ chạy lặp an toàn (idempotent mặc định), `--reset`, `--days`, `--count`, `--seed`, `--csv-path`.
"""
import csv
import os
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.finance.engines import AnomalyDetectionEngine, BurnRateAnalyzer, MLModelRegistry
from apps.finance.models import (
    BudgetAlertLog,
    ExpenseCategory,
    ExpenseTransaction,
    MonthlyBudget,
    RecurringBill,
    UserAccount,
    Wallet,
)

DEFAULT_CSV_PATH = Path(settings.BASE_DIR) / "data" / "uit_student_expenses_dataset.csv"

# =============================================================================
# 1. DANH SÁCH 6 SINH VIÊN KHÓA 2024 UIT (2452xxxx) — 6 KHOA & 3 HỒ SƠ TÀI CHÍNH
# =============================================================================
STUDENT_COHORT_2452: List[Dict[str, Any]] = [
    {
        "student_code": "24520001",
        "email": "24520001@gm.uit.edu.vn",
        "full_name": "Trương Huy Hoàng",
        "faculty": "Công nghệ Phần mềm (SE)",
        "dorm_area": "KTX Khu B - ĐHQG TP.HCM (Tòa BA4)",
        "monthly_income_limit": Decimal("4500000.00"),
        "persona": "BALANCED_ANOMALY_DEMO",
        "is_primary": True,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt Cá Nhân", Decimal("650000.00")),
            Wallet.WalletType.MOMO: ("Ví Điện Tử MoMo", Decimal("1150000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng Vietcombank", Decimal("2200000.00")),
        },
        "category_weights": [0.36, 0.12, 0.05, 0.08, 0.04, 0.04, 0.15, 0.09, 0.07],
        "spend_scale": 1.0,
    },
    {
        "student_code": "24520002",
        "email": "24520002@gm.uit.edu.vn",
        "full_name": "Nguyễn Minh Anh",
        "faculty": "Khoa học Máy tính (CS)",
        "dorm_area": "KTX Khu A - ĐHQG TP.HCM (Tòa A12)",
        "monthly_income_limit": Decimal("5000000.00"),
        "persona": "SAFE_DISCIPLINED",
        "is_primary": False,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt", Decimal("850000.00")),
            Wallet.WalletType.MOMO: ("Ví MoMo Sinh Viên", Decimal("1650000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng BIDV ĐHQG", Decimal("3400000.00")),
        },
        "category_weights": [0.44, 0.15, 0.06, 0.12, 0.05, 0.05, 0.07, 0.03, 0.03],
        "spend_scale": 0.82,
    },
    {
        "student_code": "24520003",
        "email": "24520003@gm.uit.edu.vn",
        "full_name": "Lê Hoàng Nam",
        "faculty": "Kỹ thuật Máy tính (CE)",
        "dorm_area": "KTX Khu B - ĐHQG TP.HCM (Tòa BB2)",
        "monthly_income_limit": Decimal("4200000.00"),
        "persona": "WARNING_TECH_SPENDER",
        "is_primary": False,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt", Decimal("420000.00")),
            Wallet.WalletType.MOMO: ("Ví Điện Tử MoMo", Decimal("780000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng Techcombank", Decimal("1450000.00")),
        },
        "category_weights": [0.35, 0.12, 0.05, 0.11, 0.05, 0.03, 0.12, 0.12, 0.05],
        "spend_scale": 1.08,
    },
    {
        "student_code": "24520004",
        "email": "24520004@gm.uit.edu.vn",
        "full_name": "Phạm Ngọc Hân",
        "faculty": "Hệ thống Thông tin (IS)",
        "dorm_area": "Nhà trọ Làng Đại học Thủ Đức",
        "monthly_income_limit": Decimal("5200000.00"),
        "persona": "HIGH_RISK_BROKE",
        "is_primary": False,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt", Decimal("180000.00")),
            Wallet.WalletType.MOMO: ("Ví MoMo / ShopeePay", Decimal("310000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng TPBank", Decimal("490000.00")),
        },
        "category_weights": [0.28, 0.10, 0.06, 0.05, 0.04, 0.03, 0.22, 0.15, 0.07],
        "spend_scale": 1.28,
    },
    {
        "student_code": "24520005",
        "email": "24520005@gm.uit.edu.vn",
        "full_name": "Võ Quốc Bảo",
        "faculty": "Mạng Máy tính & Truyền thông (NC)",
        "dorm_area": "KTX Khu B - ĐHQG TP.HCM (Tòa BC1)",
        "monthly_income_limit": Decimal("4400000.00"),
        "persona": "WARNING_FOOD_SOCIAL",
        "is_primary": False,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt", Decimal("510000.00")),
            Wallet.WalletType.MOMO: ("Ví Điện Tử MoMo", Decimal("890000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng VietinBank", Decimal("1600000.00")),
        },
        "category_weights": [0.38, 0.13, 0.05, 0.08, 0.05, 0.04, 0.14, 0.06, 0.07],
        "spend_scale": 1.05,
    },
    {
        "student_code": "24520006",
        "email": "24520006@gm.uit.edu.vn",
        "full_name": "Đặng Thùy Trang",
        "faculty": "Khoa học & Kỹ thuật Thông tin (DS)",
        "dorm_area": "KTX Khu A - ĐHQG TP.HCM (Tòa A08)",
        "monthly_income_limit": Decimal("4800000.00"),
        "persona": "SAFE_SCHOLARSHIP",
        "is_primary": False,
        "wallets": {
            Wallet.WalletType.CASH: ("Ví Tiền Mặt", Decimal("750000.00")),
            Wallet.WalletType.MOMO: ("Ví Điện Tử MoMo", Decimal("1550000.00")),
            Wallet.WalletType.BANK: ("Ngân Hàng Vietcombank", Decimal("3100000.00")),
        },
        "category_weights": [0.42, 0.14, 0.06, 0.13, 0.05, 0.05, 0.08, 0.04, 0.03],
        "spend_scale": 0.85,
    },
]

# =============================================================================
# 2. HỆ THỐNG 12 DANH MỤC THU / CHI CHUẨN SINH VIÊN ĐẠI HỌC (9 EXPENSE + 3 INCOME)
# =============================================================================
SYSTEM_CATEGORIES_SPEC: List[Tuple[str, str, bool, str]] = [
    (
        "Ăn uống Làng Đại học",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "Cơm trưa căn tin B1 UIT, bún bò KTX Khu B, bánh mì sáng, cơm tấm đêm chợ Nhân Văn",
    ),
    (
        "Di chuyển & Xe buýt",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "Vé xe buýt số 8/19/53, tàu Metro Bến Thành - Suối Tiên, gửi xe UIT, đổ xăng RON 95",
    ),
    (
        "Tiền phòng KTX & Điện nước",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "Phí nội trú KTX Khu A/B ĐHQG, tiền điện nước vượt định mức, nước uống bình 20L",
    ),
    (
        "Học phí & Giáo trình",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "In đề cương IE221, mua sách lập trình Python/AI, dụng cụ học tập, khóa học trực tuyến",
    ),
    (
        "Viễn thông & Internet 4G",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "Gói cước 4G Viettel/MobiFone sinh viên, nạp tiền điện thoại, chia tiền Wi-Fi phòng",
    ),
    (
        "Y tế, Thuốc men & Thể thao",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        "Thuốc cảm cúm Long Châu, vitamin mùa thi, thuê sân cầu lông/bóng đá Nhà văn hóa SV",
    ),
    (
        "Giải trí & Trà sữa",
        ExpenseCategory.CategoryType.EXPENSE,
        False,
        "Trà sữa Phúc Long/Katinat, cà phê chạy deadline, xem phim CGV Vincom Thủ Đức",
    ),
    (
        "Mua sắm & Phụ kiện Công nghệ",
        ExpenseCategory.CategoryType.EXPENSE,
        False,
        "Đơn hàng Shopee/Lazada, chuột/cáp sạc/USB, quần áo sinh viên, đồ dùng cá nhân",
    ),
    (
        "Giao lưu, CLB & Sự kiện UIT",
        ExpenseCategory.CategoryType.EXPENSE,
        False,
        "Quỹ CLB học thuật/văn nghệ, liên hoan nhóm đồ án, quà sinh nhật bạn cùng phòng KTX",
    ),
    (
        "Trợ cấp gia đình & Học bổng",
        ExpenseCategory.CategoryType.INCOME,
        True,
        "Tiền gia đình chu cấp đầu tháng và học bổng khuyến khích học tập UIT",
    ),
    (
        "Thu nhập làm thêm & Gia sư",
        ExpenseCategory.CategoryType.INCOME,
        False,
        "Gia sư Toán/Tin học, cộng tác viên lab AI, part-time lập trình web/kiểm thử",
    ),
    (
        "Thưởng cuộc thi & Hỗ trợ ĐHQG",
        ExpenseCategory.CategoryType.INCOME,
        False,
        "Giải thưởng Hackathon/CTF UIT, phụ cấp hỗ trợ sinh viên nghiên cứu khoa học",
    ),
]

# =============================================================================
# 3. BỘ TỪ ĐIỂN 85+ MẪU GIAO DỊCH THỰC TẾ TẠI UIT & LÀNG ĐẠI HỌC THỦ ĐỨC
# =============================================================================
EXPENSE_CATALOG: Dict[str, Tuple[Tuple[int, int], List[str], List[str]]] = {
    "Ăn uống Làng Đại học": (
        (22000, 58000),
        [Wallet.WalletType.CASH, Wallet.WalletType.MOMO],
        [
            "Cơm sườn bì chả căn tin B1 UIT",
            "Bún bò Huế cổng sau KTX Khu B",
            "Bánh mì ốp la 2 trứng ngã tư Quốc phòng",
            "Cơm tấm đêm chợ Nhân Văn Làng ĐH",
            "Hủ tiếu Nam Vang gõ KTX Khu A",
            "Phở bò tái viên đường số 6 Làng ĐH",
            "Xôi gà xé buổi sáng trước ca 1 IE221",
            "Bánh canh cá lóc cổng KTX Khu B",
            "Cơm gà xối mỡ quán sinh viên ĐHQG",
            "Mì cay Hàn Quốc cấp độ 2 đối diện Thư viện",
            "Bún thịt nướng chả giò căn tin UIT",
            "Cháo sườn nóng buổi tối chạy deadline",
            "Sữa tươi tiệt trùng & sandwich FamilyMart KTX",
            "Cơm chay tự chọn Làng Đại học",
            "Bún đậu mắm tôm mẹt nhỏ ăn trưa sau giờ lab",
        ],
    ),
    "Di chuyển & Xe buýt": (
        (7000, 50000),
        [Wallet.WalletType.CASH, Wallet.WalletType.MOMO],
        [
            "Vé xe buýt số 8 (ĐHQG - Bến xe Quận 8)",
            "Vé xe buýt số 19 (ĐHQG - Bến Thành)",
            "Vé xe buýt số 53 (Lê Hồng Phong - ĐHQG)",
            "Vé tàu Metro tuyến số 1 (Suối Tiên - Thảo Điền)",
            "Đổ xăng RON 95-III trạm xăng Xa lộ Hà Nội",
            "Gửi xe máy thẻ tháng/ngày nhà xe sinh viên UIT",
            "GrabBike từ KTX Khu B qua giảng đường C UIT",
            "BeBike từ Bến xe Miền Đông Mới về KTX Khu B",
            "Bơm lốp & vá vỏ xe máy tiệm sửa xe Làng ĐH",
            "Thay dầu nhớt định kỳ xe máy sinh viên",
        ],
    ),
    "Tiền phòng KTX & Điện nước": (
        (25000, 130000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.BANK],
        [
            "Đổi bình nước tinh khiết Lavie 20L phòng KTX",
            "Tiền giặt sấy tự động cửa hàng giặt KTX Khu B",
            "Chia tiền điện nước vượt định mức phòng 8 người",
            "Mua bột giặt, nước lau sàn & túi rác sinh hoạt phòng",
            "Phí gửi xe đạp/xe máy nội khu KTX Khu B",
            "Mua bóng đèn LED học bàn & ổ cắm điện nối dài",
        ],
    ),
    "Học phí & Giáo trình": (
        (15000, 115000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.BANK],
        [
            "Photocopy đề cương & slide bài giảng IE221",
            "In màu báo cáo đồ án & đóng bìa kiếng tiệm in ĐHQG",
            "Mua giáo trình Kỹ thuật lập trình Python & OOP",
            "Mua sổ tay ghi chú Cornell & bút highlight",
            "Mua tài liệu luyện đề TOEIC Reading & Listening",
            "Đóng lệ phí thi thử chuẩn đầu ra ngoại ngữ ĐHQG",
            "Mua gói Google Colab / GitHub Copilot Student bổ trợ",
            "In poster trình bày seminar môn chuyên ngành UIT",
        ],
    ),
    "Viễn thông & Internet 4G": (
        (20000, 95000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.BANK],
        [
            "Gia hạn gói cước 4G Viettel ST90K (1GB/ngày)",
            "Nạp thẻ điện thoại MobiFone khuyến mãi 20%",
            "Mua gói data 5G tốc độ cao học trực tuyến",
            "Đóng quỹ chia cước Internet cáp quang phòng trọ",
            "Gia hạn dung lượng Google One 100GB lưu đồ án",
        ],
    ),
    "Y tế, Thuốc men & Thể thao": (
        (20000, 90000),
        [Wallet.WalletType.CASH, Wallet.WalletType.MOMO],
        [
            "Mua thuốc cảm cúm, sủi Vitamin C nhà thuốc Long Châu",
            "Thuốc nhỏ mắt V.Rohto chống mỏi mắt khi code đêm",
            "Chia tiền thuê sân cầu lông Nhà văn hóa Sinh viên",
            "Tiền sân bóng đá cỏ nhân tạo giao hữu khoa CNPM",
            "Vé bơi buổi chiều hồ bơi Trung tâm TDTT ĐHQG",
            "Mua khẩu trang y tế & nước rửa tay sát khuẩn",
        ],
    ),
    "Giải trí & Trà sữa": (
        (28000, 88000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.CASH],
        [
            "Trà sữa Phúc Long size M ít đường sau giờ thi",
            "Cà phê muối chạy deadline đồ án lúc 10h tối",
            "Trà đào cam sả Highlands Coffee cổng ĐHQG",
            "Vé xem phim CGV Vincom Thủ Đức suất sinh viên",
            "Bánh tráng nướng & cá viên chiên hồ đá Làng ĐH",
            "Chè khúc bạch & tàu hũ đá cổng KTX Khu B",
            "Gia hạn gói Spotify Student nghe nhạc lúc code",
            "Trà sữa Ngô Gia hồng trà kem cheese",
            "Cà phê đen đá quán võng ôn bài buổi trưa",
            "Ăn vặt bánh tráng trộn cùng nhóm làm đồ án",
        ],
    ),
    "Mua sắm & Phụ kiện Công nghệ": (
        (35000, 125000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.BANK],
        [
            "Mua cáp sạc nhanh Type-C Baseus trên Shopee",
            "Mua lót chuột cỡ lớn bàn học KTX",
            "Mua giá đỡ tản nhiệt nhôm cho laptop",
            "Mua USB Kingston 64GB cài Ubuntu & lưu đồ án",
            "Mua áo thun polo sinh viên mặc đi thuyết trình",
            "Mua bình giữ nhiệt inox 750ml mang lên giảng đường",
            "Mua túi chống sốc laptop 15.6 inch",
        ],
    ),
    "Giao lưu, CLB & Sự kiện UIT": (
        (30000, 110000),
        [Wallet.WalletType.MOMO, Wallet.WalletType.CASH],
        [
            "Đóng quỹ sinh hoạt định kỳ CLB Học thuật UIT",
            "Hùn tiền mua bánh kem sinh nhật bạn cùng phòng KTX",
            "Liên hoan nhẹ sau buổi bảo vệ milestone đồ án",
            "Mua vé đêm nhạc hội chào tân sinh viên Khóa 2024",
            "Ủng hộ chiến dịch Xuân Tình Nguyện / Mùa Hè Xanh UIT",
            "Chia tiền nước uống buổi họp nhóm thiết kế UML",
        ],
    ),
}


def _current_month_timestamp(now, target_days_back: int, hour: int, minute: int):
    """Return a timezone-aware timestamp strictly inside `now`'s (year, month) and <= `now`."""
    safe_days_back = min(max(target_days_back, 0), max(now.day - 1, 0))
    candidate = (now - timedelta(days=safe_days_back)).replace(
        hour=hour, minute=minute, second=0, microsecond=0
    )
    if candidate > now:
        earlier = now - timedelta(minutes=min(now.hour * 60 + now.minute, (minute % 45) + 5))
        if earlier.month == now.month and earlier.year == now.year:
            return earlier.replace(second=0, microsecond=0)
        return now.replace(second=0, microsecond=0)
    return candidate


def _round_to_step(amount: Decimal, step: int = 10000) -> Decimal:
    units = (amount / Decimal(step)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return max(units * Decimal(step), Decimal(step))


def _build_student_rows(
    student_spec: Dict[str, Any],
    target_count: int,
    days: int,
    rng: random.Random,
) -> List[Dict[str, Any]]:
    """
    Build deterministic transaction rows for one student (`2452xxxx`),
    combining curated income/transfer/KTX/edge/anomaly records with weighted daily spending.
    """
    scode = student_spec["student_code"]
    semail = student_spec["email"]
    fname = student_spec["full_name"]
    faculty = student_spec["faculty"]
    dorm = student_spec["dorm_area"]
    persona = student_spec["persona"]
    is_primary = student_spec["is_primary"]
    allowance_amt = int(student_spec["monthly_income_limit"])
    scale = float(student_spec["spend_scale"])

    rows: List[Dict[str, Any]] = []

    def add_row(
        day_offset: int,
        hour: int,
        minute: int,
        force_current_month: bool,
        w_type: str,
        cat_name: str,
        cat_type: str,
        is_ess: bool,
        tx_type: str,
        amt: int,
        tag: str,
        note: str,
    ) -> None:
        rows.append(
            {
                "student_code": scode,
                "student_email": semail,
                "full_name": fname,
                "faculty": faculty,
                "dorm_area": dorm,
                "persona": persona,
                "day_offset": max(0, min(day_offset, days - 1)),
                "hour": hour,
                "minute": minute,
                "force_current_month": "1" if force_current_month else "0",
                "wallet_type": w_type,
                "category_name": cat_name,
                "category_type": cat_type,
                "is_essential": "1" if is_ess else "0",
                "transaction_type": tx_type,
                "amount_vnd": amt,
                "scenario_tag": tag,
                "note": note,
            }
        )

    prev_month_anchor = min(days - 2, 34)

    # 1. 2-3 INCOME records (Trợ cấp đầu tháng + Học bổng / Làm thêm)
    add_row(
        prev_month_anchor,
        9,
        10,
        False,
        Wallet.WalletType.BANK,
        "Trợ cấp gia đình & Học bổng",
        ExpenseCategory.CategoryType.INCOME,
        True,
        ExpenseTransaction.TransactionType.INCOME,
        allowance_amt,
        "MONTHLY_ALLOWANCE",
        f"Nhận trợ cấp gia đình đầu tháng trước ({fname})",
    )
    add_row(
        2,
        9,
        25,
        True,
        Wallet.WalletType.BANK,
        "Trợ cấp gia đình & Học bổng",
        ExpenseCategory.CategoryType.INCOME,
        True,
        ExpenseTransaction.TransactionType.INCOME,
        allowance_amt,
        "MONTHLY_ALLOWANCE",
        f"Nhận trợ cấp gia đình đầu tháng hiện tại ({fname})",
    )
    if is_primary or "SAFE" in persona:
        add_row(
            min(18, days - 3),
            15,
            40,
            False,
            Wallet.WalletType.BANK,
            "Thu nhập làm thêm & Gia sư",
            ExpenseCategory.CategoryType.INCOME,
            False,
            ExpenseTransaction.TransactionType.INCOME,
            1200000,
            "PART_TIME_INCOME",
            "Thù lao trợ giảng thực hành Python & chấm bài lab",
        )

    # 2. 2 TRANSFER records (Vietcombank -> MoMo)
    add_row(
        max(prev_month_anchor - 1, 4),
        10,
        5,
        False,
        Wallet.WalletType.BANK,
        "",
        "",
        True,
        ExpenseTransaction.TransactionType.TRANSFER,
        800000,
        "INTERNAL_TRANSFER",
        "Chuyển nội bộ Ngân hàng -> Ví MoMo chi tiêu sinh hoạt (kỳ trước)",
    )
    add_row(
        2,
        10,
        35,
        True,
        Wallet.WalletType.BANK,
        "",
        "",
        True,
        ExpenseTransaction.TransactionType.TRANSFER,
        650000,
        "INTERNAL_TRANSFER",
        "Chuyển nội bộ Ngân hàng -> Ví MoMo chi tiêu sinh hoạt (tháng này)",
    )

    # 3. 2 Fixed KTX Rent spikes (450,000 VND) -> demonstrates HuberRegressor robustness
    add_row(
        max(prev_month_anchor - 2, 5),
        14,
        0,
        False,
        Wallet.WalletType.BANK,
        "Tiền phòng KTX & Điện nước",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        ExpenseTransaction.TransactionType.EXPENSE,
        450000,
        "FIXED_KTX_BILL",
        f"Đóng tiền phòng nội trú {dorm} kỳ trước",
    )
    add_row(
        3,
        14,
        15,
        True,
        Wallet.WalletType.BANK,
        "Tiền phòng KTX & Điện nước",
        ExpenseCategory.CategoryType.EXPENSE,
        True,
        ExpenseTransaction.TransactionType.EXPENSE,
        450000,
        "FIXED_KTX_BILL",
        f"Đóng tiền phòng nội trú {dorm} tháng hiện tại",
    )

    # 4. 3 Lower-tail Edge Cases (3,000 - 10,000 VND)
    edge_specs = [
        (1, True, Wallet.WalletType.CASH, "Di chuyển & Xe buýt", 5000, "Gửi xe máy nhà xe sinh viên UIT (vé lượt)"),
        (2, True, Wallet.WalletType.CASH, "Ăn uống Làng Đại học", 8000, "Trà đá & khăn lạnh căn tin B1 UIT"),
        (min(7, days - 1), False, Wallet.WalletType.CASH, "Học phí & Giáo trình", 10000, "In bổ sung 10 trang bài tập lớn IE221"),
    ]
    for eday, ecurr, ewal, ecat, eamt, enote in edge_specs:
        add_row(
            eday,
            11,
            15,
            ecurr,
            ewal,
            ecat,
            ExpenseCategory.CategoryType.EXPENSE,
            True,
            ExpenseTransaction.TransactionType.EXPENSE,
            eamt,
            "EDGE_MIN_AMOUNT",
            enote,
        )

    # 5. Intentional Anomaly Spikes (5 for primary or HIGH_RISK, 2-3 for WARNING, 1 for SAFE)
    all_anomaly_candidates = [
        (
            1,
            True,
            Wallet.WalletType.BANK,
            "Giải trí & Trà sữa",
            False,
            1450000,
            "[ANOMALY DEMO] Đặt tiệc liên hoan & karaoke sinh nhật nhóm đồ án Làng ĐH",
        ),
        (
            2,
            True,
            Wallet.WalletType.MOMO,
            "Giải trí & Trà sữa",
            False,
            1180000,
            "[ANOMALY DEMO] Mua vé concert âm nhạc cuối tuần & tụ tập bạn bè",
        ),
        (
            min(19, days - 4),
            False,
            Wallet.WalletType.BANK,
            "Mua sắm & Phụ kiện Công nghệ",
            False,
            1650000,
            "[ANOMALY DEMO] Mua bàn phím cơ không dây & chuột ergonomic chạy đồ án",
        ),
        (
            min(33, days - 3),
            False,
            Wallet.WalletType.BANK,
            "Học phí & Giáo trình",
            True,
            1050000,
            "[ANOMALY DEMO] Nâng cấp ổ cứng SSD NVMe 1TB đột xuất cho laptop thực hành",
        ),
        (
            min(47, days - 2),
            False,
            Wallet.WalletType.MOMO,
            "Giao lưu, CLB & Sự kiện UIT",
            False,
            1280000,
            "[ANOMALY DEMO] Chuyến dã ngoại Vũng Tàu 2 ngày 1 đêm cùng CLB UIT",
        ),
    ]
    if is_primary or "HIGH_RISK" in persona:
        chosen_anomalies = all_anomaly_candidates
    elif "WARNING" in persona:
        chosen_anomalies = all_anomaly_candidates[:3]
    else:
        chosen_anomalies = [all_anomaly_candidates[3]]

    for aday, acurr, awal, acat, aess, aamt, anote in chosen_anomalies:
        add_row(
            aday,
            19,
            35,
            acurr,
            awal,
            acat,
            ExpenseCategory.CategoryType.EXPENSE,
            aess,
            ExpenseTransaction.TransactionType.EXPENSE,
            aamt,
            "INTENTIONAL_ANOMALY",
            anote,
        )

    # 6. Fill remaining daily transactions (`target_count - len(rows)`) across `0..days-1`
    expense_cat_names = list(EXPENSE_CATALOG.keys())
    weights = student_spec["category_weights"]
    essential_map = {name: is_ess for name, _, is_ess, _ in SYSTEM_CATEGORIES_SPEC}

    remaining = max(target_count - len(rows), 0)
    for idx in range(remaining):
        chosen_cat = rng.choices(expense_cat_names, weights=weights, k=1)[0]
        (low, high), wal_types, notes = EXPENSE_CATALOG[chosen_cat]

        force_curr = idx < 12
        if force_curr:
            day_off = idx % 5
        else:
            day_off = round((idx / max(remaining - 1, 1)) * (days - 1))

        raw_amt = int(rng.randrange(low, high + 1, 1000) * scale)
        raw_amt = max(5000, (raw_amt // 1000) * 1000)
        # Weekend slight bump
        if (day_off % 7) in (0, 6) and not essential_map[chosen_cat]:
            raw_amt += rng.choice([5000, 10000, 15000])

        add_row(
            day_off,
            rng.randint(7, 21),
            rng.randint(0, 59),
            force_curr,
            rng.choice(wal_types),
            chosen_cat,
            ExpenseCategory.CategoryType.EXPENSE,
            essential_map[chosen_cat],
            ExpenseTransaction.TransactionType.EXPENSE,
            raw_amt,
            "DAILY_ROUTINE",
            rng.choice(notes),
        )

    return rows


def generate_dataset_rows(primary_count: int, days: int, seed: int) -> List[Dict[str, Any]]:
    """Generate the full multi-student dataset rows deterministically."""
    rng = random.Random(seed)
    all_rows: List[Dict[str, Any]] = []
    for spec in STUDENT_COHORT_2452:
        cnt = primary_count if spec["is_primary"] else 165
        all_rows.extend(_build_student_rows(spec, target_count=cnt, days=days, rng=rng))
    return all_rows


def write_dataset_csv(csv_path: Path, rows: List[Dict[str, Any]]) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "student_code",
        "student_email",
        "full_name",
        "faculty",
        "dorm_area",
        "persona",
        "day_offset",
        "hour",
        "minute",
        "force_current_month",
        "wallet_type",
        "category_name",
        "category_type",
        "is_essential",
        "transaction_type",
        "amount_vnd",
        "scenario_tag",
        "note",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class Command(BaseCommand):
    help = (
        "Seed bộ dữ liệu lớn Khóa 2024 UIT (6 sinh viên 2452xxxx + 1 Admin, 12 danh mục, "
        "18 ví, 16 hóa đơn KTX, ~1.025 giao dịch từ data/uit_student_expenses_dataset.csv)."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Xóa sạch dữ liệu demo hiện có của các tài khoản 2452xxxx trước khi tạo lại.",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="Số ngày lịch sử chuỗi thời gian (mặc định: 60).",
        )
        parser.add_argument(
            "--count",
            type=int,
            default=200,
            help="Số lượng giao dịch cho sinh viên chính 24520001@gm.uit.edu.vn (mặc định: 200).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=221,
            help="Random seed cố định để dữ liệu tái lập 100% (mặc định: 221).",
        )
        parser.add_argument(
            "--csv-path",
            type=str,
            default=str(DEFAULT_CSV_PATH),
            help="Đường dẫn file CSV dataset chuẩn hóa (mặc định: data/uit_student_expenses_dataset.csv).",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        reset: bool = options["reset"]
        days: int = options["days"]
        count: int = options["count"]
        seed: int = options["seed"]
        csv_path = Path(options["csv_path"])

        if days < 7:
            raise CommandError("--days phải lớn hơn hoặc bằng 7.")
        if count < 20:
            raise CommandError("--count phải lớn hơn hoặc bằng 20.")

        admin_password = os.getenv("SEED_DEMO_ADMIN_PASSWORD", "Admin@123")
        student_password = os.getenv("SEED_DEMO_STUDENT_PASSWORD", "Student@123")

        # 0. Kiểm tra cả 4 pre-trained ML/DL artifacts qua Singleton MLModelRegistry (load-only)
        registry = MLModelRegistry.get_instance()
        for model_name in (
            "burn_rate_huber",
            "anomaly_iforest",
            "risk_rf_classifier",
            "deep_mlp_risk",
        ):
            registry.get_model(model_name)

        # 1. Tạo hoặc cập nhật tài khoản Admin
        admin_user, admin_created = UserAccount.objects.get_or_create(
            email="admin@uit.edu.vn",
            defaults={
                "full_name": "Giảng viên / Quản trị viên IE221",
                "role": UserAccount.Role.ADMIN,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if admin_created or reset:
            admin_user.role = UserAccount.Role.ADMIN
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.set_password(admin_password)
            admin_user.save()

        primary_email = STUDENT_COHORT_2452[0]["email"]
        cohort_emails = [s["email"] for s in STUDENT_COHORT_2452] + ["22520001@gm.uit.edu.vn"]

        # Idempotent guard: nếu sinh viên chính 24520001 đã có dữ liệu và không truyền --reset
        existing_primary = UserAccount.objects.filter(email=primary_email).first()
        if existing_primary and not reset:
            existing_w = Wallet.objects.filter(user=existing_primary).count()
            existing_t = ExpenseTransaction.objects.filter(user=existing_primary).count()
            if existing_w > 0 or existing_t > 0:
                total_sys_tx = ExpenseTransaction.objects.count()
                self.stdout.write(
                    self.style.WARNING(
                        f"[Idempotent] Dữ liệu demo Khóa 2024 ({primary_email}) đã tồn tại "
                        f"({existing_w} ví, {existing_t} giao dịch cá nhân / {total_sys_tx} giao dịch toàn hệ thống). "
                        f"Không tạo trùng lặp — truyền thêm `--reset` nếu muốn tái tạo lại từ đầu."
                    )
                )
                return

        if reset:
            old_users = list(UserAccount.all_objects.filter(email__in=cohort_emails))
            if old_users:
                BudgetAlertLog.all_objects.filter(user__in=old_users).delete()
                ExpenseTransaction.all_objects.filter(user__in=old_users).delete()
                MonthlyBudget.all_objects.filter(user__in=old_users).delete()
                RecurringBill.all_objects.filter(user__in=old_users).delete()
                Wallet.all_objects.filter(user__in=old_users).delete()
                UserAccount.all_objects.filter(email="22520001@gm.uit.edu.vn").delete()

        # 2. Xuất / đồng bộ file CSV dataset chuẩn `data/uit_student_expenses_dataset.csv`
        dataset_rows = generate_dataset_rows(primary_count=count, days=days, seed=seed)
        if (count == 200 and days == 60 and seed == 221) or not csv_path.exists():
            write_dataset_csv(csv_path, dataset_rows)

        # 3. Khởi tạo 12 Danh mục hệ thống (user=None)
        categories_by_name: Dict[str, ExpenseCategory] = {}
        for cname, ctype, is_ess, cdesc in SYSTEM_CATEGORIES_SPEC:
            cat_obj, _ = ExpenseCategory.objects.get_or_create(
                name=cname,
                category_type=ctype,
                user=None,
                defaults={"is_essential": is_ess, "description": cdesc},
            )
            categories_by_name[cname] = cat_obj

        # 4. Khởi tạo 6 Sinh viên Khóa 2024 (`24520001` .. `24520006`), Ví tiền & Hóa đơn KTX
        now = timezone.now().replace(second=0, microsecond=0)
        students_by_email: Dict[str, UserAccount] = {}
        wallets_by_student: Dict[str, Dict[str, Wallet]] = {}

        for spec in STUDENT_COHORT_2452:
            semail = spec["email"]
            stu, stu_created = UserAccount.objects.get_or_create(
                email=semail,
                defaults={
                    "student_code": spec["student_code"],
                    "full_name": spec["full_name"],
                    "role": UserAccount.Role.STUDENT,
                    "monthly_income_limit": spec["monthly_income_limit"],
                    "dorm_area": spec["dorm_area"],
                },
            )
            if stu_created or reset:
                stu.student_code = spec["student_code"]
                stu.full_name = spec["full_name"]
                stu.role = UserAccount.Role.STUDENT
                stu.monthly_income_limit = spec["monthly_income_limit"]
                stu.dorm_area = spec["dorm_area"]
                stu.set_password(student_password)
                stu.save()

            students_by_email[semail] = stu
            wallets_by_student[semail] = {}

            for w_type, (w_name, w_bal) in spec["wallets"].items():
                wallets_by_student[semail][w_type] = Wallet.objects.create(
                    user=stu,
                    name=w_name,
                    wallet_type=w_type,
                    balance=w_bal,
                )

            w_map = wallets_by_student[semail]
            RecurringBill.objects.create(
                user=stu,
                wallet=w_map[Wallet.WalletType.BANK],
                category=categories_by_name["Tiền phòng KTX & Điện nước"],
                title=f"Tiền phòng nội trú ({spec['dorm_area']})",
                amount=Decimal("450000.00"),
                due_day=5,
                auto_deduct=True,
                status=RecurringBill.BillStatus.PENDING,
            )
            RecurringBill.objects.create(
                user=stu,
                wallet=w_map[Wallet.WalletType.MOMO],
                category=categories_by_name["Viễn thông & Internet 4G"],
                title="Gói cước 4G Viettel ST90K Sinh Viên",
                amount=Decimal("90000.00"),
                due_day=10,
                auto_deduct=True,
                status=RecurringBill.BillStatus.PENDING,
            )
            if spec["is_primary"]:
                RecurringBill.objects.create(
                    user=stu,
                    wallet=w_map[Wallet.WalletType.MOMO],
                    category=categories_by_name["Tiền phòng KTX & Điện nước"],
                    title="Tiền điện nước & Internet KTX Khu B",
                    amount=Decimal("150000.00"),
                    due_day=8,
                    auto_deduct=False,
                    status=RecurringBill.BillStatus.PENDING,
                )
                RecurringBill.objects.create(
                    user=stu,
                    wallet=w_map[Wallet.WalletType.CASH],
                    category=categories_by_name["Di chuyển & Xe buýt"],
                    title="Vé tháng Xe buýt & Tàu Metro Suối Tiên",
                    amount=Decimal("120000.00"),
                    due_day=1,
                    auto_deduct=False,
                    status=RecurringBill.BillStatus.PAID,
                    last_paid_at=_current_month_timestamp(now, max(now.day - 1, 0), 8, 30),
                )

        # 5. Nạp toàn bộ giao dịch từ dataset rows vào bảng ExpenseTransaction
        tx_objects: List[ExpenseTransaction] = []
        for row in dataset_rows:
            semail = row["student_email"]
            stu = students_by_email[semail]
            w_obj = wallets_by_student[semail][row["wallet_type"]]
            cat_name = row["category_name"]
            cat_obj = categories_by_name.get(cat_name) if cat_name else None
            day_off = int(row["day_offset"])
            hr = int(row["hour"])
            mn = int(row["minute"])

            if row["force_current_month"] == "1":
                tx_dt = _current_month_timestamp(now, day_off, hr, mn)
            else:
                tx_dt = (now - timedelta(days=day_off)).replace(
                    hour=hr, minute=mn, second=0, microsecond=0
                )

            tx_objects.append(
                ExpenseTransaction(
                    user=stu,
                    wallet=w_obj,
                    category=cat_obj,
                    transaction_type=row["transaction_type"],
                    amount=Decimal(str(row["amount_vnd"])),
                    transaction_date=tx_dt,
                    note=row["note"],
                )
            )

        ExpenseTransaction.objects.bulk_create(tx_objects)

        # 6. Chạy suy luận AnomalyDetectionEngine & BurnRateAnalyzer + tạo MonthlyBudget & BudgetAlertLog cho từng sinh viên
        prev_month = 12 if now.month == 1 else now.month - 1
        prev_year = now.year - 1 if now.month == 1 else now.year
        cat_food = categories_by_name["Ăn uống Làng Đại học"]
        cat_transport = categories_by_name["Di chuyển & Xe buýt"]
        cat_ent = categories_by_name["Giải trí & Trà sữa"]

        total_flagged_anomalies = 0
        primary_flagged_anomalies = 0

        for spec in STUDENT_COHORT_2452:
            stu = students_by_email[spec["email"]]
            stu_expenses = list(
                ExpenseTransaction.objects.filter(
                    user=stu,
                    transaction_type=ExpenseTransaction.TransactionType.EXPENSE,
                ).select_related("category")
            )
            payload = [
                {
                    "id": str(tx.id),
                    "amount": float(tx.amount),
                    "transaction_date": tx.transaction_date,
                    "category__name": tx.category.name if tx.category else "",
                    "note": tx.note,
                }
                for tx in stu_expenses
            ]
            anom_report = AnomalyDetectionEngine(raw_transactions=payload).run_inference()
            z_map = {item["id"]: float(item["z_score"]) for item in anom_report.get("anomalies", [])}

            flagged: List[ExpenseTransaction] = []
            for tx in stu_expenses:
                tid = str(tx.id)
                if tid in z_map:
                    tx.is_anomaly = True
                    tx.anomaly_score = z_map[tid]
                    flagged.append(tx)
            if flagged:
                ExpenseTransaction.objects.bulk_update(flagged, ["is_anomaly", "anomaly_score"])
            total_flagged_anomalies += len(flagged)
            if spec["is_primary"]:
                primary_flagged_anomalies = len(flagged)

            curr_exps = [
                tx
                for tx in stu_expenses
                if tx.transaction_date.month == now.month and tx.transaction_date.year == now.year
            ]
            prev_exps = [
                tx
                for tx in stu_expenses
                if tx.transaction_date.month == prev_month and tx.transaction_date.year == prev_year
            ]

            prev_food = sum(
                (tx.amount for tx in prev_exps if tx.category_id == cat_food.id), Decimal("0.00")
            )
            prev_trans = sum(
                (tx.amount for tx in prev_exps if tx.category_id == cat_transport.id),
                Decimal("0.00"),
            )
            MonthlyBudget.objects.create(
                user=stu,
                category=cat_food,
                month=prev_month,
                year=prev_year,
                allocated_amount=Decimal("2000000.00"),
                spent_amount=prev_food,
                alert_threshold_pct=80,
            )
            MonthlyBudget.objects.create(
                user=stu,
                category=cat_transport,
                month=prev_month,
                year=prev_year,
                allocated_amount=Decimal("450000.00"),
                spent_amount=prev_trans,
                alert_threshold_pct=80,
            )

            curr_total = sum((tx.amount for tx in curr_exps), Decimal("0.00"))
            curr_food = sum(
                (tx.amount for tx in curr_exps if tx.category_id == cat_food.id), Decimal("0.00")
            )
            curr_ent = sum(
                (tx.amount for tx in curr_exps if tx.category_id == cat_ent.id), Decimal("0.00")
            )

            overall_b = MonthlyBudget.objects.create(
                user=stu,
                category=None,
                month=now.month,
                year=now.year,
                allocated_amount=spec["monthly_income_limit"],
                spent_amount=curr_total,
                alert_threshold_pct=80,
            )

            food_alloc = (
                _round_to_step(curr_food / Decimal("0.88"), step=10000)
                if curr_food > 0
                else Decimal("1500000.00")
            )
            food_b = MonthlyBudget.objects.create(
                user=stu,
                category=cat_food,
                month=now.month,
                year=now.year,
                allocated_amount=food_alloc,
                spent_amount=curr_food,
                alert_threshold_pct=80,
            )

            ent_alloc = (
                min(
                    Decimal("800000.00"),
                    _round_to_step(curr_ent * Decimal("0.75"), step=50000),
                )
                if (spec["is_primary"] or "HIGH_RISK" in spec["persona"]) and curr_ent > Decimal("100000.00")
                else Decimal("900000.00")
            )
            ent_b = MonthlyBudget.objects.create(
                user=stu,
                category=cat_ent,
                month=now.month,
                year=now.year,
                allocated_amount=ent_alloc,
                spent_amount=curr_ent,
                alert_threshold_pct=80,
            )

            # Cảnh báo ANOMALY gắn FK trực tiếp vào giao dịch bất thường
            for idx, a_tx in enumerate(
                sorted(flagged, key=lambda t: t.transaction_date, reverse=True)[:5]
            ):
                BudgetAlertLog.objects.create(
                    user=stu,
                    budget=overall_b,
                    transaction=a_tx,
                    alert_type=BudgetAlertLog.AlertType.ANOMALY,
                    message=(
                        f"[AI ANOMALY - {stu.student_code}] Chi tiêu đột biến {a_tx.amount:,.0f} VNĐ "
                        f"(Z-Score={a_tx.anomaly_score:.2f}): {a_tx.note}"
                    ),
                    is_read=(idx >= 2),
                )

            if food_b.usage_percentage >= 80.0:
                BudgetAlertLog.objects.create(
                    user=stu,
                    budget=food_b,
                    alert_type=BudgetAlertLog.AlertType.WARNING_80,
                    message=(
                        f"Danh mục '{cat_food.name}' của {stu.student_code} đã chạm "
                        f"{food_b.usage_percentage:.1f}% ({food_b.spent_amount:,.0f}/{food_b.allocated_amount:,.0f} VNĐ)."
                    ),
                    is_read=False,
                )

            if ent_b.usage_percentage >= 100.0:
                BudgetAlertLog.objects.create(
                    user=stu,
                    budget=ent_b,
                    alert_type=BudgetAlertLog.AlertType.CRITICAL,
                    message=(
                        f"[VƯỢT NGÂN SÁCH] Danh mục '{cat_ent.name}' của {stu.student_code} đã đạt "
                        f"{ent_b.usage_percentage:.1f}% ({ent_b.spent_amount:,.0f}/{ent_b.allocated_amount:,.0f} VNĐ)."
                    ),
                    is_read=False,
                )

            stu_balance = sum(w.balance for w in wallets_by_student[spec["email"]].values())
            burn_rep = BurnRateAnalyzer(
                raw_transactions=payload,
                current_balance=stu_balance,
                reference_date=now.date(),
            ).run_inference()
            ex_str = burn_rep.get("predicted_exhaustion_date")
            ex_date = date.fromisoformat(ex_str) if ex_str else None
            BudgetAlertLog.objects.create(
                user=stu,
                budget=overall_b,
                alert_type=BudgetAlertLog.AlertType.BURN_RATE,
                message=(
                    f"[BURN-RATE {stu.student_code}] Tốc độ tiêu ~{burn_rep['daily_burn_rate']:,.0f} VNĐ/ngày; "
                    f"khuyến nghị an toàn: {burn_rep['safe_daily_allowance']:,.0f} VNĐ/ngày."
                ),
                predicted_exhaustion_date=ex_date,
                is_read=False,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Hoàn tất seed dữ liệu Khóa 2024 UIT (seed={seed})! "
                f"Đã tạo 7 tài khoản (1 Admin + 6 SV 24520001..24520006), 18 ví, 12 danh mục, "
                f"14 hóa đơn KTX, {len(tx_objects)} giao dịch tổng ({count} giao dịch cho {primary_email}, "
                f"{primary_flagged_anomalies}/{total_flagged_anomalies} anomaly) và lưu CSV tại {csv_path.name}."
            )
        )
