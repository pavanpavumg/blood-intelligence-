from typing import Optional, Tuple
from app.schemas.lab_result import ReferenceRange
from app.core.logging import logger

class ClassificationService:
    """
    Deterministic threshold classification engine for laboratory measurements.
    Assigns status (NORMAL, HIGH, LOW, UNKNOWN) and flag (NONE, RED_FLAG, REVIEW_REQUIRED).
    """

    @classmethod
    def classify_result(
        cls,
        value: Optional[float],
        ref_range: Optional[ReferenceRange]
    ) -> Tuple[str, str]:
        """
        Classifies numeric lab value against resolved reference range.
        Returns Tuple[status, flag].
        
        Status options: 'NORMAL', 'HIGH', 'LOW', 'UNKNOWN'
        Flag options: 'NONE', 'RED_FLAG', 'REVIEW_REQUIRED'
        """
        # If value is invalid or missing -> UNKNOWN / REVIEW_REQUIRED
        if value is None:
            return "UNKNOWN", "REVIEW_REQUIRED"

        # If reference range is missing or empty -> UNKNOWN / REVIEW_REQUIRED
        if not ref_range or (ref_range.low is None and ref_range.high is None):
            return "UNKNOWN", "REVIEW_REQUIRED"

        low = ref_range.low
        high = ref_range.high

        # 1. Two-sided Range (both low and high present)
        if low is not None and high is not None:
            if value < low:
                return "LOW", "RED_FLAG"
            elif value > high:
                return "HIGH", "RED_FLAG"
            else:
                return "NORMAL", "NONE"

        # 2. Upper-bound only range (e.g. < 5.7, <= 100)
        if high is not None and low is None:
            if value > high:
                return "HIGH", "RED_FLAG"
            else:
                return "NORMAL", "NONE"

        # 3. Lower-bound only range (e.g. > 40, >= 10)
        if low is not None and high is None:
            if value < low:
                return "LOW", "RED_FLAG"
            else:
                return "NORMAL", "NONE"

        return "UNKNOWN", "REVIEW_REQUIRED"
