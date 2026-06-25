from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.responses import success_response


@api_blueprint.get("/health")
def health_check():
    return success_response({"status": "ok", "service": "ai-analytics-hub"})
