from pathlib import Path
from uuid import uuid4

from flask import Flask, g, request
from werkzeug.middleware.proxy_fix import ProxyFix

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.core.commands import register_commands
from ai_analytics_hub.core.config import get_config
from ai_analytics_hub.core.errors import register_error_handlers
from ai_analytics_hub.core.extensions import init_extensions
from ai_analytics_hub.core.logging import configure_logging
from ai_analytics_hub.web import web_blueprint


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="templates",
        static_folder="static",
    )

    config_class = get_config(config_name)
    app.config.from_object(config_class)
    app.wsgi_app = ProxyFix(  # type: ignore[assignment]
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1,
        x_port=1,
    )

    _ensure_runtime_directories(app)
    _validate_security_config(app)
    configure_logging(app)
    init_extensions(app)
    _register_blueprints(app)
    register_error_handlers(app)
    register_commands(app)
    _register_request_hooks(app)
    _register_shell_context(app)

    return app


def _ensure_runtime_directories(app: Flask) -> None:
    directories = [
        app.instance_path,
        app.config["UPLOAD_DIR"],
        app.config["REPORT_DIR"],
        app.config["LOG_DIR"],
        app.config["MODEL_CACHE_DIR"],
    ]
    database_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if database_uri.startswith("sqlite:///") and database_uri != "sqlite:///:memory:":
        sqlite_path = Path(database_uri.removeprefix("sqlite:///"))
        directories.append(str(sqlite_path.parent))
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def _register_blueprints(app: Flask) -> None:
    app.register_blueprint(web_blueprint)
    app.register_blueprint(api_blueprint)


def _validate_security_config(app: Flask) -> None:
    if len(app.config["SECRET_KEY"]) < 32:
        raise RuntimeError("SECRET_KEY must be at least 32 characters long.")
    if len(app.config["JWT_SECRET_KEY"]) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long.")


def _register_request_hooks(app: Flask) -> None:
    @app.before_request
    def attach_request_id() -> None:
        g.request_id = request.headers.get("X-Request-ID", str(uuid4()))

    @app.after_request
    def inject_request_id(response):
        response.headers["X-Request-ID"] = getattr(g, "request_id", str(uuid4()))
        return response


def _register_shell_context(app: Flask) -> None:
    from ai_analytics_hub.core.extensions import db
    from ai_analytics_hub.domain.models import (
        AuditEvent,
        ChatMessage,
        ChatSession,
        Job,
        Upload,
        User,
    )

    @app.shell_context_processor
    def shell_context():
        return {
            "db": db,
            "AuditEvent": AuditEvent,
            "ChatMessage": ChatMessage,
            "ChatSession": ChatSession,
            "Job": Job,
            "Upload": Upload,
            "User": User,
        }
