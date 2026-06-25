from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, require_api_roles
from ai_analytics_hub.api.inference_helpers import run_tracked_inference_job
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.domain.models import JobType, Role
from ai_analytics_hub.domain.schemas import NerRequest
from ai_analytics_hub.services.transformer_service import NER_MODEL, extract_entities


MODEL_VERSION = "1"


@api_blueprint.post("/ner/extract")
@api_auth_required
def extract():
    user = require_api_roles(
        Role.ADMIN.value,
        Role.ANALYST.value,
        Role.VIEWER.value,
        error_message="You do not have permission to use NER.",
    )
    payload = parse_json(NerRequest)
    result = run_tracked_inference_job(
        user=user,
        job_type=JobType.NER.value,
        parameters=payload.model_dump(),
        model_name=NER_MODEL,
        model_version=MODEL_VERSION,
        inference_action=lambda: extract_entities(text=payload.text),
        audit_action="ner_completed",
        audit_details={"text_preview": payload.text[:120]},
    )
    return success_response(result)
