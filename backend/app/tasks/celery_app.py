import os
import time
import logging
from celery import Celery

logger = logging.getLogger("stackdoctor.celery")

def make_celery(app=None):
    """
    Initializes and configures a Celery instance for background scanning and asynchronous queue processing.
    """
    broker = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0" if os.getenv("FLASK_ENV") == "production" else "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0" if os.getenv("FLASK_ENV") == "production" else "redis://localhost:6379/0")

    celery_instance = Celery(
        "stackdoctor_worker",
        broker=broker,
        backend=backend,
    )

    if app:
        celery_instance.conf.update(app.config)

        class ContextTask(celery_instance.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery_instance.Task = ContextTask

    return celery_instance


# Initialize module-level Celery instance
from app import create_app
flask_app = create_app()
celery = make_celery(flask_app)
celery_app = celery
app = celery


# ========================================================
# REGISTERED BACKGROUND TASKS
# ========================================================

@celery.task(name="ping_worker")
def ping_worker():
    """Simple ping task to verify worker responsiveness and Redis broker connection."""
    return "pong"


@celery.task(name="execute_scan_async", bind=True)
def execute_scan_async(self, scan_id: int, temp_zip_path: str, project_name: str = None):
    """
    Asynchronously executes a comprehensive static analysis scan in the Celery background worker.
    Updates the Scan record and stores all Findings and Recommendations in the database.
    """
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
    from app.analyzers.custom_policy import CustomPolicyEvaluator
    from app.analyzers.scoring_engine import ScoringEngine

    start_time = time.time()
    scan = Scan.query.get(scan_id)
    if not scan:
        logger.error(f"Scan ID {scan_id} not found in database.")
        return {"success": False, "error": f"Scan with ID {scan_id} not found."}

    scan.status = "PROCESSING"
    db.session.commit()

    try:
        processor = ZipProcessor(
            max_upload_size=flask_app.config.get("MAX_CONTENT_LENGTH", 50 * 1024 * 1024),
            max_extracted_size=flask_app.config.get("MAX_EXTRACTED_SIZE_BYTES", 150 * 1024 * 1024),
            max_entries=flask_app.config.get("MAX_ARCHIVE_ENTRIES", 3000),
            max_single_file_size=flask_app.config.get("MAX_INSPECT_FILE_SIZE_BYTES", 2 * 1024 * 1024),
        )

        with processor.extract_safely(temp_zip_path) as project_root:
            # 1. Project Detection
            detector = ProjectDetector(project_root)
            detected_info = detector.detect()

            # 2. Run All Analysis Modules
            all_findings = []
            all_findings.extend(StructureAnalyzer(project_root, detected_info).analyze())
            all_findings.extend(DependencyAnalyzer(project_root, detected_info).analyze())
            all_findings.extend(DockerAnalyzer(project_root, detected_info).analyze())
            all_findings.extend(GitHubActionsAnalyzer(project_root, detected_info).analyze())
            all_findings.extend(SecurityAnalyzer(project_root, detected_info, max_file_size=processor.max_single_file_size).analyze())
            all_findings.extend(CustomPolicyEvaluator(project_root).evaluate())

            # 3. Rule-Based Scoring Engine & Deployment Readiness
            engine = ScoringEngine()
            eval_result = engine.evaluate(all_findings, detected_info)
            scan_duration = time.time() - start_time

            # 4. Update Scan Record
            scan.health_score = eval_result["health_score"]
            scan.risk_level = eval_result["risk_level"]
            scan.status = "COMPLETED"
            scan.readiness_status = eval_result["readiness_status"]
            scan.scan_duration = scan_duration
            scan.total_findings = eval_result["total_findings"]
            scan.passed_checks = eval_result["passed_checks"]
            scan.warning_count = eval_result["warning_count"]
            scan.failed_checks = eval_result["failed_checks"]
            scan.completed_at = utc_now()

            scan.set_technologies(detected_info["technologies"])
            scan.set_summary(eval_result["module_results"])
            scan.set_readiness_reasons(eval_result["readiness_reasons"])
            scan.set_category_scores(eval_result["category_scores"])

            # 5. Save Findings Records and link Recommendations
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
                        fix_type = "dependency_upgrade"
                    elif rule_id.startswith("DOC-"):
                        fix_type = "docker_hardening"
                    elif rule_id.startswith("GHA-"):
                        fix_type = "workflow_hardening"

                    rec = Recommendation(
                        finding_id=finding.id,
                        description=f_data.get("description", ""),
                        suggested_fix=rec_text,
                        fix_type=fix_type,
                    )
                    db.session.add(rec)

            db.session.commit()
            logger.info(f"Asynchronous scan {scan.id} completed with health score {scan.health_score}")
            return {"success": True, "scan_id": scan.id, "status": "COMPLETED", "score": scan.health_score}

    except Exception as e:
        logger.error(f"Asynchronous scan {scan.id} failed: {e}")
        scan.status = "FAILED"
        db.session.commit()
        return {"success": False, "scan_id": scan.id, "error": str(e)}

    finally:
        if os.path.exists(temp_zip_path):
            try:
                os.remove(temp_zip_path)
            except OSError:
                pass
