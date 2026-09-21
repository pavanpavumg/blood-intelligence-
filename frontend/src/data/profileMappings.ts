import { ProfileConfig } from '../types';

export const PROFILE_MAPPING: Record<string, ProfileConfig> = {
  "Kidney Profile": {
    name: "Kidney Profile",
    tests: ["Urea", "Creatinine", "BUN", "BUN/Cr Ratio", "Uric Acid", "Urea Nitrogen", "Blood Urea Nitrogen"],
    icon: "🫘",
    organ: "kidneys",
    description: "Measures how well your kidneys filter waste from blood"
  },
  "Electrolyte Profile": {
    name: "Electrolyte Profile",
    tests: ["Sodium", "Potassium", "Chloride", "Calcium", "Phosphorus", "Magnesium"],
    icon: "⚡",
    organ: null,
    description: "Essential minerals that regulate body functions"
  },
  "Liver Profile": {
    name: "Liver Profile",
    tests: ["Bilirubin Total", "Bilirubin Direct", "Bilirubin Indirect", "SGOT (AST)", "SGPT (ALT)", "Alkaline Phosphatase", "Total Protein", "Albumin", "Globulin", "A/G Ratio", "SGOT", "SGPT"],
    icon: "🫀",
    organ: "liver",
    description: "Checks liver health and protein production"
  },
  "Thyroid Profile": {
    name: "Thyroid Profile",
    tests: ["T3 (Triiodothyronine)", "T4 (Thyroxine)", "TSH", "Total T3", "Total T4", "Thyroid Stimulating Hormone"],
    icon: "🦋",
    organ: "thyroid",
    description: "Hormones that regulate metabolism"
  },
  "Lipid Profile": {
    name: "Lipid Profile",
    tests: ["Total Cholesterol", "HDL Cholesterol", "LDL Cholesterol", "Triglycerides", "VLDL", "VLDL Cholesterol", "Non-HDL Cholesterol"],
    icon: "🫒",
    organ: "heart",
    description: "Fat levels in blood that affect heart health"
  },
  "Blood Counts": {
    name: "Blood Counts",
    tests: ["Haemoglobin", "Hemoglobin", "RBC Count", "Total WBC Count", "WBC Count", "Platelet Count", "Packed Cell Volume (PCV)", "PCV", "Hematocrit", "MCV", "MCH", "MCHC", "RDW CV", "RDW SD", "PDW", "MPV", "P-LCR", "PCT"],
    icon: "🩸",
    organ: "blood",
    description: "Complete blood cell analysis"
  },
  "Differential Counts": {
    name: "Differential Counts",
    tests: ["Neutrophils", "Lymphocytes", "Eosinophils", "Monocytes", "Basophils", "Absolute Neutrophil Count", "Absolute Lymphocyte Count", "Absolute Eosinophil Count", "Absolute Monocyte Count", "Absolute Basophil Count"],
    icon: "🔬",
    organ: "blood",
    description: "Types of white blood cells"
  },
  "Anemia Studies": {
    name: "Anemia Studies",
    tests: ["Iron", "Serum Iron", "TIBC", "Total Iron Binding Capacity", "Transferrin Saturation", "Ferritin", "Serum Ferritin", "Vitamin B12", "Folic Acid"],
    icon: "💉",
    organ: "blood",
    description: "Checks for iron and vitamin deficiencies"
  },
  "Diabetes Monitoring": {
    name: "Diabetes Monitoring",
    tests: ["Fasting Blood Sugar", "Post Prandial Blood Sugar", "Random Blood Sugar", "HbA1c", "Glycated Hemoglobin", "Average Blood Glucose"],
    icon: "📊",
    organ: "pancreas",
    description: "Blood sugar control indicators"
  },
  "Urinalysis": {
    name: "Urinalysis",
    tests: ["pH", "Specific Gravity", "Glucose", "Protein", "Ketones", "Bilirubin", "Blood", "Nitrite", "Leukocytes"],
    icon: "🧪",
    organ: "bladder",
    description: "Chemical analysis of urine"
  },
  "Vitamin Profile": {
    name: "Vitamin Profile",
    tests: ["Vitamin D", "25-Hydroxy Vitamin D", "Vitamin B12", "Folic Acid", "Vitamin B9"],
    icon: "💊",
    organ: null,
    description: "Essential vitamin levels"
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
