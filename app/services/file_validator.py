import re
from pathlib import Path
import magic
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """Centralized file validation service"""

    # Single source of truth for allowed file types
    ALLOWED_FILE_TYPES = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    ALLOWED_EXTENSIONS = set(ALLOWED_FILE_TYPES.keys())
    ALLOWED_MIME_TYPES = set(ALLOWED_FILE_TYPES.values())

    def __init__(self, max_file_size: int):
        self.max_file_size = max_file_size
        self.mime = magic.Magic(mime=True)

    @staticmethod
    def _extract_and_sanitize_filename(filename: str) -> str:
        """Extract basename and sanitize filename to prevent path traversal"""
        if not filename:
            raise ValueError("Filename is required")

        # Remove any path components
        safe_filename = Path(filename).name

        if not safe_filename:
            raise ValueError("Invalid filename")

        # Only allow alphanumeric, dash, underscore, and dot
        safe_filename = re.sub(r"[^\w\-.]", "_", safe_filename)

        if not safe_filename:
            raise ValueError("Filename contains no valid characters")

        return safe_filename

    @staticmethod
    def _extract_extension(filename: str) -> str:
        """Extract file extension safely"""
        if "." not in filename:
            raise ValueError("Filename must include extension")

        extension = filename.lower().rsplit(".", 1)[-1]

        if not extension or len(extension) > 10:
            raise ValueError("Invalid file extension")

        return extension

    def validate_file(
        self, filename: str, content: bytes
    ) -> tuple[str, str, str]:
        """
        Validate file and return (sanitized_filename, extension, content_type)

        Args:
            filename: Original filename from upload
            content: File bytes

        Returns:
            Tuple of (sanitized_filename, extension, content_type)

        Raises:
            ValueError: If validation fails for any reason
        """
        # Validate file size
        if len(content) > self.max_file_size:
            raise ValueError(f"File exceeds maximum size of {self.max_file_size} bytes")

        # Sanitize filename
        safe_filename = self._extract_and_sanitize_filename(filename)

        # Extract and validate extension
        extension = self._extract_extension(safe_filename)

        if extension not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"File type not allowed. Supported: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Validate MIME type
        try:
            file_mime_type = self.mime.from_buffer(content)
            if file_mime_type not in self.ALLOWED_MIME_TYPES:
                raise ValueError(
                    f"File content does not match declared type. Got: {file_mime_type}"
                )
        except ValueError:
            raise  # Re-raise validation errors
        except Exception as e:
            logger.error(f"MIME type detection failed: {e}")
            raise ValueError("Unable to validate file content type")

        content_type = self.ALLOWED_FILE_TYPES[extension]

        return safe_filename, extension, content_type
