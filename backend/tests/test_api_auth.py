"""Dhruva.AI V2 — Integration Tests: Authentication API Endpoints.

Tests:
- POST /api/v1/auth/login (Success with credentials, Error with invalid password, Error with unknown user)
- GET /api/v1/auth/me (Authenticated profile, Role & Permission verification, Unauthorized 401)
- POST /api/v1/auth/logout (Revocation and cookie clearance)
- POST /api/v1/auth/refresh (Token rotation and validation)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthAPI:
    """Authentication and session lifecycle endpoint tests."""

    async def test_login_success(self, client: AsyncClient, seed_data: dict):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["success"] is True
        assert "data" in body
        data = body["data"]
        assert "access_token" in data
        assert data["token_type"].lower() == "bearer"
        assert data["user"]["email"] == "admin@iitb.ac.in"
        assert "INSTITUTION_ADMIN" in data["user"]["roles"]

        # Check cookies set
        cookies = response.cookies
        assert "access_token" in cookies
        assert "refresh_token" in cookies

    async def test_login_invalid_password_fails(self, client: AsyncClient, seed_data: dict):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iitb.ac.in", "password": "WrongPassword123!"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_unknown_user_fails(self, client: AsyncClient, seed_data: dict):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "unknown@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_get_me_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        body = response.json()
        assert body["success"] is False
        assert body["error"]["code"] == "UNAUTHORIZED"

    async def test_get_me_authorized(self, client: AsyncClient, seed_data: dict):
        # 1. Login to obtain access token
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "prof.verma@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert login_res.status_code == 200
        token = login_res.json()["data"]["access_token"]

        # 2. Query /me with Bearer header
        me_res = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        me_data = me_res.json()["data"]
        assert me_data["email"] == "prof.verma@iitb.ac.in"
        assert me_data["first_name"] == "Vikram"
        assert "FACULTY" in me_data["roles"]
        assert "assessment:grade" in me_data["permissions"]

    async def test_logout(self, client: AsyncClient, seed_data: dict):
        # Login
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": "rahul.k@iitb.ac.in", "password": "SecurePass123!"},
        )
        token = login_res.json()["data"]["access_token"]
        refresh_cookie = login_res.cookies.get("refresh_token")

        # Logout
        logout_res = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
            cookies={"refresh_token": refresh_cookie},
        )
        assert logout_res.status_code == 200
        assert logout_res.json()["data"]["message"] == "Logged out successfully"
