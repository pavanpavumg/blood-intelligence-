import re
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from app.schemas.lab_result import LabTestResult, ReferenceRange
from app.schemas.report import PatientInfo, ReportMetadata, ExtractedReportData
from app.core.logging import logger
from app.services.test_mapping_service import TestMappingService


class ParserService:
    """
    Deterministic layout and regex parser for laboratory reports.
    Extracts metadata, patient demographics, and test rows without using an LLM.
    Supports multi-page, multi-panel reports and per-section interpretation isolation.
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
        "103/L",
        "10^3/uL",
        "10^6/uL",
        "10(3)/uL",
        "10(3)/mm3",
        "10^6/L",
        "10^3",
        "10^6",
        "/cumm",
        "cumm",
        "cmm",
        "gm%",
        "gm %",
        "g%",
        "mg/dL",
        "mg/L",
        "mmol/L",
        "uIU/mL",
        "mIU/L",
        "g/dL",
        "g/L",
        "pg/mL",
        "ng/mL",
        "mcg/dL",
        "ug/dL",
        "ug/L",
        "mEq/L",
        "IU/L",
        "U/L",
        "%",
        "fl",
        "fL",
        "um",
        "pg",
    ]

    INVALID_TEST_NAMES = {
        "mobile no",
        "mobile",
        "phone",
        "phone no",
        "tel",
        "fax",
        "final report",
        "report",
        "interim report",
        "status",
        "dr",
        "dr.",
        "doctor",
        "consultant",
        "ref by",
        "referred by",
        "less than",
        "greater than",
        "date",
        "time",
        "page",
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
        "observed values",
        "units",
        "biological reference intervals",
        "reference range",
        "differential count",
        "complete blood count (cbc)",
        "cbc",
    }

    TIMESTAMP_PATTERN = re.compile(
        r"\b\d{1,2}:\d{2}(?:\s*[AP]M)?\b|\b20\d{2}\b", re.IGNORECASE
    )

    @classmethod
    def parse_date_to_iso(cls, date_str: str) -> Optional[str]:
        """
        Converts various report date strings into ISO format.
        E.g., '23-Jun-2026 10:55 AM' -> '2026-06-23T10:55:00'
        '03-Feb-2026 06:11 PM' -> '2026-02-03T18:11:00'
        """
        if not date_str or not date_str.strip():
            return None

        clean_str = date_str.strip()

        match = re.search(
            r"(\d{1,2})[\/\-\s]([A-Za-z]{3}|\d{1,2})[\/\-\s](\d{4})(?:\s+(\d{1,2}):(\d{2})(?::(\d{2}))?\s*([AP]M)?)?",
            clean_str,
            re.IGNORECASE,
        )
        if match:
            day, month_str, year, hr, mn, sec, ampm = match.groups()
            try:
                if month_str.isdigit():
                    m = int(month_str)
                else:
                    m = datetime.strptime(month_str[:3].title(), "%b").month

                d = int(day)
                y = int(year)

                if hr and mn:
                    h = int(hr)
                    mi = int(mn)
                    s = int(sec) if sec else 0
                    if ampm:
                        ampm = ampm.upper()
                        if ampm == "PM" and h < 12:
                            h += 12
                        elif ampm == "AM" and h == 12:
                            h = 0
                    return f"{y:04d}-{m:02d}-{d:02d}T{h:02d}:{mi:02d}:{s:02d}"
                return f"{y:04d}-{m:02d}-{d:02d}"
            except Exception:
                pass

        iso_match = re.search(r"(\d{4})[\-\/](\d{1,2})[\-\/](\d{1,2})", clean_str)
        if iso_match:
            y, m, d = iso_match.groups()
            return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

        return clean_str

    @classmethod
    def extract_lab_name(cls, full_text: str, doc_lines: List[str]) -> Optional[str]:
        """
        Extracts laboratory name generically from explicit labels, known brand entities, or document header lines.
        """
        text_lower = full_text.lower()
        if "drlogy" in text_lower:
            return "Drlogy Pathology Lab"
        elif "quest diagnostics" in text_lower:
            return "Quest Diagnostics"
        elif "labcorp" in text_lower:
            return "LabCorp"
        elif (
            "centromed" in text_lower
            or "cmlkad" in text_lower
            or re.search(r"\bcml\b", text_lower)
        ):
            return "CENTROMED LABS PVT. LTD"

        # 1. Look for explicit key-value labels
        match = re.search(
            r"(?:laboratory|lab\s*name|hospital\s*laboratory|diagnostics|labs)\s*:\s*([A-Za-z0-9\.\,\s\&\-\'\(\)]+?)(?=\s*(?:\r?\n|$|vial|patient|page|ref|req))",
            full_text,
            re.IGNORECASE,
        )
        if match:
            candidate = match.group(1).strip()
            if (
                candidate
                and len(candidate) >= 3
                and not any(
                    k in candidate.lower()
                    for k in ["patient", "doctor", "report", "result"]
                )
            ):
                return candidate

        # 2. Look for header lines matching laboratory entity names (top 15 lines)
        header_lines = doc_lines[:15] if doc_lines else []
        for line in header_lines:
            clean = line.strip()
            if re.search(
                r"\b(?:labs|laboratory|diagnostics|pathology)\b", clean, re.IGNORECASE
            ):
                clean_lower = clean.lower()
                if not any(
                    k in clean_lower
                    for k in [
                        "report",
                        "department",
                        "section",
                        "patient",
                        "doctor",
                        "page",
                        "result",
                        "test",
                        "sample",
                        "vial",
                        "collected",
                        "reported",
                        "interpretation",
                        "end of",
                        "range",
                        "unit",
                        "value",
                    ]
                ):
                    clean = re.sub(r"^[\*\-\d\.\s]+", "", clean).strip()
                    if len(clean) >= 3:
                        return clean

        return None

    @classmethod
    def parse_reference_range(
        cls, text: str
    ) -> Tuple[Optional[ReferenceRange], Optional[str]]:
        """
        Parses reference ranges into numeric low, high, and raw string format.
        Supports range '70-100', less-than '<200', greater-than '>40', 'Up to 6.0', and gender-specific ranges.
        Rejects narrative interpretation text, metadata, and timestamps.
        """
        if not text or not text.strip():
            return None, None

        raw = text.strip()
        # Remove Method text (e.g. Method:Uricase-Peroxidase) and leading unit prefixes
        raw = re.sub(
            r"\bMethod\s*:\s*.*?(?=(?:\b(?:Male|Female)\b|\d+|\s*$))",
            "",
            raw,
            flags=re.IGNORECASE,
        ).strip()
        raw = re.sub(r"\bMethod\s*:\s*[^\s]+", "", raw, flags=re.IGNORECASE).strip()
        raw = re.sub(
            r"^(?:mg/dL|g/dL|mmol/L|mg/L|uIU/mL|%)\s*", "", raw, flags=re.IGNORECASE
        ).strip()
        raw = re.sub(r"\s+", " ", raw).strip()
        if not raw:
            return None, None
        raw_lower = raw.lower()

        # Reject interpretation / narrative strings
        if any(
            k in raw_lower
            for k in [
                "years",
                "vial",
                "req no",
                "sample",
                "registered",
                "reported",
                "acute phase",
                "sensitive",
                "indicator",
                "inflammation",
                "protein",
                "activation",
                "kidney disease",
                "symptoms",
                "testing is",
                "risk factors",
                "detected with",
                "hours",
            ]
        ):
            return None, None

        if cls.TIMESTAMP_PATTERN.search(raw) and not any(
            symbol in raw_lower
            for symbol in ["<", ">", "ref", "normal", "interval", "up to"]
        ):
            if re.search(r"\d{2}:\d{2}|\b20\d{2}\b", raw):
                return None, None

        # Gender-specific range check (e.g. "Male:3.6 -8.2 Female:2.3 - 6.1")
        if "male" in raw_lower or "female" in raw_lower:
            return ReferenceRange(low=None, high=None, raw=raw), None

        # Range format: 12.0 - 15.0, 4000-11000, 02 - 06, 70 - 100
        range_match = re.search(r"(\d+(?:\.\d+)?)\s*[\-\–\—]\s*(\d+(?:\.\d+)?)", raw)
        if range_match:
            try:
                low = float(range_match.group(1))
                high = float(range_match.group(2))
                if 1990 <= low <= 2099 and 1990 <= high <= 2099:
                    return None, None
                return ReferenceRange(low=low, high=high, raw=raw), None
            except ValueError:
                pass

        # Up to / Less than format: "Up to 6.0", "< 200", "<= 5.7", "less than 6"
        lt_match = re.search(
            r"(?:up\s+to|less\s+than(?:\s+or\s+equal\s+to)?|<=?)\s*(\d+(?:\.\d+)?)",
            raw,
            re.IGNORECASE,
        )
        if lt_match:
            try:
                high = float(lt_match.group(1))
                return ReferenceRange(low=None, high=high, raw=raw), None
            except ValueError:
                pass

        # Greater than / More than format: "> 40", ">= 10", "greater than 40", "more than 10"
        gt_match = re.search(
            r"(?:greater\s+than(?:\s+or\s+equal\s+to)?|more\s+than(?:\s+or\s+equal\s+to)?|>=?)\s*(\d+(?:\.\d+)?)",
            raw,
            re.IGNORECASE,
        )
        if gt_match:
            try:
                low = float(gt_match.group(1))
                return ReferenceRange(low=low, high=None, raw=raw), None
            except ValueError:
                pass

        return (
            ReferenceRange(low=None, high=None, raw=raw),
            f"Unparsed reference range format: '{raw}'",
        )

    @classmethod
    def parse_test_line(
        cls, line: str
    ) -> Tuple[Optional[LabTestResult], Optional[str]]:
        """
        Extracts test name, raw value, numerical value, unit, and reference range from a text line.
        Supports unit-less tests (e.g. BUN/CREATININE RATIO 11.26).
        """
        if not line or len(line.strip()) < 2:
            return None, None

        clean_line = line.strip()

        # Handle method prefix before analyte on the same line (e.g., "Method:Electrical Impedence * RBC Count ..." or "Peroxidase) * UREA ...")
        method_prefix_match = re.match(
            r"^(?:method|technique|procedure)\s*:\s*[A-Za-z0-9\s\-\.\&\,\(\)]+\s+(\*?\s*[A-Za-z].*)$",
            clean_line,
            re.IGNORECASE,
        )
        if method_prefix_match:
            clean_line = method_prefix_match.group(1).strip()

        # Handle continuation method prefix (e.g. "Peroxidase) * UREA 20.0 mg/dL")
        continuation_prefix_match = re.match(
            r"^[A-Za-z0-9\s\,\-]+\)\s*(\*?\s*[A-Za-z].*)$",
            clean_line,
        )
        if continuation_prefix_match:
            clean_line = continuation_prefix_match.group(1).strip()

        # Skip standalone method lines (e.g. "Method:Colorimetric", "Method:Enzymatic Method (sarcosine oxidase,", "Peroxidase)")
        if re.match(
            r"^(?:method|technique|procedure)\s*:", clean_line, re.IGNORECASE
        ) or clean_line.startswith("Peroxidase)"):
            return None, None

        # Find unit using boundary matching to avoid substring truncation (e.g. mg/L vs g/L)
        unit = None
        for u in cls.COMMON_UNITS:
            pattern = r"(?:^|\s|\b)" + re.escape(u) + r"(?:\b|\s|$)"
            if re.search(pattern, clean_line):
                unit = u
                break

        # Match numbers (integers or floats)
        num_matches = list(re.finditer(r"\b\d+(?:\.\d+)?\b", clean_line))
        if not num_matches:
            return None, "Line does not contain a numeric lab value."

        val_match = num_matches[0]
        try:
            numeric_val = float(val_match.group(0))
        except ValueError:
            return None, f"Failed to parse float value from '{val_match.group(0)}'."

        # Postal code / Visit ID / Phone / Account number guard:
        # Numbers >= 100,000 without a measurement unit are metadata (e.g. postal code, visit ID, phone, KMC no), not lab measurements.
        if numeric_val >= 100000 and not unit:
            return (
                None,
                f"Numeric value '{numeric_val}' without unit exceeds valid un-unitized threshold.",
            )

        raw_test_name = clean_line[: val_match.start()].strip(" :-_\t")
        clean_name_lower = raw_test_name.lower().strip()

        # Check against invalid test name list
        if clean_name_lower in cls.INVALID_TEST_NAMES or any(
            k in clean_name_lower
            for k in [
                "patient",
                "doctor",
                "dr.",
                "vial id",
                "req no",
                "collected on",
                "reported on",
                "interpretation",
                "kmc.no",
            ]
        ):
            return None, f"Skipped invalid test name candidate: '{raw_test_name}'"

        if not raw_test_name or len(raw_test_name) < 2:
            return None, f"Test name too short or invalid in line: '{clean_line}'"

        # Check if unit-less test is valid
        if not unit:
            catalog_item, _ = TestMappingService.match_test(raw_test_name)
            if not catalog_item and not raw_test_name.startswith("*"):
                return (
                    None,
                    f"Skipped unit-less candidate not in catalog: '{raw_test_name}'",
                )

        remaining = clean_line[val_match.end() :].strip()
        # If remaining line starts with qualitatively reported words like "Normal", strip it
        remaining = re.sub(
            r"^(?:normal|high|low|abnormal|trace|negative|positive)\b\s*",
            "",
            remaining,
            flags=re.IGNORECASE,
        ).strip()

        raw_val_str = f"{val_match.group(0)} {unit}" if unit else val_match.group(0)

        # Parse reference range if remaining string has text
        ref_range_obj = None
        warning = None
        if remaining:
            ref_range_obj, ref_warning = cls.parse_reference_range(remaining)
            if ref_warning:
                warning = ref_warning

        lab_result = LabTestResult(
            raw_test_name=raw_test_name,
            canonical_test_name=None,
            loinc_code=None,
            value=numeric_val,
            unit=unit,
            reference_range=ref_range_obj,
            raw_value=raw_val_str,
            status=None,
            flag=None,
        )

        return lab_result, warning

    @classmethod
    def parse_document_text(
        cls, report_id: str, lines: List[str]
    ) -> ExtractedReportData:
        """
        Parses document lines into PatientInfo, ReportMetadata, and List[LabTestResult].
        Supports multi-panel reports, per-section interpretation isolation, and consistency-aware Vial ID resolution.
        """
        warnings: List[str] = []

        # 1. Page-level Metadata & Discrepancy Resolution
        patient_names: List[str] = []
        patient_ages: List[int] = []
        patient_genders: List[str] = []
        patient_ids: List[str] = []
        report_dates: List[str] = []
        req_numbers: List[str] = []

        full_text = "\n".join(lines)

        # Patient Name
        for m in re.finditer(
            r"(?:patient\s*name|name|patient)\s*:\s*([A-Za-z\.\s]+?)(?=\s*(?:age|gender|sex|vial|uhid|visit|mrn|patient|ref|req|collected|registered|reported|date|client|\n|$))",
            full_text,
            re.IGNORECASE,
        ):
            name_str = m.group(1).strip()
            name_str = re.sub(r"\b(uhid|uh|visit|id)\b.*$", "", name_str, flags=re.IGNORECASE).strip()
            if len(name_str) >= 2 and name_str.lower() not in ["null", "none"]:
                patient_names.append(name_str)

        if not patient_names:
            for l in lines[:10]:
                l_clean = l.strip()
                if l_clean and not any(c.isdigit() for c in l_clean):
                    l_lower = l_clean.lower()
                    if not any(
                        k in l_lower
                        for k in [
                            "lab",
                            "hospital",
                            "pathology",
                            "clinic",
                            "report",
                            "accurate",
                            "complete",
                            "cbc",
                            "test name",
                            "investigation",
                            "observed",
                        ]
                    ):
                        if len(l_clean.split()) >= 2 and len(l_clean) <= 40:
                            patient_names.append(l_clean)
                            break

        # Patient Age & Gender
        for m in re.finditer(
            r"(?:age(?:/gender|/sex)?)\s*:\s*(\d{1,3})\s*(?:y|years|yrs|y/o)?(?:\s*\d+\s*m)?(?:\s*\d+\s*d)?\s*/\s*(female|male|f|m)",
            full_text,
            re.IGNORECASE,
        ):
            patient_ages.append(int(m.group(1)))
            g_str = m.group(2).lower()
            patient_genders.append("Female" if g_str in ["female", "f"] else "Male")

        for m in re.finditer(
            r"(?:age)\s*:\s*(\d{1,3})|(\d{1,3})\s*(?:years|yrs|y/o)",
            full_text,
            re.IGNORECASE,
        ):
            val_str = m.group(1) or m.group(2)
            if val_str:
                val = int(val_str)
                if 0 < val <= 120:
                    patient_ages.append(val)

        # Patient Gender fallback
        if not patient_genders:
            for m in re.finditer(
                r"(?:gender|sex)\s*:\s*(male|female|m|f)\b|/\s*(male|female|m|f)\b",
                full_text,
                re.IGNORECASE,
            ):
                g_str = (m.group(1) or m.group(2)).lower()
                if g_str in ["m", "male"]:
                    patient_genders.append("Male")
                elif g_str in ["f", "female"]:
                    patient_genders.append("Female")

        # Patient / Vial IDs
        for m in re.finditer(
            r"(?:vial\s*id|uhid(?:\s*no)?(?:\s*/\s*visit\s*id)?|mrn|patient\s*id|reg\s*no|sample\s*id)\s*:\s*([A-Za-z0-9\.\-/]+)",
            full_text,
            re.IGNORECASE,
        ):
            raw_id = m.group(1).strip()
            primary_id = raw_id.split("/")[0].strip()
            if primary_id:
                patient_ids.append(primary_id)

        # Request Numbers
        for m in re.finditer(
            r"(?:req\s*no\.?|request\s*no\.?|order\s*no\.?)\s*:\s*([A-Za-z0-9\-]+)",
            full_text,
            re.IGNORECASE,
        ):
            req_numbers.append(m.group(1).strip())

        # Report Dates
        reported_dates = []
        for m in re.finditer(
            r"(?:reported(?:\s*on)?|report\s*date|result\s*date|completed\s*on)\s*:\s*([0-9A-Za-z\:\s\-\/]+?)(?=\s*(?:client|page|req|sample|vial|barcode|ref|\n|$))",
            full_text,
            re.IGNORECASE,
        ):
            iso_d = cls.parse_date_to_iso(m.group(1))
            if iso_d:
                reported_dates.append(iso_d)

        if not reported_dates:
            for m in re.finditer(
                r"(?:collected\s*on|date)\s*:\s*([0-9A-Za-z\:\s\-\/]+?)(?=\s*(?:client|page|req|sample|vial|\n|$))",
                full_text,
                re.IGNORECASE,
            ):
                iso_d = cls.parse_date_to_iso(m.group(1))
                if iso_d:
                    reported_dates.append(iso_d)

        report_dates = reported_dates

        resolved_name = patient_names[0] if patient_names else None
        resolved_age = patient_ages[0] if patient_ages else None
        resolved_gender = patient_genders[0] if patient_genders else None
        resolved_date = None
        if report_dates:
            unique_dates = list(set(report_dates))
            if len(unique_dates) == 1:
                resolved_date = report_dates[0]
            else:
                date_counts: Dict[str, int] = {}
                for d in report_dates:
                    date_counts[d] = date_counts.get(d, 0) + 1
                sorted_dates = sorted(
                    date_counts.keys(), key=lambda d: (date_counts[d], d), reverse=True
                )
                resolved_date = sorted_dates[0]
                conflicting_dates = [d for d in unique_dates if d != resolved_date]
                warnings.append(
                    f"Discrepancy in Reported On timestamp across report pages (Conflicting: '{', '.join(conflicting_dates)}', Majority/Resolved: '{resolved_date}')."
                )

        resolved_patient_id = None
        if patient_ids:
            if len(set(patient_ids)) == 1:
                resolved_patient_id = patient_ids[0]
            else:
                name_consistent = (
                    len(set(patient_names)) <= 1 if patient_names else True
                )
                req_consistent = len(set(req_numbers)) <= 1 if req_numbers else True

                id_counts: Dict[str, int] = {}
                for pid in patient_ids:
                    id_counts[pid] = id_counts.get(pid, 0) + 1
                majority_id = max(id_counts, key=lambda pid: id_counts[pid])

                if name_consistent and req_consistent:
                    resolved_patient_id = majority_id
                    conflicting_ids = [
                        pid for pid in set(patient_ids) if pid != majority_id
                    ]
                    req_str = req_numbers[0] if req_numbers else "N/A"
                    name_str = resolved_name or "N/A"
                    warnings.append(
                        f"Discrepancy in Vial ID across report pages (Conflicting: '{', '.join(conflicting_ids)}', Majority: '{majority_id}'). Verified patient consistency via Request No '{req_str}' and Patient Name '{name_str}'; resolved Vial ID to majority '{majority_id}'."
                    )
                else:
                    resolved_patient_id = None
                    warnings.append(
                        f"Unresolvable patient ID discrepancy across pages ({patient_ids}); set patient_id to null."
                    )

        lab_name = cls.extract_lab_name(full_text, lines)

        # Pre-pass: Line stitching for multiline test rows where Line i is test name and Line i+1 is value/unit/range
        stitched_lines = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line and not any(c.isdigit() for c in line) and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line and re.search(r"\b\d+(?:\.\d+)?\b", next_line):
                    line_lower = line.lower()
                    if not any(
                        line_lower.startswith(prefix)
                        for prefix in ["method:", "technique:", "procedure:"]
                    ) and not any(
                        k in line_lower
                        for k in [
                            "patient",
                            "doctor",
                            "dr.",
                            "sample",
                            "investigation",
                            "result",
                            "results",
                            "laboratory",
                            "report",
                            "test",
                            "cbc",
                            "interpretation",
                            "note",
                            "differential",
                            "differential count",
                            "kinetic",
                            "modified jaffe",
                            "urease",
                            "ise",
                            "bapta",
                            "uricase",
                        ]
                    ):
                        stitched_lines.append(f"{line} {next_line}")
                        i += 2
                        continue
            stitched_lines.append(line)
            i += 1

        # 2. Section-Aware Test Extraction
        test_results: List[LabTestResult] = []
        in_lab_section = False
        skip_current_section = False

        idx = 0
        while idx < len(stitched_lines):
            line = stitched_lines[idx].strip()
            l_lower = line.lower()

            # Check for Table Header / Panel Title
            is_header_line = (
                (
                    (
                        "test name" in l_lower
                        or "investigation" in l_lower
                        or "parameter" in l_lower
                    )
                    and (
                        "observed" in l_lower
                        or "result" in l_lower
                        or "units" in l_lower
                        or "reference" in l_lower
                        or "biological" in l_lower
                        or "value" in l_lower
                    )
                )
                or l_lower.startswith("investigation result")
                or l_lower.startswith("test name")
            )

            if is_header_line:
                in_lab_section = True
                skip_current_section = False
                idx += 1
                continue

            # Check for Section Terminators (Interpretation or Doctor/Pathologist Signature Blocks)
            is_interpretation_start = any(
                term in l_lower
                for term in [
                    "interpretation:",
                    "interpretation::",
                    "clinical interpretation:",
                    "comments:",
                    "comment:",
                    "remarks:",
                    "notes:",
                ]
            )

            is_signature_start = any(
                term in l_lower
                for term in [
                    "dr.",
                    "dr ",
                    "doctor",
                    "pathologist",
                    "md pathology",
                    "kmc.no",
                    "authorized signatory",
                    "electronically authenticated",
                    "end of the report",
                    "end of report",
                    "****end of report****",
                    "------end of report------",
                ]
            )

            if is_interpretation_start or is_signature_start:
                in_lab_section = False
                skip_current_section = True

            # Extract test rows if inside active lab section
            if in_lab_section and not skip_current_section:
                # Check for multiline gender reference range continuation (e.g. "Female:2.3 - 6.1")
                if "female:" in l_lower and test_results:
                    last_test = test_results[-1]
                    if (
                        last_test.reference_range
                        and last_test.reference_range.raw
                        and "male:" in last_test.reference_range.raw.lower()
                    ):
                        last_test.reference_range.raw += f" {line}"
                        idx += 1
                        continue

                test_item, line_warning = cls.parse_test_line(line)
                if test_item:
                    test_results.append(test_item)
                    if line_warning:
                        warnings.append(line_warning)

            idx += 1

        # Fallback for documents without explicit table headers
        if not test_results:
            for line in stitched_lines:
                l_lower = line.lower()
                if any(
                    k in l_lower
                    for k in [
                        "patient name:",
                        "name:",
                        "age:",
                        "gender:",
                        "sex:",
                        "vial id",
                        "req no",
                        "sample type",
                        "collected on",
                        "registered on",
                        "reported on",
                        "dr.",
                        "doctor",
                        "final report",
                        "interpretation",
                        "kmc.no",
                    ]
                ):
                    continue
                test_item, line_warning = cls.parse_test_line(line)
                if test_item:
                    test_results.append(test_item)
                    if line_warning:
                        warnings.append(line_warning)

        if not test_results:
            warnings.append(
                "No laboratory test rows could be confidently extracted from document lines."
            )

        return ExtractedReportData(
            schema_version="1.0",
            report=ReportMetadata(
                report_id=report_id, report_date=resolved_date, lab_name=lab_name
            ),
            patient=PatientInfo(
                patient_id=resolved_patient_id,
                name=resolved_name,
                age=resolved_age,
                gender=resolved_gender,
            ),
            tests=test_results,
            warnings=warnings,
        )
