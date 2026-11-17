import React from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  FileCode2,
  PackageCheck,
  Container,
  Workflow,
  KeyRound,
  FileDown,
  ArrowRight,
  CheckCircle2,
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f8fafc', color: '#0f172a' }}>
      {/* Top Navbar */}
      <header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '20px 48px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid #e2e8f0',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #2563eb, #1d4ed8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
          }}>
            <ShieldCheck size={22} />
          </div>
          <span style={{ fontSize: '20px', fontWeight: 800, letterSpacing: '-0.02em' }}>
            StackDoctor
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <Link to="/login" className="btn btn-outline" style={{ padding: '8px 18px' }}>
            Sign In
          </Link>
          <Link to="/register" className="btn btn-primary" style={{ padding: '8px 20px' }}>
            Get Started
            <ArrowRight size={16} />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{
        maxWidth: '1100px',
        margin: '0 auto',
        padding: '80px 24px 60px',
        textAlign: 'center',
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '9999px',
          backgroundColor: '#eff6ff',
          color: '#2563eb',
          fontSize: '13px',
          fontWeight: 600,
          marginBottom: '20px',
          border: '1px solid #bfdbfe',
        }}>
          <ShieldCheck size={16} />
          Safe Static Inspection • No Code Execution
        </div>

        <h1 style={{
          fontSize: '48px',
          fontWeight: 800,
          lineHeight: 1.15,
          letterSpacing: '-0.03em',
          marginBottom: '20px',
        }}>
          Automated Software Project Health Analysis <br />
          <span style={{ color: '#2563eb' }}>&amp; Deployment Readiness Platform</span>
        </h1>

        <p style={{
          fontSize: '18px',
          color: '#64748b',
          maxWidth: '720px',
          margin: '0 auto 36px',
          lineHeight: 1.6,
        }}>
          Upload your project ZIP archive and StackDoctor will automatically inspect repository layout,
          dependency pinning, Docker configurations, CI/CD pipelines, and secrets exposure without running untrusted code.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
          <Link to="/register" className="btn btn-primary" style={{ padding: '14px 28px', fontSize: '16px' }}>
            Inspect Your Project Free
            <ArrowRight size={18} />
          </Link>
          <Link to="/login" className="btn btn-secondary" style={{ padding: '14px 24px', fontSize: '16px' }}>
            View Demo Dashboard
          </Link>
        </div>
      </section>

      {/* Feature Cards Grid */}
      <section style={{ maxWidth: '1200px', margin: '0 auto 80px', padding: '0 24px' }}>
        <h2 style={{ textAlign: 'center', fontSize: '28px', fontWeight: 700, marginBottom: '12px' }}>
          Comprehensive 5-Module Static Analysis
        </h2>
        <p style={{ textAlign: 'center', color: '#64748b', marginBottom: '40px', fontSize: '15px' }}>
          Independent inspection heuristics designed to catch common deployment blockers before production.
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '20px',
        }}>
          <div className="card">
            <div style={{ color: '#2563eb', marginBottom: '12px' }}>
              <FileCode2 size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Project Structure</h3>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Detects missing README documentation, absent .gitignore rules, missing test directories, and broken project structures.
            </p>
          </div>

          <div className="card">
            <div style={{ color: '#16a34a', marginBottom: '12px' }}>
              <PackageCheck size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Dependency Analysis</h3>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Parses requirements.txt and package.json to identify unpinned versions, missing lockfiles, and wildcard package entries.
            </p>
          </div>

          <div className="card">
            <div style={{ color: '#0284c7', marginBottom: '12px' }}>
              <Container size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Docker Configuration</h3>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Validates Dockerfile instructions, base image tags, root user avoidance, missing WORKDIR, and compose service integrity.
            </p>
          </div>

          <div className="card">
            <div style={{ color: '#7c3aed', marginBottom: '12px' }}>
              <Workflow size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>GitHub Actions CI/CD</h3>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Ensures push/PR event triggers, automated testing steps, build validation, and deployment job sanity.
            </p>
          </div>

          <div className="card">
            <div style={{ color: '#dc2626', marginBottom: '12px' }}>
              <KeyRound size={28} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '8px' }}>Security Configuration</h3>
            <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
              Identifies committed .env files, private keys, and hardcoded API tokens, with automatic masking for safe reporting.
            </p>
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section style={{ backgroundColor: '#ffffff', borderTop: '1px solid #e2e8f0', padding: '60px 24px' }}>
        <div style={{ maxWidth: '1000px', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ fontSize: '26px', fontWeight: 700, marginBottom: '32px' }}>
            How StackDoctor Works
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '32px', textAlign: 'left' }}>
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: '#3b82f6', marginBottom: '8px' }}>01</div>
              <h4 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>Upload ZIP Archive</h4>
              <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
                Drag and drop your project archive. StackDoctor verifies archive safety and unpacks files into an isolated sandbox.
              </p>
            </div>
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: '#3b82f6', marginBottom: '8px' }}>02</div>
              <h4 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>Static Inspection</h4>
              <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
                Five specialized analyzers statically evaluate syntax, manifests, configurations, and sensitive credentials without running code.
              </p>
            </div>
            <div>
              <div style={{ fontSize: '32px', fontWeight: 800, color: '#3b82f6', marginBottom: '8px' }}>03</div>
              <h4 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>Actionable Health Score</h4>
              <p style={{ fontSize: '13px', color: '#64748b', lineHeight: 1.5 }}>
                Receive an immediate health grade (0–100), itemized recommendations, and a downloadable PDF assessment report.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        padding: '24px 48px',
        backgroundColor: '#0f172a',
        color: '#94a3b8',
        fontSize: '13px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>StackDoctor © 2026 • Automated Software Project Health Analysis &amp; Deployment Readiness</div>
        <div>Built with React, Flask, MySQL &amp; ReportLab</div>
      </footer>
    </div>
  );
}
