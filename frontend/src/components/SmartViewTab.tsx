import React, { useState, useMemo } from 'react';
import { Search, X, ChevronDown, ChevronUp, Info, Activity, Filter, ChevronRight } from 'lucide-react';
import { ProcessedProfile, TestItem } from '../types';
import { RangeIndicatorBar } from './RangeIndicatorBar';
import { getTestExplanation } from '../data/explanations';

interface SmartViewTabProps {
  profiles: Record<string, ProcessedProfile>;
  selectedProfileName?: string | null;
}

export const SmartViewTab: React.FC<SmartViewTabProps> = ({ profiles, selectedProfileName }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [abnormalOnly, setAbnormalOnly] = useState(false);
  const [expandedProfiles, setExpandedProfiles] = useState<Set<string>>(() => {
    const initial = new Set<string>();
    // Auto expand profiles with abnormal tests
    for (const [name, p] of Object.entries(profiles)) {
      if (p.is_abnormal || name === selectedProfileName) {
        initial.add(name);
      }
    }
    return initial;
  });

  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  // Toggle profile accordion
  const toggleProfile = (profileName: string) => {
    setExpandedProfiles(prev => {
      const next = new Set(prev);
      if (next.has(profileName)) {
        next.delete(profileName);
      } else {
        next.add(profileName);
      }
      return next;
    });
  };

  // Toggle test row expansion
  const toggleTest = (testKey: string) => {
    setExpandedTests(prev => {
      const next = new Set(prev);
      if (next.has(testKey)) {
        next.delete(testKey);
      } else {
        next.add(testKey);
      }
      return next;
    });
  };

  // Filter profiles and tests based on search and abnormal filter
  const filteredProfiles = useMemo(() => {
    const result: Record<string, ProcessedProfile> = {};
    const query = searchQuery.toLowerCase().trim();

    for (const [pName, p] of Object.entries(profiles)) {
      let matchingTests = p.tests;

      // Filter abnormal only
      if (abnormalOnly) {
        matchingTests = matchingTests.filter(t =>
          ['HIGH', 'LOW', 'CRITICAL', 'POSITIVE'].includes(t.status) && t.flag !== 'REVIEW_REQUIRED'
        );
      }

      // Filter search query
      if (query) {
        matchingTests = matchingTests.filter(t =>
          t.test_name.toLowerCase().includes(query) ||
          t.raw_test_name.toLowerCase().includes(query) ||
          pName.toLowerCase().includes(query)
        );
      }

      if (matchingTests.length > 0 || (query && pName.toLowerCase().includes(query))) {
        result[pName] = {
          ...p,
          tests: matchingTests
        };
      }
    }

    return result;
  }, [profiles, searchQuery, abnormalOnly]);

  return (
    <div className="flex flex-col gap-5 my-2 pb-12">

      {/* 4.1 Search Bar & Filter Controls Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-center">

        {/* Search Bar */}
        <div className="md:col-span-8 relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-gray-400">
            <Search size={16} />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search parameters or tests (e.g. Urea, HbA1c, Creatinine)..."
            className="w-full pl-10 pr-10 py-3 rounded-2xl bg-white border border-gray-200 shadow-sm text-xs font-semibold text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-tez-blue/30 focus:border-tez-blue transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Filter Controls */}
        <div className="md:col-span-4 bg-white rounded-2xl p-2.5 px-4 border border-gray-200 shadow-sm flex items-center justify-between">
          <div className="flex items-center gap-3 text-[11px] font-bold text-gray-600">
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Normal
            </span>
            <span className="flex items-center gap-1">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500" /> Abnormal
            </span>
          </div>

          <label className="flex items-center gap-2 cursor-pointer text-xs font-bold text-gray-700">
            <Filter size={13} className="text-gray-400" />
            <span>Abnormal Only</span>
            <div className="relative inline-block w-9 h-5 align-middle select-none">
              <input
                type="checkbox"
                checked={abnormalOnly}
                onChange={() => setAbnormalOnly(!abnormalOnly)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-tez-blue" />
            </div>
          </label>
        </div>

      </div>

      {/* Profile Cards Accordion */}
      {Object.keys(filteredProfiles).length === 0 ? (
        <div className="bg-white rounded-3xl p-12 text-center text-gray-500 my-4 border border-gray-200 shadow-sm">
          <Activity size={40} className="mx-auto text-gray-300 mb-3 stroke-1" />
          <p className="text-sm font-bold text-gray-800">No matching test parameters found</p>
          <p className="text-xs text-gray-400 mt-1">Try resetting the search query or turning off the abnormal filter</p>
        </div>
      ) : (
        Object.entries(filteredProfiles).map(([profileName, profile]) => (
          <div
            key={profileName}
            className="bg-white rounded-3xl border border-gray-200 shadow-sm overflow-hidden transition-all"
          >
            {/* Profile Header */}
            <button
              onClick={() => toggleProfile(profileName)}
              className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-2xl flex items-center justify-center text-lg ${profile.is_abnormal
                    ? 'bg-rose-100 text-rose-600'
                    : 'bg-tez-blue-50 text-tez-blue'
                  }`}>
                  {profile.icon}
                </div>
                <div className="text-left">
                  <h3 className="text-sm font-extrabold text-gray-900">{profileName}</h3>
                  <p className="text-[11px] text-gray-500 font-medium">
                    {profile.tests.length} parameters • {profile.normal_count} normal, {profile.abnormal_count} abnormal
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {profile.is_abnormal && (
                  <span className="text-[10px] font-bold bg-rose-100 text-rose-600 px-2 py-1 rounded-full">
                    Attention Needed
                  </span>
                )}
                {expandedProfiles.has(profileName) ? (
                  <ChevronUp size={18} className="text-gray-400" />
                ) : (
                  <ChevronDown size={18} className="text-gray-400" />
                )}
              </div>
            </button>

            {/* Expanded Content */}
            {expandedProfiles.has(profileName) && (
              <div className="border-t border-gray-100">
                {profile.tests.map((test, idx) => {
                  const testKey = `${profileName}-${idx}`;
                  const isExpanded = expandedTests.has(testKey);

                  const isAbnormal = ['HIGH', 'LOW', 'CRITICAL', 'POSITIVE'].includes(test.status) && test.flag !== 'REVIEW_REQUIRED';
                  const isBorderline = test.status === 'BORDERLINE';
                  const isReview = test.flag === 'REVIEW_REQUIRED' || test.status === 'UNKNOWN';
                  const isNormal = ['NORMAL', 'REPORTED', 'OPTIMAL', 'DESIRABLE'].includes(test.status);

                  return (
                    <div
                      key={testKey}
                      className={`border-b border-gray-50 last:border-b-0 ${
                        isAbnormal ? 'bg-rose-50/30' : isBorderline ? 'bg-amber-50/30' : ''
                      }`}
                    >
                      {/* Test Row */}
                      <button
                        onClick={() => toggleTest(testKey)}
                        className="w-full px-5 py-3 flex items-center justify-between hover:bg-gray-50/50 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <div className={`w-2 h-2 rounded-full shrink-0 ${
                            isAbnormal ? 'bg-rose-500' :
                            isBorderline ? 'bg-amber-500' :
                            isReview ? 'bg-slate-400' :
                            'bg-emerald-500'
                          }`} />
                          <div className="text-left min-w-0 flex-1">
                            <div className="flex items-center gap-1.5 flex-wrap">
                              <p className="text-xs font-bold text-gray-900 truncate">{test.test_name}</p>
                              {test.specimen_type && (
                                <span className="text-[9px] font-extrabold text-blue-700 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
                                  {test.specimen_type}
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="text-[10px] text-gray-500 truncate">{test.raw_test_name}</p>
                              {test.method && (
                                <span className="text-[9px] text-slate-500 font-medium italic">
                                  • {test.method}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-3 shrink-0">
                          <div className="text-right">
                            <p className={`text-sm font-black ${
                              isAbnormal ? 'text-rose-600' :
                              isBorderline ? 'text-amber-600' :
                              isReview ? 'text-slate-700' :
                              'text-gray-900'
                            }`}>
                              {test.raw_value ? (
                                test.raw_value.includes(test.raw_unit || '___') 
                                  ? test.raw_value 
                                  : `${test.raw_value} ${test.raw_unit || ''}`
                              ) : (
                                `${test.value ?? '—'} ${test.raw_unit || ''}`
                              )}
                            </p>
                            <p className="text-[10px] text-gray-500 max-w-[140px] truncate sm:max-w-none">
                              {test.reference_range.raw || 'Standard Range'}
                            </p>
                          </div>
                          {isExpanded ? (
                            <ChevronUp size={16} className="text-gray-400" />
                          ) : (
                            <ChevronDown size={16} className="text-gray-400" />
                          )}
                        </div>
                      </button>

                      {/* Expanded Test Details */}
                      {isExpanded && (
                        <div className="px-5 pb-4 pt-2 bg-gray-50/50">
                          <RangeIndicatorBar
                            value={test.value}
                            unit={test.raw_unit}
                            range={test.reference_range}
                            status={test.status}
                          />

                          {(() => {
                            const exp = getTestExplanation(test.test_name, test.status);
                            if (!exp) return null;
                            const statusMeaning = test.status === 'HIGH' 
                              ? (exp.high_meaning || exp.meaning) 
                              : test.status === 'LOW' 
                              ? (exp.low_meaning || exp.meaning) 
                              : exp.meaning;

                            return (
                              <div className="mt-3 p-3.5 bg-tez-blue-50/70 rounded-2xl border border-tez-blue-100/80 flex flex-col gap-2 text-xs">
                                <div className="flex items-start gap-2">
                                  <Info size={15} className="text-tez-blue shrink-0 mt-0.5" />
                                  <div className="flex flex-col gap-1">
                                    <p className="text-[11px] font-extrabold text-tez-blue uppercase tracking-wider">
                                      About {test.test_name}
                                    </p>
                                    <p className="text-gray-700 leading-relaxed font-medium">
                                      {exp.what}
                                    </p>
                                    <p className="text-gray-600 leading-relaxed text-[11px]">
                                      <span className="font-bold text-gray-700">Biological Role: </span>
                                      {exp.function}
                                    </p>
                                    {statusMeaning && (
                                      <p className="text-gray-800 leading-relaxed text-[11px] pt-1 border-t border-blue-100/60 font-medium">
                                        <span className={`font-bold ${test.status === 'NORMAL' ? 'text-emerald-700' : 'text-rose-700'}`}>
                                          Clinical Interpretation ({test.status}): 
                                        </span>{' '}
                                        {statusMeaning}
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))
      )}

    </div>
  );
};