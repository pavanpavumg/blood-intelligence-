import math

from typing import Optional, Tuple, List


class ValidationService:
    """
    Validation and unit-normalization service.

    Responsibilities:
    - Normalize laboratory units
    - Validate units against known analyte expectations
    - Validate numeric values
    - Never remove an extracted test because validation fails
    """

    UNIT_MAP = {
        # Concentration
        "mg/dl": "mg/dL",
        "mg/dl.": "mg/dL",
        "mg/l": "mg/L",
        "g/dl": "g/dL",
        "g/l": "g/L",
        "gm%": "gm%",
        "gm %": "gm%",
        "g%": "gm%",
        "ug/dl": "ug/dL",
        "µg/dl": "ug/dL",
        "μg/dl": "ug/dL",
        "mcg/dl": "mcg/dL",
        "ug/l": "ug/L",
        "µg/l": "ug/L",
        "μg/l": "ug/L",
        "ng/ml": "ng/mL",
        "pg/ml": "pg/mL",
        "pg": "pg",
        # Molar
        "mmol/l": "mmol/L",
        "umol/l": "umol/L",
        # Enzymes / hormones
        "iu/l": "IU/L",
        "u/l": "U/L",
        "miu/l": "mIU/L",
        "uiu/ml": "uIU/mL",
        "ui/ml": "uIU/mL",
        # CBC
        "fl": "fL",
        "f l": "fL",
        "millions/cumm": "millions/cumm",
        "million/cumm": "millions/cumm",
        "mill/cumm": "millions/cumm",
        "milln/ul": "millions/cumm",
        "lakhs/cumm": "lakhs/cumm",
        "lakh/cumm": "lakhs/cumm",
        "cells/cumm": "cells/cumm",
        "cells/cu.mm": "cells/cumm",
        "cumm": "cells/cumm",
        "cmm": "cells/cumm",
        "10^3/ul": "10^3/uL",
        "10^3/µl": "10^3/uL",
        "10^3/μl": "10^3/uL",
        "10ˆ3/µl": "10^3/uL",
        "10ˆ3/ul": "10^3/uL",
        "103/l": "10^3/uL",
        "10(3)/ul": "10^3/uL",
        "10(3)/mm3": "10^3/uL",
        "10^6/ul": "10^6/uL",
        "10^6/µl": "10^6/uL",
        "10^6/μl": "10^6/uL",
        "10(6)/ul": "10^6/uL",
        # Electrolytes
        "meq/l": "mEq/L",
        # Percentage
        "%": "%",
        "percent": "%",
        # Misc
        "/hpf": "/HPF",
        "/lpf": "/LPF",
    }

    EXPECTED_UNITS = {
        "MCV": {
            "fl",
            "fL",
            "cu um",
            "cu.um",
        },
        "HEMOGLOBIN": {
            "g/dl",
            "gm%",
            "gm %",
            "g%",
            "g/l",
        },
        "WBC": {
            "10^3/ul",
            "10^3/µl",
            "10ˆ3/µl",
            "103/l",
            "cells/cumm",
            "cells/cu.mm",
            "cumm",
            "cmm",
            "/cumm",
        },
        "RBC": {
            "10^6/ul",
            "10^6/µl",
            "10ˆ6/µl",
            "millions/cumm",
            "million/cumm",
            "mill/cumm",
            "milln/ul",
        },
        "PLATELETS": {
            "10^3/ul",
            "10^3/µl",
            "10ˆ3/µl",
            "103/l",
            "cells/cumm",
            "cells/cu.mm",
            "cumm",
            "cmm",
            "/cumm",
            "lakhs/cumm",
            "lakh/cumm",
        },
        "RDW_CV": {
            "%",
            "percent",
        },
        "MCH": {
            "pg",
        },
        "MCHC": {
            "g/dl",
            "gm%",
            "gm %",
            "g%",
        },
        "MPV": {
            "fl",
            "fL",
        },
        "PDW": {
            "fl",
            "fL",
        },
        "P_LCR": {
            "%",
            "percent",
        },
        "PCT": {
            "%",
            "percent",
        },
        "NEUTROPHILS": {
            "%",
            "percent",
        },
        "LYMPHOCYTES": {
            "%",
            "percent",
        },
        "EOSINOPHILS": {
            "%",
            "percent",
        },
        "BASOPHILS": {
            "%",
            "percent",
        },
        "MONOCYTES": {
            "%",
            "percent",
        },
        "IG": {
            "%",
            "percent",
        },
        "AST": {
            "u/l",
            "iu/l",
        },
        "ALT": {
            "u/l",
            "iu/l",
        },
        "ALP": {
            "u/l",
            "iu/l",
        },
        "GGT": {
            "u/l",
            "iu/l",
        },
        "CPK": {
            "u/l",
            "iu/l",
        },
        "LDH": {
            "u/l",
            "iu/l",
        },
        "TSH": {
            "uiu/ml",
            "ui/ml",
            "miu/l",
        },
        "T3": {
            "ng/ml",
        },
        "T4": {
            "ug/dl",
            "µg/dl",
            "μg/dl",
        },
        "VITAMIN_D": {
            "ng/ml",
        },
        "VITAMIN_B12": {
            "pg/ml",
        },
        "IRON": {
            "ug/dl",
            "µg/dl",
            "mcg/dl",
        },
        "TIBC": {
            "ug/dl",
            "µg/dl",
            "mcg/dl",
        },
        "UIBC": {
            "ug/dl",
            "µg/dl",
            "mcg/dl",
        },
        "TRANSFERRIN_SATURATION": {
            "%",
            "percent",
        },
        "FERRITIN": {
            "ng/ml",
        },
        "CALCIUM": {
            "mg/dl",
        },
        "PHOSPHORUS": {
            "mg/dl",
        },
        "SODIUM": {
            "mmol/l",
            "meq/l",
        },
        "POTASSIUM": {
            "mmol/l",
            "meq/l",
        },
        "CHLORIDE": {
            "mmol/l",
            "meq/l",
        },
        "BICARBONATE": {
            "mmol/l",
            "meq/l",
        },
        "GLUCOSE_FASTING": {
            "mg/dl",
            "mmol/l",
        },
        "GLUCOSE_RANDOM": {
            "mg/dl",
            "mmol/l",
        },
        "HBA1C": {
            "%",
            "percent",
        },
        "CRP": {
            "mg/l",
            "mg/dl",
        },
        "HS_CRP": {
            "mg/l",
            "mg/dl",
        },
    }

    @classmethod
    def _clean_unit(cls, raw_unit: Optional[str]) -> Optional[str]:
        if not raw_unit:
            return None

        clean = raw_unit.strip().lower()

        clean = clean.replace("μ", "µ")

        clean = " ".join(clean.split())

        return clean

    @classmethod
    def normalize_unit(
        cls,
        raw_unit: Optional[str],
    ) -> Optional[str]:
        """
        Normalize representation only.

        No numerical conversion is performed.
        """

        clean = cls._clean_unit(raw_unit)

        if not clean:
            return None

        return cls.UNIT_MAP.get(clean, raw_unit.strip() if raw_unit else "")

    @classmethod
    def validate_unit_for_test(
        cls,
        test_id: Optional[str],
        raw_unit: Optional[str],
    ) -> Tuple[Optional[str], str, List[str]]:
        """
        Returns:

        (
            normalized_unit,
            validation_status,
            review_reasons
        )

        Validation status:
        VALID
        MISSING
        SUSPECT
        """

        reasons: List[str] = []

        if not raw_unit or not raw_unit.strip():
            return None, "MISSING", reasons

        normalized = cls.normalize_unit(raw_unit)

        clean_unit = cls._clean_unit(raw_unit)

        normalized_test_id = test_id.upper().strip() if test_id else None

        if normalized_test_id in cls.EXPECTED_UNITS:

            expected = {
                cls._clean_unit(unit) for unit in cls.EXPECTED_UNITS[normalized_test_id]
            }

            if clean_unit not in expected:

                reasons.append("UNEXPECTED_UNIT_FOR_TEST")

                return (
                    None,
                    "SUSPECT",
                    reasons,
                )

        return (
            normalized,
            "VALID",
            reasons,
        )

    @classmethod
    def validate_numeric_value(
        cls,
        value: Optional[float],
    ) -> Tuple[Optional[float], bool]:
        """
        Validate numerical sanity.

        Does not reject zero or negative values automatically because
        some laboratory measurements legitimately support them.
        """

        if value is None:
            return None, False

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return None, False

        if math.isnan(numeric_value):
            return None, False

        if math.isinf(numeric_value):
            return None, False

        return numeric_value, True
