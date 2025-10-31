import pytest


def test_register_farmer(client):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newfarmer@test.com",
            "password": "password",
            "first_name": "New",
            "last_name": "Farmer",
            "user_type": "farmer",
        },
    )

    assert response.status_code == 201
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["user_type"] == "farmer"


def test_login_success(client, farmer_user):
    response = client.post(
        "/api/auth/login", json={"email": "farmer@test.com", "password": "password"}
    )

    assert response.status_code == 200
    data = response.get_json()
    assert "access_token" in data
    assert data["user"]["email"] == "farmer@test.com"
