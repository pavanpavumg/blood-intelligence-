export type StatusType = 'NORMAL' | 'HIGH' | 'LOW' | 'UNKNOWN';
export type FlagType = 'NONE' | 'RED_FLAG' | 'REVIEW_REQUIRED';

export interface ReferenceRange {
  low: number | null;
  high: number | null;
  raw: string;
}

export interface SourceTrace {
  raw_test_name: string;
  raw_value: string;
}

export interface TestItem {
  test_name: string;
  raw_test_name: string;
  loinc_code: string | null;
  value: number;
  raw_unit: string | null;
  reference_range: ReferenceRange;
  status: StatusType;
  flag: FlagType;
  source_trace?: SourceTrace;
}

export interface ReportMetadata {
  report_id: string;
  report_date: string;
  lab_name: string | null;
}

export interface PatientInfo {
  patient_id: string;
  name: string;
  age: number;
  gender: 'Male' | 'Female' | 'Other';
}

export interface CompletenessInfo {
  expected_count: number;
  extracted_count: number;
  missing_tests: string[];
  unexpected_tests: string[];
  complete: boolean;
}

export interface LabReportData {
  schema_version: string;
  report: ReportMetadata;
  patient: PatientInfo;
  tests: TestItem[];
  warnings: string[];
  completeness?: CompletenessInfo;
}

export interface LabReportResponse {
  report_id: string;
  status: 'VALIDATED' | 'VALIDATED_WITH_WARNINGS' | 'FAILED';
  data: LabReportData;
}

// Profile Mapping Types
export interface ProfileConfig {
  name: string;
  tests: string[];
  icon: string;
  organ: string | null;
  description: string;
}

export interface ProcessedProfile {
  name: string;
  icon: string;
  organ: string | null;
  description: string;
  tests: TestItem[];
  normal_count: number;
  abnormal_count: number;
  is_abnormal: boolean;
}

export interface WellnessScoreResult {
  score: number;
  label: 'Excellent' | 'Good' | 'Fair' | 'Poor';
  color: 'green' | 'light-green' | 'amber' | 'red';
  total: number;
  normal: number;
  abnormal: number;
  redFlags: number;
}

export interface RiskFactor {
  id: string;
  name: string;
  severity: 'HIGH' | 'MODERATE' | 'LOW';
  advice: string;
  tests: string[];
}

export interface DietItem {
  type: 'do' | 'avoid' | 'limit';
  text: string;
}

export interface DietGroup {
  profile: string;
  icon: string;
  items: DietItem[];
}

export interface TestExplanation {
  what: string;
  function: string;
  meaning: string;
  high_meaning?: string;
  low_meaning?: string;
}
