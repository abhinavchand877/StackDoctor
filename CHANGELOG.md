# CHANGELOG — StackDoctor

All notable changes and architectural upgrades to StackDoctor are documented in this file.

---

## [2.1.1] - Docker Multi-Container Runtime & Celery Worker Stability Fixes — 2026-11-18

### Fixed
- **Celery Worker Startup Crash**:
  - Resolved `AttributeError: 'function' object has no attribute 'user_options'` by correcting Docker Compose worker command to target the Celery application instance (`app.tasks.celery_app.celery`).
  - Resolved Kombu transport `VersionMismatch` error by updating `redis>=6.1.0` in `backend/requirements.txt`.
  - Added dedicated Celery ping health check (`celery inspect ping`) in Docker Compose.
- **Database Table Creation Concurrency (Gunicorn Race Condition)**:
  - Eliminated `(1050, "Table 'scans' already exists")` OperationalError during startup across concurrent Gunicorn worker processes by introducing MySQL advisory distributed locking (`GET_LOCK('stackdoctor_init_lock', 20)`) in `backend/app/__init__.py`.
- **Frontend Container Health Check**:
  - Resolved `wget: connection refused` inside Alpine Linux by binding Nginx to both IPv4 and IPv6 (`listen 80; listen [::]:80;`) and updating Dockerfile health check to probe `127.0.0.1:80`.
- **Cross-Container Async File Sharing**:
  - Configured shared `uploads_data:/app/tmp` named Docker volume between `backend` and `worker` services so background scan tasks seamlessly process uploaded ZIP archives.
  - Corrected `Recommendation` entity constructor arguments in asynchronous task handler.
- **Eliminated Docker Container Name Collisions**:
  - Removed fixed `container_name` declarations from `docker-compose.yml` to allow Docker Compose to automatically project-scope container names (`cdd-finalphase-*-1`), preventing naming conflicts across workspaces.

---

## [2.1.0] - Final Project Audit, GitHub Readiness, CI/CD & Docker Hardening — 2026-11-18

### Added
- **Repository Root Docker Ignore**: Added root `.dockerignore` preventing transfer of sensitive environment files, caches, and test artifacts into Docker build contexts.
- **Canonical `docker/` Architecture**: Created `docker/Dockerfile.backend` and `docker/Dockerfile.frontend` supporting repository-root build contexts while preserving `backend/Dockerfile` and `frontend/Dockerfile`.
- **Comprehensive `.gitignore` Hardening**: Added exclusions for Python caches (`.mypy_cache`, `.ruff_cache`), coverage reports, database dumps (`*.dump`, `*.sql`), certificates (`*.pfx`, `*.p12`, `*.crt`), service account credentials (`*service-account*.json`), and test artifacts without blocking manifest JSON files.
- **CI/CD Quality Gates in GitHub Actions**:
  - Added backend configuration and module import validation step in `backend-tests`.
  - Added Docker Compose syntax validation (`docker compose config`) step in `docker-validation`.
  - Added strict environment variable validation test verifying informative errors on missing production variables.
- **Environment Variable Validation**: Added strict validation in `backend/app/__init__.py` verifying that `SECRET_KEY`, `JWT_SECRET_KEY`, and `DATABASE_URL` are provided in `production` mode with descriptive error messages.

### Changed
- **Debug Mode Lockdown**: Hardened `backend/run.py` to ensure `debug` mode is strictly disabled when running in production mode regardless of environment variables.
- **Frontend API Config**: Enhanced `frontend/src/services/api.js` to dynamically read `import.meta.env.VITE_API_URL` while maintaining `/api` default for reverse proxy environments.

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
