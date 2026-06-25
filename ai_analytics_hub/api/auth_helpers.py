from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from flask import g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_login import current_user
from werkzeug.exceptions import Forbidden, Unauthorized

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import User

F = TypeVar("F", bound=Callable[..., Any])


def get_api_current_user() -> User:
    if hasattr(g, "api_current_user"):
        cached_user = cast(User, g.api_current_user)
        _ensure_user_is_active(cached_user)
        return cached_user

    if current_user.is_authenticated:
        user = cast(User, current_user)
        _ensure_user_is_active(user)
        g.api_current_user = user
        return user

    try:
        verify_jwt_in_request(optional=True)
    except Exception as error:
        raise Unauthorized("Authentication is required.") from error

    identity = get_jwt_identity()
    if identity is None:
        raise Unauthorized("Authentication is required.")

    db_user = db.session.get(User, int(identity))
    if db_user is None:
        raise Unauthorized("User not found.")

    resolved_user = cast(User, db_user)
    _ensure_user_is_active(resolved_user)
    g.api_current_user = resolved_user
    return resolved_user


def require_api_roles(*allowed_roles: str, error_message: str | None = None) -> User:
    user = get_api_current_user()
    if user.role not in allowed_roles:
        raise Forbidden(error_message or "You do not have permission to access this resource.")
    return user


def api_auth_required(view_func: F) -> F:
    @wraps(view_func)
    def wrapped(*args: Any, **kwargs: Any):
        get_api_current_user()
        return view_func(*args, **kwargs)

    return cast(F, wrapped)


def _ensure_user_is_active(user: User) -> None:
    if not user.is_active:
        raise Unauthorized("This account is inactive.")
