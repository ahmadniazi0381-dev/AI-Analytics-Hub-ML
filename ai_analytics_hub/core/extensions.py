from typing import Any

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf import CSRFProtect
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
cors = CORS()
talisman = Talisman(content_security_policy=None)


def init_extensions(app: Any) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = "web.login"
    login_manager.login_message_category = "warning"
    jwt.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    cors_resources = app.config.get("CORS_RESOURCES", {})
    cors.init_app(app, resources=cors_resources)
    if app.config.get("SECURITY_HEADERS_ENABLED", True):
        content_security_policy = app.config.get("CONTENT_SECURITY_POLICY")
        if not isinstance(content_security_policy, dict | None):
            content_security_policy = None
        talisman.init_app(
            app,
            content_security_policy=content_security_policy,
            force_https=app.config.get("FORCE_HTTPS", False),
        )
