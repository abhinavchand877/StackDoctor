# STACKDOCTOR 🩺

**Intelligent Software Project Health Assessment & Deployment Readiness Platform**

[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Passing-16a34a.svg)](https://github.com/stackdoctor)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776ab.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Docker Ready](https://img.shields.io/badge/Docker-Ready-2496ed.svg)](https://www.docker.com/)
[![SARIF 2.1.0](https://img.shields.io/badge/SARIF-2.1.0-blueviolet.svg)](https://oasis-open.github.io/cti-documentation/)
[![CycloneDX 1.5](https://img.shields.io/badge/CycloneDX-1.5-orange.svg)](https://cyclonedx.org/)

---

## 1. Project Introduction

**StackDoctor** is an intelligent, developer-centric platform built to evaluate software project health, containerization standards, dependency safety, CI/CD pipeline automation, and secrets exposure before deploying to staging or production.

Developers upload a project archive (ZIP). StackDoctor extracts the repository within an isolated, strictly-sandboxed ephemeral environment, detects the project stack (Python, Node.js, React, Java, PHP, Go), and runs static analyzers across five core domains. The engine calculates an explainable **Health Score (0–100)**, evaluates a strict 4-tier **Deployment Readiness Status** (`READY`, `READY WITH WARNINGS`, `BLOCKED`, `INSUFFICIENT DATA`), masks all sensitive credentials, and generates downloadable **PDF, JSON, SARIF, and CycloneDX SBOM** diagnostic reports.

---

## 2. Problem Statement

Modern software projects frequently suffer from deployment failures, security leaks, and supply chain vulnerabilities caused by:
- Insecure Docker configurations (containers running as `root`, missing `WORKDIR`, unversioned `:latest` base images).
- Unpinned or wildcard dependencies (`*`, `latest`, dynamic Gradle/Maven specifiers) causing upstream breaking changes.
- Inadvertently committed credentials (API keys, private keys, `.env` files).
- Missing CI/CD pipelines or unsafe workflow triggers (`pull_request_target`, `write-all` permissions).
- Lack of standardized documentation (`README.md`, `.gitignore`, `.env.example`).

Deploying without automated static pre-flight checks leads to costly production outages, security compromises, and compliance failures.

---

## 3. Key Features

- **Secure Sandbox ZIP Processor:** Strict protection against Path Traversal (`ZipSlip`), ZIP bombs, symlink attacks, and oversized archives with zero code execution.
- **Multi-Stack Technology Detection:** Identifies Python, Node.js, React, Java (`pom.xml`, `build.gradle`), PHP (`composer.json`), Go (`go.mod`), Docker, and GitHub Actions.
- **5-Domain Static Analysis Engine:**
  1. *Project Structure (15% weight)*: Missing manifests, documentation, `.gitignore`, `.env.example`, framework layout.
  2. *Dependency Safety (20% weight)*: Unpinned dependencies, missing lockfiles, syntax parsing, Trivy / OSV-Scanner CVE detection.
  3. *Docker Architecture (20% weight)*: Non-root `USER`, base image pinning, `WORKDIR`, `CMD`, Compose validation, Hadolint / Checkov linting.
  4. *CI/CD Pipelines (15% weight)*: Trigger coverage, automated testing steps, least-privilege permissions, secret exposure detection, zizmor integration.
  5. *Security & Secrets (30% weight)*: Regex + Gitleaks pattern detection for OpenAI, AWS, GitHub, private keys, committed `.env` files with automatic masking.
- **Explainable Scoring Engine:** Normalized 0–100 health score with domain breakdown and severity-based deductions.
- **Independent Deployment Readiness Gate:** 4-tier status (`READY`, `READY WITH WARNINGS`, `BLOCKED`, `INSUFFICIENT DATA`) with explicit blocker explanations.
- **Multi-Format Export Engine:**
  - Executive downloadable PDF reports with ReportLab branding.
  - Standard SARIF v2.1.0 for GitHub Code Scanning and SonarQube.
  - Structured JSON diagnostics.
  - CycloneDX v1.5 Software Bill of Materials (SBOM).
- **Asynchronous Processing Ready:** Celery worker and Redis task queue support with graceful synchronous fallback.
- **Scan Comparison:** Compare two scans to track health score deltas, newly introduced findings, and resolved issues.
- **Custom Project Policies:** Evaluate `.stackdoctor.yml` repository governance rules.

---

## 4. Technology Stack

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.12, Flask 3.0.3 | REST API and static inspection orchestration |
| **ORM & Database** | Flask-SQLAlchemy 3.1.1, MySQL 8.0, SQLite (local dev) | Multi-tenant scan persistence |
| **Authentication** | Flask-JWT-Extended 4.6.0 | Secure token authentication |
| **Report Generation** | ReportLab 4.2.2 | Executive PDF generation |
| **Export Formats** | SARIF 2.1.0, JSON, CycloneDX 1.5 SBOM | Industry-standard security interchange formats |
| **Frontend Framework** | React 18, Vite 5, React Router 6 | Responsive developer SPA |
| **Styling & UI** | Tailwind CSS 3.4, Lucide React | Modern dark/light interface |
| **Background Queue** | Celery 5.4.0, Redis 7 | Optional asynchronous background scanning |
| **Testing** | Pytest 8.3.2, Pytest-Flask, Vitest 2.1.9, JSDOM | Comprehensive unit and API test suites |
| **Containerization** | Docker, Docker Compose, Nginx, Gunicorn | Production container deployment |

---

## 5. System Architecture

```mermaid
graph TD
    User([Developer / CI Agent]) -->|Uploads ZIP Archive| Frontend[React 18 SPA]
    Frontend -->|REST API with JWT| FlaskAPI[Flask 3.0 API]
    FlaskAPI -->|Auth & Scans| DB[(MySQL / SQLite Database)]
    
    subgraph "Static Analysis Engine (Zero Code Execution)"
        FlaskAPI --> ZipEngine[ZIP Sandbox & Extraction]
        ZipEngine --> TechDetect[Technology & Framework Detector]
        TechDetect --> Structure[Structure Analyzer - 15%]
        TechDetect --> Deps[Dependency Analyzer - 20%]
        TechDetect --> Docker[Docker Analyzer - 20%]
        TechDetect --> CICD[CI/CD Analyzer - 15%]
        TechDetect --> Security[Security & Secrets - 30%]
        TechDetect --> Policy[Custom YAML Policy]
        
        Deps -.->|Optional CLI| TrivyOSV[Trivy / OSV-Scanner]
        Docker -.->|Optional CLI| HadolintCheckov[Hadolint / Checkov]
        CICD -.->|Optional CLI| Zizmor[zizmor]
        Security -.->|Optional CLI| Gitleaks[Gitleaks]
        
        Structure --> Scoring[Weighted Scoring & Readiness Engine]
        Deps --> Scoring
        Docker --> Scoring
        CICD --> Scoring
        Security --> Scoring
        Policy --> Scoring
    end
    
    Scoring --> Exporters[Report Exporters]
    Exporters --> PDF[ReportLab PDF]
    Exporters --> SARIF[SARIF 2.1.0]
    Exporters --> JSON[JSON Report]
    Exporters --> SBOM[CycloneDX 1.5 SBOM]
```

---

## 6. Folder Structure

```
cdd-finalPhase/
├── backend/
│   ├── app/
│   │   ├── analyzers/        # Static analysis modules & scanner runners
│   │   ├── models/           # SQLAlchemy database entities (User, Scan, Finding, Recommendation)
│   │   ├── reports/          # PDF, JSON, and SARIF report generators
│   │   ├── routes/           # REST endpoints (auth, scans, upload, system)
│   │   ├── tasks/            # Celery worker configuration
│   │   ├── config.py         # Multi-environment configuration
│   │   ├── extensions.py     # SQLAlchemy, JWT, CORS, Migrate instances
│   │   └── __init__.py       # Application factory
│   ├── tests/                # Automated Pytest suite
│   ├── requirements.txt      # Python dependencies
│   ├── run.py                # Local development server entry point
│   └── Dockerfile            # Multi-stage production backend image
├── frontend/
│   ├── src/
│   │   ├── context/          # React Auth Context & state
│   │   ├── layouts/          # Dashboard layout & navigation
│   │   ├── pages/            # Analysis results, Dashboard, History, Scan upload
│   │   ├── services/         # Axios API client & report download handlers
│   │   ├── styles/           # Global styles and design system
│   │   └── test/             # Vitest component test suite
│   ├── package.json          # Node dependencies & test scripts
│   ├── vite.config.js        # Vite bundler configuration
│   └── Dockerfile            # Production Nginx container image
├── docs/                     # Architecture, API, Security, and Scoring specifications
├── docker-compose.yml        # Full-stack composition (MySQL, Redis, Backend, Worker, Frontend)
├── .env.example              # Environment variables template
├── CHANGELOG.md              # Historical version changelog
└── README.md                 # Primary documentation
```

---

## 7. Installation Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- Git

### Setup Backend
```powershell
# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r backend\requirements.txt
```

### Setup Frontend
```powershell
cd frontend
npm install
cd ..
```

---

## 8. Environment Configuration

Copy `.env.example` to `.env`:
```powershell
Copy-Item .env.example .env
```

Key environment variables:
```ini
FLASK_ENV=development
DEBUG=True
PORT=5000
USE_SQLITE=true
SECRET_KEY=your-custom-secret-key
JWT_SECRET_KEY=your-custom-jwt-secret-key
DATABASE_URL=mysql+pymysql://stack_user:stack_secure_pass_2026@localhost:3306/stackdoctor_db
MAX_UPLOAD_SIZE_BYTES=52428800
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## 9. Database Setup

StackDoctor supports both local SQLite and production MySQL.

### Local Development (SQLite):
Set `USE_SQLITE=true` in `.env`. Tables are created automatically on application startup.

### Production (MySQL):
```powershell
# Start MySQL via Docker
docker compose up -d mysql

# Verify database connectivity
curl http://localhost:5000/api/health
```

---

## 10. Running Frontend and Backend (Windows 11)

### Start Backend:
```powershell
.\.venv\Scripts\Activate.ps1
$env:USE_SQLITE="true"
python backend\run.py
```
Backend runs on `http://localhost:5000`.

### Start Frontend:
```powershell
cd frontend
npm run dev
```
Frontend runs on `http://localhost:5173`.

---

## 11. Docker Compose Instructions

To run the entire platform (MySQL, Redis, Flask backend, Celery worker, React Nginx frontend) with one command:
```powershell
docker compose up --build -d
```
Access the application at `http://localhost`.

---

## 12. API Documentation

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/auth/register` | Register new account | No |
| `POST` | `/api/auth/login` | Authenticate and obtain JWT | No |
| `GET` | `/api/auth/me` | Fetch current user profile | Yes |
| `POST` | `/api/upload` | Upload & inspect ZIP project archive | Yes |
| `POST` | `/api/scans` | Upload & inspect ZIP project archive | Yes |
| `GET` | `/api/scans` | List scan history and metrics | Yes |
| `GET` | `/api/scans/<id>` | Fetch detailed scan report | Yes |
| `GET` | `/api/scans/<id>/findings` | Fetch filtered findings | Yes |
| `GET` | `/api/scans/<id>/score` | Fetch domain weights and scores | Yes |
| `GET` | `/api/scans/<id>/readiness` | Fetch deployment readiness and blockers | Yes |
| `GET` | `/api/scans/compare` | Compare two scans (`?base_id=&target_id=`) | Yes |
| `GET` | `/api/scans/<id>/report/pdf` | Download ReportLab PDF report | Yes (Header/Token) |
| `GET` | `/api/scans/<id>/report/json` | Download structured JSON report | Yes |
| `GET` | `/api/scans/<id>/report/sarif` | Download SARIF v2.1.0 report | Yes |
| `GET` | `/api/scans/<id>/report/sbom` | Download CycloneDX v1.5 SBOM | Yes |
| `DELETE`| `/api/scans/<id>` | Delete scan record | Yes |
| `GET` | `/api/health` | Service health status | No |

---

## 13. Scanner Dependencies (Optional Integrations)

StackDoctor operates out-of-the-box with deterministic offline static engines. For extended CVE scanning, optional CLI binaries can be installed on PATH:

- **Trivy**: `winget install aqua.trivy` (Vulnerability and container scanning)
- **Gitleaks**: `winget install gitleaks` (High-entropy secret detection)
- **Hadolint**: `winget install hadolint` (Dockerfile linter)
- **Checkov**: `pip install checkov` (IaC and container security)
- **OSV-Scanner**: `go install github.com/google/osv-scanner/cmd/osv-scanner@latest`
- **Syft**: `winget install anchore.syft` (SBOM cataloging)

If any binary is absent, StackDoctor automatically falls back to its built-in Python inspection engines without throwing errors.

---

## 14. Testing Instructions

### Run Backend Tests (Pytest):
```powershell
.\.venv\Scripts\Activate.ps1
pytest backend\tests -v
```
*Current test suite: 36 passing automated tests covering ZIP sandbox, detectors, analyzers, scoring engine, readiness blockers, report downloads, and API tenancy.*

### Run Frontend Tests (Vitest):
```powershell
cd frontend
npm test -- --run
```
*Current test suite: 4 passing component integration tests.*

---

## 15. Security Limitations

- **Static Analysis Only:** Dynamic runtime vulnerabilities (e.g., zero-day SQL injection payload paths, memory corruption) are not discovered without executing code.
- **Deobfuscation Bounds:** Base64 or obfuscated secrets that do not match entropy or credential prefix schemas will not be detected.
- **Archive Size Caps:** Archives exceeding 50 MB or decompression ratios > 100:1 are safely rejected to protect server availability.

---

## 16. Known Limitations

- High-entropy random strings resembling API keys may occasionally trigger low-confidence warnings requiring manual user dismissal.
- Full Celery asynchronous processing requires an active Redis broker; otherwise, scans execute synchronously.

---

## 17. Future Enhancements

- AI-assisted fix patch generation (with user approval before application).
- Direct GitHub OAuth repository cloning and pull request status checks.
- Real-time Server-Sent Events (SSE) for granular step-by-step scanner progress.
- SOC2 / ISO 27001 compliance mapping reports.
