from flask import g, jsonify


def success_response(data, *, status_code: int = 200, meta: dict | None = None):
    payload = {
        "success": True,
        "data": data,
        "error": None,
        "meta": {"request_id": getattr(g, "request_id", None)},
    }
    if meta:
        payload["meta"].update(meta)
    return jsonify(payload), status_code
