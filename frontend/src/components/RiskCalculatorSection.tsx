import React from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle, ArrowRight, UserCheck } from 'lucide-react';
import { RiskFactor } from '../types';

interface RiskCalculatorSectionProps {
  risks: RiskFactor[];
  onSelectProfile?: (profileName: string) => void;
}

export const RiskCalculatorSection: React.FC<RiskCalculatorSectionProps> = ({ risks, onSelectProfile }) => {
  if (!risks || risks.length === 0) {
    return (
      <div className="bg-emerald-50 rounded-3xl p-5 border border-emerald-200/80 shadow-sm my-4 flex items-center gap-3">
        <CheckCircle size={24} className="text-emerald-600 shrink-0" />
        <div>
          <h3 className="text-xs font-extrabold text-emerald-900 uppercase tracking-wider">
            Low Clinical Risk Profile
          </h3>
          <p className="text-xs text-emerald-700 font-medium">
            No critical health risks detected based on analyzed test parameters. Maintain healthy lifestyle habits.
          </p>
        </div>
      </div>
    );
  }

  const highRisks = risks.filter(r => r.severity === 'HIGH');

  return (
    <div className="bg-white rounded-3xl p-5 border border-gray-200/80 shadow-sm my-4">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-100">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-2xl bg-rose-100 text-rose-700 flex items-center justify-center font-bold text-lg shadow-2xs">
            🛡️
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-gray-900">
              Clinical Risk Assessment
            </h3>
            <p className="text-[11px] text-gray-500 font-medium">
              Identified health conditions requiring medical awareness
            </p>
          </div>
        </div>

        <span className={`text-xs font-extrabold px-2.5 py-1 rounded-full border ${
          highRisks.length > 0 
            ? 'bg-rose-100 text-rose-800 border-rose-300 animate-pulse' 
            : 'bg-amber-100 text-amber-800 border-amber-300'
        }`}>
          {highRisks.length > 0 ? '🔴 High Risk Category' : '🟠 Moderate Risk Category'}
        </span>
      </div>

      {/* Risks List */}
      <div className="flex flex-col gap-3">
        {risks.map((risk) => (
          <div
            key={risk.id}
            className={`rounded-2xl p-4 border transition-all ${
              risk.severity === 'HIGH'
                ? 'bg-rose-50/60 border-rose-200 text-rose-950'
                : 'bg-amber-50/60 border-amber-200 text-amber-950'
            }`}
          >
            {/* Risk Title & Severity Dot */}
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${
                  risk.severity === 'HIGH' ? 'bg-rose-600 animate-ping' : 'bg-amber-500'
                }`} />
                <span className="text-xs font-extrabold tracking-tight">
                  {risk.name}
                </span>
              </div>
              <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-full ${
                risk.severity === 'HIGH' ? 'bg-rose-200 text-rose-900' : 'bg-amber-200 text-amber-900'
              }`}>
                {risk.severity} SEVERITY
              </span>
            </div>

            {/* Affected Parameters */}
            <div className="flex flex-wrap items-center gap-1 my-1.5">
              <span className="text-[10px] font-semibold text-gray-500">Triggered by:</span>
              {risk.tests.map((t) => (
                <span key={t} className="text-[10px] font-bold bg-white/80 px-2 py-0.5 rounded-md border border-gray-200 text-gray-700">
                  {t}
                </span>
              ))}
            </div>

            {/* Actionable Advice */}
            <div className="flex items-center gap-2 mt-2 pt-2 border-t border-black/5 text-xs font-bold text-gray-800">
              <UserCheck size={15} className="text-blue-600 shrink-0" />
              <span>{risk.advice}</span>
            </div>
          </div>
        ))}
      </div>

    </div>
  );
};
