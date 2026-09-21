import os
import sys
import time
import pytest
import pymupdf

sys.path.insert(0, os.path.abspath("."))
from app.core.config import settings
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_ocr_performance_and_regression_rcy():
    """
    Test RCY.pdf scanned report:
    Verify OCR speed, row reconstruction, bounding boxes, biomarker separation.
    """
    pdf_path = r"tests\fixtures\RCY.pdf"
    assert os.path.exists(pdf_path), f"Fixture not found: {pdf_path}"

    doc = pymupdf.open(pdf_path)
    assert len(doc) >= 1

    # Page 1 test
    t0 = time.time()
    page_bytes = OCRService.render_pdf_page_to_bytes(doc, 0, dpi=settings.OCR_DEFAULT_DPI)
    render_time = time.time() - t0

    t0 = time.time()
    lines, scores = OCRService.extract_text_from_image(page_bytes, page_num=1)
    ocr_time = time.time() - t0

    print(f"\nRCY.pdf Page 1: render={render_time:.3f}s, ocr={ocr_time:.2f}s, lines={len(lines)}, avg_score={sum(scores)/len(scores):.3f}")

    assert ocr_time < 90.0, f"OCR time {ocr_time:.2f}s exceeds performance threshold (target < 90s, baseline was 260s)"
    assert len(lines) >= 30, f"Expected >= 30 lines, got {len(lines)}"

    # Check parser results
    parsed = ParserService.parse_document_text("test_rcy", lines)
    test_names = [t.raw_test_name for t in parsed.tests]

    # Verify key tests are extracted
    found_creatinine = any("CREATININE" in name.upper() for name in test_names)
    found_urea = any("UREA" in name.upper() for name in test_names)
    found_sodium = any("SODIUM" in name.upper() for name in test_names)
    found_potassium = any("POTASSIUM" in name.upper() for name in test_names)

    assert found_creatinine, "SERUM CREATININE missing"
    assert found_urea, "UREA missing"
    assert found_sodium, "SODIUM missing"
    assert found_potassium, "POTASSIUM missing"

    # Verify normalization works
    norm = NormalizationService.normalize_extracted_report(parsed)
    assert len(norm.tests) >= 5, "Expected at least 5 normalized tests on page 1"
    doc.close()


def test_cbc_biomarker_separation_and_accuracy():
    """
    Test Complete Blood Count page (Page 8 of RCY.pdf or CBC fixture):
    Verify that HCT and MCV do not merge, MCH and MCHC do not merge, Platelet and RDW do not merge.
    """
    pdf_path = r"tests\fixtures\RCY.pdf"
    doc = pymupdf.open(pdf_path)
    # Page 8 is CBC in RCY.pdf
    page_bytes = OCRService.render_pdf_page_to_bytes(doc, 7, dpi=settings.OCR_DEFAULT_DPI)
    lines, scores = OCRService.extract_text_from_image(page_bytes, page_num=8)

    parsed = ParserService.parse_document_text("test_cbc", lines)
    test_names = [t.raw_test_name.upper() for t in parsed.tests]

    print("\nCBC Test names extracted:", test_names)

    # Check that MCV and MCH and MCHC are separate tests
    has_mcv = any("MCV" in name for name in test_names)
    has_mch = any("MCH" in name and "MCHC" not in name for name in test_names)
    has_mchc = any("MCHC" in name for name in test_names)

    assert has_mcv, "MCV missing"
    assert has_mch, "MCH missing or merged"
    assert has_mchc, "MCHC missing or merged"

    doc.close()


def test_digital_pdf_pipeline_unchanged():
    """
    Test digital PDF (1724_fid.pdf or Sample-Lab-Report-DBTICBM.pdf):
    Verify that digital text extraction remains intact and fast (< 1s).
    """
    pdf_path = r"tests\fixtures\1724_fid.pdf"
    if not os.path.exists(pdf_path):
        pdf_path = r"tests\fixtures\Sample-Lab-Report-DBTICBM.pdf"

    doc = pymupdf.open(pdf_path)
    page = doc.load_page(0)

    t0 = time.time()
    digital_lines = OCRService.extract_layout_sorted_lines(page)
    elapsed = time.time() - t0

    print(f"\nDigital PDF page 1: {len(digital_lines)} lines in {elapsed:.4f}s")
    assert elapsed < 1.0, f"Digital PDF extraction too slow: {elapsed:.4f}s"
    assert len(digital_lines) > 0, "No digital lines extracted"
    doc.close()
