from typing import Optional
from pydantic import BaseModel, Field

class ReferenceRange(BaseModel):
    low: Optional[float] = Field(default=None, description="Lower numeric bound of reference range")
    high: Optional[float] = Field(default=None, description="Upper numeric bound of reference range")
    raw: Optional[str] = Field(default=None, description="Raw extracted reference range text string")

class LabTestResult(BaseModel):
    raw_test_name: str = Field(..., description="Raw extracted laboratory test name")
    canonical_test_name: Optional[str] = Field(default=None, description="Canonical normalized test name (Phase 2)")
    loinc_code: Optional[str] = Field(default=None, description="Standardized LOINC code (Phase 2)")
    value: Optional[float] = Field(default=None, description="Parsed numeric laboratory value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g. mg/dL, %, uIU/mL)")
    reference_range: Optional[ReferenceRange] = Field(default=None, description="Parsed reference range object")
    raw_value: str = Field(..., description="Raw extracted numerical value text")
    status: Optional[str] = Field(default=None, description="NORMAL/HIGH/LOW status (Null in Phase 1)")
    flag: Optional[str] = Field(default=None, description="Abnormality flag (Null in Phase 1)")
