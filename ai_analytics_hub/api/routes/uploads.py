from flask import current_app, request
from werkzeug.exceptions import BadRequest, Forbidden

from ai_analytics_hub.api import api_blueprint
from ai_analytics_hub.api.auth_helpers import api_auth_required, get_api_current_user
from ai_analytics_hub.api.responses import success_response
from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import Role, Upload
from ai_analytics_hub.services.audit_service import log_event
from ai_analytics_hub.services.upload_service import save_upload


@api_blueprint.post("/uploads")
@api_auth_required
def create_upload():
    user = get_api_current_user()
    if user.role not in {Role.ADMIN.value, Role.ANALYST.value}:
        raise Forbidden("You do not have permission to upload datasets.")

    file = request.files.get("file")
    if file is None or not file.filename:
        raise BadRequest("A CSV file is required.")

    upload = save_upload(file=file, upload_dir=current_app.config["UPLOAD_DIR"], user_id=user.id)
    log_event(
        action="dataset_uploaded",
        resource_type="upload",
        resource_id=str(upload.id),
        actor_id=user.id,
        details={"filename": upload.original_filename},
    )
    return success_response({"upload": upload.to_dict()}, status_code=201)


@api_blueprint.get("/uploads")
@api_auth_required
def list_uploads():
    user = get_api_current_user()
    query = db.session.query(Upload).order_by(Upload.created_at.desc())
    if user.role != Role.ADMIN.value:
        query = query.filter_by(user_id=user.id)
    uploads = [upload.to_dict() for upload in query.limit(50).all()]
    return success_response({"uploads": uploads})
