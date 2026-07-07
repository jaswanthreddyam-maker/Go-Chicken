"""Khata Ledger Router — digital credit book for retailers."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.auth import get_current_tenant
from models.user import User
from models.khata import KhataTransaction, TransactionType
from schemas.khata import KhataTransactionCreate, KhataTransactionOut, KhataBalanceResponse

router = APIRouter()


from typing import List
from pydantic import BaseModel

class RetailerResponse(BaseModel):
    id: uuid.UUID
    name: str
    phone: str

@router.get(
    "/retailers",
    response_model=List[RetailerResponse],
    summary="Get all retailers for the current tenant"
)
async def get_retailers(
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    from models.user import UserRole
    result = await db.execute(
        select(User).where(User.tenant_id == tenant_id, User.role == UserRole.RETAILER)
    )
    return result.scalars().all()

@router.get(
    "/{retailer_id}/balance",
    response_model=KhataBalanceResponse,
    summary="Get the current Khata balance for a retailer",
)
async def get_balance(
    retailer_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Fetches the running balance from the most recent Khata transaction."""
    # 1. Fetch the retailer
    retailer = await db.get(User, retailer_id)
    if not retailer or retailer.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Retailer not found.")

    # 2. Get the latest transaction to read balance_after
    result = await db.execute(
        select(KhataTransaction)
        .where(KhataTransaction.retailer_id == retailer_id)
        .order_by(desc(KhataTransaction.created_at))
        .limit(1)
    )
    latest_txn = result.scalar_one_or_none()

    return KhataBalanceResponse(
        retailer_id=retailer.id,
        retailer_name=retailer.name,
        current_balance=latest_txn.balance_after if latest_txn else Decimal("0.00"),
        last_transaction_at=latest_txn.created_at if latest_txn else None,
    )


@router.post(
    "/transaction",
    response_model=KhataTransactionOut,
    summary="Record a new Khata transaction (charge, payment, or adjustment)",
)
async def create_transaction(
    payload: KhataTransactionCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """
    Records a new entry in the retailer's digital Khata.
    Automatically computes the new running balance:
      - 'charge' → increases the balance (retailer owes more)
      - 'payment' → decreases the balance (retailer paid)
      - 'adjustment' → can go either way (e.g., mortality credit)
    """
    # 1. Get current balance with row-level lock to prevent race conditions
    result = await db.execute(
        select(KhataTransaction)
        .where(KhataTransaction.retailer_id == payload.retailer_id)
        .order_by(desc(KhataTransaction.created_at))
        .limit(1)
        .with_for_update()
    )
    latest_txn = result.scalar_one_or_none()
    current_balance = latest_txn.balance_after if latest_txn else Decimal("0.00")

    # 2. Compute new balance
    txn_type = TransactionType(payload.type)
    if txn_type == TransactionType.CHARGE:
        new_balance = current_balance + payload.amount
    elif txn_type == TransactionType.PAYMENT:
        new_balance = current_balance - payload.amount
    else:  # ADJUSTMENT
        new_balance = current_balance - payload.amount  # Credits reduce balance

    # 3. Persist
    txn = KhataTransaction(
        tenant_id=tenant_id,  # server-derived, not from client body
        retailer_id=payload.retailer_id,
        order_id=payload.order_id,
        type=txn_type,
        amount=payload.amount,
        balance_after=new_balance,
        reference_note=payload.reference_note,
    )
    db.add(txn)
    await db.commit()
    await db.refresh(txn)

    return KhataTransactionOut(
        id=txn.id,
        type=txn.type.value,
        amount=txn.amount,
        balance_after=txn.balance_after,
        reference_note=txn.reference_note,
        created_at=txn.created_at,
    )
