// src/components/BodyMap.tsx
import React from 'react';
import { ProcessedProfile } from '../types';

interface BodyMapProps {
  profiles: Record<string, ProcessedProfile>;
  onSelectProfile: (profileName: string) => void;
}

export const BodyMap: React.FC<BodyMapProps> = ({ profiles, onSelectProfile }) => {
  const getOrganStatus = (profilesList: string[]) => {
    let hasTests = false;
    let isAbnormal = false;
    let primaryProfile = profilesList[0];

    for (const pName of profilesList) {
      const p = profiles[pName];
      if (p) {
        hasTests = true;
        if (p.is_abnormal) {
          isAbnormal = true;
          primaryProfile = pName;
        }
      }
    }
    return { hasTests, isAbnormal, primaryProfile };
  };

  return (
    <div className="bg-gradient-to-b from-slate-50 via-blue-50/30 to-indigo-50/20 rounded-3xl p-5 border border-slate-200/80 shadow-sm relative overflow-hidden my-4">

      {/* Title */}
      <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-200/60">
        <div>
          <h3 className="text-sm font-extrabold text-slate-900 flex items-center gap-1.5">
            <span>🫀</span> Medical Human Anatomy Map
          </h3>
          <p className="text-[11px] text-slate-500 font-medium">
            Anatomically targeted organ evaluation based on laboratory parameters
          </p>
        </div>
        <div className="flex items-center gap-2.5 text-[10px] font-bold bg-white/90 px-3 py-1 rounded-full border border-slate-200 shadow-sm">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Normal
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" /> Abnormal
          </span>
        </div>
      </div>

      {/* Realistic Human Body SVG */}
      <div className="relative min-h-[550px] flex items-center justify-center my-2">
        <svg
          viewBox="0 0 400 700"
          className="w-full max-w-[360px] h-auto"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Background Gradient */}
            <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#F8FAFC" />
              <stop offset="100%" stopColor="#EFF6FF" />
            </linearGradient>

            {/* Realistic Skin Gradients */}
            <radialGradient id="skinHead" cx="50%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#F5D5C0" />
              <stop offset="50%" stopColor="#E8C4A8" />
              <stop offset="100%" stopColor="#D4A882" />
            </radialGradient>

            <linearGradient id="skinTorso" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#E8C4A8" />
              <stop offset="20%" stopColor="#F5D5C0" />
              <stop offset="50%" stopColor="#FAE8DC" />
              <stop offset="80%" stopColor="#F5D5C0" />
              <stop offset="100%" stopColor="#E8C4A8" />
            </linearGradient>

            <linearGradient id="skinLimb" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#D4A882" />
              <stop offset="50%" stopColor="#E8C4A8" />
              <stop offset="100%" stopColor="#D4A882" />
            </linearGradient>

            {/* Muscle Definition */}
            <linearGradient id="muscleDef" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#C4A882" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#D4A882" stopOpacity="0.1" />
            </linearGradient>

            {/* Organ Gradients - Normal */}
            <radialGradient id="organHealthy" cx="40%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#6EE7B7" />
              <stop offset="50%" stopColor="#34D399" />
              <stop offset="100%" stopColor="#059669" />
            </radialGradient>

            {/* Organ Gradients - Abnormal */}
            <radialGradient id="organDiseased" cx="40%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#FCA5A5" />
              <stop offset="50%" stopColor="#F87171" />
              <stop offset="100%" stopColor="#DC2626" />
            </radialGradient>

            {/* Organ Gradients - Warning */}
            <radialGradient id="organWarning" cx="40%" cy="40%" r="60%">
              <stop offset="0%" stopColor="#FCD34D" />
              <stop offset="50%" stopColor="#F59E0B" />
              <stop offset="100%" stopColor="#D97706" />
            </radialGradient>

            {/* Shadow Filter */}
            <filter id="dropShadow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="3" />
              <feOffset dx="2" dy="2" result="offsetblur" />
              <feComponentTransfer>
                <feFuncA type="linear" slope="0.3" />
              </feComponentTransfer>
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Glow Filter */}
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="8" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background */}
          <rect width="400" height="700" fill="url(#bgGrad)" rx="20" />

          {/* === REALISTIC HUMAN BODY === */}

          {/* Head with realistic proportions */}
          <g filter="url(#dropShadow)">
            {/* Skull base */}
            <ellipse cx="200" cy="65" rx="38" ry="45" fill="url(#skinHead)" />
            {/* Jaw definition */}
            <path d="M 172 85 Q 200 105 228 85" fill="none" stroke="#D4A882" strokeWidth="1.5" opacity="0.5" />
            {/* Neck */}
            <path d="M 182 105 Q 200 115 218 105 L 220 135 Q 200 145 180 135 Z" fill="url(#skinTorso)" />
          </g>

          {/* Torso - Realistic anatomy */}
          <g filter="url(#dropShadow)">
            {/* Main torso */}
            <path d="M 145 140 
                     Q 200 130 255 140
                     L 265 180 Q 270 220 265 260
                     L 258 340 Q 252 400 245 440
                     L 240 520 Q 235 600 230 680
                     L 170 680 Q 165 600 160 520
                     L 155 440 Q 148 400 142 340
                     L 135 260 Q 130 220 135 180 Z"
              fill="url(#skinTorso)" stroke="#C4A882" strokeWidth="1" />

            {/* Pectoral muscles */}
            <path d="M 165 170 Q 185 165 200 175 Q 215 165 235 170" fill="none" stroke="#D4A882" strokeWidth="1" opacity="0.4" />
            <path d="M 170 195 Q 185 190 200 198 Q 215 190 230 195" fill="none" stroke="#D4A882" strokeWidth="1" opacity="0.3" />

            {/* Abdominal definition */}
            <path d="M 185 280 L 185 320 M 215 280 L 215 320" stroke="#D4A882" strokeWidth="1" opacity="0.3" />
            <path d="M 175 300 Q 200 305 225 300" fill="none" stroke="#D4A882" strokeWidth="1" opacity="0.3" />
          </g>

          {/* Arms - Realistic */}
          <g filter="url(#dropShadow)">
            {/* Left arm */}
            <path d="M 138 165 Q 105 200 98 280 Q 92 360 105 430" fill="none" stroke="url(#skinLimb)" strokeWidth="28" strokeLinecap="round" />
            {/* Right arm */}
            <path d="M 262 165 Q 295 200 302 280 Q 308 360 295 430" fill="none" stroke="url(#skinLimb)" strokeWidth="28" strokeLinecap="round" />
          </g>

          {/* Legs - Realistic */}
          <g filter="url(#dropShadow)">
            {/* Left leg */}
            <path d="M 175 680 Q 170 720 165 760" fill="none" stroke="url(#skinLimb)" strokeWidth="32" strokeLinecap="round" />
            {/* Right leg */}
            <path d="M 225 680 Q 230 720 235 760" fill="none" stroke="url(#skinLimb)" strokeWidth="32" strokeLinecap="round" />
          </g>

          {/* === INTERNAL ORGANS - REALISTIC RENDERING === */}

          {/* Thyroid */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Thyroid Profile']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer" filter={isAbnormal ? "url(#glow)" : ""}>
                <path d="M 188 125 Q 200 118 212 125 Q 218 135 212 142 Q 200 148 188 142 Q 182 135 188 125 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" opacity="0.9" />
                <ellipse cx="200" cy="132" rx="6" ry="4" fill={isAbnormal ? "#7F1D1D" : "#065F46"} opacity="0.6" />
              </g>
            );
          })()}

          {/* Heart - Realistic shape */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Lipid Profile']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer" filter={isAbnormal ? "url(#glow)" : ""}>
                <path d="M 185 185 
                         C 175 175, 160 185, 165 200
                         C 168 212, 180 225, 200 240
                         C 220 225, 232 212, 235 200
                         C 240 185, 225 175, 215 185
                         C 208 190, 203 195, 200 200
                         C 197 195, 192 190, 185 185 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" />
                {/* Heart vessels */}
                <path d="M 195 180 Q 200 170 205 180 M 190 185 Q 195 175 200 180"
                  fill="none" stroke={isAbnormal ? "#7F1D1D" : "#065F46"} strokeWidth="2" opacity="0.7" />
              </g>
            );
          })()}

          {/* Lungs - Background */}
          <g opacity="0.5">
            <path d="M 205 175 Q 240 170 250 195 Q 255 225 250 255 Q 245 275 230 280 Q 215 275 210 255 Q 205 225 205 175 Z"
              fill="#FCA5A5" stroke="#F87171" strokeWidth="1" opacity="0.4" />
            <path d="M 195 175 Q 160 170 150 195 Q 145 225 150 255 Q 155 275 170 280 Q 185 275 190 255 Q 195 225 195 175 Z"
              fill="#FCA5A5" stroke="#F87171" strokeWidth="1" opacity="0.4" />
          </g>

          {/* Liver - Realistic */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Liver Profile']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer" filter={isAbnormal ? "url(#glow)" : ""}>
                <path d="M 195 250 
                         Q 230 240 255 255
                         Q 270 270 265 295
                         Q 260 315 240 320
                         Q 220 325 205 315
                         Q 195 305 192 285
                         Q 190 265 195 250 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" />
                {/* Liver texture */}
                <path d="M 210 265 Q 230 270 245 285 M 205 280 Q 225 285 240 300"
                  fill="none" stroke={isAbnormal ? "#7F1D1D" : "#065F46"} strokeWidth="1" opacity="0.4" />
              </g>
            );
          })()}

          {/* Stomach */}
          <g opacity="0.6">
            <path d="M 175 260 Q 160 270 155 290 Q 152 315 160 330 Q 172 340 190 335 Q 205 325 202 300 Q 198 275 185 265 Z"
              fill="#FDE68A" stroke="#F59E0B" strokeWidth="1" />
          </g>

          {/* Pancreas */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Diabetes Monitoring']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer" filter={isAbnormal ? "url(#glow)" : ""}>
                <path d="M 180 320 Q 210 312 235 320 Q 245 325 238 332 Q 220 338 195 335 Q 172 332 168 325 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" />
              </g>
            );
          })()}

          {/* Kidneys - Realistic */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Kidney Profile', 'Electrolyte Profile']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer" filter={isAbnormal ? "url(#glow)" : ""}>
                {/* Right kidney */}
                <path d="M 220 355 Q 240 348 252 360 Q 262 378 258 400 Q 252 418 235 422 Q 218 418 215 400 Q 212 380 220 355 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" />
                {/* Left kidney */}
                <path d="M 180 355 Q 160 348 148 360 Q 138 378 142 400 Q 148 418 165 422 Q 182 418 185 400 Q 188 380 180 355 Z"
                  fill={isAbnormal ? "url(#organDiseased)" : "url(#organHealthy)"}
                  stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="1.5" />
                {/* Kidney details */}
                <ellipse cx="240" cy="385" rx="5" ry="10" fill={isAbnormal ? "#7F1D1D" : "#065F46"} opacity="0.5" />
                <ellipse cx="160" cy="385" rx="5" ry="10" fill={isAbnormal ? "#7F1D1D" : "#065F46"} opacity="0.5" />
              </g>
            );
          })()}

          {/* Intestines */}
          <g opacity="0.4">
            <path d="M 165 410 Q 200 400 235 410 Q 250 435 245 460 Q 235 485 200 490 Q 165 485 155 460 Q 150 435 165 410 Z"
              fill="#FED7AA" stroke="#F97316" strokeWidth="1" />
          </g>

          {/* Blood vessels */}
          {(() => {
            const { isAbnormal, primaryProfile } = getOrganStatus(['Blood Counts', 'Differential Counts', 'Anemia Studies', 'Vitamin Profile']);
            return (
              <g onClick={() => onSelectProfile(primaryProfile)} className="cursor-pointer">
                <path d="M 130 200 Q 115 260 108 320" fill="none" stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="3" strokeDasharray="6,3" opacity="0.6" />
                <path d="M 270 200 Q 285 260 292 320" fill="none" stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="3" strokeDasharray="6,3" opacity="0.6" />
              </g>
            );
          })()}

          {/* === HOTSPOT INDICATORS === */}
          {[
            { x: 200, y: 132, profiles: ['Thyroid Profile'], label: 'Thyroid', icon: '🦋' },
            { x: 200, y: 210, profiles: ['Lipid Profile'], label: 'Heart', icon: '🫀' },
            { x: 230, y: 285, profiles: ['Liver Profile'], label: 'Liver', icon: '🥩' },
            { x: 200, y: 325, profiles: ['Diabetes Monitoring'], label: 'Pancreas', icon: '📊' },
            { x: 200, y: 385, profiles: ['Kidney Profile', 'Electrolyte Profile'], label: 'Kidneys', icon: '🫘' },
            { x: 110, y: 260, profiles: ['Blood Counts'], label: 'Blood', icon: '🩸' },
          ].map((spot, i) => {
            const { hasTests, isAbnormal } = getOrganStatus(spot.profiles);
            if (!hasTests) return null;

            return (
              <g key={i} className="cursor-pointer" onClick={() => onSelectProfile(getOrganStatus(spot.profiles).primaryProfile)}>
                {/* Pulsing ring for abnormal */}
                {isAbnormal && (
                  <circle cx={spot.x} cy={spot.y} r="20" fill="none" stroke="#EF4444" strokeWidth="2" opacity="0.6">
                    <animate attributeName="r" values="15;25;15" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Main hotspot */}
                <circle cx={spot.x} cy={spot.y} r="16" fill="white" stroke={isAbnormal ? "#DC2626" : "#059669"} strokeWidth="2.5" filter="url(#dropShadow)" />
                <text x={spot.x} y={spot.y + 5} textAnchor="middle" fontSize="14">{spot.icon}</text>

                {/* Status badge */}
                <circle cx={spot.x + 12} cy={spot.y - 12} r="8" fill={isAbnormal ? "#DC2626" : "#059669"} />
                <text x={spot.x + 12} y={spot.y - 9} textAnchor="middle" fill="white" fontSize="10" fontWeight="bold">
                  {isAbnormal ? '!' : '✓'}
                </text>
              </g>
            );
          })}

        </svg>

        {/* Floating Labels */}
        <div className="absolute inset-0 pointer-events-none">
          {[
            { top: '18%', left: '50%', label: 'Thyroid', profiles: ['Thyroid Profile'] },
            { top: '30%', left: '50%', label: 'Heart', profiles: ['Lipid Profile'] },
            { top: '42%', left: '58%', label: 'Liver', profiles: ['Liver Profile'] },
            { top: '48%', left: '50%', label: 'Pancreas', profiles: ['Diabetes Monitoring'] },
            { top: '56%', left: '50%', label: 'Kidneys', profiles: ['Kidney Profile'] },
            { top: '38%', left: '22%', label: 'Blood', profiles: ['Blood Counts'] },
          ].map((item, i) => {
            const { hasTests, isAbnormal } = getOrganStatus(item.profiles);
            if (!hasTests) return null;

            return (
              <div
                key={i}
                style={{ top: item.top, left: item.left }}
                className={`
                  absolute -translate-x-1/2 px-3 py-1.5 rounded-full text-[10px] font-bold shadow-lg
                  border pointer-events-auto cursor-pointer transition-transform hover:scale-105
                  ${isAbnormal
                    ? 'bg-rose-100 border-rose-300 text-rose-800'
                    : 'bg-white/95 border-emerald-200 text-emerald-800'
                  }
                `}
                onClick={() => onSelectProfile(getOrganStatus(item.profiles).primaryProfile)}
              >
                {item.label}
                <span className={`ml-1 px-1.5 py-0.5 rounded-full text-[9px] ${isAbnormal ? 'bg-rose-200' : 'bg-emerald-100'}`}>
                  {isAbnormal ? 'Abnormal' : 'Normal'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Footer */}
      <div className="mt-2 pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px] font-semibold text-slate-500">
        <span>Click any organ to open dedicated medical profile findings</span>
        <span className="text-blue-600 font-bold">Realistic Anatomy Rendering</span>
      </div>
    </div>
  );
};

export const BodyMapRealistic = BodyMap;
export default BodyMap;