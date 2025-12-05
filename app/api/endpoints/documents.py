from functools import lru_cache
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from botocore.exceptions import ClientError

from app.models.users import UserDB
from app.models.customer import CustomerDB
from app.models.schemas.file_upload import FileUploadResponse, DocumentDeleteResponse
from app.api.dependencies.auth_deps import get_current_user
from app.db.base_db import get_session
from app.services.s3_service import S3Service
from app.services.file_validator import FileValidator
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_s3_service() -> S3Service:
    """Get or create singleton S3Service instance"""
    return S3Service()


def get_file_validator() -> FileValidator:
    """Create FileValidator with configured max file size"""
    return FileValidator(max_file_size=settings.MAX_FILE_SIZE)


@router.post(
    "/upload-document/{customer_id}",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload customer proof document",
    description="Upload a proof document (PDF/JPG) for a customer. Admin only.",
)
async def upload_document(
    customer_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserDB = Depends(get_current_user),
    validator: FileValidator = Depends(get_file_validator),
):
    """
    Upload a document for a customer to S3 and store the URL in the database.

    - **customer_id**: ID of the customer
    - **document_type**: Type of document (e.g., "passport", "license")
    - **file**: The document file to upload (PDF or JPG)
    """
    s3_service = get_s3_service()

    try:
        # Read file content
        file_content = await file.read()

        # Validate file (will raise ValueError with specific reason)
        safe_filename, extension, content_type = validator.validate_file(
            file.filename or "document", file_content
        )

        # Get session and verify customer exists with row-level lock
        with get_session() as session:
            customer = (
                session.query(CustomerDB)
                .filter(CustomerDB.id == customer_id)
                .with_for_update()  # Pessimistic locking to prevent race conditions
                .first()
            )

            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer with ID {customer_id} not found",
                )

            # Upload to S3
            try:
                s3_url = s3_service.upload_file(
                    file_content, safe_filename, customer_id, content_type
                )
            except ClientError as e:
                logger.error(f"AWS S3 error uploading document: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="File upload service temporarily unavailable",
                )

            # Update customer record with file URL (atomic with lock)
            customer.proof_image_url = s3_url
            customer.proof_image_filename = safe_filename
            session.commit()

            logger.info(
                f"Document uploaded successfully. Customer: {customer_id}, File: {safe_filename}"
            )

            return FileUploadResponse(
                customer_id=customer_id,
                file_url=s3_url,
                file_name=safe_filename,
                uploaded_at=customer.uploaded_at,
                document_type=document_type,
            )

    except HTTPException:
        raise  # Re-raise HTTP errors
    except ValueError as e:
        # File validation errors
        logger.warning(f"File validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception(f"Unexpected error uploading document for customer {customer_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.delete(
    "/documents/{customer_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete customer document",
    description="Delete the proof document for a customer. Admin only.",
)
async def delete_document(
    customer_id: int,
    current_user: UserDB = Depends(get_current_user),
):
    """
    Delete the proof document for a customer from S3 and database.

    - **customer_id**: ID of the customer whose document to delete
    """
    s3_service = get_s3_service()

    try:
        with get_session() as session:
            # Get customer with row-level lock to prevent concurrent modifications
            customer = (
                session.query(CustomerDB)
                .filter(CustomerDB.id == customer_id)
                .with_for_update()  # Pessimistic locking
                .first()
            )

            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer with ID {customer_id} not found",
                )

            if not customer.proof_image_url:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No document found for customer {customer_id}",
                )

            # Extract S3 key from URL and delete from S3
            try:
                s3_key = s3_service.get_s3_key_from_url(customer.proof_image_url)
            except ValueError as e:
                logger.error(f"Invalid S3 URL for customer {customer_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid stored document URL",
                )

            # Delete from S3
            try:
                s3_service.delete_file(s3_key)
            except ClientError as e:
                logger.error(f"AWS S3 error deleting document: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="File deletion service temporarily unavailable",
                )

            # Clear customer record (atomic with lock)
            customer.proof_image_url = None
            customer.proof_image_filename = None
            session.commit()

            logger.info(
                f"Document deleted successfully. Customer: {customer_id}, Key: {s3_key}"
            )

            return DocumentDeleteResponse(
                success=True,
                message="Document deleted successfully",
                customer_id=customer_id,
            )

    except HTTPException:
        raise  # Re-raise HTTP errors
    except Exception as e:
        logger.exception(f"Unexpected error deleting document for customer {customer_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )
