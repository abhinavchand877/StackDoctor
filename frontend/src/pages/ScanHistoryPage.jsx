import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { scansAPI } from '../services/api';
import {
  History,
  Trash2,
  FileDown,
  ExternalLink,
  UploadCloud,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export default function ScanHistoryPage() {
  const [scans, setScans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);

  useEffect(() => {
    loadScans();
  }, []);

  const loadScans = async () => {
    try {
      setLoading(true);
      const res = await scansAPI.list();
      setScans(res.data.scans || []);
    } catch (err) {
      setError('Failed to load scan history.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await scansAPI.delete(id);
      setScans(scans.filter((s) => s.id !== id));
      setDeleteConfirmId(null);
    } catch (err) {
      setError('Failed to delete scan record.');
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
        <div style={{ fontSize: '16px', fontWeight: 600 }}>Loading scan history...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Scan History</h1>
          <p className="page-subtitle">Complete log of all previous project health assessments</p>
        </div>
        <Link to="/scan/new" className="btn btn-primary">
          <UploadCloud size={16} />
          New Scan
        </Link>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}

      <div className="card">
        {scans.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '48px 24px' }}>
            <History size={40} color="#94a3b8" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>No Prior Scans Found</h3>
            <p style={{ fontSize: '14px', color: '#64748b', marginBottom: '20px' }}>
              You haven't scanned any projects yet. Upload a ZIP archive to analyze project health.
            </p>
            <Link to="/scan/new" className="btn btn-primary">
              <UploadCloud size={16} />
              Scan a Project Now
            </Link>
          </div>
        ) : (
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Scan Date</th>
                  <th>Technologies</th>
                  <th>Health Score</th>
                  <th>Readiness</th>
                  <th>Risk Classification</th>
                  <th>Findings</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {scans.map((scan) => (
                  <tr key={scan.id}>
                    <td style={{ fontWeight: 600 }}>
                      <Link to={`/results/${scan.id}`} style={{ color: '#2563eb' }}>
                        {scan.project_name}
                      </Link>
                    </td>
                    <td style={{ fontSize: '13px', color: '#64748b' }}>
                      {new Date(scan.created_at).toLocaleDateString()} {new Date(scan.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                      <span style={{ fontWeight: 700 }}>
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
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
                        <Link
                          to={`/results/${scan.id}`}
                          className="btn btn-outline"
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                          title="View detailed results"
                        >
                          <ExternalLink size={14} />
                          View
                        </Link>

                        <a
                          href={scansAPI.getPdfUrl(scan.id)}
                          target="_blank"
                          rel="noreferrer"
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px', fontSize: '12px' }}
                          title="Download PDF report"
                        >
                          <FileDown size={14} />
                          PDF
                        </a>

                        {deleteConfirmId === scan.id ? (
                          <div style={{ display: 'inline-flex', gap: '4px' }}>
                            <button
                              onClick={() => handleDelete(scan.id)}
                              className="btn btn-danger"
                              style={{ padding: '4px 8px', fontSize: '11px' }}
                            >
                              Confirm
                            </button>
                            <button
                              onClick={() => setDeleteConfirmId(null)}
                              className="btn btn-outline"
                              style={{ padding: '4px 8px', fontSize: '11px' }}
                            >
                              Cancel
                            </button>
                          </div>
                        ) : (
                          <button
                            onClick={() => setDeleteConfirmId(scan.id)}
                            className="btn btn-outline"
                            style={{ padding: '6px 8px', color: '#94a3b8' }}
                            title="Delete scan record"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
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
