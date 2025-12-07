from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from botocore.exceptions import ClientError
from datetime import datetime, timezone

from app.models.users import UserDB
from app.models.customer import CustomerDB
from app.models.schemas.file_upload import FileUploadResponse, DocumentDeleteResponse
from app.api.dependencies.auth_deps import get_current_user
from app.api.dependencies.s3_deps import get_s3_service
from app.db.base_db import get_session
from app.services.s3_service import S3Service
from app.services import file_validator
from app.services.s3_cleanup import delete_old_file_best_effort
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


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
    s3_service: S3Service = Depends(get_s3_service),
):
    """
    Upload a document for a customer to S3 and store the URL in the database.

    - **customer_id**: ID of the customer
    - **document_type**: Type of document (e.g., "passport", "license")
    - **file**: The document file to upload (PDF or JPG)
    """

    try:
        # 1. Read and validate file content
        file_content = await file.read()
        safe_filename, extension, content_type = file_validator.validate_file(
            file.filename or "document", file_content
        )

        # 2. Single transaction: validate customer, upload file, update database
        old_s3_key = None
        with get_session() as session:
            # Lock customer row for update
            customer = (
                session.query(CustomerDB)
                .filter(CustomerDB.id == customer_id)
                .with_for_update()
                .first()
            )

            if not customer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Customer with ID {customer_id} not found",
                )

            # Track old file for cleanup (best effort after transaction)
            if customer.proof_image_url:
                try:
                    old_s3_key = s3_service.get_s3_key_from_url(customer.proof_image_url)
                except ValueError:
                    logger.warning(f"Invalid old S3 URL: {customer.proof_image_url}")

            # Upload new file to S3 (within transaction lock)
            try:
                new_s3_url = s3_service.upload_file(
                    file_content, safe_filename, customer_id, content_type
                )
            except ClientError as e:
                logger.error(f"AWS S3 error uploading document: {e}")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="File upload service temporarily unavailable",
                )

            # Update customer record
            customer.proof_image_url = new_s3_url
            customer.proof_image_filename = safe_filename
            customer.uploaded_at = datetime.now(timezone.utc)
            uploaded_at = customer.uploaded_at

            session.commit()

        # 3. Best-effort cleanup of old file (after successful commit)
        if old_s3_key:
            delete_old_file_best_effort(s3_service, old_s3_key)

        logger.info(
            f"Document uploaded successfully. Customer: {customer_id}, File: {safe_filename}"
        )

        return FileUploadResponse(
            customer_id=customer_id,
            file_url=new_s3_url,
            file_name=safe_filename,
            uploaded_at=uploaded_at,
            document_type=document_type,
        )

    except HTTPException:
        raise
    except ValueError as e:
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
    s3_service: S3Service = Depends(get_s3_service),
):
    """
    Delete the proof document for a customer from S3 and database.

    - **customer_id**: ID of the customer whose document to delete
    """

    try:
        # 1. Single transaction: get customer, extract S3 key, clear record
        s3_key = None
        with get_session() as session:
            customer = (
                session.query(CustomerDB)
                .filter(CustomerDB.id == customer_id)
                .with_for_update()
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

            # Extract S3 key while holding lock
            try:
                s3_key = s3_service.get_s3_key_from_url(customer.proof_image_url)
            except ValueError as e:
                logger.error(f"Invalid S3 URL for customer {customer_id}: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid stored document URL",
                )

            # Clear customer record
            customer.proof_image_url = None
            customer.proof_image_filename = None
            session.commit()

        # 2. Best-effort cleanup (after successful commit)
        if s3_key:
            delete_old_file_best_effort(s3_service, s3_key)

        logger.info(
            f"Document deleted successfully. Customer: {customer_id}, Key: {s3_key}"
        )

        return DocumentDeleteResponse(
            success=True,
            message="Document deleted successfully",
            customer_id=customer_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error deleting document for customer {customer_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )