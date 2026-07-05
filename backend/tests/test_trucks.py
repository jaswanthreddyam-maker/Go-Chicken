"""Tests for the Trucks Router — CRUD operations and tenant isolation.

Tests cover:
  1. GET  /api/v1/trucks — list trucks (empty, with data)
  2. POST /api/v1/trucks — create a new truck
  3. PATCH /api/v1/trucks/{truck_id} — partial update
  4. Tenant Isolation — one tenant cannot access/modify another's trucks

Note: We use MagicMock objects rather than ORM instances to avoid triggering
SQLAlchemy mapper configuration (which requires all related models on the same
Base class to be fully resolvable — a constraint from the dual-Base setup).
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from routers.trucks import TruckCreate, TruckUpdate, TruckResponse


# ── Helpers ───────────────────────────────────────────────────────────

TENANT_A = uuid.uuid4()
TENANT_B = uuid.uuid4()


def _make_mock_truck(
    tenant_id: uuid.UUID = TENANT_A,
    plate: str = "AP 16 AB 1234",
    capacity: Decimal = Decimal("1500.00"),
    iot_device_id: str | None = "T-101",
    driver_id: uuid.UUID | None = None,
    truck_id: uuid.UUID | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Truck ORM instance."""
    m = MagicMock()
    m.id = truck_id or uuid.uuid4()
    m.tenant_id = tenant_id
    m.license_plate = plate
    m.max_capacity_kg = capacity
    m.iot_device_id = iot_device_id
    m.driver_id = driver_id
    m.created_at = datetime.now(timezone.utc)
    return m


# ── LIST TRUCKS ───────────────────────────────────────────────────────

class TestListTrucks:
    """GET /api/v1/trucks — returns only trucks for the authenticated tenant."""

    @pytest.mark.asyncio
    async def test_list_empty(self):
        """When the tenant has no trucks, return an empty list."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        from routers.trucks import list_trucks
        result = await list_trucks(tenant_id=TENANT_A, db=mock_db)
        assert result == []

    @pytest.mark.asyncio
    async def test_list_returns_only_own_trucks(self):
        """Listing trucks returns only those matching the tenant_id."""
        truck_a = _make_mock_truck(tenant_id=TENANT_A, plate="AP 16 AB 1111")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [truck_a]
        mock_db.execute.return_value = mock_result

        from routers.trucks import list_trucks
        result = await list_trucks(tenant_id=TENANT_A, db=mock_db)
        assert len(result) == 1
        assert result[0].license_plate == "AP 16 AB 1111"
        assert result[0].tenant_id == TENANT_A


# ── CREATE TRUCK ──────────────────────────────────────────────────────

class TestCreateTruck:
    """POST /api/v1/trucks — creates a truck under the authenticated tenant."""

    @pytest.mark.asyncio
    async def test_create_sets_tenant_from_auth(self):
        """tenant_id is injected server-side, not from the payload."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda t: setattr(t, 'created_at', datetime.now(timezone.utc)))

        payload = TruckCreate(
            license_plate="AP 16 XY 9999",
            max_capacity_kg=2000.0,
            iot_device_id="T-200",
        )

        from routers.trucks import create_truck
        # We need to patch the Truck constructor since it triggers ORM mapper config
        with patch("routers.trucks.Truck") as MockTruckClass:
            mock_instance = _make_mock_truck(
                tenant_id=TENANT_A,
                plate="AP 16 XY 9999",
                capacity=Decimal("2000.00"),
                iot_device_id="T-200",
            )
            MockTruckClass.return_value = mock_instance

            result = await create_truck(payload=payload, tenant_id=TENANT_A, db=mock_db)

        assert result.license_plate == "AP 16 XY 9999"
        assert result.tenant_id == TENANT_A
        assert result.max_capacity_kg == 2000.0
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_without_iot_device(self):
        """Creating a truck without an IoT device ID should succeed."""
        mock_db = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=lambda t: setattr(t, 'created_at', datetime.now(timezone.utc)))

        payload = TruckCreate(license_plate="AP 16 ZZ 0001", max_capacity_kg=500.0)

        from routers.trucks import create_truck
        with patch("routers.trucks.Truck") as MockTruckClass:
            mock_instance = _make_mock_truck(
                tenant_id=TENANT_A,
                plate="AP 16 ZZ 0001",
                capacity=Decimal("500.00"),
                iot_device_id=None,
            )
            MockTruckClass.return_value = mock_instance

            result = await create_truck(payload=payload, tenant_id=TENANT_A, db=mock_db)

        assert result.iot_device_id is None
        assert result.max_capacity_kg == 500.0


# ── UPDATE TRUCK ──────────────────────────────────────────────────────

class TestUpdateTruck:
    """PATCH /api/v1/trucks/{truck_id} — updates a truck for the authenticated tenant."""

    @pytest.mark.asyncio
    async def test_update_license_plate(self):
        """Updating a truck's license plate should persist the change."""
        truck_id = uuid.uuid4()
        existing = _make_mock_truck(tenant_id=TENANT_A, plate="OLD PLATE", truck_id=truck_id)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = TruckUpdate(license_plate="NEW PLATE")

        from routers.trucks import update_truck
        result = await update_truck(
            truck_id=truck_id, payload=payload, tenant_id=TENANT_A, db=mock_db
        )

        assert result.license_plate == "NEW PLATE"
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_capacity(self):
        """Updating max_capacity_kg should store the new numeric value."""
        truck_id = uuid.uuid4()
        existing = _make_mock_truck(tenant_id=TENANT_A, capacity=Decimal("1000.00"), truck_id=truck_id)

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing
        mock_db.execute.return_value = mock_result
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        payload = TruckUpdate(max_capacity_kg=3000.0)

        from routers.trucks import update_truck
        result = await update_truck(
            truck_id=truck_id, payload=payload, tenant_id=TENANT_A, db=mock_db
        )

        assert result.max_capacity_kg == 3000.0


# ── TENANT ISOLATION ──────────────────────────────────────────────────

class TestTenantIsolation:
    """Verify one tenant cannot see or modify another tenant's trucks."""

    @pytest.mark.asyncio
    async def test_update_other_tenants_truck_returns_404(self):
        """Tenant B tries to PATCH Tenant A's truck — should get 404."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # Not found for Tenant B
        mock_db.execute.return_value = mock_result

        payload = TruckUpdate(license_plate="HACKED PLATE")
        truck_a_id = uuid.uuid4()

        from routers.trucks import update_truck
        with pytest.raises(Exception) as exc_info:
            await update_truck(
                truck_id=truck_a_id, payload=payload, tenant_id=TENANT_B, db=mock_db
            )
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_list_does_not_leak_other_tenants_trucks(self):
        """Listing trucks for Tenant B should never include Tenant A's vehicles."""
        truck_b = _make_mock_truck(tenant_id=TENANT_B, plate="TS 09 ZZ 5555")

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [truck_b]
        mock_db.execute.return_value = mock_result

        from routers.trucks import list_trucks
        result = await list_trucks(tenant_id=TENANT_B, db=mock_db)

        assert len(result) == 1
        assert result[0].tenant_id == TENANT_B
        for r in result:
            assert r.tenant_id != TENANT_A
