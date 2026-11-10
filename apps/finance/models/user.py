"""
1. UserAccount Model (id, email, student_code, full_name, role: ADMIN/STUDENT, monthly_income_limit, dorm_area).
Inherits from BaseModel + AbstractBaseUser + PermissionsMixin.
"""
from decimal import Decimal
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from core.models import ActiveRecordQuerySet, BaseModel


class UserAccountManager(BaseUserManager):
    """Custom manager for UserAccount with UIT email authentication and Soft-Delete support."""

    def get_queryset(self):
        return ActiveRecordQuerySet(self.model, using=self._db).filter(is_deleted=False)

    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email sinh viên/người dùng là bắt buộc.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str = None, **extra_fields):
        extra_fields.setdefault("role", UserAccount.Role.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email=email, password=password, **extra_fields)


class UserAccount(BaseModel, AbstractBaseUser, PermissionsMixin):
    """
    Bảng 1: UserAccount - Tài khoản người dùng (Admin / Sinh viên UIT).
    Chuẩn hóa 3NF: lưu trữ định danh, hạn mức thu nhập/trợ cấp tháng và khu vực KTX.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Quản trị viên"
        STUDENT = "STUDENT", "Sinh viên"

    uit_email_validator = RegexValidator(
        regex=r"^[a-zA-Z0-9._%+-]+@(gm\.uit\.edu\.vn|uit\.edu\.vn)$",
        message="Email phải thuộc tên miền trường ĐH Công nghệ Thông tin (@gm.uit.edu.vn hoặc @uit.edu.vn).",
    )

    email = models.EmailField(
        unique=True,
        validators=[uit_email_validator],
        help_text="Email định danh UIT (VD: 22520001@gm.uit.edu.vn)",
    )
    student_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text="Mã số sinh viên UIT (MSSV)",
    )
    full_name = models.CharField(max_length=150, help_text="Họ và tên đầy đủ")
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    monthly_income_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("4500000.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Trợ cấp / hạn mức thu nhập hàng tháng của sinh viên (VNĐ)",
    )
    dorm_area = models.CharField(
        max_length=120,
        blank=True,
        default="KTX Khu B - ĐHQG TP.HCM",
        help_text="Khu vực nội trú / trọ của sinh viên (VD: KTX Khu A, KTX Khu B)",
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserAccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        db_table = "finance_user_account"
        verbose_name = "Tài khoản người dùng"
        verbose_name_plural = "Danh sách tài khoản"

    def __str__(self) -> str:
        return f"{self.full_name} ({self.email}) - {self.role}"
