import React, { useState } from 'react';
import { Utensils, ChevronDown, ChevronUp, Check, X, AlertCircle } from 'lucide-react';
import { DietGroup } from '../types';

interface DietRecommendationsSectionProps {
  recommendations: DietGroup[];
}

export const DietRecommendationsSection: React.FC<DietRecommendationsSectionProps> = ({ recommendations }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-emerald-50/60 rounded-3xl p-4 border border-emerald-200 my-4 text-emerald-900 text-xs font-semibold flex items-center gap-2">
        <Utensils size={16} className="text-emerald-600" />
        <span>Balanced standard diet recommended. No specific restricted profiles detected.</span>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-200 shadow-sm my-4 transition-all">

      {/* Header Accordion Toggle */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between text-left focus:outline-none"
      >
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-2xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-lg shadow-sm">
            🥗
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-gray-900 flex items-center gap-1.5">
              Diet & Lifestyle Guidance
            </h3>
            <p className="text-[11px] text-gray-500 font-medium">
              Targeted nutritional advice tailored for detected abnormalities
            </p>
          </div>
        </div>

        <div className="w-7 h-7 rounded-full bg-gray-100 flex items-center justify-center text-gray-600 hover:bg-gray-200 transition-colors">
          {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </div>
      </button>

      {/* Accordion Content */}
      {isOpen && (
        <div className="mt-4 pt-3 border-t border-gray-100 flex flex-col gap-4">
          {recommendations.map((group) => (
            <div
              key={group.profile}
              className="bg-gray-50/80 rounded-2xl p-4 border border-gray-200 transition-all hover:bg-gray-50"
            >
              {/* Profile Subheader */}
              <div className="flex items-center gap-2 mb-2.5 pb-1.5 border-b border-gray-200">
                <span className="text-base">{group.icon}</span>
                <span className="text-xs font-extrabold text-gray-800 uppercase tracking-wider">
                  {group.profile}
                </span>
              </div>

              {/* Items List */}
              <ul className="flex flex-col gap-2">
                {group.items.map((item, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs font-medium">
                    {item.type === 'do' && (
                      <span className="w-5 h-5 rounded-full bg-emerald-100 text-emerald-700 shrink-0 flex items-center justify-center mt-0.5 font-bold text-[11px]">
                        ✓
                      </span>
                    )}
                    {item.type === 'avoid' && (
                      <span className="w-5 h-5 rounded-full bg-rose-100 text-rose-700 shrink-0 flex items-center justify-center mt-0.5 font-bold text-[11px]">
                        ✕
                      </span>
                    )}
                    {item.type === 'limit' && (
                      <span className="w-5 h-5 rounded-full bg-amber-100 text-amber-700 shrink-0 flex items-center justify-center mt-0.5 font-bold text-[11px]">
                        !
                      </span>
                    )}
                    <span className={
                      item.type === 'do' ? 'text-emerald-950 font-semibold' :
                        item.type === 'avoid' ? 'text-rose-950 font-semibold' :
                          'text-amber-950 font-semibold'
                    }>
                      {item.text}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};