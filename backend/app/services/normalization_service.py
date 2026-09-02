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
        Transforms Phase 1 ExtractedReportData into Phase 2 NormalizedReportData (v2.0).
        """
        normalized_tests: List[NormalizedLabTestResult] = []
        warnings: List[str] = list(report_data.warnings)

        for test in report_data.tests:
            # 1. Catalog Lookup & Test Mapping
            catalog_item, mapping_status = TestMappingService.match_test(test.raw_test_name)
            
            canonical_name = catalog_item.canonical_name if catalog_item else None
            test_id = catalog_item.test_id if catalog_item else None
            # If mapping is ambiguous or review required -> loinc_code must be None
            loinc_code = catalog_item.loinc_code if (catalog_item and mapping_status == "MAPPED") else None

            # 2. Unit Normalization
            raw_unit = test.unit
            normalized_unit = ValidationService.normalize_unit(raw_unit)

            # 3. Reference Range Priority Resolution (Report Printed -> Catalog Fallback -> None)
            resolved_range, source = ReferenceRangeService.resolve_reference_range(
                report_range=test.reference_range,
                catalog_item=catalog_item,
                patient_gender=report_data.patient.gender
            )

            # 4. Numeric Value Validation
            valid_value, is_valid = ValidationService.validate_numeric_value(test.value)
            if not is_valid and test.value is not None:
                warnings.append(f"Invalid non-numeric value '{test.value}' for test '{test.raw_test_name}'.")

            # 5. Deterministic Classification
            status, flag = ClassificationService.classify_result(valid_value, resolved_range)

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
                mapping_status=mapping_status
            )
            normalized_tests.append(normalized_result)

        return NormalizedReportData(
            schema_version="2.1",
            report=report_data.report,
            patient=report_data.patient,
            tests=normalized_tests,
            warnings=warnings
        )
