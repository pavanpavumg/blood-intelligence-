import React from 'react';
import { Activity, LayoutGrid } from 'lucide-react';

interface TabNavigationProps {
  activeTab: 'overview' | 'smart-view';
  setActiveTab: (tab: 'overview' | 'smart-view') => void;
  abnormalCount?: number;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({
  activeTab,
  setActiveTab,
  abnormalCount = 0
}) => {
  return (
    <div className="sticky top-16 z-40 bg-white/90 backdrop-blur-md border-b border-gray-100 py-3 px-4 md:px-6">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Tab Controls */}
        <div className="bg-slate-100/90 p-1 rounded-full flex items-center shadow-inner border border-slate-200/80 w-full sm:w-auto">
          
          {/* Overview Tab */}
          <button
            onClick={() => setActiveTab('overview')}
            className={`flex-1 sm:flex-none py-2 px-5 rounded-full text-xs font-bold transition-all duration-200 flex items-center justify-center gap-2 ${
              activeTab === 'overview'
                ? 'bg-primary-blue text-white shadow-md shadow-primary-blue/25 scale-[1.01]'
                : 'text-slate-600 hover:text-slate-900 font-medium'
            }`}
          >
            <LayoutGrid size={15} className={activeTab === 'overview' ? 'stroke-[2.5]' : 'stroke-2'} />
            <span>Overview Dashboard</span>
          </button>

          {/* Smart View Tab */}
          <button
            onClick={() => setActiveTab('smart-view')}
            className={`flex-1 sm:flex-none py-2 px-5 rounded-full text-xs font-bold transition-all duration-200 flex items-center justify-center gap-2 relative ${
              activeTab === 'smart-view'
                ? 'bg-primary-blue text-white shadow-md shadow-primary-blue/25 scale-[1.01]'
                : 'text-slate-600 hover:text-slate-900 font-medium'
            }`}
          >
            <Activity size={15} className={activeTab === 'smart-view' ? 'stroke-[2.5]' : 'stroke-2'} />
            <span>Smart View (All Parameters)</span>
            {abnormalCount > 0 && (
              <span className={`ml-1 text-[10px] px-2 py-0.2 rounded-full font-bold ${
                activeTab === 'smart-view'
                  ? 'bg-danger-red text-white'
                  : 'bg-rose-100 text-danger-red border border-rose-200'
              }`}>
                {abnormalCount}
              </span>
            )}
          </button>

        </div>

        {/* Desktop Helper Text */}
        <div className="hidden lg:flex items-center gap-2 text-xs text-slate-400 font-medium">
          <span>Click organ hotspots or parameters to inspect detailed findings</span>
        </div>

      </div>
    </div>
  );
};
