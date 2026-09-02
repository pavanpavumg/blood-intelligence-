import pytest
from fastapi import HTTPException
from app.services.document_service import DocumentService
from app.core.config import settings

class DummyUploadFile:
    def __init__(self, filename: str):
        self.filename = filename

def test_validate_file_valid_extensions():
    for ext in [".pdf", ".png", ".jpg", ".jpeg", ".PDF", ".PNG"]:
        file = DummyUploadFile(f"report{ext}")
        contents = b"0123456789ABCDEF"
        assert DocumentService.validate_file(file, contents) == ext.lower()

def test_validate_file_invalid_extension():
    file = DummyUploadFile("malicious_script.exe")
    contents = b"0123456789ABCDEF"
    with pytest.raises(HTTPException) as exc_info:
        DocumentService.validate_file(file, contents)
    assert exc_info.value.status_code == 415
    assert "Unsupported file format" in exc_info.value.detail

def test_validate_file_empty_contents():
    file = DummyUploadFile("report.pdf")
    contents = b"123" # Less than 10 bytes
    with pytest.raises(HTTPException) as exc_info:
        DocumentService.validate_file(file, contents)
    assert exc_info.value.status_code == 400
    assert "empty or corrupted" in exc_info.value.detail

def test_validate_file_oversized():
    file = DummyUploadFile("large_report.pdf")
    # Exceed max size by 1 byte
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    oversized_bytes = b"0" * (max_bytes + 1)
    with pytest.raises(HTTPException) as exc_info:
        DocumentService.validate_file(file, oversized_bytes)
    assert exc_info.value.status_code == 413
    assert "exceeds maximum allowed limit" in exc_info.value.detail

def test_validate_file_path_traversal():
    file = DummyUploadFile("../../etc/passwd.pdf")
    contents = b"0123456789ABCDEF"
    with pytest.raises(HTTPException) as exc_info:
        DocumentService.validate_file(file, contents)
    assert exc_info.value.status_code == 400
    assert "traversal" in exc_info.value.detail
