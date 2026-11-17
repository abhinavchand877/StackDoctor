import os
import io
import zipfile
import pytest
from app.analyzers.zip_processor import ZipProcessor, ZipProcessingError
from app.analyzers.project_detector import ProjectDetector
from app.analyzers.structure_analyzer import StructureAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.analyzers.docker_analyzer import DockerAnalyzer
from app.analyzers.github_actions_analyzer import GitHubActionsAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer, mask_secret
from app.analyzers.scoring_engine import ScoringEngine
from app.reports.pdf_generator import generate_pdf_report

def create_in_memory_zip(files_dict: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files_dict.items():
            zf.writestr(fname, content)
    return buf.getvalue()

# --- ZIP PROCESSOR TESTS ---
def test_zip_processor_valid_archive(tmp_path):
    zip_bytes = create_in_memory_zip({
        "app.py": "print('hello')",
        "requirements.txt": "flask==3.0.3"
    })
    zip_path = tmp_path / "test.zip"
    zip_path.write_bytes(zip_bytes)

    processor = ZipProcessor()
    with processor.extract_safely(str(zip_path)) as extracted_dir:
        assert os.path.exists(os.path.join(extracted_dir, "app.py"))
        assert os.path.exists(os.path.join(extracted_dir, "requirements.txt"))

def test_zip_processor_corrupted_archive(tmp_path):
    bad_zip = tmp_path / "corrupt.zip"
    bad_zip.write_bytes(b"This is not a zip file at all")

    processor = ZipProcessor()
    with pytest.raises(ZipProcessingError) as exc_info:
        with processor.extract_safely(str(bad_zip)):
            pass
    assert "not a valid ZIP archive" in str(exc_info.value)

def test_zip_processor_path_traversal_prevention(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # Create an entry with path traversal attempt
        zf.writestr("../evil.txt", "malicious payload")
    traversal_zip = tmp_path / "traversal.zip"
    traversal_zip.write_bytes(buf.getvalue())

    processor = ZipProcessor()
    with pytest.raises(ZipProcessingError) as exc_info:
        with processor.extract_safely(str(traversal_zip)):
            pass
    assert "Path Traversal attack" in str(exc_info.value)

def test_zip_processor_max_entries_exceeded(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for i in range(10):
            zf.writestr(f"file_{i}.txt", "data")
    zip_path = tmp_path / "entries.zip"
    zip_path.write_bytes(buf.getvalue())

    # Limit to max 5 entries
    processor = ZipProcessor(max_entries=5)
    with pytest.raises(ZipProcessingError) as exc_info:
        with processor.extract_safely(str(zip_path)):
            pass
    assert "exceeding limit of 5" in str(exc_info.value)

# --- PROJECT DETECTOR TESTS ---
def test_project_detector_python(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask==3.0.3")
    (tmp_path / "main.py").write_text("print('ok')")

    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is True
    assert "Python" in res["technologies"]

def test_project_detector_react(tmp_path):
    pkg_json = {
        "name": "my-react-app",
        "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}
    }
    import json
    (tmp_path / "package.json").write_text(json.dumps(pkg_json))
    src = tmp_path / "src"
    src.mkdir()
    (src / "App.jsx").write_text("export default function App() { return <div>Hello</div>; }")

    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is True
    assert "React" in res["technologies"]
    assert "Node.js" in res["technologies"]

def test_project_detector_java(tmp_path):
    (tmp_path / "pom.xml").write_text("<project><modelVersion>4.0.0</modelVersion></project>")
    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is True
    assert "Java" in res["technologies"]

def test_project_detector_php(tmp_path):
    (tmp_path / "composer.json").write_text('{"name": "test/app"}')
    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is True
    assert "PHP" in res["technologies"]

def test_project_detector_go(tmp_path):
    (tmp_path / "go.mod").write_text("module example.com/app\ngo 1.22\n")
    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is True
    assert "Go" in res["technologies"]

def test_project_detector_unsupported(tmp_path):
    (tmp_path / "document.txt").write_text("Just a text file")
    detector = ProjectDetector(str(tmp_path))
    res = detector.detect()
    assert res["supported"] is False

# --- MODULE 1: STRUCTURE ANALYZER TESTS ---
def test_structure_analyzer_missing_files(tmp_path):
    analyzer = StructureAnalyzer(str(tmp_path), {"technologies": ["Python"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]
    assert "STR-001" in rule_ids  # Missing README
    assert "STR-002" in rule_ids  # Missing .gitignore
    assert "STR-003" in rule_ids  # Missing tests
    assert "STR-004" in rule_ids  # Missing requirements.txt

# --- MODULE 2: DEPENDENCY ANALYZER TESTS ---
def test_dependency_analyzer_unpinned_python(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask\nrequests>=2.0.0\npydantic==2.5.0\n")
    analyzer = DependencyAnalyzer(str(tmp_path), {"technologies": ["Python"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]
    assert "DEP-002" in rule_ids  # Unpinned Python packages

def test_dependency_analyzer_node_wildcards(tmp_path):
    import json
    pkg_json = {
        "name": "demo",
        "dependencies": {"express": "latest", "cors": "*"}
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_json))
    analyzer = DependencyAnalyzer(str(tmp_path), {"technologies": ["Node.js"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]
    assert "DEP-006" in rule_ids  # Wildcard / latest versions
    assert "DEP-007" in rule_ids  # Missing lockfile

# --- MODULE 3: DOCKER ANALYZER TESTS ---
def test_docker_analyzer_issues(tmp_path):
    dockerfile_content = (
        "FROM python:latest\n"  # Triggers unpinned :latest tag
        "COPY . /app\n"
        "RUN pip install -r /app/requirements.txt\n"
        # Missing WORKDIR
        # Missing USER (running as root)
        # Missing CMD / ENTRYPOINT
    )
    (tmp_path / "Dockerfile").write_text(dockerfile_content)

    analyzer = DockerAnalyzer(str(tmp_path), {"technologies": ["Python", "Docker"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]

    assert "DOC-004" in rule_ids  # :latest tag
    assert "DOC-005" in rule_ids  # Missing WORKDIR
    assert "DOC-007" in rule_ids  # Missing CMD
    assert "DOC-008" in rule_ids  # Running as root

# --- MODULE 4: GITHUB ACTIONS ANALYZER TESTS ---
def test_github_actions_analyzer(tmp_path):
    wf_dir = tmp_path / ".github" / "workflows"
    wf_dir.mkdir(parents=True)
    wf_content = (
        "name: CI\n"
        "on:\n"
        "  push:\n"
        "    branches: [main]\n"
        "jobs:\n"
        "  build:\n"
        "    runs-on: ubuntu-latest\n"
        "    steps:\n"
        "      - uses: actions/checkout@v4\n"
        "      - name: Install dependencies\n"
        "        run: pip install -r requirements.txt\n"
        # Missing automated test step
    )
    (wf_dir / "ci.yml").write_text(wf_content)

    analyzer = GitHubActionsAnalyzer(str(tmp_path), {"technologies": ["Python", "GitHub Actions"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]
    assert "GHA-007" in rule_ids  # Missing automated tests in CI

# --- MODULE 5: SECURITY ANALYZER TESTS ---
def test_security_analyzer_secrets_and_masking(tmp_path):
    # Create file with OpenAI key and committed .env
    (tmp_path / ".env").write_text("DATABASE_URL=postgres://user:pass@localhost:5432/db")
    (tmp_path / "config.py").write_text("API_KEY = 'sk-abcdef1234567890abcdef1234567890'")

    analyzer = SecurityAnalyzer(str(tmp_path), {"technologies": ["Python"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]

    assert "SEC-010" in rule_ids  # Committed .env
    assert "SEC-001" in rule_ids  # OpenAI key

    # Verify secret masking
    sec_finding = next(f for f in findings if f["rule_id"] == "SEC-001")
    assert "sk-abcdef1234567890abcdef1234567890" not in sec_finding["description"]
    assert "sk-****************" in sec_finding["description"]

def test_mask_secret_helper():
    assert mask_secret("sk-12345678901234567890") == "sk-****************"
    assert mask_secret("short") == "******"

# --- SCORING ENGINE TESTS ---
def test_scoring_engine_calculation():
    engine = ScoringEngine()
    findings = [
        {"rule_id": "SEC-001", "module": "Security Configuration", "severity": "Critical", "file_path": "app.py"},
        {"rule_id": "STR-001", "module": "Project Structure", "severity": "Medium", "file_path": "README.md"},
        {"rule_id": "DOC-005", "module": "Docker Configuration", "severity": "Low", "file_path": "Dockerfile"},
    ]
    # Penalties: 25 + 8 + 3 = 36. Score = 100 - 36 = 64
    res = engine.evaluate(findings, {"supported": True})
    assert res["health_score"] == 64
    assert res["risk_level"] == "Needs Attention"
    assert res["failed_checks"] == 1
    assert res["warning_count"] == 2

def test_scoring_engine_clamping_and_deduplication():
    engine = ScoringEngine()
    # 5 Critical findings -> 5 * 25 = 125 penalty, should clamp to 0
    findings = [
        {"rule_id": f"CRIT-00{i}", "module": "Security Configuration", "severity": "Critical", "file_path": f"f{i}.py"}
        for i in range(5)
    ]
    # Add duplicate finding
    findings.append({"rule_id": "CRIT-001", "module": "Security Configuration", "severity": "Critical", "file_path": "f1.py"})

    res = engine.evaluate(findings, {"supported": True})
    assert res["health_score"] == 0  # Clamped to 0
    assert res["total_findings"] == 5  # Deduplicated

# --- PDF GENERATOR TESTS ---
def test_pdf_report_generation():
    scan_mock = {
        "project_name": "DemoProject",
        "health_score": 88,
        "risk_level": "Healthy",
        "detected_technologies": ["Python", "Docker"],
        "created_at": "2026-11-12 10:00:00 UTC",
        "total_findings": 1,
        "passed_checks": 4,
        "warning_count": 1,
        "failed_checks": 0,
        "scan_summary": {
            "Project Structure": {"status": "Passed", "findings_count": 0},
            "Dependency Analysis": {"status": "Warning", "findings_count": 1},
        },
        "findings": [
            {
                "rule_id": "DEP-002",
                "title": "Unpinned Python Dependencies",
                "severity": "Medium",
                "file_path": "requirements.txt",
                "description": "Dependencies are unpinned",
                "recommendation": "Pin versions",
            }
        ]
    }
    pdf_bytes = generate_pdf_report(scan_mock)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")
