from typing import List, Dict, Any, Tuple, Optional, Set
from app.schemas.normalized_lab_result import (
    NormalizedLabTestResult,
    ClinicalProfile,
    ProfileSummary,
)
from app.profiles.profile_definitions import PROFILE_DEFINITIONS, TEST_TO_PROFILES_MAP


class ProfileService:
    """
    Deterministic Clinical Profile Grouping Service.
    Organizes normalized laboratory test results into meaningful clinical profiles
    (e.g., Kidney Profile, Complete Blood Count, Liver Profile, etc.)
    """

    @classmethod
    def group_tests(
        cls, tests: List[NormalizedLabTestResult]
    ) -> Tuple[List[ClinicalProfile], List[str]]:
        """
        Groups normalized lab test results into clinical profiles.
        Returns a tuple of (active_profiles, unassigned_test_ids).
        
        Preserves original test order, supports multiple profile membership,
        avoids empty profiles, and calculates deterministic summaries.
        """
        if not tests:
            return [], []

        # Map to accumulate tests per profile code in order of definition
        # profile_code -> list of NormalizedLabTestResult
        profile_tests_map: Dict[str, List[NormalizedLabTestResult]] = {
            code: [] for code in PROFILE_DEFINITIONS
        }

        unassigned_test_ids: List[str] = []
        assigned_test_indices: Set[int] = set()

        for idx, test in enumerate(tests):
            # Identify test identifier
            raw_id = test.test_id or test.canonical_test_name or test.raw_test_name
            lookup_key = (test.test_id or "").upper().strip()

            # Find matching profile codes
            target_profile_codes = TEST_TO_PROFILES_MAP.get(lookup_key, [])

            # Fallback check if test_id wasn't matched directly but raw_test_name matches any known aliases
            if not target_profile_codes and test.raw_test_name:
                clean_name = test.raw_test_name.upper().strip()
                for code, info in PROFILE_DEFINITIONS.items():
                    for def_tid in info["tests"]:
                        if def_tid == clean_name or def_tid.replace("_", " ") in clean_name:
                            if code not in target_profile_codes:
                                target_profile_codes.append(code)

            if target_profile_codes:
                assigned_test_indices.add(idx)
                for code in target_profile_codes:
                    if code in profile_tests_map:
                        profile_tests_map[code].append(test)
            else:
                unassigned_test_ids.append(raw_id)

        # Build ClinicalProfile objects for profiles with at least 1 test
        active_profiles: List[ClinicalProfile] = []

        for code, def_info in PROFILE_DEFINITIONS.items():
            matched_tests = profile_tests_map.get(code, [])
            if not matched_tests:
                continue

            # Collect test identifiers for this profile
            profile_test_ids: List[str] = []
            for t in matched_tests:
                t_id = t.test_id or t.raw_test_name
                if t_id not in profile_test_ids:
                    profile_test_ids.append(t_id)

            # Calculate deterministic profile summary
            summary = cls._calculate_profile_summary(matched_tests)

            clinical_profile = ClinicalProfile(
                profile_code=code,
                profile_name=def_info["profile_name"],
                test_ids=profile_test_ids,
                summary=summary,
            )
            active_profiles.append(clinical_profile)

        return active_profiles, unassigned_test_ids

    @classmethod
    def _calculate_profile_summary(
        cls, tests: List[NormalizedLabTestResult]
    ) -> ProfileSummary:
        """
        Calculates profile test counts strictly derived from deterministic status and flag.
        Does not perform medical diagnosis or infer severity.
        """
        total = len(tests)
        normal = 0
        high = 0
        low = 0
        unknown = 0
        review_required = 0

        for t in tests:
            status_str = (t.status or "").upper()
            flag_str = (t.flag or "").upper()

            if status_str == "NORMAL":
                normal += 1
            elif status_str == "HIGH":
                high += 1
            elif status_str == "LOW":
                low += 1
            else:
                unknown += 1

            if flag_str == "REVIEW_REQUIRED":
                review_required += 1

        return ProfileSummary(
            total_tests=total,
            normal=normal,
            high=high,
            low=low,
            unknown=unknown,
            review_required=review_required,
        )
