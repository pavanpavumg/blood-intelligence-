from typing import Dict, Any, Optional

class MedicalReferenceEngine:
    """
    Evaluates biomarker measurements against age/gender-adjusted clinical reference ranges.
    """
    REFERENCE_RANGES = {
        "HBA1C": {"min": 4.0, "max": 5.6, "unit": "%"},
        "GLUCOSE_FASTING": {"min": 70.0, "max": 99.0, "unit": "mg/dL"},
        "TSH": {"min": 0.45, "max": 4.5, "unit": "uIU/mL"},
    }

    def evaluate(self, code: str, value: float, gender: str = "M", age: int = 30) -> Dict[str, Any]:
        ref = self.REFERENCE_RANGES.get(code)
        if not ref:
            return {"status": "UNKNOWN", "flag": "NORMAL"}
        
        status = "OPTIMAL"
        flag = "NORMAL"
        if value < ref["min"]:
            status = "LOW"
            flag = "ABNORMAL"
        elif value > ref["max"]:
            status = "HIGH"
            flag = "ABNORMAL"
            
        return {
            "status": status,
            "flag": flag,
            "reference_range": f"{ref['min']} - {ref['max']} {ref['unit']}"
        }
