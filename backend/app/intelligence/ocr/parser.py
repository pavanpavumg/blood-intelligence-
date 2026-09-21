from typing import List, Dict, Any, Union
from pathlib import Path


class PDFOCRParser:
    """
    Document OCR engine responsible for extracting layout blocks and text
    from blood report PDFs and images.

    Delegates to OCRService which handles:
    - Digital PDFs  -> native PyMuPDF text extraction with layout ordering
    - Scanned PDFs  -> PaddleOCR at 150 DPI with coordinate-based row reconstruction
    - Images (PNG / JPG) -> PaddleOCR directly on the image bytes
    """

    def __init__(self, use_vision_fallback: bool = True) -> None:
        self.use_vision_fallback = use_vision_fallback

    def extract_raw_text(
        self,
        file_path: Union[str, Path],
    ) -> List[Dict[str, Any]]:
        """
        Parse a PDF or image file into structured text blocks.

        Returns a list of dicts, one per page:
            [
                {
                    "page":   1,
                    "text":   "...",
                    "lines":  ["..."],
                    "blocks": [{"text": "...", "score": 0.99, "bbox": [x0,y0,x1,y1]}],
                    "source": "digital" or "ocr",
                }
            ]
        """
        import pymupdf
        from app.services.ocr_service import OCRService

        file_path = Path(file_path)
        suffix = file_path.suffix.lower()
        pages: List[Dict[str, Any]] = []

        # Image files
        if suffix in {".png", ".jpg", ".jpeg"}:
            image_bytes = file_path.read_bytes()
            lines, scores = OCRService.extract_text_from_image(image_bytes, page_num=1)
            pages.append({
                "page": 1,
                "text": "\n".join(lines),
                "lines": lines,
                "blocks": [{"text": ln, "score": sc, "bbox": None} for ln, sc in zip(lines, scores)],
                "source": "ocr",
            })
            return pages

        # PDF files
        doc = pymupdf.open(str(file_path))
        try:
            for page_index in range(len(doc)):
                page_num = page_index + 1
                page = doc.load_page(page_index)
                native_text = OCRService.clean_pua_text(page.get_text("text"))

                if len(native_text.strip()) > 50:
                    # Digital PDF
                    lines = [OCRService.clean_pua_text(ln)
                             for ln in OCRService.extract_layout_sorted_lines(page)]
                    pages.append({
                        "page": page_num,
                        "text": "\n".join(lines),
                        "lines": lines,
                        "blocks": [{"text": ln, "score": 1.0, "bbox": None}
                                   for ln in lines if ln.strip()],
                        "source": "digital",
                    })
                else:
                    # Scanned page
                    image_bytes = OCRService.render_pdf_page_to_bytes(doc, page_index, dpi=150)
                    lines, scores = OCRService.extract_text_from_image(image_bytes, page_num=page_num)
                    pages.append({
                        "page": page_num,
                        "text": "\n".join(lines),
                        "lines": lines,
                        "blocks": [{"text": ln, "score": sc, "bbox": None}
                                   for ln, sc in zip(lines, scores)],
                        "source": "ocr",
                    })
        finally:
            doc.close()

        return pages
