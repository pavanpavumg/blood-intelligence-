from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.lab_result import ReferenceRange
from app.schemas.common import PatientInfo, ReportMetadata

class NormalizedLabTestResult(BaseModel):
    test_name: Optional[str] = Field(default=None, description="Extracted laboratory test name")
    raw_test_name: str = Field(..., description="Raw extracted test name from report")
    canonical_test_name: Optional[str] = Field(default=None, exclude=True, description="Canonical normalized test name")
    test_id: Optional[str] = Field(default=None, exclude=True, description="Unique test identifier in catalog")
    loinc_code: Optional[str] = Field(default=None, description="Standardized LOINC code")
    value: Optional[float] = Field(default=None, description="Parsed numeric laboratory measurement")
    raw_unit: Optional[str] = Field(default=None, description="Raw extracted measurement unit")
    normalized_unit: Optional[str] = Field(default=None, exclude=True, description="Normalized measurement unit")
    reference_range: Optional[ReferenceRange] = Field(default=None, description="Resolved reference range bounds")
    status: str = Field(..., description="Deterministic status: NORMAL, HIGH, LOW, or UNKNOWN")
    flag: str = Field(..., description="Clinical flag: NONE, RED_FLAG, or REVIEW_REQUIRED")
    mapping_status: str = Field(..., exclude=True, description="Mapping confidence status: MAPPED or REVIEW_REQUIRED")
    method: Optional[str] = Field(default=None, exclude=True, description="Extracted measurement method")
    unit_validation: Optional[str] = Field(default=None, exclude=True, description="VALID, SUSPECT, or MISSING")
    review_reasons: List[str] = Field(default_factory=list, exclude=True, description="Structured review reason codes")
    source_trace: Optional[Dict[str, Any]] = Field(default=None, description="Source page and line trace context")
    specimen: Optional[Dict[str, Any]] = Field(default=None, exclude=True, description="Specimen page, vial ID, sample type")
    result_type: Optional[str] = Field(default=None, exclude=True, description="DIRECT, CALCULATED, or TEXTUAL")

class NormalizedReportData(BaseModel):
    schema_version: str = Field(default="2.1", description="Schema version identifier")
    report: ReportMetadata = Field(..., description="Report metadata")
    patient: PatientInfo = Field(..., description="Patient demographic information")
    tests: List[NormalizedLabTestResult] = Field(default_factory=list, description="Normalized laboratory test results")
    warnings: List[str] = Field(default_factory=list, description="Extraction and normalization warnings")
    completeness: Optional[Dict[str, Any]] = Field(default=None, description="Completeness validation object")
    specimen_summary: Optional[List[Dict[str, Any]]] = Field(default=None, description="Specimen metadata across pages")

class NormalizedReportResponse(BaseModel):
    report_id: str = Field(..., description="Report identifier")
    status: str = Field(default="NORMALIZED", description="Processing status")
    data: NormalizedReportData = Field(..., description="Normalized report payload")
