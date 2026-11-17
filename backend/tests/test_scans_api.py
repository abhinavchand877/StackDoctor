import io
import zipfile

def create_sample_zip(files: dict) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, content in files.items():
            zf.writestr(fname, content)
    buf.seek(0)
    return buf

def test_upload_scan_success(client, auth_headers):
    zip_stream = create_sample_zip({
        "README.md": "# Sample Project\nDocumentation content.",
        ".gitignore": "node_modules/\n.venv/\n",
        "requirements.txt": "flask==3.0.3\nrequests==2.31.0\n",
        "tests/test_app.py": "def test_ok(): pass",
        "Dockerfile": "FROM python:3.12-slim\nWORKDIR /app\nCOPY . /app\nRUN useradd appuser\nUSER appuser\nCMD [\"python\", \"app.py\"]\n",
        ".github/workflows/ci.yml": "name: CI\non: [push, pull_request]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - run: pip install -r requirements.txt\n      - run: pytest\n"
    })

    res = client.post(
        "/api/scans",
        data={"file": (zip_stream, "sample_clean_project.zip"), "project_name": "CleanProject"},
        headers=auth_headers,
        content_type="multipart/form-data"
    )

    assert res.status_code == 201
    data = res.get_json()
    assert "scan" in data
    scan = data["scan"]
    assert scan["project_name"] == "CleanProject"
    assert "Python" in scan["detected_technologies"]
    assert "Docker" in scan["detected_technologies"]
    assert scan["health_score"] >= 85
    assert scan["risk_level"] == "Healthy"
    assert "findings" in scan

def test_upload_scan_unauthenticated(client):
    zip_stream = create_sample_zip({"app.py": "print('ok')"})
    res = client.post(
        "/api/scans",
        data={"file": (zip_stream, "project.zip")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 401

def test_upload_scan_invalid_extension(client, auth_headers):
    file_stream = io.BytesIO(b"Hello world")
    res = client.post(
        "/api/scans",
        data={"file": (file_stream, "project.tar.gz")},
        headers=auth_headers,
        content_type="multipart/form-data"
    )
    assert res.status_code == 400
    assert "Only ZIP archive files" in res.get_json()["message"]

def test_list_scans_and_metrics(client, auth_headers):
    res = client.get("/api/scans", headers=auth_headers)
    assert res.status_code == 200
    data = res.get_json()
    assert "metrics" in data
    assert "scans" in data
    assert "total_scans" in data["metrics"]
    assert "average_score" in data["metrics"]
    assert len(data["scans"]) >= 1

def test_scan_tenancy_isolation(client, auth_headers, second_user_headers):
    # Upload scan as user 1
    zip_stream = create_sample_zip({"README.md": "# User1 Project", "requirements.txt": "flask==3.0.3"})
    res1 = client.post(
        "/api/scans",
        data={"file": (zip_stream, "user1_proj.zip")},
        headers=auth_headers,
        content_type="multipart/form-data"
    )
    scan_id = res1.get_json()["scan"]["id"]

    # Try to access scan as user 2 -> should return 404 (Not Found or access denied)
    res2 = client.get(f"/api/scans/{scan_id}", headers=second_user_headers)
    assert res2.status_code == 404

    # Try to delete scan as user 2 -> should return 404
    del_res = client.delete(f"/api/scans/{scan_id}", headers=second_user_headers)
    assert del_res.status_code == 404

    # Delete scan as user 1 -> should succeed
    del_res_owner = client.delete(f"/api/scans/{scan_id}", headers=auth_headers)
    assert del_res_owner.status_code == 200

def test_pdf_report_download(client, auth_headers):
    # Upload scan first
    zip_stream = create_sample_zip({"README.md": "# My App", "requirements.txt": "flask==3.0.3"})
    res = client.post(
        "/api/scans",
        data={"file": (zip_stream, "app.zip")},
        headers=auth_headers,
        content_type="multipart/form-data"
    )
    scan_id = res.get_json()["scan"]["id"]

    # Extract token
    token = auth_headers["Authorization"].split(" ")[1]

    # Download with query param token
    pdf_res = client.get(f"/api/scans/{scan_id}/report/pdf?token={token}")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["Content-Type"] == "application/pdf"
    assert b"%PDF" in pdf_res.data

def test_api_upload_alias_and_reports(client, auth_headers):
    # Test POST /api/upload alias
    zip_stream = create_sample_zip({
        "README.md": "# Upload Alias App",
        ".gitignore": ".env\n",
        "requirements.txt": "flask==3.0.3\n",
        "app.py": "print('hello')",
    })
    res = client.post(
        "/api/upload",
        data={"file": (zip_stream, "upload_alias.zip"), "project_name": "AliasProj"},
        headers=auth_headers,
        content_type="multipart/form-data"
    )
    assert res.status_code == 201
    scan = res.get_json()["scan"]
    scan_id = scan["id"]
    assert scan["uuid"].startswith("SCAN-")
    assert "readiness_status" in scan
    assert "category_scores" in scan

    # Test GET /api/scans/<id>/findings
    f_res = client.get(f"/api/scans/{scan_id}/findings", headers=auth_headers)
    assert f_res.status_code == 200
    assert "findings" in f_res.get_json()

    # Test GET /api/scans/<id>/score
    s_res = client.get(f"/api/scans/{scan_id}/score", headers=auth_headers)
    assert s_res.status_code == 200
    assert "health_score" in s_res.get_json()
    assert "category_scores" in s_res.get_json()

    # Test GET /api/scans/<id>/readiness
    r_res = client.get(f"/api/scans/{scan_id}/readiness", headers=auth_headers)
    assert r_res.status_code == 200
    assert "readiness_status" in r_res.get_json()

    # Test GET /api/scans/<id>/report/json
    j_res = client.get(f"/api/scans/{scan_id}/report/json", headers=auth_headers)
    assert j_res.status_code == 200
    assert j_res.headers["Content-Type"] == "application/json"
    import json
    j_data = json.loads(j_res.data.decode("utf-8"))
    assert j_data["report_format"] == "StackDoctor-Assessment-v2"

    # Test GET /api/scans/<id>/report/sarif
    sarif_res = client.get(f"/api/scans/{scan_id}/report/sarif", headers=auth_headers)
    assert sarif_res.status_code == 200
    sarif_data = json.loads(sarif_res.data.decode("utf-8"))
    assert sarif_data["version"] == "2.1.0"
    assert sarif_data["runs"][0]["tool"]["driver"]["name"] == "StackDoctor"

def test_deployment_readiness_blocked_on_secret(client, auth_headers):
    # Upload a project containing a secret -> must be BLOCKED
    zip_stream = create_sample_zip({
        "README.md": "# Secret App",
        "app.py": "api_key = 'sk-proj-DEMOSECRET123456789012345678901234567890'\n",
    })
    res = client.post(
        "/api/scans",
        data={"file": (zip_stream, "insecure_app.zip")},
        headers=auth_headers,
        content_type="multipart/form-data"
    )
    assert res.status_code == 201
    scan = res.get_json()["scan"]
    assert scan["readiness_status"] == "BLOCKED"
    assert any("Exposed" in r or "SEC-" in r for r in scan["readiness_reasons"])

def test_scan_compare_and_sbom_export(client, auth_headers):
    # Create scan 1 (base)
    zip1 = create_sample_zip({"README.md": "# Base"})
    res1 = client.post("/api/upload", data={"file": (zip1, "base.zip")}, headers=auth_headers, content_type="multipart/form-data")
    id1 = res1.get_json()["scan"]["id"]

    # Create scan 2 (target with more files)
    zip2 = create_sample_zip({"README.md": "# Target", ".gitignore": "venv/\n", "requirements.txt": "flask==3.0.3\n"})
    res2 = client.post("/api/upload", data={"file": (zip2, "target.zip")}, headers=auth_headers, content_type="multipart/form-data")
    id2 = res2.get_json()["scan"]["id"]

    # Test compare
    cmp_res = client.get(f"/api/scans/compare?base_id={id1}&target_id={id2}", headers=auth_headers)
    assert cmp_res.status_code == 200
    cmp_data = cmp_res.get_json()["comparison"]
    assert "score_delta" in cmp_data
    assert "new_findings_count" in cmp_data
    assert "resolved_findings_count" in cmp_data

    # Test SBOM export
    sbom_res = client.get(f"/api/scans/{id2}/report/sbom", headers=auth_headers)
    assert sbom_res.status_code == 200
    import json
    sbom_data = json.loads(sbom_res.data.decode("utf-8"))
    assert sbom_data["bomFormat"] == "CycloneDX"
    assert sbom_data["specVersion"] == "1.5"

def test_production_env_validation_missing_vars(monkeypatch):
    """TEST CASE 6: Verify missing required environment variables produce understandable errors."""
    import pytest
    from app import create_app
    # Ensure production environment variables are not set
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ValueError) as exc_info:
        create_app("production")
    
    err_msg = str(exc_info.value)
    assert "Missing required production environment variables" in err_msg
    assert "SECRET_KEY" in err_msg

def test_docker_compose_analyzer_findings(tmp_path):
    """Test Docker Compose analysis for syntax, missing services, and hardcoded secrets."""
    from app.analyzers.docker_analyzer import DockerAnalyzer
    compose_content = (
        "version: '3.8'\n"
        "services:\n"
        "  web:\n"
        "    image: nginx:latest\n"
        "    environment:\n"
        "      - DB_PASSWORD=plaintext_insecure_pass_12345\n"
    )
    (tmp_path / "docker-compose.yml").write_text(compose_content)
    (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\nRUN useradd appuser\nUSER appuser\nCMD ['python', 'app.py']\n")
    (tmp_path / ".dockerignore").write_text(".git\n.env\n")

    analyzer = DockerAnalyzer(str(tmp_path), {"technologies": ["Docker"]})
    findings = analyzer.analyze()
    rule_ids = [f["rule_id"] for f in findings]
    assert "DOC-013" in rule_ids  # Hardcoded Secret in Compose



