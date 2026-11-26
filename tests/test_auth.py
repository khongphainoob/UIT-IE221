"""
Unit & Integration Tests for Module 1 (auth_iam):
Registration, UIT Email Validation, JWT Login, Allowance Update, and Admin RBAC (6 tests).
"""
import pytest
from datetime import timedelta
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken
from apps.finance.models import UserAccount


@pytest.mark.django_db
class TestStudentAuthentication:
    def test_registration_cannot_choose_admin_role(self, api_client):
        response = api_client.post(
            reverse("auth-register"),
            {
                "email": "22528888@gm.uit.edu.vn",
                "student_code": "22528888",
                "full_name": "Sinh viên mới",
                "password": "StrongPassword123",
                "role": "ADMIN",
                "is_staff": True,
            },
            format="json",
        )
        assert response.status_code == 201
        user = UserAccount.objects.get(email="22528888@gm.uit.edu.vn")
        assert user.role == UserAccount.Role.STUDENT
        assert user.is_staff is False

    @pytest.mark.parametrize(
        "changes",
        [
            {"student_code": ""},
            {"student_code": "ABC"},
            {"password": "123456"},
        ],
    )
    def test_registration_rejects_missing_or_invalid_identity_and_weak_password(
        self, api_client, changes
    ):
        payload = {
            "email": "22528889@gm.uit.edu.vn",
            "student_code": "22528889",
            "full_name": "Sinh viên mới",
            "password": "StrongPassword123",
        }
        payload.update(changes)
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == 400
        assert response.data["error_code"] == "validation_error"
        assert not UserAccount.objects.filter(email=payload["email"]).exists()

    def test_profile_cannot_change_own_identity_or_role(self, auth_client, student_user):
        response = auth_client.patch(
            reverse("users-me"),
            {"role": "ADMIN", "email": "other@uit.edu.vn", "student_code": "00000000", "full_name": "Tên mới"},
            format="json",
        )
        assert response.status_code == 200
        student_user.refresh_from_db()
        assert student_user.role == UserAccount.Role.STUDENT
        assert student_user.email == "22520999@gm.uit.edu.vn"
        assert student_user.student_code == "22520999"
        assert student_user.full_name == "Tên mới"

    def test_invalid_credentials_and_expired_token_return_401(self, api_client, student_user):
        bad = api_client.post(
            reverse("auth-login"),
            {"email": student_user.email, "password": "wrong"},
            format="json",
        )
        assert bad.status_code == 401
        assert bad.data["error_code"] == "authentication_failed"

        expired = AccessToken.for_user(student_user)
        expired.set_exp(lifetime=timedelta(seconds=-1))
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {expired}")
        response = api_client.get(reverse("users-me"))
        assert response.status_code == 401
        assert response.data["error_code"] == "authentication_failed"

    def test_locked_account_cannot_login_or_use_existing_token(self, api_client, student_user):
        login = api_client.post(
            reverse("auth-login"),
            {"email": student_user.email, "password": "Password@123"},
            format="json",
        )
        assert login.status_code == 200
        student_user.is_active = False
        student_user.save(update_fields=["is_active"])
        rejected = api_client.post(
            reverse("auth-login"),
            {"email": student_user.email, "password": "Password@123"},
            format="json",
        )
        assert rejected.status_code == 401
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        assert api_client.get(reverse("users-me")).status_code == 401
        api_client.credentials()
        assert api_client.post(
            reverse("auth-token-refresh"), {"refresh": login.data["refresh"]}, format="json"
        ).status_code == 401

    def test_admin_cannot_toggle_another_admin(self, api_client):
        admin = UserAccount.objects.create_superuser(
            email="first-admin@uit.edu.vn", password="AdminPassword123", full_name="Admin 1"
        )
        other = UserAccount.objects.create_superuser(
            email="second-admin@uit.edu.vn", password="AdminPassword123", full_name="Admin 2"
        )
        api_client.force_authenticate(user=admin)
        response = api_client.patch(reverse("admin-users-toggle-status", kwargs={"user_id": other.id}))
        assert response.status_code == 403
        other.refresh_from_db()
        assert other.is_active is True

    def test_register_valid_uit_email(self, api_client):
        payload = {
            "email": "22521234@gm.uit.edu.vn",
            "student_code": "22521234",
            "full_name": "Lê Văn UIT",
            "password": "StrongPassword123",
        }
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert response.data["data"]["email"] == "22521234@gm.uit.edu.vn"
        assert response.data["data"]["role"] == "STUDENT"

    def test_register_rejects_non_uit_email(self, api_client):
        payload = {
            "email": "sinhvien@gmail.com",
            "student_code": "22529999",
            "full_name": "Người Dùng Ngoài",
            "password": "StrongPassword123",
        }
        response = api_client.post(reverse("auth-register"), payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["success"] is False

    def test_jwt_login_and_me_endpoint(self, api_client, student_user):
        login_res = api_client.post(
            reverse("auth-login"),
            {"email": student_user.email, "password": "Password@123"},
            format="json",
        )
        assert login_res.status_code == status.HTTP_200_OK
        access_token = login_res.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        me_res = api_client.get(reverse("users-me"))
        assert me_res.status_code == status.HTTP_200_OK
        assert me_res.data["data"]["email"] == student_user.email

    def test_update_student_allowance_and_dorm_area(self, auth_client, student_user):
        payload = {
            "monthly_income_limit": "5500000.00",
            "dorm_area": "KTX Khu A - ĐHQG TP.HCM",
        }
        res = auth_client.patch(reverse("users-me-allowance"), payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert float(student_user.monthly_income_limit) == 5500000.0
        assert student_user.dorm_area == "KTX Khu A - ĐHQG TP.HCM"

    def test_student_cannot_access_admin_users_endpoint(self, auth_client):
        res = auth_client.get(reverse("admin-users"))
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_list_and_toggle_user_status(self, api_client, student_user):
        admin = UserAccount.objects.create_superuser(
            email="admin@uit.edu.vn",
            password="AdminPassword123",
            full_name="Admin UIT",
        )
        api_client.force_authenticate(user=admin)
        list_res = api_client.get(reverse("admin-users"))
        assert list_res.status_code == status.HTTP_200_OK
        assert list_res.data["data"]["system_statistics"]["total_users"] >= 2

        toggle_res = api_client.patch(
            reverse("admin-users-toggle-status", kwargs={"user_id": student_user.id})
        )
        assert toggle_res.status_code == status.HTTP_200_OK
        student_user.refresh_from_db()
        assert student_user.is_active is False
