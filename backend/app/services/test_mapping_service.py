import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from app.schemas.lab_result import ReferenceRange

@dataclass
class TestCatalogItem:
    test_id: str
    canonical_name: str
    aliases: List[str]
    loinc_code: Optional[str]
    category: str
    default_unit: str
    default_reference_range: Optional[ReferenceRange]
    active: bool = True

class TestMappingService:
    """
    Test Catalog and Mapping Service. Matches raw extracted test names to canonical test IDs
    and LOINC codes using deterministic alias lookup.
    """

    CATALOG: List[TestCatalogItem] = [
        TestCatalogItem(
            test_id="GLUCOSE_FASTING",
            canonical_name="Fasting Blood Glucose",
            aliases=["fasting blood glucose", "fasting glucose", "fbs", "fasting blood sugar", "glucose, fasting"],
            loinc_code="1558-6",
            category="Metabolic",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=70.0, high=99.0, raw="70 - 99 mg/dL")
        ),
        TestCatalogItem(
            test_id="HBA1C",
            canonical_name="Hemoglobin A1c",
            aliases=["hemoglobin a1c", "hba1c", "glycated hemoglobin", "a1c", "hb a1c", "glycated hemoglobin (hba1c)"],
            loinc_code="4548-4",
            category="Glycemic Control",
            default_unit="%",
            default_reference_range=ReferenceRange(low=4.0, high=5.6, raw="4.0 - 5.6 %")
        ),
        TestCatalogItem(
            test_id="CREATININE",
            canonical_name="Serum Creatinine",
            aliases=["serum creatinine", "creatinine", "creat"],
            loinc_code="2160-0",
            category="Renal",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=0.7, high=1.3, raw="0.7 - 1.3 mg/dL")
        ),
        TestCatalogItem(
            test_id="HEMOGLOBIN",
            canonical_name="Hemoglobin",
            aliases=["hemoglobin", "haemoglobin", "hgb", "hb", "hgb (hemoglobin)"],
            loinc_code="718-7",
            category="Hematology",
            default_unit="g/dL",
            default_reference_range=ReferenceRange(low=13.5, high=17.5, raw="13.5 - 17.5 g/dL")
        ),
        TestCatalogItem(
            test_id="WBC",
            canonical_name="White Blood Cell Count",
            aliases=["wbc", "white blood cell count", "total wbc count", "leukocytes"],
            loinc_code="6690-2",
            category="Hematology",
            default_unit="10^3/uL",
            default_reference_range=ReferenceRange(low=4.0, high=10.0, raw="4.0 - 10.0 10^3/uL")
        ),
        TestCatalogItem(
            test_id="RBC",
            canonical_name="Red Blood Cell Count",
            aliases=["rbc count", "total rbc count", "rbc count (electrical impedence)", "rbc", "red blood cell count"],
            loinc_code="789-8",
            category="Hematology",
            default_unit="10^6/uL",
            default_reference_range=ReferenceRange(low=3.8, high=6.5, raw="3.8 - 6.5 10^6/uL")
        ),
        TestCatalogItem(
            test_id="HCT",
            canonical_name="Hematocrit",
            aliases=["hct", "hematocrit", "packed cell volume (pcv)", "packed cell volume", "pcv"],
            loinc_code="4544-3",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=37.0, high=54.0, raw="37 - 54 %")
        ),
        TestCatalogItem(
            test_id="MCV",
            canonical_name="Mean Corpuscular Volume",
            aliases=["mean corpuscular volume (mcv)", "mean corpuscular vol(mcv)", "mean corpuscular volume", "mcv"],
            loinc_code="787-2",
            category="Hematology",
            default_unit="fL",
            default_reference_range=ReferenceRange(low=80.0, high=100.0, raw="80 - 100 fL")
        ),
        TestCatalogItem(
            test_id="MCH",
            canonical_name="Mean Corpuscular Hemoglobin",
            aliases=["mean corpuscular hb. (mch)", "mean corpuscular hb.(mch)", "mean corpuscular hb.", "mean corpuscular hb", "mean corpuscular hemoglobin", "mch"],
            loinc_code="785-6",
            category="Hematology",
            default_unit="pg",
            default_reference_range=ReferenceRange(low=27.0, high=32.0, raw="27 - 32 pg")
        ),
        TestCatalogItem(
            test_id="MCHC",
            canonical_name="Mean Corpuscular Hemoglobin Concentration",
            aliases=["mean corp.hb.con. (mchc)", "mean corpuscular hemoglobin concentration", "mchc"],
            loinc_code="786-4",
            category="Hematology",
            default_unit="g/dL",
            default_reference_range=ReferenceRange(low=32.0, high=36.0, raw="32 - 36 g/dL")
        ),
        TestCatalogItem(
            test_id="PLATELETS",
            canonical_name="Platelet Count",
            aliases=["platelet count", "platelet count (electrical impedence)", "platelets", "plt"],
            loinc_code="777-3",
            category="Hematology",
            default_unit="10^3/uL",
            default_reference_range=ReferenceRange(low=150.0, high=500.0, raw="150 - 500 10^3/uL")
        ),
        TestCatalogItem(
            test_id="RDW_SD",
            canonical_name="Red Cell Distribution Width SD",
            aliases=["rdw-sd", "rdw sd"],
            loinc_code="21000-5",
            category="Hematology",
            default_unit="fL",
            default_reference_range=ReferenceRange(low=40.0, high=55.0, raw="40.0 - 55.0 fL")
        ),
        TestCatalogItem(
            test_id="RDW_CV",
            canonical_name="Red Cell Distribution Width CV",
            aliases=["rdw-cv", "rdw cv", "rdw"],
            loinc_code="788-0",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=11.0, high=15.0, raw="11.0 - 15.0 %")
        ),
        TestCatalogItem(
            test_id="PDW",
            canonical_name="Platelet Distribution Width",
            aliases=["pdw", "platelet distribution width", "platelet distribution width (pdw)"],
            loinc_code=None,
            category="Hematology",
            default_unit="fL",
            default_reference_range=ReferenceRange(low=11.0, high=22.0, raw="11 - 22 fL")
        ),
        TestCatalogItem(
            test_id="MPV",
            canonical_name="Mean Platelet Volume",
            aliases=["mpv", "mean platelet volume"],
            loinc_code="32623-1",
            category="Hematology",
            default_unit="fL",
            default_reference_range=ReferenceRange(low=6.0, high=11.0, raw="6.0 - 11.0 fL")
        ),
        TestCatalogItem(
            test_id="P_LCR",
            canonical_name="Platelet Large Cell Ratio",
            aliases=["p-lcr", "plcr"],
            loinc_code="55864-3",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=15.0, high=35.0, raw="15 - 35 %")
        ),
        TestCatalogItem(
            test_id="PCT",
            canonical_name="Plateletcrit",
            aliases=["pct", "plateletcrit"],
            loinc_code="32623-1",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=0.1, high=0.5, raw="0.1 - 0.5 %")
        ),
        TestCatalogItem(
            test_id="NEUTROPHILS",
            canonical_name="Neutrophils Percentage",
            aliases=["neutrophils", "neutrophil %"],
            loinc_code="770-8",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=40.0, high=80.0, raw="40 - 80 %")
        ),
        TestCatalogItem(
            test_id="LYMPHOCYTES",
            canonical_name="Lymphocytes Percentage",
            aliases=["lymphocytes", "lymphocyte %"],
            loinc_code="736-9",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=20.0, high=40.0, raw="20 - 40 %")
        ),
        TestCatalogItem(
            test_id="EOSINOPHILS",
            canonical_name="Eosinophils Percentage",
            aliases=["eosinophils", "eosinophil %"],
            loinc_code="713-8",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=1.0, high=6.0, raw="1 - 6 %")
        ),
        TestCatalogItem(
            test_id="BASOPHILS",
            canonical_name="Basophils Percentage",
            aliases=["basophils", "basophil %"],
            loinc_code="706-2",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=0.0, high=1.0, raw="0 - 1 %")
        ),
        TestCatalogItem(
            test_id="MONOCYTES",
            canonical_name="Monocytes Percentage",
            aliases=["monocytes", "monocyte %"],
            loinc_code="5905-5",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=2.0, high=10.0, raw="2 - 10 %")
        ),
        TestCatalogItem(
            test_id="IG",
            canonical_name="Immature Granulocytes Percentage",
            aliases=["ig", "immature granulocytes"],
            loinc_code="53115-2",
            category="Hematology",
            default_unit="%",
            default_reference_range=ReferenceRange(low=0.0, high=0.5, raw="0 - 0.5 %")
        ),
        TestCatalogItem(
            test_id="CHOLESTEROL_TOTAL",
            canonical_name="Total Cholesterol",
            aliases=["total cholesterol", "cholesterol, total", "cholesterol"],
            loinc_code="2093-3",
            category="Lipids",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=None, high=200.0, raw="< 200 mg/dL")
        ),
        TestCatalogItem(
            test_id="TSH",
            canonical_name="Thyroid Stimulating Hormone",
            aliases=["thyroid stimulating hormone", "tsh", "thyrotropin"],
            loinc_code="11580-8",
            category="Endocrine",
            default_unit="uIU/mL",
            default_reference_range=ReferenceRange(low=0.45, high=4.5, raw="0.45 - 4.5 uIU/mL")
        ),
        TestCatalogItem(
            test_id="HDL",
            canonical_name="HDL Cholesterol",
            aliases=["hdl cholesterol", "hdl", "hdl-c"],
            loinc_code="2085-9",
            category="Lipids",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=40.0, high=None, raw="> 40 mg/dL")
        ),
        TestCatalogItem(
            test_id="LDL",
            canonical_name="LDL Cholesterol",
            aliases=["ldl cholesterol", "ldl", "ldl-c"],
            loinc_code="2089-1",
            category="Lipids",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=None, high=100.0, raw="< 100 mg/dL")
        ),
        TestCatalogItem(
            test_id="TRIGLYCERIDES",
            canonical_name="Triglycerides",
            aliases=["triglycerides", "trigs"],
            loinc_code="2571-8",
            category="Lipids",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=None, high=150.0, raw="< 150 mg/dL")
        ),
        TestCatalogItem(
            test_id="CRP",
            canonical_name="C-Reactive Protein",
            aliases=["c-reactive protein (crp)", "c-reactive protein", "c-reactive protien(crp)", "c-reactive protien", "crp"],
            loinc_code="1988-5",
            category="Inflammation",
            default_unit="mg/L",
            default_reference_range=ReferenceRange(low=None, high=6.0, raw="Up to 6.0 mg/L")
        ),
        TestCatalogItem(
            test_id="UREA",
            canonical_name="Serum Urea",
            aliases=["urea", "serum urea"],
            loinc_code="3091-6",
            category="Renal",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=16.8, high=43.2, raw="16.8 - 43.2 mg/dL")
        ),
        TestCatalogItem(
            test_id="BUN",
            canonical_name="Urea Nitrogen (BUN)",
            aliases=["urea nitrogen (bun)", "blood urea nitrogen", "bun", "urea nitrogen"],
            loinc_code="3094-0",
            category="Renal",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=8.0, high=23.0, raw="8 - 23 mg/dL")
        ),
        TestCatalogItem(
            test_id="BUN_CREATININE_RATIO",
            canonical_name="BUN/Creatinine Ratio",
            aliases=["bun/creatinine ratio", "bun / creatinine ratio", "bun:creatinine ratio", "bun/cr ratio", "bun / cr ratio", "bun:cr ratio"],
            loinc_code="3097-3",
            category="Renal",
            default_unit="",
            default_reference_range=None
        ),
        TestCatalogItem(
            test_id="URIC_ACID",
            canonical_name="Uric Acid",
            aliases=["uric acid", "serum uric acid"],
            loinc_code="3084-1",
            category="Metabolic",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=2.3, high=6.1, raw="Female:2.3 - 6.1 mg/dL")
        ),
        TestCatalogItem(
            test_id="SODIUM",
            canonical_name="Serum Sodium",
            aliases=["sodium", "serum sodium", "na"],
            loinc_code="2951-2",
            category="Electrolytes",
            default_unit="mmol/L",
            default_reference_range=ReferenceRange(low=136.0, high=145.0, raw="136 - 145 mmol/L")
        ),
        TestCatalogItem(
            test_id="POTASSIUM",
            canonical_name="Serum Potassium",
            aliases=["potassium", "serum potassium", "k"],
            loinc_code="2823-3",
            category="Electrolytes",
            default_unit="mmol/L",
            default_reference_range=ReferenceRange(low=3.5, high=5.5, raw="3.5 - 5.5 mmol/L")
        ),
        TestCatalogItem(
            test_id="CHLORIDE",
            canonical_name="Serum Chloride",
            aliases=["chloride", "serum chloride", "cl"],
            loinc_code="2075-0",
            category="Electrolytes",
            default_unit="mmol/L",
            default_reference_range=ReferenceRange(low=95.0, high=105.0, raw="95 - 105 mmol/L")
        ),
        TestCatalogItem(
            test_id="BILIRUBIN_TOTAL",
            canonical_name="Total Bilirubin",
            aliases=["total bilirubin", "bilirubin total", "bilirubin (total)", "bilirubin - total"],
            loinc_code="1975-2",
            category="Liver",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=0.2, high=1.2, raw="0.2 - 1.2 mg/dL")
        ),
        TestCatalogItem(
            test_id="BILIRUBIN_DIRECT",
            canonical_name="Direct Bilirubin",
            aliases=["direct bilirubin", "bilirubin direct", "bilirubin (direct)", "conjugated bilirubin"],
            loinc_code="1968-7",
            category="Liver",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=0.0, high=0.3, raw="0.0 - 0.3 mg/dL")
        ),
        TestCatalogItem(
            test_id="BILIRUBIN_INDIRECT",
            canonical_name="Indirect Bilirubin",
            aliases=["indirect bilirubin", "bilirubin indirect", "unconjugated bilirubin"],
            loinc_code="1971-1",
            category="Liver",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=0.1, high=0.8, raw="0.1 - 0.8 mg/dL")
        ),
        TestCatalogItem(
            test_id="AST",
            canonical_name="AST (SGOT)",
            aliases=["ast (sgot)", "ast / sgot", "ast", "sgot", "aspartate aminotransferase"],
            loinc_code="1920-8",
            category="Liver",
            default_unit="U/L",
            default_reference_range=ReferenceRange(low=0.0, high=35.0, raw="0 - 35 U/L")
        ),
        TestCatalogItem(
            test_id="ALT",
            canonical_name="ALT (SGPT)",
            aliases=["alt (sgpt)", "alt / sgpt", "alt", "sgpt", "alanine aminotransferase"],
            loinc_code="1742-6",
            category="Liver",
            default_unit="U/L",
            default_reference_range=ReferenceRange(low=0.0, high=45.0, raw="0 - 45 U/L")
        ),
        TestCatalogItem(
            test_id="ALP",
            canonical_name="Alkaline Phosphatase",
            aliases=["alkaline phosphatase", "alp"],
            loinc_code="6768-6",
            category="Liver",
            default_unit="U/L",
            default_reference_range=ReferenceRange(low=30.0, high=120.0, raw="30 - 120 U/L")
        ),
        TestCatalogItem(
            test_id="TOTAL_PROTEIN",
            canonical_name="Total Protein",
            aliases=["total protein", "protein, total", "protein (total)"],
            loinc_code="2885-2",
            category="Liver",
            default_unit="g/dL",
            default_reference_range=ReferenceRange(low=6.0, high=8.3, raw="6.0 - 8.3 g/dL")
        ),
        TestCatalogItem(
            test_id="ALBUMIN",
            canonical_name="Albumin",
            aliases=["albumin", "serum albumin"],
            loinc_code="1751-8",
            category="Liver",
            default_unit="g/dL",
            default_reference_range=ReferenceRange(low=3.5, high=5.2, raw="3.5 - 5.2 g/dL")
        ),
        TestCatalogItem(
            test_id="GLOBULIN",
            canonical_name="Globulin",
            aliases=["globulin", "serum globulin"],
            loinc_code="2336-6",
            category="Liver",
            default_unit="g/dL",
            default_reference_range=ReferenceRange(low=2.0, high=3.5, raw="2.0 - 3.5 g/dL")
        ),
        TestCatalogItem(
            test_id="AG_RATIO",
            canonical_name="A/G Ratio",
            aliases=["a/g ratio", "albumin/globulin ratio", "albumin / globulin ratio"],
            loinc_code="1759-1",
            category="Liver",
            default_unit="",
            default_reference_range=ReferenceRange(low=0.9, high=2.0, raw="0.9 - 2.0")
        ),
        TestCatalogItem(
            test_id="GGT",
            canonical_name="Gamma Glutamyl Transferase",
            aliases=["gamma glutamyl transferase", "ggt", "gamma gt"],
            loinc_code="2324-2",
            category="Liver",
            default_unit="U/L",
            default_reference_range=ReferenceRange(low=0.0, high=55.0, raw="0 - 55 U/L")
        ),
        TestCatalogItem(
            test_id="VLDL",
            canonical_name="VLDL Cholesterol",
            aliases=["vldl cholesterol", "vldl", "vldl-c"],
            loinc_code="13457-7",
            category="Lipids",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=5.0, high=40.0, raw="5 - 40 mg/dL")
        ),
        TestCatalogItem(
            test_id="IRON",
            canonical_name="Serum Iron",
            aliases=["serum iron", "iron"],
            loinc_code="2498-4",
            category="Iron Profile",
            default_unit="ug/dL",
            default_reference_range=ReferenceRange(low=60.0, high=170.0, raw="60 - 170 ug/dL")
        ),
        TestCatalogItem(
            test_id="TIBC",
            canonical_name="Total Iron Binding Capacity",
            aliases=["total iron binding capacity", "tibc"],
            loinc_code="2500-7",
            category="Iron Profile",
            default_unit="ug/dL",
            default_reference_range=ReferenceRange(low=240.0, high=450.0, raw="240 - 450 ug/dL")
        ),
        TestCatalogItem(
            test_id="TRANSFERRIN",
            canonical_name="Transferrin",
            aliases=["transferrin"],
            loinc_code="3034-6",
            category="Iron Profile",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=200.0, high=360.0, raw="200 - 360 mg/dL")
        ),
        TestCatalogItem(
            test_id="TRANSFERRIN_SATURATION",
            canonical_name="Transferrin Saturation",
            aliases=["transferrin saturation", "transferrin saturation %", "% transferrin saturation"],
            loinc_code="2502-3",
            category="Iron Profile",
            default_unit="%",
            default_reference_range=ReferenceRange(low=15.0, high=50.0, raw="15 - 50 %")
        ),
        TestCatalogItem(
            test_id="FERRITIN",
            canonical_name="Serum Ferritin",
            aliases=["serum ferritin", "ferritin"],
            loinc_code="2276-4",
            category="Iron Profile",
            default_unit="ng/mL",
            default_reference_range=ReferenceRange(low=13.0, high=150.0, raw="13 - 150 ng/mL")
        ),
        TestCatalogItem(
            test_id="T3",
            canonical_name="Triiodothyronine (T3)",
            aliases=["triiodothyronine (t3)", "triiodothyronine", "total t3", "t3"],
            loinc_code="3053-1",
            category="Endocrine",
            default_unit="ng/mL",
            default_reference_range=ReferenceRange(low=0.8, high=2.0, raw="0.8 - 2.0 ng/mL")
        ),
        TestCatalogItem(
            test_id="T4",
            canonical_name="Thyroxine (T4)",
            aliases=["thyroxine (t4)", "thyroxine", "total t4", "t4"],
            loinc_code="3026-7",
            category="Endocrine",
            default_unit="ug/dL",
            default_reference_range=ReferenceRange(low=5.1, high=14.1, raw="5.1 - 14.1 ug/dL")
        ),
        TestCatalogItem(
            test_id="GLUCOSE_RANDOM",
            canonical_name="Random Blood Sugar",
            aliases=["random blood sugar", "rbs", "random glucose", "blood sugar random"],
            loinc_code="2345-7",
            category="Metabolic",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=70.0, high=140.0, raw="70 - 140 mg/dL")
        ),
        TestCatalogItem(
            test_id="VITAMIN_D",
            canonical_name="25-Hydroxy Vitamin D",
            aliases=["25-hydroxy vitamin d", "25-oh vitamin d", "vitamin d (25-oh)", "vitamin d", "25 hydroxyvitamin d", "vitamin d3"],
            loinc_code="62292-8",
            category="Vitamins",
            default_unit="ng/mL",
            default_reference_range=ReferenceRange(low=30.0, high=100.0, raw="30 - 100 ng/mL")
        ),
        TestCatalogItem(
            test_id="VITAMIN_B12",
            canonical_name="Vitamin B12",
            aliases=["vitamin b12", "b12", "cyanocobalamin"],
            loinc_code="2132-9",
            category="Vitamins",
            default_unit="pg/mL",
            default_reference_range=ReferenceRange(low=211.0, high=911.0, raw="211 - 911 pg/mL")
        ),
        TestCatalogItem(
            test_id="MEAN_PLASMA_GLUCOSE",
            canonical_name="Approximate Mean Plasma Glucose",
            aliases=["approx mean plasma glucose", "approximate mean plasma glucose", "average blood glucose"],
            loinc_code="2713-2",
            category="Glycemic Control",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=70.0, high=126.0, raw="70 - 126 mg/dL")
        ),
        TestCatalogItem(
            test_id="PROCALCITONIN",
            canonical_name="Procalcitonin",
            aliases=["procalcitonin", "pct procalcitonin"],
            loinc_code="33959-8",
            category="Inflammation",
            default_unit="ng/mL",
            default_reference_range=ReferenceRange(low=0.0, high=0.5, raw="< 0.5 ng/mL")
        ),
        TestCatalogItem(
            test_id="CALCIUM",
            canonical_name="Calcium",
            aliases=["calcium", "serum calcium", "ca", "calcium, total", "calcium - total", "calcium (total)", "total calcium"],
            loinc_code="17861-6",
            category="Metabolic",
            default_unit="mg/dL",
            default_reference_range=ReferenceRange(low=8.6, high=10.3, raw="8.6 - 10.3 mg/dL")
        ),
    ]

    # Explicitly ambiguous names requiring manual review
    AMBIGUOUS_NAMES = {"glucose", "blood test", "panel", "sugar", "cholesterol test"}

    @classmethod
    def match_test(cls, raw_test_name: str, unit: Optional[str] = None) -> Tuple[Optional[TestCatalogItem], str]:
        """
        Matches raw test name against catalog items.
        Returns Tuple[MatchedCatalogItem, mapping_status].
        mapping_status is 'MAPPED' or 'REVIEW_REQUIRED'.
        """
        if not raw_test_name or not raw_test_name.strip():
            return None, "REVIEW_REQUIRED"

        clean = raw_test_name.lower().strip()
        # Clean symbols and collapse spaced single-letter acronyms: "m c h c" -> "mchc", "* haemoglobin" -> "haemoglobin"
        clean_norm = re.sub(r"^[*\s,:-]+|[*\s,:-]+$", "", clean)
        clean_norm = re.sub(r"(?<=\b[a-z]\b)\s+(?=\b[a-z]\b)", "", clean_norm)

        # Explicit handling for ambiguous "PCT"
        if clean_norm == "pct":
            if unit:
                u_clean = unit.lower().strip()
                if "%" in u_clean or "cumm" in u_clean or "fl" in u_clean:
                    for item in cls.CATALOG:
                        if item.test_id == "PCT":
                            return item, "MAPPED"
                elif "ng/ml" in u_clean or "ug/l" in u_clean or "pg/ml" in u_clean:
                    for item in cls.CATALOG:
                        if item.test_id == "PROCALCITONIN":
                            return item, "MAPPED"
            # If ambiguous without unit context
            return None, "REVIEW_REQUIRED"

        # Check explicit ambiguity list
        if clean_norm in cls.AMBIGUOUS_NAMES:
            return None, "REVIEW_REQUIRED"

        # 1. First Pass: Exact Alias Match
        for item in cls.CATALOG:
            if not item.active:
                continue
            for alias in item.aliases:
                if alias == clean or alias == clean_norm:
                    return item, "MAPPED"

        # 2. Second Pass: Word Boundary Match
        matched_items: List[TestCatalogItem] = []
        for item in cls.CATALOG:
            if not item.active:
                continue
            for alias in item.aliases:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, clean) or re.search(pattern, clean_norm):
                    matched_items.append(item)
                    break

        # Deduplicate matched items by test_id
        matched_items = list({it.test_id: it for it in matched_items}.values())

        if len(matched_items) == 1:
            return matched_items[0], "MAPPED"
        
        return None, "REVIEW_REQUIRED"
