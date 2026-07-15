"""PR 7 Core Financial Ledger Engine — Append-Only KhataService with FIFO Allocation & Rebuildable Projections."""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models.khata import KhataLedger, CustomerBalanceProjection, KhataInvoice

logger = logging.getLogger("gochicken.khata_service")


class KhataService:
    """Core financial accounting service enforcing strict Decimal precision, append-only ledger entries, and FIFO payment settlement."""

    @classmethod
    def _assert_decimal(cls, val: Decimal, name: str = "amount") -> None:
        if not isinstance(val, Decimal):
            raise TypeError(f"{name} must be a Decimal instance to guarantee financial precision, got {type(val)}")

    @classmethod
    async def get_entry_by_idempotency_key(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        idempotency_key: str,
    ) -> Optional[KhataLedger]:
        """Look up an existing ledger entry by idempotency key."""
        stmt = select(KhataLedger).where(
            KhataLedger.tenant_id == tenant_id,
            KhataLedger.idempotency_key == idempotency_key,
        )
        result = await db.execute(stmt)
        return result.scalars().first()

    @classmethod
    async def _update_balance_projection(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        delta_amount: Decimal,
        entry_timestamp: datetime,
    ) -> CustomerBalanceProjection:
        """Synchronously update or create the read-optimized CustomerBalanceProjection."""
        cls._assert_decimal(delta_amount, "delta_amount")
        stmt = (
            select(CustomerBalanceProjection)
            .where(
                CustomerBalanceProjection.tenant_id == tenant_id,
                CustomerBalanceProjection.customer_id == customer_id,
            )
            .with_for_update()
        )
        result = await db.execute(stmt)
        projection = result.scalars().first()

        if not projection:
            projection = CustomerBalanceProjection(
                tenant_id=tenant_id,
                customer_id=customer_id,
                outstanding_balance=Decimal("0.00"),
                last_entry_at=entry_timestamp,
                updated_at=datetime.now(timezone.utc),
            )
            db.add(projection)

        projection.outstanding_balance += delta_amount
        projection.last_entry_at = entry_timestamp
        projection.updated_at = datetime.now(timezone.utc)
        return projection

    @classmethod
    async def post_entry(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        entry_type: str,
        amount: Decimal,
        reference_type: str,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Append an immutable ledger entry and synchronously update customer balance projection."""
        cls._assert_decimal(amount, "amount")

        # Idempotency check
        existing = await cls.get_entry_by_idempotency_key(db, tenant_id, idempotency_key)
        if existing:
            logger.info(
                f"[KHATA IDEMPOTENT] Duplicate ledger posting attempt {idempotency_key} ignored. Returning existing entry."
            )
            return existing

        now = datetime.now(timezone.utc)
        entry = KhataLedger(
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type=entry_type.upper(),
            amount=amount,
            reference_type=reference_type.upper(),
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            created_at=now,
        )
        db.add(entry)

        await cls._update_balance_projection(db, tenant_id, customer_id, amount, now)

        if commit:
            await db.commit()
            await db.refresh(entry)

        return entry

    @classmethod
    async def post_invoice(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        invoice_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Record a new invoice debit entry and create an unsettled KhataInvoice record."""
        cls._assert_decimal(amount, "amount")
        if amount <= Decimal("0.00"):
            raise ValueError("Invoice amount must be strictly positive.")

        existing = await cls.get_entry_by_idempotency_key(db, tenant_id, idempotency_key)
        if existing:
            return existing

        # Ensure invoice settlement tracker exists
        stmt = select(KhataInvoice).where(
            KhataInvoice.tenant_id == tenant_id,
            KhataInvoice.invoice_id == invoice_id,
        )
        result = await db.execute(stmt)
        invoice_record = result.scalars().first()

        if not invoice_record:
            invoice_record = KhataInvoice(
                tenant_id=tenant_id,
                customer_id=customer_id,
                invoice_id=invoice_id,
                total_amount=amount,
                settled_amount=Decimal("0.00"),
                status="UNPAID",
                issued_at=datetime.now(timezone.utc),
            )
            db.add(invoice_record)

        entry = await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="INVOICE",
            amount=amount,  # + signed balance increase
            reference_type="INVOICE",
            reference_id=str(invoice_id),
            idempotency_key=idempotency_key,
            notes=notes,
            commit=commit,
        )
        return entry

    @classmethod
    async def post_payment_fifo(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        payment_amount: Decimal,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Record a payment credit entry and allocate settlement across oldest unpaid invoices first (FIFO)."""
        cls._assert_decimal(payment_amount, "payment_amount")
        if payment_amount <= Decimal("0.00"):
            raise ValueError("Payment amount must be strictly positive.")

        existing = await cls.get_entry_by_idempotency_key(db, tenant_id, idempotency_key)
        if existing:
            return existing

        # Append PAYMENT ledger entry (- signed balance reduction)
        entry = await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="PAYMENT",
            amount=-payment_amount,
            reference_type="PAYMENT",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            commit=False,
        )

        # FIFO invoice settlement allocation
        stmt = (
            select(KhataInvoice)
            .where(
                KhataInvoice.tenant_id == tenant_id,
                KhataInvoice.customer_id == customer_id,
                KhataInvoice.status != "PAID",
            )
            .order_by(KhataInvoice.issued_at.asc())
            .with_for_update()
        )
        result = await db.execute(stmt)
        unpaid_invoices = list(result.scalars().all())

        remaining_funds = payment_amount
        for inv in unpaid_invoices:
            if remaining_funds <= Decimal("0.00"):
                break

            unsettled = inv.total_amount - inv.settled_amount
            if remaining_funds >= unsettled:
                inv.settled_amount = inv.total_amount
                inv.status = "PAID"
                remaining_funds -= unsettled
            else:
                inv.settled_amount += remaining_funds
                inv.status = "PARTIALLY_PAID"
                remaining_funds = Decimal("0.00")

        if commit:
            await db.commit()
            await db.refresh(entry)

        return entry

    @classmethod
    async def post_credit_note(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Post a CREDIT_NOTE reducing outstanding balance (- signed amount)."""
        cls._assert_decimal(amount, "amount")
        if amount <= Decimal("0.00"):
            raise ValueError("Credit note amount must be strictly positive.")

        return await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="CREDIT_NOTE",
            amount=-amount,
            reference_type="RETURN",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            commit=commit,
        )

    @classmethod
    async def post_debit_note(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        amount: Decimal,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Post a DEBIT_NOTE increasing outstanding balance (+ signed amount)."""
        cls._assert_decimal(amount, "amount")
        if amount <= Decimal("0.00"):
            raise ValueError("Debit note amount must be strictly positive.")

        return await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="DEBIT_NOTE",
            amount=amount,
            reference_type="ADJUSTMENT",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            commit=commit,
        )

    @classmethod
    async def post_adjustment(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        signed_amount: Decimal,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Post a signed adjustment entry (+/- signed amount)."""
        cls._assert_decimal(signed_amount, "signed_amount")
        return await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="ADJUSTMENT",
            amount=signed_amount,
            reference_type="ADJUSTMENT",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            commit=commit,
        )

    @classmethod
    async def post_reversal(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        signed_amount: Decimal,
        idempotency_key: str,
        reference_id: Optional[str] = None,
        notes: Optional[str] = None,
        commit: bool = False,
    ) -> KhataLedger:
        """Post a non-destructive reversal entry (+/- signed amount)."""
        cls._assert_decimal(signed_amount, "signed_amount")
        return await cls.post_entry(
            db=db,
            tenant_id=tenant_id,
            customer_id=customer_id,
            entry_type="REVERSAL",
            amount=signed_amount,
            reference_type="PAYMENT",
            reference_id=reference_id,
            idempotency_key=idempotency_key,
            notes=notes,
            commit=commit,
        )

    @classmethod
    async def rebuild_projection(
        cls,
        db: AsyncSession,
        tenant_id: UUID,
        customer_id: UUID,
        commit: bool = True,
    ) -> CustomerBalanceProjection:
        """Deterministically rebuild CustomerBalanceProjection from immutable KhataLedger entries."""
        stmt = select(func.sum(KhataLedger.amount)).where(
            KhataLedger.tenant_id == tenant_id,
            KhataLedger.customer_id == customer_id,
        )
        result = await db.execute(stmt)
        total_balance = result.scalar() or Decimal("0.00")

        proj_stmt = select(CustomerBalanceProjection).where(
            CustomerBalanceProjection.tenant_id == tenant_id,
            CustomerBalanceProjection.customer_id == customer_id,
        )
        proj_res = await db.execute(proj_stmt)
        projection = proj_res.scalars().first()

        now = datetime.now(timezone.utc)
        if not projection:
            projection = CustomerBalanceProjection(
                tenant_id=tenant_id,
                customer_id=customer_id,
                outstanding_balance=total_balance,
                last_entry_at=now,
                updated_at=now,
            )
            db.add(projection)
        else:
            projection.outstanding_balance = total_balance
            projection.updated_at = now

        if commit:
            await db.commit()
            await db.refresh(projection)

        return projection
