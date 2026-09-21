import os
import sys
import time
import pymupdf

sys.path.insert(0, os.path.abspath("."))
from app.core.config import settings
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService

fixtures = [
    ("tests/fixtures/RCY.pdf", 0, "RCY.pdf Page 1 (Kidney)"),
    ("tests/fixtures/RCY.pdf", 1, "RCY.pdf Page 2 (LFT)"),
    ("tests/fixtures/RCY.pdf", 7, "RCY.pdf Page 8 (CBC)"),
    ("tests/fixtures/Z615.pdf", 0, "Z615.pdf Page 1"),
    ("tests/fixtures/investigationlabreports.pdf", 0, "investigationlabreports.pdf Page 1"),
    ("tests/fixtures/Wellwise Platinum Profile - 5048.pdf", 0, "Wellwise Platinum Profile Page 1"),
]

print("=" * 80)
print(f"{'Fixture Page':<35} | {'Render':<8} | {'OCR Time':<10} | {'Total':<8} | {'Rows':<5} | {'Conf':<6}")
print("=" * 80)

total_benchmark_time = 0

for file_path, page_idx, label in fixtures:
    if not os.path.exists(file_path):
        print(f"Skipping {file_path} (not found)")
        continue

    doc = pymupdf.open(file_path)
    if page_idx >= len(doc):
        doc.close()
        continue

    t0 = time.time()
    page_bytes = OCRService.render_pdf_page_to_bytes(doc, page_idx, dpi=settings.OCR_DEFAULT_DPI)
    t_render = time.time() - t0

    t0 = time.time()
    lines, scores = OCRService.extract_text_from_image(page_bytes, page_num=page_idx + 1)
    t_ocr = time.time() - t0

    t_total = t_render + t_ocr
    total_benchmark_time += t_total
    avg_score = sum(scores) / len(scores) if scores else 0.0

    parsed = ParserService.parse_document_text("bench", lines)
    print(f"{label:<35} | {t_render:.3f}s  | {t_ocr:.2f}s    | {t_total:.2f}s  | {len(lines):<5} | {avg_score:.3f} ({len(parsed.tests)} tests)")
    doc.close()

print("=" * 80)
print(f"Benchmark finished in {total_benchmark_time:.2f}s across {len(fixtures)} pages. Average: {total_benchmark_time/len(fixtures):.2f}s / page")
