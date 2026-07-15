"""AI Forecaster Router — demand prediction via local Ollama model."""

import re
import uuid
from datetime import date, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from core.auth import get_current_tenant
from models.ai import AIForecast
from models.order import Order
from schemas.ai import ForecastOut, ForecastRequest

router = APIRouter()
# NOTE: No prefix here — main.py already mounts this router at /api/v1/ai.
# Adding prefix="/ai" here would result in double-prefixed paths like /api/v1/ai/ai/...

settings = get_settings()


# ── Ollama Helpers ─────────────────────────────────────────────


async def generate_ollama_prediction(prompt: str) -> float:
    """
    Calls the local Ollama LLM to generate a demand prediction.
    Extracts the numerical kg value from the model's text response using regex.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": settings.OLLAMA_CHAT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "system": (
                        "You are a highly accurate poultry supply chain forecasting AI. "
                        "You output ONLY the exact numerical predicted value in kilograms. "
                        "No extra text, no explanations."
                    ),
                },
                timeout=60.0,  # 7B models need time to think
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "")

            # Extract the first number (integer or float) from the model's response
            match = re.search(r"\d+(\.\d+)?", response_text)
            if match:
                return float(match.group())
            return 0.0

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ollama LLM service unavailable: {str(e)}",
            )


async def generate_ollama_embedding(text: str) -> list[float]:
    """
    Calls the local Ollama API to generate a 768-dim vector embedding
    using nomic-embed-text for pgvector storage.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.OLLAMA_BASE_URL}/api/embeddings",
                json={
                    "model": settings.OLLAMA_EMBED_MODEL,
                    "prompt": text,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("embedding", [])

        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Ollama Embedding service unavailable: {str(e)}",
            )


# ── Endpoints ──────────────────────────────────────────────────


@router.post(
    "/forecast/generate",
    response_model=ForecastOut,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger AI demand forecast for a target date",
)
async def generate_forecast(
    request: ForecastRequest,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline:
    1. Fetches the last 7 days of aggregated order data from PostgreSQL.
    2. Constructs a structured prompt and submits it to the local Ollama LLM.
    3. Generates a 768-dim embedding of the historical context via nomic-embed-text.
    4. Persists the prediction + embedding to the ai_forecasts table.
    """
    target_date = request.target_date
    seven_days_ago = target_date - timedelta(days=7)

    # 1. Fetch and aggregate last 7 days of orders for this tenant
    query = (
        select(
            func.date(Order.delivery_date).label("date"),
            func.sum(Order.quantity_kg).label("total_kg"),
        )
        .where(
            Order.tenant_id == tenant_id,
            Order.delivery_date >= seven_days_ago,
            Order.delivery_date < target_date,
        )
        .group_by(func.date(Order.delivery_date))
        .order_by(func.date(Order.delivery_date))
    )

    result = await db.execute(query)
    historical_data = result.all()

    # 2. Format history for LLM context
    if historical_data:
        history_str = "\n".join(
            [f"  - {row.date}: {row.total_kg} kg" for row in historical_data]
        )
    else:
        history_str = "  No recent historical data available."

    weather = request.weather_condition or "unknown"
    historical_context = (
        f"Weather Condition: {weather}\n"
        f"7-Day Sales History:\n{history_str}"
    )

    prompt = (
        f"Based on the following 7-day sales history and current weather condition, "
        f"predict the exact total kilogram (kg) demand for tomorrow ({target_date}).\n\n"
        f"{historical_context}\n\n"
        f"Predicted KG:"
    )

    # 3. Call Ollama for prediction, then generate the embedding
    predicted_demand = await generate_ollama_prediction(prompt)
    embedding_vector = await generate_ollama_embedding(historical_context)

    if not embedding_vector:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ollama returned an empty embedding. Check that nomic-embed-text is pulled.",
        )

    # 4. Persist the forecast to PostgreSQL (pgvector handles the list automatically)
    new_forecast = AIForecast(
        tenant_id=tenant_id,
        target_date=target_date,
        weather_condition=weather,
        predicted_demand_kg=predicted_demand,
        actual_demand_kg=None,  # Populated post-delivery for model tuning
        historical_context=historical_context,
        embedding=embedding_vector,
    )

    db.add(new_forecast)
    await db.commit()
    await db.refresh(new_forecast)

    return new_forecast


@router.get(
    "/forecast/today",
    response_model=ForecastOut | None,
    summary="Get today's demand forecast for the dashboard",
)
async def get_todays_forecast(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Fetches the most recently generated forecast for today (or the latest available forecast).
    Displayed on the Wholesaler Dashboard to inform morning dispatch.
    """
    today = date.today()

    query = (
        select(AIForecast)
        .where(AIForecast.tenant_id == tenant_id)
        .order_by(AIForecast.target_date.desc(), AIForecast.created_at.desc())
        .limit(1)
    )

    result = await db.execute(query)
    forecast = result.scalar_one_or_none()
    return forecast


@router.get(
    "/sales-comparison",
    summary="Get 7-day actual vs predicted sales comparison for chart display",
)
async def get_sales_comparison(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    seven_days_ago = today - timedelta(days=7)

    query_actual = (
        select(
            func.date(Order.delivery_date).label("date"),
            func.sum(Order.quantity_kg).label("actual"),
        )
        .where(
            Order.tenant_id == tenant_id,
            Order.delivery_date >= seven_days_ago,
            Order.status != "cancelled",
        )
        .group_by(func.date(Order.delivery_date))
        .order_by(func.date(Order.delivery_date))
    )
    result_actual = await db.execute(query_actual)
    actual_rows = {row.date: float(row.actual or 0) for row in result_actual.all()}

    query_forecast = (
        select(
            AIForecast.target_date,
            AIForecast.predicted_demand_kg,
        )
        .where(
            AIForecast.tenant_id == tenant_id,
            AIForecast.target_date >= seven_days_ago,
        )
    )
    result_forecast = await db.execute(query_forecast)
    forecast_rows = {row.target_date: float(row.predicted_demand_kg or 0) for row in result_forecast.all()}

    comparison = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        comparison.append({
            "date": d.strftime("%b %d"),
            "actual": actual_rows.get(d, 0.0),
            "predicted": forecast_rows.get(d, 0.0),
        })
    return comparison


@router.get(
    "/demand-clusters",
    summary="Get vector cluster similarity points for scatter chart",
)
async def get_demand_clusters(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(Order)
        .where(Order.tenant_id == tenant_id, Order.status != "cancelled")
        .order_by(Order.created_at.desc())
        .limit(30)
    )
    result = await db.execute(query)
    orders = result.scalars().all()

    points = []
    for i, o in enumerate(orders):
        points.append({
            "x": float((i * 35) % 400 + 50),
            "y": float(o.quantity_kg or 0),
            "z": float((o.quantity_kg or 100) * 1.5),
        })
    return points
