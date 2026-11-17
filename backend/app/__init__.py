import os
from flask import Flask, jsonify
from app.config import config_by_name
from app.extensions import db, migrate, jwt, cors

def create_app(config_name: str = None) -> Flask:
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Enforce strict validation of production secrets and configuration
    if config_name == "production":
        missing_vars = []
        if not app.config.get("SECRET_KEY"):
            missing_vars.append("SECRET_KEY")
        if not app.config.get("JWT_SECRET_KEY"):
            missing_vars.append("JWT_SECRET_KEY")
        if not app.config.get("SQLALCHEMY_DATABASE_URI"):
            missing_vars.append("DATABASE_URL")
        if missing_vars:
            raise ValueError(
                f"Missing required production environment variables: {', '.join(missing_vars)}. "
                "Please configure them in your environment or production .env file."
            )

    # Initialize extensions
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # JWT Error handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({"error": "Unauthorized", "message": "Missing Authorization Header with Bearer token."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({"error": "Unauthorized", "message": "The provided token is invalid."}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Unauthorized", "message": "The provided token has expired."}), 401

    # Standard HTTP error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "message": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found", "message": "The requested endpoint does not exist."}), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return jsonify({"error": "Payload Too Large", "message": "Uploaded ZIP archive exceeds the maximum allowed size limit."}), 413

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal Server Error", "message": "An unexpected server error occurred."}), 500

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.scans import scans_bp, upload_bp
    from app.routes.system import system_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(scans_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(system_bp)

    # Automatically create tables if not exists
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            app.logger.warning(f"Database tables could not be created automatically: {e}")

    return app
