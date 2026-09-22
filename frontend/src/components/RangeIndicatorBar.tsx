import React from 'react';
import { ReferenceRange, StatusType } from '../types';

interface RangeIndicatorBarProps {
  value: number | string | null;
  unit: string | null;
  range: ReferenceRange;
  status: StatusType;
}

export const RangeIndicatorBar: React.FC<RangeIndicatorBarProps> = ({
  value,
  unit,
  range,
  status
}) => {
  const low = range.low;
  const high = range.high;
  const numValue = typeof value === 'number' ? value : parseFloat(String(value || ''));
  const isNumeric = !isNaN(numValue) && low !== null && high !== null;

  // Handle case where reference range numbers are missing or value is qualitative
  if (!isNumeric || low === null || high === null) {
    const isAbnormal = ['HIGH', 'LOW', 'CRITICAL', 'POSITIVE'].includes(status) && status !== 'UNKNOWN';
    const isReview = status === 'UNKNOWN';
    return (
      <div className="bg-gray-100/80 rounded-2xl p-3.5 my-2 border border-gray-200/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-extrabold text-gray-700">Observed Value:</span>
          <span className={`font-black px-2 py-0.5 rounded-md text-[11px] ${
            isAbnormal ? 'bg-rose-100 text-rose-700' :
            isReview ? 'bg-slate-100 text-slate-700' :
            'bg-emerald-100 text-emerald-700'
          }`}>
            {String(value ?? '—')} {unit || ''} ({status})
          </span>
        </div>
        <div className="text-gray-500 font-medium">
          <span className="font-semibold text-gray-600">Standard Target:</span> {range.raw || 'Clinical Reference Standard'}
        </div>
      </div>
    );
  }

  // Calculate position percentage for patient's value relative to range bounds
  // Give padding below low and above high for visual extension into red zones
  const rawSpan = high - low;
  const span = rawSpan > 0 ? rawSpan : Math.max(1, high || 1);
  const minBound = Math.max(0, low - span * 0.5);
  const maxBound = high + span * 0.5;
  const totalSpan = maxBound - minBound || 1;

  let percentage = ((numValue - minBound) / totalSpan) * 100;
  if (isNaN(percentage)) percentage = 50;
  percentage = Math.max(5, Math.min(95, percentage)); // Clamp between 5% and 95%

  // Percentages for green zone (between low and high)
  const lowPct = Math.max(0, Math.min(100, ((low - minBound) / totalSpan) * 100));
  const highPct = Math.max(0, Math.min(100, ((high - minBound) / totalSpan) * 100));
  const greenWidthPct = Math.max(0, highPct - lowPct);

  return (
    <div className="my-3 bg-gray-50/90 rounded-2xl p-3.5 border border-gray-200/60 shadow-2xs">
      
      {/* Top Labels */}
      <div className="flex items-center justify-between text-[11px] font-bold text-gray-500 mb-2">
        <span>Low Limit ({low} {unit || ''})</span>
        <span className={`px-2 py-0.5 rounded-md font-extrabold ${
          status === 'HIGH' ? 'bg-rose-100 text-rose-700' :
          status === 'LOW' ? 'bg-rose-100 text-rose-700' :
          'bg-emerald-100 text-emerald-700'
        }`}>
          Your Result: {value} {unit || ''} ({status})
        </span>
        <span>High Limit ({high} {unit || ''})</span>
      </div>

      {/* Visual Bar Track */}
      <div className="relative h-4 rounded-full bg-rose-200 overflow-hidden shadow-inner flex">
        {/* Left Red Zone (Below Low) */}
        <div style={{ width: `${lowPct}%` }} className="bg-rose-400/80 h-full" />
        
        {/* Middle Green Zone (Normal Range) */}
        <div style={{ width: `${greenWidthPct}%` }} className="bg-emerald-500 h-full" />
        
        {/* Right Red Zone (Above High) */}
        <div className="flex-1 bg-rose-400/80 h-full" />
      </div>

      {/* Value Pin Indicator Marker */}
      <div className="relative h-6 mt-1">
        <div
          style={{ left: `${percentage}%` }}
          className="absolute -translate-x-1/2 flex flex-col items-center transition-all duration-500"
        >
          {/* Arrow */}
          <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[8px] border-b-gray-900" />
          
          {/* Pin Value */}
          <div className={`text-[10px] font-black px-2 py-0.5 rounded-full shadow-md whitespace-nowrap text-white ${
            status === 'NORMAL' ? 'bg-emerald-600' : 'bg-rose-600'
          }`}>
            {value} {unit || ''}
          </div>
        </div>
      </div>

      {/* Legend below bar */}
      <div className="flex items-center justify-between text-[10px] font-semibold text-gray-400 mt-3 pt-1 border-t border-gray-200/40">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-400" /> Below Range
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500" /> Normal Range
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-400" /> Above Range
        </span>
      </div>

    </div>
  );
};
