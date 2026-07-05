"""Pydantic schemas for the AI forecasting engine."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class ForecastRequest(BaseModel):
    """Request to trigger a demand forecast generation."""

    tenant_id: uuid.UUID
    target_date: date = Field(..., description="The date to predict demand for")
    weather_condition: str | None = Field(
        None,
        description="Current weather condition (e.g. 'hot', 'rainy', 'clear'). Used by the LLM as a demand signal.",
    )


class ForecastOut(BaseModel):
    """Serialized AI forecast for dashboard display."""

    id: uuid.UUID
    target_date: date
    weather_condition: str | None
    predicted_demand_kg: Decimal | None
    actual_demand_kg: Decimal | None
    created_at: datetime

    model_config = {"from_attributes": True}
