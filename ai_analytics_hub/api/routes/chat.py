from werkzeug.exceptions import Forbidden, NotFound

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, get_api_current_user
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.domain.models import Role
from ai_analytics_hub.domain.schemas import ChatMessageCreateRequest, ChatSessionCreateRequest
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.services.chat_service import (
    add_user_message_and_generate_reply,
    create_chat_session,
    get_chat_session,
    list_chat_sessions,
)


@api_blueprint.get("/chat/sessions")
@api_auth_required
def get_sessions():
    user = get_api_current_user()
    sessions = [session.to_dict() for session in list_chat_sessions(user_id=user.id)]
    return success_response({"sessions": sessions})


@api_blueprint.post("/chat/sessions")
@api_auth_required
def create_session():
    user = get_api_current_user()
    if user.role not in {Role.ADMIN.value, Role.ANALYST.value, Role.VIEWER.value}:
        raise Forbidden("You do not have permission to use the assistant.")

    payload = parse_json(ChatSessionCreateRequest)
    session = create_chat_session(
        user_id=user.id,
        title=payload.title,
        system_prompt=payload.system_prompt,
    )
    log_event(
        action="chat_session_created",
        resource_type="chat_session",
        resource_id=str(session.id),
        actor_id=user.id,
        details={"title": session.title},
    )
    return success_response({"session": session.to_dict(include_messages=True)}, status_code=201)


@api_blueprint.get("/chat/sessions/<int:session_id>")
@api_auth_required
def get_session(session_id: int):
    user = get_api_current_user()
    session = get_chat_session(session_id=session_id, user_id=user.id)
    if not session:
        raise NotFound("Chat session not found.")
    return success_response({"session": session.to_dict(include_messages=True)})


@api_blueprint.post("/chat/sessions/<int:session_id>/messages")
@api_auth_required
def send_message(session_id: int):
    user = get_api_current_user()
    session = get_chat_session(session_id=session_id, user_id=user.id)
    if not session:
        raise NotFound("Chat session not found.")

    payload = parse_json(ChatMessageCreateRequest)
    result = add_user_message_and_generate_reply(session=session, content=payload.content)
    log_event(
        action="chat_message_completed",
        resource_type="chat_session",
        resource_id=str(session.id),
        actor_id=user.id,
        details={"message_preview": payload.content[:120]},
    )
    return success_response(result)
