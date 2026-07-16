"""Core OrderService orchestrator — governs order lifecycle transitions, audit logging, and domain invariants."""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.order import Order
from models.order_timeline import OrderTimeline
from core.order_state_machine import OrderStateMachine
from core.exceptions import InsufficientInventoryError

logger = logging.getLogger("go_chicken.order_service")


@dataclass
class OrderTransitionResult:
    """Typed result returned by every OrderService transition."""

    success: bool
    order: Optional[Order]
    previous_status: str
    new_status: str
    emitted_events: List[str] = field(default_factory=list)
    message: str = ""


class OrderService:
    """Service layer aggregate orchestrator for Order lifecycle transitions."""

    @classmethod
    async def _before_transition(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        target_status: str,
        payload: Dict[str, Any],
    ) -> None:
        """Hook executed before domain validation."""
        # Ensure order belongs to tenant
        if str(order.tenant_id) != str(tenant_id):
            raise PermissionError("Order does not belong to the active tenant.")

    @classmethod
    async def _mutate_confirm(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        payload: Dict[str, Any],
        performed_by: str,
    ) -> None:
        if payload.get("unit_price") is not None:
            order.unit_price = Decimal(str(payload["unit_price"]))
            order.total_amount = order.unit_price * order.quantity_kg
        if payload.get("truck_id") is not None:
            order.truck_id = payload["truck_id"]

        # Synchronous ACID inventory reservation inside transaction
        from core.inventory_service import InventoryService
        success, msg, _ = await InventoryService.reserve_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=order.item_type,
            quantity=order.quantity_kg,
            reference_type="order",
            reference_id=str(order.id),
            remarks=f"Reserved for confirmed order {order.id}",
            performed_by=performed_by,
            commit=False,
        )
        if not success:
            raise InsufficientInventoryError(msg)

    @classmethod
    async def _mutate_load(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        payload: Dict[str, Any],
        performed_by: str,
    ) -> None:
        target_truck_id = payload.get("truck_id") or order.truck_id
        if target_truck_id:
            from core.truck_service import TruckService
            success, msg = await TruckService.allocate_capacity(
                db=db,
                tenant_id=tenant_id,
                order=order,
                truck_id=target_truck_id,
                performed_by=performed_by,
                commit=False,
            )
            if not success:
                from core.exceptions import TruckCapacityExceededError
                raise TruckCapacityExceededError(msg)

        from core.inventory_service import InventoryService
        await InventoryService.load_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=order.item_type,
            quantity=order.quantity_kg,
            reference_type="order",
            reference_id=str(order.id),
            remarks=f"Loaded onto truck {order.truck_id}",
            performed_by=performed_by,
            commit=False,
        )

    @classmethod
    async def _mutate_dispatch(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        payload: Dict[str, Any],
    ) -> None:
        if payload.get("driver_phone") is not None:
            order.driver_phone = str(payload["driver_phone"])
        if payload.get("driver_name") is not None:
            order.driver_name = str(payload["driver_name"])
        order.dispatch_time = payload.get("dispatch_time") or datetime.now(timezone.utc)

    @classmethod
    async def _mutate_deliver(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        payload: Dict[str, Any],
        performed_by: str,
    ) -> None:
        order.delivery_date = datetime.now(timezone.utc)
        actual_kg = Decimal(str(payload.get("actual_delivered_kg", order.quantity_kg)))
        waste_kg = Decimal(str(payload.get("waste_kg", 0)))

        from core.inventory_service import InventoryService
        await InventoryService.deliver_stock(
            db=db,
            tenant_id=tenant_id,
            item_type=order.item_type,
            quantity=actual_kg,
            reference_type="order",
            reference_id=str(order.id),
            remarks=f"Delivered order {order.id}",
            performed_by=performed_by,
            commit=False,
        )
        if waste_kg > 0:
            await InventoryService.record_waste(
                db=db,
                tenant_id=tenant_id,
                item_type=order.item_type,
                quantity=waste_kg,
                reason=f"Mortality waste on order {order.id}",
                reference_id=str(order.id),
                performed_by=performed_by,
                commit=False,
            )

    @classmethod
    async def _mutate_cancel(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        previous_status: str,
        payload: Dict[str, Any],
        performed_by: str,
    ) -> None:
        from core.inventory_service import InventoryService
        if previous_status == "confirmed":
            await InventoryService.release_stock(
                db=db,
                tenant_id=tenant_id,
                item_type=order.item_type,
                quantity=order.quantity_kg,
                reference_type="order_cancel",
                reference_id=str(order.id),
                remarks=f"Released reservation on order cancel {order.id}",
                performed_by=performed_by,
                commit=False,
            )
        elif previous_status == "loaded":
            await InventoryService.return_loaded_to_available(
                db=db,
                tenant_id=tenant_id,
                item_type=order.item_type,
                quantity=order.quantity_kg,
                reference_type="order_cancel",
                reference_id=str(order.id),
                remarks=f"Returned loaded stock on order cancel {order.id}",
                performed_by=performed_by,
                commit=False,
            )

    @classmethod
    async def _mutate(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        previous_status: str,
        target_status: str,
        payload: Dict[str, Any],
        performed_by: str,
    ) -> None:
        """Synchronous ACID state & inventory dispatcher inside the DB transaction."""
        clean_target = (target_status or "").strip().lower()
        order.status = clean_target

        if clean_target == "confirmed":
            await cls._mutate_confirm(db, tenant_id, order, payload, performed_by)
        elif clean_target == "loaded":
            await cls._mutate_load(db, tenant_id, order, payload, performed_by)
        elif clean_target == "out_for_delivery":
            await cls._mutate_dispatch(db, tenant_id, order, payload)
        elif clean_target == "delivered":
            await cls._mutate_deliver(db, tenant_id, order, payload, performed_by)
        elif clean_target == "cancelled":
            await cls._mutate_cancel(db, tenant_id, order, previous_status, payload, performed_by)

    @classmethod
    async def _write_timeline(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        previous_status: str,
        target_status: str,
        performed_by: str,
        reason: Optional[str],
        payload: Dict[str, Any],
    ) -> OrderTimeline:
        """Write immutable audit entry to OrderTimeline table."""
        ctx = dict(payload or {})
        if target_status == "loaded" and order.truck_id:
            ctx["truck_id"] = str(order.truck_id)
            ctx["allocated_kg"] = float(order.quantity_kg)
            ctx["operator"] = performed_by
        elif target_status == "out_for_delivery":
            ctx["driver_name"] = order.driver_name
            ctx["driver_phone"] = order.driver_phone
            ctx["dispatch_time"] = order.dispatch_time.isoformat() if order.dispatch_time else None
        elif target_status == "delivered":
            ctx["actual_delivered_kg"] = str(payload.get("actual_delivered_kg", order.quantity_kg))
            ctx["waste_kg"] = str(payload.get("waste_kg", "0.00"))
            ctx["receiver_name"] = payload.get("receiver_name")
            ctx["receiver_phone"] = payload.get("receiver_phone")
            ctx["delivery_gps_lat"] = payload.get("delivery_gps_lat")
            ctx["delivery_gps_lng"] = payload.get("delivery_gps_lng")
            ctx["delivery_photo_url"] = payload.get("delivery_photo_url")
            ctx["delivery_signature_url"] = payload.get("delivery_signature_url")
            ctx["remarks"] = payload.get("remarks")
            ctx["invoice_status"] = "GENERATED_PENDING_KHATA"

        timeline_entry = OrderTimeline(
            tenant_id=tenant_id,
            order_id=order.id,
            from_status=previous_status,
            to_status=target_status,
            performed_by=performed_by,
            reason=reason,
            transition_context=ctx,
        )
        db.add(timeline_entry)
        return timeline_entry

    @classmethod
    async def _emit_events(
        cls,
        order: Order,
        previous_status: str,
        target_status: str,
        payload: Dict[str, Any],
    ) -> List[str]:
        """Post-commit event dispatcher hook."""
        emitted: List[str] = []
        event_name = f"Order{target_status.capitalize().replace('_', '')}IntegrationEvent"
        emitted.append(event_name)
        if target_status == "delivered":
            emitted.append("OrderInvoiceGeneratedIntegrationEvent")

        op_map = {
            "confirmed": "reserve",
            "loaded": "load",
            "delivered": "deliver",
            "cancelled": "release",
        }
        inventory_op = op_map.get(target_status, "none")

        # Structured log entry for debugging & audit trails
        logger.info(
            "Order transition completed",
            extra={
                "order_id": str(order.id),
                "tenant_id": str(order.tenant_id),
                "from": previous_status,
                "to": target_status,
                "transition": f"{previous_status}->{target_status}",
                "version": str(getattr(order, "version", 1)),
                "inventory_operation": inventory_op,
                "emitted": emitted,
            },
        )
        return emitted

    @classmethod
    async def _execute_transition(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        target_status: str,
        performed_by: str = "SYSTEM",
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Core 6-step deterministic transition engine."""
        payload = payload or {}
        previous_status = order.status

        try:
            # Step 1: Pre-transition hook
            await cls._before_transition(db, tenant_id, order, target_status, payload)

            # Step 2: Domain validation via OrderStateMachine
            is_valid, msg = OrderStateMachine.validate_transition(
                current_status=previous_status,
                target_status=target_status,
                quantity_kg=order.quantity_kg,
                truck_id=order.truck_id,
                payload=payload,
            )
            if not is_valid:
                return OrderTransitionResult(
                    success=False,
                    order=order,
                    previous_status=previous_status,
                    new_status=target_status,
                    emitted_events=[],
                    message=msg,
                )

            # Step 3: Synchronous ACID state mutations
            await cls._mutate(db, tenant_id, order, previous_status, target_status, payload, performed_by)

            # Step 4: Write immutable audit ledger entry
            await cls._write_timeline(
                db=db,
                tenant_id=tenant_id,
                order=order,
                previous_status=previous_status,
                target_status=target_status,
                performed_by=performed_by,
                reason=reason,
                payload=payload,
            )

            # Step 5: Write integration events to integration_outbox within same ACID transaction
            emitted = await cls._emit_events(order, previous_status, target_status, payload)
            from core.outbox_service import OutboxService
            await OutboxService.record_events(
                db=db,
                tenant_id=tenant_id,
                aggregate_type="Order",
                aggregate_id=order.id,
                event_types=emitted,
                payload=payload,
                commit=False,
            )

            # Step 6: Commit DB transaction atomically (Order + Inventory + Timeline + Outbox)
            await db.commit()
            await db.refresh(order)

            # Step 7: Broadcast SSE Event for Dashboard
            from core.event_broadcaster import broadcast_event
            
            # Fetch user name for rich toast
            from models.user import User
            from sqlalchemy import select
            user = await db.scalar(select(User).where(User.id == order.retailer_id))
            customer_name = user.name if user else "Retailer"
            
            event_type = f"ORDER_{target_status.upper()}"
            await broadcast_event(event_type, {
                "order_id": str(order.id),
                "customer": customer_name,
                "product": order.item_type,
                "quantity": float(order.quantity_kg),
                "amount": float(order.total_amount),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            # Also broadcast inventory change if applicable
            op_map = {"confirmed": "reserve", "loaded": "load", "delivered": "deliver", "cancelled": "release"}
            inventory_op = op_map.get(target_status, "none")
            if inventory_op != "none":
                await broadcast_event("INVENTORY_CHANGED", {
                    "item_type": order.item_type,
                    "operation": inventory_op,
                    "quantity": float(order.quantity_kg)
                })

            return OrderTransitionResult(
                success=True,
                order=order,
                previous_status=previous_status,
                new_status=target_status,
                emitted_events=emitted,
                message="Transition completed successfully",
            )

        except Exception as exc:
            await db.rollback()
            order.status = previous_status
            logger.error("Transition failed with error: %s", exc, exc_info=True)
            return OrderTransitionResult(
                success=False,
                order=order,
                previous_status=previous_status,
                new_status=target_status,
                emitted_events=[],
                message=str(exc),
            )

    # =========================================================================
    # Public Wrapper Methods
    # =========================================================================

    @classmethod
    async def confirm_order(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        unit_price: Optional[Decimal] = None,
        truck_id: Optional[UUID] = None,
        performed_by: str = "ADMIN",
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Transition order to confirmed and freeze pricing contract."""
        data = dict(payload or {})
        if unit_price is not None:
            data["unit_price"] = str(unit_price)
        if truck_id is not None:
            data["truck_id"] = truck_id
        return await cls._execute_transition(
            db=db,
            tenant_id=tenant_id,
            order=order,
            target_status="confirmed",
            performed_by=performed_by,
            reason=reason,
            payload=data,
        )

    @classmethod
    async def load_order(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        truck_id: Optional[UUID] = None,
        performed_by: str = "ADMIN",
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Transition order to loaded onto assigned delivery truck."""
        data = dict(payload or {})
        if truck_id is not None:
            data["truck_id"] = truck_id
        return await cls._execute_transition(
            db=db,
            tenant_id=tenant_id,
            order=order,
            target_status="loaded",
            performed_by=performed_by,
            reason=reason,
            payload=data,
        )

    @classmethod
    async def dispatch_order(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        driver_phone: Optional[str] = None,
        driver_name: Optional[str] = None,
        dispatch_time: Optional[datetime] = None,
        performed_by: str = "ADMIN",
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Transition order to out_for_delivery and record dispatch metadata."""
        data = dict(payload or {})
        if driver_phone is not None:
            data["driver_phone"] = driver_phone
        if driver_name is not None:
            data["driver_name"] = driver_name
        if dispatch_time is not None:
            data["dispatch_time"] = dispatch_time
        return await cls._execute_transition(
            db=db,
            tenant_id=tenant_id,
            order=order,
            target_status="out_for_delivery",
            performed_by=performed_by,
            reason=reason,
            payload=data,
        )

    @classmethod
    async def deliver_order(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        actual_delivered_kg: Optional[Decimal] = None,
        waste_kg: Decimal = Decimal("0.00"),
        payment_collected_inr: Decimal = Decimal("0.00"),
        performed_by: str = "ADMIN",
        reason: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Transition order to delivered with actual accepted weight and waste."""
        data = dict(payload or {})
        if actual_delivered_kg is not None:
            data["actual_delivered_kg"] = str(actual_delivered_kg)
        elif "actual_delivered_kg" not in data:
            data["actual_delivered_kg"] = str(order.quantity_kg)
        if waste_kg != Decimal("0.00") or "waste_kg" not in data:
            data["waste_kg"] = str(waste_kg)
        data["payment_collected_inr"] = str(payment_collected_inr)
        return await cls._execute_transition(
            db=db,
            tenant_id=tenant_id,
            order=order,
            target_status="delivered",
            performed_by=performed_by,
            reason=reason,
            payload=data,
        )

    @classmethod
    async def cancel_order(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        order: Order,
        reason: str,
        performed_by: str = "ADMIN",
        payload: Optional[Dict[str, Any]] = None,
    ) -> OrderTransitionResult:
        """Transition order to cancelled."""
        return await cls._execute_transition(
            db=db,
            tenant_id=tenant_id,
            order=order,
            target_status="cancelled",
            performed_by=performed_by,
            reason=reason,
            payload=payload,
        )
