"""Tests for authentication endpoints"""
import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_missing_password(client):
    response = await client.post(
        "/api/v1/login",
        data={"username": "admin"},
    )
    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_protected_endpoint_without_auth(client):
    response = await client.get("/api/v1/customers")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    response = await client.get(
        "/api/v1/customers",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert response.status_code in [401, 403]
