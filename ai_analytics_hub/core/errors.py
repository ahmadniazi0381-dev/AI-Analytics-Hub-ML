from http import HTTPStatus

from flask import jsonify, render_template, request
from pydantic import ValidationError
from werkzeug.exceptions import HTTPException

from ai_analytics_hub.core.exceptions import (
    DependencyNotInstalledError,
    ExternalServiceConfigurationError,
    ExternalServiceRequestError,
)


def register_error_handlers(app) -> None:
    @app.errorhandler(DependencyNotInstalledError)
    def handle_missing_dependency(error: DependencyNotInstalledError):
        return _build_response(HTTPStatus.SERVICE_UNAVAILABLE, str(error))

    @app.errorhandler(ExternalServiceConfigurationError)
    def handle_service_configuration_error(error: ExternalServiceConfigurationError):
        return _build_response(HTTPStatus.SERVICE_UNAVAILABLE, str(error))

    @app.errorhandler(ExternalServiceRequestError)
    def handle_service_request_error(error: ExternalServiceRequestError):
        return _build_response(HTTPStatus.BAD_GATEWAY, str(error))

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        return _build_response(
            HTTPStatus.BAD_REQUEST,
            "Validation failed",
            details=error.errors(),
        )

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        message = error.description or HTTPStatus(error.code or 500).phrase
        return _build_response(error.code or 500, message)

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception):
        app.logger.exception("Unhandled application error", exc_info=error)
        return _build_response(HTTPStatus.INTERNAL_SERVER_ERROR, "Internal server error")


def _build_response(status_code: int, message: str, details=None):
    if request.path.startswith("/api/"):
        response = {
            "success": False,
            "data": None,
            "error": {
                "message": message,
                "details": details,
                "status_code": status_code,
            },
        }
        return jsonify(response), status_code

    template_name = f"errors/{status_code}.html"
    try:
        return render_template(template_name, message=message), status_code
    except Exception:
        return render_template("errors/generic.html", message=message), status_code
