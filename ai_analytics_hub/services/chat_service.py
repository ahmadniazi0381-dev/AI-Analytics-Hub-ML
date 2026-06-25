from __future__ import annotations

from datetime import datetime, timezone

import httpx
from flask import current_app

from ai_analytics_hub.core.exceptions import (
    ExternalServiceConfigurationError,
    ExternalServiceRequestError,
)
from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import ChatMessage, ChatSession


def create_chat_session(*, user_id: int, title: str, system_prompt: str | None = None) -> ChatSession:
    session = ChatSession(
        user_id=user_id,
        title=title.strip() or "New Conversation",
        system_prompt=system_prompt or current_app.config["CHAT_SYSTEM_PROMPT"],
        provider=current_app.config["CHAT_PROVIDER"],
        model_name=current_app.config["OPENROUTER_MODEL"],
    )
    db.session.add(session)
    db.session.commit()
    return session


def list_chat_sessions(*, user_id: int) -> list[ChatSession]:
    return (
        db.session.query(ChatSession)
        .filter_by(user_id=user_id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


def get_chat_session(*, session_id: int, user_id: int) -> ChatSession | None:
    return (
        db.session.query(ChatSession)
        .filter_by(id=session_id, user_id=user_id)
        .one_or_none()
    )


def add_user_message_and_generate_reply(*, session: ChatSession, content: str) -> dict:
    user_message = ChatMessage(session_id=session.id, role="user", content=content.strip())
    db.session.add(user_message)
    _touch_session(session, content)
    db.session.commit()

    outbound_messages = _build_conversation_payload(session)
    provider_result = _generate_provider_response(outbound_messages)

    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=provider_result["content"],
        provider_message_id=provider_result.get("provider_message_id"),
        input_tokens=provider_result.get("input_tokens"),
        output_tokens=provider_result.get("output_tokens"),
    )
    db.session.add(assistant_message)
    _touch_session(session, provider_result["content"], is_assistant=True)
    db.session.commit()

    return {
        "session": session.to_dict(include_messages=True),
        "assistant_message": assistant_message.to_dict(),
        "provider": provider_result["provider"],
        "model_name": provider_result["model_name"],
    }


def _touch_session(session: ChatSession, latest_content: str, *, is_assistant: bool = False) -> None:
    session.last_message_at = datetime.now(timezone.utc)
    if session.title == "New Conversation" and not is_assistant:
        session.title = latest_content.strip()[:60] or session.title


def _build_conversation_payload(session: ChatSession) -> list[dict[str, str]]:
    history_limit = current_app.config["CHAT_MAX_HISTORY_MESSAGES"]
    recent_messages = session.messages[-history_limit:]
    payload: list[dict[str, str]] = []
    system_prompt = session.system_prompt or current_app.config["CHAT_SYSTEM_PROMPT"]
    if system_prompt:
        payload.append({"role": "system", "content": system_prompt})
    for message in recent_messages:
        payload.append({"role": message.role, "content": message.content})
    return payload


def _generate_provider_response(messages: list[dict[str, str]]) -> dict:
    provider = current_app.config["CHAT_PROVIDER"].lower()
    if provider == "mock":
        last_user_message = next(
            (message["content"] for message in reversed(messages) if message["role"] == "user"),
            "",
        )
        system_prompt = next(
            (message["content"] for message in messages if message["role"] == "system"),
            "",
        )
        is_kid_mode = "5-year-old" in system_prompt or "kid" in system_prompt.lower()

        if is_kid_mode:
            content = (
                f"Hello there, little explorer! 🦖 I'm your friendly AI buddy. "
                f"You asked: '{last_user_message}'. That's a super cool question! 🌟 "
                f"Think of it like this: just like how puppies learn to fetch a ball by playing, "
                f"we can teach computers to learn and play games with us! "
                f"You are doing an awesome job learning new things! Keep exploring! 🎈✨"
            )
        else:
            content = (
                "Mock assistant response: the chat UI is working, but no real AI provider is configured. "
                f"You said: {last_user_message}"
            )

        return {
            "provider": "mock",
            "model_name": "mock-assistant",
            "content": content,
            "provider_message_id": None,
            "input_tokens": None,
            "output_tokens": None,
        }

    if provider == "openrouter":
        return _call_openrouter(messages)

    raise ExternalServiceConfigurationError(
        f"Unsupported CHAT_PROVIDER '{current_app.config['CHAT_PROVIDER']}'."
    )


def _call_openrouter(messages: list[dict[str, str]]) -> dict:
    api_key = current_app.config["OPENROUTER_API_KEY"]
    if not api_key:
        raise ExternalServiceConfigurationError(
            "OPENROUTER_API_KEY is missing. Add it to your .env file to enable the assistant."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": current_app.config["OPENROUTER_SITE_URL"],
        "X-OpenRouter-Title": current_app.config["OPENROUTER_SITE_NAME"],
    }
    payload = {
        "model": current_app.config["OPENROUTER_MODEL"],
        "messages": messages,
    }

    try:
        response = httpx.post(
            current_app.config["OPENROUTER_BASE_URL"],
            headers=headers,
            json=payload,
            timeout=current_app.config["CHAT_REQUEST_TIMEOUT_SECONDS"],
        )
        response.raise_for_status()
    except httpx.HTTPError as error:
        raise ExternalServiceRequestError(
            "The assistant provider request failed. Check your API key, provider limits, or network access."
        ) from error

    response_payload = response.json()
    choice = response_payload["choices"][0]["message"]
    usage = response_payload.get("usage", {})
    return {
        "provider": "openrouter",
        "model_name": response_payload.get("model", current_app.config["OPENROUTER_MODEL"]),
        "content": choice.get("content", "").strip(),
        "provider_message_id": response_payload.get("id"),
        "input_tokens": usage.get("prompt_tokens"),
        "output_tokens": usage.get("completion_tokens"),
    }
