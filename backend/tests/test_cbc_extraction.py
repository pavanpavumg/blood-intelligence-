import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_kc_general_hospital_cbc_extraction():
    """
    Test case reproducing K C GENERAL HOSPITAL CBC report layout.
    """
    lines = [
        "K C GENERAL HOSPITAL",
        "3RD CROSS MALLESHWARAM, BANGALORE-560003",
        "UHID: KCG-202600034148",
        "Patient: Mr PAVAN M G Sex: Male",
        "Address: TUMKUR ,Karnataka,India",
        "Mobile No: 6360270028",
        "Age: 21 Years, 0 Month, 0 Days Date: 26-03-2026",
        "Visit ID: 1546301",
        "Final Report 26-03-2026 02:43 PM",
        "CBC",
        "WBC - 5.79 10^3 4 - 10 10(3)/mm3",
        "RBC Count (Electrical Impedence) - 4.41 milln/ul 3.8 - 6.5 10^6/L",
        "HGB (Hemoglobin) - 15.90 g/dL 11.5 - 17",
        "HCT - 43.30 % 37 - 54",
        "Mean Corpuscular Vol(MCV) - 98.20 um 80 - 100 um",
        "Mean Corpuscular Hb.(MCH) - 36.10 pg 27 - 32 pg",
        "Mean Corp.Hb.Con. (MCHC) - 36.70 g/dL 32 - 36",
        "PLATELET COUNT (Electrical Impedence) - 221.00 10^3 150 - 500",
        "RDW-SD - 46.60 fL 40.0 - 55.0",
        "RDW-CV - 12.80 % 11.0 - 15.0",
        "MPV - 9.90 fl 6 - 11.0",
        "P-LCR - 23.40 % 15 - 35",
        "PCT - 0.22 % less than 0.5 %",
        "Neutrophils - 57.00 % 40-80",
        "Lymphocytes - 28.00 % 20-40",
        "Eosinophils - 7.80 % 1-6",
        "Basophils - 0.50 % <1%",
        "IG - 0.50 % %",
        "Monocytes - 6.70 % 2-10%",
        "This Report is Only for Given Sample",
        "------END OF REPORT------",
        "Dr. GANESH B D 1",
        "MD pathology",
    ]

    extracted = ParserService.parse_document_text("rep_kc_general", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    # Demographics
    assert normalized.patient.name == "Mr PAVAN M G"
    assert normalized.patient.age == 21
    assert normalized.patient.gender == "Male"
    assert normalized.patient.patient_id == "KCG-202600034148"
    assert normalized.report.report_date == "2026-03-26"

    # Test count (all 19 CBC tests extracted!)
    assert len(normalized.tests) == 19

    # Specific test assertions
    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}

    # WBC
    assert "WBC" in tests_by_id
    assert tests_by_id["WBC"].value == 5.79
    assert tests_by_id["WBC"].status == "NORMAL"

    # Hemoglobin
    assert "HEMOGLOBIN" in tests_by_id
    assert tests_by_id["HEMOGLOBIN"].value == 15.90
    assert tests_by_id["HEMOGLOBIN"].status == "NORMAL"

    # Eosinophils (7.8% vs ref 1-6 -> HIGH / RED_FLAG)
    assert "EOSINOPHILS" in tests_by_id
    assert tests_by_id["EOSINOPHILS"].value == 7.80
    assert tests_by_id["EOSINOPHILS"].status == "HIGH"
    assert tests_by_id["EOSINOPHILS"].flag == "RED_FLAG"
