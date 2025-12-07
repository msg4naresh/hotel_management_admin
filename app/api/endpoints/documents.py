import logging
from datetime import datetime, timezone

from botocore.exceptions import ClientError
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.api.dependencies.common import CurrentUserDep, S3ServiceDep, SessionDep
from app.models.customer import CustomerDB
from app.models.schemas.file_upload import DocumentDeleteResponse, FileUploadResponse
from app.services import file_validator
from app.services.s3_cleanup import delete_old_file_best_effort

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
    current_user: CurrentUserDep,
    s3_service: S3ServiceDep,
    session: SessionDep,
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload a document for a customer to S3 and store the URL in the database.

    - **customer_id**: ID of the customer
    - **document_type**: Type of document (e.g., "passport", "license")
    - **file**: The document file to upload (PDF or JPG)
    """

    # 1. Read and validate file content
    file_content = await file.read()
    try:
        safe_filename, extension, content_type = file_validator.validate_file(file.filename or "document", file_content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    from fastapi.concurrency import run_in_threadpool

    def _item_upload_sync():
        # 2. Single transaction: validate customer, upload file, update database
        old_s3_key = None

        # Lock customer row for update
        customer = session.query(CustomerDB).filter(CustomerDB.id == customer_id).with_for_update().first()

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
            new_s3_url = s3_service.upload_file(file_content, safe_filename, customer_id, content_type)
        except ClientError as e:
            logger.error(f"AWS S3 error uploading document: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="File upload service temporarily unavailable",
            ) from e

        # Update customer record
        customer.proof_image_url = new_s3_url
        customer.proof_image_filename = safe_filename
        customer.uploaded_at = datetime.now(timezone.utc)

        session.commit()

        # 3. Best-effort cleanup of old file (after successful commit)
        if old_s3_key:
            delete_old_file_best_effort(s3_service, old_s3_key)

        logger.info(f"Document uploaded successfully. Customer: {customer_id}, File: {safe_filename}")

        return FileUploadResponse(
            customer_id=customer_id,
            file_url=new_s3_url,
            file_name=safe_filename,
            uploaded_at=customer.uploaded_at,
            document_type=document_type,
        )

    return await run_in_threadpool(_item_upload_sync)


@router.delete(
    "/documents/{customer_id}",
    response_model=DocumentDeleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete customer document",
    description="Delete the proof document for a customer. Admin only.",
)
async def delete_document(
    customer_id: int,
    current_user: CurrentUserDep,
    s3_service: S3ServiceDep,
    session: SessionDep,
):
    """
    Delete the proof document for a customer from S3 and database.

    - **customer_id**: ID of the customer whose document to delete
    """

    from fastapi.concurrency import run_in_threadpool

    def _delete_document_sync():
        # 1. Single transaction: get customer, extract S3 key, clear record
        s3_key = None

        customer = session.query(CustomerDB).filter(CustomerDB.id == customer_id).with_for_update().first()

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
            ) from e

        # Clear customer record
        customer.proof_image_url = None
        customer.proof_image_filename = None
        session.commit()

        # 2. Best-effort cleanup (after successful commit)
        if s3_key:
            delete_old_file_best_effort(s3_service, s3_key)

        logger.info(f"Document deleted successfully. Customer: {customer_id}, Key: {s3_key}")

        return DocumentDeleteResponse(
            success=True,
            message="Document deleted successfully",
            customer_id=customer_id,
        )

    return await run_in_threadpool(_delete_document_sync)
