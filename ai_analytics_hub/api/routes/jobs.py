from werkzeug.exceptions import Forbidden, NotFound

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, get_api_current_user
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import Job, Role


@api_blueprint.get("/jobs/<int:job_id>")
@api_auth_required
def get_job(job_id: int):
    user = get_api_current_user()
    job = db.session.get(Job, job_id)
    if not job:
        raise NotFound("Job not found.")
    if user.role != Role.ADMIN.value and job.requested_by_id != user.id:
        raise Forbidden("You do not have access to this job.")
    return success_response({"job": job.to_dict()})
