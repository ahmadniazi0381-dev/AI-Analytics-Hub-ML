from flask import request

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import AuditEvent


def log_event(
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    actor_id: int | None,
    details: dict | None = None,
) -> None:
    event = AuditEvent(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        details_json=details or {},
    )
    db.session.add(event)
    db.session.commit()
