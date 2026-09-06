import pytest
from fastapi.testclient import TestClient
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_success():
    response = client.post(
        "/api/auth/login",
        json={"email": "officer@gem.gov.in", "password": "GeM@2026!Officer"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "officer@gem.gov.in"
    assert data["user"]["role"]["name"] == "Procurement Officer"

def test_login_invalid_password():
    response = client.post(
        "/api/auth/login",
        json={"email": "officer@gem.gov.in", "password": "WrongPassword123!"}
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

def test_login_nonexistent_user():
    response = client.post(
        "/api/auth/login",
        json={"email": "unknown_user@example.com", "password": "anypassword"}
    )
    assert response.status_code == 401

def test_get_current_user_profile():
    # Login first
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "officer@gem.gov.in", "password": "GeM@2026!Officer"}
    )
    token = login_resp.json()["access_token"]

    # Request /me
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "officer@gem.gov.in"
    assert user_data["role"]["name"] == "Procurement Officer"

def test_get_current_user_profile_unauthorized():
    response = client.get("/api/auth/me")
    assert response.status_code == 401
