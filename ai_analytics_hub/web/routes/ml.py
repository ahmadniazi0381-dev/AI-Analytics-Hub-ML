"""Web routes for the Machine Learning Algorithms section."""

from flask import render_template
from flask_login import login_required

from ai_analytics_hub.web import web_blueprint


@web_blueprint.get("/ml")
@login_required
def ml_algorithms():
    """Render the Machine Learning Algorithms page (Apriori)."""
    return render_template("ml/index.html")
