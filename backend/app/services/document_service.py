import io
import json
import uuid
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.logging import logger
from app.schemas.report import ExtractedReportData, ReportUploadResponse
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService

UPLOAD_DIR = Path(settings.UPLOAD_DIR)
PROCESSED_DIR = Path("data/processed")

# Ensure storage directories exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


class DocumentService:
    """
    Stateless, in-memory document processing orchestrator for file validation,
    OCR extraction, field parsing, and streaming responses without disk storage.
    """

    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

    @classmethod
    def validate_file(cls, file: UploadFile, contents: bytes = b"") -> str:
        """
        Validates file extension, size limit, and integrity.
        Returns lowercase file extension if valid.
        """
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename missing in file upload request.",
            )

        raw_filename = file.filename
        if ".." in raw_filename or "/" in raw_filename or "\\" in raw_filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename containing directory traversal characters.",
            )

        clean_filename = Path(raw_filename).name
        ext = Path(clean_filename).suffix.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file format '{ext}'. Allowed formats: {', '.join(sorted(cls.ALLOWED_EXTENSIONS))}",
            )

        if contents:
            if len(contents) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Uploaded file is empty or corrupted.",
                )

            max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
            if len(contents) > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size ({len(contents) / (1024*1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
                )

        return ext

    @classmethod
    async def process_uploaded_report(cls, file: UploadFile) -> ReportUploadResponse:
        """
        Stateless in-memory document processing pipeline using io.BytesIO.
        Reads PDF/Image directly from RAM stream without saving files to disk.
        """
        contents = await file.read()
        ext = cls.validate_file(file, contents)

        report_id = f"rep_{uuid.uuid4().hex[:12]}"

        # Wrap uploaded bytes in an in-memory BytesIO stream
        input_stream = io.BytesIO(contents)

        extracted_lines: List[str] = []
        doc_type = "UNKNOWN"

        # 1. Detect Document Type & Extract Text from RAM Stream
        if ext == ".pdf":
            try:
                # Read PDF directly from io.BytesIO memory stream
                doc = fitz.open(stream=input_stream.getvalue(), filetype="pdf")
                if len(doc) == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Corrupted PDF document containing 0 pages.",
                    )

                # Check if Digital PDF by examining text layer
                digital_text = ""
                for page in doc:
                    digital_text += page.get_text("text")

                if len(digital_text.strip()) > 50:
                    doc_type = "DIGITAL_PDF"
                    extracted_lines = []
                    for page in doc:
                        page_lines = OCRService.extract_layout_sorted_lines(page)
                        extracted_lines.extend(page_lines)
                    logger.info(
                        f"Report [{report_id}] identified as DIGITAL_PDF. Extracted {len(extracted_lines)} layout-sorted lines in-memory."
                    )
                else:
                    doc_type = "SCANNED_PDF"
                    logger.info(
                        f"Report [{report_id}] identified as SCANNED_PDF. Rendering pages in-memory for OCR pipeline."
                    )
                    for page_idx in range(len(doc)):
                        img_bytes = OCRService.render_pdf_page_to_bytes(doc, page_idx)
                        ocr_lines, _ = OCRService.extract_text_from_image(img_bytes)
                        extracted_lines.extend(ocr_lines)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error(
                    f"Error reading PDF document '{file.filename}': {exc}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Corrupted or invalid PDF file: {exc}",
                )
        else:  # Image file (.jpg, .jpeg, .png)
            doc_type = "IMAGE"
            logger.info(
                f"Report [{report_id}] identified as IMAGE ({ext}). Running in-memory OCR preprocessing."
            )
            try:
                ocr_lines, _ = OCRService.extract_text_from_image(
                    input_stream.getvalue()
                )
                extracted_lines = ocr_lines
            except Exception as exc:
                logger.error(
                    f"OCR processing failed for image '{file.filename}': {exc}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Failed to execute OCR on uploaded image: {exc}",
                )

        if not extracted_lines:
            logger.warning(f"No text extracted from report [{report_id}].")

        # 2. Parse Fields using Deterministic Parser
        parsed_data = ParserService.parse_document_text(report_id, extracted_lines)

        # 3. Phase 2 Normalization & Classification
        normalized_data = NormalizationService.normalize_extracted_report(parsed_data)

        # Determine response status
        response_status = (
            "VALIDATED_WITH_WARNINGS" if normalized_data.warnings else "VALIDATED"
        )

        return ReportUploadResponse(
            report_id=report_id, status=response_status, data=normalized_data
        )

    @classmethod
    async def process_pdf_to_streaming_response(
        cls, file: UploadFile, output_filename: str = "processed_output.pdf"
    ) -> StreamingResponse:
        """
        Completely self-contained, stateless in-memory function that reads an uploaded PDF
        directly from an io.BytesIO memory stream and streams the output directly back
        as a StreamingResponse without storing anything to disk.
        """
        contents = await file.read()
        cls.validate_file(file, contents)

        # Read uploaded PDF directly from memory stream
        input_stream = io.BytesIO(contents)

        # Open PyMuPDF document directly from in-memory BytesIO buffer
        doc = fitz.open(stream=input_stream.getvalue(), filetype="pdf")
        if len(doc) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corrupted PDF document containing 0 pages.",
            )

        # Perform in-memory processing on PDF document
        output_buffer = io.BytesIO()
        output_bytes = doc.tobytes(garbage=4, deflate=True)
        output_buffer.write(output_bytes)
        output_buffer.seek(0)

        # Stream generated output directly back as StreamingResponse
        return StreamingResponse(
            output_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"},
        )
