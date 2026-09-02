import pytest
from app.schemas.lab_result import ReferenceRange, LabTestResult
from app.schemas.report import ExtractedReportData, ReportMetadata, PatientInfo
from app.services.classification_service import ClassificationService
from app.services.reference_range_service import ReferenceRangeService
from app.services.test_mapping_service import TestMappingService
from app.services.validation_service import ValidationService
from app.services.normalization_service import NormalizationService

# 1. Classification Tests
def test_classification_low():
    ref = ReferenceRange(low=70.0, high=100.0, raw="70 - 100")
    status, flag = ClassificationService.classify_result(65.0, ref)
    assert status == "LOW"
    assert flag == "RED_FLAG"

def test_classification_normal():
    ref = ReferenceRange(low=70.0, high=100.0, raw="70 - 100")
    status, flag = ClassificationService.classify_result(85.0, ref)
    assert status == "NORMAL"
    assert flag == "NONE"

def test_classification_high():
    ref = ReferenceRange(low=70.0, high=100.0, raw="70 - 100")
    status, flag = ClassificationService.classify_result(115.0, ref)
    assert status == "HIGH"
    assert flag == "RED_FLAG"

def test_classification_boundary_values():
    ref = ReferenceRange(low=70.0, high=100.0, raw="70 - 100")
    
    # Exact lower bound -> NORMAL
    status_low_b, flag_low_b = ClassificationService.classify_result(70.0, ref)
    assert status_low_b == "NORMAL"
    assert flag_low_b == "NONE"
    
    # Exact upper bound -> NORMAL
    status_high_b, flag_high_b = ClassificationService.classify_result(100.0, ref)
    assert status_high_b == "NORMAL"
    assert flag_high_b == "NONE"

def test_classification_one_sided_upper_bound():
    ref = ReferenceRange(low=None, high=5.7, raw="< 5.7")
    
    status_pass, flag_pass = ClassificationService.classify_result(5.5, ref)
    assert status_pass == "NORMAL"
    assert flag_pass == "NONE"
    
    status_high, flag_high = ClassificationService.classify_result(6.0, ref)
    assert status_high == "HIGH"
    assert flag_high == "RED_FLAG"

def test_classification_one_sided_lower_bound():
    ref = ReferenceRange(low=40.0, high=None, raw="> 40")
    
    status_pass, flag_pass = ClassificationService.classify_result(45.0, ref)
    assert status_pass == "NORMAL"
    assert flag_pass == "NONE"
    
    status_low, flag_low = ClassificationService.classify_result(35.0, ref)
    assert status_low == "LOW"
    assert flag_low == "RED_FLAG"

def test_classification_missing_range_returns_unknown():
    status, flag = ClassificationService.classify_result(95.0, None)
    assert status == "UNKNOWN"
    assert flag == "REVIEW_REQUIRED"

# 2. Crucial Safety Requirement Test
def test_report_printed_range_overrides_catalog_default():
    """
    Safety Requirement:
    Value = 105
    Report Reference printed on lab report = 70–110
    Catalog Default Reference range = 70–99
    Result MUST BE 'NORMAL' because laboratory-printed range takes precedence.
    """
    report_printed_ref = ReferenceRange(low=70.0, high=110.0, raw="70 - 110 mg/dL")
    catalog_item, _ = TestMappingService.match_test("Fasting Blood Glucose")
    
    # Verify catalog default is indeed 70-99
    assert catalog_item.default_reference_range.high == 99.0
    
    # Resolve range priority
    resolved_ref, source = ReferenceRangeService.resolve_reference_range(
        report_range=report_printed_ref,
        catalog_item=catalog_item
    )
    assert source == "REPORT_PRINTED"
    assert resolved_ref.high == 110.0
    
    # Classify against resolved range
    status, flag = ClassificationService.classify_result(105.0, resolved_ref)
    assert status == "NORMAL"
    assert flag == "NONE"

# 3. Test Catalog Mapping & Ambiguity Tests
def test_alias_test_mapping():
    item, mapping_status = TestMappingService.match_test("HbA1c")
    assert item is not None
    assert item.test_id == "HBA1C"
    assert item.canonical_name == "Hemoglobin A1c"
    assert item.loinc_code == "4548-4"
    assert mapping_status == "MAPPED"

def test_ambiguous_test_mapping():
    item, mapping_status = TestMappingService.match_test("Glucose")
    assert item is None
    assert mapping_status == "REVIEW_REQUIRED"

# 4. Unit Normalization Tests
def test_unit_normalization():
    assert ValidationService.normalize_unit("mg/dl") == "mg/dL"
    assert ValidationService.normalize_unit("mmol/l") == "mmol/L"
    assert ValidationService.normalize_unit("%") == "%"

# 5. Full Normalization Pipeline Integration Test
def test_full_normalization_pipeline():
    raw_report = ExtractedReportData(
        schema_version="1.0",
        report=ReportMetadata(report_id="rep_test_phase2", report_date="2026-08-24", lab_name="Quest"),
        patient=PatientInfo(name="John Doe", age=45, gender="Male"),
        tests=[
            LabTestResult(
                raw_test_name="Fasting Glucose",
                value=95.0,
                unit="mg/dl",
                reference_range=ReferenceRange(low=70.0, high=100.0, raw="70 - 100"),
                raw_value="95 mg/dl"
            ),
            LabTestResult(
                raw_test_name="Glucose",
                value=120.0,
                unit="mg/dl",
                reference_range=None,
                raw_value="120 mg/dl"
            )
        ]
    )
    
    normalized = NormalizationService.normalize_extracted_report(raw_report)
    assert normalized.schema_version == "2.1"
    assert len(normalized.tests) == 2
    
    t0 = normalized.tests[0]
    assert t0.raw_test_name == "Fasting Glucose"
    assert t0.canonical_test_name == "Fasting Blood Glucose"
    assert t0.test_id == "GLUCOSE_FASTING"
    assert t0.loinc_code == "1558-6"
    assert t0.value == 95.0
    assert t0.raw_unit == "mg/dl"
    assert t0.normalized_unit == "mg/dL"
    assert t0.status == "NORMAL"
    assert t0.flag == "NONE"
    assert t0.mapping_status == "MAPPED"
    
    t1 = normalized.tests[1]
    assert t1.raw_test_name == "Glucose"
    assert t1.canonical_test_name is None
    assert t1.loinc_code is None
    assert t1.status == "UNKNOWN"
    assert t1.flag == "REVIEW_REQUIRED"
    assert t1.mapping_status == "REVIEW_REQUIRED"
