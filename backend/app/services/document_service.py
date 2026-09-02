import json
import uuid
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile, HTTPException, status

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
    Document processing orchestrator for file validation, document type detection,
    OCR extraction, field parsing, and JSON persistence.
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
        Orchestrates full report upload pipeline.
        """
        contents = await file.read()
        ext = cls.validate_file(file, contents)

        report_id = f"rep_{uuid.uuid4().hex[:12]}"
        assert file.filename is not None
        safe_filename = Path(file.filename).name
        saved_file_path = UPLOAD_DIR / f"{report_id}_{safe_filename}"

        # 1. Store original file safely
        with open(saved_file_path, "wb") as f:
            f.write(contents)
        logger.info(f"Saved raw report upload to '{saved_file_path}'.")

        extracted_lines: List[str] = []
        doc_type = "UNKNOWN"

        # 2. Detect Document Type & Extract Text
        if ext == ".pdf":
            try:
                doc = fitz.open(stream=contents, filetype="pdf")
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
                        f"Report [{report_id}] identified as DIGITAL_PDF. Extracted {len(extracted_lines)} layout-sorted lines via PyMuPDF."
                    )
                else:
                    doc_type = "SCANNED_PDF"
                    logger.info(
                        f"Report [{report_id}] identified as SCANNED_PDF. Rendering pages for OCR pipeline."
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
                f"Report [{report_id}] identified as IMAGE ({ext}). Running OpenCV & OCR preprocessing."
            )
            try:
                ocr_lines, _ = OCRService.extract_text_from_image(contents)
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

        # 3. Parse Fields using Deterministic Parser
        parsed_data = ParserService.parse_document_text(report_id, extracted_lines)

        # 4. Phase 2 Normalization & Classification
        normalized_data = NormalizationService.normalize_extracted_report(parsed_data)

        # 5. Store processed JSON result
        processed_json_path = PROCESSED_DIR / f"{report_id}.json"
        with open(processed_json_path, "w", encoding="utf-8") as f:
            f.write(normalized_data.model_dump_json(indent=2))
        logger.info(f"Saved processed JSON payload to '{processed_json_path}'.")

        # Determine response status
        response_status = (
            "VALIDATED_WITH_WARNINGS" if normalized_data.warnings else "VALIDATED"
        )

        return ReportUploadResponse(
            report_id=report_id, status=response_status, data=normalized_data
        )
