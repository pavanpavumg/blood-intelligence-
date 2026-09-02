'use client';

import React, { useState, ChangeEvent, FormEvent } from 'react';

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

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReportUploadResponse | null>(null);

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
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
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
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getStatusBadgeStyle = (status: string | null) => {
    switch (status) {
      case 'NORMAL':
        return { backgroundColor: '#064e3b', color: '#34d399', border: '1px solid #059669' };
      case 'HIGH':
      case 'LOW':
        return { backgroundColor: '#7f1d1d', color: '#f87171', border: '1px solid #dc2626' };
      case 'UNKNOWN':
      default:
        return { backgroundColor: '#78350f', color: '#fbbf24', border: '1px solid #d97706' };
    }
  };

  const getFlagBadgeStyle = (flag: string | null) => {
    switch (flag) {
      case 'NONE':
        return { backgroundColor: '#1e293b', color: '#94a3b8' };
      case 'RED_FLAG':
        return { backgroundColor: '#991b1b', color: '#fef2f2', fontWeight: 600 };
      case 'REVIEW_REQUIRED':
      default:
        return { backgroundColor: '#854d0e', color: '#fef9c3' };
    }
  };

  return (
    <main style={{ padding: '2.5rem 1.5rem', maxWidth: '1200px', margin: '0 auto', fontFamily: 'system-ui, -apple-system, sans-serif', color: '#f8fafc' }}>
      {/* Header */}
      <header style={{ marginBottom: '2.5rem', borderBottom: '1px solid #334155', paddingBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 700, color: '#38bdf8', margin: 0, letterSpacing: '-0.025em' }}>
            🩸 Blood Test Intelligence System
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '1rem', marginTop: '0.4rem', marginBottom: 0 }}>
            Deterministic Lab Extraction, Test Mapping & Reference Range Classifier
          </p>
        </div>
        <div style={{ padding: '0.4rem 0.8rem', backgroundColor: '#0f172a', borderRadius: '0.5rem', border: '1px solid #1e293b', fontSize: '0.85rem', color: '#38bdf8' }}>
          #
        </div>
      </header>

      {/* Upload View */}
      {!result && (
        <section style={{ backgroundColor: '#1e293b', borderRadius: '1rem', border: '1px solid #334155', padding: '2rem', maxWidth: '750px', margin: '0 auto', boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.3)' }}>
          <h2 style={{ fontSize: '1.35rem', fontWeight: 600, color: '#f1f5f9', marginTop: 0, marginBottom: '0.5rem' }}>
            Upload Laboratory Report
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.92rem', marginBottom: '1.5rem' }}>
            Upload a blood test report to extract, normalize, and classify lab results deterministically without an LLM.
          </p>

          <form onSubmit={handleSubmit}>
            {/* Drag & Drop Zone */}
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              style={{
                border: '2px dashed #475569',
                borderRadius: '0.75rem',
                padding: '2.5rem 1.5rem',
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
              <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📄</div>
              <p style={{ fontSize: '1rem', fontWeight: 500, color: '#e2e8f0', margin: '0 0 0.25rem 0' }}>
                {selectedFile ? selectedFile.name : 'Click to upload or drag and drop report'}
              </p>
              <p style={{ fontSize: '0.85rem', color: '#64748b', margin: 0 }}>
                {selectedFile ? `Size: ${formatFileSize(selectedFile.size)}` : 'Supported Formats: PDF, PNG, JPG, JPEG (Max 20MB)'}
              </p>
            </div>

            {/* Error Alert */}
            {error && (
              <div style={{ backgroundColor: '#450a0a', border: '1px solid #991b1b', color: '#fca5a5', padding: '0.9rem 1.2rem', borderRadius: '0.5rem', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                ⚠️ {error}
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !selectedFile}
              style={{
                width: '100%',
                padding: '0.85rem 1.5rem',
                backgroundColor: loading || !selectedFile ? '#334155' : '#0284c7',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.5rem',
                fontSize: '1rem',
                fontWeight: 600,
                cursor: loading || !selectedFile ? 'not-allowed' : 'pointer',
                transition: 'background-color 0.2s',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                gap: '0.5rem',
              }}
            >
              {loading ? (
                <>
                  <span style={{ display: 'inline-block', width: '1rem', height: '1rem', border: '2px solid #ffffff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
                  Processing Report...
                </>
              ) : (
                'Analyze Report'
              )}
            </button>
          </form>
        </section>
      )}

      {/* Results View */}
      {result && (
        <section style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Action Bar */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{ fontSize: '1.1rem', fontWeight: 600, color: '#f8fafc' }}>
                Status:
              </span>
              <span style={{ padding: '0.3rem 0.8rem', backgroundColor: result.status.includes('WARNINGS') ? '#78350f' : '#064e3b', color: result.status.includes('WARNINGS') ? '#fde047' : '#34d399', borderRadius: '0.375rem', fontSize: '0.85rem', fontWeight: 600 }}>
                {result.status}
              </span>
            </div>
            <button
              onClick={handleReset}
              style={{ padding: '0.6rem 1.2rem', backgroundColor: '#334155', color: '#f8fafc', border: 'none', borderRadius: '0.5rem', fontSize: '0.9rem', fontWeight: 500, cursor: 'pointer' }}
            >
              ← Upload Another Report
            </button>
          </div>

          {/* Report Metadata Card */}
          <div style={{ backgroundColor: '#1e293b', padding: '1.5rem', borderRadius: '0.75rem', border: '1px solid #334155', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem' }}>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>Report ID</div>
              <div style={{ fontSize: '1rem', fontWeight: 600, color: '#38bdf8' }}>{result.data.report.report_id}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>Report Date</div>
              <div style={{ fontSize: '1rem', fontWeight: 500, color: '#f1f5f9' }}>{result.data.report.report_date || 'N/A'}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>Patient Name</div>
              <div style={{ fontSize: '1rem', fontWeight: 500, color: '#f1f5f9' }}>{result.data.patient.name || 'N/A'}</div>
            </div>
            <div>
              <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase' }}>Age / Gender</div>
              <div style={{ fontSize: '1rem', fontWeight: 500, color: '#f1f5f9' }}>
                {result.data.patient.age ? `${result.data.patient.age} yrs` : 'N/A'} / {result.data.patient.gender || 'N/A'}
              </div>
            </div>
          </div>

          {/* Warnings Callout */}
          {result.data.warnings && result.data.warnings.length > 0 && (
            <div style={{ backgroundColor: '#451a03', border: '1px solid #78350f', color: '#fde047', padding: '1rem 1.25rem', borderRadius: '0.75rem', fontSize: '0.9rem' }}>
              <div style={{ fontWeight: 600, marginBottom: '0.4rem' }}>⚠️ Parsing & Extraction Warnings:</div>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {result.data.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Results Table */}
          <div style={{ backgroundColor: '#1e293b', borderRadius: '0.75rem', border: '1px solid #334155', overflow: 'hidden' }}>
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600, color: '#f1f5f9' }}>
                Extracted Laboratory Results ({result.data.tests.length})
              </h3>
            </div>

            {result.data.tests.length === 0 ? (
              <div style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                No laboratory test rows could be confidently extracted from this document.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.92rem' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Test Name</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Result Value</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Unit</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Reference Range</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Status</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>Flag</th>
                      <th style={{ padding: '0.85rem 1.25rem' }}>LOINC</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.data.tests.map((test, index) => {
                      const displayTestName = test.canonical_test_name || test.raw_test_name;
                      const displayValue = test.value !== null ? test.value : test.raw_value || 'N/A';
                      const displayUnit = test.normalized_unit || test.raw_unit || '-';
                      const refRange = test.reference_range;
                      const displayRefRange = refRange?.raw ||
                        (refRange && refRange.low !== null && refRange.high !== null
                          ? `${refRange.low} - ${refRange.high}`
                          : '-');

                      return (
                        <tr key={index} style={{ borderBottom: index === result.data.tests.length - 1 ? 'none' : '1px solid #334155', backgroundColor: index % 2 === 0 ? '#1e293b' : '#0f172a' }}>
                          <td style={{ padding: '0.85rem 1.25rem', fontWeight: 500, color: '#f8fafc' }}>
                            {displayTestName}
                            {test.canonical_test_name && test.canonical_test_name !== test.raw_test_name && (
                              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Raw: {test.raw_test_name}</div>
                            )}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600, color: '#38bdf8' }}>
                            {displayValue}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', color: '#cbd5e1' }}>
                            {displayUnit}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', color: '#cbd5e1' }}>
                            {displayRefRange}
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem' }}>
                            <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.8rem', fontWeight: 600, ...getStatusBadgeStyle(test.status) }}>
                              {test.status || 'UNKNOWN'}
                            </span>
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem' }}>
                            <span style={{ padding: '0.25rem 0.6rem', borderRadius: '0.375rem', fontSize: '0.8rem', ...getFlagBadgeStyle(test.flag) }}>
                              {test.flag || 'REVIEW_REQUIRED'}
                            </span>
                          </td>
                          <td style={{ padding: '0.85rem 1.25rem', fontSize: '0.8rem', color: test.loinc_code ? '#a7f3d0' : '#64748b' }}>
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

      {/* Inline Spinner Keyframe */}
      <style jsx global>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </main>
  );
}
