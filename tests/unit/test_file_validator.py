"""Unit tests for file_validator module"""
import pytest
from pathlib import Path
from app.services import file_validator


class TestFileValidatorFilenameHandling:
    """Test filename sanitization and path traversal prevention"""

    def test_valid_filename_sanitization(self):
        """Test that valid filenames are handled correctly"""
        safe_name, ext, content_type = file_validator.validate_file(
            "passport.pdf", b"%PDF-1.4"
        )
        assert safe_name == "passport.pdf"
        assert ext == "pdf"
        assert content_type == "application/pdf"

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are sanitized"""
        # Attempt to use ../ in filename - results in just filename
        safe_name, ext, content_type = file_validator.validate_file(
            "../../../etc/passwd.pdf", b"%PDF-1.4"
        )
        assert safe_name == "passwd.pdf"
        assert ".." not in safe_name

    def test_unsafe_characters_sanitized(self):
        """Test that unsafe characters in filenames are replaced with underscores"""
        safe_name, ext, content_type = file_validator.validate_file(
            "my@passport#2025.pdf", b"%PDF-1.4"
        )
        assert "@" not in safe_name
        assert "#" not in safe_name
        assert "_" in safe_name
        assert "pdf" in safe_name

    def test_empty_filename_rejected(self):
        """Test that empty filenames are rejected"""
        with pytest.raises(ValueError, match="Filename is required"):
            file_validator.validate_file("", b"%PDF-1.4")

    def test_filename_without_extension_rejected(self):
        """Test that filenames without extensions are rejected"""
        with pytest.raises(ValueError, match="Filename must include extension"):
            file_validator.validate_file("passport", b"%PDF-1.4")

    def test_absolute_path_filename_stripped_to_basename(self):
        """Test that absolute paths are stripped to basename only"""
        safe_name, ext, content_type = file_validator.validate_file(
            "/home/user/documents/passport.pdf", b"%PDF-1.4"
        )
        assert safe_name == "passport.pdf"
        assert "/" not in safe_name


class TestFileValidatorExtensions:
    """Test file extension validation"""

    def test_allowed_extensions(self):
        """Test that all allowed extensions are accepted"""
        allowed = ["pdf", "jpg", "jpeg", "png"]
        for ext in allowed:
            filename = f"document.{ext}"
            # Use minimal magic bytes for each format
            if ext == "pdf":
                content = b"%PDF-1.4"
            elif ext in ["jpg", "jpeg"]:
                content = b"\xff\xd8\xff"
            elif ext == "png":
                content = b"\x89PNG\r\n\x1a\n"

            safe_name, extracted_ext, content_type = file_validator.validate_file(filename, content)
            assert extracted_ext == ext or (ext in ["jpg", "jpeg"] and extracted_ext in ["jpg", "jpeg"])

    def test_disallowed_extension_rejected(self):
        """Test that disallowed extensions are rejected"""
        with pytest.raises(ValueError, match="File type not allowed"):
            file_validator.validate_file("malware.exe", b"MZ\x90")

    def test_extension_case_insensitive(self):
        """Test that extension matching is case-insensitive"""
        safe_name, ext, content_type = file_validator.validate_file(
            "PASSPORT.PDF", b"%PDF-1.4"
        )
        assert ext == "pdf"

    def test_invalid_extension_length_rejected(self):
        """Test that extensions longer than 10 chars are rejected"""
        with pytest.raises(ValueError, match="Invalid file extension"):
            file_validator.validate_file("document.verylongextension", b"%PDF-1.4")


class TestFileValidatorSizeValidation:
    """Test file size validation"""

    def test_valid_file_size(self):
        """Test that files within size limit are accepted"""
        # Create minimal PDF content (must be valid PDF)
        small_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n" + b"x" * 100
        safe_name, ext, content_type = file_validator.validate_file(
            "document.pdf", small_content
        )
        assert safe_name == "document.pdf"

    def test_file_exceeds_size_limit(self, monkeypatch):
        """Test that files exceeding size limit are rejected"""
        # Temporarily set a small max size for testing
        from app.core import config
        monkeypatch.setattr(config.settings, "MAX_FILE_SIZE", 100)

        oversized = b"%PDF-1.4" + b"x" * 200
        with pytest.raises(ValueError, match="File exceeds maximum size"):
            file_validator.validate_file("toobig.pdf", oversized)


class TestFileValidatorMIMEType:
    """Test MIME type detection and validation"""

    def test_pdf_mime_detection(self):
        """Test that PDF MIME type is correctly detected"""
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n"
        safe_name, ext, content_type = file_validator.validate_file(
            "document.pdf", pdf_content
        )
        assert content_type == "application/pdf"

    def test_jpeg_mime_detection(self):
        """Test that JPEG MIME type is correctly detected"""
        jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        safe_name, ext, content_type = file_validator.validate_file(
            "photo.jpg", jpeg_content
        )
        assert content_type == "image/jpeg"

    def test_png_mime_detection(self):
        """Test that PNG MIME type is correctly detected"""
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        safe_name, ext, content_type = file_validator.validate_file(
            "image.png", png_content
        )
        assert content_type == "image/png"

    def test_mime_mismatch_with_extension_rejected(self):
        """Test that file content not matching declared type is rejected"""
        # Try to pass executable content as PDF
        exe_content = b"MZ\x90\x00"  # Windows executable magic bytes
        with pytest.raises(ValueError, match="File content does not match declared type"):
            file_validator.validate_file("fake.pdf", exe_content)

    def test_invalid_mime_in_pdf_extension(self):
        """Test that non-PDF content with .pdf extension is rejected"""
        text_content = b"This is just text, not a PDF"
        with pytest.raises(ValueError, match="File content does not match declared type"):
            file_validator.validate_file("notpdf.pdf", text_content)


class TestFileValidatorIntegration:
    """Integration tests combining multiple validations"""

    def test_full_validation_flow_valid_pdf(self):
        """Test complete validation flow for valid PDF"""
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3\n1 0 obj"
        result = file_validator.validate_file("my_document.pdf", pdf_content)
        assert result[0] == "my_document.pdf"  # sanitized name
        assert result[1] == "pdf"  # extension
        assert result[2] == "application/pdf"  # content type

    def test_full_validation_flow_sanitized_filename(self):
        """Test that sanitized filename is returned for unsafe inputs"""
        pdf_content = b"%PDF-1.4\n%\xE2\xE3\xCF\xD3"
        result = file_validator.validate_file("my@unsafe#file$.pdf", pdf_content)
        assert "@" not in result[0]
        assert "#" not in result[0]
        assert "$" not in result[0]

    def test_validation_fails_fast_on_size(self, monkeypatch):
        """Test that size validation fails before MIME type check"""
        from app.core import config
        monkeypatch.setattr(config.settings, "MAX_FILE_SIZE", 10)

        oversized = b"x" * 100
        with pytest.raises(ValueError, match="File exceeds maximum size"):
            file_validator.validate_file("file.pdf", oversized)

    def test_validation_fails_on_invalid_extension(self):
        """Test that extension validation fails before MIME type check"""
        content = b"%PDF-1.4"
        with pytest.raises(ValueError, match="File type not allowed"):
            file_validator.validate_file("file.doc", content)


class TestExtensionExtraction:
    """Test the extract_extension function"""

    def test_extract_valid_extension(self):
        """Test extraction of valid extensions"""
        ext = file_validator.extract_extension("document.pdf")
        assert ext == "pdf"

    def test_extract_extension_case_insensitive(self):
        """Test that extracted extensions are lowercase"""
        ext = file_validator.extract_extension("document.PDF")
        assert ext == "pdf"

    def test_multiple_dots_uses_last_extension(self):
        """Test that extension is taken from last dot"""
        ext = file_validator.extract_extension("archive.tar.gz")
        assert ext == "gz"


class TestFilenameSanitization:
    """Test the sanitize_filename function"""

    def test_sanitize_removes_path_components(self):
        """Test that path components are removed"""
        result = file_validator.sanitize_filename("/path/to/file.pdf")
        assert result == "file.pdf"

    def test_sanitize_replaces_unsafe_chars(self):
        """Test that unsafe characters are replaced with underscore"""
        result = file_validator.sanitize_filename("file@2025#v2.pdf")
        assert "@" not in result
        assert "#" not in result
        assert "_" in result

    def test_sanitize_allows_safe_chars(self):
        """Test that safe characters are preserved"""
        result = file_validator.sanitize_filename("my-file_2025.pdf")
        assert result == "my-file_2025.pdf"
