import { TestExplanation } from '../types';

export const EXPLANATIONS: Record<string, TestExplanation> = {
  "Urea": {
    what: "Urea is a waste product formed when protein is broken down in your body.",
    function: "Healthy kidneys filter urea out of your blood and excrete it in urine.",
    meaning: "Reflects kidney filtration efficiency and protein metabolism balance.",
    high_meaning: "High urea levels may indicate reduced kidney function, dehydration, or high protein intake.",
    low_meaning: "Low urea is uncommon but can be seen in severe liver disease or low protein diets."
  },
  "Creatinine": {
    what: "Creatinine is a waste byproduct of normal muscle breakdown and energy consumption.",
    function: "Kidneys continuously filter creatinine out of your blood into urine at a steady rate.",
    meaning: "Creatinine is one of the most reliable markers for evaluating kidney health.",
    high_meaning: "High creatinine levels suggest reduced kidney filtration capability.",
    low_meaning: "Low creatinine may be linked to lower muscle mass, aging, or severe malnutrition."
  },
  "BUN": {
    what: "Blood Urea Nitrogen (BUN) measures the amount of nitrogen in your blood that comes from urea.",
    function: "Evaluates how effectively your kidneys clear metabolic waste products.",
    meaning: "Provides insight into kidney performance and fluid balance in the body.",
    high_meaning: "High BUN can point toward kidney dysfunction, heart failure, or dehydration.",
    low_meaning: "Low BUN may occur with fluid overload, liver impairment, or malnutrition."
  },
  "BUN/Cr Ratio": {
    what: "BUN/Cr Ratio compares blood urea nitrogen to creatinine levels.",
    function: "Helps doctors differentiate between kidney disease and dehydration or heart conditions.",
    meaning: "Useful for determining the root cause of elevated nitrogenous wastes.",
    high_meaning: "High ratio usually suggests dehydration or reduced blood flow to the kidneys.",
    low_meaning: "Low ratio may indicate liver disease, malnutrition, or acute kidney injury."
  },
  "Uric Acid": {
    what: "Uric acid is produced when your body breaks down purines found in foods and body cells.",
    function: "Dissolves in blood, passes through kidneys, and exits via urine.",
    meaning: "Monitors gout risk and kidney stone susceptibility.",
    high_meaning: "High uric acid can cause gout (painful joint inflammation) or kidney stones.",
    low_meaning: "Low uric acid is rare and generally not a clinical concern."
  },
  "Haemoglobin": {
    what: "Haemoglobin is an iron-rich protein in red blood cells that gives blood its red color.",
    function: "Carries oxygen from your lungs to every organ and tissue in your body.",
    meaning: "Essential indicator of oxygen-carrying capacity and overall energy levels.",
    high_meaning: "High haemoglobin can occur with chronic lung disease, smoking, or dehydration.",
    low_meaning: "Low haemoglobin indicates anemia, causing fatigue, shortness of breath, and pale skin."
  },
  "Hemoglobin": {
    what: "Haemoglobin is an iron-rich protein in red blood cells that carries oxygen.",
    function: "Transports oxygen from lungs to all organs and returns carbon dioxide back to lungs.",
    meaning: "Primary marker for detecting anemia.",
    high_meaning: "Elevated levels may stem from smoking, high altitude, or lung conditions.",
    low_meaning: "Low levels indicate anemia, leading to tiredness and weakness."
  },
  "RBC Count": {
    what: "Red Blood Cell (RBC) count measures the number of red cells circulating in your bloodstream.",
    function: "Delivers vital oxygen to your muscles and vital organs.",
    meaning: "Key metric in Complete Blood Count (CBC) analysis.",
    high_meaning: "High RBC count (erythrocytosis) can result from low oxygen levels, smoking, or bone marrow conditions.",
    low_meaning: "Low RBC count reflects anemia or blood loss."
  },
  "Total WBC Count": {
    what: "White Blood Cell (WBC) count measures the primary defenders of your immune system.",
    function: "Fights off bacteria, viruses, fungi, and other foreign pathogens.",
    meaning: "Reflects immune system activity and inflammatory status.",
    high_meaning: "High WBC count signals active infection, inflammation, stress, or tissue injury.",
    low_meaning: "Low WBC count (leukopenia) indicates weakened immune defense or bone marrow suppression."
  },
  "WBC Count": {
    what: "White Blood Cell count assesses the body's infection-fighting immune cells.",
    function: "Protects the body against microbial infections and cellular damage.",
    meaning: "Standard indicator of infection or systemic inflammation.",
    high_meaning: "Elevated during active bacterial or viral infections.",
    low_meaning: "Reduced levels leave the body more vulnerable to infections."
  },
  "Platelet Count": {
    what: "Platelets (thrombocytes) are tiny cell fragments essential for normal blood clotting.",
    function: "Form clots at wound sites to prevent excessive bleeding.",
    meaning: "Evaluates clotting capability and bleeding risk.",
    high_meaning: "High platelets (thrombocytosis) increase clot risks or signal chronic inflammation.",
    low_meaning: "Low platelets (thrombocytopenia) increase risk of bruising, nosebleeds, and prolonged bleeding."
  },
  "Packed Cell Volume (PCV)": {
    what: "PCV (Hematocrit) measures the percentage of blood volume occupied by red blood cells.",
    function: "Reflects blood thickness and red cell concentration.",
    meaning: "Helps assess hydration and oxygen transport density.",
    high_meaning: "High PCV indicates dehydration or overproduction of red blood cells.",
    low_meaning: "Low PCV indicates anemia or fluid overload."
  },
  "MCV": {
    what: "Mean Corpuscular Volume (MCV) measures the average size of individual red blood cells.",
    function: "Helps classify the specific type of anemia present.",
    meaning: "Differentiates microcytic, normocytic, and macrocytic anemias.",
    high_meaning: "High MCV (large cells) points to Vitamin B12 or Folate deficiency.",
    low_meaning: "Low MCV (small cells) suggests iron deficiency anemia or thalassemia."
  },
  "MCH": {
    what: "Mean Corpuscular Hemoglobin (MCH) measures the average amount of hemoglobin inside a red cell.",
    function: "Reflects oxygen carrying density per red cell.",
    meaning: "Correlates closely with red cell size (MCV).",
    high_meaning: "High MCH is often seen in B12/Folate deficiency.",
    low_meaning: "Low MCH is typical in iron deficiency anemia."
  },
  "MCHC": {
    what: "MCHC measures the concentration of hemoglobin relative to red cell volume.",
    function: "Assesses how rich red cells are in oxygen-binding pigment.",
    meaning: "Used alongside MCV and MCH to evaluate blood disorders.",
    high_meaning: "High MCHC can indicate hereditary spherocytosis or burn injuries.",
    low_meaning: "Low MCHC signals severe iron deficiency anemia."
  },
  "RDW CV": {
    what: "Red Cell Distribution Width (RDW-CV) measures variations in the size of red blood cells.",
    function: "Indicates whether red cells are uniform or varying in size.",
    meaning: "Elevated RDW is an early warning marker for mixed anemias.",
    high_meaning: "High RDW means significant variation in red cell size, common in early iron or B12 deficiency.",
    low_meaning: "Low RDW means red cells are uniform in size (normal finding)."
  },
  "RDW SD": {
    what: "RDW-SD measures the standard deviation of red blood cell volume.",
    function: "Complements RDW-CV to detect early nutritional deficiencies.",
    meaning: "Evaluates red blood cell size variation.",
    high_meaning: "High values suggest bone marrow is producing mismatched red cells due to deficiency.",
    low_meaning: "Normal or low values indicate consistent cell size."
  },
  "PDW": {
    what: "Platelet Distribution Width (PDW) measures variation in platelet sizes.",
    function: "Shows whether platelets are young (larger) or mature.",
    meaning: "Evaluates platelet active production in bone marrow.",
    high_meaning: "High PDW suggests active bone marrow release of new platelets.",
    low_meaning: "Usually non-significant clinical finding."
  },
  "MPV": {
    what: "Mean Platelet Volume (MPV) measures the average size of platelets in blood.",
    function: "Larger young platelets are more reactive and clot-efficient.",
    meaning: "Provides clues regarding platelet turnover rates.",
    high_meaning: "High MPV occurs when bone marrow rapidly produces platelets to combat low counts.",
    low_meaning: "Low MPV suggests reduced platelet production by bone marrow."
  },
  "Neutrophils": {
    what: "Neutrophils are the most abundant white blood cells, serving as first responders.",
    function: "Rapidly engulf and destroy invasive bacterial infections.",
    meaning: "Primary marker for acute bacterial infections.",
    high_meaning: "High neutrophils indicate acute bacterial infection, severe physical stress, or inflammation.",
    low_meaning: "Low neutrophils (neutropenia) increase vulnerability to bacterial infections."
  },
  "Lymphocytes": {
    what: "Lymphocytes are white blood cells responsible for viral immunity and antibody production.",
    function: "Recognize viral invaders and coordinate targeted immune memory.",
    meaning: "Key indicator of viral defense and chronic immune responses.",
    high_meaning: "High lymphocytes occur during viral infections like mononucleosis or flu.",
    low_meaning: "Low lymphocytes can result from stress, steroid use, or immune suppression."
  },
  "Eosinophils": {
    what: "Eosinophils are specialized white blood cells that combat parasites and allergens.",
    function: "Release enzymes during allergic reactions and asthma.",
    meaning: "Evaluates allergic responses and parasitic defense.",
    high_meaning: "High eosinophils suggest allergies, asthma, eczema, or parasitic infections.",
    low_meaning: "Low eosinophils are generally considered normal."
  },
  "Monocytes": {
    what: "Monocytes are large white blood cells that clear cellular debris and chronic pathogens.",
    function: "Transform into macrophages in tissue to consume damaged cells.",
    meaning: "Reflects recovery from infection or chronic inflammatory states.",
    high_meaning: "High monocytes occur in chronic infections, autoimmune conditions, or recovery phases.",
    low_meaning: "Low monocytes are rarely clinically significant."
  },
  "Basophils": {
    what: "Basophils are rare white blood cells that release histamine during inflammatory responses.",
    function: "Trigger immediate allergic inflammatory pathways.",
    meaning: "Monitors rare allergic and myeloproliferative conditions.",
    high_meaning: "High basophils occur in severe allergies, hypothyroidism, or bone marrow conditions.",
    low_meaning: "Low basophils are considered a normal finding."
  },
  "Sodium": {
    what: "Sodium is an essential electrolyte that regulates body water distribution and nerve signals.",
    function: "Controls blood pressure, fluid balance, and muscle contractions.",
    meaning: "Crucial electrolyte for hydration and cellular function.",
    high_meaning: "High sodium (hypernatremia) indicates dehydration, excessive salt intake, or kidney issues.",
    low_meaning: "Low sodium (hyponatremia) can cause confusion, weakness, and results from excess water or diuretic use."
  },
  "Potassium": {
    what: "Potassium is a vital mineral controlling heart rhythm and muscle contraction.",
    function: "Maintains regular cardiac electrical activity and cellular hydration.",
    meaning: "Critical electrolyte evaluated for heart and kidney safety.",
    high_meaning: "High potassium (hyperkalemia) is dangerous for heart rhythm and requires urgent medical attention.",
    low_meaning: "Low potassium (hypokalemia) causes muscle cramps, weakness, and irregular heartbeat."
  },
  "Chloride": {
    what: "Chloride works alongside sodium and potassium to maintain blood acid-base balance.",
    function: "Helps regulate blood volume, pressure, and pH balance.",
    meaning: "Evaluates fluid balance and acid-base status.",
    high_meaning: "High chloride occurs with dehydration, kidney disease, or metabolic acidosis.",
    low_meaning: "Low chloride can be caused by prolonged vomiting, heart failure, or Addison disease."
  },
  "Calcium": {
    what: "Calcium is an abundant mineral essential for strong bones, teeth, and muscle action.",
    function: "Enables nerve transmission, blood clotting, and heart muscle function.",
    meaning: "Monitors bone health, parathyroid function, and kidney health.",
    high_meaning: "High calcium (hypercalcemia) can weaken bones and affect kidney function.",
    low_meaning: "Low calcium (hypocalcemia) causes muscle cramps, tingling fingers, and bone density loss."
  },
  "Total Cholesterol": {
    what: "Total Cholesterol measures the overall sum of blood fats in your circulatory system.",
    function: "Used by body to build cell membranes and synthesize hormones.",
    meaning: "Standard screening parameter for cardiovascular health.",
    high_meaning: "High cholesterol increases plaque buildup risk in arteries and heart disease risk.",
    low_meaning: "Very low cholesterol is rare but can occur with hyperthyroidism or liver disease."
  },
  "HDL Cholesterol": {
    what: "HDL is known as 'Good' cholesterol because it protects arterial walls.",
    function: "Scavenges excess cholesterol from arteries and returns it to the liver for removal.",
    meaning: "Higher levels correlate with lower heart attack and stroke risk.",
    high_meaning: "High HDL is desirable and protective for cardiovascular health.",
    low_meaning: "Low HDL increases risk for coronary artery disease."
  },
  "LDL Cholesterol": {
    what: "LDL is known as 'Bad' cholesterol because it deposits fats in blood vessel walls.",
    function: "Delivers cholesterol to body tissues, but excess builds up as arterial plaque.",
    meaning: "Primary therapeutic target for preventing heart disease.",
    high_meaning: "High LDL creates arterial blockages, escalating heart attack and stroke risks.",
    low_meaning: "Low LDL is ideal for heart protection."
  },
  "Triglycerides": {
    what: "Triglycerides are the most common type of fat derived from unburned caloric intake.",
    function: "Stored in fat cells to serve as future metabolic energy reserves.",
    meaning: "Important indicator of metabolic health, diet, and cardiovascular risk.",
    high_meaning: "High triglycerides are linked to metabolic syndrome, fatty liver, and heart disease.",
    low_meaning: "Low triglycerides can result from low-fat diets or hyperthyroidism."
  },
  "VLDL": {
    what: "VLDL (Very Low-Density Lipoprotein) carries triglycerides to tissues.",
    function: "Transports newly synthesized fats from liver to body fat stores.",
    meaning: "Contributes to arterial plaque formation when elevated.",
    high_meaning: "High VLDL is associated with elevated heart disease risk and metabolic strain.",
    low_meaning: "Low VLDL is generally considered healthy."
  },
  "SGOT (AST)": {
    what: "AST (SGOT) is an enzyme found abundantly in liver cells, heart, and skeletal muscle.",
    function: "Helps process amino acids for cellular energy production.",
    meaning: "Marker of liver cell or muscular damage.",
    high_meaning: "High AST indicates liver inflammation, muscle injury, or heavy alcohol use.",
    low_meaning: "Low AST is normal and healthy."
  },
  "SGPT (ALT)": {
    what: "ALT (SGPT) is an enzyme concentrated primarily in liver cells.",
    function: "Converts proteins into energy for liver functioning.",
    meaning: "The most specific blood marker for liver cell health.",
    high_meaning: "High ALT signals liver cell strain, fatty liver, hepatitis, or medication toxicity.",
    low_meaning: "Low ALT is normal and expected."
  },
  "Bilirubin Total": {
    what: "Bilirubin is an orange-yellow pigment formed during normal breakdown of red blood cells.",
    function: "Processed by the liver and excreted into bile.",
    meaning: "Evaluates liver function, bile duct flow, and red cell breakdown rates.",
    high_meaning: "High total bilirubin causes jaundice (yellowing of eyes and skin) and signals liver or gall bladder issues.",
    low_meaning: "Low levels are non-significant."
  },
  "Alkaline Phosphatase": {
    what: "Alkaline Phosphatase (ALP) is an enzyme present in liver bile ducts and bone tissue.",
    function: "Aids in protein breakdown and bone mineralization.",
    meaning: "Monitors liver bile drainage and bone growth balance.",
    high_meaning: "High ALP points toward bile duct obstruction, liver strain, or rapid bone repair.",
    low_meaning: "Low ALP can occur with zinc deficiency or malnutrition."
  },
  "HbA1c": {
    what: "HbA1c measures average blood sugar levels over the past 2 to 3 months.",
    function: "Reflects sugar coating attached to red cell hemoglobin molecules.",
    meaning: "Gold standard test for diagnosing and managing diabetes.",
    high_meaning: "HbA1c above 5.7% indicates Pre-diabetes; 6.5%+ indicates Diabetes requiring management.",
    low_meaning: "Low HbA1c is normal, but very low levels can occur with frequent hypoglycemia."
  },
  "Fasting Blood Sugar": {
    what: "Fasting Blood Sugar measures glucose levels after an 8-12 hour overnight fast.",
    function: "Assesses baseline insulin control without recent food intake.",
    meaning: "Key indicator of diabetes risk and metabolic stability.",
    high_meaning: "High fasting sugar indicates impaired glucose tolerance or diabetes.",
    low_meaning: "Low sugar (hypoglycemia) causes shakiness, sweating, and confusion."
  },
  "Vitamin D": {
    what: "Vitamin D (25-Hydroxy) is a fat-soluble vitamin synthesized through sunlight and diet.",
    function: "Enables calcium absorption for strong bones, teeth, and robust immune health.",
    meaning: "Crucial nutrient for bone density, mood, and immune defense.",
    high_meaning: "Toxicity is rare but can cause hypercalcemia from massive over-supplementation.",
    low_meaning: "Deficiency causes weak bones (osteopenia/osteoporosis), muscle weakness, and low immunity."
  },
  "Vitamin B12": {
    what: "Vitamin B12 (Cobalamin) is an essential vitamin required for nerve function and red cell synthesis.",
    function: "Maintains myelin nerve sheaths and DNA synthesis.",
    meaning: "Evaluates neurological health and blood formation capability.",
    high_meaning: "Elevated levels can stem from B12 injections or liver disease.",
    low_meaning: "Low B12 leads to numbness, tingling in hands/feet, memory issues, and megaloblastic anemia."
  }
};

export function getTestExplanation(testName: string, status: string = 'NORMAL'): TestExplanation {
  if (!testName) {
    return {
      what: "Clinical laboratory parameter analyzed in blood or urine.",
      function: "Helps physicians monitor organ performance and internal metabolic balance.",
      meaning: status === "HIGH" ? "Result is above the expected reference range." : status === "LOW" ? "Result is below the expected reference range." : "Result is within normal reference limits.",
      high_meaning: "Values above reference limits warrant clinical review.",
      low_meaning: "Values below reference limits warrant clinical review."
    };
  }

  const trimmed = testName.trim();
  const directMatch = EXPLANATIONS[trimmed];
  if (directMatch) return directMatch;

  const strippedName = trimmed.replace(/\b(Count|Total|Serum|Blood)\b/gi, '').trim();
  const strippedMatch = EXPLANATIONS[strippedName];
  if (strippedMatch) return strippedMatch;

  // Case-insensitive fallback
  const lower = trimmed.toLowerCase();
  for (const [key, val] of Object.entries(EXPLANATIONS)) {
    if (key.toLowerCase() === lower || lower.includes(key.toLowerCase())) {
      return val;
    }
  }

  return {
    what: `${trimmed} is a standard clinical laboratory parameter analyzed in blood or urine.`,
    function: "Helps physicians monitor organ performance and internal metabolic balance.",
    meaning: status === "HIGH" ? "Result is above the expected reference range." : status === "LOW" ? "Result is below the expected reference range." : "Result is within normal reference limits.",
    high_meaning: "Values above reference limits warrant clinical review.",
    low_meaning: "Values below reference limits warrant clinical review."
  };
}
