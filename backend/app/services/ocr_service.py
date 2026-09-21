import os
import time
import logging
from typing import List, Tuple, Optional, Any, Dict, Iterator, cast

import pymupdf
import numpy as np
import cv2

# Windows CPU stability flags
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_allocator_strategy", "naive_best_fit")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

from app.core.config import settings
from app.core.logging import logger


class OCRService:
    """
    Production-ready OCR service.

    Features:
    - Lazy PaddleOCR initialization
    - Lightweight mode (PP-OCRv4 mobile models, no unwarp/ori overhead)
    - Optional GPU auto-detection
    - In-memory image processing
    - Configurable DPI rendering (Fast=200, Balanced=220, High=300)
    - Fast -> Fallback conditional preprocessing
    - Granular per-step timing instrumentation
    - Multiple OCR result formats
    - Page-level logging
    - No disk storage
    """

    _paddle_ocr_instance: Optional[Any] = None
    _init_attempted: bool = False

    DPI_FAST: int = settings.OCR_DPI_FAST
    DPI_BALANCED: int = settings.OCR_DPI_BALANCED
    DPI_HIGH: int = settings.OCR_DPI_HIGH

    # ---------------------------------------------------------
    # PaddleOCR initialization
    # ---------------------------------------------------------

    @classmethod
    def get_paddle_ocr(cls) -> Optional[Any]:
        """
        Initialize PaddleOCR only once and cache the result.
        Uses lightweight PP-OCRv4 mobile models with doc orientation/unwarping
        disabled for maximum throughput while preserving full accuracy.
        Auto-detects GPU if CUDA is available.
        """

        if cls._init_attempted:
            return cls._paddle_ocr_instance

        cls._init_attempted = True

        try:
            import paddle
            from paddleocr import PaddleOCR

            device = "cpu"
            try:
                if paddle.is_compiled_with_cuda() and hasattr(paddle, "device") and hasattr(paddle.device, "cuda") and paddle.device.cuda.device_count() > 0:
                    device = "gpu"
                    logger.info("CUDA GPU detected. PaddleOCR will use GPU acceleration.")
                else:
                    logger.info("PaddleOCR using CPU inference.")
            except Exception as gpu_err:
                logger.debug(f"GPU check skipped: {gpu_err}")

            engine = None

            # Try modern / compatible constructor options starting with lightweight PP-OCRv4
            constructor_attempts = [
                {
                    "lang": "en",
                    "ocr_version": settings.OCR_VERSION,
                    "enable_mkldnn": False,
                    "use_doc_orientation_classify": False,
                    "use_doc_unwarping": False,
                    "use_textline_orientation": False,
                    "device": device,
                },
                {
                    "lang": "en",
                    "enable_mkldnn": False,
                    "use_doc_orientation_classify": False,
                    "use_doc_unwarping": False,
                    "use_textline_orientation": False,
                    "device": device,
                },
                {
                    "lang": "en",
                    "enable_mkldnn": False,
                    "device": device,
                },
                {
                    "lang": "en",
                },
                {},
            ]

            last_error = None

            for options in constructor_attempts:
                try:
                    engine = PaddleOCR(**options)
                    break
                except (TypeError, ValueError) as exc:
                    last_error = exc
                    continue

            if engine is None:
                raise RuntimeError(
                    f"Unable to initialize PaddleOCR. Last error: {last_error}"
                )

            cls._paddle_ocr_instance = engine

            logger.info("PaddleOCR engine initialized successfully.")

        except ImportError as exc:
            logger.error(
                "PaddleOCR is not installed. "
                "Install it using: python -m pip install paddleocr paddlepaddle. "
                f"Error: {exc}"
            )
            cls._paddle_ocr_instance = None

        except Exception as exc:
            logger.error(
                f"Failed to initialize PaddleOCR: {exc}",
                exc_info=True,
            )
            cls._paddle_ocr_instance = None

        return cls._paddle_ocr_instance

    # ---------------------------------------------------------
    # Reset OCR engine - useful for testing
    # ---------------------------------------------------------

    @classmethod
    def reset_engine(cls) -> None:
        """
        Reset cached OCR engine.
        Useful during testing or after dependency changes.
        """

        cls._paddle_ocr_instance = None
        cls._init_attempted = False

    # ---------------------------------------------------------
    # Decode image bytes
    # ---------------------------------------------------------

    @staticmethod
    def decode_image(image_bytes: bytes) -> np.ndarray:
        """
        Decode image bytes into OpenCV BGR image.
        """

        if not image_bytes:
            raise ValueError("Image bytes are empty.")

        array = np.frombuffer(image_bytes, dtype=np.uint8)

        image = cv2.imdecode(array, cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError("Unable to decode image bytes using OpenCV.")

        return np.ascontiguousarray(image)

    # ---------------------------------------------------------
    # Image preprocessing
    # ---------------------------------------------------------

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> np.ndarray:
        """
        Create a grayscale threshold image for difficult scans.

        Normalises the channel count before processing so the function
        works correctly with grayscale, BGR, and BGRA source images.
        """

        image = OCRService.decode_image(image_bytes)

        # Normalise to BGR regardless of source channel count
        if image.ndim == 2:
            # Already grayscale — promote to BGR so downstream steps are
            # channel-agnostic.
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        elif image.shape[2] == 4:
            # BGRA — strip the alpha channel.
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

        gray = cv2.cvtColor(
            image,
            cv2.COLOR_BGR2GRAY,
        )

        # Noise reduction
        blurred = cv2.GaussianBlur(
            gray,
            (3, 3),
            0,
        )

        # Otsu thresholding
        _, threshold = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        return np.ascontiguousarray(threshold)

    # ---------------------------------------------------------
    # Clean OCR text
    # ---------------------------------------------------------

    @staticmethod
    def clean_pua_text(text: str) -> str:
        """
        Clean corrupted private-use Unicode characters.
        """

        if not text:
            return ""

        output = []

        for char in text:
            code = ord(char)

            if 0xF000 <= code <= 0xF0FF:
                output.append(chr(code - 0xF000))

            elif 0xE000 <= code <= 0xF8FF:
                ascii_code = code & 0xFF

                if 32 <= ascii_code <= 126:
                    output.append(chr(ascii_code))
                else:
                    output.append(char)

            else:
                output.append(char)

        return "".join(output).strip()

    # ---------------------------------------------------------
    # Safe float conversion
    # ---------------------------------------------------------

    @staticmethod
    def safe_float(value: Any, default: float = 0.95) -> float:
        """
        Convert OCR confidence safely to float.
        """

        try:
            if value is None:
                return default

            return float(value)

        except (TypeError, ValueError):
            return default

    # ---------------------------------------------------------
    # Extract one OCR line
    # ---------------------------------------------------------

    @classmethod
    def _extract_text_and_score(
        cls,
        item: Any,
    ) -> Tuple[Optional[str], float]:
        """
        Extract text and confidence from legacy OCR formats.
        """

        if item is None:
            return None, 0.0

        # Legacy format:
        # [bounding_box, ("text", confidence)]
        if isinstance(item, (list, tuple)):

            if len(item) >= 2:
                value = item[1]

                if isinstance(value, (list, tuple)):
                    if len(value) >= 1:
                        text = value[0]

                        if isinstance(text, str):
                            score = cls.safe_float(value[1]) if len(value) > 1 else 0.95

                            return text.strip(), score

                if isinstance(value, str):
                    return value.strip(), 0.95

        # Dictionary format
        if isinstance(item, dict):

            text = item.get("rec_text") or item.get("text") or item.get("transcription")

            score = (
                item.get("rec_score")
                if item.get("rec_score") is not None
                else item.get("score", 0.95)
            )

            if text:
                return (
                    str(text).strip(),
                    cls.safe_float(score),
                )

        # Object format
        text = (
            getattr(item, "rec_text", None)
            or getattr(item, "text", None)
            or getattr(item, "transcription", None)
        )

        if text:
            score = getattr(
                item,
                "rec_score",
                getattr(item, "score", 0.95),
            )

            return (
                str(text).strip(),
                cls.safe_float(score),
            )

        # Raw string
        if isinstance(item, str):
            return item.strip(), 0.95

        return None, 0.0

    # ---------------------------------------------------------
    # Extract structured OCR items with bounding boxes
    # ---------------------------------------------------------

    @classmethod
    def extract_structured_ocr_items(
        cls,
        result: Any,
    ) -> List[Dict[str, Any]]:
        """
        Extract structured items containing text, confidence score,
        and bounding box coordinates [x0, y0, x1, y1].
        """

        items: List[Dict[str, Any]] = []

        if result is None:
            return items

        # Case 1: Dictionary or Object with rec_texts, rec_scores, dt_polys/rec_boxes
        if isinstance(result, dict) or hasattr(result, "rec_texts"):

            get_val = (
                (lambda k: result.get(k))
                if isinstance(result, dict)
                else (lambda k: getattr(result, k, None))
            )

            texts = get_val("rec_texts") or get_val("texts")
            scores = get_val("rec_scores") or get_val("scores")
            polys = get_val("dt_polys") or get_val("rec_polys") or get_val("rec_boxes")

            if texts:
                for idx, text in enumerate(texts):

                    if not text:
                        continue

                    clean_text = cls.clean_pua_text(str(text))

                    if not clean_text:
                        continue

                    score = (
                        cls.safe_float(scores[idx])
                        if scores is not None and idx < len(scores)
                        else 0.95
                    )

                    bbox = None

                    if polys is not None and idx < len(polys):

                        poly = polys[idx]

                        try:
                            poly_arr = np.array(poly)

                            if poly_arr.ndim == 2 and poly_arr.shape[1] == 2:
                                xs = poly_arr[:, 0]
                                ys = poly_arr[:, 1]
                                bbox = [
                                    float(xs.min()),
                                    float(ys.min()),
                                    float(xs.max()),
                                    float(ys.max()),
                                ]

                            elif poly_arr.size >= 4:
                                flat = poly_arr.flatten()
                                bbox = [
                                    float(flat[0]),
                                    float(flat[1]),
                                    float(flat[2]),
                                    float(flat[3]),
                                ]

                        except Exception:
                            bbox = None

                    items.append(
                        {
                            "text": clean_text,
                            "score": score,
                            "bbox": bbox,
                        }
                    )

                return items

        # Case 2: Nested list or tuple (Legacy PaddleOCR format)
        if isinstance(result, (list, tuple)):

            for element in result:

                if isinstance(element, (list, tuple)) and len(element) >= 2:

                    bbox_data = element[0]
                    val = element[1]

                    text = None
                    score = 0.95

                    if isinstance(val, (list, tuple)) and len(val) >= 1:
                        text = val[0]

                        if len(val) > 1:
                            score = cls.safe_float(val[1])

                    elif isinstance(val, str):
                        text = val

                    if text and isinstance(text, str):

                        clean_text = cls.clean_pua_text(text)

                        if clean_text:
                            bbox = None

                            try:
                                poly_arr = np.array(bbox_data)

                                if poly_arr.ndim == 2 and poly_arr.shape[1] == 2:
                                    xs = poly_arr[:, 0]
                                    ys = poly_arr[:, 1]
                                    bbox = [
                                        float(xs.min()),
                                        float(ys.min()),
                                        float(xs.max()),
                                        float(ys.max()),
                                    ]

                            except Exception:
                                pass

                            items.append(
                                {
                                    "text": clean_text,
                                    "score": score,
                                    "bbox": bbox,
                                }
                            )

                            continue

                # Recursively check sub-elements
                sub = cls.extract_structured_ocr_items(element)

                if sub:
                    items.extend(sub)

        return items

    # ---------------------------------------------------------
    # Reconstruct visual rows from OCR items using coordinates
    # ---------------------------------------------------------

    @classmethod
    def reconstruct_rows_from_ocr_items(
        cls,
        items: List[Dict[str, Any]],
        image_height: Optional[int] = None,
        y_tolerance: Optional[float] = None,
    ) -> List[str]:
        """
        Group OCR items into visual horizontal table rows based on Y-coordinates,
        and sort items left-to-right by X-coordinates within each row.
        """

        if not items:
            return []

        if y_tolerance is None:
            if image_height and image_height > 0:
                y_tolerance = max(10.0, min(22.0, image_height * 0.004))
            else:
                y_tolerance = 12.0

        valid_items = []
        no_bbox_items = []

        for item in items:
            text = item.get("text")
            if not text:
                continue

            bbox = item.get("bbox")

            if bbox and len(bbox) == 4:
                x0, y0, x1, y1 = bbox
                center_y = (y0 + y1) / 2.0
                center_x = (x0 + x1) / 2.0

                valid_items.append(
                    {
                        "text": text,
                        "score": item.get("score", 0.95),
                        "x0": x0,
                        "center_x": center_x,
                        "center_y": center_y,
                    }
                )
            else:
                no_bbox_items.append(text)

        # Sort valid items vertically by Y center
        valid_items.sort(key=lambda it: it["center_y"])

        row_groups: List[List[Dict[str, Any]]] = []

        for item in valid_items:
            placed = False

            for group in row_groups:
                avg_y = sum(it["center_y"] for it in group) / len(group)

                if abs(item["center_y"] - avg_y) <= y_tolerance:
                    group.append(item)
                    placed = True
                    break

            if not placed:
                row_groups.append([item])

        # Sort row groups vertically by average Y coordinate
        row_groups.sort(
            key=lambda group: (sum(it["center_y"] for it in group) / len(group))
        )

        reconstructed_lines: List[str] = []

        for group in row_groups:
            # Sort items within row horizontally from left to right
            group.sort(key=lambda it: it["center_x"])

            row_str = " ".join(it["text"] for it in group).strip()

            if row_str:
                reconstructed_lines.append(row_str)

        if no_bbox_items:
            reconstructed_lines.extend(no_bbox_items)

        return reconstructed_lines

    # ---------------------------------------------------------
    # Parse modern PaddleOCR result (legacy helper wrapper)
    # ---------------------------------------------------------

    @classmethod
    def _extract_modern_result(
        cls,
        result: Any,
    ) -> List[Tuple[str, float]]:
        """
        Legacy list extractor for backward compatibility.
        """
        items = cls.extract_structured_ocr_items(result)
        return [(it["text"], it["score"]) for it in items if it.get("text")]

    # ---------------------------------------------------------
    # Execute PaddleOCR
    # ---------------------------------------------------------

    @classmethod
    def _run_ocr_engine(
        cls,
        engine: Any,
        image: np.ndarray,
    ) -> Any:
        """
        Support both:
        - PaddleOCR v2: engine.ocr(image)
        - PaddleOCR v3 / paddlex: engine.predict(image)

        paddlex (PaddleOCR v3) only accepts ``numpy.ndarray`` or ``str``
        (file path) — PIL Images are silently discarded (no exception is
        raised; the engine just returns an empty result), so PIL is NOT used.

        If passing a numpy array raises an error (numpy overrides ``__rmod__``
        so bare ``%`` formatting in PaddleOCR's logging can throw
        ``TypeError``), we fall back to writing a temp PNG and passing its
        path, which is always accepted by paddlex.
        """

        # Ensure contiguous uint8 numpy array for the C++ inference runner.
        if isinstance(image, np.ndarray):
            image = np.ascontiguousarray(image, dtype=np.uint8)

        def _collect(raw: Any) -> Any:
            """Materialise a generator / iterator result into a list."""
            if not isinstance(raw, (list, tuple, dict)):
                try:
                    return list(raw)
                except TypeError:
                    pass
            return raw

        def _predict_via_path(eng: Any) -> Any:
            """
            Write *image* to a temp PNG and run inference with the file path.
            paddlex explicitly supports str paths and this avoids all numpy
            type-checking / logging issues.
            """
            import tempfile
            import os as _os

            tmp_path: Optional[str] = None
            try:
                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as tmp:
                    tmp_path = tmp.name

                success = cv2.imwrite(tmp_path, image)
                if not success:
                    raise RuntimeError("cv2.imwrite failed for temp OCR image.")

                if hasattr(eng, "predict"):
                    return _collect(eng.predict(tmp_path))

                if hasattr(eng, "ocr"):
                    return eng.ocr(tmp_path)

            finally:
                if tmp_path:
                    try:
                        _os.unlink(tmp_path)
                    except Exception:
                        pass

            return None

        # Attempt 1: modern API (v3+) — pass numpy array to predict().
        if hasattr(engine, "predict"):
            try:
                return _collect(engine.predict(image))
            except Exception as exc:
                logger.warning(
                    "PaddleOCR predict(numpy) failed: %s — retrying via temp file.",
                    str(exc),
                )

            # Attempt 2: predict() via temp file path.
            try:
                result = _predict_via_path(engine)
                if result is not None:
                    return result
            except Exception as exc:
                logger.warning("PaddleOCR predict(file) failed: %s", str(exc))

        # Attempt 3: legacy API (v2) — engine.ocr().
        if hasattr(engine, "ocr"):
            try:
                return engine.ocr(image)
            except Exception as exc:
                logger.warning("PaddleOCR ocr(numpy) failed: %s — retrying via temp file.", str(exc))

            try:
                result = _predict_via_path(engine)
                if result is not None:
                    return result
            except Exception as exc:
                logger.warning("PaddleOCR ocr(file) failed: %s", str(exc))

        raise RuntimeError(
            "Installed PaddleOCR engine exposes neither predict() nor ocr() method."
        )

    # ---------------------------------------------------------
    # Safe image resize for paddlex compatibility
    # ---------------------------------------------------------

    @staticmethod
    def safe_resize_for_paddlex(
        image: np.ndarray,
        max_side: int = 1200,
    ) -> np.ndarray:
        """
        Downscale *image* so its longest side is at most *max_side* pixels.

        paddlex's ``resize_image_type0`` crashes on Windows with
        ``cv2.error: Unknown C++ exception`` when it receives an image that
        it needs to *upscale* beyond ~1280 px.  By pre-shrinking to 1200 px
        we ensure paddlex only ever downscales, which is always safe.

        Aspect ratio is preserved.  Images already within the limit are
        returned unchanged (no copy made).
        """
        h, w = image.shape[:2]
        long_side = max(h, w)

        if long_side <= max_side:
            return image

        scale = max_side / long_side
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))

        # IMPORTANT: Do NOT use cv2.resize here.
        # paddlex loads its own OpenCV DLLs on Windows; once the engine is
        # initialised the system cv2 global state is corrupted and cv2.resize
        # raises "Unknown C++ exception from OpenCV code" for the rest of the
        # process lifetime.
        # PIL (Pillow) is completely independent of OpenCV and always safe.
        try:
            from PIL import Image as _PILImage  # type: ignore[import-untyped]

            # PIL treats the channels naively (doesn't care BGR vs RGB for
            # a pure resize), so no colour conversion is needed.
            pil_img = _PILImage.fromarray(image)
            try:
                _lanczos = _PILImage.Resampling.LANCZOS  # Pillow >= 9.1
            except AttributeError:
                _lanczos = _PILImage.LANCZOS  # type: ignore[attr-defined]  # Pillow < 9.1
            pil_resized = pil_img.resize((new_w, new_h), _lanczos)
            return np.ascontiguousarray(np.array(pil_resized), dtype=np.uint8)

        except Exception:
            # Last resort: crude numpy row/column subsampling (no OpenCV).
            step_h = max(1, h // new_h)
            step_w = max(1, w // new_w)
            return np.ascontiguousarray(image[::step_h, ::step_w])

    # ---------------------------------------------------------
    # Extract OCR from image bytes
    # ---------------------------------------------------------

    @classmethod
    def extract_text_from_image(
        cls,
        image_bytes: bytes,
        page_num: Optional[int] = None,
        confidence_threshold: Optional[float] = None,
        enable_fallback: Optional[bool] = None,
    ) -> Tuple[List[str], List[float]]:
        """
        Extract text from image bytes using coordinate-based row reconstruction.

        Fast -> Fallback Workflow:
        1. Fast pass: Run lightweight OCR on original image (safe-resized).
        2. Quality check: If lines >= 3 and confidence >= threshold, return immediately.
        3. Fallback pass (conditional): Only run image preprocessing if fast pass
           yields poor confidence (< 0.80) or zero text.
        """

        t_page_start = time.time()
        lines: List[str] = []
        confidences: List[float] = []

        page_label = f"Page {page_num}" if page_num is not None else "Image"
        conf_thresh = confidence_threshold if confidence_threshold is not None else settings.OCR_CONFIDENCE_THRESHOLD
        allow_fallback = enable_fallback if enable_fallback is not None else settings.OCR_ENABLE_FALLBACK

        engine = cls.get_paddle_ocr()

        if engine is None:
            logger.warning(f"OCR engine unavailable for {page_label}.")
            return lines, confidences

        try:
            # 1. Image decoding & safe-resize
            t0 = time.time()
            original_image = cls.decode_image(image_bytes)
            img_height = original_image.shape[0]
            safe_original = cls.safe_resize_for_paddlex(
                original_image,
                max_side=settings.OCR_MAX_SIDE,
            )
            decode_time = time.time() - t0

            # 2. Fast pass: Original image OCR
            t0 = time.time()
            raw_result = cls._run_ocr_engine(
                engine,
                safe_original,
            )
            ocr_time = time.time() - t0

            # 3. Structured extraction & coordinate row reconstruction
            t0 = time.time()
            structured_items = cls.extract_structured_ocr_items(raw_result)
            structured_extraction_time = time.time() - t0

            t0 = time.time()
            if structured_items:
                lines = cls.reconstruct_rows_from_ocr_items(
                    structured_items,
                    image_height=img_height,
                )
                confidences = [
                    item.get("score", 0.95) for item in structured_items
                ]
            row_reconstruction_time = time.time() - t0

            avg_conf = (
                sum(confidences) / len(confidences) if confidences else 0.0
            )

            # 4. Fast -> Fallback Check (Step 5 & 6)
            is_acceptable = len(lines) >= 3 and avg_conf >= conf_thresh
            if not is_acceptable and allow_fallback:
                logger.info(
                    f"OCR [{page_label}]: Fast pass insufficient "
                    f"({len(lines)} lines, avg_conf={avg_conf:.3f} < {conf_thresh}). "
                    f"Triggering fallback pass with image preprocessing."
                )
                try:
                    t_pre_start = time.time()
                    processed_image = cls.preprocess_image(image_bytes)
                    safe_processed = cls.safe_resize_for_paddlex(
                        processed_image,
                        max_side=settings.OCR_MAX_SIDE,
                    )
                    fallback_result = cls._run_ocr_engine(engine, safe_processed)
                    fb_structured = cls.extract_structured_ocr_items(fallback_result)

                    if fb_structured:
                        fb_lines = cls.reconstruct_rows_from_ocr_items(
                            fb_structured,
                            image_height=img_height,
                        )
                        fb_confidences = [item.get("score", 0.95) for item in fb_structured]
                        fb_avg_conf = sum(fb_confidences) / len(fb_confidences) if fb_confidences else 0.0

                        # Adopt fallback if it found more lines or higher confidence
                        if len(fb_lines) > len(lines) or (len(fb_lines) == len(lines) and fb_avg_conf > avg_conf):
                            lines = fb_lines
                            confidences = fb_confidences
                            avg_conf = fb_avg_conf
                            logger.info(
                                f"OCR [{page_label}]: Fallback preprocessing succeeded. "
                                f"{len(lines)} rows, avg_conf={avg_conf:.3f}"
                            )

                    ocr_time += (time.time() - t_pre_start)

                except Exception as fb_exc:
                    logger.warning(
                        f"OCR [{page_label}] fallback preprocessing failed: {fb_exc}"
                    )

            total_page_time = time.time() - t_page_start

            # Step 1 timing instrumentation
            logger.info(
                f"OCR [{page_label}] TIMING: "
                f"decode_time={decode_time:.3f}s, "
                f"ocr_time={ocr_time:.3f}s, "
                f"structured_extraction_time={structured_extraction_time:.3f}s, "
                f"row_reconstruction_time={row_reconstruction_time:.3f}s, "
                f"total_page_time={total_page_time:.3f}s | "
                f"Extracted {len(lines)} visual rows from {len(confidences)} OCR items (avg_conf={avg_conf:.3f})"
            )

        except Exception as exc:
            logger.error(
                f"Error executing OCR for {page_label}: {exc}",
                exc_info=True,
            )

        return lines, confidences

    # ---------------------------------------------------------
    # Digital PDF layout extraction
    # ---------------------------------------------------------

    @staticmethod
    def extract_layout_sorted_lines(
        page: pymupdf.Page,
        y_tolerance: float = 4.0,
    ) -> List[str]:
        """
        Extract text from digital PDF while preserving
        visual line ordering.
        """

        words = page.get_text("words")

        if not words:
            return []

        sorted_words = sorted(
            words,
            key=lambda word: (
                word[1],
                word[0],
            ),
        )

        line_groups: List[List[Tuple[float, float, str]]] = []

        for word in sorted_words:

            x0 = word[0]
            y0 = word[1]
            text = OCRService.clean_pua_text(word[4])

            if not text:
                continue

            placed = False

            for group in line_groups:

                average_y = sum(item[1] for item in group) / len(group)

                if abs(y0 - average_y) <= y_tolerance:

                    group.append(
                        (
                            x0,
                            y0,
                            text,
                        )
                    )

                    placed = True
                    break

            if not placed:

                line_groups.append(
                    [
                        (
                            x0,
                            y0,
                            text,
                        )
                    ]
                )

        line_groups.sort(
            key=lambda group: (sum(item[1] for item in group) / len(group))
        )

        result_lines: List[str] = []

        for group in line_groups:

            group.sort(key=lambda item: item[0])

            line = " ".join(item[2] for item in group).strip()

            if line:
                result_lines.append(line)

        return result_lines

    # ---------------------------------------------------------
    # Render PDF page in memory
    # ---------------------------------------------------------

    @staticmethod
    def render_pdf_page_to_bytes(
        doc: pymupdf.Document,
        page_number: int,
        dpi: Optional[int] = None,
    ) -> bytes:
        """
        Render a PDF page to PNG bytes entirely in memory.

        Default DPI is configurable via settings.OCR_DEFAULT_DPI (200 DPI).
        DPI Profiles:
        - FAST = 200 (default)
        - BALANCED = 220
        - HIGH = 300
        """

        target_dpi = dpi if dpi is not None else settings.OCR_DEFAULT_DPI
        t0 = time.time()

        page = doc.load_page(page_number)

        pixmap = page.get_pixmap(
            dpi=target_dpi,
            alpha=False,
        )

        data = cast(bytes, pixmap.tobytes("png"))
        render_time = time.time() - t0
        logger.debug(
            f"Rendered page {page_number + 1} at {target_dpi} DPI in {render_time:.3f}s ({len(data)} bytes)."
        )

        return data

    # ---------------------------------------------------------
    # Parallel OCR
    # ---------------------------------------------------------

    @staticmethod
    def extract_text_from_images_parallel(
        page_images: List[Tuple[bytes, int]],
    ) -> List[Tuple[List[str], List[float]]]:
        """
        Run OCR on multiple pre-rendered page images concurrently across
        the worker pool. page_images is a list of (image_bytes, page_num)
        tuples, in the order you want results returned (order is preserved).
        """
        return extract_text_from_images_parallel(page_images)

    @staticmethod
    def _shutdown_ocr_pool() -> None:
        """
        Shut down the background OCR worker pool.
        """
        _shutdown_ocr_pool()


# ============================================================
# Parallel OCR Process Pool
# ============================================================

import atexit
from concurrent.futures import ProcessPoolExecutor

# Cap worker count — OCR is CPU + RAM heavy per worker, more isn't
# free. Override via env var if needed. Default is 1 (sequential in-process
# with cached singleton engine) which uses minimal RAM (~500MB) and prevents
# model duplication. Set to 2+ for multi-process concurrency if RAM permits.
OCR_WORKER_COUNT = int(os.environ.get("OCR_WORKER_COUNT", "1"))

_ocr_process_pool: Optional[ProcessPoolExecutor] = None


def _ocr_page_worker(image_bytes: bytes, page_num: int) -> Tuple[List[str], List[float]]:
    """
    Runs inside a separate worker process. Must be a plain module-level
    function (not a classmethod/lambda) so it can be pickled and sent
    to the worker by ProcessPoolExecutor.
    """
    return OCRService.extract_text_from_image(image_bytes, page_num=page_num)


def get_ocr_process_pool() -> ProcessPoolExecutor:
    """
    Lazily creates a module-level process pool, reused across requests
    for the lifetime of the server.
    """
    global _ocr_process_pool

    if _ocr_process_pool is None:
        logger.info(f"Starting OCR process pool with {OCR_WORKER_COUNT} workers.")
        _ocr_process_pool = ProcessPoolExecutor(max_workers=OCR_WORKER_COUNT)

    return _ocr_process_pool


def _shutdown_ocr_pool() -> None:
    global _ocr_process_pool
    if _ocr_process_pool is not None:
        logger.info("Shutting down OCR process pool.")
        _ocr_process_pool.shutdown(wait=False, cancel_futures=True)
        _ocr_process_pool = None


# Best-effort cleanup on interpreter exit.
atexit.register(_shutdown_ocr_pool)


def extract_text_from_images_parallel(
    page_images: List[Tuple[bytes, int]],
) -> List[Tuple[List[str], List[float]]]:
    """
    Run OCR on multiple pre-rendered page images.

    If OCR_WORKER_COUNT <= 1, processes sequentially in-process using the cached
    singleton engine (0 process overhead, minimal RAM usage, ideal for Windows dev).
    If OCR_WORKER_COUNT > 1, utilizes the ProcessPoolExecutor across worker processes.
    """
    if not page_images:
        return []

    if OCR_WORKER_COUNT <= 1:
        results: List[Tuple[List[str], List[float]]] = []
        for image_bytes, page_num in page_images:
            try:
                results.append(OCRService.extract_text_from_image(image_bytes, page_num=page_num))
            except Exception as exc:
                logger.error(f"OCR failed for page {page_num}: {exc}", exc_info=True)
                results.append(([], []))
        return results

    pool = get_ocr_process_pool()

    futures = [
        pool.submit(_ocr_page_worker, image_bytes, page_num)
        for image_bytes, page_num in page_images
    ]

    results = []
    for future in futures:
        try:
            results.append(future.result())
        except Exception as exc:
            logger.error(f"OCR worker process failed: {exc}", exc_info=True)
            results.append(([], []))

    return results
