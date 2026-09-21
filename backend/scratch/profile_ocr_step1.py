import os
import sys
import time
import pymupdf

# Set baseline flags as in current ocr_service.py
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_allocator_strategy", "naive_best_fit")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

sys.path.insert(0, os.path.abspath("."))
from app.services.ocr_service import OCRService

pdf_path = r"tests\fixtures\RCY.pdf"
doc = pymupdf.open(pdf_path)

print(f"Profiling Page 1 of {pdf_path} (Current Baseline: 150 DPI, OMP=1, sequential)...")

t_start_total = time.time()

# 1. Render time
t0 = time.time()
page_bytes = OCRService.render_pdf_page_to_bytes(doc, 0, dpi=150)
t_render = time.time() - t0

# 2. Image decoding & resize
t0 = time.time()
original_image = OCRService.decode_image(page_bytes)
img_height = original_image.shape[0]
safe_image = OCRService.safe_resize_for_paddlex(original_image)
t_decode_resize = time.time() - t0

# 3. OCR engine init & inference
t0 = time.time()
engine = OCRService.get_paddle_ocr()
t_engine_init = time.time() - t0

t0 = time.time()
raw_ocr_result = OCRService._run_ocr_engine(engine, safe_image)
t_ocr_inference = time.time() - t0

# 4. Structured extraction
t0 = time.time()
structured_items = OCRService.extract_structured_ocr_items(raw_ocr_result)
t_structured = time.time() - t0

# 5. Row reconstruction
t0 = time.time()
lines = OCRService.reconstruct_rows_from_ocr_items(structured_items, image_height=img_height)
t_row_recon = time.time() - t0

t_total_page = time.time() - t_start_total

print("\n--- TIMING BREAKDOWN (Baseline Page 1) ---")
print(f"render_time:                {t_render:.3f} s")
print(f"decode_and_resize_time:     {t_decode_resize:.3f} s")
print(f"engine_init_time (first):   {t_engine_init:.3f} s")
print(f"ocr_time (inference):       {t_ocr_inference:.3f} s")
print(f"structured_extraction_time: {t_structured:.3f} s")
print(f"row_reconstruction_time:    {t_row_recon:.3f} s")
print(f"total_page_time:            {t_total_page:.3f} s")
print(f"Items extracted: {len(structured_items)}, Rows reconstructed: {len(lines)}")
doc.close()
