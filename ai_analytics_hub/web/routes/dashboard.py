from flask import render_template
from flask_login import current_user, login_required

from ai_analytics_hub.web import web_blueprint


@web_blueprint.get("/")
def index():
    if current_user.is_authenticated:
        return render_template("dashboard/index.html")
    return render_template("dashboard/landing.html")


@web_blueprint.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard/index.html")
