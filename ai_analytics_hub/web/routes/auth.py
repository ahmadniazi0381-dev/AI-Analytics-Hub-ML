from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy.exc import OperationalError

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.services.auth_service import authenticate_user, login_web_user, logout_web_user
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.web import web_blueprint


@web_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        try:
            db.session.execute(db.select(1))
            user = authenticate_user(email, password)
        except OperationalError:
            flash("Database is not initialized yet. Run 'flask init-db' first.", "danger")
            return render_template("auth/login.html")
        if not user:
            log_event(
                action="web_login_failed",
                resource_type="user",
                resource_id=None,
                actor_id=None,
                details={"email": email},
            )
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html")

        login_web_user(user)
        log_event(
            action="web_login_succeeded",
            resource_type="user",
            resource_id=str(user.id),
            actor_id=user.id,
            details={"email": user.email},
        )
        flash("Welcome back.", "success")
        return redirect(url_for("web.dashboard"))

    return render_template("auth/login.html")


@web_blueprint.get("/logout")
def logout():
    if current_user.is_authenticated:
        log_event(
            action="web_logout",
            resource_type="user",
            resource_id=str(current_user.id),
            actor_id=current_user.id,
            details={"email": current_user.email},
        )
        logout_web_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("web.login"))
