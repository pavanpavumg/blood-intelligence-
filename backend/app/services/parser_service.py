import re
from datetime import datetime
from enum import Enum
from typing import List, Dict, Tuple, Optional

from app.schemas.lab_result import (
    LabTestResult,
    ReferenceRange,
)

from app.schemas.report import (
    PatientInfo,
    ReportMetadata,
    ExtractedReportData,
)

from app.core.logging import logger
from app.services.test_mapping_service import TestMappingService


class LineType(str, Enum):
    METADATA = "METADATA"
    SECTION_HEADING = "SECTION_HEADING"
    INTERPRETATION = "INTERPRETATION"
    REFERENCE_ROW = "REFERENCE_ROW"
    TEST_ROW = "TEST_ROW"
    NOTE = "NOTE"
    UNKNOWN = "UNKNOWN"


class ParserService:
    """
    Deterministic parser for laboratory reports.

    Main goals:
    - Parse every laboratory row across multi-page reports.
    - Do not depend on table headers.
    - Support OCR text.
    - Support one-line and multi-line rows.
    - Preserve raw test names.
    - Extract value/unit/reference range.
    - Avoid metadata/narrative false positives.
    """

    COMMON_UNITS = [
        "Millions/cumm",
        "millions/cumm",
        "million/cumm",
        "millions/cu.mm",
        "mill/cumm",
        "mill/cmm",
        "milln/ul",
        "milln/uL",
        "lakhs/cumm",
        "lakh/cumm",
        "Cells/cumm",
        "cells/cumm",
        "cells/cu.mm",
        "10^3/µL",
        "10ˆ3/µL",
        "10^3/uL",
        "10ˆ3/uL",
        "103/L",
        "10(3)/uL",
        "10(3)/mm3",
        "10^6/uL",
        "10^6/µL",
        "10^6/L",
        "10(6)/uL",
        "10^3",
        "10ˆ3",
        "10^6",
        "10ˆ6",
        "/cumm",
        "cumm",
        "cmm",
        "gm%",
        "gm %",
        "g%",
        "mg/dL",
        "mg/L",
        "mmol/L",
        "umol/L",
        "mEq/L",
        "IU/mL",
        "uIU/mL",
        "µIU/mL",
        "μIU/mL",
        "mIU/mL",
        "IU/ml",
        "uIU/ml",
        "µIU/ml",
        "μIU/ml",
        "mIU/ml",
        "mIU/L",
        "g/dL",
        "g/L",
        "pg/mL",
        "pg",
        "ng/mL",
        "mcg/dL",
        "ug/dL",
        "µg/dL",
        "μg/dL",
        "ug/L",
        "µg/L",
        "μg/L",
        "IU/L",
        "U/L",
        "/HPF",
        "/LPF",
        "fL",
        "fl",
        "um",
        "µm",
        "μm",
        "%",
        "ratio",
        "Ratio",
    ]

    # Longest first prevents "g/dL" matching incorrectly
    # before "mg/dL".
    COMMON_UNITS = sorted(
        COMMON_UNITS,
        key=len,
        reverse=True,
    )

    METADATA_PREFIXES = (
        "name",
        "patient name",
        "patient",
        "uhid",
        "uhid no",
        "address",
        "mobile",
        "mobile no",
        "phone",
        "telephone",
        "fax",
        "age",
        "sex",
        "gender",
        "date",
        "report date",
        "collection date",
        "registered date",
        "registration date",
        "visit id",
        "final report",
        "report",
        "sample",
        "referred by",
        "ref by",
        "ref",
        "ref cust",
        "ref doctor",
        "order no",
        "order id",
        "order",
        "request id",
        "request no",
        "request",
        "req no",
        "hotline",
        "hospital hotline",
        "client code",
        "client name",
        "client",
        "lab no",
        "sample no",
        "vial id",
        "barcode",
        "page",
        "printed on",
        "printed",
        "note",
        "notes",
        "doctor",
        "dr",
        "pathologist",
        "signature",
        "approved by",
        "checked by",
        "kmc.no",
        "kmc no",
        "kmc",
        "reg no",
        "reg.no",
        "license no",
        "license",
    )

    METADATA_REGEX = re.compile(
        r"\b(?:"
        r"name|patient\s*name|patient\s*id|uhid|uhid\s*no|visit\s*id|mrn|"
        r"ref(?:\.|\s+by|\s+cust|\s+doctor)?|referred\s*by|client\s*code|client\s*name|client|"
        r"barcode|sample|vial\s*id|req\s*no|request\s*no|request\s*id|order\s*no|order\s*id|"
        r"age|gender|sex|mobile|phone|telephone|fax|address|kmc(?:\.no|\s*no)?|reg(?:\.no|\s*no)?|"
        r"reported(?:\s*on)?|registered(?:\s*on)?|collected(?:\s*on)?|printed(?:\s*on)?|"
        r"final\s*report|interim\s*report"
        r")\s*[:\-]",
        re.IGNORECASE,
    )

    INVALID_EXACT_NAMES = {
        "mobile",
        "mobile no",
        "phone",
        "phone no",
        "telephone",
        "fax",
        "report",
        "final report",
        "interim report",
        "status",
        "date",
        "time",
        "page",
        "doctor",
        "dr",
        "dr.",
        "consultant",
        "pathologist",
        "signature",
        "approved by",
        "checked by",
        "lab no",
        "sample no",
        "vial id",
        "req no",
        "request no",
        "sample type",
        "collected on",
        "registered on",
        "reported on",
        "client name",
        "client code",
        "address",
        "visit id",
        "test name",
        "test names",
        "observed values",
        "observed value",
        "units",
        "unit",
        "biological reference intervals",
        "reference interval",
        "differential count",
        "cbc",
        "complete blood count",
        "male",
        "female",
        "males",
        "females",
        "adults",
        "children",
        "infants",
        "non-diabetic",
        "pre-diabetic",
        "diabetic",
        "desirable",
        "optimal",
        "borderline high",
        "very high",
        "near optimal",
    }

    INVALID_NAME_FRAGMENTS = (
        "patient name",
        "patient id",
        "patient age",
        "patient gender",
        "patient sex",
        "doctor name",
        "ref doctor",
        "referred by",
        "vial id",
        "req no",
        "request no",
        "collected on",
        "registered on",
        "reported on",
        "booking centre",
        "booking center",
        "interpretation",
        "clinical interpretation",
        "clinical comments",
        "comments:",
        "remarks:",
        "notes:",
        "risk level",
        "cardiovascular risk",
        "primary prevention",
        "aha/cdc",
        "nacb expert",
        "clinical significance",
        "kindly correlate",
        "end of the report",
        "end of report",
        "electronically authenticated",
        "pathologist",
        "authorized signatory",
        "nabl",
        "accredited",
        "accreditation",
        "pvt ltd",
        "pvt. ltd",
        "pvt.ltd",
        "labs pvt",
        "tez.health",
        ".health",
        "inspiring better",
        "better quality",
    )

    NARRATIVE_FRAGMENTS = (
        "may be detected",
        "detected with 6 hours",
        "acute phase",
        "risk factors",
        "primary prevention settings",
        "clinical significance",
        "kindly correlate",
        "please correlate",
        "testing is",
        "this test",
        "interpretation:",
        "clinical interpretation:",
        "cardiovascular risk",
    )

    HEADER_FRAGMENTS = (
        "test name",
        "observed values",
        "observed value",
        "investigation",
        "parameter",
        "result",
        "units",
        "reference range",
        "biological reference",
    )

    SECTION_STOP_WORDS = (
        "interpretation",
        "clinical interpretation",
        "comments:",
        "remarks:",
        "notes:",
        "clinical significance",
        "kindly correlate",
        "risk level",
        "end of report",
        "end of the report",
    )

    TIMESTAMP_PATTERN = re.compile(
        r"""
        \b
        \d{1,2}:\d{2}
        (?:\s*[AP]M)?
        \b
        |
        \b20\d{2}\b
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    CATEGORY_PREFIXES = (
        "desirable",
        "optimal",
        "near optimal",
        "undesirable",
        "high risk",
        "low risk",
        "moderate risk",
        "borderline high",
        "borderline risk",
        "borderline",
        "very high",
        "high",
        "deficiency",
        "insufficiency",
        "sufficiency",
        "toxicity",
        "non-diabetic",
        "pre-diabetic",
        "diabetic",
        "non diabetic",
        "pre diabetic",
        "1st trimester",
        "2nd trimester",
        "3rd trimester",
        "first trimester",
        "second trimester",
        "third trimester",
        "trimester",
    )

    SECTION_HEADINGS = (
        "lipid profile",
        "lipid screen",
        "haematology",
        "hematology",
        "complete blood count",
        "cbc",
        "biochemistry",
        "clinical biochemistry",
        "clinical pathology",
        "serology",
        "microbiology",
        "urinalysis",
        "urine examination",
        "urine analysis",
        "renal panel",
        "renal profile",
        "kidney function test",
        "kidney basic screen",
        "liver function test",
        "lft",
        "thyroid profile",
        "iron profile",
        "iron deficiency profile",
        "vitamin profile",
        "diabetic profile",
        "electrolyte panel",
        "electrolytes",
        "differential count",
    )

    @classmethod
    def _is_section_heading(cls, line: str) -> bool:
        if not line:
            return False
        clean = cls._normalize_spaces(line).strip()
        lower = clean.lower()

        if re.fullmatch(r"[-_=+|*~ ]+", clean):
            return True

        if any(h in lower for h in cls.HEADER_FRAGMENTS):
            if not re.search(r"\d", clean):
                return True
            header_count = sum(
                1
                for h in (
                    "test name",
                    "observed",
                    "result",
                    "units",
                    "unit",
                    "reference",
                    "interval",
                    "investigation",
                    "parameter",
                )
                if h in lower
            )
            if header_count >= 3:
                return True

        clean_name = re.sub(r"^[*\-•▪◦\s]+|[*\-•▪◦\s]+$", "", lower)
        if clean_name in cls.SECTION_HEADINGS:
            return True

        if any(
            clean_name.startswith(h) and len(clean_name) <= len(h) + 5
            for h in cls.SECTION_HEADINGS
        ):
            return True

        return False

    @classmethod
    def _is_interpretation_start(cls, line: str) -> bool:
        if not line:
            return False
        clean = cls._normalize_spaces(line).strip()
        lower = clean.lower()

        if re.search(
            r"^(?:clinical\s+)?(?:interpretation|intrepratation|comments|notes|remarks|significance|methodology)\s*[:\-]?",
            lower,
        ):
            return True

        if lower in (
            "interpretation",
            "clinical interpretation",
            "comments",
            "clinical comments",
            "notes",
            "remarks",
            "clinical significance",
            "kindly correlate",
            "please correlate",
        ):
            return True

        if re.search(
            r"\b(?:clinical\s+interpretation|clinical\s+significance|kindly\s+correlate|please\s+correlate)\b",
            lower,
        ):
            return True

        return False

    @classmethod
    def _is_reference_row(cls, line: str) -> bool:
        if not line:
            return False
        clean = cls._normalize_spaces(line).strip()
        lower = clean.lower()

        if re.match(r"^(?:method|technique|procedure)\s*:", clean, re.I):
            return True

        if re.match(
            r"^(?:female|male|females|males|adults|children|infants|newborns|pregnancy)\s*[:\-]?\s*(?:(?:less\s+than|greater\s+than|[<>]=?)\s*)?\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?",
            clean,
            re.I,
        ):
            return True

        if re.match(
            r"^(?:biological\s+reference\s+interval[s]?|reference\s+(?:interval|range)[s]?|bio\.?\s*ref\.?\s*interval[s]?)\s*[:\-]?",
            clean,
            re.I,
        ):
            return True

        if re.search(r"\b(?:sensitivity|density|molecular)\b", lower):
            return False

        # Strip leading (HbA1c) or (HBA1C) or parenthesized test references
        clean_cat = re.sub(r"^\([^)]+\)\s*", "", clean).strip()
        for cat in cls.CATEGORY_PREFIXES:
            cat_pat = (
                r"^"
                + re.escape(cat)
                + r"\b(?:\s*(?:range\s*is|is|level\s*is|risk|value\s*is)?\s*[:=]?\s*|\s+)(?:(?:less\s+than|greater\s+than|[<>]=?)\s*)?\d"
            )
            if re.search(cat_pat, clean, re.I) or re.search(cat_pat, clean_cat, re.I):
                return True

        if re.search(
            r"\b(?:trimester)\b.*?\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?",
            clean,
            re.I,
        ):
            return True

        if re.search(
            r"\b(?:values?\s+(?:greater|less)\s+than|\bindicate\s+diabetes|\brepeat\s+testing)\b",
            lower,
        ):
            return True

        if re.match(
            r"^\s*(?:[<>]=?\s*)?\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?(?:\s*[A-Za-z/%µμ\^]+)?\s*$",
            clean,
        ):
            return True

        if re.match(
            r"^(?:high(?:\s+risk)?|borderline(?:\s+risk|\s+high)?|undesirable|optimal|desirable)\s*[:=]\s*\d+(?:\.\d+)?",
            clean,
        ):
            return True

        return False

    @classmethod
    def classify_line(cls, line: str, in_interpretation: bool = False) -> LineType:
        if not line or not line.strip():
            return LineType.UNKNOWN

        clean = cls._normalize_spaces(line).strip()
        lower = clean.lower()

        if lower.startswith("page "):
            return LineType.METADATA

        if cls._is_section_heading(clean):
            return LineType.SECTION_HEADING

        if cls._is_interpretation_start(clean):
            return LineType.INTERPRETATION

        if in_interpretation:
            if clean.startswith(("*", "•", "▪", "◦")) and re.search(r"\d", clean):
                pass
            else:
                return LineType.INTERPRETATION

        if cls.is_metadata_line(clean) or cls._looks_like_metadata(clean):
            return LineType.METADATA

        if cls._is_reference_row(clean):
            return LineType.REFERENCE_ROW

        if cls._parse_qualitative(clean) is not None:
            return LineType.TEST_ROW

        unit, unit_match = cls._find_unit(clean)
        if unit and unit_match:
            before_unit = clean[: unit_match.start()].strip()
            if re.search(
                r"(?<![A-Za-z0-9])(-?\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?)[*#]?\s*$",
                before_unit,
            ):
                return LineType.TEST_ROW

        if re.search(r"[A-Za-z]", clean) and re.search(
            r"[:=]?\s*(-?\d+(?:\.\d+)?)[*#]?\s*$", clean
        ):
            return LineType.TEST_ROW

        return LineType.UNKNOWN

    @classmethod
    def _attach_reference_row(cls, test: LabTestResult, line: str) -> None:
        clean = line.strip()
        lower = clean.lower()

        pure_method_match = re.match(
            r"^(?:method|technique|procedure)\s*:\s*(.*?)$", clean, re.IGNORECASE
        )
        if pure_method_match:
            cand_method = pure_method_match.group(1).strip()
            demo_match = re.search(
                r"\b(female|male|females|males)\s*:\s*(\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?)",
                cand_method,
                re.IGNORECASE,
            )
            if demo_match:
                demo_range = demo_match.group(0)
                cand_method = cand_method[: demo_match.start()].strip()
                if test.reference_range:
                    if test.reference_range.raw:
                        test.reference_range.raw = (
                            f"{test.reference_range.raw} {demo_range}".strip()
                        )
                    else:
                        test.reference_range.raw = demo_range
                    test.reference_range.type = "DEMOGRAPHIC"
                else:
                    test.reference_range = ReferenceRange(
                        low=None, high=None, raw=demo_range, type="DEMOGRAPHIC"
                    )

            if cand_method:
                clean_c = re.sub(
                    r"^(?:method|technique|procedure)\s*:\s*",
                    "",
                    cand_method,
                    flags=re.IGNORECASE,
                ).strip()
                if not test.method:
                    test.method = clean_c
                elif clean_c not in test.method:
                    test.method = f"{test.method} {clean_c}"
            return

        demo_line_match = re.match(
            r"^(female|male|females|males)\s*[:\-]?\s*(\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?.*)$",
            clean,
            re.IGNORECASE,
        )
        if demo_line_match:
            if test.reference_range:
                if test.reference_range.raw:
                    test.reference_range.raw = (
                        f"{test.reference_range.raw} {clean}".strip()
                    )
                else:
                    test.reference_range.raw = clean
                test.reference_range.type = "DEMOGRAPHIC"
            else:
                test.reference_range = ReferenceRange(
                    low=None, high=None, raw=clean, type="DEMOGRAPHIC"
                )
            return

        ref_type = (
            "PREGNANCY"
            if "trimester" in lower or "pregnancy" in lower
            else "CATEGORICAL"
        )
        if test.reference_range:
            if test.reference_range.raw:
                if clean not in test.reference_range.raw:
                    test.reference_range.raw = (
                        f"{test.reference_range.raw} {clean}".strip()
                    )
            else:
                test.reference_range.raw = clean
            if test.reference_range.type in (
                None,
                "TWO_SIDED",
                "UPPER_ONLY",
                "LOWER_ONLY",
            ):
                test.reference_range.type = ref_type
        else:
            test.reference_range = ReferenceRange(
                low=None, high=None, raw=clean, type=ref_type
            )

    @classmethod
    def _clean_pua(cls, text: str) -> str:
        if not text:
            return ""

        res = re.sub(
            r"[\uf000-\uf0ff]",
            lambda m: chr(ord(m.group(0)) - 0xF000),
            text,
        )
        return res.replace("\u03bc", "µ")

    @classmethod
    def _normalize_spaces(cls, text: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            text.strip(),
        )

    @classmethod
    def parse_date_to_iso(
        cls,
        date_str: str,
    ) -> Optional[str]:

        if not date_str:
            return None

        clean = date_str.strip()

        patterns = [
            (
                r"(\d{1,2})[-/\s]"
                r"([A-Za-z]{3}|\d{1,2})[-/\s]"
                r"(\d{4})"
                r"(?:\s+(\d{1,2}):(\d{2})"
                r"(?::(\d{2}))?\s*([AP]M)?)?"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                clean,
                re.IGNORECASE,
            )

            if not match:
                continue

            day, month, year, hour, minute, second, ampm = match.groups()

            try:

                if month.isdigit():
                    month_number = int(month)
                else:
                    month_number = datetime.strptime(
                        month[:3].title(),
                        "%b",
                    ).month

                day_number = int(day)
                year_number = int(year)

                if hour and minute:

                    h = int(hour)
                    m = int(minute)
                    s = int(second or 0)

                    if ampm:
                        ampm = ampm.upper()

                        if ampm == "PM" and h != 12:
                            h += 12

                        if ampm == "AM" and h == 12:
                            h = 0

                    return (
                        f"{year_number:04d}-"
                        f"{month_number:02d}-"
                        f"{day_number:02d}T"
                        f"{h:02d}:{m:02d}:{s:02d}"
                    )

                return f"{year_number:04d}-" f"{month_number:02d}-" f"{day_number:02d}"

            except Exception:
                continue

        iso = re.search(
            r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})",
            clean,
        )

        if iso:
            year, month, day = iso.groups()

            return f"{int(year):04d}-" f"{int(month):02d}-" f"{int(day):02d}"

        return None

    @classmethod
    def extract_lab_name(
        cls,
        full_text: str,
        doc_lines: List[str],
    ) -> Optional[str]:

        text = full_text.lower()

        known = {
            "drlogy": "Drlogy Pathology Lab",
            "quest diagnostics": "Quest Diagnostics",
            "labcorp": "LabCorp",
            "centromed": "CENTROMED LABS PVT. LTD",
        }

        for key, value in known.items():

            if key in text:
                return value

        match = re.search(
            r"(?:laboratory|lab\s*name|"
            r"hospital\s*laboratory|diagnostics|labs)"
            r"\s*:\s*"
            r"([A-Za-z0-9.,&'()\- ]+)",
            full_text,
            re.IGNORECASE,
        )

        if match:

            candidate = match.group(1).strip()

            if len(candidate) >= 3 and not any(
                bad in candidate.lower()
                for bad in (
                    "patient",
                    "doctor",
                    "report",
                    "result",
                )
            ):
                return candidate

        for line in doc_lines[:15]:

            clean = line.strip()

            if re.search(
                r"\b(labs?|laboratory|diagnostics|pathology)\b",
                clean,
                re.IGNORECASE,
            ):

                lower = clean.lower()

                if any(
                    bad in lower
                    for bad in (
                        "report",
                        "department",
                        "patient",
                        "doctor",
                        "page",
                        "result",
                        "test",
                        "sample",
                        "vial",
                    )
                ):
                    continue

                clean = re.sub(
                    r"^[*\-\d.\s]+",
                    "",
                    clean,
                ).strip()

                if len(clean) >= 3:
                    return clean

        return None

    @classmethod
    def parse_reference_range(
        cls,
        text: str,
    ) -> Tuple[
        Optional[ReferenceRange],
        Optional[str],
    ]:

        if not text:
            return None, None

        # Remove dates and timestamps such as:
        # 26-03-2026, 26/03/2026, 2026-03-26, 14:30:00
        text = re.sub(
            r"\b\d{1,4}[-/]\d{1,2}[-/]\d{1,4}(?:\s+\d{1,2}:\d{2}(?::\d{2})?)?\b",
            " ",
            text,
        )
        text = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?\b", " ", text)

        text = re.sub(r"\s+", " ", text).strip()

        if not text:
            return None, None

        raw = cls._normalize_spaces(text)

        # Remove method text
        raw = re.sub(
            r"\bmethod\s*:\s*" r".*?" r"(?=(?:male|female|" r"up\s*to|" r"<|>|" r"\d))",
            "",
            raw,
            flags=re.IGNORECASE,
        )

        raw = cls._normalize_spaces(raw)

        if not raw:
            return None, None

        lower = raw.lower()

        # Obvious narrative
        if any(
            term in lower
            for term in (
                "patient",
                "doctor",
                "pathology",
                "kmc.no",
                "reported on",
                "registered on",
                "collected on",
                "vial",
                "req no",
                "sample",
                "clinical significance",
                "risk factors",
                "testing is",
            )
        ):
            return None, None

        # Demographic
        if "male:" in lower or "female:" in lower:
            demo_num = re.search(r"(-?\d+(?:\.\d+)?)\s*[-–—]\s*(-?\d+(?:\.\d+)?)", raw)
            d_low = float(demo_num.group(1)) if demo_num else None
            d_high = float(demo_num.group(2)) if demo_num else None
            return (
                ReferenceRange(
                    low=d_low,
                    high=d_high,
                    raw=raw,
                    type="DEMOGRAPHIC",
                ),
                None,
            )

        # Pregnancy
        if "trimester" in lower or "pregnancy" in lower:
            return (
                ReferenceRange(
                    low=None,
                    high=None,
                    raw=raw,
                    type="PREGNANCY",
                ),
                None,
            )

        # Categorical
        categorical_words = (
            "desirable",
            "optimal",
            "near optimal",
            "borderline",
            "non-diabetic",
            "pre-diabetic",
            "diabetic",
            "insufficiency",
            "deficiency",
            "sufficiency",
        )

        if any(word in lower for word in categorical_words):
            return (
                ReferenceRange(
                    low=None,
                    high=None,
                    raw=raw,
                    type="CATEGORICAL",
                ),
                None,
            )

        # Numeric two-sided range
        match = re.search(
            r"(-?\d+(?:\.\d+)?)" r"\s*[-–—]\s*" r"(-?\d+(?:\.\d+)?)",
            raw,
        )

        if match:

            low = float(match.group(1))
            high = float(match.group(2))

            # Avoid treating years as reference ranges
            if not (1900 <= low <= 2100 and 1900 <= high <= 2100):

                return (
                    ReferenceRange(
                        low=low,
                        high=high,
                        raw=raw,
                        type="TWO_SIDED",
                    ),
                    None,
                )

        # Upper-only
        upper = re.search(
            r"(?:"
            r"up\s*to|"
            r"upto|"
            r"less\s*than|"
            r"<="
            r"|<"
            r")"
            r"\s*(\d+(?:\.\d+)?)",
            raw,
            re.IGNORECASE,
        )

        if upper:

            high = float(upper.group(1))

            operator = (
                "<=" if ("<=" in lower or "up to" in lower or "upto" in lower) else "<"
            )

            return (
                ReferenceRange(
                    low=None,
                    high=high,
                    raw=raw,
                    type="UPPER_ONLY",
                    operator=operator,
                ),
                None,
            )

        # Lower-only
        lower_match = re.search(
            r"(?:"
            r"greater\s*than|"
            r"more\s*than|"
            r">="
            r"|>"
            r")"
            r"\s*(\d+(?:\.\d+)?)",
            raw,
            re.IGNORECASE,
        )

        if lower_match:

            low = float(lower_match.group(1))

            operator = (
                ">="
                if (
                    ">=" in lower
                    or "greater than or equal" in lower
                    or "more than or equal" in lower
                )
                else ">"
            )

            return (
                ReferenceRange(
                    low=low,
                    high=None,
                    raw=raw,
                    type="LOWER_ONLY",
                    operator=operator,
                ),
                None,
            )

        return (
            ReferenceRange(
                low=None,
                high=None,
                raw=raw,
            ),
            f"Unparsed reference range: '{raw}'",
        )

    @classmethod
    def _find_unit(
        cls,
        text: str,
    ) -> Tuple[
        Optional[str],
        Optional[re.Match],
    ]:
        candidates: List[Tuple[int, int, str, re.Match]] = []

        for unit in cls.COMMON_UNITS:
            pattern = re.compile(
                r"(?<![A-Za-z0-9µμ])" + re.escape(unit) + r"(?![A-Za-z0-9])",
                re.IGNORECASE,
            )
            for m in pattern.finditer(text):
                candidates.append((m.start(), m.end(), m.group(0), m))

        if not candidates:
            return None, None

        # Sort candidates by start position ascending, then by length descending
        candidates.sort(key=lambda c: (c[0], -(c[1] - c[0])))

        # Find the first unit that has a valid numeric observed value (or range) immediately preceding it
        for start, end, unit_str, match in candidates:
            before = text[:start].strip()
            if re.search(
                r"(?<![A-Za-z0-9])(-?\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?)[*#]?\s*$",
                before,
            ):
                return unit_str, match

        # Fallback to the first candidate
        first = candidates[0]
        return first[2], first[3]

    @classmethod
    def _remove_test_prefix(
        cls,
        name: str,
    ) -> str:

        name = name.strip()

        # Keep asterisk for test name fidelity

        # Remove bullets
        name = re.sub(
            r"^[•▪◦]+\s*",
            "",
            name,
        )

        return name.strip()

    @classmethod
    def is_metadata_line(cls, line: str) -> bool:
        """
        Returns True when a line belongs to patient/report metadata
        rather than a laboratory test.
        """
        if not line:
            return True

        clean_text = re.sub(r"[^\w\s]", " ", line.strip().lower())
        normalized = re.sub(r"\s+", " ", clean_text).strip()

        if not normalized:
            return True

        if re.search(
            r"(?:address|street|road|cross|layout|nagar|marg|complex|building|floor|station)\b.*\d{6}\b",
            line,
            re.IGNORECASE,
        ):
            return True

        if re.search(r"\b(?:pin|pincode|zip)\s*[:\-]?\s*\d{6}\b", line, re.IGNORECASE):
            return True

        if re.search(r"[A-Za-z]\s*[-–,]\s*\d{6}\b", line):
            return True

        if re.search(
            r"\b(?:bangalore|karnataka|india|malleswaram|tumkur|pincode)\b",
            line,
            re.IGNORECASE,
        ):
            return True

        for prefix in cls.METADATA_PREFIXES:
            clean_prefix = re.sub(
                r"\s+", " ", re.sub(r"[^\w\s]", " ", prefix.lower())
            ).strip()
            if normalized.startswith(clean_prefix):
                return True

        if cls.METADATA_REGEX.search(line):
            return True

        return False

    @classmethod
    def _looks_like_metadata(
        cls,
        name: str,
    ) -> bool:

        if cls.is_metadata_line(name):
            return True

        lower = name.lower().strip()

        if lower.startswith(("female:", "male:", "females:", "males:")):
            return True

        if lower in cls.INVALID_EXACT_NAMES:
            return True

        if any(fragment in lower for fragment in cls.INVALID_NAME_FRAGMENTS):
            return True

        if any(fragment in lower for fragment in cls.NARRATIVE_FRAGMENTS):
            return True

        # URLs / email / obvious contact information
        if "@" in lower:
            return True

        if "http://" in lower or "https://" in lower:
            return True

        return False

    @classmethod
    def _extract_numeric_candidate(
        cls,
        text: str,
    ) -> Optional[re.Match]:

        matches = list(
            re.finditer(
                r"(?<![A-Za-z])" r"-?\d+(?:\.\d+)?" r"(?![A-Za-z])",
                text,
            )
        )

        # Ignore "25" when part of "25-Hydroxy Vitamin D" or "25-OH Vitamin D"
        matches = [
            m
            for m in matches
            if not (
                m.group(0) == "25"
                and re.match(
                    r"^\s*[-–—]?\s*(?:hydroxy|oh)\b", text[m.end() :], re.IGNORECASE
                )
            )
        ]

        if not matches:
            return None

        # 1. Check for two-sided reference range pattern (e.g. 4 - 10, 3.8 - 6.5, 40.0-55.0)
        range_match = re.search(
            r"(?<![A-Za-z])\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?(?![A-Za-z])",
            text,
        )
        if range_match:
            candidates_before_range = [
                m for m in matches if m.end() <= range_match.start()
            ]
            if candidates_before_range:
                return candidates_before_range[0]

        # 2. Check for upper/lower limit reference range pattern (e.g. less than 0.5, < 1, > 60)
        limit_match = re.search(
            r"\b(?:less\s+than|greater\s+than|up\s*to|upto|below|above|[<>]=?)\s*\d+(?:\.\d+)?",
            text,
            re.IGNORECASE,
        )
        if limit_match:
            candidates_before_limit = [
                m for m in matches if m.end() <= limit_match.start()
            ]
            if candidates_before_limit:
                return candidates_before_limit[0]

        # 3. Prefer number before status word (High/Low/Abnormal/Normal)
        status_match = re.search(r"\b(high|low|abnormal|normal)\b", text, re.IGNORECASE)
        if status_match:
            candidates_before_status = [
                m for m in matches if m.end() <= status_match.start()
            ]
            if candidates_before_status:
                return candidates_before_status[0]

        # 4. Prefer a number close to a unit.
        unit, unit_match = cls._find_unit(text)

        if unit_match:

            candidates_before_unit = [
                m for m in matches if m.end() <= unit_match.start()
            ]

            if candidates_before_unit:

                return candidates_before_unit[0]

        # Otherwise use the first numeric candidate.
        return matches[0]

    @classmethod
    def _clean_test_name_and_method(cls, raw_name: str) -> Tuple[str, Optional[str]]:
        extracted_method = None
        raw_name = raw_name.strip(" :=-|\t<>")

        # Separate trailing parenthesized method (including nested parens e.g., "(Method: Enzymatic Method (sarcosine oxidase, Peroxidase))")
        if raw_name.endswith(")"):
            depth = 0
            open_idx = -1
            for idx in range(len(raw_name) - 1, -1, -1):
                if raw_name[idx] == ")":
                    depth += 1
                elif raw_name[idx] == "(":
                    depth -= 1
                    if depth == 0:
                        open_idx = idx
                        break
            if open_idx != -1:
                cand = raw_name[open_idx + 1 : -1].strip()
                if any(
                    term in cand.lower()
                    for term in (
                        "imped",
                        "hplc",
                        "eia",
                        "clia",
                        "pod",
                        "enzyme",
                        "enzymatic",
                        "immuno",
                        "calc",
                        "direct",
                        "colorimetric",
                        "method",
                        "tech",
                        "oxidase",
                        "peroxidase",
                        "urease",
                        "arsenazo",
                        "ferrozine",
                    )
                ):
                    clean_method = re.sub(
                        r"^(?:method|technique|procedure)\s*:\s*",
                        "",
                        cand,
                        flags=re.IGNORECASE,
                    ).strip()
                    extracted_method = clean_method
                    raw_name = raw_name[:open_idx].strip()

        raw_name = cls._remove_test_prefix(raw_name)
        raw_name = raw_name.strip(" :=-|\t")
        return raw_name, extracted_method

    @classmethod
    def _parse_qualitative(
        cls,
        line: str,
    ) -> Optional[LabTestResult]:
        qualitative_words = (
            "negative",
            "positive",
            "nil",
            "trace",
            "present",
            "absent",
            "turbid",
            "clear",
            "straw",
            "pale yellow",
            "yellow",
            "cloudy",
            "bloody",
            "reactive",
            "non-reactive",
            "detected",
            "not detected",
        )
        pattern = re.compile(
            r"\b(" + "|".join(re.escape(w) for w in qualitative_words) + r")\b",
            re.IGNORECASE,
        )
        matches = list(pattern.finditer(line))
        if not matches:
            return None

        first_m = matches[0]
        name = line[: first_m.start()].strip(" :=-_\t*•▪◦")
        if not name or len(name) < 2 or not re.search(r"[A-Za-z]", name):
            return None

        if cls.is_metadata_line(name) or cls._looks_like_metadata(name):
            return None

        val = first_m.group(1)

        # Check for secondary reference token after observed value (e.g. "Protein TRACE Nil")
        after_val = line[first_m.end() :].strip(" :=-_\t")
        ref_range = None
        if after_val:
            ref_m = pattern.search(after_val)
            if ref_m:
                ref_range = ReferenceRange(
                    low=None, high=None, raw=ref_m.group(1), type="CATEGORICAL"
                )
            elif any(
                w in after_val.lower()
                for w in ("normal", "nil", "negative", "absent")
            ):
                ref_range = ReferenceRange(
                    low=None, high=None, raw=after_val, type="CATEGORICAL"
                )

        normal_words = {
            "negative",
            "nil",
            "absent",
            "normal",
            "clear",
            "pale yellow",
            "straw",
            "yellow",
            "non-reactive",
            "not detected",
        }
        name_lower = name.lower()
        if name_lower in ("colour", "color", "appearance"):
            status = "REPORTED"
        elif val.lower() in normal_words:
            status = "NORMAL"
        else:
            status = "HIGH"

        return LabTestResult(
            raw_test_name=name,
            canonical_test_name=None,
            loinc_code=None,
            value=None,
            unit=None,
            reference_range=ref_range,
            raw_value=val,
            status=status,
            flag="NONE",
            method=None,
        )

    @classmethod
    def parse_test_line(
        cls,
        line: str,
    ) -> Tuple[
        Optional[LabTestResult],
        Optional[str],
    ]:
        if not line:
            return None, None

        line = cls._normalize_spaces(line)
        if len(line) < 2:
            return None, None

        lower = line.lower()

        # Reject table borders
        if line.startswith(("|", "+")) or re.fullmatch(r"[-_= ]+", line):
            return None, None

        # Reject metadata and headers
        if cls.is_metadata_line(line) or cls._looks_like_metadata(line):
            return None, None

        if any(h in lower for h in cls.HEADER_FRAGMENTS):
            if not re.search(r"\d", line):
                return None, None

        # Check if line is purely a reference category row
        if cls._is_reference_row(line):
            return None, None

        # Method extraction if prefixed or parenthesized
        extracted_method = None
        method_match = re.match(
            r"^(?:method|technique|procedure)\s*:\s*(.*?)\s+(.+)$",
            line,
            re.IGNORECASE,
        )
        if method_match:
            extracted_method = method_match.group(1).strip()
            line = method_match.group(2).strip()

        prefix_method = re.match(r"^\(([^)]+)\)\s*(.+)$", line)
        if prefix_method:
            possible_method = prefix_method.group(1).strip()
            possible_name = prefix_method.group(2).strip()
            if any(
                w in possible_method.lower()
                for w in (
                    "pod",
                    "hplc",
                    "enzyme",
                    "immuno",
                    "method",
                    "calculated",
                    "direct",
                    "clia",
                    "eia",
                )
            ):
                extracted_method = possible_method
                line = possible_name

        # Clean bullets from start of line (preserve asterisk for test name fidelity)
        line = re.sub(r"^[•▪◦]+\s*", "", line).strip()

        # -------------------------------------------------------------
        # Branch 1: Check for Unit in the line
        # -------------------------------------------------------------
        unit, unit_match = cls._find_unit(line)

        if unit and unit_match:
            before_unit = line[: unit_match.start()].strip()
            after_unit = line[unit_match.end() :].strip()

            # Check for range observed value: e.g. "Pus cells 10-12 /HPF" or "Epithelial cells 4-5 /HPF"
            # OR reference range in layout [Test] [Result] [Flag] [Ref Range] [Unit]
            obs_range_m = re.search(
                r"(?<![A-Za-z0-9])(\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?)\s*$",
                before_unit,
            )
            if obs_range_m:
                before_range = before_unit[: obs_range_m.start()].strip()
                val_match_before = re.search(
                    r"(-?\d+(?:\.\d+)?)[*#]?\s*(?:(high|low|normal|borderline|[HL]))?\s*$",
                    before_range,
                    re.IGNORECASE,
                )
                if val_match_before:
                    # layout: [Test Name] [Observed Value] [Flag] [Reference Range] [Unit]
                    # e.g. "Serum Creatinine 1.80 High 0.70 - 1.30 mg/dL"
                    raw_val = val_match_before.group(1)
                    numeric_val = float(raw_val)
                    flag_cand = val_match_before.group(2)
                    flag = flag_cand.upper() if flag_cand else None
                    if flag == "H":
                        flag = "HIGH"
                    elif flag == "L":
                        flag = "LOW"
                    raw_name = before_range[: val_match_before.start()].strip(" :-|\t")
                    ref_range_str = obs_range_m.group(1).replace(" ", "")
                    ref_range, warning = cls.parse_reference_range(ref_range_str)

                    raw_name, sub_method = cls._clean_test_name_and_method(raw_name)
                    if sub_method and not extracted_method:
                        extracted_method = sub_method

                    if not raw_name or not re.search(r"[A-Za-z]", raw_name):
                        return None, None

                    return (
                        LabTestResult(
                            raw_test_name=raw_name,
                            canonical_test_name=None,
                            loinc_code=None,
                            value=numeric_val,
                            unit=unit,
                            reference_range=ref_range,
                            raw_value=f"{raw_val} {unit}",
                            status=flag if flag in ("HIGH", "LOW", "NORMAL") else None,
                            flag=flag if flag in ("HIGH", "LOW") else "NONE",
                            method=extracted_method,
                        ),
                        warning,
                    )
                else:
                    # Genuine range observed value: e.g. "Pus cells 10-12 /HPF"
                    obs_range_str = obs_range_m.group(1).replace(" ", "")
                    raw_name = before_range.strip(" :-|\t")
                    raw_val = f"{obs_range_str} {unit}"
                    val_parts = re.split(r"[-–—]", obs_range_str)
                    numeric_val = float(val_parts[0]) if val_parts else None

                    ref_range, warning = (
                        cls.parse_reference_range(after_unit)
                        if after_unit
                        else (None, None)
                    )

                    raw_name, sub_method = cls._clean_test_name_and_method(raw_name)
                    if sub_method and not extracted_method:
                        extracted_method = sub_method

                    if not raw_name or not re.search(r"[A-Za-z]", raw_name):
                        return None, None

                    return (
                        LabTestResult(
                            raw_test_name=raw_name,
                            canonical_test_name=None,
                            loinc_code=None,
                            value=numeric_val,
                            unit=unit,
                            reference_range=ref_range,
                            raw_value=raw_val,
                            status=None,
                            flag=None,
                            method=extracted_method,
                        ),
                        warning,
                    )

            # Check for single numeric observed value: e.g. "Vitamin B12 360.2 pg/mL", "HbA1c 5.2 %", "Iron 71 µg/dL"
            num_m = re.search(
                r"([<>=]=?\s*)?(-?\d+(?:\.\d+)?)[*#]?\s*$",
                before_unit,
            )
            if num_m:
                val_str = num_m.group(2)
                numeric_val = float(val_str)
                raw_name = before_unit[: num_m.start()].strip(" :-|\t")
                raw_val = f"{num_m.group(0).strip()} {unit}"

                ref_range, warning = (
                    cls.parse_reference_range(after_unit)
                    if after_unit
                    else (None, None)
                )

                raw_name, sub_method = cls._clean_test_name_and_method(raw_name)
                if sub_method and not extracted_method:
                    extracted_method = sub_method

                if not raw_name or not re.search(r"[A-Za-z]", raw_name):
                    return None, None

                return (
                    LabTestResult(
                        raw_test_name=raw_name,
                        canonical_test_name=None,
                        loinc_code=None,
                        value=numeric_val,
                        unit=unit,
                        reference_range=ref_range,
                        raw_value=raw_val,
                        status=None,
                        flag=None,
                        method=extracted_method,
                    ),
                    warning,
                )

        # -------------------------------------------------------------
        # Branch 2: No Unit found in the line
        # -------------------------------------------------------------

        # Check qualitative results (e.g. "Protein TRACE", "Bacteria PRESENT", "Urobilinogen Negative")
        qualitative = cls._parse_qualitative(line)
        if qualitative:
            if extracted_method and not qualitative.method:
                qualitative.method = extracted_method
            return qualitative, None

        # Check numeric without unit (e.g. "CHOL / HDL Ratio = 3.26", "CHOL/HDL Ratio 3.26", "BUN/Creatinine Ratio 15.2 10.0-20.0")
        ref_end_m = re.search(
            r"(?<![A-Za-z0-9])\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?\s*$",
            line,
        )
        limit_end_m = re.search(
            r"\b(?:less\s+than|greater\s+than|[<>]=?)\s*\d+(?:\.\d+)?\s*$",
            line,
            re.IGNORECASE,
        )
        ref_m = ref_end_m or limit_end_m
        if ref_m:
            ref_text = ref_m.group(0).strip()
            line_before_ref = line[: ref_m.start()].strip()
            num_m = re.search(
                r"([<>=]=?\s*)?(-?\d+(?:\.\d+)?)[*#]?\s*$",
                line_before_ref,
            )
            if num_m:
                val_str = num_m.group(2)
                numeric_val = float(val_str)
                raw_name = line_before_ref[: num_m.start()].strip(" :-|\t")
                ref_range, warning = cls.parse_reference_range(ref_text)
                raw_name, sub_method = cls._clean_test_name_and_method(raw_name)
                if sub_method and not extracted_method:
                    extracted_method = sub_method

                if raw_name and re.search(r"[A-Za-z]", raw_name):
                    return (
                        LabTestResult(
                            raw_test_name=raw_name,
                            canonical_test_name=None,
                            loinc_code=None,
                            value=numeric_val,
                            unit=None,
                            reference_range=ref_range,
                            raw_value=val_str,
                            status=None,
                            flag=None,
                            method=extracted_method,
                        ),
                        warning,
                    )

        # Trailing numeric value without reference (e.g. "CHOL / HDL Ratio = 3.26")
        trailing_num_m = re.search(
            r"[:=]?\s*(-?\d+(?:\.\d+)?)[*#]?\s*$",
            line,
        )
        if trailing_num_m:
            val_str = trailing_num_m.group(1)
            numeric_val = float(val_str)
            raw_name = line[: trailing_num_m.start()].strip(" :=-|\t")
            raw_name, sub_method = cls._clean_test_name_and_method(raw_name)
            if sub_method and not extracted_method:
                extracted_method = sub_method

            if (
                raw_name
                and len(raw_name) >= 2
                and re.search(r"[A-Za-z]", raw_name)
                and not cls._looks_like_metadata(raw_name)
                and not cls._is_reference_row(raw_name)
            ):
                return (
                    LabTestResult(
                        raw_test_name=raw_name,
                        canonical_test_name=None,
                        loinc_code=None,
                        value=numeric_val,
                        unit=None,
                        reference_range=None,
                        raw_value=val_str,
                        status=None,
                        flag=None,
                        method=extracted_method,
                    ),
                    None,
                )

        return None, "Line does not contain a numeric lab value."

    @classmethod
    def _stitch_lines(
        cls,
        lines: list[str],
    ) -> list[str]:

        result: list[str] = []

        i = 0
        in_interpretation = False

        while i < len(lines):

            current = cls._normalize_spaces(lines[i])

            if not current:
                i += 1
                continue

            current_lower = current.lower()

            c_type = cls.classify_line(current, in_interpretation=in_interpretation)
            if c_type == LineType.SECTION_HEADING:
                in_interpretation = False
                result.append(current)
                i += 1
                continue

            if c_type == LineType.INTERPRETATION:
                in_interpretation = True
                result.append(current)
                i += 1
                continue

            if in_interpretation:
                result.append(current)
                i += 1
                continue

            # Metadata lines and reference rows must never be stitched as a test name
            if c_type in (
                LineType.METADATA,
                LineType.REFERENCE_ROW,
            ):
                result.append(current)
                i += 1
                continue

            # If current already contains a complete qualitative result, do not stitch
            if cls._parse_qualitative(current) is not None:
                result.append(current)
                i += 1
                continue

            has_numeric_result = bool(cls._extract_numeric_candidate(current)) or bool(
                cls._find_unit(current)[0]
            )

            if not has_numeric_result:
                stitched = False
                for lookahead in (1, 2, 3):
                    if i + lookahead < len(lines):
                        next_line = cls._normalize_spaces(lines[i + lookahead])
                        if next_line and re.search(
                            r"(?<![A-Za-z])-?\d+(?:\.\d+)?", next_line
                        ):
                            # next_line must NOT be a separate test line, reference row, header, or metadata!
                            if next_line.startswith(("*", "•", "▪", "◦")):
                                break

                            n_type = cls.classify_line(next_line, in_interpretation=in_interpretation)
                            if n_type in (
                                LineType.METADATA,
                                LineType.SECTION_HEADING,
                                LineType.REFERENCE_ROW,
                                LineType.INTERPRETATION,
                            ):
                                break

                            # Intermediate lines must NOT be table headers
                            intermediates = [
                                cls._normalize_spaces(lines[i + k])
                                for k in range(1, lookahead)
                            ]
                            header_in_middle = any(
                                any(
                                    term in mid.lower()
                                    for term in (
                                        "test name",
                                        "observed value",
                                        "units",
                                        "reference",
                                        "investigation",
                                        "biological",
                                    )
                                )
                                for mid in intermediates
                            )
                            if header_in_middle:
                                break

                            # Intermediate lines shouldn't have numbers
                            if any(re.search(r"\d", mid) for mid in intermediates):
                                break

                            blocked = any(
                                term in current_lower
                                for term in (
                                    "patient",
                                    "doctor",
                                    "report",
                                    "result",
                                    "investigation",
                                    "interpretation",
                                    "reference",
                                    "sample",
                                    "page",
                                    "method:",
                                    "technique:",
                                )
                            )
                            if blocked or cls.is_metadata_line(next_line):
                                break

                            if lookahead == 1:
                                result.append(f"{current} {next_line}")
                                i += 2
                                stitched = True
                                break
                            elif lookahead == 2:
                                mid = intermediates[0]
                                if not cls.is_metadata_line(mid):
                                    result.append(f"{current} ({mid}) {next_line}")
                                    i += 3
                                    stitched = True
                                    break
                            elif lookahead == 3:
                                mid_text = " ".join(intermediates)
                                if not any(
                                    cls.is_metadata_line(m) for m in intermediates
                                ):
                                    result.append(f"{current} ({mid_text}) {next_line}")
                                    i += 4
                                    stitched = True
                                    break
                if stitched:
                    continue

            result.append(current)
            i += 1

        return result

    @classmethod
    def _extract_metadata(
        cls,
        lines: List[str],
    ) -> Tuple[
        Optional[str],
        Optional[int],
        Optional[str],
        Optional[str],
        List[str],
        List[str],
        List[str],
        List[str],
    ]:

        full_text = "\n".join(lines)

        patient_names: List[str] = []
        ages: List[int] = []
        genders: List[str] = []
        patient_ids: List[str] = []
        reported_dates: List[str] = []
        req_numbers: List[str] = []

        # Patient name
        name_pattern = re.compile(
            r"(?:patient\s*name|"
            r"patient\b|name\b)"
            r"\s*[:\-]?\s*"
            r"([A-Za-z][A-Za-z .'-]{1,60})"
            r"(?=\s+(?:age|gender|sex|"
            r"vial|uhid|visit|mrn|req|"
            r"collected|registered|reported|"
            r"date|client|address|lab\s*no)|"
            r"[\r\n]|$)",
            re.IGNORECASE,
        )

        for match in name_pattern.finditer(full_text):

            name = cls._normalize_spaces(match.group(1))

            if (
                len(name) >= 2
                and name.lower()
                not in {
                    "null",
                    "none",
                    "patient",
                }
                and not cls._looks_like_metadata(name)
            ):
                patient_names.append(name)

        # Age
        for match in re.finditer(
            r"\b(?:age|age\s*/\s*gender|age\s*/\s*sex)\s*[:\-]\s*(\d{1,3})\b",
            full_text,
            re.IGNORECASE,
        ):
            ages.append(int(match.group(1)))

        # Gender
        for match in re.finditer(
            r"(?:gender|sex|age\s*/\s*gender|age\s*/\s*sex)\s*[:\-]\s*(?:(?:\d{1,3}\s*(?:years?|yrs?|y)?\s*/\s*)?)(male|female|m|f)\b",
            full_text,
            re.IGNORECASE,
        ):

            value = match.group(1).lower()

            genders.append("Male" if value in {"male", "m"} else "Female")

        # Vial / patient ID
        for match in re.finditer(
            r"(?:vial\s*id|uhid|patient\s*id|" r"mrn)\s*[:\-]?\s*([A-Za-z0-9\-\/]+)",
            full_text,
            re.IGNORECASE,
        ):
            patient_ids.append(match.group(1).strip())

        # Request number
        for match in re.finditer(
            r"(?:req\s*no\.?|request\s*no\.?)\s*" r"[:\-]?\s*([A-Za-z0-9\-\/]+)",
            full_text,
            re.IGNORECASE,
        ):
            req_numbers.append(match.group(1).strip())

        # Reported On / Report Date / Final Report Date / Reported
        for match in re.finditer(
            r"(?:reported\s*on|reported|report\s*date|final\s*report|collection\s*date|registered\s*date|date)\s*[:\-]?\s*"
            r"([0-9A-Za-z:/\-\s]{5,40}?)"
            r"(?=[\r\n]|\s+(?:patient|client|page|req|sample|vial|visit|uhid|age|sex|gender|a/c|$))",
            full_text,
            re.IGNORECASE,
        ):

            date_value = cls.parse_date_to_iso(match.group(1))

            if date_value:
                reported_dates.append(date_value)

        return (
            patient_names[0] if patient_names else None,
            ages[0] if ages else None,
            genders[0] if genders else None,
            patient_ids[0] if patient_ids else None,
            reported_dates,
            patient_ids,
            req_numbers,
            patient_names,
        )

    @classmethod
    def _deduplicate_tests(
        cls,
        tests: List[LabTestResult],
    ) -> List[LabTestResult]:

        result: List[LabTestResult] = []

        seen = set()

        has_b12 = any("b12" in (t.raw_test_name or "").lower() for t in tests)
        for test in tests:
            name = cls._normalize_spaces(test.raw_test_name).lower()
            name_clean = re.sub(r"^[*\s,:-]+|[*\s,:-]+$", "", name)

            # Drop standalone "vitamin - b" if vitamin b12 is present
            if name_clean in ("vitamin - b", "vitamin b") and has_b12:
                continue

            # Drop false tests with impossible negative numbers (e.g. -6380 from MC-6380)
            if test.value is not None and test.value < -100:
                continue

            # Drop metadata or watermark lines
            if any(bad in name for bad in ("tez.health", "nabl", "pvt ltd", "pvt.ltd", "better quality")):
                continue

            value = str(test.value) if test.value is not None else str(test.raw_value)
            unit = test.unit.lower() if test.unit else ""

            key = (
                name,
                value,
                unit,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(test)

        return result

    @classmethod
    def parse_document_text(
        cls,
        report_id: str,
        lines: List[str],
    ) -> ExtractedReportData:

        warnings: List[str] = []

        # ---------------------------------------------------------
        # 1. Clean OCR text
        # ---------------------------------------------------------

        cleaned_lines = []

        for line in lines:

            line = cls._clean_pua(line or "")

            line = line.replace(
                "\x00",
                "",
            )

            line = cls._normalize_spaces(line)

            if line:
                cleaned_lines.append(line)

        # ---------------------------------------------------------
        # 2. Metadata
        # ---------------------------------------------------------

        (
            resolved_name,
            resolved_age,
            resolved_gender,
            first_patient_id,
            reported_dates,
            patient_ids,
            req_numbers,
            patient_names,
        ) = cls._extract_metadata(cleaned_lines)

        # Resolve report date
        resolved_date = None

        if reported_dates:

            counts: Dict[str, int] = {}

            for date in reported_dates:
                counts[date] = counts.get(date, 0) + 1

            resolved_date = max(
                counts,
                key=lambda d: counts[d],
            )

            if len(counts) > 1:

                conflicts = [d for d in counts if d != resolved_date]

                warnings.append(
                    "Discrepancy in Reported On "
                    "timestamp across report pages "
                    f"(Conflicting: "
                    f"'{', '.join(conflicts)}', "
                    f"Majority/Resolved: "
                    f"'{resolved_date}')."
                )

        # Resolve patient ID
        resolved_patient_id = first_patient_id

        if patient_ids:

            id_counts: Dict[str, int] = {}

            for pid in patient_ids:
                id_counts[pid] = id_counts.get(pid, 0) + 1

            resolved_patient_id = max(
                id_counts,
                key=lambda pid: id_counts[pid],
            )

            if len(id_counts) > 1:

                conflicts = [pid for pid in id_counts if pid != resolved_patient_id]

                warnings.append(
                    "Discrepancy in patient ID "
                    "across report pages "
                    f"(Conflicting: "
                    f"'{', '.join(conflicts)}', "
                    f"Resolved: "
                    f"'{resolved_patient_id}')."
                )

        # ---------------------------------------------------------
        # 3. Lab name
        # ---------------------------------------------------------

        full_text = "\n".join(cleaned_lines)

        lab_name = cls.extract_lab_name(
            full_text,
            cleaned_lines,
        )

        # ---------------------------------------------------------
        # 4. Multi-line reconstruction
        # ---------------------------------------------------------

        stitched_lines = cls._stitch_lines(cleaned_lines)

        # ---------------------------------------------------------
        # 5. Parse EVERY relevant line
        #
        # Important:
        # We intentionally do NOT require:
        #
        #     in_lab_section == True
        #
        # This fixes the main extraction bug.
        # ---------------------------------------------------------

        tests: List[LabTestResult] = []
        in_interpretation = False

        for index, line in enumerate(stitched_lines):
            line = line.strip()
            if not line:
                continue

            lower = line.lower()
            if lower.startswith("page "):
                continue

            # Classify line
            c_type = cls.classify_line(line, in_interpretation=in_interpretation)

            if c_type == LineType.SECTION_HEADING:
                in_interpretation = False
                continue

            if c_type == LineType.INTERPRETATION:
                in_interpretation = True
                continue

            if in_interpretation:
                continue

            if c_type == LineType.METADATA:
                continue

            if c_type == LineType.REFERENCE_ROW:
                if tests:
                    cls._attach_reference_row(tests[-1], line)
                continue

            # Continuation of a multi-line method (e.g. "Peroxidase)" or closes unmatched paren)
            if (
                tests
                and tests[-1].method
                and (
                    tests[-1].method.count("(") > tests[-1].method.count(")")
                    or tests[-1].method.endswith(",")
                )
            ):
                if not bool(
                    cls._extract_numeric_candidate(line)
                ) and not line.startswith(("*", "•", "▪", "◦")):
                    tests[-1].method = f"{tests[-1].method} {line}".strip()
                    continue

            # Reset interpretation state upon encountering candidate test
            in_interpretation = False

            test, warning = cls.parse_test_line(line)
            if test is not None:
                tests.append(test)
                if warning:
                    warnings.append(warning)

        # ---------------------------------------------------------
        # 6. Remove duplicates
        # ---------------------------------------------------------

        tests = cls._deduplicate_tests(tests)

        # ---------------------------------------------------------
        # 7. Diagnostics
        # ---------------------------------------------------------

        logger.info(
            "PARSER_RESULT report_id=%s "
            "input_lines=%d "
            "stitched_lines=%d "
            "extracted_tests=%d",
            report_id,
            len(cleaned_lines),
            len(stitched_lines),
            len(tests),
        )

        logger.info(
            "PARSER_TEST_NAMES report_id=%s tests=%s",
            report_id,
            [test.raw_test_name for test in tests],
        )

        if not tests:

            warnings.append(
                "NO_TESTS_EXTRACTED: "
                "No laboratory test rows "
                "could be confidently "
                "extracted from document."
            )

        return ExtractedReportData(
            schema_version="1.0",
            report=ReportMetadata(
                report_id=report_id,
                report_date=resolved_date,
                lab_name=lab_name,
            ),
            patient=PatientInfo(
                patient_id=resolved_patient_id,
                name=resolved_name,
                age=resolved_age,
                gender=resolved_gender,
            ),
            tests=tests,
            warnings=warnings,
        )
