"""The published schema must describe the API a student can actually call."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_swagger_and_schema_expose_five_modules_and_jwt():
    client = APIClient()
    assert client.get(reverse("swagger-ui")).status_code == 200
    response = client.get(reverse("schema"), HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    document = response.json()
    assert len(document["tags"]) == 5
    assert {tag["name"] for tag in document["tags"]} == {
        "1. Auth & User Management",
        "2. Wallets",
        "3. Categories, Transactions & Recurring Bills",
        "4. Budgets & Alerts",
        "5. Analytics & ML Serving Engine",
    }
    assert document["components"]["securitySchemes"]["jwtAuth"]["scheme"] == "bearer"
    wallet_get = document["paths"]["/api/v1/wallets/"]["get"]
    assert {"jwtAuth": []} in wallet_get["security"]
    assert wallet_get["tags"] == ["2. Wallets"]
    assert document["paths"]["/api/v1/auth/login/"]["post"]["tags"] == [
        "1. Auth & User Management"
    ]


@pytest.mark.django_db
def test_wallet_schema_matches_success_and_error_envelopes(api_client, student_user):
    document = api_client.get(reverse("schema"), HTTP_ACCEPT="application/json").json()
    wallet_get = document["paths"]["/api/v1/wallets/"]["get"]
    success = wallet_get["responses"]["200"]["content"]["application/json"]["schema"]
    success = document["components"]["schemas"][success["$ref"].split("/")[-1]]
    assert success["properties"]["success"]["type"] == "boolean"
    assert "data" in success["properties"]
    wallet_item = success["properties"]["data"]["items"]
    wallet_item = document["components"]["schemas"][wallet_item["$ref"].split("/")[-1]]
    assert {"id", "name", "wallet_type", "balance"} <= set(wallet_item["properties"])
    error = wallet_get["responses"]["401"]["content"]["application/json"]["schema"]
    error = document["components"]["schemas"][error["$ref"].split("/")[-1]]
    assert {"success", "status", "error_code", "message", "error"} <= set(error["properties"])

    assert api_client.get(reverse("wallet-list-create")).status_code == 401
    login = api_client.post(
        reverse("auth-login"),
        {"email": student_user.email, "password": "Password@123"},
        format="json",
    )
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
    actual = api_client.get(reverse("wallet-list-create"))
    assert actual.status_code == 200
    assert actual.data == {"success": True, "data": []}
