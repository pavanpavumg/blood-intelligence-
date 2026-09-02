import pytest
from app.services.parser_service import ParserService
from app.schemas.lab_result import LabTestResult, ReferenceRange
from app.schemas.report import ExtractedReportData

def test_parse_reference_range_span():
    ref, warning = ParserService.parse_reference_range("70 - 100")
    assert ref is not None
    assert ref.low == 70.0
    assert ref.high == 100.0
    assert ref.raw == "70 - 100"
    assert warning is None

def test_parse_reference_range_less_than():
    ref, warning = ParserService.parse_reference_range("< 200 mg/dL")
    assert ref is not None
    assert ref.low is None
    assert ref.high == 200.0
    assert ref.raw == "< 200 mg/dL"
    assert warning is None

def test_parse_reference_range_greater_than():
    ref, warning = ParserService.parse_reference_range("> 40")
    assert ref is not None
    assert ref.low == 40.0
    assert ref.high is None
    assert ref.raw == "> 40"
    assert warning is None

def test_parse_test_line_success():
    line = "Fasting Blood Glucose 95.5 mg/dL 70 - 100"
    result, warning = ParserService.parse_test_line(line)
    
    assert result is not None
    assert result.raw_test_name == "Fasting Blood Glucose"
    assert result.value == 95.5
    assert result.unit == "mg/dL"
    assert result.raw_value == "95.5 mg/dL"
    assert result.status is None  # Phase 1 requirement
    assert result.flag is None    # Phase 1 requirement
    assert result.canonical_test_name is None
    assert result.loinc_code is None
    assert result.reference_range.low == 70.0
    assert result.reference_range.high == 100.0

def test_parse_malformed_row_does_not_crash():
    line = "Random Header Line Without Numeric Values"
    result, warning = ParserService.parse_test_line(line)
    assert result is None
    assert warning == "Line does not contain a numeric lab value."

def test_parse_document_text_patient_and_metadata():
    lines = [
        "Quest Diagnostics",
        "Patient Name: John Doe",
        "Age: 45 Years",
        "Gender: Male",
        "Report Date: 2026-08-24",
        "Patient ID: P-98765",
        "Hemoglobin A1c 5.8 % 4.0 - 5.6"
    ]
    
    parsed: ExtractedReportData = ParserService.parse_document_text("rep_test123", lines)
    assert parsed.schema_version == "1.0"
    assert parsed.report.report_id == "rep_test123"
    assert parsed.report.report_date == "2026-08-24"
    assert parsed.report.lab_name == "Quest Diagnostics"
    
    assert parsed.patient.name == "John Doe"
    assert parsed.patient.age == 45
    assert parsed.patient.gender == "Male"
    assert parsed.patient.patient_id == "P-98765"
    
    assert len(parsed.tests) == 1
    assert parsed.tests[0].raw_test_name == "Hemoglobin A1c"
    assert parsed.tests[0].value == 5.8
    assert parsed.tests[0].unit == "%"

def test_empty_report_handling():
    parsed: ExtractedReportData = ParserService.parse_document_text("rep_empty", [])
    assert parsed.report.report_id == "rep_empty"
    assert len(parsed.tests) == 0
    assert any("No laboratory test rows" in w for w in parsed.warnings)

def test_non_test_metadata_filtering():
    lines = [
        "Mobile No: 6360270028",
        "Final Report 26-03-2026 02:43 PM",
        "Dr. GANESH B D",
        "Hemoglobin A1c 5.8 % 4.0 - 5.6"
    ]
    parsed: ExtractedReportData = ParserService.parse_document_text("rep_filtered", lines)
    
    # Verify phone number, timestamp, and doctor name were filtered out
    assert len(parsed.tests) == 1
    assert parsed.tests[0].raw_test_name == "Hemoglobin A1c"
    assert parsed.tests[0].value == 5.8

