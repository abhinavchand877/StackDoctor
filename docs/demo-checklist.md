# StackDoctor External Examiner & Demo Checklist

This checklist guides examiners and presenters through demonstrating StackDoctor's core static analysis features.

---

## 1. Preparation & Demo Archives

Pre-built demo archives are generated inside `sample_projects/archives/`:
1. `python_demo_project.zip`: Python Flask project containing intentional issues (unpinned dependencies, Dockerfile running as root with `:latest`, committed `.env`, missing CI test steps).
2. `node_react_demo_project.zip`: React/Node project with wildcard package versions, missing lockfiles.
3. `clean_healthy_project.zip`: Reference production-ready project meeting all baseline criteria (healthy score >= 90).

To regenerate the demo archives at any time:
```powershell
python scripts\create_demo_archives.py
```

---

## 2. Walkthrough Checklist

### Step 1: Launch Application
- Start the application locally or via Docker Compose:
  ```powershell
  docker compose up -d --build
  ```
- Navigate to `http://localhost` (or `http://localhost:5173` if running dev server).

### Step 2: Register a New Developer Account
- Click **Get Started** from the Landing Page.
- Fill in:
  - Username: `examiner`
  - Email: `examiner@stackdoctor.test`
  - Password: `Password123!`
- Verify redirection to the **Dashboard**. Note the clean empty state.

### Step 3: Run First Scan (Demonstrate Problem Detection)
- Click **New Project Scan** (or navigate to `/scan/new`).
- Drag and drop `sample_projects/archives/python_demo_project.zip`.
- Enter Project Name: `Demo Flask Microservice`.
- Click **Start Automated Project Health Scan**.
- Observe live progress indicator and transition to **Analysis Results**.

### Step 4: Inspect Results & Module Findings
- Check **Overall Health Score** (should be in "Needs Review" or "Needs Attention" range).
- Review **Detected Technologies**: Python, Docker, GitHub Actions.
- Review **Module 1 (Structure):** Notice detected tests and structure layout.
- Review **Module 2 (Dependencies):** Notice `DEP-002: Unpinned Python Dependencies Detected`.
- Review **Module 3 (Docker):** Notice `DOC-004: Unpinned ':latest' Base Image` and `DOC-008: Container Execution as Root User`.
- Review **Module 4 (CI/CD):** Notice `GHA-007: Missing Automated Testing in CI Pipeline`.
- Review **Module 5 (Security):** Notice `SEC-010: Sensitive Environment File Committed` and `SEC-001: Potential OpenAI API Key Exposed`.
  - **Verify Secret Masking:** Ensure the API key appears as `sk-proj-demo****************` and that raw secrets are never shown.

### Step 5: Download PDF Health Report
- Click **Download PDF Report**.
- Open the generated PDF:
  - Verify StackDoctor branding.
  - Verify Project health score and classification badge.
  - Verify category summary table.
  - Verify itemized findings and recommended solutions.
  - Verify secret masking in the PDF.

### Step 6: Scan a Healthy Project
- Navigate to **New Scan**.
- Upload `sample_projects/archives/clean_healthy_project.zip`.
- Run scan: Observe score >= 90 ("Healthy", Green badge).

### Step 7: Inspect Scan History & Multi-Tenancy
- Click **Scan History** in the sidebar.
- Notice both scans are listed with timestamp, health score, and risk badge.
- Open another incognito browser window, register a second account (`examiner2`), and verify that examiner2's history is empty and cannot access examiner1's scan IDs.
