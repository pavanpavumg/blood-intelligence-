'use client';

import React, { useState, ChangeEvent, FormEvent, useMemo } from 'react';

interface ReferenceRange {
  low: number | null;
  high: number | null;
  raw: string | null;
}

interface LabTestResult {
  raw_test_name: string;
  canonical_test_name: string | null;
  test_id: string | null;
  loinc_code: string | null;
  value: number | null;
  raw_value?: string | null;
  raw_unit: string | null;
  normalized_unit: string | null;
  reference_range: ReferenceRange | null;
  status: 'NORMAL' | 'HIGH' | 'LOW' | 'UNKNOWN' | null;
  flag: 'NONE' | 'RED_FLAG' | 'REVIEW_REQUIRED' | null;
  mapping_status: 'MAPPED' | 'REVIEW_REQUIRED' | 'UNMAPPED';
  warnings?: string[];
}

interface PatientInfo {
  patient_id: string | null;
  name: string | null;
  age: number | null;
  gender: string | null;
}

interface ReportMetadata {
  report_id: string;
  report_date: string | null;
  lab_name: string | null;
}

interface NormalizedReportData {
  schema_version: string;
  report: ReportMetadata;
  patient: PatientInfo;
  tests: LabTestResult[];
  warnings: string[];
}

interface ReportUploadResponse {
  report_id: string;
  status: string;
  data: NormalizedReportData;
}

type FilterCategory = 'ALL' | 'ABNORMAL' | 'HIGH' | 'LOW' | 'NORMAL' | 'REVIEW';

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReportUploadResponse | null>(null);

  // Dashboard Controls
  const [activeFilter, setActiveFilter] = useState<FilterCategory>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a blood test report file (PDF, PNG, JPG, JPEG).');
      return;
    }

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${API_BASE_URL}/api/reports/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: `Upload failed with HTTP ${res.status}` }));
        throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
      }

      const data: ReportUploadResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred during processing.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
    setActiveFilter('ALL');
    setSearchQuery('');
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  // Clinical Summary Statistics
  const stats = useMemo(() => {
    if (!result?.data?.tests) {
      return { total: 0, normal: 0, high: 0, low: 0, review: 0 };
    }
    const tests = result.data.tests;
    return {
      total: tests.length,
      normal: tests.filter(t => t.status === 'NORMAL').length,
      high: tests.filter(t => t.status === 'HIGH').length,
      low: tests.filter(t => t.status === 'LOW').length,
      review: tests.filter(t => t.status === 'UNKNOWN' || t.mapping_status === 'REVIEW_REQUIRED' || t.flag === 'REVIEW_REQUIRED').length,
    };
  }, [result]);

  // Filtered Lab Results for Doctors
  const filteredTests = useMemo(() => {
    if (!result?.data?.tests) return [];

    return result.data.tests.filter(test => {
      const testName = (test.canonical_test_name || test.raw_test_name).toLowerCase();
      const loinc = (test.loinc_code || '').toLowerCase();
      const query = searchQuery.toLowerCase().trim();

      const matchesSearch = !query || testName.includes(query) || loinc.includes(query);

      let matchesCategory = true;
      if (activeFilter === 'ABNORMAL') {
        matchesCategory = test.status === 'HIGH' || test.status === 'LOW';
      } else if (activeFilter === 'HIGH') {
        matchesCategory = test.status === 'HIGH';
      } else if (activeFilter === 'LOW') {
        matchesCategory = test.status === 'LOW';
      } else if (activeFilter === 'NORMAL') {
        matchesCategory = test.status === 'NORMAL';
      } else if (activeFilter === 'REVIEW') {
        matchesCategory = test.status === 'UNKNOWN' || test.mapping_status === 'REVIEW_REQUIRED';
      }

      return matchesSearch && matchesCategory;
    });
  }, [result, activeFilter, searchQuery]);

  const getStatusBadgeStyle = (status: string | null) => {
    switch (status) {
      case 'NORMAL':
        return { backgroundColor: '#064e3b', color: '#34d399', border: '1px solid #059669', icon: '🟢' };
      case 'HIGH':
        return { backgroundColor: '#7f1d1d', color: '#f87171', border: '1px solid #dc2626', icon: '🚨' };
      case 'LOW':
        return { backgroundColor: '#78350f', color: '#fbbf24', border: '1px solid #d97706', icon: '⚠️' };
      case 'UNKNOWN':
      default:
        return { backgroundColor: '#334155', color: '#cbd5e1', border: '1px solid #64748b', icon: '❓' };
    }
  };

  const getFlagBadgeStyle = (flag: string | null) => {
    switch (flag) {
      case 'NONE':
        return { backgroundColor: '#0f172a', color: '#64748b', border: '1px solid #1e293b' };
      case 'RED_FLAG':
        return { backgroundColor: '#991b1b', color: '#fef2f2', border: '1px solid #ef4444', fontWeight: 600 };
      case 'REVIEW_REQUIRED':
      default:
        return { backgroundColor: '#854d0e', color: '#fef9c3', border: '1px solid #eab308' };
    }
  };

  return (
    <main style={{ padding: '2.5rem 1.5rem', maxWidth: '1280px', margin: '0 auto', fontFamily: 'system-ui, -apple-system, sans-serif', color: '#f8fafc' }}>
      {/* Top Header */}
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid #334155', paddingBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '1.8rem' }}>🩸</span>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', margin: 0, letterSpacing: '-0.025em' }}>
              Blood Test Intelligence — Doctor Clinical Dashboard
            </h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginTop: '0.4rem', marginBottom: 0 }}>
            Automated Clinical Triaging, High/Low Abnormalities Classifier & Deterministic Extraction
          </p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center' }}>
          <span style={{ padding: '0.4rem 0.8rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', border: '1px solid #1e293b', fontSize: '0.85rem', color: '#38bdf8', fontWeight: 600 }}>
            Phase 0–2 Engine v2.1
          </span>
        </div>
      </header>

      {/* Upload View */}
      {!result && (
        <section style={{ backgroundColor: '#1e293b', borderRadius: '1rem', border: '1px solid #334155', padding: '2.5rem', maxWidth: '750px', margin: '0 auto', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)' }}>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f1f5f9', marginTop: 0, marginBottom: '0.5rem' }}>
            Upload Laboratory Report
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.95rem', marginBottom: '1.75rem', lineHeight: 1.5 }}>
            Upload a blood test PDF or scanned image report to instantly analyze High, Low, and Normal clinical biomarkers.
          </p>

          <form onSubmit={handleSubmit}>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              style={{
                border: '2px dashed #475569',
                borderRadius: '0.75rem',
                padding: '3rem 1.5rem',
                textAlign: 'center',
                backgroundColor: '#0f172a',
                cursor: 'pointer',
                transition: 'border-color 0.2s',
                marginBottom: '1.5rem',
              }}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <div style={{ fontSize: '2.75rem', marginBottom: '0.75rem' }}>📄</div>
              <p style={{ fontSize: '1.05rem', fontWeight: 600, color: '#e2e8f0', margin: '0 0 0.35rem 0' }}>
                {selectedFile ? selectedFile.name : 'Click to upload or drag & drop laboratory report'}
              </p>
              <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
                {selectedFile ? `File Size: ${formatFileSize(selectedFile.size)}` : 'Supported Formats: PDF, PNG, JPG, JPEG (Max 20MB)'}
              </p>
            </div>

            {error && (
              <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fca5a5', padding: '0.9rem 1.2rem', borderRadius: '0.5rem', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                ⚠️ {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !selectedFile}
              style={{
                width: '100%',
                padding: '0.9rem 1.5rem',
                backgroundColor: loading || !selectedFile ? '#334155' : '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '1.05rem',
                fontWeight: 700,
                cursor: loading || !selectedFile ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '0.6rem',
              }}
            >
              {loading ? (
                <>
                  <span style={{ display: 'inline-block', width: '1.1rem', height: '1.1rem', border: '2px solid #ffffff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                  Analyzing Blood Report...
                </>
              ) : (
                '🔬 Process & Analyze Report'
              )}
            </button>
          </form>
        </section>
      )}

      {/* Doctor Dashboard View */}
      {result && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {/* Top Bar Controls */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', backgroundColor: '#1e293b', padding: '1.25rem 1.5rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1rem', fontWeight: 600, color: '#f8fafc' }}>Extraction Status:</span>
              <span style={{ padding: '0.35rem 0.85rem', backgroundColor: result.status.includes('WARNINGS') ? '#78350f' : '#064e3b', color: result.status.includes('WARNINGS') ? '#fde047' : '#34d399', borderRadius: '0.375rem', fontSize: '0.85rem', fontWeight: 700 }}>
                {result.status}
              </span>
            </div>
            <button
              onClick={handleReset}
              style={{ padding: '0.65rem 1.25rem', backgroundColor: '#334155', color: '#f8fafc', border: 'none', borderRadius: '0.5rem', fontSize: '0.9rem', fontWeight: 600, cursor: 'pointer', transition: 'background-color 0.2s' }}
            >
              ← Upload Another Report
            </button>
          </div>

          {/* Clinical Analytics Cards (Total, Normal, High, Low, Review) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '1.25rem' }}>
            {/* Total Biomarkers */}
            <div style={{ backgroundColor: '#0f172a', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #334155' }}>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Total Tests</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8', marginTop: '0.3rem' }}>{stats.total}</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.2rem' }}>Extracted Biomarkers</div>
            </div>

            {/* Normal Biomarkers */}
            <div style={{ backgroundColor: '#064e3b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #059669' }}>
              <div style={{ fontSize: '0.8rem', color: '#a7f3d0', textTransform: 'uppercase', fontWeight: 700 }}>🟢 Normal</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#34d399', marginTop: '0.3rem' }}>{stats.normal}</div>
              <div style={{ fontSize: '0.75rem', color: '#a7f3d0', opacity: 0.9, marginTop: '0.2rem' }}>Within Reference Range</div>
            </div>

            {/* High Biomarkers */}
            <div style={{ backgroundColor: '#7f1d1d', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #dc2626' }}>
              <div style={{ fontSize: '0.8rem', color: '#fca5a5', textTransform: 'uppercase', fontWeight: 700 }}>🚨 High</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f87171', marginTop: '0.3rem' }}>{stats.high}</div>
              <div style={{ fontSize: '0.75rem', color: '#fca5a5', opacity: 0.9, marginTop: '0.2rem' }}>Above Upper Limit</div>
            </div>

            {/* Low Biomarkers */}
            <div style={{ backgroundColor: '#78350f', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #d97706' }}>
              <div style={{ fontSize: '0.8rem', color: '#fde047', textTransform: 'uppercase', fontWeight: 700 }}>⚠️ Low</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#fbbf24', marginTop: '0.3rem' }}>{stats.low}</div>
              <div style={{ fontSize: '0.75rem', color: '#fde047', opacity: 0.9, marginTop: '0.2rem' }}>Below Lower Limit</div>
            </div>

            {/* Review Required */}
            <div style={{ backgroundColor: '#1e293b', padding: '1.25rem', borderRadius: '0.75rem', border: '1px solid #475569' }}>
              <div style={{ fontSize: '0.8rem', color: '#cbd5e1', textTransform: 'uppercase', fontWeight: 700 }}>❓ Review Required</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#e2e8f0', marginTop: '0.3rem' }}>{stats.review}</div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginTop: '0.2rem' }}>Requires Doctor Inspection</div>
            </div>
          </div>

          {/* Clinical Alert Callout (If High or Low detected) */}
          {(stats.high > 0 || stats.low > 0) && (
            <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fecaca', padding: '1.2rem 1.5rem', borderRadius: '0.75rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <span style={{ fontSize: '1.8rem' }}>🚨</span>
              <div>
                <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fca5a5' }}>
                  Clinical Attention Required
                </div>
                <div style={{ fontSize: '0.9rem', color: '#f87171', marginTop: '0.2rem' }}>
                  Detected <strong>{stats.high} HIGH</strong> and <strong>{stats.low} LOW</strong> abnormal blood biomarkers in this report.
                </div>
              </div>
            </div>
          )}

          {/* Patient Metadata Banner */}
          <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #334155', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Report ID</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#38bdf8', marginTop: '0.2rem' }}>{result.data.report.report_id}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Report Date</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f1f5f9', marginTop: '0.2rem' }}>{result.data.report.report_date || 'N/A'}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Patient Name</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f1f5f9', marginTop: '0.2rem' }}>{result.data.patient.name || 'N/A'}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Age / Gender</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#f1f5f9', marginTop: '0.2rem' }}>
                {result.data.patient.age ? `${result.data.patient.age} Y` : 'N/A'} / {result.data.patient.gender || 'N/A'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '0.78rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>Lab Facility</div>
              <div style={{ fontSize: '1.05rem', fontWeight: 600, color: '#34d399', marginTop: '0.2rem' }}>{result.data.report.lab_name || 'Standard Pathology Lab'}</div>
            </div>
          </div>

          {/* Warnings Callout */}
          {result.data.warnings && result.data.warnings.length > 0 && (
            <div style={{ backgroundColor: '#451a03', border: '1px solid #78350f', color: '#fde047', padding: '1rem 1.25rem', borderRadius: '0.75rem', fontSize: '0.9rem' }}>
              <div style={{ fontWeight: 700, marginBottom: '0.4rem' }}>⚠️ Processing Warnings:</div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {result.data.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Filter & Search Bar */}
          <div style={{ backgroundColor: '#1e293b', padding: '1.25rem 1.5rem', borderRadius: '0.75rem', border: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            {/* Filter Buttons */}
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <button
                onClick={() => setActiveFilter('ALL')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'ALL' ? '#0284c7' : '#0f172a',
                  color: activeFilter === 'ALL' ? '#ffffff' : '#94a3b8',
                }}
              >
                All ({stats.total})
              </button>
              <button
                onClick={() => setActiveFilter('ABNORMAL')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'ABNORMAL' ? '#991b1b' : '#0f172a',
                  color: activeFilter === 'ABNORMAL' ? '#ffffff' : '#fca5a5',
                }}
              >
                🚨 Abnormalities ({stats.high + stats.low})
              </button>
              <button
                onClick={() => setActiveFilter('HIGH')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'HIGH' ? '#7f1d1d' : '#0f172a',
                  color: activeFilter === 'HIGH' ? '#ffffff' : '#f87171',
                }}
              >
                High ({stats.high})
              </button>
              <button
                onClick={() => setActiveFilter('LOW')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'LOW' ? '#78350f' : '#0f172a',
                  color: activeFilter === 'LOW' ? '#ffffff' : '#fbbf24',
                }}
              >
                Low ({stats.low})
              </button>
              <button
                onClick={() => setActiveFilter('NORMAL')}
                style={{
                  padding: '0.45rem 0.9rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                  backgroundColor: activeFilter === 'NORMAL' ? '#064e3b' : '#0f172a',
                  color: activeFilter === 'NORMAL' ? '#ffffff' : '#34d399',
                }}
              >
                Normal ({stats.normal})
              </button>
            </div>

            {/* Search Input */}
            <input
              type="text"
              placeholder="🔍 Search test name or LOINC..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                padding: '0.45rem 0.9rem',
                backgroundColor: '#0f172a',
                border: '1px solid #334155',
                borderRadius: '0.5rem',
                color: '#f8fafc',
                fontSize: '0.88rem',
                width: '240px',
              }}
            />
          </div>

          {/* Biomarkers Table */}
          <div style={{ backgroundColor: '#1e293b', borderRadius: '0.75rem', border: '1px solid #334155', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f1f5f9' }}>
                Laboratory Results ({filteredTests.length})
              </h3>
            </div>

            {filteredTests.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                No lab tests match the selected filter or search criteria.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.92rem' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Biomarker Test Name</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Result Value</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Unit</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Reference Range</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Clinical Status</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>Risk Flag</th>
                      <th style={{ padding: '0.9rem 1.25rem' }}>LOINC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTests.map((test, index) => {
                      const displayTestName = test.canonical_test_name || test.raw_test_name;
                      const displayValue = test.value !== null ? test.value : test.raw_value || 'N/A';
                      const displayUnit = test.normalized_unit || test.raw_unit || '-';
                      const refRange = test.reference_range;
                      const displayRefRange = refRange?.raw ||
                        (refRange && refRange.low !== null && refRange.high !== null
                          ? `${refRange.low} - ${refRange.high}`
                          : '-');

                      const statusStyle = getStatusBadgeStyle(test.status);
                      const flagStyle = getFlagBadgeStyle(test.flag);

                      return (
                        <tr
                          key={index}
                          style={{
                            borderBottom: index === filteredTests.length - 1 ? 'none' : '1px solid #334155',
                            backgroundColor: test.status === 'HIGH'
                              ? 'rgba(127, 29, 29, 0.15)'
                              : test.status === 'LOW'
                                ? 'rgba(120, 53, 15, 0.15)'
                                : index % 2 === 0 ? '#1e293b' : '#0f172a'
                          }}
                        >
                          <td style={{ padding: '0.9rem 1.25rem', fontWeight: 600, color: '#f8fafc' }}>
                            {displayTestName}
                            {test.canonical_test_name && test.canonical_test_name !== test.raw_test_name && (
                              <div style={{ fontSize: '0.75rem', color: '#64748b', fontWeight: 400 }}>Raw OCR: {test.raw_test_name}</div>
                            )}
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem', fontWeight: 800, fontSize: '1rem', color: test.status === 'HIGH' ? '#f87171' : test.status === 'LOW' ? '#fbbf24' : '#38bdf8' }}>
                            {displayValue}
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem', color: '#cbd5e1' }}>
                            {displayUnit}
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem', color: '#cbd5e1', fontWeight: 500 }}>
                            {displayRefRange}
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem' }}>
                            <span style={{ padding: '0.3rem 0.7rem', borderRadius: '0.375rem', fontSize: '0.82rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '0.35rem', ...statusStyle }}>
                              <span>{statusStyle.icon}</span>
                              <span>{test.status || 'UNKNOWN'}</span>
                            </span>
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem' }}>
                            <span style={{ padding: '0.25rem 0.65rem', borderRadius: '0.375rem', fontSize: '0.8rem', ...flagStyle }}>
                              {test.flag || 'REVIEW_REQUIRED'}
                            </span>
                          </td>
                          <td style={{ padding: '0.9rem 1.25rem', fontSize: '0.8rem', color: test.loinc_code ? '#a7f3d0' : '#64748b', fontWeight: 500 }}>
                            {test.loinc_code ? `LOINC ${test.loinc_code}` : 'Unmapped'}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Spinner Animation Keyframe */}
      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </main>
  );
}
