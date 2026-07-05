"""SQLAlchemy model for error_logs — persists background task failures."""

import uuid

from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from models.base import Base


class ErrorLog(Base):
    """Stores errors from background tasks (webhook processing, Ollama calls, etc.).

    Since BackgroundTasks run outside the request lifecycle, exceptions are
    silently swallowed by FastAPI. This table ensures every failure is
    captured and queryable for debugging.
    """

    __tablename__ = "error_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False)        # e.g., "whatsapp_webhook"
    error_type = Column(String(255), nullable=False)     # Exception class name
    error_message = Column(Text, nullable=False)         # Full error message
    stack_trace = Column(Text, nullable=True)            # Full traceback
    payload = Column(JSONB, nullable=True)               # Raw payload that caused it
    created_at = Column(DateTime, server_default=func.now())
