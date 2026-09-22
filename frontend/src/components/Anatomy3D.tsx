'use client';

import React, {
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  Component,
  ErrorInfo,
  ReactNode
} from 'react';

import * as THREE from 'three';

import {
  Canvas,
  ThreeEvent,
} from '@react-three/fiber';

import {
  Environment,
  Html,
  OrbitControls,
  useGLTF,
} from '@react-three/drei';

import { ProcessedProfile } from '../types';

import './anatomy/anatomy.css';

/* ============================================================
   TYPES
============================================================ */

export type AnatomyGender = 'male' | 'female';

export interface Anatomy3DProps {
  gender: AnatomyGender;
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (profileName: string) => void;
  className?: string;
}

interface OrganDefinition {
  id: string;
  label: string;
  meshNames: string[];
  profiles: string[];
  color?: string;
}

/* ============================================================
   ORGAN DEFINITIONS
============================================================ */

const ORGAN_DEFINITIONS: OrganDefinition[] = [
  {
    id: 'thyroid',
    label: 'Thyroid',
    meshNames: [
      'Thyroid',
      'thyroid',
      'Thyroid_Gland',
      'thyroid_gland',
    ],
    profiles: ['Thyroid Profile'],
    color: '#22c55e',
  },
  {
    id: 'heart',
    label: 'Heart',
    meshNames: [
      'Heart',
      'heart',
      'Heart_001',
      'heart_mesh',
    ],
    profiles: ['Lipid Profile'],
    color: '#ef4444',
  },
  {
    id: 'left-lung',
    label: 'Left Lung',
    meshNames: [
      'LeftLung',
      'left_lung',
      'Left_Lung',
      'Lung_L',
    ],
    profiles: [],
    color: '#60a5fa',
  },
  {
    id: 'right-lung',
    label: 'Right Lung',
    meshNames: [
      'RightLung',
      'right_lung',
      'Right_Lung',
      'Lung_R',
    ],
    profiles: [],
    color: '#60a5fa',
  },
  {
    id: 'liver',
    label: 'Liver',
    meshNames: [
      'Liver',
      'liver',
      'Liver_001',
    ],
    profiles: ['Liver Profile'],
    color: '#f59e0b',
  },
  {
    id: 'stomach',
    label: 'Stomach',
    meshNames: [
      'Stomach',
      'stomach',
    ],
    profiles: [],
    color: '#f97316',
  },
  {
    id: 'pancreas',
    label: 'Pancreas',
    meshNames: [
      'Pancreas',
      'pancreas',
    ],
    profiles: ['Diabetes Monitoring'],
    color: '#facc15',
  },
  {
    id: 'left-kidney',
    label: 'Left Kidney',
    meshNames: [
      'LeftKidney',
      'left_kidney',
      'Left_Kidney',
      'Kidney_L',
    ],
    profiles: [
      'Kidney Profile',
      'Electrolyte Profile',
    ],
    color: '#a855f7',
  },
  {
    id: 'right-kidney',
    label: 'Right Kidney',
    meshNames: [
      'RightKidney',
      'right_kidney',
      'Right_Kidney',
      'Kidney_R',
    ],
    profiles: [
      'Kidney Profile',
      'Electrolyte Profile',
    ],
    color: '#a855f7',
  },
  {
    id: 'intestines',
    label: 'Intestines',
    meshNames: [
      'Intestines',
      'intestines',
      'SmallIntestine',
      'LargeIntestine',
    ],
    profiles: [],
    color: '#fb923c',
  },
  {
    id: 'uterus',
    label: 'Uterus',
    meshNames: [
      'Uterus',
      'uterus',
      'Uterus_001',
    ],
    profiles: [
      'Female Reproductive Profile',
      'Reproductive Profile',
      'Gynecology Profile',
    ],
    color: '#ec4899',
  },
  {
    id: 'left-ovary',
    label: 'Left Ovary',
    meshNames: [
      'LeftOvary',
      'left_ovary',
      'Left_Ovary',
    ],
    profiles: [
      'Female Reproductive Profile',
      'Reproductive Profile',
      'Gynecology Profile',
    ],
    color: '#f472b6',
  },
  {
    id: 'right-ovary',
    label: 'Right Ovary',
    meshNames: [
      'RightOvary',
      'right_ovary',
      'Right_Ovary',
    ],
    profiles: [
      'Female Reproductive Profile',
      'Reproductive Profile',
      'Gynecology Profile',
    ],
    color: '#f472b6',
  },
  {
    id: 'prostate',
    label: 'Prostate',
    meshNames: [
      'Prostate',
      'prostate',
      'Prostate_Gland',
    ],
    profiles: [
      'Prostate Profile',
      'Male Reproductive Profile',
      'Reproductive Profile',
    ],
    color: '#60a5fa',
  },
  {
    id: 'brain',
    label: 'Brain',
    meshNames: [
      'Brain',
      'brain',
      'Brain_001',
    ],
    profiles: [],
    color: '#c084fc',
  },
];

/* ============================================================
   PROFILE HELPERS
============================================================ */

function getProfileStatus(
  profiles: Record<string, ProcessedProfile>,
  profileNames: string[]
) {
  let hasTests = false;
  let isAbnormal = false;
  let primaryProfile = '';

  for (const profileName of profileNames) {
    const profile = profiles[profileName];
    if (!profile) {
      continue;
    }

    hasTests = true;

    if (!primaryProfile) {
      primaryProfile = profileName;
    }

    if (profile.is_abnormal) {
      isAbnormal = true;
      primaryProfile = profileName;
    }
  }

  return {
    hasTests,
    isAbnormal,
    primaryProfile,
  };
}

/* ============================================================
   FIND ORGAN
============================================================ */

function findOrganDefinition(
  meshName: string
): OrganDefinition | undefined {
  const normalized = meshName.toLowerCase();

  return ORGAN_DEFINITIONS.find((organ) =>
    organ.meshNames.some(
      (name) =>
        name.toLowerCase() === normalized
    )
  );
}

/* ============================================================
   3D MODEL PROPS
============================================================ */

interface AnatomyModelProps {
  gender: AnatomyGender;
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (
    profileName: string
  ) => void;
  onHover: (
    organ: OrganDefinition | null
  ) => void;
}

/* ============================================================
   3D MODEL COMPONENT
============================================================ */

const AnatomyModel: React.FC<AnatomyModelProps> = ({
  gender,
  profiles,
  onSelectProfile,
  onHover,
}) => {
  const modelPath =
    gender === 'male'
      ? '/models/anatomy/male-anatomy.glb'
      : '/models/anatomy/female-anatomy.glb';

  const { scene } = useGLTF(modelPath);

  const clonedScene = useMemo(
    () => scene.clone(true),
    [scene]
  );

  const originalMaterials = useRef<
    Map<string, THREE.Material>
  >(new Map());

  const hoveredObject = useRef<
    THREE.Object3D | null
  >(null);

  /* ----------------------------------------------------------
     Prepare meshes
  ---------------------------------------------------------- */

  useEffect(() => {
    clonedScene.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) {
        return;
      }

      object.castShadow = true;
      object.receiveShadow = true;

      object.userData.originalMaterial =
        object.material;

      originalMaterials.current.set(
        object.uuid,
        object.material as THREE.Material
      );

      object.userData.originalEmissive =
        object.material instanceof THREE.MeshStandardMaterial
          ? object.material.emissive.clone()
          : new THREE.Color('#000000');

      object.userData.originalEmissiveIntensity =
        object.material instanceof THREE.MeshStandardMaterial
          ? object.material.emissiveIntensity
          : 0;
    });
  }, [clonedScene]);

  /* ----------------------------------------------------------
     Apply status colors
  ---------------------------------------------------------- */

  useEffect(() => {
    clonedScene.traverse((object) => {
      if (!(object instanceof THREE.Mesh)) {
        return;
      }

      const organ = findOrganDefinition(
        object.name
      );

      if (!organ) {
        return;
      }

      if (
        !(object.material instanceof THREE.MeshStandardMaterial)
      ) {
        return;
      }

      const material = object.material;

      const status = getProfileStatus(
        profiles,
        organ.profiles
      );

      material.emissiveIntensity = 0;

      if (status.isAbnormal) {
        material.emissive.set('#ef4444');
        material.emissiveIntensity = 0.55;
      } else if (status.hasTests) {
        material.emissive.set('#22c55e');
        material.emissiveIntensity = 0.25;
      } else {
        material.emissive.set('#000000');
        material.emissiveIntensity = 0;
      }
    });
  }, [clonedScene, profiles]);

  /* ----------------------------------------------------------
     Hover
  ---------------------------------------------------------- */

  const handlePointerOver = (
    event: ThreeEvent<PointerEvent>
  ) => {
    event.stopPropagation();
    const object = event.object;
    const organ = findOrganDefinition(object.name);

    if (!organ) {
      return;
    }

    hoveredObject.current = object;
    onHover(organ);
    document.body.style.cursor = 'pointer';

    if (
      object instanceof THREE.Mesh &&
      object.material instanceof THREE.MeshStandardMaterial
    ) {
      object.material.emissive.set('#38bdf8');
      object.material.emissiveIntensity = 0.45;
    }
  };

  /* ----------------------------------------------------------
     Hover leave
  ---------------------------------------------------------- */

  const handlePointerOut = (
    event: ThreeEvent<PointerEvent>
  ) => {
    event.stopPropagation();
    const object = event.object;
    const organ = findOrganDefinition(object.name);

    if (!organ) {
      return;
    }

    document.body.style.cursor = 'default';
    onHover(null);

    const status = getProfileStatus(
      profiles,
      organ.profiles
    );

    if (
      object instanceof THREE.Mesh &&
      object.material instanceof THREE.MeshStandardMaterial
    ) {
      if (status.isAbnormal) {
        object.material.emissive.set('#ef4444');
        object.material.emissiveIntensity = 0.55;
      } else if (status.hasTests) {
        object.material.emissive.set('#22c55e');
        object.material.emissiveIntensity = 0.25;
      } else {
        object.material.emissive.set('#000000');
        object.material.emissiveIntensity = 0;
      }
    }

    hoveredObject.current = null;
  };

  /* ----------------------------------------------------------
     Click
  ---------------------------------------------------------- */

  const handleClick = (
    event: ThreeEvent<MouseEvent>
  ) => {
    event.stopPropagation();
    const object = event.object;
    const organ = findOrganDefinition(object.name);

    if (!organ) {
      return;
    }

    const status = getProfileStatus(
      profiles,
      organ.profiles
    );

    if (status.hasTests && status.primaryProfile) {
      onSelectProfile(status.primaryProfile);
    }
  };

  return (
    <group
      rotation={[0, 0, 0]}
      position={[0, -1.25, 0]}
      scale={2.6}
    >
      <primitive
        object={clonedScene}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onClick={handleClick}
      />
    </group>
  );
};

/* ============================================================
   LIGHTWEIGHT MODEL LOADER
============================================================ */

const ModelLoader: React.FC = () => {
  return (
    <Html center>
      <div className="anatomy-loader">
        <div className="anatomy-loader-ring" />
        <span>Loading 3D anatomy...</span>
      </div>
    </Html>
  );
};

/* ============================================================
   ERROR BOUNDARY FOR MODEL NOT FOUND
============================================================ */

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

class ModelErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(_: Error): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.warn('3D Anatomy Model could not be loaded from /models/anatomy/*.glb:', error.message);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

/* ============================================================
   FALLBACK PROCEDURAL 3D MESH VIEW WHEN GLB IS NOT YET ADDED
============================================================ */

const ProceduralAnatomyView: React.FC<{
  gender: AnatomyGender;
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (name: string) => void;
  onHover: (organ: OrganDefinition | null) => void;
}> = ({ gender, profiles, onSelectProfile, onHover }) => {
  return (
    <group position={[0, -0.2, 0]}>
      {/* Head */}
      <mesh position={[0, 1.8, 0]}>
        <sphereGeometry args={[0.3, 32, 32]} />
        <meshStandardMaterial color="#E8C4A8" roughness={0.4} />
      </mesh>

      {/* Torso */}
      <mesh position={[0, 0.8, 0]}>
        <cylinderGeometry args={[gender === 'male' ? 0.45 : 0.38, gender === 'male' ? 0.38 : 0.48, 1.4, 32]} />
        <meshStandardMaterial color="#E8C4A8" transparent opacity={0.35} roughness={0.5} />
      </mesh>

      {/* Stylized Internal Organs */}
      {ORGAN_DEFINITIONS.filter(o => o.profiles.length > 0).map((organ, idx) => {
        const status = getProfileStatus(profiles, organ.profiles);
        const yPos = organ.id === 'thyroid' ? 1.4 :
                     organ.id === 'heart' ? 1.05 :
                     organ.id === 'liver' ? 0.75 :
                     organ.id === 'pancreas' ? 0.6 :
                     organ.id.includes('kidney') ? 0.4 :
                     0.1;
        const xPos = organ.id === 'liver' ? 0.18 :
                     organ.id === 'heart' ? -0.06 :
                     organ.id === 'left-kidney' ? -0.22 :
                     organ.id === 'right-kidney' ? 0.22 :
                     0;
        const zPos = 0.08;

        const color = status.isAbnormal ? '#ef4444' : status.hasTests ? '#22c55e' : '#94a3b8';

        return (
          <mesh
            key={organ.id}
            position={[xPos, yPos, zPos]}
            onPointerOver={(e) => {
              e.stopPropagation();
              onHover(organ);
              document.body.style.cursor = 'pointer';
            }}
            onPointerOut={(e) => {
              e.stopPropagation();
              onHover(null);
              document.body.style.cursor = 'default';
            }}
            onClick={(e) => {
              e.stopPropagation();
              if (status.hasTests && status.primaryProfile) {
                onSelectProfile(status.primaryProfile);
              }
            }}
          >
            <sphereGeometry args={[organ.id === 'heart' || organ.id === 'liver' ? 0.16 : 0.11, 24, 24]} />
            <meshStandardMaterial
              color={color}
              emissive={color}
              emissiveIntensity={status.isAbnormal ? 0.5 : 0.25}
              roughness={0.2}
            />
          </mesh>
        );
      })}
    </group>
  );
};

/* ============================================================
   MAIN COMPONENT
============================================================ */

export const Anatomy3D: React.FC<Anatomy3DProps> = ({
  gender,
  profiles,
  onSelectProfile,
  className = '',
}) => {
  const [hoveredOrgan, setHoveredOrgan] =
    useState<OrganDefinition | null>(null);

  const modelPath =
    gender === 'male'
      ? '/models/anatomy/male-anatomy.glb'
      : '/models/anatomy/female-anatomy.glb';

  return (
    <div className={`anatomy-3d-wrapper ${className}`}>
      {/* ------------------------------------------------------
          Canvas
      ------------------------------------------------------ */}
      <Canvas
        shadows
        camera={{
          position: [0, 0.3, 5.8],
          fov: 35,
          near: 0.1,
          far: 100,
        }}
        dpr={[1, 2]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: 'high-performance',
        }}
      >
        <color attach="background" args={['#f8fafc']} />

        {/* Ambient lighting */}
        <ambientLight intensity={1.5} />

        {/* Main key light */}
        <directionalLight
          position={[4, 6, 5]}
          intensity={3}
          castShadow
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
        />

        {/* Fill light */}
        <directionalLight
          position={[-4, 2, 3]}
          intensity={1.4}
        />

        {/* Rim light */}
        <pointLight
          position={[0, 3, -3]}
          intensity={1.5}
          color="#60a5fa"
        />

        <Suspense fallback={<ModelLoader />}>
          <ModelErrorBoundary
            fallback={
              <ProceduralAnatomyView
                gender={gender}
                profiles={profiles}
                onSelectProfile={onSelectProfile}
                onHover={setHoveredOrgan}
              />
            }
          >
            <AnatomyModel
              key={modelPath}
              gender={gender}
              profiles={profiles}
              onSelectProfile={onSelectProfile}
              onHover={setHoveredOrgan}
            />
          </ModelErrorBoundary>

          <Environment
            preset="studio"
            environmentIntensity={0.35}
          />
        </Suspense>

        {/* ----------------------------------------------------
            Controls
        ---------------------------------------------------- */}
        <OrbitControls
          enablePan={false}
          enableZoom
          enableRotate
          minDistance={3}
          maxDistance={8}
          minPolarAngle={Math.PI / 4}
          maxPolarAngle={Math.PI - Math.PI / 4}
          dampingFactor={0.08}
          enableDamping
        />
      </Canvas>

      {/* ------------------------------------------------------
          Hover information
      ------------------------------------------------------ */}
      {hoveredOrgan && (
        <div className="anatomy-hover-card">
          <div className="anatomy-hover-title">
            {hoveredOrgan.label}
          </div>

          {(() => {
            const status = getProfileStatus(
              profiles,
              hoveredOrgan.profiles
            );

            if (!status.hasTests) {
              return (
                <div className="anatomy-hover-muted">
                  No laboratory profile available
                </div>
              );
            }

            return (
              <div
                className={
                  status.isAbnormal
                    ? 'anatomy-status abnormal'
                    : 'anatomy-status normal'
                }
              >
                <span className="anatomy-status-dot" />
                {status.isAbnormal
                  ? 'Abnormal findings'
                  : 'Within reported range'}
              </div>
            );
          })()}
        </div>
      )}

      {/* ------------------------------------------------------
          Controls hint
      ------------------------------------------------------ */}
      <div className="anatomy-controls-hint">
        <span>🖱 Drag</span>
        <span>Scroll to zoom</span>
        <span>Click an organ</span>
      </div>
    </div>
  );
};

/* ============================================================
   PRELOAD MODELS (OPTIONAL / NON-BLOCKING)
============================================================ */

if (typeof window !== 'undefined') {
  try {
    useGLTF.preload('/models/anatomy/male-anatomy.glb');
    useGLTF.preload('/models/anatomy/female-anatomy.glb');
  } catch (_) {}
}

export default Anatomy3D;
