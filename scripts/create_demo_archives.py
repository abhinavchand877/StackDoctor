import os
import zipfile

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLES_DIR = os.path.join(BASE_DIR, "sample_projects")
ARCHIVES_DIR = os.path.join(SAMPLES_DIR, "archives")

def make_zip(source_dir: str, target_zip: str):
    os.makedirs(os.path.dirname(target_zip), exist_ok=True)
    with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, source_dir)
                zf.write(full_path, rel_path)
    print(f"Created archive: {target_zip}")

def build_demo_projects():
    # 1. Python Sample (With intentional, safe-to-demonstrate issues)
    py_dir = os.path.join(SAMPLES_DIR, "python_sample")
    os.makedirs(py_dir, exist_ok=True)
    os.makedirs(os.path.join(py_dir, "tests"), exist_ok=True)
    os.makedirs(os.path.join(py_dir, ".github", "workflows"), exist_ok=True)

    with open(os.path.join(py_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Python Demo Service\n\nA demonstration microservice for StackDoctor analysis.\n")

    # Intentional issue: missing pinned versions
    with open(os.path.join(py_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("flask\nrequests>=2.0.0\npydantic\n")

    with open(os.path.join(py_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write("# Demo application\nimport os\nfrom flask import Flask\napp = Flask(__name__)\n\n# Safe mock credential (masked in StackDoctor)\nMOCK_KEY = 'sk-proj-demo1234567890abcdef1234567890'\n\n@app.route('/')\ndef home():\n    return {'status': 'healthy'}\n")

    # Intentional issue: Dockerfile with :latest, no WORKDIR, running as root
    with open(os.path.join(py_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:latest\nCOPY . /app\nRUN pip install -r /app/requirements.txt\nCMD [\"python\", \"/app/app.py\"]\n")

    # Intentional issue: workflow missing test steps
    with open(os.path.join(py_dir, ".github", "workflows", "ci.yml"), "w", encoding="utf-8") as f:
        f.write("name: CI\non: [push, pull_request]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install -r requirements.txt\n")

    # Intentional issue: committed .env file
    with open(os.path.join(py_dir, ".env"), "w", encoding="utf-8") as f:
        f.write("FLASK_ENV=development\nDATABASE_URL=sqlite:///test.db\nAPI_KEY=mock-dev-token-9988\n")

    # 2. Node.js / React Sample (With intentional issues)
    node_dir = os.path.join(SAMPLES_DIR, "node_sample")
    os.makedirs(node_dir, exist_ok=True)
    os.makedirs(os.path.join(node_dir, "src"), exist_ok=True)
    os.makedirs(os.path.join(node_dir, ".github", "workflows"), exist_ok=True)

    with open(os.path.join(node_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Node / React Sample\n\nFrontend demo with intentional configuration warnings.\n")

    # Intentional issue: wildcard dependencies, missing lockfile
    with open(os.path.join(node_dir, "package.json"), "w", encoding="utf-8") as f:
        f.write('{\n  "name": "demo-react-app",\n  "version": "1.0.0",\n  "dependencies": {\n    "react": "latest",\n    "react-dom": "*",\n    "axios": "^1.6.0"\n  }\n}\n')

    with open(os.path.join(node_dir, "src", "App.jsx"), "w", encoding="utf-8") as f:
        f.write("import React from 'react';\nexport default function App() { return <h1>Demo</h1>; }\n")

    with open(os.path.join(node_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write("node_modules/\ndist/\n")

    # 3. Clean Reference Project (Healthy, scores >= 90)
    clean_dir = os.path.join(SAMPLES_DIR, "clean_sample")
    os.makedirs(clean_dir, exist_ok=True)
    os.makedirs(os.path.join(clean_dir, "tests"), exist_ok=True)
    os.makedirs(os.path.join(clean_dir, ".github", "workflows"), exist_ok=True)

    with open(os.path.join(clean_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# Clean Production Ready Service\n\nFull production best-practices demonstration.\n")

    with open(os.path.join(clean_dir, ".gitignore"), "w", encoding="utf-8") as f:
        f.write(".venv/\n__pycache__/\n.env\n*.pyc\n")

    with open(os.path.join(clean_dir, "requirements.txt"), "w", encoding="utf-8") as f:
        f.write("flask==3.0.3\ngunicorn==22.0.0\npytest==8.3.2\n")

    with open(os.path.join(clean_dir, "app.py"), "w", encoding="utf-8") as f:
        f.write("from flask import Flask\napp = Flask(__name__)\n@app.route('/')\ndef index(): return {'status': 'healthy'}\n")

    with open(os.path.join(clean_dir, "tests", "test_app.py"), "w", encoding="utf-8") as f:
        f.write("def test_health():\n    assert 1 + 1 == 2\n")

    with open(os.path.join(clean_dir, ".dockerignore"), "w", encoding="utf-8") as f:
        f.write(".git\n.env\n__pycache__\n.venv\n")

    with open(os.path.join(clean_dir, "Dockerfile"), "w", encoding="utf-8") as f:
        f.write("FROM python:3.12-slim\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nRUN useradd -m appuser\nUSER appuser\nCMD [\"gunicorn\", \"--bind\", \"0.0.0.0:5000\", \"app:app\"]\n")

    with open(os.path.join(clean_dir, ".github", "workflows", "ci.yml"), "w", encoding="utf-8") as f:
        f.write("name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install -r requirements.txt\n      - run: pytest\n      - run: docker build -t myapp .\n")

    # Compile archives
    make_zip(py_dir, os.path.join(ARCHIVES_DIR, "python_demo_project.zip"))
    make_zip(node_dir, os.path.join(ARCHIVES_DIR, "node_react_demo_project.zip"))
    make_zip(clean_dir, os.path.join(ARCHIVES_DIR, "clean_healthy_project.zip"))

if __name__ == "__main__":
    build_demo_projects()
