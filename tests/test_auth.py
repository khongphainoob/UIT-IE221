"""
Unit & Integration Tests for Module 1 (auth_iam):
Registration, UIT Email Validation, JWT Login, Allowance Update, and Admin RBAC (6 tests).
"""
import pytest
from django.urls import reverse
from rest_framework import status
from apps.finance.models import UserAccount


@pytest.mark.django_db
class TestStudentAuthentication:
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
