"""Pydantic schemas for the Khata (digital credit ledger)."""

import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class KhataTransactionCreate(BaseModel):
    """Payload to record a new Khata entry (charge, payment, or adjustment).

    Note: ``tenant_id`` is NOT accepted here — it is derived server-side
    from the authenticated session via ``Depends(get_current_tenant)``.
    """

    retailer_id: uuid.UUID
    order_id: uuid.UUID | None = None
    type: str = Field(..., pattern="^(charge|payment|adjustment)$")
    amount: Decimal = Field(..., gt=0)
    reference_note: str | None = None


class KhataTransactionOut(BaseModel):
    """Serialized Khata transaction for API response."""

    id: uuid.UUID
    type: str
    amount: Decimal
    balance_after: Decimal
    reference_note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class KhataBalanceResponse(BaseModel):
    """Current balance summary for a retailer."""

    retailer_id: uuid.UUID
    retailer_name: str
    current_balance: Decimal
    last_transaction_at: datetime | None
