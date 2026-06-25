import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


def _normalize_database_url(raw_url: str) -> str:
    if raw_url in {"sqlite://", "sqlite:///:memory:"}:
        return raw_url

    if raw_url.startswith("sqlite:///"):
        db_path = raw_url.removeprefix("sqlite:///")
        if db_path.startswith("/") or (len(db_path) > 1 and db_path[1] == ":"):
            return raw_url
        absolute_path = (BASE_DIR / db_path).resolve()
        return f"sqlite:///{absolute_path.as_posix()}"

    return raw_url


class BaseConfig:
    SECRET_KEY = os.getenv(
        "SECRET_KEY", "dev-secret-key-change-me-before-production-1234567890"
    )
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "dev-jwt-secret-change-me-before-production-1234567890"
    )
    SQLALCHEMY_DATABASE_URI = _normalize_database_url(
        os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'instance' / 'app.db'}")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
    UPLOAD_DIR = str(BASE_DIR / os.getenv("UPLOAD_DIR", "data/uploads"))
    REPORT_DIR = str(BASE_DIR / os.getenv("REPORT_DIR", "data/reports"))
    LOG_DIR = str(BASE_DIR / os.getenv("LOG_DIR", "logs"))
    MODEL_CACHE_DIR = str(BASE_DIR / os.getenv("MODEL_CACHE_DIR", "data/model_cache"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH_MB", "250")) * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    JSON_SORT_KEYS = False
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    WTF_CSRF_TIME_LIMIT = None
    ASYNC_TASKS_ENABLED = os.getenv("ASYNC_TASKS_ENABLED", "true").lower() == "true"
    SECURITY_HEADERS_ENABLED = True
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@gmail.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin@123")
    CORS_RESOURCES = {r"/api/*": {"origins": "*"}}
    CHAT_PROVIDER = os.getenv("CHAT_PROVIDER", "openrouter")
    CHAT_MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_MAX_HISTORY_MESSAGES", "16"))
    CHAT_REQUEST_TIMEOUT_SECONDS = int(os.getenv("CHAT_REQUEST_TIMEOUT_SECONDS", "45"))
    CHAT_SYSTEM_PROMPT = os.getenv(
        "CHAT_SYSTEM_PROMPT",
        (
            "You are the AI Analytics Hub assistant. Help users analyze data, "
            "understand AI outputs, and make practical product decisions in a "
            "professional tone."
        ),
    )
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1/chat/completions"
    )
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
    OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5000")
    OPENROUTER_SITE_NAME = os.getenv("OPENROUTER_SITE_NAME", "AI Analytics Hub")
    FORCE_HTTPS = False
    CONTENT_SECURITY_POLICY = {
        "default-src": ["'self'"],
        "script-src": ["'self'", "https://cdn.jsdelivr.net"],
        "style-src": ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"],
        "img-src": ["'self'", "data:"],
        "connect-src": ["'self'"],
        "font-src": ["'self'", "data:"],
    }


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    ENV_NAME = "development"
    SECURITY_HEADERS_ENABLED = False


class TestingConfig(BaseConfig):
    TESTING = True
    ENV_NAME = "testing"
    WTF_CSRF_ENABLED = False
    LOGIN_DISABLED = False
    ASYNC_TASKS_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECURITY_HEADERS_ENABLED = False
    CHAT_PROVIDER = "mock"
    SECRET_KEY = "testing-secret-key-with-sufficient-length-123456"
    JWT_SECRET_KEY = "testing-jwt-secret-key-with-sufficient-length-123456"
    RATELIMIT_STORAGE_URI = "memory://"


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV_NAME = "production"
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    FORCE_HTTPS = True
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", BaseConfig.REDIS_URL)


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(config_name: str | None) -> type[BaseConfig]:
    env_name: str = config_name or os.getenv("FLASK_ENV") or "development"
    return CONFIG_MAP.get(env_name, DevelopmentConfig)
