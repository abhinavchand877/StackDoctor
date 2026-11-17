from datetime import datetime, timezone
from app.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class Finding(db.Model):
    __tablename__ = "findings"

    id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey("scans.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_id = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(80), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(30), nullable=False)  # Critical, High, Medium, Low, Informational
    file_path = db.Column(db.String(255), nullable=True)
    line_number = db.Column(db.Integer, nullable=True)
    masked_evidence = db.Column(db.Text, nullable=True)
    recommendation = db.Column(db.Text, nullable=True)
    scanner = db.Column(db.String(80), default="static_rule_engine", nullable=True)
    confidence = db.Column(db.String(30), default="HIGH", nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    recommendations = db.relationship("Recommendation", backref="finding", lazy="dynamic", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "rule_id": self.rule_id,
            "module": self.module,
            "category": self.category or self.module,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "masked_evidence": self.masked_evidence,
            "recommendation": self.recommendation,
            "scanner": self.scanner or "static_rule_engine",
            "confidence": self.confidence or "HIGH",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "recommendations": [r.to_dict() for r in self.recommendations.all()] if hasattr(self, "recommendations") else [],
        }

    def __repr__(self) -> str:
        return f"<Finding [{self.severity}] {self.rule_id} in {self.file_path}>"
