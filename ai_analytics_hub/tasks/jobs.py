from typing import Any

from celery import shared_task

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import Job, Upload
from ai_analytics_hub.services.apriori_service import run_apriori_analysis
from ai_analytics_hub.services.classifier_service import train_classifier
from ai_analytics_hub.services.job_service import mark_completed, mark_failed, mark_running


def process_apriori_job(job_id: int) -> dict:
    job = _load_job(job_id)
    upload = _require_upload(job)
    parameters = _require_parameters(job)
    mark_running(job)
    try:
        result = run_apriori_analysis(
            upload=upload,
            min_support=float(parameters["min_support"]),
            min_confidence=float(parameters["min_confidence"]),
            min_lift=float(parameters["min_lift"]),
            max_len=int(parameters["max_len"]),
        )
        mark_completed(job, result)
        return result
    except Exception as error:
        mark_failed(job, str(error))
        raise


def process_classifier_job(job_id: int, report_dir: str) -> dict:
    job = _load_job(job_id)
    upload = _require_upload(job)
    parameters = _require_parameters(job)
    mark_running(job)
    try:
        result = train_classifier(
            upload=upload,
            target_column=str(parameters["target_column"]),
            epochs=int(parameters["epochs"]),
            batch_size=int(parameters["batch_size"]),
            test_size=float(parameters["test_size"]),
            report_dir=report_dir,
        )
        mark_completed(job, result)
        return result
    except Exception as error:
        mark_failed(job, str(error))
        raise


@shared_task(name="ai_analytics_hub.tasks.run_apriori_job")
def run_apriori_job(job_id: int) -> dict:
    return process_apriori_job(job_id)


@shared_task(name="ai_analytics_hub.tasks.run_classifier_job")
def run_classifier_job(job_id: int, report_dir: str) -> dict:
    return process_classifier_job(job_id, report_dir)


def _load_job(job_id: int) -> Job:
    job = db.session.get(Job, job_id)
    if not job:
        raise ValueError(f"Job {job_id} was not found.")
    return job


def _require_upload(job: Job) -> Upload:
    if job.upload is None:
        raise ValueError(f"Job {job.id} does not have an associated upload.")
    return job.upload


def _require_parameters(job: Job) -> dict[str, Any]:
    if job.parameters_json is None:
        raise ValueError(f"Job {job.id} does not have parameters.")
    return job.parameters_json
