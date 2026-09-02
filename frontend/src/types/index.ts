export interface BiomarkerValue {
  code: string;
  name: string;
  value: number;
  unit: string;
  status: 'OPTIMAL' | 'LOW' | 'HIGH' | 'SLIGHTLY_ELEVATED';
  referenceRange: string;
}

export interface LabReport {
  id: string;
  filename: string;
  uploadDate: string;
  biomarkers: BiomarkerValue[];
  flaggedCount: number;
}
