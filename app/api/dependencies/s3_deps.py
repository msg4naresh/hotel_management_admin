import logging

from app.core.config import settings
from app.services.local_storage_service import LocalStorageService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)

# Union type so either service can be used interchangeably
StorageService = S3Service | LocalStorageService


def get_s3_service() -> StorageService:
    """Return the appropriate storage service based on STORAGE_MODE config."""
    mode = settings.RESOLVED_STORAGE_MODE
    if mode == "local":
        logger.debug("Using local file storage")
        return LocalStorageService()
    logger.debug("Using AWS S3 storage")
    return S3Service()
