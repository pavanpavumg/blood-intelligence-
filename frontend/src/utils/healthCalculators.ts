import {
  TestItem,
  ProcessedProfile,
  WellnessScoreResult,
  RiskFactor,
  DietGroup,
  DietItem
} from '../types';
import { PROFILE_MAPPING } from '../data/profileMappings';

export function groupTestsIntoProfiles(tests: TestItem[]): Record<string, ProcessedProfile> {
  const profiles: Record<string, ProcessedProfile> = {};

  // Initialize all defined profiles
  for (const [profileName, config] of Object.entries(PROFILE_MAPPING)) {
    profiles[profileName] = {
      name: profileName,
      icon: config.icon,
      organ: config.organ,
      description: config.description,
      tests: [],
      normal_count: 0,
      abnormal_count: 0,
      is_abnormal: false
    };
  }

  const assignedTests = new Set<string>();

  // Map tests to matching profiles
  for (const test of tests) {
    let matched = false;

    for (const [profileName, config] of Object.entries(PROFILE_MAPPING)) {
      const isMatch = config.tests.some(
        t => t.toLowerCase() === test.test_name.toLowerCase() ||
             test.raw_test_name.toLowerCase().includes(t.toLowerCase())
      );

      if (isMatch) {
        profiles[profileName].tests.push(test);
        assignedTests.add(test.test_name);
        matched = true;

        if (test.status === 'NORMAL') {
          profiles[profileName].normal_count++;
        } else {
          profiles[profileName].abnormal_count++;
          profiles[profileName].is_abnormal = true;
        }
      }
    }

    // Handle unassigned tests under a general "Other Tests" profile
    if (!matched) {
      if (!profiles["Other Parameters"]) {
        profiles["Other Parameters"] = {
          name: "Other Parameters",
          icon: "🔬",
          organ: null,
          description: "Additional laboratory measurements",
          tests: [],
          normal_count: 0,
          abnormal_count: 0,
          is_abnormal: false
        };
      }
      profiles["Other Parameters"].tests.push(test);
      if (test.status === 'NORMAL') {
        profiles["Other Parameters"].normal_count++;
      } else {
        profiles["Other Parameters"].abnormal_count++;
        profiles["Other Parameters"].is_abnormal = true;
      }
    }
  }

  // Filter out empty profiles
  return Object.fromEntries(
    Object.entries(profiles).filter(([_, p]) => p.tests.length > 0)
  );
}

export function calculateWellnessScore(tests: TestItem[]): WellnessScoreResult {
  const total = tests.length;
  if (total === 0) {
    return {
      score: 100,
      label: 'Excellent',
      color: 'green',
      total: 0,
      normal: 0,
      abnormal: 0,
      redFlags: 0
    };
  }

  const normal = tests.filter(t => t.status === 'NORMAL').length;
  const abnormal = total - normal;
  const redFlags = tests.filter(t => t.flag === 'RED_FLAG').length;

  let baseScore = (normal / total) * 100;
  // Deduct 5 points per red flag critical abnormality
  const penalty = redFlags * 5;
  const score = Math.max(0, Math.round(baseScore - penalty));

  let label: WellnessScoreResult['label'] = 'Excellent';
  let color: WellnessScoreResult['color'] = 'green';

  if (score >= 90) {
    label = 'Excellent';
    color = 'green';
  } else if (score >= 75) {
    label = 'Good';
    color = 'light-green';
  } else if (score >= 60) {
    label = 'Fair';
    color = 'amber';
  } else {
    label = 'Poor';
    color = 'red';
  }

  return {
    score,
    label,
    color,
    total,
    normal,
    abnormal,
    redFlags
  };
}

export function calculateRisks(tests: TestItem[], profiles: Record<string, ProcessedProfile>): RiskFactor[] {
  const risks: RiskFactor[] = [];

  // 1. Kidney Risk
  const kidneyProfile = profiles["Kidney Profile"];
  if (kidneyProfile) {
    const abnormalKidney = kidneyProfile.tests.filter(t => t.status !== 'NORMAL');
    const redFlagKidney = kidneyProfile.tests.filter(t => t.flag === 'RED_FLAG');

    if (redFlagKidney.length >= 2 || abnormalKidney.length >= 3) {
      risks.push({
        id: "kidney_disease",
        name: "Chronic Kidney Disease Risk",
        severity: "HIGH",
        advice: "Consult a Nephrologist immediately for comprehensive renal evaluation.",
        tests: abnormalKidney.map(t => t.test_name)
      });
    } else if (abnormalKidney.length >= 1) {
      risks.push({
        id: "kidney_strain",
        name: "Kidney Strain / Dehydration Risk",
        severity: "MODERATE",
        advice: "Increase daily water intake (2.5 - 3.0 L) and re-check renal panel in 3 weeks.",
        tests: abnormalKidney.map(t => t.test_name)
      });
    }
  }

  // 2. Electrolyte Imbalance Risk
  const electrolyteProfile = profiles["Electrolyte Profile"];
  if (electrolyteProfile) {
    const abnormalElec = electrolyteProfile.tests.filter(t => t.status !== 'NORMAL');
    if (abnormalElec.some(t => t.test_name.toLowerCase().includes('potassium') && t.status === 'HIGH')) {
      risks.push({
        id: "hyperkalemia",
        name: "Hyperkalemia (Cardiac Risk)",
        severity: "HIGH",
        advice: "Elevated potassium requires prompt medical evaluation to prevent heart rhythm complications.",
        tests: ["Potassium"]
      });
    } else if (abnormalElec.length >= 2) {
      risks.push({
        id: "electrolyte_imbalance",
        name: "Electrolyte Imbalance Risk",
        severity: "MODERATE",
        advice: "Ensure optimal hydration and monitor fluid-electrolyte intake with a physician.",
        tests: abnormalElec.map(t => t.test_name)
      });
    }
  }

  // 3. Anemia Risk
  const hb = tests.find(t => t.test_name.toLowerCase().includes('haemoglobin') || t.test_name.toLowerCase().includes('hemoglobin'));
  const rbc = tests.find(t => t.test_name.toLowerCase().includes('rbc'));
  if ((hb && hb.status === 'LOW') || (rbc && rbc.status === 'LOW')) {
    risks.push({
      id: "anemia_risk",
      name: "Anemia / Oxygen Deficit Risk",
      severity: hb?.flag === 'RED_FLAG' ? "HIGH" : "MODERATE",
      advice: "Iron supplementation, Folate/B12 evaluation, and clinical workup recommended.",
      tests: [hb?.test_name, rbc?.test_name].filter(Boolean) as string[]
    });
  }

  // 4. Diabetes Risk
  const hba1c = tests.find(t => t.test_name.toLowerCase().includes('hba1c'));
  const fastingSugar = tests.find(t => t.test_name.toLowerCase().includes('fasting blood sugar') || t.test_name.toLowerCase().includes('fasting sugar'));
  if ((hba1c && hba1c.status === 'HIGH') || (fastingSugar && fastingSugar.status === 'HIGH')) {
    risks.push({
      id: "diabetes_risk",
      name: "Glycemic Dysregulation / Diabetes Risk",
      severity: (hba1c && hba1c.value >= 6.5) ? "HIGH" : "MODERATE",
      advice: "Consult an Endocrinologist for dietary modification and blood glucose monitoring.",
      tests: [hba1c?.test_name, fastingSugar?.test_name].filter(Boolean) as string[]
    });
  }

  // 5. Lipid / Cardiovascular Risk
  const ldl = tests.find(t => t.test_name.toLowerCase().includes('ldl'));
  const totalChol = tests.find(t => t.test_name.toLowerCase().includes('total cholesterol') || t.test_name === 'Cholesterol');
  if ((ldl && ldl.status === 'HIGH') || (totalChol && totalChol.status === 'HIGH')) {
    risks.push({
      id: "cardio_risk",
      name: "Atherosclerotic Heart Disease Risk",
      severity: "MODERATE",
      advice: "Adopt heart-healthy low-saturated-fat diet, regular exercise, and lipid monitoring.",
      tests: [ldl?.test_name, totalChol?.test_name].filter(Boolean) as string[]
    });
  }

  // 6. Vitamin Deficiency
  const vitD = tests.find(t => t.test_name.toLowerCase().includes('vitamin d'));
  if (vitD && vitD.status === 'LOW') {
    risks.push({
      id: "vitamin_d_deficiency",
      name: "Vitamin D Deficiency / Bone Density Risk",
      severity: "MODERATE",
      advice: "Consider oral Vitamin D3 supplementation under doctor guidance and safe sunlight exposure.",
      tests: ["Vitamin D"]
    });
  }

  return risks;
}

export function generateDietRecommendations(profiles: Record<string, ProcessedProfile>): DietGroup[] {
  const recommendations: DietGroup[] = [];

  for (const [profileName, profile] of Object.entries(profiles)) {
    if (!profile.is_abnormal) continue;

    const items: DietItem[] = [];

    switch (profileName) {
      case "Kidney Profile": {
        const highCreatinine = profile.tests.some(t => t.test_name.toLowerCase().includes('creatinine') && t.status === 'HIGH');
        const highUrea = profile.tests.some(t => t.test_name.toLowerCase().includes('urea') && t.status === 'HIGH');
        if (highCreatinine || highUrea) {
          items.push(
            { type: 'do', text: 'Increase hydration: drink 2.5 - 3.0 liters of plain water daily' },
            { type: 'avoid', text: 'Reduce heavy protein intake (limit red meat, organ meats, and excess dairy)' },
            { type: 'avoid', text: 'Avoid high-sodium foods (processed snacks, canned soups, pickles, papads)' },
            { type: 'limit', text: 'Limit phosphorus-rich foods (dark colas, nuts, processed cheese)' }
          );
        }
        break;
      }

      case "Electrolyte Profile": {
        const highK = profile.tests.some(t => t.test_name.toLowerCase().includes('potassium') && t.status === 'HIGH');
        if (highK) {
          items.push(
            { type: 'avoid', text: 'Avoid high-potassium fruits (bananas, oranges, avocados, tomatoes)' },
            { type: 'avoid', text: 'Avoid salt substitutes containing potassium chloride' },
            { type: 'do', text: 'Leach potassium from vegetables by soaking sliced veggies before cooking' }
          );
        }
        break;
      }

      case "Blood Counts":
      case "Anemia Studies": {
        const lowHb = profile.tests.some(t => t.test_name.toLowerCase().includes('haemoglobin') && t.status === 'LOW');
        if (lowHb) {
          items.push(
            { type: 'do', text: 'Eat iron-rich foods (spinach, beetroot, lentils, pomegranates, dates)' },
            { type: 'do', text: 'Pair iron foods with Vitamin C (lemon juice, oranges) to double absorption' },
            { type: 'avoid', text: 'Avoid drinking tea or coffee within 1 hour of meals (tannins block iron absorption)' }
          );
        }
        break;
      }

      case "Diabetes Monitoring":
      case "Glycemic Profile": {
        items.push(
          { type: 'avoid', text: 'Eliminate refined sugars, sugary beverages, pastries, and white bread' },
          { type: 'do', text: 'Switch to complex carbohydrates with low glycemic index (brown rice, oats, quinoa)' },
          { type: 'do', text: 'Incorporate soluble fiber (chia seeds, flaxseeds, legumes) to stabilize blood sugar' },
          { type: 'limit', text: 'Control fruit portion sizes (choose green apples, berries over mangoes)' }
        );
        break;
      }

      case "Lipid Profile": {
        items.push(
          { type: 'avoid', text: 'Avoid trans-fats, deep-fried fast foods, and hydrogenated oils' },
          { type: 'do', text: 'Include Omega-3 rich foods (walnuts, chia seeds, flaxseeds, fatty fish)' },
          { type: 'limit', text: 'Limit saturated fats (butter, ghee, full-fat palm oil)' }
        );
        break;
      }

      case "Vitamin Profile": {
        const lowVitD = profile.tests.some(t => t.test_name.toLowerCase().includes('vitamin d') && t.status === 'LOW');
        if (lowVitD) {
          items.push(
            { type: 'do', text: 'Get 15-20 minutes of morning sunlight exposure daily' },
            { type: 'do', text: 'Include fortified milk, egg yolks, mushrooms, and Vitamin D fortified foods' }
          );
        }
        break;
      }
    }

    if (items.length > 0) {
      recommendations.push({
        profile: profileName,
        icon: profile.icon,
        items
      });
    }
  }

  return recommendations;
}
