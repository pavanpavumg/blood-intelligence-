import React from 'react';
import { User, Calendar, Share2, FileText, Upload } from 'lucide-react';
import { PatientInfo, ReportMetadata } from '../types';

interface HeaderBarProps {
  patient: PatientInfo;
  report: ReportMetadata;
  status: string;
  onUploadNewPdf?: () => void;
}

export const HeaderBar: React.FC<HeaderBarProps> = ({ patient, report, status, onUploadNewPdf }) => {
  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return dateStr;
      return d.toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md shadow-xs border-b border-gray-100 h-16 transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 md:px-6 h-full flex items-center justify-between">
        
        {/* Left: Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-primary-blue flex items-center justify-center text-white font-black text-base shadow-md shadow-primary-blue/25">
            T
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-black tracking-tight text-slate-900 leading-none">
              Tez <span className="text-primary-blue">SmartApp</span>
            </span>
            <span className="text-[10px] font-semibold text-gray-400 tracking-wider uppercase leading-none mt-1">
              Smart Health Viewer
            </span>
          </div>
        </div>

        {/* Center: Patient Demographics & Report Date */}
        <div className="flex items-center gap-2 md:gap-4">
          {/* Patient Info */}
          <div className="flex items-center gap-2 bg-bg-light-blue px-3 py-1.5 rounded-full border border-blue-100">
            <div className="w-5 h-5 rounded-full bg-primary-blue text-white flex items-center justify-center">
              <User size={12} className="stroke-[2.5]" />
            </div>
            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800">
              <span className="truncate max-w-[100px] sm:max-w-[160px]">{patient.name}</span>
              {patient.age ? <span className="text-slate-400 text-[11px] font-normal">({patient.age}y, {patient.gender})</span> : null}
            </div>
          </div>

          {/* Date */}
          <div className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-slate-600 bg-bg-light-blue px-3 py-1.5 rounded-full border border-blue-100">
            <Calendar size={13} className="text-primary-blue" />
            <span>{formatDate(report.report_date)}</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          {onUploadNewPdf && (
            <button
              onClick={onUploadNewPdf}
              className="hidden sm:flex items-center gap-1.5 px-3.5 py-1.5 bg-primary-blue hover:bg-blue-600 text-white text-xs font-extrabold rounded-full shadow-sm shadow-primary-blue/25 transition-all active:scale-95"
            >
              <Upload size={13} />
              <span>Upload New PDF</span>
            </button>
          )}

          <button 
            onClick={() => {
              if (navigator.share) {
                navigator.share({ title: `Smart Health Report - ${patient.name}`, url: window.location.href }).catch(() => {});
              } else {
                alert(`Smart Health Report link copied for ${patient.name}`);
              }
            }}
            aria-label="Share Report"
            className="w-9 h-9 rounded-full bg-bg-light-blue hover:bg-blue-100 text-primary-blue flex items-center justify-center transition-colors border border-blue-100 active:scale-95"
          >
            <Share2 size={16} />
          </button>
        </div>

      </div>
    </header>
  );
};
