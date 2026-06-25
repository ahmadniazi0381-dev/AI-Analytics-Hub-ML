from __future__ import annotations

import hashlib
from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from ai_analytics_hub.core.extensions import db
from ai_analytics_hub.domain.models import Upload, UploadStatus


ALLOWED_EXTENSIONS = {".csv"}
ALLOWED_MIME_TYPES = {
    "application/csv",
    "application/vnd.ms-excel",
    "text/csv",
    "text/plain",
}


def save_upload(*, file: FileStorage, upload_dir: str, user_id: int) -> Upload:
    original_name = file.filename or "dataset.csv"
    safe_name = secure_filename(original_name)
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Only CSV uploads are supported.")
    if file.mimetype not in ALLOWED_MIME_TYPES:
        raise ValueError("Unsupported file type. Please upload a valid CSV file.")

    target_name = f"{uuid4()}-{safe_name}"
    target_path = Path(upload_dir) / target_name
    file.save(target_path)
    _validate_csv_signature(target_path)

    checksum = hashlib.sha256(target_path.read_bytes()).hexdigest()
    upload = Upload(
        user_id=user_id,
        filename=target_name,
        original_filename=original_name,
        content_type=file.mimetype or "text/csv",
        storage_path=str(target_path),
        checksum_sha256=checksum,
        file_size_bytes=target_path.stat().st_size,
        status=UploadStatus.STORED.value,
    )
    db.session.add(upload)
    db.session.commit()
    return upload


def _validate_csv_signature(target_path: Path) -> None:
    try:
        preview = target_path.read_text(encoding="utf-8", errors="strict")[:2048]
    except UnicodeDecodeError as error:
        target_path.unlink(missing_ok=True)
        raise ValueError("The uploaded file is not valid UTF-8 text.") from error

    if not any(delimiter in preview for delimiter in [",", ";", "\t"]):
        target_path.unlink(missing_ok=True)
        raise ValueError("The uploaded file does not look like a valid CSV dataset.")
