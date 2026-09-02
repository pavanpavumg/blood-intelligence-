from typing import Optional, List, Union, Any
from pydantic import BaseModel, Field
from app.schemas.lab_result import LabTestResult
from app.schemas.common import PatientInfo, ReportMetadata
from app.schemas.normalized_lab_result import NormalizedReportData

class ExtractedReportData(BaseModel):
    schema_version: str = Field(default="1.0", description="Schema version identifier")
    report: ReportMetadata = Field(..., description="Report header metadata")
    patient: PatientInfo = Field(..., description="Patient demographic information")
    tests: List[LabTestResult] = Field(default_factory=list, description="Extracted laboratory test results")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal extraction warnings")

class ReportUploadResponse(BaseModel):
    report_id: str = Field(..., description="Unique generated report ID")
    status: str = Field(default="EXTRACTED", description="Processing status state")
    data: Union[ExtractedReportData, NormalizedReportData, Any] = Field(..., description="Structured extracted/normalized report payload")
