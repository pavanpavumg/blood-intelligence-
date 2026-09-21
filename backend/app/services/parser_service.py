import re

from datetime import datetime
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
        "uIU/mL",
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

    @classmethod
    def _clean_pua(cls, text: str) -> str:
        if not text:
            return ""

        return re.sub(
            r"[\uf000-\uf0ff]",
            lambda m: chr(ord(m.group(0)) - 0xF000),
            text,
        )

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
            return (
                ReferenceRange(
                    low=None,
                    high=None,
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

        for unit in cls.COMMON_UNITS:

            pattern = re.compile(
                r"(?<!\w)" + re.escape(unit) + r"(?!\w)",
                re.IGNORECASE,
            )

            match = pattern.search(text)

            if match:
                return unit, match

        return None, None

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
    def _parse_qualitative(
        cls,
        line: str,
    ) -> Optional[LabTestResult]:

        qualitative_pattern = re.compile(
            r"\b("
            r"negative|"
            r"positive|"
            r"nil|"
            r"trace|"
            r"present|"
            r"absent|"
            r"normal|"
            r"clear|"
            r"turbid|"
            r"pale\s+yellow|"
            r"straw|"
            r"yellow"
            r")\b",
            re.IGNORECASE,
        )

        match = qualitative_pattern.search(line)

        if not match:
            return None

        name = line[: match.start()].strip(" :-_\t")

        if not name:
            return None

        if cls._looks_like_metadata(name):
            return None

        value = match.group(1)

        normal_words = {
            "negative",
            "nil",
            "absent",
            "normal",
            "clear",
            "pale yellow",
            "straw",
        }

        status = "NORMAL" if value.lower() in normal_words else "HIGH"

        return LabTestResult(
            raw_test_name=name,
            canonical_test_name=None,
            loinc_code=None,
            value=None,
            unit=None,
            reference_range=ReferenceRange(
                low=None,
                high=None,
                raw=value,
                type="CATEGORICAL",
            ),
            raw_value=value,
            status=status,
            flag=None,
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

        # Ignore visual table borders
        if (
            line.startswith("|")
            or line.startswith("+")
            or re.fullmatch(
                r"[-_= ]+",
                line,
            )
        ):
            return None, None

        # Ignore headers
        if any(h in lower for h in cls.HEADER_FRAGMENTS):
            # But don't reject genuine tests merely because
            # "result" appears in a long row.
            if not re.search(
                r"\d",
                line,
            ):
                return None, None

        if cls._looks_like_metadata(line):
            return None, None

        # Method extraction
        extracted_method = None

        method_match = re.match(
            r"^(?:method|technique|procedure)" r"\s*:\s*(.*?)\s+" r"(.+)$",
            line,
            re.IGNORECASE,
        )

        if method_match:

            extracted_method = method_match.group(1).strip()

            line = method_match.group(2).strip()

            lower = line.lower()

        # Parenthesized method before test name
        prefix_method = re.match(
            r"^\(([^)]+)\)\s*(.+)$",
            line,
        )

        if prefix_method:

            possible_method = prefix_method.group(1).strip()

            possible_name = prefix_method.group(2).strip()

            if any(
                word in possible_method.lower()
                for word in (
                    "pod",
                    "hplc",
                    "enzyme",
                    "immuno",
                    "method",
                    "calculated",
                    "direct",
                )
            ):

                extracted_method = possible_method
                line = possible_name

        # Find unit first.
        unit, unit_match = cls._find_unit(line)

        # Numeric result
        value_match = cls._extract_numeric_candidate(line)

        # If no number, attempt qualitative extraction.
        if not value_match:

            qualitative = cls._parse_qualitative(line)

            if qualitative:
                return qualitative, None

            return None, "Line does not contain a numeric lab value."

        numeric_value = float(value_match.group(0))

        # Avoid extracting the "25" from
        # 25-Hydroxy Vitamin D.
        prefix = line[: value_match.start()].strip()

        if re.search(
            r"[A-Za-z]-$",
            prefix,
        ):
            next_part = line[value_match.end() :]

            if re.match(
                r"[-–—][A-Za-z]",
                next_part,
            ):
                second_match = re.search(
                    r"(?<![A-Za-z])" r"-?\d+(?:\.\d+)?" r"(?![A-Za-z])",
                    next_part,
                )

                if second_match:
                    value_match = second_match
                    numeric_value = float(second_match.group(0))

        # Determine test name.
        raw_name = line[: value_match.start()]

        # Remove trailing unit or relational operators before value match
        if unit:
            raw_name = re.sub(
                r"\b" + re.escape(unit) + r"\b.*$", "", raw_name, flags=re.IGNORECASE
            )

        raw_name = re.sub(
            r"(?:\b(?:less\s+than|greater\s+than|up\s*to|upto|below|above)\b|[<>=]+).*$",
            "",
            raw_name,
            flags=re.IGNORECASE,
        )

        # Remove trailing separators
        raw_name = raw_name.strip(" :-|\t")

        raw_name = cls._remove_test_prefix(raw_name)

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
                    )
                ):
                    clean_method = re.sub(
                        r"^(?:method|technique|procedure)\s*:\s*",
                        "",
                        cand,
                        flags=re.IGNORECASE,
                    ).strip()
                    if not extracted_method:
                        extracted_method = clean_method
                    raw_name = raw_name[:open_idx].strip()

        if not raw_name:
            return None, None

        raw_clean = raw_name.lower().strip(" :-|")
        if raw_clean in {
            "female",
            "male",
            "females",
            "males",
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
        }:
            return None, None

        if cls._looks_like_metadata(raw_name):
            return None, None

        # Very long narrative line is unlikely to be a test.
        if len(raw_name) > 100:
            return None, None

        # A test name should contain alphabetic characters.
        if not re.search(
            r"[A-Za-z]",
            raw_name,
        ):
            return None, None

        # Everything after the value is a possible reference range.
        remainder_start = value_match.end()

        remainder = line[remainder_start:].strip()

        # Remove unit token from remainder if present
        if unit and unit_match:
            unit_pattern = re.compile(
                r"(?<!\w)" + re.escape(unit) + r"(?!\w)",
                re.IGNORECASE,
            )
            remainder = unit_pattern.sub(" ", remainder).strip()

        # Truncate remainder at metadata keyword boundaries
        metadata_split = re.split(
            r"\b(?:date|visit\s*id|uhid|age|sex|gender|mobile|phone|ref(?:erred)?\s*by|sample|final\s*report)\b",
            remainder,
            flags=re.IGNORECASE,
        )
        if metadata_split:
            remainder = metadata_split[0].strip()

        # Remove status words before reference range.
        remainder = re.sub(
            r"^(?:normal|high|low|" r"abnormal|trace|" r"positive|negative)\b\s*",
            "",
            remainder,
            flags=re.IGNORECASE,
        ).strip()

        reference_range = None
        warning = None

        if remainder:

            reference_range, warning = cls.parse_reference_range(remainder)

        raw_value = f"{value_match.group(0)}" f"{' ' + unit if unit else ''}"

        result = LabTestResult(
            raw_test_name=raw_name,
            canonical_test_name=None,
            loinc_code=None,
            value=numeric_value,
            unit=unit,
            reference_range=reference_range,
            raw_value=raw_value,
            status=None,
            flag=None,
            method=extracted_method,
        )

        return result, warning

    @classmethod
    def _stitch_lines(
        cls,
        lines: list[str],
    ) -> list[str]:

        result: list[str] = []

        i = 0

        while i < len(lines):

            current = cls._normalize_spaces(lines[i])

            if not current:
                i += 1
                continue

            current_lower = current.lower()

            # Metadata lines, headers, and method lines must never be stitched as a test name
            if (
                cls.is_metadata_line(current)
                or current_lower
                in (
                    "cbc",
                    "complete blood count",
                    "haematology",
                    "biochemistry",
                    "clinical pathology",
                    "serology",
                    "microbiology",
                    "urinalysis",
                    "urine examination",
                    "lipid profile",
                    "renal panel",
                    "renal profile",
                    "liver function test",
                    "kidney basic screen",
                )
                or any(
                    term in current_lower
                    for term in (
                        "test name",
                        "investigation",
                        "reference range",
                        "observed value",
                        "biological reference",
                        "panel",
                        "screen",
                        "profile",
                        "header",
                    )
                )
                or re.match(
                    r"^(?:method|technique|procedure)\b", current, re.IGNORECASE
                )
            ):
                result.append(current)
                i += 1
                continue

            has_numeric_result = bool(cls._extract_numeric_candidate(current))

            if not has_numeric_result:
                stitched = False
                for lookahead in (1, 2, 3):
                    if i + lookahead < len(lines):
                        next_line = cls._normalize_spaces(lines[i + lookahead])
                        if next_line and re.search(
                            r"(?<![A-Za-z])-?\d+(?:\.\d+)?", next_line
                        ):
                            # next_line must NOT be a separate test line!
                            if next_line.startswith(("*", "•", "▪", "◦")):
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
            r"patient|name)"
            r"\s*[:\-]\s*"
            r"([A-Za-z][A-Za-z .'-]{1,60})"
            r"(?=\s+(?:age|gender|sex|"
            r"vial|uhid|visit|mrn|req|"
            r"collected|registered|reported|"
            r"date|client|address|lab\s*no)|"
            r"\s*$)",
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
            r"(?:vial\s*id|uhid|patient\s*id|" r"mrn)\s*[:\-]\s*([A-Za-z0-9\-\/]+)",
            full_text,
            re.IGNORECASE,
        ):
            patient_ids.append(match.group(1).strip())

        # Request number
        for match in re.finditer(
            r"(?:req\s*no|request\s*no)\s*" r"[:\-]\s*([A-Za-z0-9\-\/]+)",
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

        for test in tests:

            name = cls._normalize_spaces(test.raw_test_name).lower()

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

        for index, line in enumerate(stitched_lines):

            line = line.strip()

            if not line:
                continue

            if cls.is_metadata_line(line):
                continue

            lower = line.lower()

            # Ignore obvious page headers
            if lower.startswith("page "):
                continue

            # Ignore section narrative
            if any(term in lower for term in cls.SECTION_STOP_WORDS):
                continue

            # Check if line is a pure method line (e.g. "Method:ISE Direct" or "Method:Calculated")
            pure_method_match = re.match(
                r"^(?:method|technique|procedure)\s*:\s*(.*?)$", line, re.IGNORECASE
            )
            if pure_method_match:
                cand_method = pure_method_match.group(1).strip()
                # Check if this method line has a demographic range (e.g. "Uricase-Peroxidase Female:2.3 - 6.1")
                demo_match = re.search(
                    r"\b(female|male|females|males)\s*:\s*(\d+(?:\.\d+)?\s*[-–—]\s*\d+(?:\.\d+)?)",
                    cand_method,
                    re.IGNORECASE,
                )
                if demo_match:
                    demo_range = demo_match.group(0)
                    cand_method = cand_method[: demo_match.start()].strip()
                    if tests and tests[-1].reference_range:
                        if tests[-1].reference_range.raw:
                            tests[-1].reference_range.raw = (
                                f"{tests[-1].reference_range.raw} {demo_range}".strip()
                            )
                        else:
                            tests[-1].reference_range.raw = demo_range
                        tests[-1].reference_range.type = "DEMOGRAPHIC"

                if cand_method and tests:
                    clean_c = re.sub(
                        r"^(?:method|technique|procedure)\s*:\s*",
                        "",
                        cand_method,
                        flags=re.IGNORECASE,
                    ).strip()
                    if not tests[-1].method:
                        tests[-1].method = clean_c
                    elif clean_c not in tests[-1].method:
                        tests[-1].method = f"{tests[-1].method} {clean_c}"
                continue

            # Check if line is a continuation of a multi-line method (e.g. "Peroxidase)" or closes unmatched paren)
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

            # Check if line is a demographic reference range line (e.g. "Female: 2.3 - 6.1" or "Female 2.3 - 6.1")
            demo_line_match = re.match(
                r"^(female|male|females|males)\s*[:\-]?\s*(\d+(?:\.\d+)?(?:\s*[-–—]\s*\d+(?:\.\d+)?)?.*)$",
                line,
                re.IGNORECASE,
            )
            if demo_line_match:
                if tests and tests[-1].reference_range:
                    raw_demo = line.strip()
                    if tests[-1].reference_range.raw:
                        tests[-1].reference_range.raw = (
                            f"{tests[-1].reference_range.raw} {raw_demo}".strip()
                        )
                    else:
                        tests[-1].reference_range.raw = raw_demo
                    tests[-1].reference_range.type = "DEMOGRAPHIC"
                continue

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
