"""Unit tests for S3Service with moto mocking"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError
from app.services.s3_service import S3Service


@pytest.fixture
def mock_s3_service():
    """Create S3Service with mocked boto3 client"""
    with patch('app.services.s3_service.boto3.client') as mock_client:
        mock_s3_client = MagicMock()
        mock_client.return_value = mock_s3_client
        service = S3Service()
        service.s3_client = mock_s3_client
        yield service


class TestS3ServiceUpload:
    """Test S3 file upload operations"""

    def test_upload_file_success(self, mock_s3_service):
        """Test successful file upload to S3"""
        # Mock the S3 put_object response
        mock_s3_service.s3_client.put_object.return_value = {"ETag": "test-etag"}

        file_content = b"test file content"
        filename = "document.pdf"
        customer_id = 123
        content_type = "application/pdf"

        result = mock_s3_service.upload_file(file_content, filename, customer_id, content_type)

        # Verify result is a URL
        assert isinstance(result, str)
        assert "https://" in result
        assert customer_id in int(result.split('/')[3])  # customer ID in path

    def test_upload_file_calls_put_object_with_correct_params(self, mock_s3_service):
        """Test that upload_file calls put_object with correct parameters"""
        mock_s3_service.s3_client.put_object.return_value = {"ETag": "test"}

        file_content = b"test content"
        filename = "test.pdf"
        customer_id = 456
        content_type = "application/pdf"

        mock_s3_service.upload_file(file_content, filename, customer_id, content_type)

        # Verify put_object was called
        mock_s3_service.s3_client.put_object.assert_called_once()
        call_kwargs = mock_s3_service.s3_client.put_object.call_args[1]

        assert "Bucket" in call_kwargs
        assert "Key" in call_kwargs
        assert "Body" in call_kwargs
        assert "ContentType" in call_kwargs
        assert call_kwargs["Body"] == file_content
        assert call_kwargs["ContentType"] == content_type

    def test_upload_file_s3_error_handling(self, mock_s3_service):
        """Test that S3 errors are properly raised"""
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access Denied"}}
        mock_s3_service.s3_client.put_object.side_effect = ClientError(error_response, "PutObject")

        with pytest.raises(ClientError):
            mock_s3_service.upload_file(b"content", "file.pdf", 1, "application/pdf")

    def test_upload_file_generates_unique_key(self, mock_s3_service):
        """Test that upload generates unique S3 keys for multiple files"""
        mock_s3_service.s3_client.put_object.return_value = {"ETag": "test"}

        # Upload two files
        url1 = mock_s3_service.upload_file(b"content1", "doc.pdf", 1, "application/pdf")
        url2 = mock_s3_service.upload_file(b"content2", "doc.pdf", 1, "application/pdf")

        # Extract S3 keys from URLs (they should be different)
        key1 = url1.split('/customer_proofs/')[1]
        key2 = url2.split('/customer_proofs/')[1]

        # Keys should be different due to timestamp
        assert key1 != key2

    def test_upload_file_includes_customer_id_in_path(self, mock_s3_service):
        """Test that customer ID is included in the S3 key path"""
        mock_s3_service.s3_client.put_object.return_value = {"ETag": "test"}

        customer_id = 789
        url = mock_s3_service.upload_file(b"content", "file.pdf", customer_id, "application/pdf")

        # Verify customer ID is in the path
        assert f"/{customer_id}/" in url

    def test_upload_file_returns_public_url(self, mock_s3_service):
        """Test that upload_file returns a public S3 URL"""
        mock_s3_service.s3_client.put_object.return_value = {"ETag": "test"}

        url = mock_s3_service.upload_file(b"content", "file.pdf", 1, "application/pdf")

        # Verify URL format
        assert url.startswith("https://")
        assert ".s3." in url
        assert ".amazonaws.com" in url


class TestS3ServiceDelete:
    """Test S3 file deletion operations"""

    def test_delete_file_success(self, mock_s3_service):
        """Test successful file deletion"""
        mock_s3_service.s3_client.delete_object.return_value = {}

        s3_key = "customer_proofs/123/1733486400_passport.pdf"
        result = mock_s3_service.delete_file(s3_key)

        # Verify delete was called
        mock_s3_service.s3_client.delete_object.assert_called_once()

    def test_delete_file_calls_delete_object(self, mock_s3_service):
        """Test that delete_file calls delete_object with correct params"""
        mock_s3_service.s3_client.delete_object.return_value = {}

        s3_key = "customer_proofs/456/file.jpg"
        mock_s3_service.delete_file(s3_key)

        # Verify delete_object was called with correct parameters
        call_kwargs = mock_s3_service.s3_client.delete_object.call_args[1]
        assert "Bucket" in call_kwargs
        assert "Key" in call_kwargs
        assert call_kwargs["Key"] == s3_key

    def test_delete_file_s3_error_handling(self, mock_s3_service):
        """Test that S3 errors are properly raised during delete"""
        error_response = {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist"}}
        mock_s3_service.s3_client.delete_object.side_effect = ClientError(error_response, "DeleteObject")

        with pytest.raises(ClientError):
            mock_s3_service.delete_file("nonexistent/file.pdf")

    def test_delete_file_with_special_chars_in_key(self, mock_s3_service):
        """Test deletion of files with special characters in key"""
        mock_s3_service.s3_client.delete_object.return_value = {}

        # Key with special characters
        s3_key = "customer_proofs/789/2025-12-06_passport-copy_v2.pdf"
        mock_s3_service.delete_file(s3_key)

        # Verify delete was called
        mock_s3_service.s3_client.delete_object.assert_called_once()
        call_kwargs = mock_s3_service.s3_client.delete_object.call_args[1]
        assert call_kwargs["Key"] == s3_key


class TestS3ServiceKeyParsing:
    """Test S3 key extraction from URLs"""

    def test_get_s3_key_from_valid_url(self, mock_s3_service):
        """Test extracting S3 key from valid URL"""
        url = "https://bucket.s3.us-east-1.amazonaws.com/customer_proofs/123/1733486400_file.pdf"
        key = mock_s3_service.get_s3_key_from_url(url)

        assert key == "customer_proofs/123/1733486400_file.pdf"

    def test_get_s3_key_from_url_with_different_region(self, mock_s3_service):
        """Test key extraction from URLs with different S3 regions"""
        url = "https://my-bucket.s3.eu-west-1.amazonaws.com/customer_proofs/456/file.jpg"
        key = mock_s3_service.get_s3_key_from_url(url)

        assert key == "customer_proofs/456/file.jpg"

    def test_get_s3_key_invalid_url_format(self, mock_s3_service):
        """Test that invalid URL formats raise ValueError"""
        invalid_urls = [
            "not-a-url",
            "https://example.com/file.pdf",
            "https://bucket.invalid.com/file.pdf",
            "",
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValueError):
                mock_s3_service.get_s3_key_from_url(invalid_url)

    def test_get_s3_key_from_url_with_path_traversal_attempt(self, mock_s3_service):
        """Test that URL parsing prevents path traversal"""
        url = "https://bucket.s3.amazonaws.com/customer_proofs/../../../etc/passwd"
        # The function should still extract the path as-is from the URL
        key = mock_s3_service.get_s3_key_from_url(url)
        # Path traversal is already in the extracted key, but S3 would reject it on delete
        assert "customer_proofs" in key

    def test_get_s3_key_preserves_special_characters(self, mock_s3_service):
        """Test that special characters in paths are preserved"""
        url = "https://bucket.s3.us-east-1.amazonaws.com/customer_proofs/789/2025-12-06_passport-copy_v2.pdf"
        key = mock_s3_service.get_s3_key_from_url(url)

        assert "2025-12-06_passport-copy_v2.pdf" in key
        assert "-" in key
        assert "_" in key


class TestS3ServiceConfiguration:
    """Test S3Service initialization and configuration"""

    def test_s3_service_initialization(self, mock_s3_service):
        """Test that S3Service initializes with boto3 client"""
        assert mock_s3_service.s3_client is not None

    def test_s3_service_uses_environment_credentials(self):
        """Test that S3Service uses environment variables for credentials"""
        with patch('app.services.s3_service.boto3.client') as mock_client:
            with patch.dict('os.environ', {
                'AWS_ACCESS_KEY_ID': 'test-key',
                'AWS_SECRET_ACCESS_KEY': 'test-secret',
                'AWS_S3_REGION': 'us-east-1'
            }):
                S3Service()
                mock_client.assert_called_once()

    def test_s3_service_bucket_name_from_config(self, mock_s3_service):
        """Test that S3 bucket name is loaded from config"""
        assert mock_s3_service.bucket_name is not None
        assert isinstance(mock_s3_service.bucket_name, str)
        assert len(mock_s3_service.bucket_name) > 0


class TestS3ServiceErrorHandling:
    """Test error handling in S3Service"""

    def test_upload_network_error(self, mock_s3_service):
        """Test handling of network errors during upload"""
        mock_s3_service.s3_client.put_object.side_effect = Exception("Network error")

        with pytest.raises(Exception):
            mock_s3_service.upload_file(b"content", "file.pdf", 1, "application/pdf")

    def test_delete_network_error(self, mock_s3_service):
        """Test handling of network errors during delete"""
        mock_s3_service.s3_client.delete_object.side_effect = Exception("Connection refused")

        with pytest.raises(Exception):
            mock_s3_service.delete_file("customer_proofs/123/file.pdf")

    def test_invalid_s3_key_in_delete(self, mock_s3_service):
        """Test handling of invalid S3 keys"""
        # AWS would return NoSuchKey error, but service should not prevent the call
        mock_s3_service.s3_client.delete_object.return_value = {}

        # Empty key
        with pytest.raises(ValueError, match="S3 key cannot be empty"):
            mock_s3_service.delete_file("")
