"""End-to-end tests for document upload workflows (S3 integration)"""
import pytest
from io import BytesIO


@pytest.mark.asyncio
async def test_document_upload_workflow(client, admin_auth_headers, test_customer):
    """Test document upload workflow: Create customer -> Upload document -> Verify S3 URL -> Delete"""
    # Step 1: Create a mock PDF file
    pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj"

    # Step 2: Upload document for customer
    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "passport"},
        files={"file": ("passport.pdf", BytesIO(pdf_content), "application/pdf")},
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    upload_response = response.json()
    assert "file_url" in upload_response
    assert "s3" in upload_response["file_url"] or "amazonaws" in upload_response["file_url"]

    s3_url = upload_response["file_url"]

    # Step 3: Verify S3 URL is valid
    assert s3_url.startswith("https://")
    assert str(test_customer.id) in s3_url

    # Step 4: Delete document
    response = await client.delete(
        f"/api/v1/documents/{test_customer.id}",
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 404]  # 404 if doc was never actually uploaded to S3


@pytest.mark.asyncio
async def test_document_upload_jpg_format(client, admin_auth_headers, test_customer):
    """Test uploading JPG format document"""
    # JPG magic bytes
    jpg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"

    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "id_card"},
        files={"file": ("id_card.jpg", BytesIO(jpg_content), "image/jpeg")},
        headers=admin_auth_headers,
    )

    assert response.status_code in [200, 201]
    if response.status_code in [200, 201]:
        data = response.json()
        assert data["document_type"] == "id_card"


@pytest.mark.asyncio
async def test_document_upload_invalid_file_type(client, admin_auth_headers, test_customer):
    """Test that invalid file types are rejected"""
    # EXE magic bytes
    exe_content = b"MZ\x90\x00"

    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "passport"},
        files={"file": ("malware.exe", BytesIO(exe_content), "application/x-msdownload")},
        headers=admin_auth_headers,
    )

    assert response.status_code in [400, 413, 415]


@pytest.mark.asyncio
async def test_document_upload_nonexistent_customer(client, admin_auth_headers):
    """Test uploading document for non-existent customer"""
    pdf_content = b"%PDF-1.4"

    response = await client.post(
        "/api/v1/upload-document/99999",
        data={"document_type": "passport"},
        files={"file": ("doc.pdf", BytesIO(pdf_content), "application/pdf")},
        headers=admin_auth_headers,
    )

    assert response.status_code in [404, 400, 422]


@pytest.mark.asyncio
async def test_document_upload_without_auth(client, test_customer):
    """Test that document upload requires authentication"""
    pdf_content = b"%PDF-1.4"

    response = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "passport"},
        files={"file": ("doc.pdf", BytesIO(pdf_content), "application/pdf")},
    )

    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_document_delete_nonexistent_customer(client, admin_auth_headers):
    """Test deleting document for non-existent customer"""
    response = await client.delete(
        "/api/v1/documents/99999",
        headers=admin_auth_headers,
    )

    assert response.status_code in [404, 400, 422]


@pytest.mark.asyncio
async def test_document_replace_workflow(client, admin_auth_headers, test_customer):
    """Test replacing an existing document with a new one"""
    pdf_content_1 = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj\n"
    pdf_content_2 = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n2 0 obj\n"

    # Upload first document
    response1 = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "passport"},
        files={"file": ("passport_v1.pdf", BytesIO(pdf_content_1), "application/pdf")},
        headers=admin_auth_headers,
    )
    assert response1.status_code in [200, 201]
    first_url = response1.json()["file_url"]

    # Upload second document (replace)
    response2 = await client.post(
        f"/api/v1/upload-document/{test_customer.id}",
        data={"document_type": "passport"},
        files={"file": ("passport_v2.pdf", BytesIO(pdf_content_2), "application/pdf")},
        headers=admin_auth_headers,
    )
    assert response2.status_code in [200, 201]
    second_url = response2.json()["file_url"]

    # URLs should be different
    if response1.status_code in [200, 201] and response2.status_code in [200, 201]:
        assert first_url != second_url
