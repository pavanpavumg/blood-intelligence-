from typing import Optional
from pydantic import BaseModel, Field

class PatientInfo(BaseModel):
    patient_id: Optional[str] = Field(default=None, description="Patient ID or MRN")
    name: Optional[str] = Field(default=None, description="Patient full name")
    age: Optional[int] = Field(default=None, description="Patient age in years")
    gender: Optional[str] = Field(default=None, description="Patient gender (Male/Female/Other)")

class ReportMetadata(BaseModel):
    report_id: str = Field(..., description="Unique report identifier")
    report_date: Optional[str] = Field(default=None, description="Report or collection date (YYYY-MM-DD)")
    lab_name: Optional[str] = Field(default=None, description="Laboratory / Healthcare provider name")
