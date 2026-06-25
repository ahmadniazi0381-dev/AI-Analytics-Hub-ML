from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, require_api_roles
from ai_analytics_hub.api.inference_helpers import run_tracked_inference_job
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.api.validation import parse_json
from ai_analytics_hub.domain.models import JobType, Role
from ai_analytics_hub.domain.schemas import QuestionAnswerRequest
from ai_analytics_hub.services.transformer_service import QA_MODEL, answer_question


MODEL_VERSION = "1"


@api_blueprint.post("/qa/ask")
@api_auth_required
def ask_question():
    user = require_api_roles(
        Role.ADMIN.value,
        Role.ANALYST.value,
        Role.VIEWER.value,
        error_message="You do not have permission to use the QA module.",
    )
    payload = parse_json(QuestionAnswerRequest)
    result = run_tracked_inference_job(
        user=user,
        job_type=JobType.QA.value,
        parameters=payload.model_dump(),
        model_name=QA_MODEL,
        model_version=MODEL_VERSION,
        inference_action=lambda: answer_question(
            context=payload.context,
            question=payload.question,
        ),
        audit_action="qa_inference_completed",
        audit_details={"question_preview": payload.question[:120]},
    )
    return success_response(result)
