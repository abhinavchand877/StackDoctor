import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scansAPI } from '../services/api';
import {
  FolderKanban,
  Activity,
  AlertTriangle,
  UploadCloud,
  ArrowRight,
  ShieldAlert,
  FileCode2,
  PackageCheck,
  Container,
  Workflow,
  KeyRound,
  ExternalLink,
} from 'lucide-react';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState({
    total_scans: 0,
    average_score: 0,
    total_issues: 0,
    category_stats: {},
  });
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const res = await scansAPI.list();
      setMetrics(res.data.metrics || {});
      setScans(res.data.scans || []);
    } catch (err) {
      setError('Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  const getScoreBadgeClass = (score) => {
    if (score >= 85) return 'badge-healthy';
    if (score >= 70) return 'badge-review';
    return 'badge-attention';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '80px 0', color: '#64748b' }}>
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Loading project analytics...</div>
      </div>
    );
  }

  const categoryCards = [
    { name: 'Project Structure', icon: <FileCode2 size={20} color="#2563eb" /> },
    { name: 'Dependency Analysis', icon: <PackageCheck size={20} color="#16a34a" /> },
    { name: 'Docker Configuration', icon: <Container size={20} color="#0284c7" /> },
    { name: 'GitHub Actions', icon: <Workflow size={20} color="#7c3aed" /> },
    { name: 'Security Configuration', icon: <KeyRound size={20} color="#dc2626" /> },
  ];

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Project Health Dashboard</h1>
          <p className="page-subtitle">Continuous static inspection &amp; deployment readiness monitoring</p>
        </div>
        <Link to="/scan/new" className="btn btn-primary">
          <UploadCloud size={18} />
          New Project Scan
        </Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      {/* Aggregate Metric Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon" style={{ backgroundColor: '#eff6ff', color: '#2563eb' }}>
            <FolderKanban size={22} />
          </div>
          <div>
            <div className="stat-value">{metrics.total_scans}</div>
            <div className="stat-label">Total Scans Performed</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ backgroundColor: '#f0fdf4', color: '#16a34a' }}>
            <Activity size={22} />
          </div>
          <div>
            <div className="stat-value">
              {metrics.total_scans > 0 ? `${metrics.average_score} / 100` : 'N/A'}
            </div>
            <div className="stat-label">Average Health Score</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon" style={{ backgroundColor: '#fef2f2', color: '#dc2626' }}>
            <AlertTriangle size={22} />
          </div>
          <div>
            <div className="stat-value">{metrics.total_issues}</div>
            <div className="stat-label">Total Detected Issues</div>
          </div>
        </div>
      </div>

      {/* Category-Wise Inspection Statistics */}
      {metrics.total_scans > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '14px', color: '#0f172a' }}>
            Inspection Modules Overview
          </h3>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px',
          }}>
            {categoryCards.map((cat) => {
              const stats = metrics.category_stats?.[cat.name] || { passed: 0, warning: 0, failed: 0, total_issues: 0 };
              return (
                <div key={cat.name} className="card" style={{ padding: '16px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                    {cat.icon}
                    <span style={{ fontSize: '13px', fontWeight: 600 }}>{cat.name}</span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#64748b' }}>
                    <span style={{ color: '#dc2626', fontWeight: 600 }}>{stats.failed} failures</span> •{' '}
                    <span style={{ color: '#d97706', fontWeight: 600 }}>{stats.warning} warnings</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recent Scans Section */}
      <div className="card">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '20px',
        }}>
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: 700 }}>Recent Project Scans</h2>
            <p style={{ fontSize: '13px', color: '#64748b' }}>Latest inspection results and health reports</p>
          </div>
          {scans.length > 0 && (
            <Link to="/history" style={{ fontSize: '13px', color: '#2563eb', fontWeight: 600 }}>
              View All History →
            </Link>
          )}
        </div>

        {scans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <div style={{
              width: '56px',
              height: '56px',
              borderRadius: '50%',
              backgroundColor: '#eff6ff',
              color: '#2563eb',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '16px',
            }}>
              <UploadCloud size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>No Scans Performed Yet</h3>
            <p style={{ fontSize: '14px', color: '#64748b', maxWidth: '420px', margin: '0 auto 20px' }}>
              Upload your software project ZIP archive to evaluate its structure, Docker configurations, dependencies, and security posture.
            </p>
            <Link to="/scan/new" className="btn btn-primary">
              <UploadCloud size={16} />
              Run Your First Scan
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Detected Technologies</th>
                  <th>Health Score</th>
                  <th>Readiness</th>
                  <th>Risk Level</th>
                  <th>Issues</th>
                  <th>Scanned At</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {scans.slice(0, 6).map((scan) => (
                  <tr key={scan.id}>
                    <td style={{ fontWeight: 600, color: '#0f172a' }}>
                      <Link to={`/results/${scan.id}`} style={{ color: '#2563eb' }}>
                        {scan.project_name}
                      </Link>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        {scan.detected_technologies?.map((tech) => (
                          <span key={tech} className="badge badge-neutral" style={{ fontSize: '11px' }}>
                            {tech}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontWeight: 700, fontSize: '14px' }}>
                        {scan.health_score} / 100
                      </span>
                    </td>
                    <td>
                      <span
                        className="badge"
                        style={{
                          fontSize: '11px',
                          backgroundColor:
                            scan.readiness_status === 'READY'
                              ? '#f0fdf4'
                              : scan.readiness_status === 'BLOCKED'
                              ? '#fef2f2'
                              : '#fffbeb',
                          color:
                            scan.readiness_status === 'READY'
                              ? '#166534'
                              : scan.readiness_status === 'BLOCKED'
                              ? '#991b1b'
                              : '#92400e',
                          border: `1px solid ${
                            scan.readiness_status === 'READY'
                              ? '#bbf7d0'
                              : scan.readiness_status === 'BLOCKED'
                              ? '#fecaca'
                              : '#fde68a'
                          }`,
                        }}
                      >
                        {scan.readiness_status || 'READY'}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getScoreBadgeClass(scan.health_score)}`}>
                        {scan.risk_level}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{scan.total_findings}</span>
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(scan.created_at).toLocaleDateString()} {new Date(scan.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link to={`/results/${scan.id}`} className="btn btn-outline" style={{ padding: '6px 12px', fontSize: '12px' }}>
                        View Report
                        <ExternalLink size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
