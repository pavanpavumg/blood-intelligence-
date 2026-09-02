import pytest
from pathlib import Path
import fitz
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_bharathi_multi_panel_extraction():
    """
    Multi-panel regression test fixture verifying extraction on BNG2611421_MrsBHARATHIKJOSHI.pdf.
    """
    uploads_dir = Path(r"c:\Users\TezHealth\Desktop\blood-test-intelligence\backend\data\uploads")
    pdf_path = None
    for f in uploads_dir.glob("*.pdf"):
        if "2611421" in f.name or "BHARATHI" in f.name:
            pdf_path = f
            break

    assert pdf_path is not None and pdf_path.exists(), "BNG2611421_MrsBHARATHIKJOSHI.pdf fixture not found"

    doc = fitz.open(pdf_path)
    extracted_lines = []
    for page in doc:
        page_lines = OCRService.extract_layout_sorted_lines(page)
        extracted_lines.extend(page_lines)

    parsed = ParserService.parse_document_text("rep_bharathi_test", extracted_lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)

    # Demographics & Consistency-aware Vial ID resolution
    assert normalized.patient.name == "Mrs. BHARATHI K JOSHI"
    assert normalized.patient.age == 63
    assert normalized.patient.gender == "Female"
    assert normalized.patient.patient_id == "2950084"
    assert normalized.report.report_date == "2026-02-03T18:11:00"

    # Laboratory Name Extraction
    assert normalized.report.lab_name == "CENTROMED LABS PVT. LTD"

    # Total Test Count Assertion (22 lab tests)
    assert len(normalized.tests) == 22

    # Explicit warning for Vial ID discrepancy & Report Date discrepancy
    assert any("Discrepancy in Vial ID" in w for w in normalized.warnings)
    assert any(
        "Reported On" in w or "report date" in w.lower() or "timestamp" in w.lower()
        for w in normalized.warnings
    )

    tests_by_name = {t.raw_test_name.strip(): t for t in normalized.tests}
    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}

    # 1-5. CRP Assertions
    assert "CRP" in tests_by_id
    crp = tests_by_id["CRP"]
    assert crp.value == 3.69
    assert crp.raw_unit == "mg/L"
    assert crp.normalized_unit == "mg/L"
    assert crp.reference_range is not None
    assert crp.reference_range.high == 6.0
    assert crp.status == "NORMAL"
    assert crp.flag == "NONE"

    # 6-8, 17-20. Interpretation & Doctor Signature Exclusion Assertions
    invalid_terms = ["dr faeeza", "kmc.no", "103490", "acute phase", "detoxification", "inflammatory", "kidney disease"]
    for test in normalized.tests:
        name_lower = test.raw_test_name.lower()
        for term in invalid_terms:
            assert term not in name_lower, f"Narrative/doctor text '{term}' incorrectly leaked into test row: '{test.raw_test_name}'"

    # 9. CBC Tests Extracted & MCHC Normalization
    assert "HEMOGLOBIN" in tests_by_id
    assert tests_by_id["HEMOGLOBIN"].value == 12.3
    assert tests_by_id["HEMOGLOBIN"].raw_unit == "gm%"

    assert "RBC" in tests_by_id
    assert tests_by_id["RBC"].value == 4.56
    assert tests_by_id["RBC"].raw_unit == "millions/cumm"

    assert "WBC" in tests_by_id
    assert tests_by_id["WBC"].value == 9100.0

    assert "PLATELETS" in tests_by_id
    assert tests_by_id["PLATELETS"].value == 2.53

    assert "MCHC" in tests_by_id
    mchc = tests_by_id["MCHC"]
    assert mchc.raw_test_name == "* M C H C"
    assert mchc.test_name == "* MCHC"
    assert mchc.test_id == "MCHC"

    # 10-12. Kidney Screen Tests Extracted & Unit-less BUN/Creatinine Ratio
    assert "CREATININE" in tests_by_id
    assert tests_by_id["CREATININE"].value == 0.83
    assert tests_by_id["CREATININE"].raw_unit == "mg/dL"

    assert "UREA" in tests_by_id
    assert tests_by_id["UREA"].value == 20.0

    assert "BUN" in tests_by_id
    assert tests_by_id["BUN"].value == 9.35

    assert "BUN_CREATININE_RATIO" in tests_by_id
    bun_cr = tests_by_id["BUN_CREATININE_RATIO"]
    assert bun_cr.value == 11.26
    assert bun_cr.raw_unit is None
    assert bun_cr.reference_range is None
    assert bun_cr.status == "UNKNOWN"
    assert bun_cr.flag == "REVIEW_REQUIRED"
    assert bun_cr.mapping_status == "MAPPED"

    # 13. URIC ACID gender-specific range & Method text exclusion
    assert "URIC_ACID" in tests_by_id
    uric = tests_by_id["URIC_ACID"]
    assert uric.value == 3.46
    assert uric.reference_range.low == 2.3
    assert uric.reference_range.high == 6.1
    assert "Method:" not in uric.reference_range.raw
    assert "Uricase-Peroxidase" not in uric.reference_range.raw
    assert uric.status == "NORMAL"
    assert uric.flag == "NONE"

    # 14. Sodium classification (140 -> NORMAL)
    assert "SODIUM" in tests_by_id
    so = tests_by_id["SODIUM"]
    assert so.value == 140.0
    assert so.status == "NORMAL"

    # 15. Potassium classification (3.19 -> LOW / RED_FLAG)
    assert "POTASSIUM" in tests_by_id
    po = tests_by_id["POTASSIUM"]
    assert po.value == 3.19
    assert po.status == "LOW"
    assert po.flag == "RED_FLAG"

    # 16. Chloride classification (102 -> NORMAL)
    assert "CHLORIDE" in tests_by_id
    cl = tests_by_id["CHLORIDE"]
    assert cl.value == 102.0
    assert cl.status == "NORMAL"
