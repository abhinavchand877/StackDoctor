# CHANGELOG — StackDoctor

All notable changes and architectural upgrades to StackDoctor are documented in this file.

---

## [2.0.0] - Final Phase Upgrade — 2026-11-17

### Added
- **Multi-Technology Detection Engine**: Added detection and analysis support for Java (`pom.xml`, `build.gradle`), PHP (`composer.json`), and Go (`go.mod`) in addition to Python, Node.js, and React.
- **External Security & Vulnerability Scanners**:
  - `scanner_runner.py` with process timeouts and safe execution.
  - Trivy vulnerability and secret scanner integration.
  - OSV-Scanner open source vulnerability integration.
  - Hadolint Dockerfile linter integration.
  - Checkov IaC security scanner integration.
  - zizmor GitHub Actions workflow security integration.
  - Gitleaks credential detection integration.
- **Deterministic Offline Fallbacks**: Every module includes standalone AST, regex, and static parsers to ensure full analysis fidelity even when CLI binaries are absent.
- **Weighted Health Scoring Engine**:
  - Project Structure: 15%
  - Dependencies: 20%
  - Docker: 20%
  - CI/CD: 15%
  - Security: 30%
- **4-Tier Deployment Readiness Engine**:
  - `READY`: Health score $\ge$ 85, zero critical or high issues.
  - `READY WITH WARNINGS`: Health score $\ge$ 60 with non-blocking warnings.
  - `BLOCKED`: Triggered by any Critical finding (exposed secrets, private keys, broken manifests) or Security score < 50.
  - `INSUFFICIENT DATA`: Triggered when project architecture is unrecognized.
  - Explicit blocker explanations generated for every blocked scan.
- **Report & Export Formats**:
  - SARIF v2.1.0 exporter (`/api/scans/<id>/report/sarif`) for GitHub Code Scanning and SonarQube.
  - Structured JSON exporter (`/api/scans/<id>/report/json`).
  - CycloneDX v1.5 SBOM generator (`/api/scans/<id>/report/sbom`).
  - Enhanced ReportLab PDF generator with readiness badges and domain score tables.
- **Asynchronous Task Processing Architecture**:
  - Celery worker and Redis queue integration (`app.tasks.celery_app`).
  - Graceful synchronous fallback when worker is offline.
- **Scan Comparison Endpoint**:
  - `GET /api/scans/compare?base_id=<id1>&target_id=<id2>` calculating score delta and finding changes.
- **Custom Project Policies**:
  - `.stackdoctor.yml` policy evaluation for required repository files and blacklisted packages.
- **Database Enhancements**:
  - Added `Recommendation` model linking findings to actionable code fixes.
  - Added UUID, readiness status, readiness reasons, scan duration, and category scores to `Scan` entity.
  - Added line numbers, scanner source, and masked evidence to `Finding` entity.
- **Frontend Dashboard Enhancements**:
  - Added Deployment Readiness status badges across Dashboard, History, and Results pages.
  - Added one-click export buttons for PDF, JSON, and SARIF.
  - Added domain score weight breakdown cards.
  - Added search, keyword filtering, and scanner source tags to findings.

### Changed
- Preserved existing Flask application factory, SQLite/MySQL configuration, and JWT authentication.
- Maintained backward compatibility across all legacy routes while adding sub-resource endpoints.
- Fixed Vitest localStorage compatibility for Node 22 test environments.

### Security
- Verified zero code execution guarantee across all analyzers.
- Confirmed strict secret masking across API payloads, database models, and PDF/JSON reports.
- Hardened ZIP extraction against ZipSlip and decompression ratio abuse.

---

## [1.0.0] - Baseline Initial Release — 2026-11-12
- Initial proof-of-concept with 5 static analysis modules.
- Secure ZIP upload sandbox with ZipSlip and ZIP bomb defenses.
- Basic 0–100 rule engine.
- ReportLab PDF generator.
- React/Vite dashboard with user authentication.
