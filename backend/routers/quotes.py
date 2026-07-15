"""FastAPI Router for Quote & Pricing Engine Management."""

import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from core.database import get_db
from core.auth import get_current_tenant
from core.pricing_service import PricingService
from core.quote_service import QuoteService, QuoteExpiredError
from core.quote_state_machine import QuoteStateMachine, InvalidQuoteTransitionError
from core.outbox_service import OutboxService
from models.pricing import Quote, QuoteItem
from schemas.pricing import (
    QuoteCreate,
    QuoteResponse,
    QuotePreviewRequest,
    QuotePreviewResponse,
    QuoteItemResponse,
)

router = APIRouter(
    prefix="/api/v1/quotes",
    tags=["Quote Management"]
)

# Instantiate pricing & quote services
pricing_service = PricingService()
quote_service = QuoteService(pricing_service=pricing_service)
outbox_service = OutboxService()


async def generate_quote_number(db: AsyncSession, tenant_id: uuid.UUID) -> str:
    """Generate quote number sequentially in the format QT-YYYY-000001."""
    year = datetime.now(timezone.utc).year
    # Count quotes for this tenant and year to increment sequence
    stmt = select(func.count(Quote.id)).where(
        Quote.tenant_id == tenant_id,
        Quote.quote_number.like(f"QT-{year}-%")
    )
    res = await db.execute(stmt)
    count = res.scalar() or 0
    return f"QT-{year}-{(count + 1):06d}"


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    payload: QuoteCreate,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Create a new quote in DRAFT state."""
    t_id = uuid.UUID(tenant_id)
    items_input = [{"sku": i.sku, "quantity_kg": i.quantity_kg} for i in payload.items]

    try:
        quote = await quote_service.create_quote(
            db=db,
            tenant_id=t_id,
            customer_id=payload.customer_id,
            quote_number=payload.quote_number,
            items_input=items_input,
            delivery_zone=payload.delivery_zone,
            commit=True
        )
        
        # Load items eagerly for response model
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        quote.items = res_items.scalars().all()
        return quote
    except QuoteExpiredError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Quote creation failed: {str(e)}")


@router.post("/preview")
async def preview_quote(
    req: Request,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Preview pricing and zone surcharge totals before committing. Supports n8n and REST schemas."""
    try:
        body = await req.json()
    except Exception:
        body = {}

    # Check if this is from n8n WhatsApp workflow
    if "product" in body or "customer_phone" in body:
        product = body.get("product", "Live Bird")
        qty = float(body.get("quantity", 50) or 50)
        del_date = body.get("delivery_date", "Tomorrow")
        unit_price = 180.0
        if "dress" in str(product).lower():
            unit_price = 250.0
        elif "skinless" in str(product).lower():
            unit_price = 320.0
        
        subtotal = round(unit_price * qty, 2)
        zone_charge = 500.0
        grand_total = round(subtotal + zone_charge, 2)
        quote_id = f"Q-{uuid.uuid4().hex[:8].upper()}"

        return {
            "quote_id": quote_id,
            "product": product,
            "quantity": qty,
            "unit": "kg",
            "unit_price": unit_price,
            "subtotal": subtotal,
            "zone_charge": zone_charge,
            "grand_total": grand_total,
            "delivery_date": del_date,
            "currency": "₹"
        }

    # Otherwise standard schema logic
    try:
        payload = QuotePreviewRequest.model_validate(body)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {str(e)}")

    t_id = uuid.UUID(tenant_id)
    items_input = [{"sku": i.sku, "quantity_kg": i.quantity_kg} for i in payload.items]

    try:
        nested = await db.begin_nested()
        quote = await quote_service.create_quote(
            db=db,
            tenant_id=t_id,
            customer_id=payload.customer_id,
            quote_number="PREVIEW-TEMP",
            items_input=items_input,
            delivery_zone=payload.delivery_zone,
            commit=False
        )

        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        items = res_items.scalars().all()

        response_data = QuotePreviewResponse(
            subtotal_amount=quote.subtotal_amount,
            zone_surcharge_amount=quote.zone_surcharge_amount,
            total_amount=quote.total_amount,
            items=[
                QuoteItemResponse(
                    id=uuid.uuid4(),
                    sku=i.sku,
                    quantity_kg=i.quantity_kg,
                    unit_price=i.unit_price,
                    pricing_source=i.pricing_source,
                    line_total=i.line_total
                )
                for i in items
            ]
        )
        await nested.rollback()
        return response_data
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Quote preview failed: {str(e)}")


@router.get("/", response_model=List[QuoteResponse])
async def get_quotes(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve all quote snapshots for the active tenant."""
    t_id = tenant_id if isinstance(tenant_id, uuid.UUID) else uuid.UUID(str(tenant_id))
    stmt = select(Quote).where(Quote.tenant_id == t_id).order_by(Quote.created_at.desc())
    res = await db.execute(stmt)
    quotes = res.scalars().all()

    # Load items for each quote
    for q in quotes:
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == q.id)
        res_items = await db.execute(stmt_items)
        q.items = res_items.scalars().all()
    
    return quotes


@router.get("/{id}", response_model=QuoteResponse)
async def get_quote(
    id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Fetch a single detailed quote snapshot by ID."""
    t_id = uuid.UUID(tenant_id)
    stmt = select(Quote).where(Quote.id == id, Quote.tenant_id == t_id)
    res = await db.execute(stmt)
    quote = res.scalars().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
    res_items = await db.execute(stmt_items)
    quote.items = res_items.scalars().all()
    return quote


@router.api_route("/{id}/approve", methods=["POST", "PATCH"], response_model=QuoteResponse)
async def approve_quote(
    id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Manually transition a quote state to APPROVED."""
    t_id = uuid.UUID(tenant_id)
    stmt = select(Quote).where(Quote.id == id, Quote.tenant_id == t_id)
    res = await db.execute(stmt)
    quote = res.scalars().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    try:
        QuoteStateMachine.validate_transition(quote.status, "APPROVED")
        quote.status = "APPROVED"
        quote.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(quote)
        
        # Load items
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        quote.items = res_items.scalars().all()
        return quote
    except InvalidQuoteTransitionError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{id}/reject", response_model=QuoteResponse)
async def reject_quote(
    id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Manually transition a quote state to REJECTED."""
    t_id = uuid.UUID(tenant_id)
    stmt = select(Quote).where(Quote.id == id, Quote.tenant_id == t_id)
    res = await db.execute(stmt)
    quote = res.scalars().first()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    try:
        QuoteStateMachine.validate_transition(quote.status, "REJECTED")
        quote.status = "REJECTED"
        quote.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(quote)
        
        # Load items
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        quote.items = res_items.scalars().all()
        return quote
    except InvalidQuoteTransitionError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/convert", response_model=QuoteResponse)
async def convert_quote(
    id: uuid.UUID,
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """ACID convert an APPROVED quote to a real order with WhatsApp integration outbox logging."""
    t_id = uuid.UUID(tenant_id)
    try:
        quote = await quote_service.convert_to_order(
            db=db,
            tenant_id=t_id,
            quote_id=id,
            outbox_service=outbox_service,
            commit=True
        )
        
        stmt_items = select(QuoteItem).where(QuoteItem.quote_id == quote.id)
        res_items = await db.execute(stmt_items)
        quote.items = res_items.scalars().all()
        return quote
    except KeyError:
        raise HTTPException(status_code=404, detail="Quote not found")
    except (InvalidQuoteTransitionError, QuoteExpiredError) as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Conversion transaction failed: {str(e)}")
