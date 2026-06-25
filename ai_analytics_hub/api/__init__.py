from flask import Blueprint

from ai_analytics_hub.core.extensions import csrf

api_blueprint = Blueprint("api", __name__, url_prefix="/api/v1")
csrf.exempt(api_blueprint)

from ai_analytics_hub.api.routes import (  # noqa: E402,F401
    apriori,
    auth,
    chat,
    classifier,
    health,
    jobs,
    ner,
    qa,
    text_generation,
    uploads,
)
