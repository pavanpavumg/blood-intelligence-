import React, { useEffect, useState } from 'react';
import { ShieldAlert, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { WellnessScoreResult } from '../types';

interface WellnessScoreCardProps {
  scoreData: WellnessScoreResult;
}

export const WellnessScoreCard: React.FC<WellnessScoreCardProps> = ({ scoreData }) => {
  const [displayScore, setDisplayScore] = useState(0);

  // Animated count-up effect
  useEffect(() => {
    let start = 0;
    const duration = 1000;
    const increment = Math.ceil(scoreData.score / (duration / 16));
    const timer = setInterval(() => {
      start += increment;
      if (start >= scoreData.score) {
        setDisplayScore(scoreData.score);
        clearInterval(timer);
      } else {
        setDisplayScore(start);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [scoreData.score]);

  const getBadgeStyle = () => {
    switch (scoreData.color) {
      case 'green':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'light-green':
        return 'bg-lime-100 text-lime-800 border-lime-300';
      case 'amber':
        return 'bg-amber-100 text-amber-800 border-amber-300';
      case 'red':
        return 'bg-red-100 text-red-800 border-red-300';
    }
  };

  const getScoreTextColor = () => {
    switch (scoreData.color) {
      case 'green':
        return 'text-success-green';
      case 'light-green':
        return 'text-lime-600';
      case 'amber':
        return 'text-warning-amber';
      case 'red':
        return 'text-danger-red';
    }
  };

  return (
    <div className="bg-bg-cream/60 rounded-3xl p-5 border border-amber-200/70 shadow-sm relative overflow-hidden transition-all">
      {/* Decorative Background Aura */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-bg-cream rounded-full blur-2xl pointer-events-none" />
      
      <div className="relative z-10 flex flex-col gap-4">
        
        {/* Header Row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-gray-500 uppercase tracking-wider">
              Health Status
            </span>
          </div>
          
          {/* Status Pill Badge */}
          <div className={`px-3 py-1 rounded-full text-xs font-extrabold border shadow-2xs flex items-center gap-1.5 ${getBadgeStyle()}`}>
            {scoreData.color === 'green' && <CheckCircle2 size={13} className="text-success-green" />}
            {scoreData.color === 'amber' && <AlertTriangle size={13} className="text-warning-amber" />}
            {scoreData.color === 'red' && <ShieldAlert size={13} className="text-danger-red" />}
            <span>{scoreData.label} Wellness Score</span>
          </div>
        </div>

        {/* Score & Counter Grid */}
        <div className="flex items-baseline justify-between pt-1">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className={`text-5xl font-black tracking-tight ${getScoreTextColor()}`}>
                {displayScore}
              </span>
              <span className="text-lg font-bold text-gray-400">/ 100</span>
            </div>
            <p className="text-xs font-medium text-gray-500 mt-1">
              Calculated from {scoreData.total} laboratory parameters
            </p>
          </div>

          {/* Quick Metrics */}
          <div className="flex flex-col items-end gap-1 text-right">
            <div className="flex items-center gap-1.5 text-xs font-bold text-success-green bg-green-50 px-2.5 py-0.5 rounded-md border border-emerald-200/60">
              <span>{scoreData.normal} Normal</span>
            </div>
            {scoreData.abnormal > 0 && (
              <div className="flex items-center gap-1.5 text-xs font-bold text-danger-red bg-red-50 px-2.5 py-0.5 rounded-md border border-rose-200/60">
                <span>{scoreData.abnormal} Abnormal</span>
              </div>
            )}
          </div>
        </div>

        {/* Alert Banner */}
        {scoreData.redFlags > 0 ? (
          <div className="bg-rose-500/10 border border-rose-300/80 rounded-2xl p-3 flex items-start gap-2.5 text-rose-900 mt-1 shadow-2xs animate-pulse">
            <ShieldAlert size={18} className="text-rose-600 shrink-0 mt-0.5" />
            <div className="text-xs">
              <span className="font-extrabold block text-rose-700">
                Urgent: Critical Deviations Detected
              </span>
              <span className="font-medium text-rose-800">
                {scoreData.redFlags} test parameter{scoreData.redFlags > 1 ? 's require' : ' requires'} immediate clinical attention. Tap organs below to check specific abnormalities.
              </span>
            </div>
          </div>
        ) : (
          <div className="bg-emerald-500/10 border border-emerald-300/80 rounded-2xl p-3 flex items-center gap-2 text-emerald-900 mt-1">
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
            <span className="text-xs font-semibold">
              All measured parameters are within standard baseline reference ranges.
            </span>
          </div>
        )}

      </div>
    </div>
  );
};
