import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { scansAPI } from '../services/api';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  FileDown,
  ArrowLeft,
  FileCode2,
  PackageCheck,
  Container,
  Workflow,
  KeyRound,
  FileText,
  AlertCircle,
  ExternalLink,
  Code2,
  Clock,
  Fingerprint,
} from 'lucide-react';

export default function AnalysisResultsPage() {
  const { id } = useParams();
  const [scan, setScan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('ALL');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchScanDetails();
  }, [id]);

  const fetchScanDetails = async () => {
    try {
      setLoading(true);
      const res = await scansAPI.get(id);
      setScan(res.data.scan);
    } catch (err) {
      setError(err.response?.data?.message || 'Could not load scan results.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPdf = () => {
    const pdfUrl = scansAPI.getPdfUrl(id);
    window.open(pdfUrl, '_blank');
  };

  const handleDownloadJson = async () => {
    try {
      await scansAPI.downloadJson(id, scan?.project_name);
    } catch (err) {
      alert('Failed to download JSON report: ' + (err.message || 'Error'));
    }
  };

  const handleDownloadSarif = async () => {
    try {
      await scansAPI.downloadSarif(id, scan?.project_name);
    } catch (err) {
      alert('Failed to download SARIF report: ' + (err.message || 'Error'));
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: '#64748b' }}>
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Loading inspection report...</div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <AlertCircle size={36} color="#dc2626" style={{ margin: '0 auto 12px' }} />
        <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '8px' }}>Scan Report Unavailable</h2>
        <p style={{ color: '#64748b', marginBottom: '20px' }}>{error || 'The requested scan could not be retrieved.'}</p>
        <Link to="/history" className="btn btn-secondary">
          <ArrowLeft size={16} />
          Return to History
        </Link>
      </div>
    );
  }

  const getScoreColor = (score) => {
    if (score >= 85) return '#16a34a';
    if (score >= 70) return '#d97706';
    return '#dc2626';
  };

  const getReadinessBadge = (status) => {
    if (status === 'READY') {
      return { bg: '#f0fdf4', text: '#166534', border: '#bbf7d0', icon: <CheckCircle2 size={16} /> };
    }
    if (status === 'READY WITH WARNINGS') {
      return { bg: '#fffbeb', text: '#92400e', border: '#fde68a', icon: <AlertTriangle size={16} /> };
    }
    if (status === 'BLOCKED') {
      return { bg: '#fef2f2', text: '#991b1b', border: '#fecaca', icon: <ShieldAlert size={16} /> };
    }
    return { bg: '#f8fafc', text: '#475569', border: '#e2e8f0', icon: <AlertCircle size={16} /> };
  };

  const getSeverityBadgeClass = (severity) => {
    const sev = (severity || '').toLowerCase();
    if (sev === 'critical') return 'badge-failed';
    if (sev === 'high') return 'badge-failed';
    if (sev === 'medium') return 'badge-warning';
    if (sev === 'low') return 'badge-passed';
    return 'badge-neutral';
  };

  const summary = scan.scan_summary || {};
  const categoryScores = scan.category_scores || {};
  const findings = scan.findings || [];
  const readiness = getReadinessBadge(scan.readiness_status);

  // Filter findings based on active tab, severity, and search query
  const filteredFindings = findings.filter((f) => {
    const mod = f.category || f.module;
    const matchModule = activeTab === 'ALL' || f.module === activeTab || f.category === activeTab;
    const matchSev =
      severityFilter === 'ALL' ||
      f.severity?.toUpperCase() === severityFilter.toUpperCase();
    const query = searchQuery.trim().toLowerCase();
    const matchSearch =
      !query ||
      f.title?.toLowerCase().includes(query) ||
      f.rule_id?.toLowerCase().includes(query) ||
      f.file_path?.toLowerCase().includes(query) ||
      f.description?.toLowerCase().includes(query);

    return matchModule && matchSev && matchSearch;
  });

  const moduleTabs = [
    { key: 'ALL', label: 'All Findings', count: findings.length },
    { key: 'Project Structure', label: '1. Project Structure', icon: <FileCode2 size={16} /> },
    { key: 'Dependency Analysis', label: '2. Dependencies', icon: <PackageCheck size={16} /> },
    { key: 'Docker Configuration', label: '3. Docker', icon: <Container size={16} /> },
    { key: 'GitHub Actions', label: '4. GitHub Actions', icon: <Workflow size={16} /> },
    { key: 'Security Configuration', label: '5. Security', icon: <KeyRound size={16} /> },
  ];

  return (
    <div>
      {/* Back Link & Header */}
      <div style={{ marginBottom: '16px' }}>
        <Link to="/dashboard" style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '13px',
          color: '#64748b',
          fontWeight: 600,
        }}>
          <ArrowLeft size={14} /> Back to Dashboard
        </Link>
      </div>

      <div className="page-header" style={{ marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <h1 className="page-title">{scan.project_name}</h1>
            <span className={`badge ${scan.health_score >= 85 ? 'badge-healthy' : scan.health_score >= 70 ? 'badge-review' : 'badge-attention'}`}>
              Health: {scan.risk_level}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px', color: '#64748b', marginTop: '6px', flexWrap: 'wrap' }}>
            <span><Fingerprint size={13} style={{ display: 'inline', verticalAlign: '-2px' }} /> <code>{scan.uuid || `SCAN-${scan.id}`}</code></span>
            <span>•</span>
            <span>Archive: <code>{scan.original_filename}</code></span>
            <span>•</span>
            <span><Clock size={13} style={{ display: 'inline', verticalAlign: '-2px' }} /> {scan.scan_duration}s</span>
            <span>•</span>
            <span>{new Date(scan.created_at).toLocaleString()}</span>
          </div>
        </div>

        {/* Export Buttons */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <button onClick={handleDownloadPdf} className="btn btn-secondary" style={{ padding: '8px 14px', fontSize: '13px' }}>
            <FileDown size={15} /> PDF
          </button>
          <button onClick={handleDownloadJson} className="btn btn-secondary" style={{ padding: '8px 14px', fontSize: '13px' }}>
            <FileDown size={15} /> JSON
          </button>
          <button onClick={handleDownloadSarif} className="btn btn-secondary" style={{ padding: '8px 14px', fontSize: '13px' }}>
            <FileDown size={15} /> SARIF
          </button>
        </div>
      </div>

      {/* Deployment Readiness Banner */}
      <div style={{
        backgroundColor: readiness.bg,
        border: `1px solid ${readiness.border}`,
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: readiness.text, fontWeight: 700, fontSize: '15px' }}>
            {readiness.icon}
            <span>Deployment Readiness Status: {scan.readiness_status}</span>
          </div>
          <span style={{ fontSize: '12px', color: readiness.text, fontWeight: 600 }}>
            {scan.readiness_status === 'BLOCKED' ? 'Production Release Blocked' : scan.readiness_status === 'READY' ? 'Ready for Deployment' : 'Review Warnings Before Deploy'}
          </span>
        </div>

        {scan.readiness_reasons && scan.readiness_reasons.length > 0 && (
          <ul style={{ margin: '6px 0 0 20px', padding: 0, fontSize: '13px', color: readiness.text, lineHeight: 1.5 }}>
            {scan.readiness_reasons.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        )}
      </div>

      {/* Overview Score & Metrics Banner */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px',
        marginBottom: '28px',
      }}>
        {/* Health Score Card */}
        <div className="card" style={{
          textAlign: 'center',
          padding: '24px 20px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#ffffff',
        }}>
          <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px' }}>
            Overall Health Score
          </div>
          <div style={{
            fontSize: '52px',
            fontWeight: 800,
            lineHeight: 1,
            color: getScoreColor(scan.health_score),
            marginBottom: '6px',
          }}>
            {scan.health_score}
            <span style={{ fontSize: '20px', color: '#94a3b8', fontWeight: 600 }}>/100</span>
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: '#0f172a', marginBottom: '4px' }}>
            {scan.risk_level}
          </div>
          <p style={{ fontSize: '12px', color: '#64748b', lineHeight: 1.4, margin: 0 }}>
            Weighted assessment across 5 core static quality domains.
          </p>
        </div>

        {/* Detailed Stats Card */}
        <div className="card" style={{ padding: '24px' }}>
          <div style={{ marginBottom: '14px' }}>
            <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#64748b', letterSpacing: '0.05em' }}>
              Detected Stack & Frameworks
            </span>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginTop: '6px' }}>
              {scan.detected_technologies?.map((tech) => (
                <span key={tech} className="badge badge-neutral" style={{ fontSize: '12px', padding: '4px 10px' }}>
                  {tech}
                </span>
              ))}
            </div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
            paddingTop: '14px',
            borderTop: '1px solid #e2e8f0',
          }}>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#0f172a' }}>{scan.total_findings}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>Total Issues</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#16a34a' }}>{scan.passed_checks}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>Passed Modules</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#d97706' }}>{scan.warning_count}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>Warnings</div>
            </div>
            <div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#dc2626' }}>{scan.failed_checks}</div>
              <div style={{ fontSize: '11px', color: '#64748b' }}>Failures</div>
            </div>
          </div>
        </div>
      </div>

      {/* Category Weights and Scores Breakdown */}
      {Object.keys(categoryScores).length > 0 && (
        <div className="card" style={{ padding: '20px', marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#1e293b', marginBottom: '14px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Domain Weights & Health Scores
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
            {Object.entries(categoryScores).map(([catName, catData]) => {
              const score = catData.score || 0;
              const weight = catData.weight || 20;
              return (
                <div key={catName} style={{ backgroundColor: '#f8fafc', padding: '12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', fontWeight: 600, color: '#334155', marginBottom: '4px' }}>
                    <span>{catName}</span>
                    <span style={{ color: '#64748b' }}>{weight}% wt</span>
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: getScoreColor(score), marginBottom: '6px' }}>
                    {score}<span style={{ fontSize: '12px', color: '#94a3b8' }}>/100</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', backgroundColor: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${score}%`, height: '100%', backgroundColor: getScoreColor(score) }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Tabs and Findings Filter */}
      <div className="tabs-nav" style={{ marginBottom: '16px' }}>
        {moduleTabs.map((t) => (
          <button
            key={t.key}
            className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.icon}
            {t.label}
          </button>
        ))}
      </div>

      {/* Filter and Search Bar */}
      <div style={{ display: 'flex', gap: '12px', marginBottom: '18px', flexWrap: 'wrap', alignItems: 'center' }}>
        <input
          type="text"
          placeholder="Filter by file path, rule ID, or keyword..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            minWidth: '220px',
            padding: '8px 12px',
            fontSize: '13px',
            borderRadius: '6px',
            border: '1px solid #cbd5e1',
          }}
        />

        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSeverityFilter(sev)}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 600,
                borderRadius: '4px',
                border: '1px solid',
                cursor: 'pointer',
                borderColor: severityFilter === sev ? '#0f172a' : '#cbd5e1',
                backgroundColor: severityFilter === sev ? '#0f172a' : '#ffffff',
                color: severityFilter === sev ? '#ffffff' : '#475569',
              }}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div>
        {filteredFindings.length === 0 ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px', backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' }}>
            <CheckCircle2 size={32} color="#16a34a" style={{ margin: '0 auto 8px' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#166534', marginBottom: '4px' }}>
              No Findings Match Filters
            </h3>
            <p style={{ fontSize: '13px', color: '#15803d' }}>
              All checks in this view passed or no issues match your filter query.
            </p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {filteredFindings.map((finding) => (
              <div key={finding.id || finding.rule_id} className="card" style={{ padding: '20px' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  justifyContent: 'space-between',
                  gap: '12px',
                  marginBottom: '10px',
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span className="badge badge-neutral" style={{ fontSize: '11px', fontFamily: 'monospace' }}>
                        {finding.rule_id}
                      </span>
                      {finding.scanner && (
                        <span style={{ fontSize: '11px', color: '#64748b', backgroundColor: '#f1f5f9', padding: '2px 6px', borderRadius: '4px', fontWeight: 600 }}>
                          {finding.scanner}
                        </span>
                      )}
                      <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                        {finding.title}
                      </h3>
                    </div>
                    {finding.file_path && (
                      <div style={{ marginTop: '6px', display: 'flex', gap: '8px', alignItems: 'center' }}>
                        <code style={{ fontSize: '12px', color: '#475569', backgroundColor: '#f1f5f9', padding: '2px 8px', borderRadius: '4px' }}>
                          {finding.file_path} {finding.line_number ? `:${finding.line_number}` : ''}
                        </code>
                      </div>
                    )}
                  </div>
                  <span className={`badge ${getSeverityBadgeClass(finding.severity)}`}>
                    {finding.severity}
                  </span>
                </div>

                <p style={{ fontSize: '14px', color: '#334155', marginBottom: '10px', lineHeight: 1.5 }}>
                  {finding.description}
                </p>

                {finding.masked_evidence && (
                  <div style={{ marginBottom: '10px' }}>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase' }}>Evidence: </span>
                    <code style={{ fontSize: '12px', color: '#dc2626', backgroundColor: '#fef2f2', padding: '2px 6px', borderRadius: '4px' }}>
                      {finding.masked_evidence}
                    </code>
                  </div>
                )}

                {finding.recommendation && (
                  <div style={{
                    backgroundColor: '#f8fafc',
                    border: '1px solid #e2e8f0',
                    borderRadius: '6px',
                    padding: '12px 14px',
                    fontSize: '13px',
                  }}>
                    <strong style={{ color: '#1e293b', display: 'block', marginBottom: '2px' }}>
                      Recommended Action:
                    </strong>
                    <span style={{ color: '#475569', lineHeight: 1.5 }}>
                      {finding.recommendation}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
