# StackDoctor Local Development Guide (Windows PowerShell)

This guide walks through configuring and running StackDoctor locally on Windows without Docker, using Python 3.12 and Node.js.

---

## 1. Prerequisites

- **Python 3.12+**
- **Node.js 20+ & npm 10+**
- **Git**

Verify your local installation:
```powershell
python --version
node --version
npm --version
```

---

## 2. Backend Setup

1. Open PowerShell and navigate to the project directory:
   ```powershell
   cd e:\Sem-III\CDD\CDD-final-project
   ```

2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install backend dependencies:
   ```powershell
   pip install -r backend\requirements.txt
   ```

4. Configure local environment variables:
   ```powershell
   Copy-Item .env.example .env
   ```
   *(Optional: If running without MySQL locally, set `USE_SQLITE=true` in `.env` to automatically use SQLite during local development).*

5. Start the Flask development server:
   ```powershell
   $env:PYTHONPATH = "backend"
   python backend\run.py
   ```
   The Flask backend will launch at `http://localhost:5000`. Test the health endpoint:
   ```powershell
   Invoke-RestMethod http://localhost:5000/api/health
   ```

---

## 3. Frontend Setup

1. Open a new PowerShell terminal:
   ```powershell
   cd e:\Sem-III\CDD\CDD-final-project\frontend
   ```

2. Install npm dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   The React application will be available at `http://localhost:5173`. Vite will automatically proxy API calls from `/api/*` to `http://localhost:5000`.

---

## 4. Running Automated Tests

### Run Backend Pytest Suite
```powershell
cd e:\Sem-III\CDD\CDD-final-project
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH = "backend"
pytest backend\tests -v
```

### Run Frontend Vitest Suite
```powershell
cd e:\Sem-III\CDD\CDD-final-project\frontend
npm test
```

### Test Frontend Production Build
```powershell
cd e:\Sem-III\CDD\CDD-final-project\frontend
npm run build
```
