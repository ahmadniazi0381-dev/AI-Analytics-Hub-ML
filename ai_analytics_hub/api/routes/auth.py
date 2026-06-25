from flask_limiter.util import get_remote_address
from werkzeug.exceptions import Unauthorized

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, get_api_current_user
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.core.extensions import limiter
from ai_analytics_hub.domain.schemas import LoginRequest
from ai_analytics_hub.services.auth_service import authenticate_user, issue_api_token
from ai_analytics_hub.services.audit_service import log_event


@api_blueprint.post("/auth/login")
@limiter.limit("10 per minute", key_func=get_remote_address)
def login():
    payload = parse_json(LoginRequest)
    user = authenticate_user(payload.email, payload.password)
    if not user:
        raise Unauthorized("Invalid email or password.")

    token = issue_api_token(user)
    log_event(
        action="api_login",
        resource_type="user",
        resource_id=str(user.id),
        actor_id=user.id,
        details={"email": user.email},
    )
    return success_response({"token": token, "user": user.to_dict()})


@api_blueprint.get("/auth/me")
@api_auth_required
def me():
    user = get_api_current_user()
    return success_response({"user": user.to_dict()})
