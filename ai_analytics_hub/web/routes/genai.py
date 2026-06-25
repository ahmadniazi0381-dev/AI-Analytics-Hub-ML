"""Web routes for the Generative AI (Transformers) section."""

from flask import render_template
from flask_login import login_required

from ai_analytics_hub.web import web_blueprint


@web_blueprint.get("/genai")
@login_required
def genai_algorithms():
    """Render the Generative AI page (QA with voice, Text Generation, NER)."""
    return render_template("genai/index.html")
