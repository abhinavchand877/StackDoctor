import json
from datetime import datetime, timezone
from app.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class Scan(db.Model):
    __tablename__ = "scans"

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64), unique=True, index=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_name = db.Column(db.String(150), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    detected_technologies = db.Column(db.Text, nullable=False)  # JSON-serialized list of strings
    health_score = db.Column(db.Integer, nullable=False)  # 0 to 100
    risk_level = db.Column(db.String(50), nullable=False)  # Healthy, Needs Review, Needs Attention
    status = db.Column(db.String(30), default="COMPLETED", nullable=False)  # PENDING, PROCESSING, COMPLETED, FAILED
    readiness_status = db.Column(db.String(50), default="READY", nullable=False)  # READY, READY WITH WARNINGS, BLOCKED, INSUFFICIENT DATA
    readiness_reasons = db.Column(db.Text, nullable=True)  # JSON-serialized list of blockers/warnings
    scan_duration = db.Column(db.Float, default=0.0, nullable=False)
    total_findings = db.Column(db.Integer, default=0, nullable=False)
    passed_checks = db.Column(db.Integer, default=0, nullable=False)
    warning_count = db.Column(db.Integer, default=0, nullable=False)
    failed_checks = db.Column(db.Integer, default=0, nullable=False)
    scan_summary = db.Column(db.Text, nullable=True)  # JSON-serialized module results
    category_scores = db.Column(db.Text, nullable=True)  # JSON-serialized category scores dict
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)

    findings = db.relationship("Finding", backref="scan", lazy="dynamic", cascade="all, delete-orphan")

    def get_technologies(self) -> list:
        try:
            return json.loads(self.detected_technologies)
        except Exception:
            return []

    def set_technologies(self, tech_list: list) -> None:
        self.detected_technologies = json.dumps(tech_list)

    def get_summary(self) -> dict:
        try:
            return json.loads(self.scan_summary) if self.scan_summary else {}
        except Exception:
            return {}

    def set_summary(self, summary_dict: dict) -> None:
        self.scan_summary = json.dumps(summary_dict)

    def get_readiness_reasons(self) -> list:
        try:
            return json.loads(self.readiness_reasons) if self.readiness_reasons else []
        except Exception:
            return []

    def set_readiness_reasons(self, reasons: list) -> None:
        self.readiness_reasons = json.dumps(reasons)

    def get_category_scores(self) -> dict:
        try:
            return json.loads(self.category_scores) if self.category_scores else {}
        except Exception:
            return {}

    def set_category_scores(self, scores: dict) -> None:
        self.category_scores = json.dumps(scores)

    def to_dict(self, include_findings: bool = False) -> dict:
        data = {
            "id": self.id,
            "uuid": self.uuid or f"SCAN-{self.id}",
            "user_id": self.user_id,
            "project_name": self.project_name,
            "original_filename": self.original_filename,
            "detected_technologies": self.get_technologies(),
            "health_score": self.health_score,
            "risk_level": self.risk_level,
            "status": self.status,
            "readiness_status": self.readiness_status,
            "readiness_reasons": self.get_readiness_reasons(),
            "scan_duration": round(self.scan_duration, 2),
            "total_findings": self.total_findings,
            "passed_checks": self.passed_checks,
            "warning_count": self.warning_count,
            "failed_checks": self.failed_checks,
            "category_scores": self.get_category_scores(),
            "scan_summary": self.get_summary(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
        if include_findings:
            data["findings"] = [f.to_dict() for f in self.findings.all()]
        return data

    def __repr__(self) -> str:
        return f"<Scan {self.id}: {self.project_name} (Score: {self.health_score})>"
