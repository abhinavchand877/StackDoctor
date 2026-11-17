import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    SECRET_KEY = os.getenv("SECRET_KEY", "stackdoctor-dev-secret-key-change-in-prod-2026")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "stackdoctor-jwt-super-secret-key-2026")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_EXPIRATION_HOURS", "24")))
    
    # Database config: prefer MySQL from env, fallback to SQLite if needed
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://stack_user:stack_pass@localhost:3306/stackdoctor_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload limits
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_SIZE_BYTES", str(50 * 1024 * 1024)))  # 50 MB
    MAX_EXTRACTED_SIZE_BYTES = int(os.getenv("MAX_EXTRACTED_SIZE_BYTES", str(150 * 1024 * 1024)))  # 150 MB
    MAX_ARCHIVE_ENTRIES = int(os.getenv("MAX_ARCHIVE_ENTRIES", "3000"))
    MAX_INSPECT_FILE_SIZE_BYTES = int(os.getenv("MAX_INSPECT_FILE_SIZE_BYTES", str(2 * 1024 * 1024)))  # 2 MB
    
    # Background worker configuration
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    ASYNC_SCANS_ENABLED = os.getenv("ASYNC_SCANS_ENABLED", "false").lower() == "true"


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # For local dev without MySQL running, can use SQLite fallback
    if os.getenv("USE_SQLITE", "false").lower() == "true":
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, '..', 'stackdoctor_dev.db')}"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    # In-memory or temporary SQLite database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False
    # In production, ensure non-default keys are provided
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
