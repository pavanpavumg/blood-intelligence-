// src/components/BodyMap.tsx
'use client';

import React, { useState } from 'react';
import dynamic from 'next/dynamic';
import { ProcessedProfile } from '../types';
import { AnatomyGender } from './Anatomy3D';
import './anatomy/anatomy.css';

// Dynamic import with SSR disabled for Three.js WebGL canvas compatibility
const Anatomy3D = dynamic(() => import('./Anatomy3D'), {
  ssr: false,
  loading: () => (
    <div className="anatomy-3d-wrapper flex items-center justify-center">
      <div className="anatomy-loader">
        <div className="anatomy-loader-ring" />
        <span>Loading 3D anatomy...</span>
      </div>
    </div>
  ),
});

interface BodyMapProps {
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (profileName: string) => void;
  gender?: AnatomyGender;
}

export const BodyMap: React.FC<BodyMapProps> = ({
  profiles,
  onSelectProfile,
  gender = 'male',
}) => {
  const [selectedGender, setSelectedGender] =
    useState<AnatomyGender>(gender);

  const getOrganStatus = (profileNames: string[]) => {
    let hasTests = false;
    let isAbnormal = false;
    let primaryProfile = profileNames[0] ?? '';

    for (const profileName of profileNames) {
      const profile = profiles[profileName];
      if (!profile) {
        continue;
      }

      hasTests = true;

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
  };

  const genderProfile =
    selectedGender === 'male'
      ? getOrganStatus([
          'Male Reproductive Profile',
          'Prostate Profile',
          'Reproductive Profile',
        ])
      : getOrganStatus([
          'Female Reproductive Profile',
          'Gynecology Profile',
          'Reproductive Profile',
        ]);

  return (
    <section
      className="
        relative
        my-4
        overflow-hidden
        rounded-3xl
        border
        border-slate-200/80
        bg-gradient-to-b
        from-slate-50
        via-blue-50/30
        to-indigo-50/20
        p-4
        shadow-sm
      "
    >
      {/* ======================================================
          HEADER
      ====================================================== */}
      <div
        className="
          mb-3
          flex
          flex-col
          gap-3
          border-b
          border-slate-200/60
          pb-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <h3
            className="
              flex
              items-center
              gap-2
              text-sm
              font-extrabold
              text-slate-900
            "
          >
            <span className="text-lg">🫀</span>
            Medical 3D Anatomy
          </h3>

          <p
            className="
              mt-1
              text-[11px]
              font-medium
              text-slate-500
            "
          >
            Interactive organ visualization based on laboratory findings
          </p>
        </div>

        {/* ====================================================
            GENDER SWITCH
        ==================================================== */}
        <div
          className="
            inline-flex
            self-start
            rounded-full
            border
            border-slate-200
            bg-white/90
            p-1
            shadow-sm
            sm:self-auto
          "
          role="group"
          aria-label="Select anatomy gender"
        >
          <button
            type="button"
            aria-pressed={selectedGender === 'male'}
            onClick={() => setSelectedGender('male')}
            className={`
              rounded-full
              px-4
              py-1.5
              text-[11px]
              font-bold
              transition-all
              duration-200
              focus:outline-none
              focus:ring-2
              focus:ring-blue-400/50
              ${
                selectedGender === 'male'
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }
            `}
          >
            ♂ Male
          </button>

          <button
            type="button"
            aria-pressed={selectedGender === 'female'}
            onClick={() => setSelectedGender('female')}
            className={`
              rounded-full
              px-4
              py-1.5
              text-[11px]
              font-bold
              transition-all
              duration-200
              focus:outline-none
              focus:ring-2
              focus:ring-pink-400/50
              ${
                selectedGender === 'female'
                  ? 'bg-pink-600 text-white shadow-sm'
                  : 'text-slate-600 hover:bg-slate-100'
              }
            `}
          >
            ♀ Female
          </button>
        </div>
      </div>

      {/* ======================================================
          STATUS LEGEND
      ====================================================== */}
      <div
        className="
          mb-2
          flex
          justify-center
          gap-4
          text-[10px]
          font-bold
          text-slate-600
          sm:justify-end
        "
      >
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
          Normal
        </span>

        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-rose-500" />
          Abnormal
        </span>
      </div>

      {/* ======================================================
          3D ANATOMY
      ====================================================== */}
      <Anatomy3D
        gender={selectedGender}
        profiles={profiles}
        onSelectProfile={onSelectProfile}
        className="w-full"
      />

      {/* ======================================================
          REPRODUCTIVE PROFILE INFORMATION
      ====================================================== */}
      {genderProfile.hasTests && (
        <div
          className="
            mt-3
            rounded-2xl
            border
            border-slate-200
            bg-white/80
            px-4
            py-3
            text-xs
            shadow-sm
          "
        >
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="font-bold text-slate-800">
                {selectedGender === 'female'
                  ? 'Female reproductive profile'
                  : 'Male reproductive profile'}
              </div>

              <div className="mt-0.5 text-[10px] text-slate-500">
                Laboratory profile available
              </div>
            </div>

            <button
              type="button"
              onClick={() =>
                onSelectProfile(genderProfile.primaryProfile)
              }
              className={`
                rounded-full
                px-3
                py-1.5
                text-[10px]
                font-bold
                transition
                ${
                  genderProfile.isAbnormal
                    ? 'bg-rose-100 text-rose-700 hover:bg-rose-200'
                    : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
                }
              `}
            >
              {genderProfile.isAbnormal
                ? 'View findings'
                : 'View profile'}
            </button>
          </div>
        </div>
      )}

      {/* ======================================================
          FOOTER
      ====================================================== */}
      <div
        className="
          mt-3
          flex
          flex-col
          items-center
          justify-between
          gap-2
          border-t
          border-slate-200/60
          pt-3
          text-[10px]
          font-semibold
          text-slate-500
          sm:flex-row
        "
      >
        <span>
          Drag to rotate • Scroll to zoom • Click an organ
        </span>

        <span className="font-bold text-blue-600">
          {selectedGender === 'male'
            ? 'Male 3D Anatomy'
            : 'Female 3D Anatomy'}
        </span>
      </div>
    </section>
  );
};

export const BodyMapRealistic = BodyMap;

export default BodyMap;