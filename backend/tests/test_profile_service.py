import pytest
from app.schemas.normalized_lab_result import NormalizedLabTestResult
from app.profiles.profile_service import ProfileService

def make_test(test_id: str, raw_name: str, value: float = 10.0, status: str = "NORMAL", flag: str = "NONE", loinc: str = None, res_type: str = "DIRECT"):
    return NormalizedLabTestResult(
        test_id=test_id,
        raw_test_name=raw_name,
        test_name=raw_name,
        value=value,
        status=status,
        flag=flag,
        mapping_status="MAPPED",
        loinc_code=loinc,
        result_type=res_type,
    )

def test_empty_test_list():
    profiles, unassigned = ProfileService.group_tests([])
    assert profiles == []
    assert unassigned == []

def test_kidney_profile_assignment():
    tests = [
        make_test("CREATININE", "Creatinine", 2.62, "HIGH", "RED_FLAG"),
        make_test("UREA", "Urea", 56.50, "HIGH", "RED_FLAG"),
        make_test("BUN", "BUN", 26.40, "HIGH", "RED_FLAG"),
        make_test("BUN_CREATININE_RATIO", "BUN/Cr Ratio", 10.08, "UNKNOWN", "REVIEW_REQUIRED"),
        make_test("URIC_ACID", "Uric Acid", 4.85, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    assert unassigned == []
    p_dict = {p.profile_code: p for p in profiles}
    assert "KIDNEY_PROFILE" in p_dict
    kidney = p_dict["KIDNEY_PROFILE"]
    assert kidney.profile_name == "Kidney Profile"
    assert set(kidney.test_ids) == {"CREATININE", "UREA", "BUN", "BUN_CREATININE_RATIO", "URIC_ACID"}
    assert kidney.summary.total_tests == 5
    assert kidney.summary.normal == 1
    assert kidney.summary.high == 3
    assert kidney.summary.low == 0
    assert kidney.summary.unknown == 1
    assert kidney.summary.review_required == 1

def test_cbc_assignment():
    tests = [
        make_test("HEMOGLOBIN", "Hb", 13.5, "NORMAL", "NONE"),
        make_test("RBC", "RBC Count", 4.5, "NORMAL", "NONE"),
        make_test("WBC", "Total WBC", 7500.0, "NORMAL", "NONE"),
        make_test("PLATELETS", "Platelets", 250000.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "CBC" in p_dict
    cbc = p_dict["CBC"]
    assert cbc.profile_name == "Complete Blood Count"
    assert set(cbc.test_ids) == {"HEMOGLOBIN", "RBC", "WBC", "PLATELETS"}

def test_liver_profile_assignment():
    tests = [
        make_test("BILIRUBIN_TOTAL", "Total Bilirubin", 0.8, "NORMAL", "NONE"),
        make_test("AST", "SGOT / AST", 22.0, "NORMAL", "NONE"),
        make_test("ALT", "SGPT / ALT", 25.0, "NORMAL", "NONE"),
        make_test("ALP", "Alk Phos", 85.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "LIVER_PROFILE" in p_dict
    liver = p_dict["LIVER_PROFILE"]
    assert set(liver.test_ids) == {"BILIRUBIN_TOTAL", "AST", "ALT", "ALP"}

def test_lipid_profile_assignment():
    tests = [
        make_test("CHOLESTEROL_TOTAL", "Total Cholesterol", 180.0, "NORMAL", "NONE"),
        make_test("HDL", "HDL Cholesterol", 55.0, "NORMAL", "NONE"),
        make_test("LDL", "LDL Cholesterol", 95.0, "NORMAL", "NONE"),
        make_test("TRIGLYCERIDES", "Triglycerides", 120.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "LIPID_PROFILE" in p_dict
    lipid = p_dict["LIPID_PROFILE"]
    assert set(lipid.test_ids) == {"CHOLESTEROL_TOTAL", "HDL", "LDL", "TRIGLYCERIDES"}

def test_iron_profile_assignment():
    tests = [
        make_test("IRON", "Serum Iron", 80.0, "NORMAL", "NONE"),
        make_test("TIBC", "TIBC", 300.0, "NORMAL", "NONE"),
        make_test("FERRITIN", "Ferritin", 45.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "IRON_PROFILE" in p_dict
    iron = p_dict["IRON_PROFILE"]
    assert set(iron.test_ids) == {"IRON", "TIBC", "FERRITIN"}

def test_thyroid_profile_assignment():
    tests = [
        make_test("T3", "Total T3", 1.2, "NORMAL", "NONE"),
        make_test("T4", "Total T4", 8.0, "NORMAL", "NONE"),
        make_test("TSH", "TSH", 2.5, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "THYROID_PROFILE" in p_dict
    thyroid = p_dict["THYROID_PROFILE"]
    assert set(thyroid.test_ids) == {"T3", "T4", "TSH"}

def test_glycemic_profile_assignment():
    tests = [
        make_test("GLUCOSE_FASTING", "Fasting Glucose", 95.0, "NORMAL", "NONE"),
        make_test("HBA1C", "HbA1c", 5.4, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "GLYCEMIC_PROFILE" in p_dict
    glycemic = p_dict["GLYCEMIC_PROFILE"]
    assert set(glycemic.test_ids) == {"GLUCOSE_FASTING", "HBA1C"}

def test_vitamin_profile_assignment():
    tests = [
        make_test("VITAMIN_D", "25-OH Vitamin D", 35.0, "NORMAL", "NONE"),
        make_test("VITAMIN_B12", "Vitamin B12", 450.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "VITAMIN_PROFILE" in p_dict
    vit = p_dict["VITAMIN_PROFILE"]
    assert set(vit.test_ids) == {"VITAMIN_D", "VITAMIN_B12"}

def test_electrolyte_profile_assignment():
    tests = [
        make_test("SODIUM", "Sodium", 140.0, "NORMAL", "NONE"),
        make_test("POTASSIUM", "Potassium", 4.2, "NORMAL", "NONE"),
        make_test("CHLORIDE", "Chloride", 101.0, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "ELECTROLYTE_PROFILE" in p_dict
    elec = p_dict["ELECTROLYTE_PROFILE"]
    assert set(elec.test_ids) == {"SODIUM", "POTASSIUM", "CHLORIDE"}

def test_multiple_profile_membership():
    """Sodium and Potassium belong to both Kidney Profile and Electrolyte Profile."""
    tests = [
        make_test("SODIUM", "Sodium", 140.0, "NORMAL", "NONE"),
        make_test("POTASSIUM", "Potassium", 4.2, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_codes = {p.profile_code for p in profiles}
    assert "KIDNEY_PROFILE" in p_codes
    assert "ELECTROLYTE_PROFILE" in p_codes
    assert unassigned == []

def test_unknown_unassigned_test_preservation():
    """Unmapped or unknown test IDs are preserved in unassigned_test_ids."""
    tests = [
        make_test("SODIUM", "Sodium", 140.0, "NORMAL", "NONE"),
        make_test(None, "UNKNOWN_EXPERIMENTAL_MARKER_XYZ", 99.9, "UNKNOWN", "REVIEW_REQUIRED"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    assert len(profiles) > 0
    assert "UNKNOWN_EXPERIMENTAL_MARKER_XYZ" in unassigned

def test_duplicate_canonical_test_ids():
    """Duplicate extracted canonical test IDs in the same report are handled cleanly without breaking."""
    tests = [
        make_test("CREATININE", "Serum Creatinine", 1.0, "NORMAL", "NONE"),
        make_test("CREATININE", "Creatinine (Repeat)", 1.1, "NORMAL", "NONE"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "KIDNEY_PROFILE" in p_dict
    assert p_dict["KIDNEY_PROFILE"].summary.total_tests == 2

def test_calculated_test_preservation():
    """Calculated/derived tests (e.g. Mean Plasma Glucose) are preserved in profiles."""
    tests = [
        make_test("MEAN_PLASMA_GLUCOSE", "Approx Mean Plasma Glucose", 110.0, "NORMAL", "NONE", res_type="CALCULATED"),
    ]
    profiles, unassigned = ProfileService.group_tests(tests)
    p_dict = {p.profile_code: p for p in profiles}
    assert "GLYCEMIC_PROFILE" in p_dict

def test_raw_test_name_changes_do_not_break_grouping():
    """If raw_test_name varies ('Hb', 'Haemoglobin', 'HGB'), matching canonical test_id='HEMOGLOBIN' still groups correctly."""
    t1 = make_test("HEMOGLOBIN", "Haemoglobin Test")
    t2 = make_test("HEMOGLOBIN", "HGB (Blood)")
    profiles1, _ = ProfileService.group_tests([t1])
    profiles2, _ = ProfileService.group_tests([t2])
    assert profiles1[0].profile_code == "CBC"
    assert profiles2[0].profile_code == "CBC"

def test_loinc_and_canonical_id_grouping():
    """Verifies that LOINC code presence works alongside canonical test_id."""
    t = make_test("CREATININE", "Creatinine", 1.2, "NORMAL", "NONE", loinc="2160-0")
    profiles, _ = ProfileService.group_tests([t])
    assert len(profiles) == 1
    assert profiles[0].profile_code == "KIDNEY_PROFILE"
