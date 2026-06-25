"""Web routes for the Deep Learning Algorithms section."""

from flask import render_template
from flask_login import login_required

from ai_analytics_hub.web import web_blueprint


@web_blueprint.get("/dl")
@login_required
def dl_algorithms():
    """Render the Deep Learning Algorithms page (Neural Network Classifier)."""
    return render_template("dl/index.html")
