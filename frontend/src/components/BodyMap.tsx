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
      <div className="relative min-h-[620px] flex items-center justify-center my-2">
        <svg
          viewBox="0 0 560 780"
          className="w-full max-w-[540px] h-auto"
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

            {/* Shadow Filter — single subtle pass, applied once to the whole
                silhouette (not per body-part) so shadows don't stack and
                blur the shape into a soft blob. Reduced blur + opacity vs.
                the original. */}
            <filter id="dropShadow" x="-15%" y="-15%" width="130%" height="130%">
              <feGaussianBlur in="SourceAlpha" stdDeviation="1.5" />
              <feOffset dx="1.5" dy="1.5" result="offsetblur" />
              <feComponentTransfer>
                <feFuncA type="linear" slope="0.22" />
              </feComponentTransfer>
              <feMerge>
                <feMergeNode />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            {/* Glow Filter (unchanged — used only on abnormal organs) */}
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="8" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background */}
          <rect width="560" height="780" fill="url(#bgGrad)" rx="20" />

          {/* === REALISTIC HUMAN BODY SILHOUETTE (CENTERED) === */}
          <g transform="translate(80, 0)">
            <g filter="url(#dropShadow)">

              {/* Head */}
              <ellipse cx="200" cy="65" rx="37" ry="44" fill="url(#skinHead)" />
              <path d="M 172 86 Q 200 106 228 86" fill="none" stroke="#D4A882" strokeWidth="1.5" opacity="0.5" />
              {/* Neck */}
              <path d="M 183 102 Q 200 112 217 102 L 219 140 Q 200 150 181 140 Z" fill="url(#skinTorso)" />

              {/* Torso + pelvis + both legs + feet — one continuous outline */}
              <path
                d="M140,150
                 Q130,170 138,200
                 Q145,225 148,250
                 Q152,270 158,290
                 Q150,320 145,355
                 Q140,390 144,415
                 Q147,430 150,440
                 Q145,460 144,475
                 Q140,520 144,565
                 Q147,610 152,650
                 Q155,675 158,700
                 Q152,715 150,728
                 Q155,738 165,743
                 Q172,745 178,736
                 Q180,720 176,702
                 Q182,660 186,615
                 Q190,560 192,510
                 Q195,485 200,472
                 Q205,485 208,510
                 Q210,560 214,615
                 Q218,660 224,702
                 Q220,720 222,736
                 Q228,745 235,743
                 Q245,738 250,728
                 Q248,715 242,700
                 Q245,675 248,650
                 Q253,610 256,565
                 Q260,520 256,475
                 Q255,460 250,440
                 Q253,430 256,415
                 Q260,390 255,355
                 Q250,320 242,290
                 Q248,270 252,250
                 Q255,225 262,200
                 Q270,170 260,150
                 Q235,140 218,140
                 L182,140
                 Q165,140 140,150 Z"
                fill="url(#skinTorso)"
                stroke="#C4A882"
                strokeWidth="1"
              />

              {/* Left arm — tapered filled shape, not a thick round stroke */}
              <path
                d="M148,155
                 Q120,165 112,200
                 Q106,240 110,280
                 Q113,320 118,355
                 Q120,375 128,388
                 Q136,392 140,382
                 Q136,350 133,315
                 Q130,275 133,235
                 Q136,200 150,175
                 Q155,165 148,155 Z"
                fill="url(#skinLimb)"
                stroke="#C4A882"
                strokeWidth="1"
              />

              {/* Right arm */}
              <path
                d="M252,155
                 Q280,165 288,200
                 Q294,240 290,280
                 Q287,320 282,355
                 Q280,375 272,388
                 Q264,392 260,382
                 Q264,350 267,315
                 Q270,275 267,235
                 Q264,200 250,175
                 Q245,165 252,155 Z"
                fill="url(#skinLimb)"
                stroke="#C4A882"
                strokeWidth="1"
              />

              {/* Abdominal / chest definition (kept from original, positions
                still line up with the new torso outline) */}
              <path d="M 165 170 Q 185 165 200 175 Q 215 165 235 170" fill="none" stroke="#D4A882" strokeWidth="1" opacity="0.4" />
              <path d="M 185 300 L 185 340 M 215 300 L 215 340" stroke="#D4A882" strokeWidth="1" opacity="0.3" />
              <path d="M 175 320 Q 200 325 225 320" fill="none" stroke="#D4A882" strokeWidth="1" opacity="0.3" />
            </g>

            {/* === INTERNAL ORGANS - REALISTIC RENDERING === */}
            {/* Unchanged below: same organ shapes, same profile-name arrays,
              same onSelectProfile wiring, same hotspot/label logic. */}

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
          </g>

          {/* === EXTERNAL CALLOUTS & LEADER LINES (OUTSIDE THE BODY) === */}
          {[
            {
              label: 'Thyroid',
              icon: '🦋',
              profiles: ['Thyroid Profile'],
              organPoint: { x: 280, y: 132 },
              linePath: 'M 264 132 L 205 116 L 160 116',
              card: { x: 14, y: 95, w: 146, h: 42 }
            },
            {
              label: 'Heart',
              icon: '🫀',
              profiles: ['Lipid Profile'],
              organPoint: { x: 280, y: 198 },
              linePath: 'M 296 198 L 350 181 L 400 181',
              card: { x: 400, y: 160, w: 146, h: 42 }
            },
            {
              label: 'Blood System',
              icon: '🩸',
              profiles: ['Blood Counts', 'Differential Counts', 'Anemia Studies', 'Vitamin Profile'],
              organPoint: { x: 192, y: 245 },
              linePath: 'M 176 245 L 160 245',
              card: { x: 14, y: 225, w: 146, h: 42 }
            },
            {
              label: 'Liver',
              icon: '🥩',
              profiles: ['Liver Profile'],
              organPoint: { x: 315, y: 278 },
              linePath: 'M 331 278 L 365 286 L 400 286',
              card: { x: 400, y: 265, w: 146, h: 42 }
            },
            {
              label: 'Pancreas',
              icon: '📊',
              profiles: ['Diabetes Monitoring'],
              organPoint: { x: 280, y: 325 },
              linePath: 'M 264 325 L 210 351 L 160 351',
              card: { x: 14, y: 330, w: 146, h: 42 }
            },
            {
              label: 'Kidneys',
              icon: '🫘',
              profiles: ['Kidney Profile', 'Electrolyte Profile'],
              organPoint: { x: 280, y: 388 },
              linePath: 'M 296 388 L 360 391 L 400 391',
              card: { x: 400, y: 370, w: 146, h: 42 }
            }
          ].map((item) => {
            const { hasTests, isAbnormal, primaryProfile } = getOrganStatus(item.profiles);
            if (!hasTests) return null;

            return (
              <g
                key={item.label}
                className="cursor-pointer transition-transform duration-200 hover:scale-[1.02]"
                onClick={() => primaryProfile && onSelectProfile(primaryProfile)}
              >
                {/* Pointer / Leader Line connecting organ icon to external text card */}
                <path
                  d={item.linePath}
                  fill="none"
                  stroke={isAbnormal ? '#EF4444' : '#10B981'}
                  strokeWidth="1.75"
                  strokeDasharray="4,2"
                  opacity="0.9"
                />

                {/* === CIRCULAR ORGAN ICON BADGE (INSIDE HUMAN BODY) === */}
                <g filter="url(#dropShadow)">
                  {/* Radar pulse for abnormal organs */}
                  {isAbnormal && (
                    <circle
                      cx={item.organPoint.x}
                      cy={item.organPoint.y}
                      r="16"
                      fill="none"
                      stroke="#EF4444"
                      strokeWidth="2"
                      opacity="0.7"
                    >
                      <animate attributeName="r" values="16;22;16" dur="2.4s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.7;0;0.7" dur="2.4s" repeatCount="indefinite" />
                    </circle>
                  )}

                  {/* White circular badge on organ */}
                  <circle
                    cx={item.organPoint.x}
                    cy={item.organPoint.y}
                    r="15"
                    fill="#FFFFFF"
                    stroke={isAbnormal ? '#EF4444' : '#10B981'}
                    strokeWidth="2"
                  />

                  {/* Organ icon inside body */}
                  <text
                    x={item.organPoint.x}
                    y={item.organPoint.y + 0.5}
                    fontSize="14"
                    textAnchor="middle"
                    dominantBaseline="central"
                  >
                    {item.icon}
                  </text>

                  {/* Mini status indicator badge at top-right of the organ icon */}
                  <circle
                    cx={item.organPoint.x + 10}
                    cy={item.organPoint.y - 10}
                    r="6.5"
                    fill={isAbnormal ? '#DC2626' : '#059669'}
                    stroke="#FFFFFF"
                    strokeWidth="1.5"
                  />
                  <text
                    x={item.organPoint.x + 10}
                    y={item.organPoint.y - 9.5}
                    fontSize="8.5"
                    fontWeight="900"
                    fill="#FFFFFF"
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontFamily="system-ui, -apple-system, sans-serif"
                  >
                    {isAbnormal ? '!' : '✓'}
                  </text>
                </g>

                {/* Callout Card Box outside the body */}
                <rect
                  x={item.card.x}
                  y={item.card.y}
                  width={item.card.w}
                  height={item.card.h}
                  rx="12"
                  fill="white"
                  stroke={isAbnormal ? '#FCA5A5' : '#A7F3D0'}
                  strokeWidth="1.5"
                  filter="url(#dropShadow)"
                />

                {/* Icon */}
                <text
                  x={item.card.x + 10}
                  y={item.card.y + 26}
                  fontSize="15"
                >
                  {item.icon}
                </text>

                {/* Organ Label */}
                <text
                  x={item.card.x + 32}
                  y={item.card.y + 18}
                  fontSize="11"
                  fontWeight="800"
                  fill="#0F172A"
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {item.label}
                </text>

                {/* Status Pill Badge */}
                <rect
                  x={item.card.x + 32}
                  y={item.card.y + 23}
                  width={isAbnormal ? 58 : 50}
                  height="14"
                  rx="7"
                  fill={isAbnormal ? '#FEE2E2' : '#D1FAE5'}
                  stroke={isAbnormal ? '#FCA5A5' : '#A7F3D0'}
                  strokeWidth="0.75"
                />
                <text
                  x={item.card.x + 37}
                  y={item.card.y + 33.5}
                  fontSize="8.5"
                  fontWeight="800"
                  fill={isAbnormal ? '#991B1B' : '#065F46'}
                  fontFamily="system-ui, -apple-system, sans-serif"
                >
                  {isAbnormal ? 'ABNORMAL' : 'NORMAL'}
                </text>
              </g>
            );
          })}
        </svg>
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