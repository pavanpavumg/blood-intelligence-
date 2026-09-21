import os, sys, time
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_use_mkldnn", "0")
os.environ.setdefault("FLAGS_allocator_strategy", "naive_best_fit")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
sys.path.insert(0, os.path.dirname(os.path.abspath(".")))
import pymupdf
from app.services.ocr_service import OCRService

PDF_PATH = r"tests\fixtures\RCY.pdf"
print("=" * 60)
print("RCY.pdf OCR Test")
print("=" * 60)
doc = pymupdf.open(PDF_PATH)
print(f"Pages: {len(doc)}")

print("\n--- Native text check per page ---")
for i in range(len(doc)):
    text = doc[i].get_text("text").strip()
    print(f"  Page {i+1}: {len(text)} chars native text")

print("\nInitialising PaddleOCR engine...")
t0 = time.time()
engine = OCRService.get_paddle_ocr()
print(f"Engine ready in {time.time()-t0:.1f}s  (ok={engine is not None})")

print("\n--- DPI size check on page 1 ---")
for dpi in (100, 150, 200, 250, 300):
    px = doc.load_page(0).get_pixmap(dpi=dpi, alpha=False)
    print(f"  DPI={dpi}  size={px.width}x{px.height}")

SAFE_DPI = 150
print(f"\n--- OCR at {SAFE_DPI} DPI (first 3 pages) ---")
all_lines = []
for pi in range(min(len(doc), 3)):
    pnum = pi + 1
    print(f"\nPage {pnum}:")
    t0 = time.time()
    img_bytes = OCRService.render_pdf_page_to_bytes(doc, pi, dpi=SAFE_DPI)
    print(f"  Rendered {len(img_bytes)//1024} KB in {time.time()-t0:.2f}s")
    t0 = time.time()
    lines, scores = OCRService.extract_text_from_image(img_bytes, page_num=pnum)
    print(f"  OCR done in {time.time()-t0:.2f}s -> {len(lines)} lines")
    if lines:
        avg = sum(scores)/len(scores) if scores else 0
        print(f"  Avg confidence: {avg:.3f}")
        for ln in lines[:15]:
            print(f"    {ln}")
        all_lines.extend(lines)
    else:
        print("  !! No text extracted")

print(f"\nTotal lines from 3 pages: {len(all_lines)}")
doc.close()
