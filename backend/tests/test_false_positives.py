import pytest
from app.services.parser_service import ParserService
from app.services.normalization_service import NormalizationService


def test_false_positive_exclusion_rules():
    """
    Explicit test ensuring narrative numbers, doctor signatures, dates, IDs, and metadata are excluded from tests[].
    """
    lines = [
        "PATIENT INFORMATION",
        "Age: 63 Years",
        "Vial ID: 2950084",
        "Request No: BNG2611421",
        "Reported On: 03-Feb-2026 06:11 PM",
        "KMC.No: 103490",
        "Test Name Observed Values Units Biological Reference Intervals",
        "C-Reactive Protein 3.69 mg/L Up to 6.0",
        "INTERPRETATION:",
        "CRP is an acute phase protein. A rise in CRP may be detected within 6 hours.",
        "Dr Faeeza Begum MD, Pathologist KMC.No:103490",
        "Electronically Authenticated Page 1 of 1"
    ]

    parsed = ParserService.parse_document_text("rep_fp_test", lines)
    normalized = NormalizationService.normalize_extracted_report(parsed)

    # 1. Exactly 1 valid lab test (CRP) extracted
    assert len(normalized.tests) == 1
    assert normalized.tests[0].value == 3.69

    # 2. Verify narrative/metadata numbers are NOT extracted as tests
    extracted_test_names = [t.raw_test_name.lower() for t in normalized.tests]
    forbidden_terms = [
        "63 years",
        "2950084",
        "bng2611421",
        "03-feb-2026",
        "103490",
        "kmc.no",
        "6 hours",
        "faeeza begum",
        "pathologist",
        "page 1",
    ]
    for term in forbidden_terms:
        for name in extracted_test_names:
            assert term not in name, f"Forbidden narrative/metadata term '{term}' extracted as test: '{name}'"
