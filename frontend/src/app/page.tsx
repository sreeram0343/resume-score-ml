'use client';

import { useState, useEffect, useRef, DragEvent, ChangeEvent } from 'react';

// Interfaces mapping FastAPI response schemas
interface ATSFlags {
  tables_detected: boolean;
  columns_detected: boolean;
  images_detected: boolean;
  special_chars_ratio: number;
  is_scanned_pdf: boolean;
}

interface UploadResponse {
  resume_id: string;
  filename: string;
  word_count: number;
  page_count: number;
  ats_flags: ATSFlags;
  preview_text: string;
  warnings: string[];
}

interface Suggestion {
  category: string;
  impact: number;
  message: string;
}

interface WaterfallData {
  base_value: number;
  values: number[];
  feature_names: string[];
}

interface ScoreResponse {
  resume_id: string;
  score_id: string;
  overall_score: number;
  ats_score: number;
  content_score: number;
  keyword_score: number;
  semantic_score: number;
  grade: string;
  explanation_text: string;
  suggestions: Suggestion[];
  keyword_gaps: string[];
  waterfall_data: WaterfallData;
  processing_time_ms: number;
}

// Templates for role inputs to improve DX/UX testing
const ROLE_TEMPLATES = [
  {
    role: 'Backend Engineer',
    description: 'Seeking a Senior Backend Engineer proficient in Python, FastAPI, and PostgreSQL. Experience with Redis caching, Docker containerization, and machine learning models (like XGBoost or Scikit-Learn) is highly desirable. Candidates should have experience writing robust test suites and designing async databases.',
  },
  {
    role: 'Frontend Engineer',
    description: 'Looking for a Senior Frontend Developer skilled in React, Next.js, and TypeScript. Expertise in CSS, modern design systems, web optimization, and responsive design is required. Experience connecting to RESTful APIs and implementing custom UI visualization charts (SVG/canvas) is a major plus.',
  },
  {
    role: 'Data Scientist',
    description: 'We are hiring a Data Scientist to build and evaluate predictive models. Must have solid knowledge of Python, pandas, NumPy, and Scikit-Learn. Practical experience with XGBoost, SHAP explainer analysis, and neural networks is required. Familiarity with FastAPI deployment is a bonus.',
  }
];

const BACKEND_URL = 'http://localhost:8000';

export default function Home() {
  // Application State
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState<boolean>(false);
  
  // Loading & Flow State
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadData, setUploadData] = useState<UploadResponse | null>(null);
  const [targetRole, setTargetRole] = useState<string>('');
  const [jobDescription, setJobDescription] = useState<string>('');
  const [isScoring, setIsScoring] = useState<boolean>(false);
  const [scoreData, setScoreData] = useState<ScoreResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Check backend health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/v1/health`);
        if (res.ok) {
          setApiOnline(true);
        } else {
          setApiOnline(false);
        }
      } catch (err) {
        setApiOnline(false);
      }
    };
    checkHealth();
  }, []);

  // Drag & Drop handlers
  const handleDrag = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setIsDragActive(true);
    } else if (e.type === 'dragleave') {
      setIsDragActive(false);
    }
  };

  const handleDrop = async (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      await handleFileUpload(droppedFile);
    }
  };

  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];
      await handleFileUpload(selectedFile);
    }
  };

  // Upload file to Backend
  const handleFileUpload = async (selectedFile: File) => {
    setError(null);
    setUploadData(null);
    setScoreData(null);
    
    // Validate file type
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'txt'].includes(ext || '')) {
      setError('Unsupported file type. Please upload a PDF, DOCX, or TXT file.');
      return;
    }

    // Validate size (10MB maximum)
    if (selectedFile.size > 10 * 1024 * 1024) {
      setError('File is too large. Max limit is 10MB.');
      return;
    }

    setFile(selectedFile);
    setIsUploading(true);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/resume/upload_resume`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({ detail: 'Failed to upload and parse resume.' }));
        throw new Error(errDetail.detail || 'Upload failed');
      }

      const data: UploadResponse = await res.json();
      setUploadData(data);
    } catch (err: any) {
      setError(err.message || 'Error occurred during resume upload.');
      setFile(null);
    } finally {
      setIsUploading(false);
    }
  };

  // Submit for Scoring
  const handleScoreResume = async () => {
    if (!uploadData?.resume_id) return;
    if (!targetRole.trim()) {
      setError('Please provide a target role title.');
      return;
    }

    setIsScoring(true);
    setError(null);
    setScoreData(null);

    try {
      const res = await fetch(`${BACKEND_URL}/api/v1/resume/score_resume/${uploadData.resume_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          target_role: targetRole,
          job_description: jobDescription || undefined,
        }),
      });

      if (!res.ok) {
        const errDetail = await res.json().catch(() => ({ detail: 'Failed to score resume.' }));
        throw new Error(errDetail.detail || 'Scoring failed');
      }

      const data: ScoreResponse = await res.json();
      setScoreData(data);
    } catch (err: any) {
      setError(err.message || 'Error occurred during resume scoring.');
    } finally {
      setIsScoring(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadData(null);
    setScoreData(null);
    setTargetRole('');
    setJobDescription('');
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const applyTemplate = (role: string, desc: string) => {
    setTargetRole(role);
    setJobDescription(desc);
  };

  // Calculate circular SVG progress values
  const strokeDashoffset = scoreData 
    ? 282.6 - (282.6 * scoreData.overall_score) / 100 
    : 282.6;

  // Render SVG Icon Helper
  const renderIcon = (type: string) => {
    switch (type) {
      case 'upload':
        return (
          <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
        );
      case 'file':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
          </svg>
        );
      case 'delete':
        return (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        );
      case 'sparkles':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m0-12.728l.707.707m11.314 11.314l.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
          </svg>
        );
      case 'chart':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="20" x2="18" y2="10"></line>
            <line x1="12" y1="20" x2="12" y2="4"></line>
            <line x1="6" y1="20" x2="6" y2="14"></line>
          </svg>
        );
      case 'bulb':
        return (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .6 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"></path>
            <line x1="9" y1="18" x2="15" y2="18"></line>
            <line x1="10" y1="22" x2="14" y2="22"></line>
          </svg>
        );
      case 'check':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--success)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="20 6 9 17 4 12"></polyline>
          </svg>
        );
      case 'x':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--danger)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        );
    }
  };

  // Helper to get color for values/scores
  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--success)';
    if (score >= 60) return 'var(--warning)';
    return 'var(--danger)';
  };

  // Helper to map waterfall indices mathematically to offsets
  const getWaterfallBars = () => {
    if (!scoreData?.waterfall_data) return null;
    
    const { base_value, values, feature_names } = scoreData.waterfall_data;
    
    // Find min and max points to calibrate horizontal scale limits
    let current = base_value;
    let minVal = base_value;
    let maxVal = base_value;
    
    const steps = values.map((val, idx) => {
      const start = current;
      current += val;
      if (current < minVal) minVal = current;
      if (current > maxVal) maxVal = current;
      return {
        name: feature_names[idx] || `Feature ${idx}`,
        value: val,
        start,
        end: current
      };
    });

    // Padding the visual range slightly
    const minRange = Math.max(0, minVal - 10);
    const maxRange = Math.min(100, maxVal + 10);
    const totalRange = maxRange - minRange || 1;

    // Convert values to container percentage widths and offsets
    const baseWidth = ((base_value - minRange) / totalRange) * 100;
    const finalWidth = ((current - minRange) / totalRange) * 100;
    const baseOffset = 0;

    const renderedSteps = steps.map((s) => {
      const startPercent = ((Math.min(s.start, s.end) - minRange) / totalRange) * 100;
      const widthPercent = (Math.abs(s.value) / totalRange) * 100;
      
      let friendlyName = s.name;
      if (s.name === 'ats_score') friendlyName = 'ATS Compliance';
      else if (s.name === 'content_score') friendlyName = 'Content Quality';
      else if (s.name === 'keyword_score') friendlyName = 'Keyword Matching';
      else if (s.name === 'semantic_score') friendlyName = 'Semantic Relevance';

      return {
        name: friendlyName,
        value: s.value,
        offset: startPercent,
        width: widthPercent,
        type: s.value >= 0 ? 'positive' : 'negative'
      };
    });

    return {
      minRange,
      maxRange,
      base: {
        name: 'Model Base Value',
        value: base_value,
        offset: ((minRange) < 0 ? Math.abs(minRange)/totalRange : 0) * 100,
        width: baseWidth
      },
      steps: renderedSteps,
      final: {
        name: 'Overall Score',
        value: current,
        offset: 0,
        width: finalWidth
      }
    };
  };

  const wData = getWaterfallBars();

  return (
    <main className="app-container">
      {/* Top Header Navigation */}
      <header className="app-header">
        <div className="logo-section">
          <h1>
            Resume AI Optimizer <span className="logo-badge">PRO</span>
          </h1>
          <p>Explainable Machine-Learning ATS Optimization Engine</p>
        </div>
        <div className="api-status">
          <span className={`status-dot ${apiOnline === true ? 'online' : apiOnline === false ? 'offline' : ''}`} />
          {apiOnline === true ? 'AI Engine Active' : apiOnline === false ? 'AI Engine Offline' : 'Connecting...'}
        </div>
      </header>

      <div className="dashboard-grid">
        {/* Left Column: Form Upload & Config */}
        <section className="glass-panel">
          <h2 className="section-title">
            {renderIcon('sparkles')}
            1. Document & Role Input
          </h2>

          {/* Error Alert */}
          {error && (
            <div className="error-box">
              {renderIcon('x')}
              <div>
                <strong>Error:</strong> {error}
              </div>
            </div>
          )}

          {/* File Upload Zone */}
          {!file ? (
            <div
              className={`upload-zone ${isDragActive ? 'drag-active' : ''}`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                className="hidden"
                style={{ display: 'none' }}
                accept=".pdf,.docx,.txt"
                onChange={handleFileChange}
              />
              {renderIcon('upload')}
              <div className="upload-text">
                <h3>Drag & drop your resume</h3>
                <p>Supports PDF, DOCX, and TXT (Max 10MB)</p>
              </div>
            </div>
          ) : (
            <div className="file-card">
              <div className="file-info">
                {renderIcon('file')}
                <div className="file-meta">
                  <h4>{file.name}</h4>
                  <p>{(file.size / 1024).toFixed(1)} KB • {isUploading ? 'Parsing...' : 'Uploaded'}</p>
                </div>
              </div>
              {!isUploading && !isScoring && (
                <button className="btn-icon" onClick={handleReset} title="Remove file">
                  {renderIcon('delete')}
                </button>
              )}
            </div>
          )}

          {/* Upload loading state */}
          {isUploading && (
            <div style={{ textAlign: 'center', margin: '1.5rem 0', color: 'var(--text-secondary)' }}>
              <p style={{ fontSize: '0.875rem', marginBottom: '0.5rem' }}>Extracting sections and analyzing structural layout...</p>
              <div className="pulse-loader">
                <span className="pulse-bubble" />
                <span className="pulse-bubble" />
                <span className="pulse-bubble" />
              </div>
            </div>
          )}

          {/* Pre-flight ATS findings (displays immediately after file upload) */}
          {uploadData && (
            <div className="preflight-container">
              <div className="preflight-header">
                <span>ATS Pre-Flight Scan</span>
                <span style={{ color: 'var(--success)' }}>Complete</span>
              </div>
              <div className="preflight-grid">
                <div className="preflight-badge">
                  <span className="badge-label">Word Count:</span>
                  <span className="badge-val">{uploadData.word_count}</span>
                </div>
                <div className="preflight-badge">
                  <span className="badge-label">Pages:</span>
                  <span className="badge-val">{uploadData.page_count}</span>
                </div>
                <div className="preflight-badge">
                  <span className="badge-label">File Layout:</span>
                  <span className={`badge-val ${uploadData.ats_flags.columns_detected ? 'pass' : 'pass'}`}>
                    {uploadData.ats_flags.columns_detected ? 'Multi-Column' : 'Standard'}
                  </span>
                </div>
                <div className="preflight-badge">
                  <span className="badge-label">Scanned Image:</span>
                  <span className={`badge-val ${uploadData.ats_flags.is_scanned_pdf ? 'fail' : 'pass'}`}>
                    {uploadData.ats_flags.is_scanned_pdf ? 'Yes (Bad)' : 'No (Good)'}
                  </span>
                </div>
              </div>

              {/* Parsing Warnings */}
              {uploadData.warnings && uploadData.warnings.length > 0 && (
                <div className="warning-box">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ flexShrink: 0 }}>
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                    <line x1="12" y1="9" x2="12" y2="13" />
                    <line x1="12" y1="17" x2="12.01" y2="17" />
                  </svg>
                  <div>
                    {uploadData.warnings.map((warn, i) => (
                      <div key={i}>{warn}</div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Job description & Role Details Form */}
          {uploadData && (
            <div style={{ marginTop: '2rem', animation: 'slide-up 0.4s forwards' }}>
              <div className="form-group">
                <label htmlFor="target-role">Target Role / Title</label>
                <input
                  id="target-role"
                  className="input-text"
                  type="text"
                  placeholder="e.g. Senior Backend Engineer"
                  value={targetRole}
                  onChange={(e) => setTargetRole(e.target.value)}
                  disabled={isScoring}
                />
              </div>

              <div className="form-group">
                <label htmlFor="job-description">Job Description / Requirements (Optional)</label>
                <textarea
                  id="job-description"
                  className="textarea-description"
                  placeholder="Paste the target job description here to enable semantic keyword gap scoring and requirements matching..."
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  disabled={isScoring}
                />
              </div>

              {/* Quick Template Selector */}
              <div style={{ marginBottom: '1.5rem' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>Quick JD Templates</span>
                <div className="templates-list">
                  {ROLE_TEMPLATES.map((tpl, idx) => (
                    <button
                      key={idx}
                      className="template-btn"
                      type="button"
                      onClick={() => applyTemplate(tpl.role, tpl.description)}
                      disabled={isScoring}
                    >
                      {tpl.role}
                    </button>
                  ))}
                </div>
              </div>

              <button
                className="btn-primary"
                onClick={handleScoreResume}
                disabled={isScoring || !targetRole.trim()}
              >
                {isScoring ? (
                  <>
                    <span>Running ML scoring pipeline...</span>
                    <span className="pulse-loader" style={{ marginLeft: '0.5rem' }}>
                      <span className="pulse-bubble" />
                      <span className="pulse-bubble" />
                      <span className="pulse-bubble" />
                    </span>
                  </>
                ) : (
                  <>
                    <span>Analyze & Score Resume</span>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polygon points="5 3 19 12 5 21 5 3"></polygon>
                    </svg>
                  </>
                )}
              </button>
            </div>
          )}
        </section>

        {/* Right Column: Visualization & Results Dashboard */}
        <section className="glass-panel" style={{ minHeight: '500px' }}>
          <h2 className="section-title">
            {renderIcon('chart')}
            2. AI Explainability Dashboard
          </h2>

          {isScoring && !scoreData && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '8rem 2rem' }}>
              <div className="pulse-loader" style={{ marginBottom: '1.5rem' }}>
                <span className="pulse-bubble" style={{ width: '12px', height: '12px' }} />
                <span className="pulse-bubble" style={{ width: '12px', height: '12px' }} />
                <span className="pulse-bubble" style={{ width: '12px', height: '12px' }} />
              </div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700, marginBottom: '0.25rem' }}>Calculating Feature Contributions</h3>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', textAlign: 'center', maxWidth: '350px' }}>
                Running the XGBoost inference model and estimating game-theoretic SHAP values...
              </p>
            </div>
          )}

          {!scoreData && !isScoring && (
            <div className="empty-results">
              <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h2>No analysis generated yet</h2>
              <p>Upload a resume and click the analyze button to generate scores, structural diagnostics, and AI recommendations.</p>
            </div>
          )}

          {scoreData && (
            <div className="results-dashboard">
              {/* Score Header Grid */}
              <div className="results-header">
                {/* Radial Gauge */}
                <div className="score-circle-container">
                  <svg className="gauge-svg" width="120" height="120" viewBox="0 0 100 100">
                    <circle className="gauge-bg" cx="50" cy="50" r="45" />
                    <circle
                      className="gauge-path"
                      cx="50"
                      cy="50"
                      r="45"
                      stroke={getScoreColor(scoreData.overall_score)}
                      strokeDasharray="282.6"
                      strokeDashoffset={strokeDashoffset}
                    />
                  </svg>
                  <div className="score-overlay">
                    <span className="score-num" style={{ color: getScoreColor(scoreData.overall_score) }}>
                      {Math.round(scoreData.overall_score)}
                    </span>
                    <div className="score-grade">{scoreData.grade}</div>
                  </div>
                </div>

                {/* Explanation text */}
                <div className="explanation-card">
                  <h3 style={{ color: getScoreColor(scoreData.overall_score) }}>Grade {scoreData.grade} Match</h3>
                  <p>{scoreData.explanation_text}</p>
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                    Scored in {scoreData.processing_time_ms}ms • Powered by XGBoost Regressor v1.0
                  </p>
                </div>
              </div>

              {/* Sub-Scores Matrix */}
              <div className="subscores-grid">
                {[
                  { label: 'ATS Scan', val: scoreData.ats_score },
                  { label: 'Quality', val: scoreData.content_score },
                  { label: 'Keywords', val: scoreData.keyword_score },
                  { label: 'Semantic', val: scoreData.semantic_score },
                ].map((sc, idx) => (
                  <div key={idx} className="subscore-card">
                    <div className="subscore-label">{sc.label}</div>
                    <div className="subscore-value" style={{ color: getScoreColor(sc.val) }}>
                      {Math.round(sc.val)}
                    </div>
                    <div className="subscore-bar-container">
                      <div
                        className="subscore-bar"
                        style={{
                          width: `${sc.val}%`,
                          backgroundColor: getScoreColor(sc.val),
                          boxShadow: `0 0 6px ${getScoreColor(sc.val)}`
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* SHAP Waterfall Chart */}
              {wData && (
                <div className="waterfall-section">
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                    Feature Impact (SHAP Waterfall)
                  </h3>
                  <div className="waterfall-container">
                    {/* Base Value Row */}
                    <div className="waterfall-row">
                      <div className="waterfall-label">Model Base Value</div>
                      <div className="waterfall-bar-track">
                        <div
                          className="waterfall-bar base"
                          style={{
                            left: `${wData.base.offset}%`,
                            width: `${wData.base.width}%`
                          }}
                        />
                      </div>
                      <div className="waterfall-val neutral">{wData.base.value.toFixed(1)}</div>
                    </div>

                    {/* Step Rows */}
                    {wData.steps.map((step, idx) => (
                      <div key={idx} className="waterfall-row">
                        <div className="waterfall-label">{step.name}</div>
                        <div className="waterfall-bar-track">
                          <div
                            className={`waterfall-bar ${step.type}`}
                            style={{
                              left: `${step.offset}%`,
                              width: `${step.width}%`
                            }}
                          />
                        </div>
                        <div className={`waterfall-val ${step.type === 'positive' ? 'pos' : 'neg'}`}>
                          {step.value >= 0 ? '+' : ''}
                          {step.value.toFixed(1)}
                        </div>
                      </div>
                    ))}

                    {/* Final Output Row */}
                    <div className="waterfall-row" style={{ marginTop: '0.75rem', paddingTop: '0.75rem', borderTop: '1px solid var(--panel-border)' }}>
                      <div className="waterfall-label" style={{ fontWeight: 800, color: 'var(--text-primary)' }}>Final Score</div>
                      <div className="waterfall-bar-track">
                        <div
                          className="waterfall-bar final"
                          style={{
                            left: `${wData.final.offset}%`,
                            width: `${wData.final.width}%`,
                            backgroundColor: getScoreColor(wData.final.value)
                          }}
                        />
                      </div>
                      <div className="waterfall-val neutral" style={{ fontWeight: 800, fontSize: '1rem', color: getScoreColor(wData.final.value) }}>
                        {wData.final.value.toFixed(1)}
                      </div>
                    </div>

                    {/* Legend */}
                    <div className="waterfall-legend">
                      <div className="legend-item">
                        <span className="legend-color base-c" />
                        <span>Baseline</span>
                      </div>
                      <div className="legend-item">
                        <span className="legend-color pos-c" />
                        <span>Positive Impact</span>
                      </div>
                      <div className="legend-item">
                        <span className="legend-color neg-c" />
                        <span>Negative Impact</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Actionable Suggestions */}
              {scoreData.suggestions && scoreData.suggestions.length > 0 && (
                <div className="suggestions-section">
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                    {renderIcon('bulb')}
                    Actionable Improvement Plan
                  </h3>
                  <div className="suggestions-list">
                    {scoreData.suggestions
                      .sort((a, b) => a.impact - b.impact) // show most critical/negative first
                      .map((sug, idx) => (
                        <div key={idx} className="suggestion-item">
                          <div className="suggestion-content">
                            <span className={`suggestion-cat-badge ${sug.category}`}>
                              {sug.category}
                            </span>
                            <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                              {sug.message}
                            </span>
                          </div>
                          <span className={`suggestion-impact-badge ${sug.impact >= 0 ? 'pos' : 'neg'}`}>
                            {sug.impact >= 0 ? '+' : ''}
                            {sug.impact.toFixed(1)} pts
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Keyword Gaps */}
              {scoreData.keyword_gaps && scoreData.keyword_gaps.length > 0 && (
                <div className="gaps-section">
                  <div className="gaps-header">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polygon points="12 2 2 7 12 12 22 7 12 2"></polygon>
                      <polyline points="2 17 12 22 22 17"></polyline>
                      <polyline points="2 12 12 17 22 12"></polyline>
                    </svg>
                    <span>Missing Critical Keywords ({scoreData.keyword_gaps.length})</span>
                  </div>
                  <div className="gaps-container">
                    {scoreData.keyword_gaps.map((word, idx) => (
                      <span key={idx} className="gap-pill">
                        {renderIcon('x')}
                        {word}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
