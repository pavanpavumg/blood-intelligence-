import math
from typing import Optional, Tuple

class ValidationService:
    """
    Unit normalization and numeric value validation service.
    """

    UNIT_MAP = {
        "mg/dl": "mg/dL",
        "mg/dl.": "mg/dL",
        "mmol/l": "mmol/L",
        "g/dl": "g/dL",
        "gm%": "gm%",
        "gm %": "gm%",
        "g%": "gm%",
        "millions/cumm": "millions/cumm",
        "million/cumm": "millions/cumm",
        "mill/cumm": "millions/cumm",
        "milln/ul": "millions/cumm",
        "lakhs/cumm": "lakhs/cumm",
        "lakh/cumm": "lakhs/cumm",
        "cells/cumm": "cells/cumm",
        "cumm": "cells/cumm",
        "10^3/ul": "10^3/uL",
        "10^3/µl": "10^3/uL",
        "10ˆ3/µl": "10^3/uL",
        "103/l": "10^3/uL",
        "10(3)/ul": "10^3/uL",
        "10^6/ul": "10^6/uL",
        "ui/ml": "uIU/mL",
        "uiu/ml": "uIU/mL",
        "miu/l": "mIU/L",
        "%": "%",
        "percent": "%",
        "pg/ml": "pg/mL",
        "ng/ml": "ng/mL",
        "fl": "fL",
        "pg": "pg",
        "iu/l": "IU/L",
        "u/l": "U/L",
    }

    @classmethod
    def normalize_unit(cls, raw_unit: Optional[str]) -> Optional[str]:
        """
        Normalizes unit string representation safely.
        Does not perform silent unit conversion when conversion factors are unknown.
        """
        if not raw_unit or not raw_unit.strip():
            return None
        
        clean = raw_unit.strip().lower()
        return cls.UNIT_MAP.get(clean, raw_unit.strip())

    @classmethod
    def validate_numeric_value(cls, value: Optional[float]) -> Tuple[Optional[float], bool]:
        """
        Validates float numerical sanity.
        Returns Tuple[ValidatedValue, isValid].
        """
        if value is None:
            return None, False
        
        if math.isnan(value) or math.isinf(value):
            return None, False
            
        return value, True
