from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ai_analytics_hub.core.security import roles_required
from ai_analytics_hub.domain.models import Role
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.services.auth_service import (
    create_user,
    list_users,
    reset_user_password_by_id,
    update_user_profile,
)
from ai_analytics_hub.web import web_blueprint


def _parse_user_id(raw_user_id: str) -> int:
    try:
        return int(raw_user_id)
    except ValueError as exc:
        raise ValueError("The selected user is invalid.") from exc


@web_blueprint.get("/admin")
@login_required
@roles_required(Role.ADMIN.value)
def admin_index():
    return redirect(url_for("web.admin_users"))


@web_blueprint.route("/admin/users", methods=["GET", "POST"])
@login_required
@roles_required(Role.ADMIN.value)
def admin_users():
    if request.method == "POST":
        action = request.form.get("action", "").strip()
        try:
            if action == "create-user":
                user = create_user(
                    email=request.form.get("email", ""),
                    full_name=request.form.get("full_name", ""),
                    password=request.form.get("password", ""),
                    role=request.form.get("role", Role.ANALYST.value),
                )
                log_event(
                    action="admin_user_created",
                    resource_type="user",
                    resource_id=str(user.id),
                    actor_id=current_user.id,
                    details={"email": user.email, "role": user.role},
                )
                flash(f"User '{user.email}' was created successfully.", "success")
            elif action == "update-user":
                user_id = _parse_user_id(request.form.get("user_id", ""))
                requested_role = request.form.get("role", Role.ANALYST.value)
                requested_is_active = request.form.get("is_active") == "on"
                if user_id == current_user.id and requested_role != Role.ADMIN.value:
                    raise ValueError("You cannot remove your own admin access.")
                if user_id == current_user.id and not requested_is_active:
                    raise ValueError("You cannot deactivate your own account.")

                user = update_user_profile(
                    user_id=user_id,
                    email=request.form.get("email", ""),
                    full_name=request.form.get("full_name", ""),
                    role=requested_role,
                    is_active=requested_is_active,
                )
                log_event(
                    action="admin_user_updated",
                    resource_type="user",
                    resource_id=str(user.id),
                    actor_id=current_user.id,
                    details={
                        "email": user.email,
                        "role": user.role,
                        "is_active": user.is_active,
                    },
                )
                flash(f"User '{user.email}' was updated successfully.", "success")
            elif action == "reset-password":
                user_id = _parse_user_id(request.form.get("user_id", ""))
                user = reset_user_password_by_id(
                    user_id=user_id,
                    new_password=request.form.get("new_password", ""),
                )
                log_event(
                    action="admin_user_password_reset",
                    resource_type="user",
                    resource_id=str(user.id),
                    actor_id=current_user.id,
                    details={"email": user.email},
                )
                flash(f"Password for '{user.email}' was reset successfully.", "success")
            else:
                raise ValueError("Unsupported admin action.")
        except ValueError as exc:
            flash(str(exc), "danger")
        return redirect(url_for("web.admin_users"))

    users = list_users()
    role_choices = [role.value for role in Role]
    user_summary = {
        "total": len(users),
        "admins": sum(user.role == Role.ADMIN.value for user in users),
        "analysts": sum(user.role == Role.ANALYST.value for user in users),
        "viewers": sum(user.role == Role.VIEWER.value for user in users),
    }
    return render_template(
        "admin/users.html",
        users=users,
        role_choices=role_choices,
        user_summary=user_summary,
    )
