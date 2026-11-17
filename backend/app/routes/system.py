from flask import Blueprint, jsonify
from app.extensions import db

system_bp = Blueprint("system", __name__, url_prefix="/api")

@system_bp.route("/health", methods=["GET"])
def health():
    db_status = "healthy"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"unreachable: {str(e)}"

    return jsonify({
        "status": "ok",
        "service": "stackdoctor-backend",
        "database": db_status,
        "version": "1.0.0",
    }), 200
