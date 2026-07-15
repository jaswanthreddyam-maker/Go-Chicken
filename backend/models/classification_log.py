"""SQLAlchemy model for classification_logs — persists every Ollama/regex classification attempt.

This is the backbone of the monitoring layer. Every WhatsApp message that
goes through the classification pipeline gets a row here, regardless of
whether Ollama succeeded or regex took over.

Key metrics tracked:
  - confidence: Ollama's confidence score (0.0 if Ollama failed)
  - order_source: "ollama" or "regex" — which classifier was actually used
  - latency_ms: How long Ollama took to respond (0 if it was skipped/failed)
"""

import uuid

from sqlalchemy import Column, String, Text, Float, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID

from models.base import Base


class ClassificationLog(Base):
    """Stores every classification attempt for monitoring and threshold tuning.

    Query examples:
        -- Ollama hit rate
        SELECT order_source, COUNT(*) FROM classification_logs GROUP BY order_source;

        -- Low-confidence patterns
        SELECT message_snippet, confidence FROM classification_logs
        WHERE confidence BETWEEN 0.4 AND 0.6 ORDER BY created_at DESC;

        -- Ollama latency p95
        SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms)
        FROM classification_logs WHERE order_source = 'ollama';
    """

    __tablename__ = "classification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_snippet = Column(Text, nullable=False)       # First 100 chars of the message
    intent = Column(String(20), nullable=True)           # ORDER, INQUIRY, GREETING, or null if Ollama failed
    confidence = Column(Float, default=0.0)              # Ollama's confidence (0.0 if failed)
    order_source = Column(String(20), nullable=False)    # "ollama" or "regex" — which won
    latency_ms = Column(Integer, default=0)              # Ollama response time in ms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
