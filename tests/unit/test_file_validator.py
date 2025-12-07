"""Tests for file validation"""

import pytest

from app.services import file_validator


# Core validation tests
def test_validates_pdf():
    safe_name, ext, content_type = file_validator.validate_file("document.pdf", b"%PDF-1.4")
    assert ext == "pdf"
    assert content_type == "application/pdf"


def test_validates_jpeg():
    safe_name, ext, content_type = file_validator.validate_file("photo.jpg", b"\xff\xd8\xff\xe0\x00\x10JFIF")
    assert ext == "jpg"
    assert content_type == "image/jpeg"


def test_validates_png():
    safe_name, ext, content_type = file_validator.validate_file("image.png", b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    assert ext == "png"
    assert content_type == "image/png"


# Security tests
def test_sanitizes_path_traversal():
    safe_name, _, _ = file_validator.validate_file("../../../etc/passwd.pdf", b"%PDF-1.4")
    assert safe_name == "passwd.pdf"
    assert ".." not in safe_name


def test_sanitizes_unsafe_characters():
    safe_name, _, _ = file_validator.validate_file("my@file#2025.pdf", b"%PDF-1.4")
    assert "@" not in safe_name
    assert "#" not in safe_name


def test_strips_absolute_paths():
    safe_name, _, _ = file_validator.validate_file("/home/user/documents/passport.pdf", b"%PDF-1.4")
    assert safe_name == "passport.pdf"
    assert "/" not in safe_name


# Rejection tests
def test_rejects_empty_filename():
    with pytest.raises(ValueError, match="Filename is required"):
        file_validator.validate_file("", b"%PDF-1.4")


def test_rejects_missing_extension():
    with pytest.raises(ValueError, match="Filename must include extension"):
        file_validator.validate_file("passport", b"%PDF-1.4")


def test_rejects_disallowed_extension():
    with pytest.raises(ValueError, match="File type not allowed"):
        file_validator.validate_file("malware.exe", b"MZ\x90")


def test_rejects_mime_mismatch():
    with pytest.raises(ValueError, match="File content does not match declared type"):
        file_validator.validate_file("fake.pdf", b"MZ\x90\x00")


def test_rejects_oversized_file(monkeypatch):
    from app.core import config

    monkeypatch.setattr(config.settings, "MAX_FILE_SIZE", 100)

    with pytest.raises(ValueError, match="File exceeds maximum size"):
        file_validator.validate_file("big.pdf", b"%PDF-1.4" + b"x" * 200)
