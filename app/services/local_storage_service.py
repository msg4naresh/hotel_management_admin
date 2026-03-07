"""Local file system storage service — drop-in replacement for S3Service in dev."""

import logging
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class LocalStorageService:
    """Store uploaded files on the local filesystem and serve them via a static URL."""

    def __init__(self):
        self.upload_dir = Path(settings.LOCAL_UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        # Base URL used to build the public URL for stored files
        self.base_url = settings.LOCAL_UPLOAD_BASE_URL.rstrip("/")

    # ---- public API (mirrors S3Service) ----

    def generate_s3_key(self, customer_id: int, filename: str) -> str:
        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        return f"customer_proofs/{customer_id}/{timestamp_ms}_{filename}"

    def generate_s3_url(self, s3_key: str) -> str:
        return f"{self.base_url}/{s3_key}"

    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        customer_id: int,
        content_type: str,
    ) -> str:
        key = self.generate_s3_key(customer_id, filename)
        dest = self.upload_dir / key
        dest.parent.mkdir(parents=True, exist_ok=True)

        dest.write_bytes(file_content)
        url = self.generate_s3_url(key)
        logger.info(
            "Saved file locally. Customer: %s, Path: %s", customer_id, dest
        )
        return url

    def delete_file(self, s3_key: str) -> bool:
        target = self.upload_dir / s3_key
        try:
            target.unlink(missing_ok=True)
            logger.info("Deleted local file: %s", target)
            return True
        except Exception as e:
            logger.error("Failed to delete local file %s: %s", target, e)
            raise

    def get_s3_key_from_url(self, url: str) -> str:
        prefix = f"{self.base_url}/"
        if url.startswith(prefix):
            return url[len(prefix):]
        raise ValueError(f"URL not from expected local storage: {url}")
