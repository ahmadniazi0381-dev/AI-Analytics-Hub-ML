from __future__ import annotations

from datetime import datetime, timezone

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import Job, JobStatus


def create_job(
    *,
    requested_by_id: int,
    job_type: str,
    upload_id: int | None = None,
    parameters: dict | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
) -> Job:
    job = Job(
        requested_by_id=requested_by_id,
        job_type=job_type,
        upload_id=upload_id,
        status=JobStatus.QUEUED.value,
        parameters_json=parameters or {},
        model_name=model_name,
        model_version=model_version,
    )
    db.session.add(job)
    db.session.commit()
    return job


def mark_running(job: Job) -> Job:
    job.status = JobStatus.RUNNING.value
    job.started_at = datetime.now(timezone.utc)
    db.session.commit()
    return job


def mark_completed(job: Job, result: dict) -> Job:
    job.status = JobStatus.COMPLETED.value
    job.result_json = result
    job.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return job


def mark_failed(job: Job, error_message: str) -> Job:
    job.status = JobStatus.FAILED.value
    job.error_message = error_message
    job.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return job
