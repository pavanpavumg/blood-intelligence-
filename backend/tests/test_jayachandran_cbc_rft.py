import pytest
from pathlib import Path
import fitz
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_jayachandran_cbc_rft_extraction():
    """
    Regression test verifying extraction on Mr.JAYACHANDRAN_KAD393.4.PDF (26 tests, CBC + RFT).
    """
    uploads_dir = Path(
        r"c:\Users\TezHealth\Desktop\blood-test-intelligence\backend\data\uploads"
    )
    pdf_path = None
    for f in uploads_dir.glob("*.pdf"):
        if "JAYACHANDRAN" in f.name:
            pdf_path = f
            break

    assert (
        pdf_path is not None and pdf_path.exists()
    ), "Mr.JAYACHANDRAN_KAD393.4.PDF fixture not found"

    doc = fitz.open(pdf_path)
    extracted_lines = []
    for page in doc:
        page_lines = OCRService.extract_layout_sorted_lines(page)
        extracted_lines.extend(page_lines)

    parsed = ParserService.parse_document_text("rep_jayachandran_test", extracted_lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)

    # 1. Total test count assertion (26 tests)
    assert len(normalized.tests) == 26

    # 2-5. Demographics assertions
    assert normalized.patient.name == "Mr.JAYACHANDRAN"
    assert normalized.patient.age == 69
    assert normalized.patient.gender == "Male"
    assert normalized.patient.patient_id == "KAD393.00000004"

    # 6-7. Report Date & Discrepancy warning assertions
    assert normalized.report.report_date == "2026-08-05T14:13:00"
    assert any(
        "Reported" in w or "timestamp" in w.lower() or "report date" in w.lower()
        for w in normalized.warnings
    )

    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}
    tests_by_raw_name = {t.raw_test_name.strip(): t for t in normalized.tests}

    # 8-12. False-positive metadata/interpretation/doctor leakage prevention
    invalid_terms = [
        "jayachandran",
        "kad393",
        "h5672528",
        "tez health",
        "self",
        "dr. impana",
        "dr. nithyanandam",
        "mc-6941",
        "interpretation notes",
        "complete blood count gives",
        "kidney/renal function tests",
        "barcode",
    ]
    for test in normalized.tests:
        name_lower = test.raw_test_name.lower()
        for term in invalid_terms:
            assert (
                term not in name_lower
            ), f"Metadata/narrative term '{term}' leaked into test: '{test.raw_test_name}'"

    # 13. RBC unit normalized correctly
    assert "RBC" in tests_by_id
    rbc = tests_by_id["RBC"]
    assert rbc.value == 3.31
    assert rbc.raw_unit == "Millions/cumm"
    assert rbc.normalized_unit == "millions/cumm"
    assert rbc.reference_range is not None
    assert "Electrical Impedance" not in rbc.reference_range.raw
    assert rbc.reference_range.raw == "4.5 - 5.9"

    # 14. WBC unit normalized correctly
    assert "WBC" in tests_by_id
    wbc = tests_by_id["WBC"]
    assert wbc.value == 7950.0
    assert wbc.raw_unit == "Cells/cumm"
    assert wbc.normalized_unit == "cells/cumm"
    assert wbc.reference_range is not None
    assert "Electrical Impedance" not in wbc.reference_range.raw
    assert wbc.reference_range.raw == "4000 - 10000"

    # 15. Platelet unit normalized correctly
    assert "PLATELETS" in tests_by_id
    plt = tests_by_id["PLATELETS"]
    assert plt.value == 101.0
    assert plt.normalized_unit == "10^3/uL"

    # 16. MCV preserves blank unit (no invented unit)
    assert "MCV" in tests_by_id
    mcv = tests_by_id["MCV"]
    assert mcv.value == 89.8
    assert mcv.raw_unit is None
    assert mcv.normalized_unit is None

    # 17. Haemoglobin reference raw excludes method
    assert "HEMOGLOBIN" in tests_by_id
    hb = tests_by_id["HEMOGLOBIN"]
    assert hb.value == 10.5
    assert "Spectrophotometry" not in hb.reference_range.raw
    assert hb.reference_range.raw == "13.0 - 17.0"

    # 20-21. Creatinine gender-specific range (Male 0.70 - 1.20) & HIGH status
    assert "CREATININE" in tests_by_id
    creat = tests_by_id["CREATININE"]
    assert creat.value == 2.62
    assert creat.reference_range is not None
    assert creat.reference_range.low == 0.70
    assert creat.reference_range.high == 1.20
    assert creat.status == "HIGH"
    assert creat.flag == "RED_FLAG"

    # 22-23. Uric Acid Male range (3.4 - 7.0) & NORMAL status
    assert "URIC_ACID" in tests_by_id
    uric = tests_by_id["URIC_ACID"]
    assert uric.value == 4.85
    assert uric.reference_range is not None
    assert uric.reference_range.low == 3.4
    assert uric.reference_range.high == 7.0
    assert "Uricase" not in uric.reference_range.raw
    assert uric.status == "NORMAL"

    # 24-26. BUN/Cr Ratio is NOT mapped to BUN, reference_range is None, status UNKNOWN
    assert "BUN_CREATININE_RATIO" in tests_by_id
    bun_cr = tests_by_id["BUN_CREATININE_RATIO"]
    assert bun_cr.test_id != "BUN"
    assert bun_cr.value == 10.08
    assert bun_cr.reference_range is None
    assert bun_cr.status == "UNKNOWN"

    # 27. MCH mapped
    assert "MCH" in tests_by_id
    mch = tests_by_id["MCH"]
    assert mch.value == 31.6
    assert mch.canonical_test_name == "Mean Corpuscular Hemoglobin"

    # 28. PDW mapped
    assert "PDW" in tests_by_id
    pdw = tests_by_id["PDW"]
    assert pdw.value == 16.8
    assert pdw.canonical_test_name == "Platelet Distribution Width"

    # 29. Calcium mapped
    assert "CALCIUM" in tests_by_id
    ca = tests_by_id["CALCIUM"]
    assert ca.value == 8.03
    assert ca.canonical_test_name == "Calcium"
    assert ca.status == "LOW"

    # 30. Neutrophils test_name == "Neutrophils"
    assert "NEUTROPHILS" in tests_by_id
    neu = tests_by_id["NEUTROPHILS"]
    assert neu.test_name == "Neutrophils"
    assert neu.raw_test_name == "Neutrophils"
    assert neu.value == 59.2
