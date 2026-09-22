import { ProfileConfig } from '../types';

export const PROFILE_MAPPING: Record<string, ProfileConfig> = {
  "Kidney Profile": {
    name: "Kidney Profile",
    tests: [
      "Urea", "*UREA", "* UREA", "Creatinine", "SERUM CREATININE", "* SERUM CREATININE",
      "BUN", "UREA NITROGEN (BUN)", "* UREA NITROGEN (BUN)", "Blood Urea Nitrogen",
      "BUN/Cr Ratio", "BUN/CREATININE RATIO", "* BUN/CREATININE RATIO",
      "Uric Acid", "URIC ACID", "* URIC ACID"
    ],
    icon: "🫘",
    organ: "kidneys",
    description: "Measures how well your kidneys filter waste from blood"
  },
  "Electrolyte Profile": {
    name: "Electrolyte Profile",
    tests: [
      "Sodium", "* SODIUM", "Potassium", "* POTASSIUM", "Chloride", "*CHLORIDE", "* CHLORIDE",
      "Calcium", "* Calcium", "Phosphorus", "Magnesium"
    ],
    icon: "⚡",
    organ: null,
    description: "Essential minerals that regulate body functions"
  },
  "Liver Profile": {
    name: "Liver Profile",
    tests: [
      "Bilirubin Total", "TOTAL BILIRUBIN", "* TOTAL BILIRUBIN",
      "Bilirubin Direct", "DIRECT BILIRUBIN", "* DIRECT BILIRUBIN",
      "Bilirubin Indirect", "INDIRECT BILIRUBIN", "* INDIRECT BILIRUBIN",
      "SGOT (AST)", "SGOT / AST", "* SGOT / AST", "SGOT", "AST",
      "SGPT (ALT)", "SGPT / ALT", "* SGPT / ALT", "SGPT", "ALT",
      "Alkaline Phosphatase", "Alkaline Phosphatase (ALP)", "Alkaline Phosphatase(ALP)", "* Alkaline Phosphatase(ALP)",
      "Total Protein", "PROTEIN-TOTAL", "* PROTEIN-TOTAL",
      "Albumin", "ALBUMIN", "* ALBUMIN",
      "Globulin", "GLOBULIN", "* GLOBULIN",
      "A/G Ratio", "A/G RATIO", "* A/G RATIO",
      "Gamma Glutamyl Transferase", "GAMMA GLUTAMYL TRANSFERASE", "* GAMMA GLUTAMYL TRANSFERASE", "GGT"
    ],
    icon: "🫀",
    organ: "liver",
    description: "Checks liver health, enzymes, and protein synthesis"
  },
  "Thyroid Profile": {
    name: "Thyroid Profile",
    tests: [
      "T3 (Triiodothyronine)", "TOTAL TRIIODOTHYRONINE (T3)", "TOTAL TRIIODOTHYRONINE ( T3)", "* TOTAL TRIIODOTHYRONINE ( T3)", "Total T3", "T3",
      "T4 (Thyroxine)", "TOTAL THYROXINE (T4)", "* TOTAL THYROXINE (T4)", "Total T4", "T4",
      "TSH", "Thyroid Stimulating Hormone", "Thyroid Stimulating Hormone (TSH)", "Thyroid Stimulating Hormone.(TSH)", "* Thyroid Stimulating Hormone.(TSH)"
    ],
    icon: "🦋",
    organ: "thyroid",
    description: "Hormones that regulate metabolism and energy balance"
  },
  "Lipid Profile": {
    name: "Lipid Profile",
    tests: [
      "Total Cholesterol", "TOTAL CHOLESTEROL", "* TOTAL CHOLESTEROL",
      "HDL Cholesterol", "HDL - CHOLESTEROL", "* HDL - CHOLESTEROL", "HDL-CHOLESTEROL", "* HDL-CHOLESTEROL",
      "LDL Cholesterol", "LDL - CHOLESTEROL", "* LDL - CHOLESTEROL", "LDL-CHOLESTEROL", "*LDL-CHOLESTEROL",
      "Triglycerides", "TRIGLYCERIDES", "* TRIGLYCERIDES",
      "VLDL", "VLDL Cholesterol", "VLDL - CHOLESTEROL", "*VLDL CHOLESTEROL", "* VLDL CHOLESTEROL",
      "Non-HDL Cholesterol",
      "CHOL/HDL Ratio", "CHOL / HDL Ratio", "CHOL / HDL Ratio.", "* CHOL / HDL Ratio.", "*CHOL/ HDL Ratio.",
      "LDL/HDL Ratio", "LDL / HDL RATIO", "* LDL / HDL RATIO",
      "HDL/LDL Ratio", "HDL / LDL CHOLESTEROL RATIO", "* HDL/LDL CHOLESTEROL RATIO", "HDL/LDL CHOLESTEROL RATIO"
    ],
    icon: "🫒",
    organ: "heart",
    description: "Cholesterol, triglycerides, and lipid risk ratios"
  },
  "Blood Counts": {
    name: "Blood Counts",
    tests: [
      "Haemoglobin", "HAEMOGLOBIN", "* HAEMOGLOBIN", "Hemoglobin",
      "Total WBC Count", "TOTAL LEUCOCYTE COUNT (TLC)", "* TOTAL LEUCOCYTE COUNT (TLC)", "WBC Count", "WBC",
      "RBC Count", "RBC COUNT", "* RBC COUNT",
      "Packed Cell Volume (PCV)", "PCV", "* PCV", "Hematocrit", "HCT",
      "MCV", "* MCV", "MCH", "* MCH", "MCHC", "* MCHC",
      "RDW CV", "RDW-CV", "* RDW-CV", "RDW SD", "RDW-SD", "* RDW-SD",
      "Platelet Count", "PLATELET COUNT", "* PLATELET COUNT",
      "MPV", "* MPV", "PDW", "* PDW", "PCT", "* PCT", "P-LCR"
    ],
    icon: "🩸",
    organ: "blood",
    description: "Complete blood cell count and cellular indices"
  },
  "Differential Counts": {
    name: "Differential Counts",
    tests: [
      "Neutrophils", "Lymphocytes", "Eosinophils", "Monocytes", "Basophils",
      "Absolute Neutrophil Count", "Absolute Lymphocyte Count", "Absolute Eosinophil Count", "Absolute Monocyte Count", "Absolute Basophil Count"
    ],
    icon: "🔬",
    organ: "blood",
    description: "White blood cell sub-types and immune response"
  },
  "Anemia Studies": {
    name: "Anemia Studies",
    tests: [
      "Iron", "IRON", "*IRON", "Serum Iron",
      "TIBC", "Total Iron Binding Capacity", "Total Iron Binding Capacity (TIBC)", "* Total Iron Binding Capacity (TIBC)",
      "Transferrin", "TRANSFERRIN", "*TRANSFERRIN",
      "Transferrin Saturation", "TRANSFERRIN SATURATION", "* TRANSFERRIN SATURATION",
      "Ferritin", "FERRITIN", "* FERRITIN", "Serum Ferritin"
    ],
    icon: "💉",
    organ: "blood",
    description: "Iron storage, transport proteins, and ferritin evaluation"
  },
  "Diabetes Monitoring": {
    name: "Diabetes Monitoring",
    tests: [
      "Fasting Blood Sugar", "Post Prandial Blood Sugar", "Random Blood Sugar",
      "Random Blood Sugar-Glucose (RBS)", "Random Blood Sugar-Glucose", "Random Blood Glucose", "* RANDOM BLOOD GLUCOSE",
      "HbA1c", "Glycated Hemoglobin", "Average Blood Glucose", "Glycosylated Haemoglobin", "* GLYCOSYLATED HAEMOGLOBIN",
      "Estimated Average Glucose (eAG)", "Estimated Average Glucose", "Approximate mean plasma glucose", "* Approximate mean plasma glucose"
    ],
    icon: "📊",
    organ: "pancreas",
    description: "Glycemic control and glycosylated hemoglobin"
  },
  "Urinalysis": {
    name: "Urinalysis",
    tests: [
      "Colour", "Color", "Appearance", "Specific Gravity", "pH", "* pH", "* SPECIFIC GRAVITY",
      "Protein", "Protein Urine", "Glucose", "Glucose Urine", "Ketone Bodies", "Ketones", "Bilirubin",
      "Urobilinogen", "Bile Salts", "Bile Pigments", "Blood", "Nitrite", "Leukocytes",
      "Pus Cells", "*PUS CELLS.", "Pus Cells.", "Epithelial Cells", "* EPITHELIAL CELLS",
      "R.B.C.", "RBC", "RBCs", "Casts", "Crystals", "Bacteria", "Others",
      "Urine Colour", "Urine Appearance", "Urine pH", "Urine Specific Gravity", "Urine Protein",
      "Urine Glucose", "Urine Blood", "Urine Pus Cells", "Urine Epithelial Cells", "Urine RBCs"
    ],
    icon: "🧪",
    organ: "bladder",
    description: "Physical, chemical, and microscopic examination of urine"
  },
  "Vitamin Profile": {
    name: "Vitamin Profile",
    tests: [
      "Vitamin D", "25-Hydroxy Vitamin D", "25-OH Vitamin D", "25-OH VITAMIN ( VIT D3 )", "* 25-OH VITAMIN ( VIT D3 )",
      "Vitamin - B12", "Vitamin B12", "* Vitamin - B12", "Folic Acid", "Vitamin B9"
    ],
    icon: "💊",
    organ: null,
    description: "Essential vitamins for neurological and bone wellness"
  }
};

export const ORGAN_MAPPING: Record<string, string[]> = {
  "brain": [],
  "thyroid": ["Thyroid Profile"],
  "lungs": [],
  "heart": ["Lipid Profile"],
  "liver": ["Liver Profile"],
  "stomach": ["Diabetes Monitoring"],
  "kidneys": ["Kidney Profile", "Electrolyte Profile"],
  "bladder": ["Urinalysis"],
  "pancreas": ["Diabetes Monitoring"],
  "blood": ["Blood Counts", "Differential Counts", "Anemia Studies", "Vitamin Profile"]
};
