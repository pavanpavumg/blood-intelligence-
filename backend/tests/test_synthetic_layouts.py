import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService
from app.schemas.lab_result import LabTestResult


def test_scenario_1_single_line_lab_rows():
    lines = [
        "PATIENT REPORT",
        "Patient: Jane Doe Age: 30 Female",
        "Test Name Result Unit Reference Range",
        "Fasting Glucose 95.0 mg/dL 70.0 - 99.0",
        "Total Cholesterol 185 mg/dL < 200",
        "------End of Report------"
    ]
    parsed = ParserService.parse_document_text("rep_s1", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 2
    assert normalized.tests[0].value == 95.0
    assert normalized.tests[0].status == "NORMAL"
    assert normalized.tests[1].value == 185.0
    assert normalized.tests[1].status == "NORMAL"


def test_scenario_2_multiline_lab_rows():
    lines = [
        "LABORATORY TEST REPORT",
        "Test Name",
        "Observed Values Units Reference Intervals",
        "Hemoglobin",
        "14.2 g/dL 12.0 - 16.0",
        "Serum Creatinine",
        "0.9 mg/dL 0.7 - 1.3",
        "Note: Normal limits."
    ]
    parsed = ParserService.parse_document_text("rep_s2", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 2
    assert normalized.tests[0].value == 14.2
    assert normalized.tests[1].value == 0.9


def test_scenario_3_table_style_pdf():
    lines = [
        "Patient Name: Mark Smith Age: 50 Gender: Male",
        "Investigation Result Unit Reference Range",
        "WBC 11.5 10^3/uL 4.0 - 10.0",
        "RBC 4.5 10^6/uL 3.8 - 6.5",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s3", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 2
    assert normalized.tests[0].status == "HIGH"
    assert normalized.tests[0].flag == "RED_FLAG"


def test_scenario_4_scanned_ocr_text():
    lines = [
        "METABOLIC PANEL",
        "Investigation Result Reference Value Unit",
        "Serum Creatinine",
        "1.80 High 0.70 - 1.30 mg/dL",
        "****End of Report****"
    ]
    parsed = ParserService.parse_document_text("rep_s4", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 1.80
    assert normalized.tests[0].status == "HIGH"


def test_scenario_5_metadata_before_table():
    lines = [
        "Name : Mrs. GIRIJA",
        "Age/Gender : 75 Years / Female Vial ID : 3494187",
        "Ref.By : Self Collected On : 22-Jun-2026 02:27 PM",
        "Req No. : BNG2666471 Registered On : 22-Jun-2026 02:08 PM",
        "Test Name Observed Values Units Biological Reference Intervals",
        "* HAEMOGLOBIN 6.5 gm% 12.0 - 15.0",
        "Method:Colorimetric",
        "-------------- End Of The Report --------------"
    ]
    parsed = ParserService.parse_document_text("rep_s5", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert normalized.patient.name == "Mrs. GIRIJA"
    assert normalized.patient.age == 75
    assert len(normalized.tests) == 1
    assert normalized.tests[0].test_name == "* HAEMOGLOBIN"


def test_scenario_6_metadata_after_table():
    lines = [
        "Test Name Observed Values Units Biological Reference Intervals",
        "Fasting Glucose 105 mg/dL 70 - 100",
        "End of Report",
        "Doctor Signature: Dr Smith",
        "Printed On: 2026-08-24 10:00 AM"
    ]
    parsed = ParserService.parse_document_text("rep_s6", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 105.0
    assert normalized.tests[0].status == "HIGH"


def test_scenario_7_diverse_reference_ranges():
    lines = [
        "Investigation Result Unit Reference Range",
        "HbA1c 5.4 % < 5.7",
        "HDL 45.0 mg/dL > 40.0",
        "Eosinophils 2 % 02 - 06",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s7", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 3
    assert normalized.tests[0].status == "NORMAL"
    assert normalized.tests[1].status == "NORMAL"
    assert normalized.tests[2].status == "NORMAL"


def test_scenario_8_missing_reference_range():
    lines = [
        "Investigation Result Unit Reference Range",
        "Glucose 120.0 mg/dL",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s8", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    # Catalog fallback or UNKNOWN
    assert normalized.tests[0].value == 120.0


def test_scenario_9_missing_unit():
    lines = [
        "Investigation Result Reference Range",
        "Fasting Glucose 95 70 - 100",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s9", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 95.0


def test_scenario_10_metadata_multiple_numbers():
    lines = [
        "Client Code: CMLKAD56 Postal Code: 560003",
        "Phone: 9876543210 Reg No: 998877",
        "Test Name Result Unit Reference Range",
        "Platelet Count 250000 /cumm 150000 - 450000",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s10", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 250000.0


def test_scenario_11_phone_numbers_filtering():
    lines = [
        "Hospital Hotline: 18001234567 Mobile: 9876543210",
        "Test Name Result Unit Reference Range",
        "WBC 6500 cells/cumm 4000 - 11000",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s11", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 6500.0


def test_scenario_12_dates_filtering():
    lines = [
        "Collection Date: 2026-06-22 Registration Date: 2026-06-22",
        "Test Name Result Unit Reference Range",
        "HbA1c 5.2 % 4.0 - 5.6",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s12", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 5.2


def test_scenario_13_order_request_numbers_filtering():
    lines = [
        "Order No: ORD998877 Request ID: REQ112233",
        "Test Name Result Unit Reference Range",
        "Hemoglobin 13.5 g/dL 12.0 - 16.0",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s13", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 13.5


def test_scenario_14_multiple_panels():
    lines = [
        "Patient: John Doe",
        "LIPID PANEL",
        "Investigation Result Unit Reference Range",
        "Total Cholesterol 220 mg/dL < 200",
        "Triglycerides 140 mg/dL < 150",
        "CBC PANEL",
        "WBC 8500 /cumm 4000 - 11000",
        "End of Report"
    ]
    parsed = ParserService.parse_document_text("rep_s14", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)
    assert len(normalized.tests) == 3
    assert normalized.tests[0].status == "HIGH"
    assert normalized.tests[1].status == "NORMAL"
    assert normalized.tests[2].status == "NORMAL"
