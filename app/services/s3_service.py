import boto3
import logging
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    def __init__(self):
        """Initialize S3 client with AWS credentials from environment"""
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION,
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        self.region = settings.AWS_S3_REGION

    def generate_s3_key(self, customer_id: int, filename: str) -> str:
        """
        Generate S3 object key with millisecond timestamp to ensure uniqueness
        Format: customer_proofs/{customer_id}/{timestamp_ms}_{filename}

        Args:
            customer_id: Customer ID
            filename: Already-sanitized filename (must come from FileValidator)

        Returns:
            S3 object key
        """
        timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
        return f"customer_proofs/{customer_id}/{timestamp_ms}_{filename}"

    def generate_s3_url(self, s3_key: str) -> str:
        """Generate public S3 URL for the uploaded file"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"

    def upload_file(
        self, file_content: bytes, filename: str, customer_id: int, content_type: str
    ) -> str:
        """
        Upload file to S3 and return the public URL

        Args:
            file_content: File bytes to upload
            filename: Sanitized filename (must come from FileValidator)
            customer_id: Customer ID for path organization
            content_type: MIME type (must come from FileValidator)

        Returns:
            Public S3 URL of uploaded file

        Raises:
            ValueError: If URL extraction fails
            ClientError: If S3 upload fails (boto3)
        """
        from botocore.exceptions import ClientError

        try:
            s3_key = self.generate_s3_key(customer_id, filename)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
            )

            s3_url = self.generate_s3_url(s3_key)
            logger.info(
                f"Successfully uploaded file to S3. Customer: {customer_id}, Key: {s3_key}"
            )
            return s3_url

        except ClientError as e:
            logger.error(f"AWS S3 upload error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise

    def delete_file(self, s3_key: str) -> bool:
        """
        Delete file from S3

        Args:
            s3_key: S3 object key to delete

        Returns:
            True if successful

        Raises:
            ClientError: If S3 delete fails (boto3)
        """
        from botocore.exceptions import ClientError

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            logger.info(f"Successfully deleted file from S3. Key: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"AWS S3 delete error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise

    def get_s3_key_from_url(self, s3_url: str) -> str:
        """
        Extract S3 key from public URL

        Args:
            s3_url: Full S3 public URL

        Returns:
            S3 object key

        Raises:
            ValueError: If URL is not from expected bucket
        """
        prefix = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/"
        if not s3_url.startswith(prefix):
            raise ValueError(f"URL not from expected bucket: {s3_url}")
        return s3_url[len(prefix) :]
