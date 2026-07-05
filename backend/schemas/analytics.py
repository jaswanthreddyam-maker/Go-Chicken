"""Pydantic schemas for the analytics / monitoring endpoints.

Covers both raw classification log entries and aggregated statistics
for the Brain Health dashboard.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, UUID4


# ── Raw Log Entry ──────────────────────────────────────────────


class ClassificationLogOut(BaseModel):
    """Single classification log entry — returned in the recent logs list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID4
    message_snippet: str
    intent: Optional[str] = None
    confidence: float = 0.0
    order_source: str
    latency_ms: int = 0
    created_at: datetime


# ── Aggregated Stats ───────────────────────────────────────────


class SourceBreakdown(BaseModel):
    """How many classifications each source handled."""

    ollama_count: int = 0
    regex_count: int = 0
    total: int = 0
    ollama_hit_rate_pct: float = Field(
        0.0, description="Percentage of classifications handled by Ollama"
    )


class ConfidenceStats(BaseModel):
    """Ollama confidence distribution across all classifications."""

    avg_confidence: float = 0.0
    min_confidence: float = 0.0
    max_confidence: float = 0.0
    low_confidence_count: int = Field(
        0, description="Number of classifications below the threshold"
    )


class LatencyStats(BaseModel):
    """Ollama response time statistics (only for successful Ollama calls)."""

    avg_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    max_ms: float = 0.0


class IntentBreakdown(BaseModel):
    """Count of each classified intent type."""

    order_count: int = 0
    inquiry_count: int = 0
    greeting_count: int = 0
    failed_count: int = Field(
        0, description="Ollama failed — no intent classified"
    )


class ClassificationStats(BaseModel):
    """Full analytics response for the Brain Health dashboard."""

    source_breakdown: SourceBreakdown
    confidence_stats: ConfidenceStats
    latency_stats: LatencyStats
    intent_breakdown: IntentBreakdown
    current_threshold: float = Field(
        ..., description="Current OLLAMA_CONFIDENCE_THRESHOLD from config"
    )
