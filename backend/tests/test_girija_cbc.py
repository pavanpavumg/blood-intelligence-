import pytest
from pathlib import Path
import fitz
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_girija_cbc_pdf_extraction():
    """
    Regression test fixture verifying extraction on BNG2666471_MrsGIRIJA.pdf.
    """
    pdf_path = Path(r"c:\Users\TezHealth\Desktop\blood-test-intelligence\backend\data\uploads\rep_3a3a30e98aa6_BNG2666471_MrsGIRIJA.pdf")
    assert pdf_path.exists(), f"PDF fixture not found at {pdf_path}"

    doc = fitz.open(pdf_path)
    extracted_lines = []
    for page in doc:
        page_lines = OCRService.extract_layout_sorted_lines(page)
        extracted_lines.extend(page_lines)

    parsed = ParserService.parse_document_text("rep_girija_test", extracted_lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)

    # 1-5. Metadata Assertions
    assert normalized.patient.name == "Mrs. GIRIJA"
    assert normalized.patient.age == 75
    assert normalized.patient.gender == "Female"
    assert normalized.patient.patient_id == "3494187"
    assert normalized.report.report_date == "2026-06-23T10:55:00"

    # 6. Test count (exactly 13 lab tests)
    assert len(normalized.tests) == 13

    # 7-11. Metadata leakage assertion: No metadata or header terms inside tests[]
    invalid_terms = ["name", "girija", "vial", "req no", "sample type", "collected on", "registered on", "reported on", "client name"]
    for test in normalized.tests:
        test_name_lower = (test.raw_test_name or "").lower()
        for term in invalid_terms:
            assert term not in test_name_lower, f"Metadata term '{term}' incorrectly leaked into test_name: '{test.raw_test_name}'"

    # 21. No false reference-range warnings from metadata
    for warning in normalized.warnings:
        assert "Years / Female" not in warning
        assert "Vial ID" not in warning

    # Map tests by test_id / canonical name
    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}

    # 12. Hemoglobin (6.5 gm% 12.0 - 15.0 -> LOW / RED_FLAG)
    assert "HEMOGLOBIN" in tests_by_id
    hgb = tests_by_id["HEMOGLOBIN"]
    assert hgb.value == 6.5
    assert hgb.raw_unit == "gm%"
    assert hgb.normalized_unit == "gm%"
    assert hgb.reference_range is not None
    assert hgb.reference_range.low == 12.0
    assert hgb.reference_range.high == 15.0
    assert hgb.status == "LOW"
    assert hgb.flag == "RED_FLAG"
    assert hgb.mapping_status == "MAPPED"

    # 13. RBC (2.74 millions/cumm 4.50 - 5.50 -> LOW / RED_FLAG)
    assert "RBC" in tests_by_id
    rbc = tests_by_id["RBC"]
    assert rbc.value == 2.74
    assert rbc.raw_unit == "millions/cumm"
    assert rbc.normalized_unit == "millions/cumm"
    assert rbc.reference_range.low == 4.5
    assert rbc.reference_range.high == 5.5
    assert rbc.status == "LOW"
    assert rbc.flag == "RED_FLAG"

    # 14. WBC (14800 cells/cumm 4000-11000 -> HIGH / RED_FLAG)
    assert "WBC" in tests_by_id
    wbc = tests_by_id["WBC"]
    assert wbc.value == 14800.0
    assert wbc.raw_unit == "cells/cumm"
    assert wbc.normalized_unit == "cells/cumm"
    assert wbc.reference_range.low == 4000.0
    assert wbc.reference_range.high == 11000.0
    assert wbc.status == "HIGH"
    assert wbc.flag == "RED_FLAG"

    # 15. Platelet (3.07 lakhs/cumm 1.5 - 4.5 -> NORMAL / NONE)
    assert "PLATELETS" in tests_by_id
    plt = tests_by_id["PLATELETS"]
    assert plt.value == 3.07
    assert plt.raw_unit == "lakhs/cumm"
    assert plt.normalized_unit == "lakhs/cumm"
    assert plt.reference_range.low == 1.5
    assert plt.reference_range.high == 4.5
    assert plt.status == "NORMAL"
    assert plt.flag == "NONE"

    # 16 & 22. MCV (77 fL 80 - 100 -> LOW / RED_FLAG, MAPPED)
    assert "MCV" in tests_by_id
    mcv = tests_by_id["MCV"]
    assert mcv.value == 77.0
    assert mcv.raw_unit == "fL"
    assert mcv.normalized_unit == "fL"
    assert mcv.reference_range.low == 80.0
    assert mcv.reference_range.high == 100.0
    assert mcv.status == "LOW"
    assert mcv.mapping_status == "MAPPED"

    # 17. MCH (23.7 pg 27 - 33 -> LOW / RED_FLAG)
    assert "MCH" in tests_by_id
    mch = tests_by_id["MCH"]
    assert mch.value == 23.7
    assert mch.raw_unit == "pg"
    assert mch.normalized_unit == "pg"
    assert mch.reference_range.low == 27.0
    assert mch.reference_range.high == 33.0
    assert mch.status == "LOW"

    # 18 & 23. MCHC (30.6 g/dL 32.0 - 34.0 -> LOW / RED_FLAG, MAPPED)
    assert "MCHC" in tests_by_id
    mchc = tests_by_id["MCHC"]
    assert mchc.value == 30.6
    assert mchc.raw_unit == "g/dL"
    assert mchc.normalized_unit == "g/dL"
    assert mchc.reference_range.low == 32.0
    assert mchc.reference_range.high == 34.0
    assert mchc.status == "LOW"
    assert mchc.mapping_status == "MAPPED"

    # Differential count tests
    assert "NEUTROPHILS" in tests_by_id
    neu = tests_by_id["NEUTROPHILS"]
    assert neu.value == 80.0
    assert neu.status == "HIGH"

    assert "LYMPHOCYTES" in tests_by_id
    lymp = tests_by_id["LYMPHOCYTES"]
    assert lymp.value == 15.0
    assert lymp.status == "LOW"

    assert "EOSINOPHILS" in tests_by_id
    eos = tests_by_id["EOSINOPHILS"]
    assert eos.value == 2.0
    assert eos.status == "NORMAL"

    assert "MONOCYTES" in tests_by_id
    mono = tests_by_id["MONOCYTES"]
    assert mono.value == 3.0
    assert mono.status == "NORMAL"

    assert "BASOPHILS" in tests_by_id
    bas = tests_by_id["BASOPHILS"]
    assert bas.value == 0.0
    assert bas.status == "NORMAL"
