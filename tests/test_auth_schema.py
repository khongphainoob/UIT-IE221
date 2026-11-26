"""OpenAPI must describe the authentication and role boundary exposed by W2.03."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_auth_schema_documents_login_refresh_profile_and_admin_errors():
    schema = APIClient().get(reverse("schema"), HTTP_ACCEPT="application/json").json()
    paths = schema["paths"]
    login = paths["/api/v1/auth/login/"]["post"]
    refresh = paths["/api/v1/auth/token/refresh/"]["post"]
    profile = paths["/api/v1/users/me/"]["get"]
    admin_toggle = paths["/api/v1/admin/users/{user_id}/toggle-status/"]["patch"]

    assert login["tags"] == refresh["tags"] == ["1. Auth & User Management"]
    assert {"200", "401"} <= set(login["responses"])
    assert {"200", "401"} <= set(refresh["responses"])
    assert {"jwtAuth": []} in profile["security"]
    assert {"200", "401"} <= set(profile["responses"])
    assert {"200", "401", "403", "404"} <= set(admin_toggle["responses"])

    success = profile["responses"]["200"]["content"]["application/json"]["schema"]
    success = schema["components"]["schemas"][success["$ref"].split("/")[-1]]
    assert {"success", "data"} <= set(success["properties"])
    error = admin_toggle["responses"]["403"]["content"]["application/json"]["schema"]
    error = schema["components"]["schemas"][error["$ref"].split("/")[-1]]
    assert {"error_code", "message", "error"} <= set(error["properties"])
