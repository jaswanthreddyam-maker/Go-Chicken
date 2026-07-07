"""Analytics Router — Brain Health dashboard for classification monitoring.

Endpoints:
  GET /api/v1/analytics/classification       → Recent classification logs (paginated)
  GET /api/v1/analytics/classification/stats  → Aggregated stats for dashboard

These endpoints let you:
  1. See every classification attempt (message, intent, confidence, latency)
  2. Monitor Ollama vs regex hit rate
  3. Find low-confidence message patterns for threshold tuning
  4. Track Ollama response latency (p50, p95)
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.auth import get_current_tenant
from models.classification_log import ClassificationLog
from schemas.analytics import (
    ClassificationLogOut,
    ClassificationStats,
    ConfidenceStats,
    IntentBreakdown,
    LatencyStats,
    SourceBreakdown,
)

logger = logging.getLogger("go_chicken.analytics")

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics — Brain Health"],
)

settings = get_settings()


# ── Recent Classification Logs ─────────────────────────────────


@router.get(
    "/classification",
    response_model=list[ClassificationLogOut],
    summary="Get recent classification logs",
)
async def get_classification_logs(
    limit: int = Query(50, ge=1, le=500, description="Number of logs to return"),
    source: str = Query(None, description="Filter by source: 'ollama' or 'regex'"),
    intent: str = Query(None, description="Filter by intent: 'ORDER', 'INQUIRY', 'GREETING'"),
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Fetch recent classification log entries, newest first.

    Use filters to drill into specific patterns:
      ?source=regex        → Show only regex fallback cases
      ?intent=ORDER        → Show only order classifications
      ?source=ollama&limit=10 → Last 10 Ollama-classified messages
    """
    query = select(ClassificationLog).order_by(ClassificationLog.created_at.desc())

    if source:
        query = query.where(ClassificationLog.order_source == source)
    if intent:
        query = query.where(ClassificationLog.intent == intent.upper())

    query = query.limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()
    return logs


# ── Aggregated Stats (Brain Health Dashboard) ──────────────────


@router.get(
    "/classification/stats",
    response_model=ClassificationStats,
    summary="Get aggregated classification statistics",
)
async def get_classification_stats(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Full analytics for the Brain Health dashboard.

    Returns:
      - Source breakdown (Ollama vs regex hit rate)
      - Confidence distribution (avg, min, max, low-confidence count)
      - Latency stats (avg, p50, p95, max — Ollama only)
      - Intent breakdown (ORDER vs INQUIRY vs GREETING vs failed)
      - Current confidence threshold from config
    """

    # ── Source Breakdown ───────────────────────────────────────
    source_query = select(
        func.count().label("total"),
        func.count(case((ClassificationLog.order_source == "ollama", 1))).label("ollama_count"),
        func.count(case((ClassificationLog.order_source == "regex", 1))).label("regex_count"),
    )
    source_result = await db.execute(source_query)
    source_row = source_result.one()

    total = source_row.total or 0
    ollama_count = source_row.ollama_count or 0
    regex_count = source_row.regex_count or 0

    source_breakdown = SourceBreakdown(
        ollama_count=ollama_count,
        regex_count=regex_count,
        total=total,
        ollama_hit_rate_pct=round((ollama_count / total * 100) if total > 0 else 0, 1),
    )

    # ── Confidence Stats ───────────────────────────────────────
    conf_query = select(
        func.avg(ClassificationLog.confidence).label("avg_conf"),
        func.min(ClassificationLog.confidence).label("min_conf"),
        func.max(ClassificationLog.confidence).label("max_conf"),
        func.count(
            case((ClassificationLog.confidence < settings.OLLAMA_CONFIDENCE_THRESHOLD, 1))
        ).label("low_conf_count"),
    ).where(ClassificationLog.confidence > 0)  # Exclude failed (0.0) entries
    conf_result = await db.execute(conf_query)
    conf_row = conf_result.one()

    confidence_stats = ConfidenceStats(
        avg_confidence=round(float(conf_row.avg_conf or 0), 3),
        min_confidence=round(float(conf_row.min_conf or 0), 3),
        max_confidence=round(float(conf_row.max_conf or 0), 3),
        low_confidence_count=conf_row.low_conf_count or 0,
    )

    # ── Latency Stats (Ollama-only) ────────────────────────────
    latency_query = select(
        func.avg(ClassificationLog.latency_ms).label("avg_ms"),
        func.max(ClassificationLog.latency_ms).label("max_ms"),
        func.percentile_cont(0.5).within_group(ClassificationLog.latency_ms).label("p50_ms"),
        func.percentile_cont(0.95).within_group(ClassificationLog.latency_ms).label("p95_ms"),
    ).where(
        ClassificationLog.order_source == "ollama",
        ClassificationLog.latency_ms > 0,
    )
    latency_result = await db.execute(latency_query)
    latency_row = latency_result.one()

    latency_stats = LatencyStats(
        avg_ms=round(float(latency_row.avg_ms or 0), 1),
        p50_ms=round(float(latency_row.p50_ms or 0), 1),
        p95_ms=round(float(latency_row.p95_ms or 0), 1),
        max_ms=round(float(latency_row.max_ms or 0), 1),
    )

    # ── Intent Breakdown ───────────────────────────────────────
    intent_query = select(
        func.count(case((ClassificationLog.intent == "ORDER", 1))).label("order_count"),
        func.count(case((ClassificationLog.intent == "INQUIRY", 1))).label("inquiry_count"),
        func.count(case((ClassificationLog.intent == "GREETING", 1))).label("greeting_count"),
        func.count(case((ClassificationLog.intent.is_(None), 1))).label("failed_count"),
    )
    intent_result = await db.execute(intent_query)
    intent_row = intent_result.one()

    intent_breakdown = IntentBreakdown(
        order_count=intent_row.order_count or 0,
        inquiry_count=intent_row.inquiry_count or 0,
        greeting_count=intent_row.greeting_count or 0,
        failed_count=intent_row.failed_count or 0,
    )

    return ClassificationStats(
        source_breakdown=source_breakdown,
        confidence_stats=confidence_stats,
        latency_stats=latency_stats,
        intent_breakdown=intent_breakdown,
        current_threshold=settings.OLLAMA_CONFIDENCE_THRESHOLD,
    )
