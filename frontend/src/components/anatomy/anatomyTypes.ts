import { ProcessedProfile } from '../../types';

export type AnatomyGender = 'male' | 'female';

export interface OrganDefinition {
  id: string;
  label: string;
  meshNames: string[];
  profiles: string[];
  color?: string;
}

export interface Anatomy3DProps {
  gender: AnatomyGender;
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (profileName: string) => void;
  className?: string;
}
