import os
import sys
import time

sys.path.insert(0, os.path.abspath("."))
import pymupdf

# Test with multi-threading enabled
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["FLAGS_allocator_strategy"] = "naive_best_fit"
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"

from paddleocr import PaddleOCR
from app.services.ocr_service import OCRService

pdf_path = r"tests\fixtures\RCY.pdf"
doc = pymupdf.open(pdf_path)
page_bytes = OCRService.render_pdf_page_to_bytes(doc, 0, dpi=150)
original_image = OCRService.decode_image(page_bytes)
safe_image = OCRService.safe_resize_for_paddlex(original_image)

print("Initializing PaddleOCR with 4 threads and text_recognition_batch_size=8...")
t0 = time.time()
engine = PaddleOCR(
    lang="en",
    enable_mkldnn=False,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    text_recognition_batch_size=8,
)
print(f"Init in {time.time()-t0:.2f}s")

print("Running inference on Page 1...")
t0 = time.time()
result = list(engine.predict(safe_image))
elapsed = time.time() - t0
print(f"Inference completed in {elapsed:.2f}s (was 256.78s!)")

structured = OCRService.extract_structured_ocr_items(result)
lines = OCRService.reconstruct_rows_from_ocr_items(structured, image_height=original_image.shape[0])
print(f"Items extracted: {len(structured)}, Rows: {len(lines)}")
for ln in lines[:5]:
    print("  |", ln)
doc.close()
