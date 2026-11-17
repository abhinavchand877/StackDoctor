from typing import List, Dict, Any

# Category weights according to StackDoctor specification:
# Project structure: 15%, Dependencies: 20%, Docker: 20%, CI/CD: 15%, Security: 30%
CATEGORY_WEIGHTS = {
    "Project Structure": 0.15,
    "Dependencies": 0.20,
    "Docker": 0.20,
    "CI/CD": 0.15,
    "Security": 0.30,
}

# Module name alias mappings to canonical category keys
MODULE_TO_CATEGORY = {
    "Project Structure": "Project Structure",
    "Dependency Analysis": "Dependencies",
    "Dependencies": "Dependencies",
    "Docker Configuration": "Docker",
    "Docker": "Docker",
    "GitHub Actions": "CI/CD",
    "CI/CD": "CI/CD",
    "Security Configuration": "Security",
    "Security": "Security",
}

# Configurable severity penalty weights for category score deduction
SEVERITY_PENALTIES = {
    "Critical": 25,
    "High": 15,
    "Medium": 8,
    "Low": 3,
    "Informational": 0,
}

class ScoringEngine:
    """
    Centralized rule-based scoring and deployment readiness engine.
    Calculates 5 weighted category scores (Structure 15%, Dependencies 20%, Docker 20%, CI/CD 15%, Security 30%),
    evaluates 4 deployment readiness states (READY, READY WITH WARNINGS, BLOCKED, INSUFFICIENT DATA),
    and generates rule-based fix recommendations.
    """

    def __init__(self, category_weights: Dict[str, float] = None, severity_penalties: Dict[str, int] = None):
        self.weights = category_weights or CATEGORY_WEIGHTS
        self.penalties = severity_penalties or SEVERITY_PENALTIES

    def evaluate(self, all_findings: List[Dict[str, Any]], detected_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes list of raw findings and returns normalized weighted score, category breakdowns,
        deployment readiness status, and actionable recommendations.
        """
        # Deduplicate findings by (rule_id, file_path)
        unique_findings = []
        seen = set()

        for f in all_findings:
            key = (f.get("rule_id"), f.get("file_path"))
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)

        # Categorize findings into the 5 canonical domains
        canonical_categories = ["Project Structure", "Dependencies", "Docker", "CI/CD", "Security"]
        category_findings = {cat: [] for cat in canonical_categories}

        warning_count = 0
        failed_checks = 0
        critical_blockers = []
        high_severity_warnings = []

        for finding in unique_findings:
            sev = finding.get("severity", "Informational")
            raw_module = finding.get("category") or finding.get("module", "Project Structure")
            canonical_cat = MODULE_TO_CATEGORY.get(raw_module, "Project Structure")

            category_findings[canonical_cat].append(finding)

            if sev == "Critical":
                failed_checks += 1
                critical_blockers.append(
                    f"[{canonical_cat}] {finding.get('title')}: {finding.get('description')} ({finding.get('file_path') or 'project'})"
                )
            elif sev == "High":
                failed_checks += 1
                high_severity_warnings.append(
                    f"[{canonical_cat}] {finding.get('title')} ({finding.get('file_path') or 'project'})"
                )
            elif sev in ["Medium", "Low"]:
                warning_count += 1

        # 1. Compute Category Scores and Module Results
        category_scores = {}
        module_results = {}
        weighted_score_accum = 0.0

        for cat in canonical_categories:
            f_list = category_findings[cat]
            cat_penalty = sum(self.penalties.get(f.get("severity"), 0) for f in f_list)
            cat_score = max(0, min(100, 100 - cat_penalty))
            weight = self.weights.get(cat, 0.20)
            weighted_score_accum += cat_score * weight

            if not detected_info.get("supported", False):
                status = "Inconclusive"
            elif not f_list:
                status = "Passed"
            else:
                severities = {f.get("severity") for f in f_list}
                if "Critical" in severities or "High" in severities:
                    status = "Failed"
                else:
                    status = "Warning"

            category_scores[cat] = {
                "score": cat_score,
                "weight": int(weight * 100),
                "status": status,
                "findings_count": len(f_list),
            }

            # Maintain legacy module name mapping for existing UI and tests
            legacy_module_name = {
                "Project Structure": "Project Structure",
                "Dependencies": "Dependency Analysis",
                "Docker": "Docker Configuration",
                "CI/CD": "GitHub Actions",
                "Security": "Security Configuration",
            }[cat]

            module_results[legacy_module_name] = {
                "module": legacy_module_name,
                "category": cat,
                "status": status,
                "score": cat_score,
                "findings_count": len(f_list),
                "findings": f_list,
            }

        # Overall health score clamped between 0 and 100
        total_penalty = sum(self.penalties.get(f.get("severity"), 0) for f in unique_findings)
        health_score = max(0, min(100, 100 - total_penalty))
        weighted_score = max(0, min(100, int(round(weighted_score_accum))))

        # Risk level classification
        if health_score >= 85:
            risk_level = "Healthy"
        elif health_score >= 70:
            risk_level = "Needs Review"
        else:
            risk_level = "Needs Attention"

        # 2. Deployment Readiness Evaluation
        if not detected_info.get("supported", False):
            readiness_status = "INSUFFICIENT DATA"
            readiness_reasons = ["Project architecture or frameworks could not be identified from uploaded archive."]
        elif critical_blockers:
            readiness_status = "BLOCKED"
            readiness_reasons = critical_blockers
        elif high_severity_warnings or health_score < 70:
            readiness_status = "READY WITH WARNINGS"
            readiness_reasons = high_severity_warnings or ["Health score is below threshold for unconditional release."]
        else:
            readiness_status = "READY"
            readiness_reasons = ["All security policies, dependency validations, and container configurations passed."]

        # 3. Rule-Based Fix Recommendations Generation
        recommendations = []
        for finding in unique_findings:
            rec_text = finding.get("recommendation")
            if rec_text:
                fix_type = "config_patch"
                rule_id = finding.get("rule_id", "")
                if rule_id.startswith("SEC-"):
                    fix_type = "security_remediation"
                elif rule_id.startswith("DEP-"):
                    fix_type = "version_bump"
                elif rule_id.startswith("GHA-"):
                    fix_type = "pipeline_step"

                recommendations.append({
                    "rule_id": rule_id,
                    "title": finding.get("title"),
                    "file_path": finding.get("file_path"),
                    "severity": finding.get("severity"),
                    "description": finding.get("description"),
                    "suggested_fix": rec_text,
                    "fix_type": fix_type,
                })

        passed_checks = sum(1 for res in module_results.values() if res["status"] == "Passed")

        return {
            "health_score": health_score,
            "weighted_score": weighted_score,
            "risk_level": risk_level,
            "readiness_status": readiness_status,
            "readiness_reasons": readiness_reasons,
            "category_scores": category_scores,
            "total_findings": len(unique_findings),
            "passed_checks": passed_checks,
            "warning_count": warning_count,
            "failed_checks": failed_checks,
            "unique_findings": unique_findings,
            "module_results": module_results,
            "recommendations": recommendations,
        }
