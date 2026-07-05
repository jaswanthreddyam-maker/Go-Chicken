"""Trucks Router — Fleet management for the Wholesaler Dashboard.

All endpoints derive ``tenant_id`` from the authenticated session via
``Depends(get_current_tenant)``.  The tenant is **never** accepted from
client-supplied query params or request bodies.
"""

import logging
import uuid
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_tenant
from core.database import get_db
from models.logistics import Truck

logger = logging.getLogger("go_chicken.trucks")

router = APIRouter(
    prefix="/api/v1/trucks",
    tags=["Fleet Management"],
)


# ── Pydantic Schemas ──────────────────────────────────────────────────

class TruckCreate(BaseModel):
    """Payload to register a new truck. ``tenant_id`` is injected server-side."""
    license_plate: str = Field(..., min_length=1, max_length=50, json_schema_extra={"example": "AP 16 AB 1234"})
    max_capacity_kg: float = Field(1000.0, gt=0, json_schema_extra={"example": 2000.0})
    iot_device_id: str | None = Field(None, max_length=100, json_schema_extra={"example": "T-104"})


class TruckUpdate(BaseModel):
    """Partial update payload for a truck."""
    license_plate: str | None = None
    max_capacity_kg: float | None = Field(None, gt=0)
    iot_device_id: str | None = None
    driver_id: uuid.UUID | None = None


class TruckResponse(BaseModel):
    """Serialized truck for API responses."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    license_plate: str
    max_capacity_kg: float
    iot_device_id: str | None = None
    driver_id: uuid.UUID | None = None
    created_at: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/", response_model=List[TruckResponse])
async def list_trucks(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """List all trucks belonging to the authenticated tenant."""
    result = await db.execute(
        select(Truck)
        .where(Truck.tenant_id == tenant_id)
        .order_by(Truck.created_at.desc())
    )
    trucks = result.scalars().all()

    return [
        TruckResponse(
            id=t.id,
            tenant_id=t.tenant_id,
            license_plate=t.license_plate,
            max_capacity_kg=float(t.max_capacity_kg),
            iot_device_id=t.iot_device_id,
            driver_id=t.driver_id,
            created_at=t.created_at.isoformat() if t.created_at else None,
        )
        for t in trucks
    ]


@router.post("/", response_model=TruckResponse, status_code=status.HTTP_201_CREATED)
async def create_truck(
    payload: TruckCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Register a new truck under the authenticated tenant.

    ``tenant_id`` is injected server-side from the authenticated session.
    """
    truck = Truck(
        tenant_id=tenant_id,
        license_plate=payload.license_plate,
        max_capacity_kg=Decimal(str(payload.max_capacity_kg)),
        iot_device_id=payload.iot_device_id,
    )
    db.add(truck)
    await db.commit()
    await db.refresh(truck)

    logger.info(f"🚛 Created truck {truck.id} (plate={truck.license_plate}) for tenant {tenant_id}")

    return TruckResponse(
        id=truck.id,
        tenant_id=truck.tenant_id,
        license_plate=truck.license_plate,
        max_capacity_kg=float(truck.max_capacity_kg),
        iot_device_id=truck.iot_device_id,
        driver_id=truck.driver_id,
        created_at=truck.created_at.isoformat() if truck.created_at else None,
    )


@router.patch("/{truck_id}", response_model=TruckResponse)
async def update_truck(
    truck_id: uuid.UUID,
    payload: TruckUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Update a truck that belongs to the authenticated tenant.

    Returns 404 if the truck does not exist **or** belongs to a different tenant,
    preventing information leakage about other tenants' fleet.
    """
    result = await db.execute(
        select(Truck).where(
            Truck.id == truck_id,
            Truck.tenant_id == tenant_id,  # tenant isolation
        )
    )
    truck = result.scalar_one_or_none()
    if truck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Truck not found.",
        )

    # Apply partial updates
    if payload.license_plate is not None:
        truck.license_plate = payload.license_plate
    if payload.max_capacity_kg is not None:
        truck.max_capacity_kg = Decimal(str(payload.max_capacity_kg))
    if payload.iot_device_id is not None:
        truck.iot_device_id = payload.iot_device_id
    if payload.driver_id is not None:
        truck.driver_id = payload.driver_id

    await db.commit()
    await db.refresh(truck)

    logger.info(f"🚛 Updated truck {truck.id} for tenant {tenant_id}")

    return TruckResponse(
        id=truck.id,
        tenant_id=truck.tenant_id,
        license_plate=truck.license_plate,
        max_capacity_kg=float(truck.max_capacity_kg),
        iot_device_id=truck.iot_device_id,
        driver_id=truck.driver_id,
        created_at=truck.created_at.isoformat() if truck.created_at else None,
    )
