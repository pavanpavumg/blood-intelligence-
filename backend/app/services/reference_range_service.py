import re
from typing import Optional, Tuple
from app.schemas.lab_result import ReferenceRange
from app.services.test_mapping_service import TestCatalogItem
from app.core.logging import logger

class ReferenceRangeService:
    """
    Resolves reference ranges adhering to strict priority rules:
    Priority 1: Printed reference range on the laboratory report (gender-aware).
    Priority 2: Controlled catalog fallback reference range.
    Priority 3: None (yields status = 'UNKNOWN').
    """

    @classmethod
    def resolve_reference_range(
        cls,
        report_range: Optional[ReferenceRange],
        catalog_item: Optional[TestCatalogItem],
        patient_gender: Optional[str] = None
    ) -> Tuple[Optional[ReferenceRange], str]:
        """
        Resolves reference range and returns Tuple[SelectedReferenceRange, ResolutionSource].
        Source is one of: 'REPORT_PRINTED', 'CATALOG_DEFAULT', or 'UNAVAILABLE'.
        """
        # Priority 1: Report-printed reference range
        if report_range and (report_range.low is not None or report_range.high is not None or report_range.raw):
            raw = report_range.raw or ""
            # Strip Method text and trailing method names (e.g. Electrical Impedance, Calculated, Urease, ISE, BAPTA, Modified Jaffe, Kinetic, Spectrophotometry)
            raw = re.sub(r"^(?:Millions/cumm|Cells/cumm|mg/dL|g/dL|mmol/L|mg/L|uIU/mL|%)\s*", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r"\bMethod\s*:\s*.*?(?=(?:\b(?:Male|Female|Males|Females)\b|\d+|\s*$))", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(r"\bMethod\s*:\s*[^\s]+", "", raw, flags=re.IGNORECASE).strip()
            raw = re.sub(
                r"\b(?:spectrophotometry[^\s]*|electrical\s+impedance|impedance(?:/[^\s]+)?|modified\s+jaffe|kinetic|urease|ise|bapta|uricase|calculated|colorimetric|enzymatic[^\s]*|flowcytometry[^\s]*)\b.*$",
                "",
                raw,
                flags=re.IGNORECASE,
            ).strip()
            raw = re.sub(r"\s+", " ", raw).strip()
            if not raw and report_range.low is None and report_range.high is None:
                if catalog_item and catalog_item.default_reference_range:
                    return catalog_item.default_reference_range, "CATALOG_DEFAULT"
                return None, "UNAVAILABLE"

            # Gender-specific range extraction if raw contains Male / Female bounds
            if "male" in raw.lower() or "female" in raw.lower():
                gender_str = (patient_gender or "").lower()
                low = report_range.low
                high = report_range.high

                if "female" in gender_str or gender_str == "f":
                    f_match = re.search(r"females?\s*:\s*(\d+(?:\.\d+)?)\s*[\-\–\—]\s*(\d+(?:\.\d+)?)", raw, re.I)
                    if f_match:
                        low = float(f_match.group(1))
                        high = float(f_match.group(2))
                elif "male" in gender_str or gender_str == "m":
                    m_match = re.search(r"males?\s*:\s*(\d+(?:\.\d+)?)\s*[\-\–\—]\s*(\d+(?:\.\d+)?)", raw, re.I)
                    if m_match:
                        low = float(m_match.group(1))
                        high = float(m_match.group(2))

                return ReferenceRange(low=low, high=high, raw=raw), "REPORT_PRINTED"

            return ReferenceRange(low=report_range.low, high=report_range.high, raw=raw), "REPORT_PRINTED"

        # Priority 2: Catalog default reference range
        if catalog_item and catalog_item.default_reference_range:
            return catalog_item.default_reference_range, "CATALOG_DEFAULT"

        # Priority 3: Unavailable / Unknown
        return None, "UNAVAILABLE"
