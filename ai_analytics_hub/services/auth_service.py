import re
from typing import cast

from flask_jwt_extended import create_access_token
from flask_login import login_user, logout_user

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.core.security import hash_password, verify_password
from ai_analytics_hub.domain.models import Role, User

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
VALID_ROLES = {role.value for role in Role}


def _normalize_email(email: str) -> str:
    normalized_email = email.strip().lower()
    if not EMAIL_PATTERN.fullmatch(normalized_email):
        raise ValueError("Enter a valid email address.")
    return normalized_email


def _normalize_full_name(full_name: str) -> str:
    normalized_name = full_name.strip()
    if len(normalized_name) < 3:
        raise ValueError("Full name must be at least 3 characters long.")
    return normalized_name


def _normalize_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in VALID_ROLES:
        raise ValueError("Select a valid role.")
    return normalized_role


def _validate_password(password: str) -> str:
    normalized_password = password.strip()
    if len(normalized_password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    return normalized_password


def authenticate_user(email: str, password: str) -> User | None:
    user = db.session.query(User).filter_by(email=email.strip().lower()).one_or_none()
    if not user or not verify_password(user.password_hash, password):
        return None
    if not user.is_active:
        return None
    return user


def issue_api_token(user: User) -> str:
    return cast(
        str,
        create_access_token(identity=str(user.id), additional_claims={"role": user.role}),
    )


def login_web_user(user: User) -> None:
    login_user(user, remember=True)


def logout_web_user() -> None:
    logout_user()


def create_user(
    *,
    email: str,
    full_name: str,
    password: str,
    role: str = Role.ANALYST.value,
) -> User:
    normalized_email = _normalize_email(email)
    normalized_name = _normalize_full_name(full_name)
    normalized_role = _normalize_role(role)
    normalized_password = _validate_password(password)
    if get_user_by_email(normalized_email) is not None:
        raise ValueError("A user with this email already exists.")

    user = User(
        email=normalized_email,
        full_name=normalized_name,
        password_hash=hash_password(normalized_password),
        role=normalized_role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def get_user_by_email(email: str) -> User | None:
    return db.session.query(User).filter_by(email=email.strip().lower()).one_or_none()


def get_user_by_id(user_id: int) -> User | None:
    return db.session.get(User, user_id)


def list_users() -> list[User]:
    return db.session.query(User).order_by(User.id.asc()).all()


def update_user_profile(
    *,
    user_id: int,
    full_name: str,
    email: str,
    role: str,
    is_active: bool,
) -> User:
    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError("The selected user was not found.")

    normalized_email = _normalize_email(email)
    normalized_name = _normalize_full_name(full_name)
    normalized_role = _normalize_role(role)
    existing_user = get_user_by_email(normalized_email)
    if existing_user is not None and existing_user.id != user.id:
        raise ValueError("A user with this email already exists.")

    user.email = normalized_email
    user.full_name = normalized_name
    user.role = normalized_role
    user.is_active = is_active
    db.session.commit()
    return user


def reset_user_password_by_id(*, user_id: int, new_password: str) -> User:
    user = get_user_by_id(user_id)
    if user is None:
        raise ValueError("The selected user was not found.")

    user.password_hash = hash_password(_validate_password(new_password))
    db.session.commit()
    return user


def update_user_email(*, current_email: str, new_email: str) -> User:
    user = get_user_by_email(current_email)
    if user is None:
        raise ValueError(f"User with email '{current_email}' was not found.")

    normalized_email = _normalize_email(new_email)
    existing_user = get_user_by_email(normalized_email)
    if existing_user is not None and existing_user.id != user.id:
        raise ValueError(f"Email '{new_email}' is already in use.")

    user.email = normalized_email
    db.session.commit()
    return user


def update_user_role(*, email: str, role: str) -> User:
    user = get_user_by_email(email)
    if user is None:
        raise ValueError(f"User with email '{email}' was not found.")

    user.role = _normalize_role(role)
    db.session.commit()
    return user


def reset_user_password(*, email: str, new_password: str) -> User:
    user = get_user_by_email(email)
    if user is None:
        raise ValueError(f"User with email '{email}' was not found.")

    user.password_hash = hash_password(_validate_password(new_password))
    db.session.commit()
    return user


def ensure_default_admin(email: str, password: str) -> User:
    user = db.session.query(User).filter_by(email=email.lower()).one_or_none()
    if user:
        return user
    return create_user(
        email=email,
        full_name="Platform Administrator",
        password=password,
        role=Role.ADMIN.value,
    )
