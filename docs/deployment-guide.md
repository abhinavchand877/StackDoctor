# StackDoctor — Complete Deployment & CI/CD Guide

## 1. Local Development Setup (Windows 11 & Linux)

### Backend Local Run
```powershell
# 1. Activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r backend\requirements.txt

# 3. Start local development server with SQLite
$env:USE_SQLITE="true"
$env:FLASK_ENV="development"
python backend\run.py
```
Backend will start on `http://127.0.0.1:5000`.

### Frontend Local Run
```powershell
cd frontend
npm install
npm run dev
```
Frontend development server will start on `http://localhost:5173`.

---

## 2. Multi-Service Containerized Deployment with Docker Compose

Docker Compose coordinates five services with isolated networking, persistence, and health checks:
1. `mysql`: MySQL 8.0 relational database with persistent named volume (`mysql_data`).
2. `redis`: Redis 7 in-memory cache and Celery broker.
3. `backend`: Multi-stage Python 3.12 Flask app running under Gunicorn (3 workers, non-root user `appuser`).
4. `worker`: Celery asynchronous background worker.
5. `frontend`: High-performance Nginx 1.27 reverse proxy serving the built React bundle and routing `/api/` calls to the backend.

### Quickstart Command
```bash
# 1. Copy environment configuration
cp .env.example .env

# 2. Build and launch all 5 services
docker compose up -d --build

# 3. Check container status & health checks
docker compose ps

# 4. Verify API connectivity
curl http://localhost/api/health
```

### Stopping Services
```bash
docker compose down
# To clean database volumes:
docker compose down -v
```

---

## 3. GitHub Actions Automated Pipeline (`.github/workflows/ci-cd.yml`)

The CI/CD pipeline enforces automated quality and security gates on every code change before building or releasing artifacts.

### Pipeline Stages & Flowchart

```
┌──────────────────────────┐     ┌──────────────────────────┐
│ Stage 1: Backend Tests   │     │ Stage 2: Frontend Tests  │
│ (Pytest 36 tests)        │     │ (Vitest 4 tests + Build) │
└─────────────┬────────────┘     └────────────┬─────────────┘
              │                               │
              └───────────────┬───────────────┘
                              ▼
               ┌─────────────────────────────┐
               │ Stage 3: Docker Build Check │
               │ (Backend & Frontend Build)  │
               └──────────────┬──────────────┘
                              ▼ (Only on push to 'main')
               ┌─────────────────────────────┐
               │ Stage 4: GHCR Image Publish │
               │ (ghcr.io/.../backend & web) │
               └──────────────┬──────────────┘
                              ▼ (Only if DEPLOY_ENABLED == 'true')
               ┌─────────────────────────────┐
               │ Stage 5: Production Deploy  │
               │ (SSH & Docker Compose Pull) │
               └─────────────────────────────┘
```

### Pipeline Triggers
- **`push: branches: [main]`**: Triggers full test, build, GHCR publish, and deployment flow.
- **`pull_request: branches: [main]`**: Executes Stages 1–3 (backend tests, frontend tests, docker build validation) to prevent broken PR merges without publishing images or deploying.
- **`workflow_dispatch`**: Allows manual trigger from GitHub Actions web console.

### Stage Breakdown

1. **Stage 1 — `backend-tests`**:
   - Checks out code with `actions/checkout@v4`.
   - Configures Python 3.12 with pip cache.
   - Installs dependencies from `backend/requirements.txt`.
   - Runs full Pytest suite: `pytest -v --tb=short`.

2. **Stage 2 — `frontend-tests`**:
   - Configures Node.js 20 LTS with npm cache.
   - Runs `npm install`.
   - Runs `npm test -- --run` (Vitest).
   - Validates Vite production bundle compilation (`npm run build`).

3. **Stage 3 — `docker-validation`**:
   - Depends on `[backend-tests, frontend-tests]`.
   - Sets up Docker Buildx.
   - Tests building `backend/Dockerfile` and `frontend/Dockerfile` with `push: false`.

4. **Stage 4 — `publish-images`**:
   - Only runs on `push` to `main` branch after Docker builds succeed.
   - Authenticates against GitHub Container Registry (`ghcr.io`) using `${{ secrets.GITHUB_TOKEN }}`.
   - Pushes versioned tags (`${{ github.sha }}`) and `:latest` for backend and frontend.

5. **Stage 5 — `deploy`**:
   - Depends on `publish-images`.
   - Gated on GitHub repository variable `vars.DEPLOY_ENABLED == 'true'`.
   - Connects securely to the production host via SSH.
   - Executes `docker compose pull` and `docker compose up -d --remove-orphans`.

---

## 4. GitHub Secrets and Variables Reference

To enable remote deployment to your VPS or cloud instance:

### Repository Variables (`Settings > Secrets and variables > Actions > Variables`):
| Variable | Value | Description |
| :--- | :--- | :--- |
| `DEPLOY_ENABLED` | `true` | Gates Stage 5 remote deployment. Set to `false` to disable. |

### Repository Secrets (`Settings > Secrets and variables > Actions > Secrets`):
| Secret Name | Example Value | Description |
| :--- | :--- | :--- |
| `DEPLOY_HOST` | `203.0.113.15` | Target server public IP or FQDN |
| `DEPLOY_USER` | `deploy` | Dedicated non-root deployment user with Docker group access |
| `DEPLOY_SSH_KEY` | `-----BEGIN OPENSSH PRIVATE KEY-----...` | Private SSH key paired with server `authorized_keys` |
| `DEPLOY_KNOWN_HOSTS` | `203.0.113.15 ssh-ed25519 AAAAC3...` | Server SSH fingerprint from `ssh-keyscan -H <HOST>` |

---

## 5. Verification & Audit Checklist

- [x] Dockerfile health checks added to both backend and frontend.
- [x] Backend runs as unprivileged user (`appuser` UID 1001).
- [x] Reverse proxy config passes client requests with 50 MB max body size.
- [x] Zero code execution guarantee preserved across all analyzers.
- [x] Pipeline validates tests before any image publishing or deployment.
