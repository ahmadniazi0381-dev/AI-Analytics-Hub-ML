from __future__ import annotations

from collections.abc import Callable

from ai_analytics_hub.domain.models import User
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.services.job_service import create_job, mark_completed, mark_failed, mark_running


def run_tracked_inference_job(
    *,
    user: User,
    job_type: str,
    parameters: dict,
    model_name: str,
    model_version: str,
    inference_action: Callable[[], dict],
    audit_action: str,
    audit_details: dict,
) -> dict:
    job = create_job(
        requested_by_id=user.id,
        job_type=job_type,
        parameters=parameters,
        model_name=model_name,
        model_version=model_version,
    )
    mark_running(job)
    try:
        result = inference_action()
        mark_completed(job, result)
    except Exception as error:
        mark_failed(job, str(error))
        raise

    log_event(
        action=audit_action,
        resource_type="job",
        resource_id=str(job.id),
        actor_id=user.id,
        details=audit_details,
    )
    return {"job": job.to_dict(), "result": result}
