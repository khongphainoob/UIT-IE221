"""
Authentication & User Account Serializers (DRF JSON Template Layer).
"""
from decimal import Decimal
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from apps.finance.models import UserAccount


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """Serializer đăng ký tài khoản sinh viên UIT."""

    password = serializers.CharField(
        write_only=True, min_length=6, style={"input_type": "password"}
    )

    class Meta:
        model = UserAccount
        fields = [
            "id",
            "email",
            "student_code",
            "full_name",
            "password",
            "role",
            "monthly_income_limit",
            "dorm_area",
            "created_at",
        ]
        read_only_fields = ["id", "role", "created_at"]
        extra_kwargs = {
            "student_code": {"required": True, "allow_blank": False, "allow_null": False},
        }

    def validate_student_code(self, value):
        if not (len(value) == 8 and value.isdecimal()):
            raise serializers.ValidationError("MSSV phải gồm đúng 8 chữ số.")
        return value

    def validate(self, attrs):
        student = UserAccount(
            email=attrs.get("email", ""),
            student_code=attrs.get("student_code"),
            full_name=attrs.get("full_name", ""),
        )
        try:
            validate_password(attrs["password"], user=student)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": exc.messages}) from exc
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return UserAccount.objects.create_user(password=password, **validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer trả về & cập nhật thông tin hồ sơ người dùng."""

    class Meta:
        model = UserAccount
        fields = [
            "id",
            "email",
            "student_code",
            "full_name",
            "role",
            "monthly_income_limit",
            "dorm_area",
            "is_active",
            "created_at",
        ]
        read_only_fields = [
            "id", "email", "student_code", "role", "is_active", "created_at"
        ]


class UserAllowanceUpdateSerializer(serializers.ModelSerializer):
    """Serializer cập nhật trợ cấp tháng (`monthly_income_limit`) và khu vực KTX (`dorm_area`)."""

    monthly_income_limit = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal("0.00"),
        required=False,
    )
    dorm_area = serializers.CharField(max_length=120, required=False, allow_blank=True)

    class Meta:
        model = UserAccount
        fields = ["monthly_income_limit", "dorm_area", "full_name"]
