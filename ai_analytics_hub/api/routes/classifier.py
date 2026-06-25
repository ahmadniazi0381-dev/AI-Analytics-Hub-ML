from flask import current_app
from werkzeug.exceptions import NotFound

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, require_api_roles
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import JobType, Role, Upload
from ai_analytics_hub.domain.schemas import ClassifierJobRequest
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.services.job_service import create_job
from ai_analytics_hub.tasks.jobs import process_classifier_job, run_classifier_job


@api_blueprint.post("/classifier/jobs")
@api_auth_required
def create_classifier_job():
    user = require_api_roles(
        Role.ADMIN.value,
        Role.ANALYST.value,
        error_message="You do not have permission to train classifiers.",
    )
    payload = parse_json(ClassifierJobRequest)
    upload = db.session.get(Upload, payload.upload_id)
    if not upload:
        raise NotFound("Upload not found.")

    job = create_job(
        requested_by_id=user.id,
        upload_id=upload.id,
        job_type=JobType.CLASSIFIER.value,
        parameters=payload.model_dump(),
        model_name="tensorflow-sequential-classifier",
        model_version="1",
    )
    log_event(
        action="classifier_job_created",
        resource_type="job",
        resource_id=str(job.id),
        actor_id=user.id,
        details=payload.model_dump(),
    )

    report_dir = current_app.config["REPORT_DIR"]
    if current_app.config["ASYNC_TASKS_ENABLED"]:
        run_classifier_job.delay(job.id, report_dir)
    else:
        try:
            process_classifier_job(job.id, report_dir)
        except Exception:
            pass

    return success_response({"job": job.to_dict()}, status_code=202)
