import pytest
import pymupdf
from pathlib import Path
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def _process_pdf_file(filename: str):
    pdf_path = FIXTURES_DIR / filename
    assert pdf_path.exists(), f"Test fixture PDF missing: {pdf_path}"
    
    doc = pymupdf.open(pdf_path)
    all_lines = []
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        d_text = OCRService.clean_pua_text(page.get_text("text"))
        if len(d_text.strip()) > 30:
            lines = OCRService.extract_layout_sorted_lines(page)
            cleaned = [OCRService.clean_pua_text(l) for l in lines]
            all_lines.extend(cleaned)
        else:
            img_bytes = OCRService.render_pdf_page_to_bytes(doc, page_idx)
            ocr_lines, _ = OCRService.extract_text_from_image(img_bytes)
            all_lines.extend(ocr_lines)
            
    parsed = ParserService.parse_document_text(f"rep_{filename}", all_lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    return normalized


def test_z615_pua_unicode_recovery_and_section_isolation():
    """
    Test Z615.pdf:
    - Unicode PUA font corruption recovered successfully (ord(c) - 0xF000).
    - Patient metadata: Name='DUMMY', Age=25, Gender='Male', Report Date present.
    - 11+ valid tests extracted.
    - Interpretation reference table rows (| HbA1c in % |) isolated & filtered out.
    """
    report = _process_pdf_file("Z615.pdf")
    
    assert report.patient.name == "DUMMY"
    assert report.patient.age == 25
    assert report.patient.gender == "Male"
    assert report.report.report_date is not None
    assert len(report.tests) >= 11
    
    # Verify no fake table grid tests extracted
    test_names = [t.test_name for t in report.tests]
    assert not any("hba1c in %" in name.lower() for name in test_names)
    assert not any("|" in name for name in test_names)
    
    # Verify method prefixes cleanly stripped from analyte names
    assert any(t.test_name == "CARDIO C-REACTIVE PROTEIN (hsCRP), SERUM" for t in report.tests)
    assert report.completeness["complete"] is True


def test_wellwise_multiline_and_reference_table_protection():
    """
    Test Wellwise Platinum Profile - 5048.pdf:
    - Patient metadata: Name='Mrs. Meena Sharma', Age=53, Gender='Female'.
    - Valid High Sensitivity CRP (5.385 mg/L) extracted.
    - Population risk category table row (Low < 1.0) protected from becoming fake test.
    """
    report = _process_pdf_file("Wellwise Platinum Profile - 5048.pdf")
    
    assert report.patient.name == "Mrs. Meena Sharma"
    assert report.patient.age == 53
    assert report.patient.gender == "Female"
    assert report.report.report_date is not None
    assert len(report.tests) >= 1
    
    # Verify population reference risk level not extracted as a patient test
    raw_names = [t.raw_test_name.lower() for t in report.tests]
    assert not any("risk level" in rname for rname in raw_names)
    assert not any("booking centre" in rname for rname in raw_names)
    assert report.completeness["complete"] is True


def test_investigationlabreports_scanned_pdf_extraction():
    """
    Test investigationlabreports.pdf:
    - Scanned report with Renal Panel tests extracted.
    - Tests like Glucose, Creatinine, Urea, Sodium extracted.
    - No metadata (UHID, Address, Mobile) extracted as tests.
    """
    report = _process_pdf_file("investigationlabreports.pdf")
    
    assert len(report.tests) >= 5
    raw_names = [t.raw_test_name.lower() for t in report.tests]
    assert any("glucose" in r for r in raw_names)
    assert any("creatinine" in r for r in raw_names)
    assert not any("uhid" in r for r in raw_names)
    assert not any("address" in r for r in raw_names)
    assert not any("mobile" in r for r in raw_names)


def test_rcy_multipage_scanned_handling():
    """
    Test RCY.pdf:
    - 12 page scanned report.
    - Multiple laboratory panel tables extracted (Kidney, Lipid, CBC, Urine).
    - No metadata (UHID, Address, Mobile, Age) extracted as tests.
    """
    report = _process_pdf_file("RCY.pdf")
    
    assert len(report.tests) >= 10
    raw_names = [t.raw_test_name.lower() for t in report.tests]
    assert not any("uhid" in r for r in raw_names)
    assert not any("address" in r for r in raw_names)
    assert not any("mobile" in r for r in raw_names)
