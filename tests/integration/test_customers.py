import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_customer(client: AsyncClient, admin_auth_headers: dict):
    response = await client.post(
        "/api/v1/create-customer",
        json={
            "name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "0987654321",
            "address": "456 Oak Ave",
            "proof_of_identity": "Driver License",
        },
        headers=admin_auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "jane.doe@example.com"


@pytest.mark.integration
async def test_list_customers(client: AsyncClient, test_customer, admin_auth_headers: dict):
    response = await client.get("/api/v1/customers", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    customer_ids = [c["id"] for c in data]
    assert test_customer.id in customer_ids


@pytest.mark.integration
async def test_upload_document(client: AsyncClient, test_customer, admin_auth_headers: dict, s3_client):
    # Prepare a dummy file
    file_content = b"%PDF-1.4 dummy content"
    files = {"file": ("test.pdf", file_content, "application/pdf")}

    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        files=files,
        data={"document_type": "passport"},
        headers=admin_auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert "file_url" in data
    assert data["document_type"] == "passport"

    # Verify file is in mocked S3
    response_s3 = s3_client.list_objects(Bucket="test-bucket")
    assert "Contents" in response_s3
    assert len(response_s3["Contents"]) == 1


@pytest.mark.integration
async def test_upload_invalid_file(client: AsyncClient, test_customer, admin_auth_headers: dict):
    # Prepare an invalid file (exe)
    file_content = b"MZ\x90\x00\x03\x00\x00\x00"
    files = {"file": ("virus.exe", file_content, "application/octet-stream")}

    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        files=files,
        data={"document_type": "passport"},
        headers=admin_auth_headers,
    )

    # Expect 400 Bad Request due to validation
    assert response.status_code == 400
