from ai_analytics_hub import create_app
from ai_analytics_hub.tasks.celery_app import create_celery

flask_app = create_app()
celery_app = create_celery(flask_app)
