from typing import Dict, Any, List


# ============================================================
# CLINICAL PROFILE DEFINITIONS
# ============================================================
#
# IMPORTANT:
# This file MUST NOT import PROFILE_DEFINITIONS or
# TEST_TO_PROFILES_MAP from itself.
#
# profile_service.py imports these definitions from this file.
# ============================================================

PROFILE_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    # ========================================================
    # COMPLETE BLOOD COUNT
    # ========================================================
    "CBC": {
        "profile_name": "Complete Blood Count",
        "tests": [
            "HEMOGLOBIN",
            "RBC",
            "WBC",
            "PLATELETS",
            "HCT",
            "MCV",
            "MCH",
            "MCHC",
            "RDW_CV",
            "RDW_SD",
            "PDW",
            "MPV",
            "P_LCR",
            "PCT",
            "NEUTROPHILS",
            "LYMPHOCYTES",
            "EOSINOPHILS",
            "BASOPHILS",
            "MONOCYTES",
            "IG",
        ],
    },
    # ========================================================
    # KIDNEY PROFILE
    # ========================================================
    "KIDNEY_PROFILE": {
        "profile_name": "Kidney Profile",
        "tests": [
            "UREA",
            "CREATININE",
            "BUN",
            "BUN_CREATININE_RATIO",
            "URIC_ACID",
            "SODIUM",
            "POTASSIUM",
            "CHLORIDE",
            "BICARBONATE",
            "EGFR",
            "CALCIUM",
        ],
    },
    # ========================================================
    # ELECTROLYTE PROFILE
    # ========================================================
    "ELECTROLYTE_PROFILE": {
        "profile_name": "Electrolyte Profile",
        "tests": [
            "SODIUM",
            "POTASSIUM",
            "CHLORIDE",
            "BICARBONATE",
        ],
    },
    # ========================================================
    # LIVER PROFILE
    # ========================================================
    "LIVER_PROFILE": {
        "profile_name": "Liver Profile",
        "tests": [
            "BILIRUBIN_TOTAL",
            "BILIRUBIN_DIRECT",
            "BILIRUBIN_INDIRECT",
            "AST",
            "ALT",
            "ALP",
            "TOTAL_PROTEIN",
            "ALBUMIN",
            "GLOBULIN",
            "AG_RATIO",
            "GGT",
        ],
    },
    # ========================================================
    # LIPID PROFILE
    # ========================================================
    "LIPID_PROFILE": {
        "profile_name": "Lipid Profile",
        "tests": [
            "CHOLESTEROL_TOTAL",
            "HDL",
            "LDL",
            "TRIGLYCERIDES",
            "VLDL",
        ],
    },
    # ========================================================
    # IRON PROFILE
    # ========================================================
    "IRON_PROFILE": {
        "profile_name": "Iron Profile",
        "tests": [
            "IRON",
            "TIBC",
            "UIBC",
            "TRANSFERRIN",
            "TRANSFERRIN_SATURATION",
            "FERRITIN",
        ],
    },
    # ========================================================
    # THYROID PROFILE
    # ========================================================
    "THYROID_PROFILE": {
        "profile_name": "Thyroid Profile",
        "tests": [
            "T3",
            "T4",
            "TSH",
            "FREE_T3",
            "FREE_T4",
        ],
    },
    # ========================================================
    # GLYCEMIC / DIABETES PROFILE
    # ========================================================
    "GLYCEMIC_PROFILE": {
        "profile_name": "Diabetes / Glycemic Profile",
        "tests": [
            "GLUCOSE_RANDOM",
            "GLUCOSE_FASTING",
            "HBA1C",
            "HBA1C_IFCC",
            "MEAN_PLASMA_GLUCOSE",
            "AVERAGE_GLUCOSE",
        ],
    },
    # ========================================================
    # VITAMIN PROFILE
    # ========================================================
    "VITAMIN_PROFILE": {
        "profile_name": "Vitamin Profile",
        "tests": [
            "VITAMIN_D",
            "VITAMIN_B12",
            "FOLATE",
        ],
    },
    # ========================================================
    # CALCIUM / BONE PROFILE
    # ========================================================
    "CALCIUM_BONE_PROFILE": {
        "profile_name": "Calcium / Bone Profile",
        "tests": [
            "CALCIUM",
            "PHOSPHORUS",
            "VITAMIN_D",
        ],
    },
    # ========================================================
    # INFLAMMATORY MARKERS
    # ========================================================
    "INFLAMMATORY_MARKERS": {
        "profile_name": "Inflammatory Markers",
        "tests": [
            "CRP",
            "HS_CRP",
            "PROCALCITONIN",
        ],
    },
    # ========================================================
    # MUSCLE ENZYMES
    # ========================================================
    "MUSCLE_ENZYMES": {
        "profile_name": "Muscle Enzymes",
        "tests": [
            "CPK",
            "CK",
            "LDH",
        ],
    },
    # ========================================================
    # CARDIOVASCULAR MARKERS
    # ========================================================
    "CARDIOVASCULAR_MARKERS": {
        "profile_name": "Cardiovascular Markers",
        "tests": [
            "APOLIPOPROTEIN_A1",
            "APOLIPOPROTEIN_B",
            "APO_B_APO_A1_RATIO",
        ],
    },
    # ========================================================
    # AUTOIMMUNE MARKERS
    # ========================================================
    "AUTOIMMUNE_MARKERS": {
        "profile_name": "Autoimmune Markers",
        "tests": [
            "RHEUMATOID_FACTOR",
            "RF",
        ],
    },
    # ========================================================
    # INFECTIOUS DISEASE MARKERS
    # ========================================================
    "INFECTIOUS_DISEASE_MARKERS": {
        "profile_name": "Infectious Disease Markers",
        "tests": [
            "HBSAG",
            "HBsAG",
            "HEPATITIS_B_SURFACE_ANTIGEN",
        ],
    },
    # ========================================================
    # URINE ROUTINE / MICROSCOPY
    # ========================================================
    "URINE_ROUTINE": {
        "profile_name": "Urine Routine / Microscopy",
        "tests": [
            "URINE_PH",
            "URINE_SPECIFIC_GRAVITY",
            "URINE_PROTEIN",
            "URINE_GLUCOSE",
            "URINE_KETONES",
            "URINE_BILIRUBIN",
            "URINE_UROBILINOGEN",
            "URINE_BLOOD",
            "URINE_NITRITE",
            "URINE_LEUKOCYTE_ESTERASE",
            "URINE_RBC",
            "URINE_WBC",
            "URINE_EPITHELIAL_CELLS",
            "URINE_CASTS",
            "URINE_CRYSTALS",
            "URINE_BACTERIA",
        ],
    },
    # ========================================================
    # ALLERGY PROFILE
    # ========================================================
    "ALLERGY_PROFILE": {
        "profile_name": "Allergy Profile",
        "tests": [
            "TOTAL_IGE",
            "IGE",
            "ALLERGY_SCREEN",
        ],
    },
}


# ============================================================
# TEST -> PROFILE REVERSE MAP
# ============================================================
#
# Example:
#
# "SODIUM" ->
# [
#     "KIDNEY_PROFILE",
#     "ELECTROLYTE_PROFILE"
# ]
#
# This allows a single laboratory test to belong to multiple
# clinical profiles.
# ============================================================

TEST_TO_PROFILES_MAP: Dict[str, List[str]] = {}


for profile_code, profile_info in PROFILE_DEFINITIONS.items():

    tests = profile_info.get("tests", [])

    for test_id in tests:

        normalized_test_id = str(test_id).strip().upper()

        if not normalized_test_id:
            continue

        if normalized_test_id not in TEST_TO_PROFILES_MAP:
            TEST_TO_PROFILES_MAP[normalized_test_id] = []

        if profile_code not in TEST_TO_PROFILES_MAP[normalized_test_id]:
            TEST_TO_PROFILES_MAP[normalized_test_id].append(profile_code)


# ============================================================
# OPTIONAL EXPORTS
# ============================================================

__all__ = [
    "PROFILE_DEFINITIONS",
    "TEST_TO_PROFILES_MAP",
]
