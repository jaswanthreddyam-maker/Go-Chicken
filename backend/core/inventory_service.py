"""Enterprise Inventory Service — ledger-based inventory management.

Enforces an immutable ledger of transactions (PURCHASE, RESERVE, RELEASE,
LOAD, DELIVER, RETURN, WASTE, ADJUSTMENT) and maintains accurate fast-read
snapshots on InventoryItem.
"""

import logging
import uuid
from decimal import Decimal
from typing import List, Tuple, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from models.inventory import InventoryItem, InventoryTransaction

logger = logging.getLogger("go_chicken.inventory_service")


DEFAULT_ITEMS = [
    {"item_type": "BROILER", "minimum_stock": Decimal("300.00"), "reorder_level": Decimal("500.00")},
    {"item_type": "DESI", "minimum_stock": Decimal("100.00"), "reorder_level": Decimal("200.00")},
    {"item_type": "LAYER", "minimum_stock": Decimal("200.00"), "reorder_level": Decimal("350.00")},
]


class InventoryService:
    @staticmethod
    def normalize_item_type(item_type: str) -> str:
        """Normalize poultry item names so queries and orders map consistently."""
        clean = (item_type or "BROILER").strip().upper()
        if clean in ("LIVE BIRD", "LIVE_BIRD", "BROILER"):
            return "BROILER"
        return clean

    @classmethod
    async def get_all_inventory(
        cls, db: AsyncSession, tenant_id: uuid.UUID
    ) -> List[InventoryItem]:
        """Fetch all inventory items for a tenant, seeding defaults if none exist."""
        result = await db.execute(
            select(InventoryItem)
            .where(InventoryItem.tenant_id == tenant_id)
            .order_by(InventoryItem.item_type)
        )
        items = result.scalars().all()
        if not items:
            logger.info(f"Seeding default enterprise inventory items for tenant {tenant_id}")
            for default in DEFAULT_ITEMS:
                item = InventoryItem(
                    tenant_id=tenant_id,
                    item_type=default["item_type"],
                    unit="KG",
                    available_qty=Decimal("820.00") if default["item_type"] == "BROILER" else (Decimal("150.00") if default["item_type"] == "DESI" else Decimal("340.00")),
                    reserved_qty=Decimal("120.00") if default["item_type"] == "BROILER" else (Decimal("0.00") if default["item_type"] == "DESI" else Decimal("20.00")),
                    loaded_qty=Decimal("60.00") if default["item_type"] == "BROILER" else Decimal("0.00"),
                    minimum_stock=default["minimum_stock"],
                    reorder_level=default["reorder_level"],
                )
                db.add(item)
            await db.commit()
            result = await db.execute(
                select(InventoryItem)
                .where(InventoryItem.tenant_id == tenant_id)
                .order_by(InventoryItem.item_type)
            )
            items = result.scalars().all()
        return list(items)

    @classmethod
    async def get_or_create_item(
        cls, db: AsyncSession, tenant_id: uuid.UUID, item_type: str, commit: bool = True
    ) -> InventoryItem:
        """Fetch an item snapshot or create it with 0 available stock if missing."""
        normalized = cls.normalize_item_type(item_type)
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.tenant_id == tenant_id,
                InventoryItem.item_type == normalized,
            )
        )
        item = result.scalar_one_or_none()
        if not isinstance(item, InventoryItem):
            item = None
        if not item:
            item = InventoryItem(
                tenant_id=tenant_id,
                item_type=normalized,
                unit="KG",
                available_qty=Decimal("0.00"),
                reserved_qty=Decimal("0.00"),
                loaded_qty=Decimal("0.00"),
                delivered_qty=Decimal("0.00"),
                waste_qty=Decimal("0.00"),
                minimum_stock=Decimal("200.00"),
                reorder_level=Decimal("400.00"),
            )
            db.add(item)
            if commit:
                await db.commit()
                await db.refresh(item)
        return item

    @classmethod
    async def purchase_stock(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "purchase",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
    ) -> InventoryItem:
        """Record supplier purchase (+ quantity to available stock)."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Purchase quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type)
        item.available_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="PURCHASE",
            quantity=qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Purchased {qty} KG",
            performed_by=performed_by,
        )
        db.add(txn)
        await db.commit()
        await db.refresh(item)
        logger.info(f"[PURCHASE] Tenant {tenant_id} added {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def reserve_stock(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "order",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> Tuple[bool, str, InventoryItem]:
        """Reserve stock for an order. Checks available inventory first."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Reserve quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type, commit=commit)

        if item.available_qty < qty:
            msg = f"Insufficient stock. Only {item.available_qty} KG is currently available."
            logger.warning(
                f"[RESERVE FAILED] Tenant {tenant_id} item {item.item_type}: requested {qty} KG, available {item.available_qty} KG"
            )
            return False, msg, item

        item.available_qty -= qty
        item.reserved_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="RESERVE",
            quantity=-qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Reserved {qty} KG for order",
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[RESERVE SUCCESS] Tenant {tenant_id} reserved {qty} KG of {item.item_type}")
        return True, "Reserved successfully", item

    @classmethod
    async def release_stock(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "order_cancel",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Release previously reserved stock back to available stock."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Release quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type, commit=commit)
        actual_release = min(item.reserved_qty, qty)
        item.reserved_qty = max(Decimal("0.00"), item.reserved_qty - qty)
        item.available_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="RELEASE",
            quantity=qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Released {qty} KG reservation",
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[RELEASE] Tenant {tenant_id} released {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def load_stock(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "truck",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Move stock from Reserved -> Loaded onto truck."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Load quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type, commit=commit)
        item.reserved_qty = max(Decimal("0.00"), item.reserved_qty - qty)
        item.loaded_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="LOAD",
            quantity=-qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Loaded {qty} KG onto truck",
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[LOAD] Tenant {tenant_id} loaded {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def return_loaded_to_available(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "order_unload",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Return loaded stock back to warehouse available stock upon emergency unload or cancel."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Return quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type, commit=commit)
        item.loaded_qty = max(Decimal("0.00"), item.loaded_qty - qty)
        item.available_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="RELEASE",
            quantity=qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Returned {qty} KG loaded stock to available",
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[UNLOAD -> AVAILABLE] Tenant {tenant_id} returned {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def deliver_stock(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reference_type: Optional[str] = "delivery",
        reference_id: Optional[str] = None,
        remarks: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Move stock from Loaded -> Delivered."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Deliver quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type, commit=commit)
        item.loaded_qty = max(Decimal("0.00"), item.loaded_qty - qty)
        item.delivered_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="DELIVER",
            quantity=-qty,
            reference_type=reference_type,
            reference_id=reference_id,
            remarks=remarks or f"Delivered {qty} KG",
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[DELIVER] Tenant {tenant_id} delivered {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def record_waste(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        reason: Optional[str] = "Mortality / dead birds",
        reference_id: Optional[str] = None,
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Record inventory waste (deducted from available stock)."""
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValueError("Waste quantity must be positive")

        item = await cls.get_or_create_item(db, tenant_id, item_type)
        item.available_qty = max(Decimal("0.00"), item.available_qty - qty)
        item.waste_qty += qty

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="WASTE",
            quantity=-qty,
            reference_type="waste",
            reference_id=reference_id,
            remarks=reason,
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[WASTE] Tenant {tenant_id} recorded {qty} KG waste of {item.item_type}: {reason}")
        return item

    @classmethod
    async def record_adjustment(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: str,
        quantity: Decimal,
        remarks: Optional[str] = "Manual inventory audit adjustment",
        performed_by: Optional[str] = None,
        commit: bool = True,
    ) -> InventoryItem:
        """Manual stock audit adjustment (+ or - quantity)."""
        qty = Decimal(str(quantity))

        item = await cls.get_or_create_item(db, tenant_id, item_type)
        item.available_qty = max(Decimal("0.00"), item.available_qty + qty)

        txn = InventoryTransaction(
            tenant_id=tenant_id,
            inventory_item_id=item.id,
            transaction_type="ADJUSTMENT",
            quantity=qty,
            reference_type="adjustment",
            remarks=remarks,
            performed_by=performed_by,
        )
        db.add(txn)
        if commit:
            await db.commit()
            await db.refresh(item)
        logger.info(f"[ADJUSTMENT] Tenant {tenant_id} adjusted {qty} KG of {item.item_type}")
        return item

    @classmethod
    async def get_recent_transactions(
        cls,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        item_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[InventoryTransaction]:
        """Fetch recent ledger transactions for audit trail and dashboard."""
        stmt = (
            select(InventoryTransaction)
            .where(InventoryTransaction.tenant_id == tenant_id)
            .order_by(desc(InventoryTransaction.created_at))
            .limit(limit)
        )
        if item_type:
            normalized = cls.normalize_item_type(item_type)
            # Join or filter by inventory_item
            stmt = (
                select(InventoryTransaction)
                .join(InventoryItem)
                .where(
                    InventoryTransaction.tenant_id == tenant_id,
                    InventoryItem.item_type == normalized,
                )
                .order_by(desc(InventoryTransaction.created_at))
                .limit(limit)
            )

        result = await db.execute(stmt)
        return list(result.scalars().all())
