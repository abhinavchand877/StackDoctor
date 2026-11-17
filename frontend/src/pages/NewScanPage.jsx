import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { scansAPI } from '../services/api';
import {
  UploadCloud,
  FileArchive,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Code2,
} from 'lucide-react';

export default function NewScanPage() {
  const [file, setFile] = useState(null);
  const [projectName, setProjectName] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scanStep, setScanStep] = useState('');
  const [error, setError] = useState('');

  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelection(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelection = (selectedFile) => {
    setError('');
    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
      setError('Invalid file type. Only ZIP archives (.zip) are supported.');
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setError('File size exceeds the 50 MB limit.');
      return;
    }
    setFile(selectedFile);
    if (!projectName) {
      const baseName = selectedFile.name.replace(/\.[^/.]+$/, '');
      setProjectName(baseName);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a project ZIP archive to scan.');
      return;
    }

    setLoading(true);
    setError('');
    setScanStep('Uploading archive & verifying compression safety...');

    const formData = new FormData();
    formData.append('file', file);
    if (projectName.trim()) {
      formData.append('project_name', projectName.trim());
    }

    try {
      setTimeout(() => setScanStep('Detecting frameworks & unpacking isolated sandbox...'), 600);
      setTimeout(() => setScanStep('Executing 5-module static inspection heuristics...'), 1200);

      const res = await scansAPI.create(formData);
      const scanId = res.data.scan.id;
      navigate(`/results/${scanId}`);
    } catch (err) {
      const msg = err.response?.data?.message || err.response?.data?.error || 'Failed to analyze project archive.';
      setError(msg);
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">New Project Scan</h1>
          <p className="page-subtitle">Inspect repository layout, dependencies, Docker, CI/CD, and security</p>
        </div>
      </div>

      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Required Explanatory Banner */}
        <div className="card" style={{
          backgroundColor: '#eff6ff',
          borderColor: '#bfdbfe',
          marginBottom: '24px',
          display: 'flex',
          gap: '16px',
          alignItems: 'center',
        }}>
          <div style={{ color: '#2563eb' }}>
            <ShieldCheck size={32} />
          </div>
          <div>
            <p style={{ fontSize: '14px', fontWeight: 600, color: '#1e3a8a', lineHeight: 1.5 }}>
              Upload your project ZIP file and StackDoctor will automatically inspect its structure,
              dependencies, Docker configuration and CI/CD setup.
            </p>
            <p style={{ fontSize: '12px', color: '#3b82f6', marginTop: '4px' }}>
              Static analysis only • No uploaded scripts, binaries, or container builds are executed.
            </p>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ marginBottom: '24px' }}>
            {/* Project Name Field */}
            <div className="form-group">
              <label className="form-label">Project Name (Optional)</label>
              <input
                type="text"
                className="form-input"
                placeholder="e.g. MyAwesomeApp"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                disabled={loading}
              />
              <span style={{ fontSize: '12px', color: '#64748b', marginTop: '4px', display: 'block' }}>
                Defaults to the archive filename if left blank.
              </span>
            </div>

            {/* Drag & Drop Upload Zone */}
            <div
              className={`dropzone ${dragActive ? 'dropzone-active' : ''}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              style={{ marginBottom: '20px' }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                style={{ display: 'none' }}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileSelection(e.target.files[0]);
                  }
                }}
                disabled={loading}
              />

              <div className="dropzone-icon">
                <FileArchive size={48} />
              </div>

              {file ? (
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                    {file.name}
                  </div>
                  <div style={{ fontSize: '13px', color: '#16a34a', fontWeight: 600, marginTop: '4px' }}>
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready to inspect
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b', marginTop: '6px' }}>
                    Click or drop another file to change archive
                  </div>
                </div>
              ) : (
                <div>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                    Drop your project ZIP file here, or browse
                  </div>
                  <div style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>
                    Standard .zip archives up to 50 MB compressed (150 MB extracted limit)
                  </div>
                </div>
              )}
            </div>

            {/* Supported Technologies Pill List */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>
                Supported Frameworks:
              </span>
              <span className="badge badge-neutral">Python (Flask, Django, FastAPI)</span>
              <span className="badge badge-neutral">Node.js (Express, Nest, TS)</span>
              <span className="badge badge-neutral">React (Vite, CRA, Next.js)</span>
              <span className="badge badge-neutral">Docker / Compose</span>
              <span className="badge badge-neutral">GitHub Actions</span>
            </div>
          </div>

          {/* Submit / Progress Section */}
          {loading ? (
            <div className="card" style={{ textAlign: 'center', padding: '32px' }}>
              <Loader2 size={32} className="spin-animation" style={{ color: '#2563eb', margin: '0 auto 12px' }} />
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>
                {scanStep}
              </div>
              <div style={{ fontSize: '13px', color: '#64748b', marginTop: '6px' }}>
                Please wait while StackDoctor runs static security, architecture, and Docker rules.
              </div>
            </div>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%', padding: '14px', fontSize: '15px' }}
              disabled={!file}
            >
              <UploadCloud size={18} />
              Start Automated Project Health Scan
            </button>
          )}
        </form>
      </div>
    </div>
  );
}
