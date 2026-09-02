import logging
import fitz  # PyMuPDF
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple, Optional, cast

from app.core.logging import logger

class OCRService:
    """
    OCR Service for document preprocessing using OpenCV and text extraction using PaddleOCR
    with PyMuPDF layout-sorted fallback.
    """

    _paddle_ocr_instance: Optional[Any] = None

    @classmethod
    def get_paddle_ocr(cls) -> Optional[Any]:
        """
        Lazy-loads and returns a singleton instance of PaddleOCR to prevent re-initialization overhead.
        """
        if cls._paddle_ocr_instance is None:
            try:
                from paddleocr import PaddleOCR
                cls._paddle_ocr_instance = PaddleOCR(
                    use_textline_orientation=True,
                    lang="en"
                )
                logger.info("Initialized PaddleOCR engine singleton successfully.")
            except Exception as exc:
                logger.warning(f"PaddleOCR singleton initialization deferred: {exc}")
                return None
        return cls._paddle_ocr_instance

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        """
        Applies OpenCV image preprocessing pipeline:
        1. Decode byte buffer to BGR matrix
        2. Grayscale conversion
        3. Noise reduction via Gaussian Blur
        4. Otsu Binarization / Thresholding
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image file bytes into OpenCV image matrix.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    @classmethod
    def _extract_text_and_score(cls, line_item: Any) -> Tuple[Optional[str], float]:
        """
        Helper extracting text string and confidence score from various OCR payload formats.
        """
        if isinstance(line_item, (list, tuple)) and len(line_item) >= 2:
            val = line_item[1]
            if isinstance(val, (list, tuple)) and len(val) >= 1:
                text = str(val[0]).strip()
                score = float(val[1]) if len(val) > 1 else 0.95
                return text, score
            elif isinstance(val, str):
                return val.strip(), 0.95

        if isinstance(line_item, dict):
            text = line_item.get("rec_text") or line_item.get("text")
            score = line_item.get("rec_score") or line_item.get("score") or 0.95
            if text:
                return str(text).strip(), float(score)

        return None, 0.0

    @classmethod
    def extract_text_from_image(cls, image_bytes: bytes) -> Tuple[List[str], List[float]]:
        """
        Extracts text lines and confidence scores from an image.
        Uses PaddleOCR natively with PyMuPDF layout container fallback.
        """
        lines: List[str] = []
        confidences: List[float] = []

        # 1. Primary: PaddleOCR Engine
        ocr_engine = cls.get_paddle_ocr()
        if ocr_engine is not None:
            try:
                nparr = np.frombuffer(image_bytes, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                result = ocr_engine.ocr(img, cls=True)

                if result:
                    for res_block in result:
                        if not res_block:
                            continue
                        for line_item in res_block:
                            text_str, conf = cls._extract_text_and_score(line_item)
                            if text_str:
                                lines.append(text_str)
                                confidences.append(conf)

                if lines:
                    return lines, confidences
            except Exception as exc:
                logger.warning(f"PaddleOCR execution error: {exc}. Trying PyMuPDF fallback.")

        # 2. Fallback: PyMuPDF pixmap OCR via PDF container wrapper
        try:
            preprocessed_img = cls.preprocess_image(image_bytes)
            is_success, buffer = cv2.imencode(".png", preprocessed_img)
            if is_success:
                doc = fitz.open(stream=buffer.tobytes(), filetype="png")
                for page in doc:
                    page_lines = cls.extract_layout_sorted_lines(page)
                    lines.extend(page_lines)
                if lines:
                    return lines, [0.95] * len(lines)
        except Exception as exc:
            logger.error(f"PyMuPDF image container fallback error: {exc}")

        return lines, confidences

    @staticmethod
    def extract_layout_sorted_lines(
        page: fitz.Page, y_tolerance: float = 4.0
    ) -> List[str]:
        """
        Extracts text words from a PyMuPDF page and groups them into horizontal lines by y-coordinate.
        Sorts lines vertically top-to-bottom and words horizontally left-to-right to accurately
        reconstruct multi-column lab tables.
        """
        words = page.get_text("words")
        if not words:
            return []

        sorted_words = sorted(words, key=lambda w: (w[1], w[0]))

        lines_dict: List[List[Tuple[float, float, str]]] = []
        for w in sorted_words:
            x0, y0, word_str = w[0], w[1], w[4]

            placed = False
            for line_group in lines_dict:
                avg_y = sum(item[1] for item in line_group) / len(line_group)
                if abs(y0 - avg_y) <= y_tolerance:
                    line_group.append((x0, y0, word_str))
                    placed = True
                    break

            if not placed:
                lines_dict.append([(x0, y0, word_str)])

        lines_dict.sort(key=lambda g: sum(item[1] for item in g) / len(g))

        result_lines = []
        for g in lines_dict:
            g.sort(key=lambda item: item[0])
            line_str = " ".join(item[2] for item in g).strip()
            if line_str:
                result_lines.append(line_str)

        return result_lines

    @staticmethod
    def render_pdf_page_to_bytes(doc: fitz.Document, page_number: int) -> bytes:
        """
        Renders a PDF page to PNG image bytes for OCR processing.
        """
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        return cast(bytes, pix.tobytes("png"))
