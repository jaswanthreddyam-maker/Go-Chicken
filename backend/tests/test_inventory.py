"""Unit tests for Enterprise Inventory Service and Inventory API router."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
import pytest

from models.inventory import InventoryItem, InventoryTransaction
from core.inventory_service import InventoryService


class TestInventoryService:
    """Test enterprise ledger and snapshot inventory business logic."""

    @pytest.mark.asyncio
    async def test_get_all_inventory_seeds_defaults_when_empty(self):
        """When no inventory items exist for tenant, seed defaults (BROILER, DESI, LAYER)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.side_effect = [[], [
            InventoryItem(id=uuid.uuid4(), item_type="BROILER", available_qty=Decimal("820.00"), minimum_stock=Decimal("300.00")),
            InventoryItem(id=uuid.uuid4(), item_type="DESI", available_qty=Decimal("150.00"), minimum_stock=Decimal("100.00")),
            InventoryItem(id=uuid.uuid4(), item_type="LAYER", available_qty=Decimal("340.00"), minimum_stock=Decimal("200.00")),
        ]]
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        tenant_id = uuid.uuid4()
        items = await InventoryService.get_all_inventory(mock_db, tenant_id)

        assert len(items) == 3
        assert mock_db.add.call_count == 3
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_purchase_stock_increments_available_and_creates_txn(self):
        """Purchasing stock should increment available_qty and log PURCHASE transaction."""
        mock_db = AsyncMock()
        tenant_id = uuid.uuid4()
        item_id = uuid.uuid4()
        existing_item = InventoryItem(
            id=item_id,
            tenant_id=tenant_id,
            item_type="BROILER",
            available_qty=Decimal("500.00"),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing_item
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        item = await InventoryService.purchase_stock(
            mock_db, tenant_id, "BROILER", Decimal("300.00"), remarks="Morning Purchase"
        )

        assert item.available_qty == Decimal("800.00")
        assert mock_db.add.call_count == 1
        txn_arg = mock_db.add.call_args[0][0]
        assert isinstance(txn_arg, InventoryTransaction)
        assert txn_arg.transaction_type == "PURCHASE"
        assert txn_arg.quantity == Decimal("300.00")
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_reserve_stock_success(self):
        """Reserving stock when available >= requested should move available -> reserved."""
        mock_db = AsyncMock()
        tenant_id = uuid.uuid4()
        item = InventoryItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            item_type="BROILER",
            available_qty=Decimal("500.00"),
            reserved_qty=Decimal("100.00"),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        success, msg, updated = await InventoryService.reserve_stock(
            mock_db, tenant_id, "BROILER", Decimal("120.00")
        )

        assert success is True
        assert updated.available_qty == Decimal("380.00")
        assert updated.reserved_qty == Decimal("220.00")
        txn = mock_db.add.call_args[0][0]
        assert txn.transaction_type == "RESERVE"
        assert txn.quantity == Decimal("-120.00")

    @pytest.mark.asyncio
    async def test_reserve_stock_insufficient(self):
        """Reserving more stock than available should reject and return informative error message."""
        mock_db = AsyncMock()
        tenant_id = uuid.uuid4()
        item = InventoryItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            item_type="BROILER",
            available_qty=Decimal("140.00"),
            reserved_qty=Decimal("100.00"),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute.return_value = mock_result

        success, msg, updated = await InventoryService.reserve_stock(
            mock_db, tenant_id, "BROILER", Decimal("200.00")
        )

        assert success is False
        assert "Only 140.00 KG is currently available" in msg
        assert updated.available_qty == Decimal("140.00")
        assert updated.reserved_qty == Decimal("100.00")

    @pytest.mark.asyncio
    async def test_load_and_deliver_stock_pipeline(self):
        """Moving stock along state machine: Reserved -> Loaded -> Delivered."""
        mock_db = AsyncMock()
        tenant_id = uuid.uuid4()
        item = InventoryItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            item_type="BROILER",
            available_qty=Decimal("500.00"),
            reserved_qty=Decimal("100.00"),
            loaded_qty=Decimal("0.00"),
            delivered_qty=Decimal("0.00"),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Step 1: Load 80 KG
        await InventoryService.load_stock(mock_db, tenant_id, "BROILER", Decimal("80.00"))
        assert item.reserved_qty == Decimal("20.00")
        assert item.loaded_qty == Decimal("80.00")

        # Step 2: Deliver 80 KG
        await InventoryService.deliver_stock(mock_db, tenant_id, "BROILER", Decimal("80.00"))
        assert item.loaded_qty == Decimal("0.00")
        assert item.delivered_qty == Decimal("80.00")

    @pytest.mark.asyncio
    async def test_record_waste(self):
        """Wastage reduces available stock and logs mortality reason."""
        mock_db = AsyncMock()
        tenant_id = uuid.uuid4()
        item = InventoryItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            item_type="BROILER",
            available_qty=Decimal("500.00"),
            waste_qty=Decimal("0.00"),
        )
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = item
        mock_db.execute.return_value = mock_result
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        updated = await InventoryService.record_waste(
            mock_db, tenant_id, "BROILER", Decimal("5.00"), reason="Dead birds during heat"
        )

        assert updated.available_qty == Decimal("495.00")
        assert updated.waste_qty == Decimal("5.00")
        txn = mock_db.add.call_args[0][0]
        assert txn.transaction_type == "WASTE"
        assert txn.remarks == "Dead birds during heat"
