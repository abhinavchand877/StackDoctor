import os
import time
import uuid
import tempfile
import json
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify, current_app, Response, make_response
from flask_jwt_extended import jwt_required, get_jwt_identity, decode_token
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.scan import Scan, utc_now
from app.models.finding import Finding
from app.models.recommendation import Recommendation
from app.analyzers.zip_processor import ZipProcessor, ZipProcessingError
from app.analyzers.project_detector import ProjectDetector
from app.analyzers.structure_analyzer import StructureAnalyzer
from app.analyzers.dependency_analyzer import DependencyAnalyzer
from app.analyzers.docker_analyzer import DockerAnalyzer
from app.analyzers.github_actions_analyzer import GitHubActionsAnalyzer
from app.analyzers.security_analyzer import SecurityAnalyzer
from app.analyzers.scoring_engine import ScoringEngine
from app.reports.pdf_generator import generate_pdf_report
from app.reports.sarif_exporter import generate_sarif_report
from app.reports.json_exporter import generate_json_report
from app.analyzers.sbom_generator import generate_sbom
from app.analyzers.custom_policy import CustomPolicyEvaluator

scans_bp = Blueprint("scans", __name__, url_prefix="/api/scans")
upload_bp = Blueprint("upload", __name__, url_prefix="/api/upload")

def get_current_user_id() -> int:
    return int(get_jwt_identity())

def find_scan(scan_identifier, user_id: int):
    """Finds a scan by integer ID or string UUID for the given user."""
    try:
        scan_id_int = int(scan_identifier)
        scan = Scan.query.filter_by(id=scan_id_int, user_id=user_id).first()
        if scan:
            return scan
    except (ValueError, TypeError):
        pass

    return Scan.query.filter_by(uuid=str(scan_identifier), user_id=user_id).first()

@scans_bp.route("", methods=["POST"])
@upload_bp.route("", methods=["POST"])
@jwt_required()
def create_scan():
    user_id = get_current_user_id()
    start_time = time.time()

    if "file" not in request.files:
        return jsonify({"error": "Bad Request", "message": "No file uploaded. Please provide a ZIP archive."}), 400

    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "Bad Request", "message": "No file selected."}), 400

    filename = secure_filename(uploaded_file.filename)
    if not filename.lower().endswith(".zip"):
        return jsonify({"error": "Bad Request", "message": "Only ZIP archive files (.zip) are supported."}), 400

    custom_name = request.form.get("project_name", "").strip()
    project_name = custom_name if custom_name else os.path.splitext(filename)[0]
    scan_uuid = f"SCAN-{uuid.uuid4().hex[:12].upper()}"

    # Save uploaded file to safe temporary location
    upload_tmp_dir = current_app.config.get("UPLOAD_TMP_DIR")
    if upload_tmp_dir:
        os.makedirs(upload_tmp_dir, exist_ok=True)
    temp_zip_fd, temp_zip_path = tempfile.mkstemp(suffix=".zip", prefix="upload_", dir=upload_tmp_dir)
    os.close(temp_zip_fd)
    zip_retained_for_celery = False

    try:
        uploaded_file.save(temp_zip_path)

        # Check if asynchronous processing is requested or globally enabled
        is_async = (
            request.args.get("async", "false").lower() == "true"
            or request.form.get("async", "false").lower() == "true"
            or current_app.config.get("ASYNC_SCANS_ENABLED", False)
        )
        if is_async:
            scan = Scan(
                uuid=scan_uuid,
                user_id=user_id,
                project_name=project_name,
                original_filename=filename,
                health_score=0,
                risk_level="Pending Analysis",
                status="PENDING",
                readiness_status="PENDING",
                scan_duration=0.0,
                total_findings=0,
                passed_checks=0,
                warning_count=0,
                failed_checks=0,
            )
            scan.set_technologies([])
            scan.set_summary({})
            scan.set_readiness_reasons([])
            scan.set_category_scores({})
            db.session.add(scan)
            db.session.commit()

            try:
                from app.tasks.celery_app import execute_scan_async
                execute_scan_async.delay(scan.id, temp_zip_path, project_name)
                zip_retained_for_celery = True
                return jsonify({
                    "message": "Scan submitted for asynchronous background processing.",
                    "scan": scan.to_dict(),
                    "status": "PENDING"
                }), 202
            except Exception as e:
                current_app.logger.warning(f"Celery dispatch failed: {e}. Executing synchronously.")
                # Continue below with synchronous execution


        processor = ZipProcessor(
            max_upload_size=current_app.config.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024),
            max_extracted_size=current_app.config.get("MAX_EXTRACTED_SIZE_BYTES", 150 * 1024 * 1024),
            max_entries=current_app.config.get("MAX_ARCHIVE_ENTRIES", 3000),
            max_single_file_size=current_app.config.get("MAX_INSPECT_FILE_SIZE_BYTES", 2 * 1024 * 1024),
        )

        with processor.extract_safely(temp_zip_path) as project_root:
            # 1. Project Detection
            detector = ProjectDetector(project_root)
            detected_info = detector.detect()

            # 2. Run All 5 Analysis Modules
            all_findings = []

            # Module 1: Structure Analyzer
            m1 = StructureAnalyzer(project_root, detected_info)
            all_findings.extend(m1.analyze())

            # Module 2: Dependency Analyzer
            m2 = DependencyAnalyzer(project_root, detected_info)
            all_findings.extend(m2.analyze())

            # Module 3: Docker Analyzer
            m3 = DockerAnalyzer(project_root, detected_info)
            all_findings.extend(m3.analyze())

            # Module 4: GitHub Actions Analyzer
            m4 = GitHubActionsAnalyzer(project_root, detected_info)
            all_findings.extend(m4.analyze())

            # Module 5: Security Analyzer
            m5 = SecurityAnalyzer(project_root, detected_info, max_file_size=processor.max_single_file_size)
            all_findings.extend(m5.analyze())

            # Module 6: Custom Project Policies (.stackdoctor.yml)
            m_custom = CustomPolicyEvaluator(project_root)
            all_findings.extend(m_custom.evaluate())

            # 3. Rule-Based Scoring Engine & Deployment Readiness
            engine = ScoringEngine()
            eval_result = engine.evaluate(all_findings, detected_info)
            scan_duration = time.time() - start_time

            # 4. Save Scan Record to Database
            scan = Scan(
                uuid=scan_uuid,
                user_id=user_id,
                project_name=project_name,
                original_filename=filename,
                health_score=eval_result["health_score"],
                risk_level=eval_result["risk_level"],
                status="COMPLETED",
                readiness_status=eval_result["readiness_status"],
                scan_duration=scan_duration,
                total_findings=eval_result["total_findings"],
                passed_checks=eval_result["passed_checks"],
                warning_count=eval_result["warning_count"],
                failed_checks=eval_result["failed_checks"],
                completed_at=utc_now(),
            )
            scan.set_technologies(detected_info["technologies"])
            scan.set_summary(eval_result["module_results"])
            scan.set_readiness_reasons(eval_result["readiness_reasons"])
            scan.set_category_scores(eval_result["category_scores"])

            db.session.add(scan)
            db.session.flush()  # Get generated scan.id

            # Save Findings Records and link Recommendations
            for f_data in eval_result["unique_findings"]:
                finding = Finding(
                    scan_id=scan.id,
                    rule_id=f_data["rule_id"],
                    module=f_data.get("module", "General"),
                    category=f_data.get("category") or f_data.get("module"),
                    title=f_data["title"],
                    description=f_data["description"],
                    severity=f_data["severity"],
                    file_path=f_data.get("file_path"),
                    line_number=f_data.get("line_number"),
                    masked_evidence=f_data.get("masked_evidence"),
                    recommendation=f_data.get("recommendation"),
                    scanner=f_data.get("scanner", "static_rule_engine"),
                    confidence=f_data.get("confidence", "HIGH"),
                )
                db.session.add(finding)
                db.session.flush()

                rec_text = f_data.get("recommendation")
                if rec_text:
                    fix_type = "config_patch"
                    rule_id = f_data.get("rule_id", "")
                    if rule_id.startswith("SEC-"):
                        fix_type = "security_remediation"
                    elif rule_id.startswith("DEP-"):
                        fix_type = "version_bump"
                    elif rule_id.startswith("GHA-"):
                        fix_type = "pipeline_step"

                    rec = Recommendation(
                        finding_id=finding.id,
                        description=f_data.get("description", ""),
                        suggested_fix=rec_text,
                        fix_type=fix_type,
                    )
                    db.session.add(rec)

            db.session.commit()

            return jsonify({
                "message": "Scan completed successfully.",
                "scan": scan.to_dict(include_findings=True),
            }), 201

    except ZipProcessingError as e:
        return jsonify({"error": "ZIP Processing Error", "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Scan analysis exception: {str(e)}")
        return jsonify({"error": "Internal Error", "message": f"Failed to complete scan analysis: {str(e)}"}), 500
    finally:
        if not zip_retained_for_celery and os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError:
                pass


@scans_bp.route("", methods=["GET"])
@jwt_required()
def list_scans():
    user_id = get_current_user_id()
    scans = Scan.query.filter_by(user_id=user_id).order_by(Scan.created_at.desc()).all()

    # Calculate aggregate dashboard metrics
    total_scans = len(scans)
    avg_score = round(sum(s.health_score for s in scans) / total_scans, 1) if total_scans > 0 else 0
    total_issues = sum(s.total_findings for s in scans)

    # Category statistics aggregation
    category_stats = {}
    for scan in scans:
        summary = scan.get_summary()
        for mod, info in summary.items():
            if mod not in category_stats:
                category_stats[mod] = {"passed": 0, "warning": 0, "failed": 0, "total_issues": 0}
            status = info.get("status", "Passed")
            if status == "Passed":
                category_stats[mod]["passed"] += 1
            elif status == "Warning":
                category_stats[mod]["warning"] += 1
            elif status == "Failed":
                category_stats[mod]["failed"] += 1
            category_stats[mod]["total_issues"] += info.get("findings_count", 0)

    return jsonify({
        "metrics": {
            "total_scans": total_scans,
            "average_score": avg_score,
            "total_issues": total_issues,
            "category_stats": category_stats,
        },
        "scans": [s.to_dict(include_findings=False) for s in scans],
    }), 200


@scans_bp.route("/<scan_id>", methods=["GET"])
@jwt_required()
def get_scan(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan not found or access denied."}), 404

    return jsonify({"scan": scan.to_dict(include_findings=True)}), 200


@scans_bp.route("/<scan_id>/findings", methods=["GET"])
@jwt_required()
def get_scan_findings(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan not found or access denied."}), 404

    category_filter = request.args.get("category")
    severity_filter = request.args.get("severity")

    findings_query = scan.findings
    if category_filter:
        findings_query = findings_query.filter(
            (Finding.category == category_filter) | (Finding.module == category_filter)
        )
    if severity_filter:
        findings_query = findings_query.filter_by(severity=severity_filter)

    findings = [f.to_dict() for f in findings_query.all()]
    return jsonify({
        "scan_id": scan.id,
        "scan_uuid": scan.uuid,
        "total": len(findings),
        "findings": findings,
    }), 200


@scans_bp.route("/<scan_id>/score", methods=["GET"])
@jwt_required()
def get_scan_score(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan not found or access denied."}), 404

    return jsonify({
        "scan_id": scan.id,
        "scan_uuid": scan.uuid,
        "health_score": scan.health_score,
        "risk_level": scan.risk_level,
        "category_scores": scan.get_category_scores(),
        "summary": scan.get_summary(),
    }), 200


@scans_bp.route("/<scan_id>/readiness", methods=["GET"])
@jwt_required()
def get_scan_readiness(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan not found or access denied."}), 404

    return jsonify({
        "scan_id": scan.id,
        "scan_uuid": scan.uuid,
        "readiness_status": scan.readiness_status,
        "readiness_reasons": scan.get_readiness_reasons(),
        "health_score": scan.health_score,
    }), 200


@scans_bp.route("/<scan_id>/report/json", methods=["GET"])
@jwt_required()
def download_json_report(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan report not found or access denied."}), 404

    scan_dict = scan.to_dict(include_findings=True)
    json_content = generate_json_report(scan_dict)

    safe_name = "".join(c for c in scan.project_name if c.isalnum() or c in ("-", "_")).strip() or "project"
    filename = f"StackDoctor_Report_{safe_name}_scan{scan.id}.json"

    response = make_response(json_content)
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@scans_bp.route("/<scan_id>/report/sarif", methods=["GET"])
@jwt_required()
def download_sarif_report(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan report not found or access denied."}), 404

    scan_dict = scan.to_dict(include_findings=True)
    sarif_content = generate_sarif_report(scan_dict)

    safe_name = "".join(c for c in scan.project_name if c.isalnum() or c in ("-", "_")).strip() or "project"
    filename = f"StackDoctor_Report_{safe_name}_scan{scan.id}.sarif"

    response = make_response(sarif_content)
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@scans_bp.route("/<scan_id>", methods=["DELETE"])
@jwt_required()
def delete_scan(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan not found or access denied."}), 404

    db.session.delete(scan)
    db.session.commit()

    return jsonify({"message": f"Scan '{scan.project_name}' deleted successfully."}), 200


@scans_bp.route("/<scan_id>/report/pdf", methods=["GET"])
def download_pdf_report(scan_id):
    token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif request.args.get("token"):
        token = request.args.get("token")

    if not token:
        return jsonify({"error": "Unauthorized", "message": "Missing authentication token."}), 401

    try:
        decoded = decode_token(token)
        user_id = int(decoded["sub"])
    except Exception:
        return jsonify({"error": "Unauthorized", "message": "Invalid or expired token."}), 401

    scan = find_scan(scan_id, user_id)
    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan report not found or access denied."}), 404

    scan_dict = scan.to_dict(include_findings=True)
    pdf_bytes = generate_pdf_report(scan_dict)

    safe_name = "".join(c for c in scan.project_name if c.isalnum() or c in ("-", "_")).strip() or "project"
    filename = f"StackDoctor_Report_{safe_name}_scan{scan.id}.pdf"

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@scans_bp.route("/compare", methods=["GET"])
@jwt_required()
def compare_scans():
    user_id = get_current_user_id()
    base_id = request.args.get("base_id")
    target_id = request.args.get("target_id")

    if not base_id or not target_id:
        return jsonify({"error": "Bad Request", "message": "Both base_id and target_id query parameters are required."}), 400

    base_scan = find_scan(base_id, user_id)
    target_scan = find_scan(target_id, user_id)

    if not base_scan or not target_scan:
        return jsonify({"error": "Not Found", "message": "One or both specified scans were not found."}), 404

    base_findings = {f.rule_id: f for f in base_scan.findings.all()}
    target_findings = {f.rule_id: f for f in target_scan.findings.all()}

    new_rule_ids = set(target_findings.keys()) - set(base_findings.keys())
    resolved_rule_ids = set(base_findings.keys()) - set(target_findings.keys())

    return jsonify({
        "comparison": {
            "base_scan": {"id": base_scan.id, "project_name": base_scan.project_name, "score": base_scan.health_score, "readiness": base_scan.readiness_status},
            "target_scan": {"id": target_scan.id, "project_name": target_scan.project_name, "score": target_scan.health_score, "readiness": target_scan.readiness_status},
            "score_delta": target_scan.health_score - base_scan.health_score,
            "new_findings_count": len(new_rule_ids),
            "resolved_findings_count": len(resolved_rule_ids),
            "new_findings": [target_findings[rid].to_dict() for rid in new_rule_ids],
            "resolved_findings": [base_findings[rid].to_dict() for rid in resolved_rule_ids],
        }
    }), 200


@scans_bp.route("/<scan_id>/report/sbom", methods=["GET"])
@jwt_required()
def download_sbom_report(scan_id):
    user_id = get_current_user_id()
    scan = find_scan(scan_id, user_id)

    if not scan:
        return jsonify({"error": "Not Found", "message": "Scan report not found or access denied."}), 404

    # Generate CycloneDX SBOM for scan
    sbom_dict = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tools": [{"vendor": "StackDoctor", "name": "StackDoctor SBOM Engine", "version": "2.0.0"}],
            "component": {"type": "application", "name": scan.project_name, "version": "1.0.0"},
        },
        "components": [
            {"type": "framework", "name": tech, "version": "detected"}
            for tech in scan.get_technologies()
        ],
    }

    safe_name = "".join(c for c in scan.project_name if c.isalnum() or c in ("-", "_")).strip() or "project"
    filename = f"StackDoctor_SBOM_{safe_name}_scan{scan.id}.json"

    response = make_response(json.dumps(sbom_dict, indent=2))
    response.headers["Content-Type"] = "application/json"
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response
