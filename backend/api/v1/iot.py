"""IoT & Telemetry Router — receives live truck sensor data."""

from fastapi import APIRouter, Depends, HTTPException, Header
import hmac
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from core.database import get_db
from models.logistics import Truck, IoTReading
from schemas.iot import TelemetryPayload, TelemetryResponse

router = APIRouter()
settings = get_settings()


@router.post(
    "/trucks/{device_id}/telemetry",
    response_model=TelemetryResponse,
    summary="Ingest IoT telemetry from a truck sensor",
)
async def receive_telemetry(
    device_id: str,
    payload: TelemetryPayload,
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db),
):
    """
    Receives temperature and GPS data from a truck's IoT device.
    Automatically flags an alert if the temperature exceeds the safe threshold.
    """
    if not hmac.compare_digest(x_api_key, settings.IOT_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid IoT API key")

    # 1. Look up the truck by its IoT device ID
    result = await db.execute(
        select(Truck).where(Truck.iot_device_id == device_id)
    )
    truck = result.scalar_one_or_none()

    if not truck:
        raise HTTPException(status_code=404, detail=f"No truck registered with device_id: {device_id}")

    # 2. Determine if an alert should be triggered
    alert = payload.temperature > settings.TEMPERATURE_ALERT_THRESHOLD

    # 3. Persist the reading
    reading = IoTReading(
        truck_id=truck.id,
        temperature=payload.temperature,
        recorded_at=payload.recorded_at,
        alert_triggered=alert,
    )
    db.add(reading)
    await db.flush()

    # 4. TODO: If alert is True, push a notification to the driver app
    #    (e.g., via Firebase Cloud Messaging or WebSocket)

    return TelemetryResponse(
        reading_id=str(reading.id),
        device_id=device_id,
        temperature=payload.temperature,
        alert_triggered=alert,
        message="ALERT: Temperature exceeded safe threshold!" if alert else "Reading recorded.",
    )
