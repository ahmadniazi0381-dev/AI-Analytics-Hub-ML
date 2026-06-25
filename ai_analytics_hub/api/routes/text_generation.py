from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, require_api_roles
from ai_analytics_hub.api.inference_helpers import run_tracked_inference_job
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.domain.models import JobType, Role
from ai_analytics_hub.domain.schemas import TextGenerationRequest
from ai_analytics_hub.services.transformer_service import TEXT_MODEL, generate_text


MODEL_VERSION = "1"


@api_blueprint.post("/text-generation/generate")
@api_auth_required
def generate():
    user = require_api_roles(
        Role.ADMIN.value,
        Role.ANALYST.value,
        Role.VIEWER.value,
        error_message="You do not have permission to use text generation.",
    )
    payload = parse_json(TextGenerationRequest)
    result = run_tracked_inference_job(
        user=user,
        job_type=JobType.TEXT_GENERATION.value,
        parameters=payload.model_dump(),
        model_name=TEXT_MODEL,
        model_version=MODEL_VERSION,
        inference_action=lambda: generate_text(
            prompt=payload.prompt,
            max_new_tokens=payload.max_new_tokens,
            temperature=payload.temperature,
        ),
        audit_action="text_generation_completed",
        audit_details={"prompt_preview": payload.prompt[:120]},
    )
    return success_response(result)
