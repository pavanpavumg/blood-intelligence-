import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_regression_a_chol_hdl_ratio():
    """
    A. CHOL/HDL Ratio
    Input: CHOL/HDL Ratio = 3.26
    Expected:
        test_name = CHOL/HDL Ratio
        value = 3.26
        unit = null
        reference_range = null
        status = REPORTED
        flag = NONE
    Must NOT inherit HDL's reference range.
    Must NOT be LOW or RED_FLAG.
    """
    lines = [
        "LIPID PROFILE",
        "HDL Cholesterol 47.3 mg/dL > 40",
        "CHOL / HDL Ratio = 3.26",
    ]
    extracted = ParserService.parse_document_text("test_a", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    ratio_test = next((t for t in normalized.tests if "ratio" in t.raw_test_name.lower()), None)
    assert ratio_test is not None, "CHOL / HDL Ratio should be extracted"
    assert ratio_test.value == 3.26
    assert ratio_test.raw_unit is None
    assert ratio_test.reference_range is None
    assert ratio_test.status == "REPORTED"
    assert ratio_test.flag == "NONE"


def test_regression_b_hdl_categories():
    """
    B. HDL
    Input: HDL = 47.3 mg/dL
    Reference categories:
        Desirable >59
        Optimal 40-59
        Undesirable <40
    Expected:
        value = 47.3
        unit = mg/dL
        preserve categories (>59, 40-59, <40)
        classify 47.3 as Optimal/Normal
        Do NOT create Undesirable = 40 as a test!
    """
    lines = [
        "HDL Cholesterol 47.3 mg/dL",
        "Desirable >59",
        "Optimal 40-59",
        "Undesirable <40",
    ]
    extracted = ParserService.parse_document_text("test_b", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1, "Only HDL Cholesterol should be emitted as a test"
    hdl = normalized.tests[0]
    assert hdl.value == 47.3
    assert hdl.raw_unit == "mg/dL"
    assert hdl.reference_range is not None
    assert hdl.reference_range.selected_category == "OPTIMAL"
    assert hdl.status == "NORMAL"
    assert hdl.flag == "NONE"
    # Ensure categories are preserved in metadata
    raw_ref = hdl.reference_range.raw
    assert "40" in raw_ref and "59" in raw_ref


def test_regression_c_vitamin_b12():
    """
    C. Vitamin B12
    Input: Vitamin B12 = 360.2 pg/mL, reference = 180-916
    Expected:
        test_name = Vitamin B12
        value = 360.2
        unit = pg/mL
        reference = 180-916
    Must NOT produce Vitamin B1 = 2.
    """
    lines = [
        "Vitamin B12 360.2 pg/mL 180 - 916",
    ]
    extracted = ParserService.parse_document_text("test_c", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    test = normalized.tests[0]
    assert "b12" in test.raw_test_name.lower() or "b12" in (test.test_name or "").lower()
    assert test.value == 360.2
    assert test.raw_unit == "pg/mL"
    assert test.reference_range.low == 180.0
    assert test.reference_range.high == 916.0

    # Also test with hyphenated or spaced OCR variations
    lines2 = [
        "Vitamin - B12 360.2 pg/mL 180-916",
    ]
    extracted2 = ParserService.parse_document_text("test_c2", lines2)
    assert extracted2.tests[0].value == 360.2
    assert extracted2.tests[0].unit == "pg/mL"
    assert "b12" in extracted2.tests[0].raw_test_name.lower()


def test_regression_d_hba1c_reference_not_a_test():
    """
    D. HbA1c
    Input:
        HbA1c = 5.2 %
        Pre-diabetic = 5.9-6.5
    Expected:
        only patient result = 5.2
    Must NOT produce Pre-diabetic = 5.9.
    """
    lines = [
        "HbA1c 5.2 %",
        "Non-diabetic 4.8 - 5.9",
        "Pre-diabetic 5.9 - 6.5",
        "Diabetic >= 6.5",
    ]
    extracted = ParserService.parse_document_text("test_d", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1, "Only HbA1c should be extracted as a test"
    hba1c = normalized.tests[0]
    assert hba1c.value == 5.2
    assert hba1c.raw_unit == "%"
    assert hba1c.reference_range.selected_category == "NON_DIABETIC"
    assert hba1c.status == "NORMAL"

    test_names = [t.raw_test_name.lower() for t in normalized.tests]
    assert "pre-diabetic" not in test_names
    assert "diabetic" not in test_names


def test_regression_e_iron_unit_preserved():
    """
    E. Iron
    Expected: Iron = 71 µg/dL
    Do not output 71 g/dL.
    """
    lines = [
        "Iron 71 µg/dL 37 - 145",
    ]
    extracted = ParserService.parse_document_text("test_e", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    iron = normalized.tests[0]
    assert iron.value == 71.0
    assert iron.raw_unit == "µg/dL"
    assert iron.normalized_unit == "µg/dL"
    assert iron.raw_unit != "g/dL"


def test_regression_f_tibc_unit_preserved():
    """
    F. TIBC
    Expected: TIBC = 347.2 µg/dL
    """
    lines = [
        "TIBC 347.2 µg/dL 240 - 450",
    ]
    extracted = ParserService.parse_document_text("test_f", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    tibc = normalized.tests[0]
    assert tibc.value == 347.2
    assert tibc.raw_unit == "µg/dL"
    assert tibc.normalized_unit == "µg/dL"


def test_regression_g_vitamin_d_categories():
    """
    G. Vitamin D
    Expected: 25-OH Vitamin D = 29.22 ng/mL
    Preserve: <10, 10-30, 30-100, >100
    Classify as Insufficiency.
    Do NOT create Sufficiency = 30 or Toxicity = 100 as separate tests.
    """
    lines = [
        "25-OH Vitamin D 29.22 ng/mL",
        "Deficiency <10",
        "Insufficiency 10-30",
        "Sufficiency 30-100",
        "Toxicity >100",
    ]
    extracted = ParserService.parse_document_text("test_g", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    vit_d = normalized.tests[0]
    assert vit_d.value == 29.22
    assert vit_d.raw_unit == "ng/mL"
    assert vit_d.reference_range.selected_category == "INSUFFICIENCY"
    assert vit_d.status == "NORMAL"

    names = [t.raw_test_name.lower() for t in normalized.tests]
    assert "sufficiency" not in names
    assert "toxicity" not in names
    assert "deficiency" not in names


def test_regression_h_thyroid_trimester_references():
    """
    H. Thyroid
    Expected: T3 = 0.93 ng/mL
    Must NOT produce:
        2nd Trimester = 0.91
        3rd Trimester = 1.04
    """
    lines = [
        "T3 0.93 ng/mL",
        "1st trimester 0.71-1.75",
        "2nd trimester 0.91-1.95",
        "3rd trimester 1.04-1.82",
    ]
    extracted = ParserService.parse_document_text("test_h", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    t3 = normalized.tests[0]
    assert t3.value == 0.93
    assert t3.raw_unit == "ng/mL"

    names = [t.raw_test_name.lower() for t in normalized.tests]
    assert "2nd trimester" not in names
    assert "3rd trimester" not in names


def test_regression_i_lipid_categories_not_tests():
    """
    I. Lipid reference categories
    Must NOT produce tests:
        High Risk = 240
        Undesirable = 40
        High = 160
        Borderline Risk = 3
    """
    lines = [
        "LIPID PROFILE",
        "Total Cholesterol 154.2 mg/dL",
        "Desirable <200",
        "Borderline Risk : 200-239",
        "High Risk : >= 240",
        "HDL Cholesterol 47.3 mg/dL",
        "Optimal 40-59",
        "Undesirable <40",
        "LDL Cholesterol 84.82 mg/dL",
        "Optimal <100",
        "High 160-189",
    ]
    extracted = ParserService.parse_document_text("test_i", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    # Genuine tests: Total Cholesterol, HDL Cholesterol, LDL Cholesterol
    assert len(normalized.tests) == 3
    names = [t.raw_test_name.lower() for t in normalized.tests]
    assert "high risk" not in names
    assert "undesirable" not in names
    assert "high" not in names
    assert "borderline risk" not in names
    assert "optimal" not in names


def test_regression_j_urine_qualitative_results():
    """
    J. Urine qualitative
    Expected:
        Protein = TRACE
        Bacteria = PRESENT
        Urobilinogen = Negative
        Ketones = Negative
        Blood = Negative
        Nitrite = Negative
        Colour = YELLOW
        Appearance = TURBID
    Must be observed results, NOT reference values.
    """
    lines = [
        "URINE EXAMINATION",
        "Colour YELLOW",
        "Appearance TURBID",
        "Protein TRACE Nil",
        "Bacteria PRESENT Absent",
        "Urobilinogen Negative Normal",
        "Ketones Negative",
        "Blood Negative",
        "Nitrite Negative",
    ]
    extracted = ParserService.parse_document_text("test_j", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    tests_by_name = {t.raw_test_name.lower(): t for t in normalized.tests}
    assert "protein" in tests_by_name
    assert tests_by_name["protein"].source_trace["raw_value"] == "TRACE"
    assert tests_by_name["protein"].value is None

    assert "bacteria" in tests_by_name
    assert tests_by_name["bacteria"].source_trace["raw_value"] == "PRESENT"

    assert "urobilinogen" in tests_by_name
    assert tests_by_name["urobilinogen"].source_trace["raw_value"] == "Negative"

    assert "colour" in tests_by_name
    assert tests_by_name["colour"].source_trace["raw_value"] == "YELLOW"


def test_regression_k_urine_ranges_not_truncated():
    """
    K. Urine ranges
    Expected:
        Pus cells = 10-12 /HPF
        Epithelial cells = 4-5 /HPF
    Do NOT truncate to 10 or 4.
    """
    lines = [
        "Pus cells 10-12 /HPF 0-5",
        "Epithelial cells 4-5 /HPF 0-5",
    ]
    extracted = ParserService.parse_document_text("test_k", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    tests_by_name = {t.raw_test_name.lower(): t for t in normalized.tests}
    assert "pus cells" in tests_by_name
    pus = tests_by_name["pus cells"]
    assert "10-12" in pus.source_trace["raw_value"]
    assert pus.raw_unit == "/HPF"
    assert pus.reference_range.low == 0.0
    assert pus.reference_range.high == 5.0

    assert "epithelial cells" in tests_by_name
    epi = tests_by_name["epithelial cells"]
    assert "4-5" in epi.source_trace["raw_value"]
    assert epi.raw_unit == "/HPF"


def test_regression_l_metadata_not_tests():
    """
    L. Metadata
    Must NOT produce tests from:
        UHID, Patient, Address, Mobile, Age, Date, Doctor, Pathologist
    """
    lines = [
        "UHID: 12345678",
        "Patient: Mr Test Patient",
        "Address: 123 Health Street, Bangalore",
        "Mobile: 9876543210",
        "Age: 35 Years Sex: Male",
        "Date: 2026-09-21",
        "Referred By: Dr. Specialist MD",
        "Pathologist: Dr. Consultant MD",
        "Glucose 90 mg/dL 70-100",
    ]
    extracted = ParserService.parse_document_text("test_l", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    assert normalized.tests[0].raw_test_name == "Glucose"
    assert normalized.tests[0].value == 90.0


def test_regression_m_interpretation_prose_not_tests():
    """
    M. Interpretation
    No tests should be created from numeric values appearing inside interpretation paragraphs.
    """
    lines = [
        "CLINICAL BIOCHEMISTRY",
        "HbA1c 5.2 %",
        "CLINICAL INTERPRETATION:",
        "A hemoglobin A1c test measures the amount of blood sugar attached to hemoglobin.",
        "Non-diabetic range is 4.8 to 5.9 %.",
        "Pre-diabetic range is 5.9 to 6.5 %.",
        "Values greater than 6.5 % indicate diabetes.",
        "Repeat testing should be done every 3 to 6 months.",
    ]
    extracted = ParserService.parse_document_text("test_m", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 5.2
    assert normalized.tests[0].raw_unit == "%"


def test_regression_n_pavan_cbc_regression():
    """
    N. CBC Regression
    Verify existing PAVAN CBC extraction remains exact.
    """
    lines = [
        "KC General Hospital",
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
    ]
    extracted = ParserService.parse_document_text("test_n", lines)
    normalized = NormalizationService.normalize_extracted_report(extracted)

    tests_by_id = {t.test_id: t for t in normalized.tests if t.test_id}
    assert tests_by_id["WBC"].value == 5.79
    assert tests_by_id["RBC"].value == 4.41
    assert tests_by_id["HEMOGLOBIN"].value == 15.90
    assert tests_by_id["HCT"].value == 43.30
    assert tests_by_id["MCV"].value == 98.20
    assert tests_by_id["MCH"].value == 36.10
    assert tests_by_id["MCHC"].value == 36.70
    assert tests_by_id["PLATELETS"].value == 221.00
    assert tests_by_id["RDW_SD"].value == 46.60
    assert tests_by_id["RDW_CV"].value == 12.80
    assert tests_by_id["MPV"].value == 9.90
    assert tests_by_id["P_LCR"].value == 23.40
    assert tests_by_id["PCT"].value == 0.22
    assert tests_by_id["NEUTROPHILS"].value == 57.00
    assert tests_by_id["LYMPHOCYTES"].value == 28.00
    assert tests_by_id["EOSINOPHILS"].value == 7.80
    assert tests_by_id["BASOPHILS"].value == 0.50
    assert tests_by_id["IG"].value == 0.50
    assert tests_by_id["MONOCYTES"].value == 6.70
