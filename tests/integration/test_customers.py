"""Integration tests for customer endpoints"""
import pytest


@pytest.mark.asyncio
async def test_get_customers_success(client, admin_auth_headers, test_customer):
    """Test retrieving list of customers"""
    response = await client.get(
        "/api/v1/customers",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_customers_requires_auth(client):
    """Test that getting customers requires authentication"""
    response = await client.get("/api/v1/customers")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_create_customer_success(client, admin_auth_headers):
    """Test creating a new customer"""
    customer_data = {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "phone": "9876543210",
        "address": "456 Oak Ave",
        "proof_of_identity": "ID Card",
    }

    response = await client.post(
        "/api/v1/create-customer",
        json=customer_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    data = response.json()
    assert data["name"] == "Jane Smith"
    assert data["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_create_customer_duplicate_email(client, admin_auth_headers, test_customer):
    """Test that duplicate email is rejected"""
    customer_data = {
        "name": "Different Name",
        "email": test_customer.email,  # duplicate
        "phone": "5555555555",
        "address": "123 New St",
        "proof_of_identity": "Passport",
    }

    response = await client.post(
        "/api/v1/create-customer",
        json=customer_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 409]


@pytest.mark.asyncio
async def test_create_customer_missing_fields(client, admin_auth_headers):
    """Test that missing fields are rejected"""
    customer_data = {
        "name": "John Doe",
        # missing email, phone, address, proof_of_identity
    }

    response = await client.post(
        "/api/v1/create-customer",
        json=customer_data,
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 422]


@pytest.mark.asyncio
async def test_customer_with_s3_fields(client, admin_auth_headers, test_customer):
    """Test that customer can have S3 document fields"""
    response = await client.get(
        f"/api/v1/customers",
        headers=admin_auth_headers,
    )

    assert response.status_code == 200
    customers = response.json()

    # Find our test customer
    customer = next((c for c in customers if c["id"] == test_customer.id), None)
    if customer:
        # Should have s3 fields (they can be None)
        assert "proof_image_url" in customer or "proof_image_filename" in customer


@pytest.mark.asyncio
async def test_get_customer_by_id_requires_auth(client, test_customer):
    """Test that getting customer by ID requires authentication"""
    response = await client.get(f"/api/v1/customers/{test_customer.id}")

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_nonexistent_customer(client, admin_auth_headers):
    """Test getting a customer that doesn't exist"""
    response = await client.get(
        "/api/v1/customers/99999",
        headers=admin_auth_headers,
    )

    assert response.status_code in [404, 422]
