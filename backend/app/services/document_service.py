import asyncio
import io
import uuid
import pymupdf

from pathlib import Path
from typing import List

from fastapi import (
    UploadFile,
    HTTPException,
    status,
)

from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.core.logging import logger

from app.schemas.report import (
    ReportUploadResponse,
)

from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import (
    NormalizationService,
)


class DocumentService:
    """
    Stateless in-memory document processing service.

    Supports:
    - PDF files
    - JPG/JPEG files
    - PNG files
    - Digital PDF text extraction
    - Scanned PDF OCR (parallelized across a worker process pool)
    - Multi-page documents
    - In-memory processing
    - No permanent file storage
    """

    ALLOWED_EXTENSIONS = {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
    }

    # ---------------------------------------------------------
    # Validate uploaded file
    # ---------------------------------------------------------

    @classmethod
    def validate_file(
        cls,
        file: UploadFile,
        contents: bytes = b"",
    ) -> str:
        """
        Validate filename, extension, size, and content.
        """

        if not file.filename:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded filename is missing.",
            )

        filename = file.filename

        # Prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename.",
            )

        clean_filename = Path(filename).name

        extension = Path(clean_filename).suffix.lower()

        if extension not in cls.ALLOWED_EXTENSIONS:

            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Unsupported file format '{extension}'. "
                    f"Allowed formats: "
                    f"{', '.join(sorted(cls.ALLOWED_EXTENSIONS))}"
                ),
            )

        if not contents:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        if len(contents) > max_size:

            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"File size "
                    f"{len(contents) / (1024 * 1024):.2f} MB "
                    f"exceeds maximum allowed size of "
                    f"{settings.MAX_UPLOAD_SIZE_MB} MB."
                ),
            )

        return extension

    # ---------------------------------------------------------
    # Process uploaded report
    # ---------------------------------------------------------

    @classmethod
    async def process_uploaded_report(
        cls,
        file: UploadFile,
    ) -> ReportUploadResponse:
        """
        Process uploaded medical report entirely in memory.
        """

        contents = await file.read()

        extension = cls.validate_file(
            file,
            contents,
        )

        report_id = f"rep_{uuid.uuid4().hex[:12]}"

        input_stream = io.BytesIO(contents)

        extracted_lines: List[str] = []

        document_type = "UNKNOWN"

        # =====================================================
        # PDF PROCESSING
        # =====================================================

        if extension == ".pdf":

            doc = None

            try:

                doc = pymupdf.open(
                    stream=input_stream.getvalue(),
                    filetype="pdf",
                )

                if len(doc) == 0:

                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="PDF contains zero pages.",
                    )

                # -------------------------------------------------
                # Detect digital PDF
                # -------------------------------------------------

                digital_text_parts = []

                for page in doc:

                    text = page.get_text("text")

                    if text and text.strip():

                        digital_text_parts.append(text.strip())

                digital_text = "\n".join(digital_text_parts)

                # -------------------------------------------------
                # Digital PDF path
                # -------------------------------------------------

                if len(digital_text.strip()) > 50:

                    document_type = "DIGITAL_PDF"

                    logger.info(f"Report [{report_id}] identified as " f"DIGITAL_PDF.")

                    for page_index in range(len(doc)):

                        page = doc.load_page(page_index)

                        page_lines = OCRService.extract_layout_sorted_lines(page)

                        extracted_lines.extend(page_lines)

                    logger.info(
                        f"Report [{report_id}] extracted "
                        f"{len(extracted_lines)} digital PDF lines."
                    )

                # -------------------------------------------------
                # Scanned PDF path — PARALLELIZED
                # -------------------------------------------------
                # Rendering (PyMuPDF, fast, CPU-light) still happens
                # sequentially in this process, since pymupdf.Document
                # objects aren't safe to share across processes.
                # OCR (slow, CPU-heavy) is fanned out across a pool
                # of worker processes so pages run concurrently
                # instead of one-at-a-time. See ocr_service.py's
                # extract_text_from_images_parallel().

                else:

                    document_type = "SCANNED_PDF"

                    logger.info(
                        f"Report [{report_id}] identified as "
                        f"SCANNED_PDF with {len(doc)} pages. "
                        f"Rendering all pages before dispatching to "
                        f"OCR worker pool."
                    )

                    # Step 1: render every page to PNG bytes up front.
                    # This is fast (no OCR yet) and must stay in this
                    # process since `doc` can't cross a process
                    # boundary.
                    rendered_pages: List[tuple] = []

                    for page_index in range(len(doc)):

                        page_number = page_index + 1

                        image_bytes = OCRService.render_pdf_page_to_bytes(
                            doc,
                            page_index,
                            dpi=settings.OCR_DEFAULT_DPI,
                        )

                        rendered_pages.append((image_bytes, page_number))

                    logger.info(
                        f"Report [{report_id}]: {len(rendered_pages)} "
                        f"pages rendered. Dispatching to OCR pool."
                    )

                    # Step 2: run OCR for all pages concurrently across
                    # the worker pool. This call blocks until every
                    # page's OCR is done, so we push it to a thread via
                    # run_in_executor to avoid blocking the FastAPI
                    # event loop for other concurrent requests while
                    # we wait.
                    loop = asyncio.get_running_loop()

                    ocr_results = await loop.run_in_executor(
                        None,
                        OCRService.extract_text_from_images_parallel,
                        rendered_pages,
                    )

                    # Step 3: stitch results back together in page order.
                    for (image_bytes, page_number), (page_lines, page_scores) in zip(
                        rendered_pages, ocr_results
                    ):

                        if page_lines:

                            extracted_lines.extend(page_lines)

                            logger.info(
                                f"Page {page_number}: "
                                f"{len(page_lines)} OCR lines extracted."
                            )

                        else:

                            logger.warning(
                                f"Page {page_number}: " f"No OCR text extracted."
                            )

                    logger.info(
                        f"Report [{report_id}] completed scanned "
                        f"PDF OCR. Total lines: "
                        f"{len(extracted_lines)}"
                    )

            except HTTPException:
                raise

            except Exception as exc:

                logger.error(
                    f"Failed to process PDF " f"'{file.filename}': {exc}",
                    exc_info=True,
                )

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(f"Unable to process PDF document: {exc}"),
                )

            finally:

                if doc is not None:

                    try:
                        doc.close()

                    except Exception:
                        pass

        # =====================================================
        # IMAGE PROCESSING
        # =====================================================

        else:

            document_type = "IMAGE"

            logger.info(f"Report [{report_id}] identified as IMAGE " f"({extension}).")

            try:

                extracted_lines, _ = OCRService.extract_text_from_image(
                    contents,
                    page_num=1,
                )

                logger.info(
                    f"Image OCR completed. " f"Extracted {len(extracted_lines)} lines."
                )

            except Exception as exc:

                logger.error(
                    f"Image OCR failed: {exc}",
                    exc_info=True,
                )

                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=(f"Failed to process uploaded image: {exc}"),
                )

        # =====================================================
        # EMPTY EXTRACTION WARNING
        # =====================================================

        if not extracted_lines:

            logger.warning(
                f"Report [{report_id}] produced no extracted text. "
                f"Document type: {document_type}"
            )

        # =====================================================
        # PARSING
        # =====================================================

        parsed_data = ParserService.parse_document_text(
            report_id,
            extracted_lines,
        )

        # =====================================================
        # NORMALIZATION
        # =====================================================

        normalized_data = NormalizationService.normalize_extracted_report(parsed_data)

        response_status = (
            "VALIDATED_WITH_WARNINGS" if normalized_data.warnings else "VALIDATED"
        )

        return ReportUploadResponse(
            report_id=report_id,
            status=response_status,
            data=normalized_data,
        )

    # ---------------------------------------------------------
    # In-memory PDF streaming
    # ---------------------------------------------------------

    @classmethod
    async def process_pdf_to_streaming_response(
        cls,
        file: UploadFile,
        output_filename: str = "processed_output.pdf",
    ) -> StreamingResponse:
        """
        Read PDF from memory and return it as a stream.
        """

        contents = await file.read()

        extension = cls.validate_file(
            file,
            contents,
        )

        if extension != ".pdf":

            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="Only PDF files are supported.",
            )

        try:

            input_stream = io.BytesIO(contents)

            doc = pymupdf.open(
                stream=input_stream.getvalue(),
                filetype="pdf",
            )

            if len(doc) == 0:

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="PDF contains zero pages.",
                )

            output_bytes = doc.tobytes(
                garbage=4,
                deflate=True,
            )

            output_stream = io.BytesIO(output_bytes)

            output_stream.seek(0)

            doc.close()

            return StreamingResponse(
                output_stream,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": (f'attachment; filename="{output_filename}"')
                },
            )

        except HTTPException:
            raise

        except Exception as exc:

            logger.error(
                f"PDF streaming failed: {exc}",
                exc_info=True,
            )

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to stream PDF: {exc}",
            )
