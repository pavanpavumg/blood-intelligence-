from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ReferenceRange(BaseModel):
    low: Optional[float] = Field(default=None, description="Lower numeric bound of reference range")
    high: Optional[float] = Field(default=None, description="Upper numeric bound of reference range")
    raw: Optional[str] = Field(default=None, description="Raw extracted reference range text string")
    type: Optional[str] = Field(default=None, description="Range type: TWO_SIDED, UPPER_ONLY, LOWER_ONLY, DEMOGRAPHIC, PREGNANCY, CATEGORICAL")
    operator: Optional[str] = Field(default=None, description="Range operator: <=, <, >=, >")
    selected_group: Optional[str] = Field(default=None, description="Selected demographic or pregnancy group")
    categories: Optional[List[Dict[str, Any]]] = Field(default=None, description="Categorical reference range definitions")
    selected_category: Optional[str] = Field(default=None, description="Selected qualitative category label")

class LabTestResult(BaseModel):
    raw_test_name: str = Field(..., description="Raw extracted laboratory test name")
    canonical_test_name: Optional[str] = Field(default=None, description="Canonical normalized test name (Phase 2)")
    loinc_code: Optional[str] = Field(default=None, description="Standardized LOINC code (Phase 2)")
    value: Optional[float] = Field(default=None, description="Parsed numeric laboratory value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement (e.g. mg/dL, %, uIU/mL)")
    reference_range: Optional[ReferenceRange] = Field(default=None, description="Parsed reference range object")
    raw_value: str = Field(..., description="Raw extracted numerical value text")
    status: Optional[str] = Field(default=None, description="NORMAL/HIGH/LOW status")
    flag: Optional[str] = Field(default=None, description="Abnormality flag")
    method: Optional[str] = Field(default=None, description="Extracted measurement method")
    unit_validation: Optional[str] = Field(default=None, description="VALID, SUSPECT, or MISSING")
    review_reasons: List[str] = Field(default_factory=list, description="Structured review reason codes")
    source_trace: Optional[Dict[str, Any]] = Field(default=None, description="Source page and line trace context")
    specimen: Optional[Dict[str, Any]] = Field(default=None, description="Specimen page, vial ID, sample type")
    result_type: Optional[str] = Field(default=None, description="DIRECT, CALCULATED, or TEXTUAL")

