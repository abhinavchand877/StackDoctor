# StackDoctor Architecture Documentation

## 1. System Overview

StackDoctor is designed as a 3-tier modular web application consisting of:
1. **Frontend Tier:** React + Vite single-page application (SPA) with Lucide React icons, styled with a modern SaaS developer-tool theme.
2. **Backend Tier:** Flask REST API written in Python 3.12, orchestrating secure ZIP extraction, static analysis modules, rule-based scoring, and ReportLab PDF generation.
3. **Database Tier:** MySQL 8.0 relational database queried via SQLAlchemy ORM.

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│         React 18 SPA (Vite + React Router + Lucide)         │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST APIs (JWT Auth)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Nginx Reverse Proxy (Port 80)               │
│         Routes / -> Static UI | Routes /api/ -> Flask       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Flask Backend (Port 5000)                  │
│  ┌───────────────────────┬───────────────────────────────┐  │
│  │ Authentication        │ Secure ZIP Sandbox            │  │
│  │ JWT / PBKDF2 Hashing  │ Path traversal & bomb defense │  │
│  ├───────────────────────┴───────────────────────────────┤  │
│  │              Project Detection Engine                 │  │
│  │           (Python, Node.js, React, Docker)            │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │              5 Static Analysis Modules                │  │
│  │  1. Structure   2. Dependencies   3. Docker           │  │
│  │  4. GitHub Actions                5. Security         │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │             Rule-Based Scoring Engine                 │  │
│  │    Deduplication • Severity Penalties • Health Grade  │  │
│  ├───────────────────────────────────────────────────────┤  │
│  │             ReportLab PDF Report Engine               │  │
│  └───────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLAlchemy ORM
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    MySQL 8.0 Database                       │
│              Tables: users, scans, findings                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure & Module Responsibilities

```
CDD-final-project/
├── backend/
│   ├── app/
│   │   ├── analyzers/
│   │   │   ├── project_detector.py        # Framework & tech detection
│   │   │   ├── zip_processor.py           # Secure extraction & sandbox
│   │   │   ├── structure_analyzer.py      # Module 1: Layout & files
│   │   │   ├── dependency_analyzer.py     # Module 2: Manifest parsing
│   │   │   ├── docker_analyzer.py         # Module 3: Dockerfile & Compose
│   │   │   ├── github_actions_analyzer.py # Module 4: CI/CD workflows
│   │   │   ├── security_analyzer.py       # Module 5: Secrets & keys
│   │   │   └── scoring_engine.py          # Central rule deduction engine
│   │   ├── models/
│   │   │   ├── user.py                    # User account schema
│   │   │   ├── scan.py                    # Scan summary & score
│   │   │   └── finding.py                 # Individual issue schema
│   │   ├── reports/
│   │   │   └── pdf_generator.py           # ReportLab PDF creation
│   │   ├── routes/
│   │   │   ├── auth.py                    # Login & registration APIs
│   │   │   ├── scans.py                   # Scan execution & retrieval
│   │   │   └── system.py                  # Health check API
│   │   ├── config.py                      # Environment configurations
│   │   ├── extensions.py                  # SQLAlchemy, JWT, CORS
│   │   └── __init__.py                    # Flask application factory
│   ├── tests/                             # Pytest test suite (30 tests)
│   ├── Dockerfile                         # Production backend image
│   └── run.py                             # Development server entry point
├── frontend/
│   ├── src/
│   │   ├── context/AuthContext.jsx        # JWT session provider
│   │   ├── layouts/DashboardLayout.jsx    # Sidebar navigation layout
│   │   ├── pages/                         # Landing, Dashboard, Scan, etc.
│   │   ├── services/api.js                # Axios REST API client
│   │   └── styles/index.css               # Clean SaaS design system
│   ├── Dockerfile                         # Multi-stage frontend image
│   ├── nginx.conf                         # Reverse proxy configuration
│   └── vite.config.js                     # Vite build configuration
├── sample_projects/                       # Safe sample projects for testing
├── scripts/create_demo_archives.py        # Demo archive generation script
├── docker-compose.yml                     # Multi-container orchestration
├── .github/workflows/ci-cd.yml            # CI/CD automation workflow
└── README.md                              # Comprehensive guide
```

---

## 3. Scoring Heuristics

The health score starts at a baseline of **100 points**. Deductions are applied for each unique finding based on severity:

| Severity Level | Penalty Deduction | Description |
| :--- | :---: | :--- |
| **Critical** | `-25 pts` | Syntax errors, invalid manifests, exposed private keys. |
| **High** | `-15 pts` | Missing CMD, unpinned dependencies with wildcards, missing tests in CI. |
| **Medium** | `-8 pts` | Missing lockfile, running container as root, missing README/.gitignore. |
| **Low** | `-3 pts` | Missing WORKDIR, missing .dockerignore, missing optional configs. |
| **Informational** | `0 pts` | Best practice recommendations (e.g. deployment triggers). |

### Health Score Classifications
- **85 – 100:** Healthy (Green)
- **70 – 84:** Needs Review (Amber)
- **0 – 69:** Needs Attention (Red)
