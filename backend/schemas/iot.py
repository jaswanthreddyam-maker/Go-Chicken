"""Pydantic schemas for IoT telemetry endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field


class TelemetryPayload(BaseModel):
    """Incoming payload from a truck's IoT sensor."""

    temperature: float = Field(..., description="Current cargo temperature in Celsius")
    latitude: float | None = Field(None, description="GPS latitude of the truck")
    longitude: float | None = Field(None, description="GPS longitude of the truck")
    recorded_at: datetime = Field(..., description="Timestamp of the sensor reading")


class TelemetryResponse(BaseModel):
    """Response after processing a telemetry reading."""

    reading_id: str
    device_id: str
    temperature: float
    alert_triggered: bool
    message: str
