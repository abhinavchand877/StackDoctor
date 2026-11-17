import json
from typing import Dict, Any

def generate_json_report(scan_data: Dict[str, Any]) -> str:
    """
    Exports clean, structured, standardized JSON diagnostic reports with project metadata,
    deployment readiness, category weights and scores, and prioritized findings.
    """
    report = {
        "report_format": "StackDoctor-Assessment-v2",
        "scan_id": scan_data.get("id"),
        "scan_uuid": scan_data.get("uuid"),
        "project_name": scan_data.get("project_name"),
        "original_filename": scan_data.get("original_filename"),
        "detected_technologies": scan_data.get("detected_technologies", []),
        "scan_timestamp": scan_data.get("created_at"),
        "completed_at": scan_data.get("completed_at"),
        "scan_duration_seconds": scan_data.get("scan_duration", 0),
        "assessment": {
            "health_score": scan_data.get("health_score"),
            "risk_level": scan_data.get("risk_level"),
            "readiness_status": scan_data.get("readiness_status"),
            "readiness_reasons": scan_data.get("readiness_reasons", []),
            "category_scores": scan_data.get("category_scores", {}),
        },
        "statistics": {
            "total_findings": scan_data.get("total_findings", 0),
            "passed_checks": scan_data.get("passed_checks", 0),
            "warning_count": scan_data.get("warning_count", 0),
            "failed_checks": scan_data.get("failed_checks", 0),
        },
        "findings": scan_data.get("findings", []),
    }
    return json.dumps(report, indent=2)
