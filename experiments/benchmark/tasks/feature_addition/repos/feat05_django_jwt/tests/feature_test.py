"""Feature tests: JWT Authentication.

These tests verify JWT auth was correctly added.
They should FAIL before the feature and PASS after.
"""

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def registered_user(api_client):
    """Register a test user and return credentials."""
    resp = api_client.post(
        "/api/auth/register/",
        {"email": "test@example.com", "password": "SecurePass123!"},
        format="json",
    )
    assert resp.status_code == 201
    return {"email": "test@example.com", "password": "SecurePass123!"}


@pytest.fixture
def auth_tokens(api_client, registered_user):
    """Get JWT tokens for a registered user."""
    resp = api_client.post(
        "/api/auth/login/",
        registered_user,
        format="json",
    )
    assert resp.status_code == 200
    return resp.data


@pytest.mark.django_db
class TestJWTAuth:
    def test_register_endpoint_exists(self, api_client):
        """POST /api/auth/register/ should exist and accept email+password."""
        resp = api_client.post(
            "/api/auth/register/",
            {"email": "new@example.com", "password": "TestPass123!"},
            format="json",
        )
        assert resp.status_code == 201

    def test_login_returns_tokens(self, api_client, registered_user):
        """POST /api/auth/login/ should return access and refresh tokens."""
        resp = api_client.post(
            "/api/auth/login/",
            registered_user,
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_refresh_token_works(self, api_client, auth_tokens):
        """POST /api/auth/refresh/ should return a new access token."""
        resp = api_client.post(
            "/api/auth/refresh/",
            {"refresh": auth_tokens["refresh"]},
            format="json",
        )
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_items_require_auth(self, api_client):
        """GET /api/items/ should require authentication (401 without token)."""
        resp = api_client.get("/api/items/")
        assert resp.status_code == 401

    def test_items_accessible_with_token(self, api_client, auth_tokens):
        """GET /api/items/ should work with valid JWT token."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access']}")
        resp = api_client.get("/api/items/")
        assert resp.status_code == 200

    def test_create_item_with_auth(self, api_client, auth_tokens):
        """POST /api/items/ should work with valid JWT token."""
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_tokens['access']}")
        resp = api_client.post(
            "/api/items/",
            {"name": "Auth Widget", "price": "9.99"},
            format="json",
        )
        assert resp.status_code == 201

    def test_invalid_token_rejected(self, api_client):
        """Request with invalid token should return 401."""
        api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token-here")
        resp = api_client.get("/api/items/")
        assert resp.status_code == 401

    def test_login_with_wrong_password(self, api_client, registered_user):
        """Login with wrong password should return 401."""
        resp = api_client.post(
            "/api/auth/login/",
            {"email": registered_user["email"], "password": "WrongPassword123!"},
            format="json",
        )
        assert resp.status_code == 401
