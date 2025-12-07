"""Integration tests for authentication endpoints"""
import pytest


@pytest.mark.asyncio
async def test_login_successful(client, admin_user):
    """Test successful login with valid credentials"""
    # OAuth2PasswordRequestForm expects form data, not JSON
    response = await client.post(
        "/api/v1/login",
        data={"username": "admin", "password": "AdminPass123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = await client.post(
        "/api/v1/login",
        data={"username": "nonexistent", "password": "WrongPass"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_missing_credentials(client):
    """Test login with missing credentials"""
    response = await client.post(
        "/api/v1/login",
        data={"username": "admin"},  # missing password
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_health_check_success(client):
    """Test health check endpoint"""
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data or "message" in data


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client):
    """Test that protected endpoints require authentication"""
    # Assuming /api/v1/customers is protected
    response = await client.get("/api/v1/customers")

    # Should return 401 or 403 without auth
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_protected_endpoint_with_auth(client, admin_auth_headers):
    """Test that protected endpoints work with authentication"""
    response = await client.get(
        "/api/v1/customers",
        headers=admin_auth_headers,
    )

    # Should return 200 (or 204 if empty)
    assert response.status_code in [200, 204]


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    """Test that invalid JWT token is rejected"""
    response = await client.get(
        "/api/v1/customers",
        headers={"Authorization": "Bearer invalid.token.here"},
    )

    assert response.status_code in [401, 403]
