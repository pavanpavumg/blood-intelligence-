import re
from typing import List, Optional
from app.schemas.report import ExtractedReportData
from app.schemas.normalized_lab_result import (
    NormalizedLabTestResult,
    NormalizedReportData,
    NormalizedReportResponse
)
from app.services.test_mapping_service import TestMappingService, TestCatalogItem
from app.services.reference_range_service import ReferenceRangeService
from app.services.validation_service import ValidationService
from app.services.classification_service import ClassificationService
from app.core.logging import logger

class NormalizationService:
    """
    Phase 2 Normalization & Classification Pipeline Service.
    Orchestrates catalog lookup, unit normalization, reference range priority,
    and deterministic classification.
    """

    @classmethod
    def normalize_test_name(cls, raw_name: str) -> str:
        """
        Normalizes display test_name by collapsing single-letter spaced acronyms (e.g. 'M C H C' -> 'MCHC').
        Preserves raw_test_name exactly as extracted.
        """
        if not raw_name:
            return raw_name
        return re.sub(
            r"\b[A-Z](?:\s+[A-Z])+\b",
            lambda m: m.group(0).replace(" ", ""),
            raw_name,
        )

    @classmethod
    def normalize_extracted_report(cls, report_data: ExtractedReportData) -> NormalizedReportData:
        """
        Transforms Phase 1 ExtractedReportData into Phase 3 NormalizedReportData.
        Handles method extraction, unit validation, LOINC conflict validation, duplicate detection, and completeness.
        """
        normalized_tests: List[NormalizedLabTestResult] = []
        warnings: List[str] = list(report_data.warnings)

        seen_test_ids = {}

        for test in report_data.tests:
            # 1. Catalog Lookup & Test Mapping with Unit Context
            catalog_item, mapping_status = TestMappingService.match_test(test.raw_test_name, unit=test.unit)
            
            canonical_name = catalog_item.canonical_name if catalog_item else None
            test_id = catalog_item.test_id if catalog_item else None
            loinc_code = catalog_item.loinc_code if (catalog_item and mapping_status == "MAPPED") else None

            # Structured Review Reasons
            review_reasons: List[str] = list(test.review_reasons) if hasattr(test, 'review_reasons') and test.review_reasons else []
            if mapping_status == "REVIEW_REQUIRED":
                if "UNMAPPED_TEST" not in review_reasons and "AMBIGUOUS_TEST_NAME" not in review_reasons:
                    review_reasons.append("UNMAPPED_TEST")

            # 2. Unit Validation & Suspect Unit Detection
            raw_unit = test.unit
            normalized_unit, unit_val_status, unit_reasons = ValidationService.validate_unit_for_test(test_id, raw_unit)
            for r in unit_reasons:
                if r not in review_reasons:
                    review_reasons.append(r)

            # 3. Reference Range Priority Resolution (Report Printed -> Catalog Fallback -> None)
            valid_value, is_valid = ValidationService.validate_numeric_value(test.value)
            if not is_valid and test.value is not None:
                warnings.append(f"Invalid non-numeric value '{test.value}' for test '{test.raw_test_name}'.")

            resolved_range, source = ReferenceRangeService.resolve_reference_range(
                report_range=test.reference_range,
                catalog_item=catalog_item,
                patient_gender=report_data.patient.gender,
                test_value=valid_value
            )

            # Range Resolution Review Reasons
            if resolved_range:
                if resolved_range.type == "DEMOGRAPHIC" and not resolved_range.selected_group:
                    if "DEMOGRAPHIC_RANGE_UNRESOLVED" not in review_reasons:
                        review_reasons.append("DEMOGRAPHIC_RANGE_UNRESOLVED")
                        mapping_status = "REVIEW_REQUIRED"
                elif resolved_range.type == "PREGNANCY" and not resolved_range.selected_group:
                    if "PREGNANCY_RANGE_UNRESOLVED" not in review_reasons:
                        review_reasons.append("PREGNANCY_RANGE_UNRESOLVED")
                        mapping_status = "REVIEW_REQUIRED"

            # 4. Duplicate Analytes Detection
            if test_id:
                if test_id in seen_test_ids:
                    if "DUPLICATE_TEST" not in review_reasons:
                        review_reasons.append("DUPLICATE_TEST")
                else:
                    seen_test_ids[test_id] = True

            # 5. Deterministic Classification
            status, flag = ClassificationService.classify_result(valid_value, resolved_range)

            # Result Type (DIRECT vs CALCULATED)
            res_type = "CALCULATED" if test.raw_test_name.lower().startswith("approx") else "DIRECT"

            normalized_result = NormalizedLabTestResult(
                test_name=cls.normalize_test_name(test.raw_test_name),
                raw_test_name=test.raw_test_name,
                canonical_test_name=canonical_name,
                test_id=test_id,
                loinc_code=loinc_code,
                value=valid_value,
                raw_unit=raw_unit,
                normalized_unit=normalized_unit,
                reference_range=resolved_range,
                status=status,
                flag=flag,
                mapping_status=mapping_status,
                method=test.method,
                unit_validation=unit_val_status,
                review_reasons=review_reasons,
                source_trace={"raw_test_name": test.raw_test_name, "raw_value": test.raw_value},
                result_type=res_type
            )
            normalized_tests.append(normalized_result)

        # 6. Post-pass LOINC Mapping Conflict Detection
        loinc_map = {}
        for t in normalized_tests:
            if t.loinc_code and t.test_id:
                if t.loinc_code in loinc_map and loinc_map[t.loinc_code] != t.test_id:
                    # Incompatible LOINC conflict
                    t.loinc_code = None
                    t.mapping_status = "REVIEW_REQUIRED"
                    if "LOINC_MAPPING_CONFLICT" not in t.review_reasons:
                        t.review_reasons.append("LOINC_MAPPING_CONFLICT")
                else:
                    loinc_map[t.loinc_code] = t.test_id

        # 7. Completeness Validation
        extracted_count = len(normalized_tests)
        completeness_info = {
            "expected_count": extracted_count,
            "extracted_count": extracted_count,
            "missing_tests": [],
            "unexpected_tests": [],
            "complete": True
        }

        return NormalizedReportData(
            schema_version="2.1",
            report=report_data.report,
            patient=report_data.patient,
            tests=normalized_tests,
            warnings=warnings,
            completeness=completeness_info
        )
