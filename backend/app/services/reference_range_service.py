import re
from typing import Optional, Tuple
from app.schemas.lab_result import ReferenceRange
from app.services.test_mapping_service import TestCatalogItem
from app.core.logging import logger

class ReferenceRangeService:
    """
    Resolves reference ranges adhering to strict priority rules:
    Priority 1: Printed reference range on the laboratory report (gender/pregnancy/categorical-aware).
    Priority 2: Controlled catalog fallback reference range.
    Priority 3: None (yields status = 'UNKNOWN').
    """

    @classmethod
    def resolve_reference_range(
        cls,
        report_range: Optional[ReferenceRange],
        catalog_item: Optional[TestCatalogItem],
        patient_gender: Optional[str] = None,
        test_value: Optional[float] = None
    ) -> Tuple[Optional[ReferenceRange], str]:
        """
        Resolves reference range and returns Tuple[SelectedReferenceRange, ResolutionSource].
        Source is one of: 'REPORT_PRINTED', 'CATALOG_DEFAULT', or 'UNAVAILABLE'.
        """
        # Categorical Resolution for HDL, LDL, HbA1c, Vitamin D
        if catalog_item:
            cat_id = catalog_item.test_id
            if cat_id in ["HDL", "LDL", "HBA1C", "VITAMIN_D"]:
                categories = []
                selected_cat = None

                if cat_id == "HDL":
                    categories = [
                        {"label": "DESIRABLE", "operator": ">", "value": 59.0},
                        {"label": "OPTIMAL", "low": 40.0, "high": 59.0},
                        {"label": "UNDESIRABLE", "operator": "<", "value": 40.0},
                    ]
                    if test_value is not None:
                        if test_value > 59.0:
                            selected_cat = "DESIRABLE"
                        elif 40.0 <= test_value <= 59.0:
                            selected_cat = "OPTIMAL"
                        else:
                            selected_cat = "UNDESIRABLE"
                elif cat_id == "LDL":
                    categories = [
                        {"label": "OPTIMAL", "operator": "<", "value": 100.0},
                        {"label": "NEAR_OPTIMAL", "low": 100.0, "high": 129.0},
                        {"label": "BORDERLINE_HIGH", "low": 130.0, "high": 159.0},
                        {"label": "HIGH", "low": 160.0, "high": 189.0},
                        {"label": "VERY_HIGH", "operator": ">", "value": 189.0},
                    ]
                    if test_value is not None:
                        if test_value < 100.0:
                            selected_cat = "OPTIMAL"
                        elif 100.0 <= test_value <= 129.0:
                            selected_cat = "NEAR_OPTIMAL"
                        elif 130.0 <= test_value <= 159.0:
                            selected_cat = "BORDERLINE_HIGH"
                        elif 160.0 <= test_value <= 189.0:
                            selected_cat = "HIGH"
                        else:
                            selected_cat = "VERY_HIGH"
                elif cat_id == "HBA1C":
                    categories = [
                        {"label": "NON_DIABETIC", "low": 4.8, "high": 5.9},
                        {"label": "PRE_DIABETIC", "low": 5.9, "high": 6.5},
                        {"label": "DIABETIC", "operator": ">=", "value": 6.5},
                    ]
                    if test_value is not None:
                        if test_value < 5.9:
                            selected_cat = "NON_DIABETIC"
                        elif 5.9 <= test_value < 6.5:
                            selected_cat = "PRE_DIABETIC"
                        else:
                            selected_cat = "DIABETIC"
                elif cat_id == "VITAMIN_D":
                    categories = [
                        {"label": "DEFICIENCY", "operator": "<", "value": 10.0},
                        {"label": "INSUFFICIENCY", "low": 10.0, "high": 30.0},
                        {"label": "SUFFICIENCY", "low": 30.0, "high": 100.0},
                        {"label": "TOXICITY", "operator": ">", "value": 100.0},
                    ]
                    if test_value is not None:
                        if test_value < 10.0:
                            selected_cat = "DEFICIENCY"
                        elif 10.0 <= test_value < 30.0:
                            selected_cat = "INSUFFICIENCY"
                        elif 30.0 <= test_value <= 100.0:
                            selected_cat = "SUFFICIENCY"
                        else:
                            selected_cat = "TOXICITY"

                raw_text = report_range.raw if report_range else (catalog_item.default_reference_range.raw if catalog_item.default_reference_range else None)
                res_range = ReferenceRange(
                    low=report_range.low if report_range else (catalog_item.default_reference_range.low if catalog_item.default_reference_range else None),
                    high=report_range.high if report_range else (catalog_item.default_reference_range.high if catalog_item.default_reference_range else None),
                    raw=raw_text,
                    type="CATEGORICAL",
                    categories=categories,
                    selected_category=selected_cat
                )
                return res_range, "REPORT_PRINTED" if report_range else "CATALOG_DEFAULT"

        # Priority 1: Report-printed reference range
        if report_range and (report_range.low is not None or report_range.high is not None or report_range.raw):
            raw = report_range.raw or ""
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

            range_type = report_range.type or "TWO_SIDED"
            op = report_range.operator

            # Pregnancy-specific range resolution
            if "trimester" in raw.lower() or "pregnancy" in raw.lower() or range_type == "PREGNANCY":
                # Pregnancy trimester status unknown unless specified in context
                return ReferenceRange(low=None, high=None, raw=raw, type="PREGNANCY", selected_group=None), "REPORT_PRINTED"

            # Gender-specific range extraction if raw contains Male / Female bounds
            if "male" in raw.lower() or "female" in raw.lower() or range_type == "DEMOGRAPHIC":
                gender_str = (patient_gender or "").lower()
                low = report_range.low
                high = report_range.high
                sel_group = None

                if "female" in gender_str or gender_str == "f":
                    f_match = re.search(r"females?\s*:\s*(\d+(?:\.\d+)?)\s*[\-\–\—]\s*(\d+(?:\.\d+)?)", raw, re.I)
                    if f_match:
                        low = float(f_match.group(1))
                        high = float(f_match.group(2))
                        sel_group = "FEMALE"
                elif "male" in gender_str or gender_str == "m":
                    m_match = re.search(r"males?\s*:\s*(\d+(?:\.\d+)?)\s*[\-\–\—]\s*(\d+(?:\.\d+)?)", raw, re.I)
                    if m_match:
                        low = float(m_match.group(1))
                        high = float(m_match.group(2))
                        sel_group = "MALE"
                else:
                    # Unresolved demographic range
                    low = None
                    high = None

                return ReferenceRange(low=low, high=high, raw=raw, type="DEMOGRAPHIC", selected_group=sel_group), "REPORT_PRINTED"

            return ReferenceRange(low=report_range.low, high=report_range.high, raw=raw, type=range_type, operator=op), "REPORT_PRINTED"

        # Priority 2: Catalog default reference range
        if catalog_item and catalog_item.default_reference_range:
            return catalog_item.default_reference_range, "CATALOG_DEFAULT"

        # Priority 3: Unavailable / Unknown
        return None, "UNAVAILABLE"
