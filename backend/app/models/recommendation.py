from datetime import datetime, timezone
from app.extensions import db

def utc_now():
    return datetime.now(timezone.utc)

class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    finding_id = db.Column(db.Integer, db.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    suggested_fix = db.Column(db.Text, nullable=True)
    fix_type = db.Column(db.String(50), default="rule_remediation", nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "description": self.description,
            "suggested_fix": self.suggested_fix,
            "fix_type": self.fix_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Recommendation {self.id} for Finding {self.finding_id}>"
