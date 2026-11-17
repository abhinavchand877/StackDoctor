# StackDoctor Production Deployment Guide

## 1. Containerized Deployment with Docker Compose

The simplest and most reliable way to run StackDoctor in production or staging is with Docker Compose.

### Step 1: Clone the Repository & Configure Environment
```bash
git clone https://github.com/your-username/stackdoctor.git
cd stackdoctor
cp .env.example .env
```
Ensure you update `SECRET_KEY`, `JWT_SECRET_KEY`, and `MYSQL_PASSWORD` in `.env`.

### Step 2: Start All Services
```bash
docker compose up -d --build
```

This single command builds and starts:
1. `mysql`: MySQL 8.0 with persistent storage volume (`mysql_data`).
2. `backend`: Multi-stage Python 3.12 Flask app running under Gunicorn (3 workers, non-root user).
3. `frontend`: High-performance Nginx reverse proxy serving the built React bundle and routing `/api/` calls to the backend.

### Step 3: Verify Container Health
```bash
docker compose ps
curl http://localhost/api/health
```

### Stopping the Application
```bash
docker compose down
```
*(Data in MySQL is preserved in the `mysql_data` Docker volume. To delete the database volume explicitly, use `docker compose down -v`).*

---

## 2. GitHub Actions Automated Deployment Configuration

StackDoctor includes a complete CI/CD workflow in `.github/workflows/ci-cd.yml`.

### Step 1: Enable Automated Deployment
In your GitHub repository, navigate to **Settings > Secrets and variables > Actions > Variables**:
- Name: `DEPLOY_ENABLED`
- Value: `true` (set to `false` to disable remote deployment).

### Step 2: Configure SSH Deployment Secrets
In GitHub repository **Settings > Secrets and variables > Actions > Secrets**, add:
- `DEPLOY_HOST`: Target server public IP address or domain (e.g. `203.0.113.10`).
- `DEPLOY_USER`: SSH user with Docker permissions (e.g. `ubuntu` or `deploy`).
- `DEPLOY_SSH_KEY`: Private SSH key authorized in the server's `~/.ssh/authorized_keys`.
- `DEPLOY_KNOWN_HOSTS`: Target server's SSH fingerprint from `ssh-keyscan -H <DEPLOY_HOST>`.

### Step 3: Container Publishing Permissions
The workflow automatically publishes container images to GitHub Container Registry (`ghcr.io`) using the built-in `GITHUB_TOKEN`.
In repository **Settings > Actions > General > Workflow permissions**, ensure:
- Select **Read and write permissions**.
