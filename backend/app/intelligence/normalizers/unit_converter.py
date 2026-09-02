from typing import Dict, Any, Tuple

class UnitConverter:
    """
    Standardizes biomarker test names to canonical codes and converts non-standard units.
    """
    CANONICAL_MAPPINGS = {
        "hba1c": "HBA1C",
        "glycated hemoglobin": "HBA1C",
        "fasting blood sugar": "GLUCOSE_FASTING",
        "fasting glucose": "GLUCOSE_FASTING",
        "tsh": "TSH",
    }

    @classmethod
    def normalize_name(cls, raw_name: str) -> str:
        clean = raw_name.lower().strip()
        for key, code in cls.CANONICAL_MAPPINGS.items():
            if key in clean:
                return code
        return raw_name.upper().replace(" ", "_")

    @classmethod
    def convert_to_standard(cls, code: str, value: float, from_unit: str) -> Tuple[float, str]:
        """
        Converts measurements (e.g. mmol/L to mg/dL for glucose).
        """
        if code == "GLUCOSE_FASTING" and from_unit.lower() == "mmol/l":
            return round(value * 18.0182, 2), "mg/dL"
        return value, from_unit
