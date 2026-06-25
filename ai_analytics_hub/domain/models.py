"""
Domain models for the Analytics Platform.

Each class maps directly to a table defined in schema.sql.
SQLAlchemy handles all ORM operations; raw SQL is only used
for schema introspection and migration purposes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from flask_login import UserMixin
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ai_analytics_hub.core.extensions import Base, db, login_manager


def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(UTC)


class Role(StrEnum):
    """User roles controlling access levels across the platform."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UploadStatus(StrEnum):
    """Lifecycle states for a dataset upload."""

    STORED = "stored"
    FAILED = "failed"


class JobType(StrEnum):
    """Supported background job types."""

    APRIORI = "apriori"
    CLASSIFIER = "classifier"
    QA = "qa"
    TEXT_GENERATION = "text_generation"
    NER = "ner"


class JobStatus(StrEnum):
    """Execution states for a background job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at columns.

    Both columns are timezone-aware and automatically managed:
    created_at is set once on insert; updated_at is refreshed on every update.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )


class User(UserMixin, TimestampMixin, Base):
    """
    Registered platform user.

    Passwords are never stored in plain text; only bcrypt hashes are kept.
    The role field controls which routes and actions are accessible.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), default=Role.ANALYST.value, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    uploads: Mapped[list[Upload]] = relationship(back_populates="owner", lazy="selectin")
    jobs: Mapped[list[Job]] = relationship(back_populates="requested_by", lazy="selectin")
    chat_sessions: Mapped[list[ChatSession]] = relationship(
        back_populates="owner", lazy="selectin"
    )

    def get_id(self) -> str:
        """Return the user primary key as a string (required by Flask-Login)."""
        return str(self.id)

    def to_dict(self) -> dict:
        """Serialize the user to a JSON-safe dict (excludes password_hash)."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
        }

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"


@login_manager.user_loader
def load_user(user_id: str) -> User | None:
    """Load a user from the database by their session ID."""
    return db.session.get(User, int(user_id))


class Upload(TimestampMixin, Base):
    """
    A CSV dataset file uploaded by a user.

    The actual file bytes are stored on disk at storage_path.
    The checksum_sha256 is used to detect duplicate uploads.
    """

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=UploadStatus.STORED.value)

    owner: Mapped[User] = relationship(back_populates="uploads", lazy="joined")
    jobs: Mapped[list[Job]] = relationship(back_populates="upload", lazy="selectin")

    def to_dict(self) -> dict:
        """Serialize the upload to a JSON-safe dict."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "original_filename": self.original_filename,
            "content_type": self.content_type,
            "storage_path": self.storage_path,
            "checksum_sha256": self.checksum_sha256,
            "file_size_bytes": self.file_size_bytes,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Upload id={self.id} filename={self.original_filename!r} status={self.status!r}>"


class Job(TimestampMixin, Base):
    """
    A background analytics or inference job.

    Jobs are created immediately with status='queued' and transitioned
    to 'running' → 'completed' or 'failed' by the Celery worker.
    Results and errors are stored as JSON in result_json / error_message.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    upload_id: Mapped[int | None] = mapped_column(
        ForeignKey("uploads.id"), nullable=True, index=True
    )
    requested_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32), default=JobStatus.QUEUED.value, nullable=False
    )
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameters_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    result_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    upload: Mapped[Upload | None] = relationship(back_populates="jobs", lazy="joined")
    requested_by: Mapped[User] = relationship(back_populates="jobs", lazy="joined")

    def to_dict(self) -> dict:
        """Serialize the job to a JSON-safe dict."""
        return {
            "id": self.id,
            "upload_id": self.upload_id,
            "requested_by_id": self.requested_by_id,
            "job_type": self.job_type,
            "status": self.status,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "parameters": self.parameters_json or {},
            "result": self.result_json,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<Job id={self.id} type={self.job_type!r} status={self.status!r}>"


class AuditEvent(Base):
    """
    An immutable audit log entry.

    Every significant action (login, upload, admin change) is recorded here
    for compliance and debugging purposes. Rows are never updated or deleted.
    """

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(64), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    def to_dict(self) -> dict:
        """Serialize the audit event to a JSON-safe dict."""
        return {
            "id": self.id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "details": self.details_json or {},
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<AuditEvent id={self.id} action={self.action!r}>"


class ChatSession(TimestampMixin, Base):
    """
    A named conversation thread belonging to a user.

    Each session stores its provider and model so that conversations can be
    replayed or migrated to a different backend without data loss.
    """

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Conversation")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="openrouter")
    model_name: Mapped[str] = mapped_column(
        String(255), nullable=False, default="openrouter/free"
    )
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    owner: Mapped[User] = relationship(back_populates="chat_sessions", lazy="joined")
    messages: Mapped[list[ChatMessage]] = relationship(
        back_populates="session",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        """
        Serialize the session to a JSON-safe dict.

        Args:
            include_messages: When True, embed all messages in the response.
        """
        payload: dict[str, Any] = {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "provider": self.provider,
            "model_name": self.model_name,
            "system_prompt": self.system_prompt,
            "last_message_at": (
                self.last_message_at.isoformat() if self.last_message_at else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_messages:
            payload["messages"] = [message.to_dict() for message in self.messages]
        return payload

    def __repr__(self) -> str:
        return f"<ChatSession id={self.id} title={self.title!r}>"


class ChatMessage(Base):
    """
    A single message within a ChatSession.

    The role is either 'user' or 'assistant'. Token counts are stored
    for cost tracking when using paid provider APIs.
    """

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages", lazy="joined")

    def to_dict(self) -> dict:
        """Serialize the message to a JSON-safe dict."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "provider_message_id": self.provider_message_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"<ChatMessage id={self.id} role={self.role!r}>"
