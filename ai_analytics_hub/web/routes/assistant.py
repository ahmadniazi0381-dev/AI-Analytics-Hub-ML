from flask import render_template, redirect, url_for
from flask_login import login_required

from ai_analytics_hub.web import web_blueprint


@web_blueprint.get("/assistant")
@login_required
def assistant():
    return render_template("assistant/index.html")


@web_blueprint.get("/workbench")
@login_required
def workbench():
    return redirect(url_for("web.ml_algorithms"))
