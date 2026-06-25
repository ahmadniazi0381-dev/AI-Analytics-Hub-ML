from flask import Blueprint

web_blueprint = Blueprint("web", __name__)

from ai_analytics_hub.web.routes import admin, assistant, auth, dashboard, ml, dl, genai  # noqa: E402,F401
