import os, sys, time
sys.path.insert(0, os.path.abspath("."))
import pymupdf
from paddleocr import PaddleOCR
from app.services.ocr_service import OCRService

pdf_path = r"tests\fixtures\RCY.pdf"
doc = pymupdf.open(pdf_path)

# Test 200 DPI
t0 = time.time()
page_bytes_200 = OCRService.render_pdf_page_to_bytes(doc, 0, dpi=200)
t_render = time.time() - t0

original_image = OCRService.decode_image(page_bytes_200)
safe_image = OCRService.safe_resize_for_paddlex(original_image, max_side=1200)

print("Initializing PP-OCRv4 with batch_size=8...")
t0 = time.time()
engine = PaddleOCR(
    lang="en",
    ocr_version="PP-OCRv4",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_recognition_batch_size=8,
)
print(f"Init in {time.time()-t0:.2f}s")

print("Running Page 1 inference (200 DPI rendered, safe-resized, batch=8)...")
t0 = time.time()
result = list(engine.predict(safe_image))
infer_time = time.time() - t0
print(f"Inference took: {infer_time:.2f}s (render: {t_render:.3f}s)")

structured = OCRService.extract_structured_ocr_items(result)
lines = OCRService.reconstruct_rows_from_ocr_items(structured, image_height=original_image.shape[0])
print(f"Extracted {len(structured)} items, {len(lines)} rows")
for ln in lines[:8]:
    print("  |", ln)
doc.close()
