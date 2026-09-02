import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService

def test_drlogy_pathology_lab_cbc_extraction():
    """
    Test case reproducing Drlogy Pathology Lab CBC report OCR output layout.
    """
    lines = [
        "DRLOGY PATHOLOGY LAB",
        "105-108, SMART VISION COMPLEX, HEALTHCARE ROAD, MUMBAI - 689578",
        "Yashvi M. Patel",
        "Age : 21 Years",
        "Sex : Female",
        "UHID : 556",
        "Complete Blood Count (CBC)",
        "Investigation Result Reference Value Unit",
        "Hemoglobin (Hb)",
        "13.00 Normal 13.00 - 17.00 g/dL",
        "Total RBC count",
        "5.00 Normal 4.50 - 5.50 mill/cumm",
        "Packed Cell Volume (PCV)",
        "45 Normal 40 - 50 %",
        "Mean Corpuscular Volume (MCV)",
        "100 Normal 83 - 101 fL",
        "MCH",
        "30 Normal 27 - 32 pg",
        "MCHC",
        "33.00 Normal 32.50 - 34.50 g/dL",
        "RDW",
        "12.00 Normal 11.60 - 14.00 %",
        "Total WBC count",
        "10000 Normal 4000 - 11000 cumm",
        "Neutrophils",
        "60 Normal 50 - 62 %",
        "Lymphocytes",
        "30 Normal 20 - 40 %",
        "Eosinophils",
        "2 Normal 00 - 06 %",
        "Monocytes",
        "8 Normal 00 - 10 %",
        "Basophils",
        "0 Normal 00 - 02 %",
        "Platelet Count",
        "20000 Normal 150000 - 410000 cumm",
        "****End of Report****"
    ]
    
    extracted = ParserService.parse_document_text("rep_drlogy_test", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)
    
    # Demographics
    assert normalized.patient.age == 21
    assert normalized.patient.gender == "Female"
    assert normalized.patient.patient_id == "556"
    assert normalized.report.lab_name == "Drlogy Pathology Lab"
    
    # Test count (all 13 lab tests extracted!)
    assert len(normalized.tests) >= 13
    
    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}
    
    # Hemoglobin
    assert "HEMOGLOBIN" in tests_by_id
    assert tests_by_id["HEMOGLOBIN"].value == 13.00
    assert tests_by_id["HEMOGLOBIN"].status == "NORMAL"
    
    # Platelet Count (20000 vs ref 150000 - 410000 -> LOW / RED_FLAG)
    assert "PLATELETS" in tests_by_id
    assert tests_by_id["PLATELETS"].value == 20000.0
    assert tests_by_id["PLATELETS"].status == "LOW"
    assert tests_by_id["PLATELETS"].flag == "RED_FLAG"
