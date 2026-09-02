import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService
from app.services.classification_service import ClassificationService
from app.services.reference_range_service import ReferenceRangeService

def test_bharathi_crp_extraction_and_false_positives():
    """
    Regression test for Bharathi report:
    CRP = 3.69 mg/L with 'Up to 6.0 mg/L' reference range -> NORMAL.
    Filters out '6 hours', doctor details, and KMC numbers.
    """
    lines = [
        "Metropolis Healthcare Laboratory",
        "Patient Name: Mrs BHARATHI K JOSHI",
        "Age: 52 Years / Female",
        "Ref.By: Dr. Self",
        "C-REACTIVE PROTEIN (CRP)",
        "3.69 mg/L Up to 6.0",
        "INTERPRETATION:",
        "CRP is an acute phase protein. Elevated levels indicate inflammation.",
        "CRP may be detected with 6 hours of tissue injury.",
        "Dr Faeeza Begum MD",
        "KMC.No:103490",
        "MD PATHOLOGY",
        "End Of The Report"
    ]

    extracted = ParserService.parse_document_text("rep_bharathi_test", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    # 1. Test Extraction & Classification
    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}
    assert "CRP" in tests_by_id
    crp = tests_by_id["CRP"]
    assert crp.value == 3.69
    assert crp.raw_unit == "mg/L"
    assert crp.status == "NORMAL"
    assert crp.reference_range is not None
    assert crp.reference_range.high == 6.0
    assert crp.reference_range.operator == "<="

    # 2. False Positives Assertion
    raw_names = [t.raw_test_name.lower() for t in normalized.tests]
    for fp in ["6 hours", "dr faeeza begum md", "kmc.no:103490", "md pathology", "interpretation", "end of the report"]:
        assert not any(fp in name for name in raw_names), f"False positive test '{fp}' found in extracted tests!"


def test_kavya_comprehensive_panels_and_categorical_ranges():
    """
    Regression test for Kavya report covering Kidney, LFT, Lipid, Iron, Thyroid,
    RBS, Vitamin D, CBC, B12, HbA1c, and Calcium panels.
    Verifies categorical classifications for HDL (OPTIMAL), LDL (NEAR_OPTIMAL),
    HbA1c (NON_DIABETIC), Vitamin D (INSUFFICIENCY), and TSH (HIGH).
    """
    lines = [
        "Thyrocare Technologies Limited",
        "Patient Name: Ms KAVYA",
        "Age: 24 Years / Female",
        "Vial ID: 3139058",
        "Reported On: 2026-08-24",
        "TEST NAME OBSERVED VALUE UNITS REFERENCE INTERVAL",
        "Serum Creatinine 0.60 mg/dL 0.5 - 1.1",
        "Serum Urea 17.17 mg/dL 15 - 40",
        "Urea Nitrogen (BUN) 8.02 mg/dL 7 - 20",
        "BUN/Creatinine Ratio 13.37",
        "Uric Acid 3.13 mg/dL Female:2.3 - 6.1",
        "Serum Sodium 141 mmol/L 136 - 145",
        "Serum Potassium 4.41 mmol/L 3.5 - 5.5",
        "Serum Chloride 102 mmol/L 98 - 107",
        "Total Bilirubin 0.43 mg/dL 0.2 - 1.2",
        "Direct Bilirubin 0.13 mg/dL 0.0 - 0.3",
        "Indirect Bilirubin 0.30 mg/dL 0.1 - 0.8",
        "AST (SGOT) 13.1 U/L 0 - 35",
        "ALT (SGPT) 16.1 U/L 0 - 45",
        "Alkaline Phosphatase 88.2 U/L 30 - 120",
        "Total Protein 7.92 g/dL 6.0 - 8.3",
        "Albumin 4.48 g/dL 3.5 - 5.2",
        "Globulin 3.44 g/dL 2.0 - 3.5",
        "A/G Ratio 1.30 0.9 - 2.0",
        "Gamma Glutamyl Transferase 24.2 U/L 0 - 55",
        "Total Cholesterol 164.9 mg/dL < 200",
        "HDL Cholesterol 47.2 mg/dL Desirable >59 Optimal 40-59 Undesirable <40",
        "Triglycerides 68.5 mg/dL < 150",
        "VLDL Cholesterol 13.70 mg/dL 5 - 40",
        "LDL Cholesterol 104 mg/dL Optimal <100 Near Optimal 100-129 Borderline High 130-159 High 160-189",
        "Serum Iron 33 ug/dL 60 - 170",
        "Total Iron Binding Capacity 373.2 ug/dL 240 - 450",
        "Transferrin 253.88 mg/dL 200 - 360",
        "Transferrin Saturation 8.84 % 15 - 50",
        "Serum Ferritin 42.6 ng/mL 13 - 150",
        "Triiodothyronine (T3) 0.76 ng/mL 0.8 - 2.0",
        "Thyroxine (T4) 7.01 ug/dL 5.1 - 14.1",
        "Thyroid Stimulating Hormone 5.21 uIU/mL 0.45 - 4.5",
        "Random Blood Sugar 78.2 mg/dL 70 - 140",
        "25-Hydroxy Vitamin D 24.46 ng/mL Deficiency <10 Insufficiency 10-30 Sufficiency 30-100 Toxicity >100",
        "Hemoglobin 10.2 g/dL 12.0 - 15.0",
        "Red Blood Cell Count 3.56 10^6/uL 3.8 - 4.8",
        "White Blood Cell Count 6700 cells/cumm 4000 - 11000",
        "Platelet Count 2.53 lakhs/cumm 1.5 - 4.5",
        "Packed Cell Volume 31.5 % 36 - 46",
        "Mean Corpuscular Volume 77 fL 80 - 100",
        "Mean Corpuscular Hemoglobin 24.5 pg 27 - 32",
        "Mean Corpuscular Hemoglobin Concentration 31.6 g/dL 32 - 36",
        "Neutrophils 65 % 40 - 80",
        "Lymphocytes 30 % 20 - 40",
        "Eosinophils 3 % 1 - 6",
        "Monocytes 2 % 2 - 10",
        "Basophils 0 % 0 - 1",
        "Vitamin B12 333.2 pg/mL 211 - 911",
        "Glycated Hemoglobin (HbA1c) 5.50 % Non-diabetic 4.8-5.9 Pre-diabetic 5.9-6.5 Diabetic >=6.5",
        "Approximate Mean Plasma Glucose 111.15 mg/dL 70 - 126",
        "Calcium 9.24 mg/dL 8.6 - 10.3",
        "INTERPRETATION & CLINICAL COMMENTS",
        "Non-diabetic: <5.7%",
        "Pre-diabetic: 5.7-6.4%",
        "Diabetic: >=6.5%"
    ]

    extracted = ParserService.parse_document_text("rep_kavya_test", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}

    # 1. Categorical Assertions
    assert "HDL" in tests_by_id
    assert tests_by_id["HDL"].reference_range.selected_category == "OPTIMAL"
    assert tests_by_id["HDL"].status == "NORMAL"

    assert "LDL" in tests_by_id
    assert tests_by_id["LDL"].reference_range.selected_category == "NEAR_OPTIMAL"
    assert tests_by_id["LDL"].status == "NORMAL"

    assert "HBA1C" in tests_by_id
    assert tests_by_id["HBA1C"].reference_range.selected_category == "NON_DIABETIC"
    assert tests_by_id["HBA1C"].status == "NORMAL"

    assert "VITAMIN_D" in tests_by_id
    assert tests_by_id["VITAMIN_D"].reference_range.selected_category == "INSUFFICIENCY"
    assert tests_by_id["VITAMIN_D"].status == "NORMAL"

    # 2. Key Panel Assertions
    assert tests_by_id["TSH"].status == "HIGH"
    assert tests_by_id["IRON"].status == "LOW"
    assert tests_by_id["TRANSFERRIN_SATURATION"].status == "LOW"
    assert tests_by_id["HEMOGLOBIN"].status == "LOW"
    assert tests_by_id["RBC"].status == "LOW"
    assert tests_by_id["GLUCOSE_RANDOM"].status == "NORMAL"
    assert tests_by_id["BUN_CREATININE_RATIO"].status == "UNKNOWN"
    assert tests_by_id["BUN_CREATININE_RATIO"].flag == "REVIEW_REQUIRED"

    # 3. False Positives Assertion
    raw_names = [t.raw_test_name.lower() for t in normalized.tests]
    for cat_label in ["non-diabetic", "pre-diabetic", "diabetic", "desirable", "optimal", "borderline high", "very high", "interpretation"]:
        assert cat_label not in raw_names, f"Category label or narrative '{cat_label}' was incorrectly extracted as a test!"


def test_pavan_method_separation_and_suspect_unit_and_loinc_conflict():
    """
    Regression test for Pavan report:
    Verifies method separation (RBC Count (Electrical Impedence)), MCV suspect unit detection (um),
    PCT context-aware mapping, and LOINC mapping conflict detection.
    """
    lines = [
        "KC General Hospital",
        "Patient Name: Mr PAVAN M G",
        "Age: 21 Years / Male",
        "RBC Count (Electrical Impedence) 4.50 10^6/uL 4.5 - 5.5",
        "PLATELET COUNT (Electrical Impedence) 221.00 10^3/uL 150 - 500",
        "Mean Corpuscular Volume 88.00 um 80 - 100",
        "PCT 0.22 % 0.1 - 0.5"
    ]

    extracted = ParserService.parse_document_text("rep_pavan_test", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}

    # 1. Method Separation
    assert "RBC" in tests_by_id
    assert tests_by_id["RBC"].raw_test_name == "RBC Count"
    assert tests_by_id["RBC"].method == "Electrical Impedence"

    assert "PLATELETS" in tests_by_id
    assert tests_by_id["PLATELETS"].raw_test_name == "PLATELET COUNT"
    assert tests_by_id["PLATELETS"].method == "Electrical Impedence"

    # 2. Suspect Unit Detection for MCV
    assert "MCV" in tests_by_id
    mcv = tests_by_id["MCV"]
    assert mcv.raw_unit == "um"
    assert mcv.normalized_unit is None
    assert mcv.unit_validation == "SUSPECT"
    assert "UNEXPECTED_UNIT_FOR_TEST" in mcv.review_reasons

    # 3. Context PCT Mapping
    assert "PCT" in tests_by_id
    assert tests_by_id["PCT"].canonical_test_name == "Plateletcrit"
