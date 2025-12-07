"""Simple best-effort S3 file cleanup (no queues, no retries, no complexity)"""

import logging

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def delete_old_file_best_effort(s3_service, s3_key: str) -> None:
    """
    Delete old S3 file. Log failures but don't block requests.

    This is intentionally simple - S3 delete operations are:
    - Fast (~100ms)
    - Idempotent (safe to retry)
    - Rare to fail with proper credentials

    If cleanup fails, it's logged for manual review. No queues, no retries,
    no background workers needed for this scale.
    """
    try:
        s3_service.delete_file(s3_key)
        logger.info(f"Deleted old file: {s3_key}")
    except ClientError as e:
        # Log and move on - S3 cleanup failures shouldn't block uploads
        logger.warning(f"Failed to delete old file {s3_key}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting {s3_key}: {e}")
