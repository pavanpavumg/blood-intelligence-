import re

from typing import List

from app.schemas.report import ExtractedReportData

from app.schemas.normalized_lab_result import (
    NormalizedLabTestResult,
    NormalizedReportData,
)

from app.services.test_mapping_service import (
    TestMappingService,
)

from app.services.reference_range_service import (
    ReferenceRangeService,
)

from app.services.validation_service import (
    ValidationService,
)

from app.services.classification_service import (
    ClassificationService,
)

from app.profiles.profile_service import (
    ProfileService,
)

from app.core.logging import logger


class NormalizationService:
    """
    Converts extracted laboratory rows into normalized results.

    Important:
    Validation does NOT remove extracted tests.

    Completeness is not inferred from extracted_count.
    """

    @classmethod
    def normalize_test_name(
        cls,
        raw_name: str,
    ) -> str:

        if not raw_name:
            return raw_name

        # M C H C -> MCHC
        return re.sub(
            r"\b[A-Z]" r"(?:\s+[A-Z])+\b",
            lambda match: match.group(0).replace(
                " ",
                "",
            ),
            raw_name,
        )

    @classmethod
    def normalize_extracted_report(
        cls,
        report_data: ExtractedReportData,
    ) -> NormalizedReportData:

        normalized_tests: List[NormalizedLabTestResult] = []

        warnings: List[str] = list(report_data.warnings)

        seen_test_ids = {}

        # ---------------------------------------------------------
        # 1. Normalize every extracted row
        # ---------------------------------------------------------

        for test in report_data.tests:

            # -----------------------------------------------------
            # Mapping
            # -----------------------------------------------------

            catalog_item, mapping_status = TestMappingService.match_test(
                test.raw_test_name,
                unit=test.unit,
            )

            canonical_name = catalog_item.canonical_name if catalog_item else None

            test_id = catalog_item.test_id if catalog_item else None

            loinc_code = (
                catalog_item.loinc_code
                if (catalog_item and mapping_status == "MAPPED")
                else None
            )

            # -----------------------------------------------------
            # Review reasons
            # -----------------------------------------------------

            review_reasons = list(
                getattr(
                    test,
                    "review_reasons",
                    [],
                )
                or []
            )

            if mapping_status == "REVIEW_REQUIRED":

                if "UNMAPPED_TEST" not in review_reasons:

                    review_reasons.append("UNMAPPED_TEST")

            # -----------------------------------------------------
            # Unit validation
            # -----------------------------------------------------

            normalized_unit, unit_status, unit_reasons = (
                ValidationService.validate_unit_for_test(
                    test_id,
                    test.unit,
                )
            )

            for reason in unit_reasons:

                if reason not in review_reasons:
                    review_reasons.append(reason)

            if unit_status == "SUSPECT":

                if "SUSPECT_UNIT" not in review_reasons:

                    review_reasons.append("SUSPECT_UNIT")

            # -----------------------------------------------------
            # Numeric validation
            # -----------------------------------------------------

            valid_value, is_valid = ValidationService.validate_numeric_value(test.value)

            if test.value is not None and not is_valid:

                warnings.append(
                    "Invalid non-numeric "
                    f"value '{test.value}' "
                    f"for test "
                    f"'{test.raw_test_name}'."
                )

            # -----------------------------------------------------
            # Reference range
            # -----------------------------------------------------

            resolved_range, range_source = (
                ReferenceRangeService.resolve_reference_range(
                    report_range=test.reference_range,
                    catalog_item=catalog_item,
                    patient_gender=(report_data.patient.gender),
                    test_value=valid_value,
                )
            )

            # -----------------------------------------------------
            # Demographic / pregnancy checks
            # -----------------------------------------------------

            if resolved_range:

                if (
                    resolved_range.type == "DEMOGRAPHIC"
                    and not resolved_range.selected_group
                ):

                    if "DEMOGRAPHIC_RANGE_UNRESOLVED" not in review_reasons:

                        review_reasons.append("DEMOGRAPHIC_RANGE_UNRESOLVED")

                    mapping_status = "REVIEW_REQUIRED"

                elif (
                    resolved_range.type == "PREGNANCY"
                    and not resolved_range.selected_group
                ):

                    if "PREGNANCY_RANGE_UNRESOLVED" not in review_reasons:

                        review_reasons.append("PREGNANCY_RANGE_UNRESOLVED")

                    mapping_status = "REVIEW_REQUIRED"

            # -----------------------------------------------------
            # Duplicate detection
            # -----------------------------------------------------

            if test_id:

                if test_id in seen_test_ids:

                    if "DUPLICATE_TEST" not in review_reasons:

                        review_reasons.append("DUPLICATE_TEST")

                else:

                    seen_test_ids[test_id] = True

            # -----------------------------------------------------
            # Classification
            # -----------------------------------------------------

            if test_id in ("CHOL_HDL_RATIO", "LDL_HDL_RATIO"):
                status = "REPORTED"
                flag = "NONE"
            elif test.status:
                status = test.status
                flag = test.flag or "NONE"
            else:
                status, flag = ClassificationService.classify_result(
                    valid_value,
                    resolved_range,
                )

            # -----------------------------------------------------
            # Result type
            # -----------------------------------------------------

            raw_name_lower = test.raw_test_name.lower() if test.raw_test_name else ""

            result_type = (
                "CALCULATED" if raw_name_lower.startswith("approx") else "DIRECT"
            )

            # -----------------------------------------------------
            # Normalized result
            # -----------------------------------------------------

            normalized_result = NormalizedLabTestResult(
                test_name=(cls.normalize_test_name(test.raw_test_name)),
                raw_test_name=(test.raw_test_name),
                canonical_test_name=(canonical_name),
                test_id=test_id,
                loinc_code=loinc_code,
                value=valid_value,
                raw_unit=test.unit,
                normalized_unit=(normalized_unit),
                reference_range=(resolved_range),
                status=status,
                flag=flag,
                mapping_status=(mapping_status),
                method=test.method,
                unit_validation=(unit_status),
                review_reasons=(review_reasons),
                source_trace={
                    "raw_test_name": test.raw_test_name,
                    "raw_value": test.raw_value,
                },
                result_type=result_type,
            )

            normalized_tests.append(normalized_result)

        # ---------------------------------------------------------
        # 2. LOINC conflict detection
        # ---------------------------------------------------------

        loinc_map = {}

        for test in normalized_tests:

            if test.loinc_code and test.test_id:

                previous = loinc_map.get(test.loinc_code)

                if previous and previous != test.test_id:

                    test.loinc_code = None

                    test.mapping_status = "REVIEW_REQUIRED"

                    if "LOINC_MAPPING_CONFLICT" not in test.review_reasons:

                        test.review_reasons.append("LOINC_MAPPING_CONFLICT")

                else:

                    loinc_map[test.loinc_code] = test.test_id

        # ---------------------------------------------------------
        # 3. Diagnostics
        # ---------------------------------------------------------

        mapped_count = sum(1 for test in normalized_tests if test.test_id)

        review_count = sum(
            1 for test in normalized_tests if test.mapping_status == "REVIEW_REQUIRED"
        )

        logger.info(
            "NORMALIZATION_RESULT "
            "report_id=%s "
            "input_tests=%d "
            "normalized_tests=%d "
            "mapped_tests=%d "
            "review_required=%d",
            report_data.report.report_id,
            len(report_data.tests),
            len(normalized_tests),
            mapped_count,
            review_count,
        )

        logger.info(
            "NORMALIZED_TESTS report_id=%s tests=%s",
            report_data.report.report_id,
            [
                {
                    "raw": test.raw_test_name,
                    "test_id": test.test_id,
                    "mapping": test.mapping_status,
                    "value": test.value,
                }
                for test in normalized_tests
            ],
        )

        # ---------------------------------------------------------
        # 4. Completeness
        # ---------------------------------------------------------
        #
        # IMPORTANT:
        #
        # Do NOT do:
        #
        # expected_count = extracted_count
        #
        # because that makes:
        #
        # 2 extracted -> 2 expected -> complete=True
        #
        # There is currently no reliable expected analyte count
        # supplied by the parser.
        #
        # Therefore an extraction containing tests is considered
        # "extracted", but NOT automatically "complete".
        # ---------------------------------------------------------

        extracted_count = len(normalized_tests)

        expected_count = None

        completeness_complete = False

        if extracted_count == 0:

            completeness_complete = False

            no_test_warning = (
                "NO_TESTS_EXTRACTED: "
                "No laboratory test rows "
                "could be extracted from "
                "report."
            )

            if no_test_warning not in warnings:

                warnings.append(no_test_warning)

        else:

            warnings.append(
                "COMPLETENESS_NOT_VERIFIED: "
                "Expected analyte count is "
                "not available; report cannot "
                "be declared complete solely "
                "from extracted test count."
            )

        completeness_info = {
            "expected_count": expected_count,
            "extracted_count": extracted_count,
            "missing_tests": [],
            "unexpected_tests": [],
            "complete": completeness_complete,
        }

        # ---------------------------------------------------------
        # 5. Profiles
        # ---------------------------------------------------------

        profiles, unassigned_test_ids = ProfileService.group_tests(normalized_tests)

        # ---------------------------------------------------------
        # 6. Final response
        # ---------------------------------------------------------

        return NormalizedReportData(
            schema_version="2.1",
            report=report_data.report,
            patient=report_data.patient,
            tests=normalized_tests,
            profiles=profiles,
            unassigned_test_ids=(unassigned_test_ids),
            warnings=warnings,
            completeness=(completeness_info),
        )
