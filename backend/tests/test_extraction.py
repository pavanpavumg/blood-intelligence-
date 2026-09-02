import pytest
import fitz
from fastapi import UploadFile, HTTPException
from io import BytesIO

from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService

def test_document_validation():
    # Valid extension
    file_valid = UploadFile(filename="report.pdf", file=BytesIO(b"dummy pdf content"))
    ext = DocumentService.validate_file(file_valid)
    assert ext == ".pdf"
    
    # Invalid extension
    file_invalid = UploadFile(filename="report.exe", file=BytesIO(b"executable"))
    with pytest.raises(HTTPException) as exc_info:
        DocumentService.validate_file(file_invalid)
    assert exc_info.value.status_code in (400, 415)
    assert "Unsupported file" in exc_info.value.detail

def test_pdf_extraction_digital(sample_pdf_bytes: bytes):
    doc = fitz.open(stream=sample_pdf_bytes, filetype="pdf")
    assert len(doc) == 1
    
    text = doc[0].get_text("text")
    assert "Quest Diagnostics" in text
    assert "Fasting Blood Glucose" in text
    assert "95 mg/dL" in text

def test_image_preprocessing(sample_image_bytes: bytes):
    processed = OCRService.preprocess_image(sample_image_bytes)
    assert processed is not None
    assert processed.ndim == 2  # Grayscale thresholded matrix
