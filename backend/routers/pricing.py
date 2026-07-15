"""Router for Management Dashboard Pricing Controls.

Allows admins to view and dynamically update poultry rates without editing `.env`
or restarting the server. Changes take effect immediately in WhatsApp auto-replies.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.database import get_db
from core.auth import get_current_tenant
from core.pricing_service import get_all_prices, update_price
from models.pricing import ProductPrice
from schemas.pricing import PriceUpdate, PriceResponse

router = APIRouter(
    prefix="/api/v1/pricing",
    tags=["Pricing Management"]
)


@router.get("/", response_model=List[PriceResponse])
async def get_prices(
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Fetch current prices for all product types.
    
    If database table is empty, it automatically seeds default prices from `.env`.
    """
    prices_map = await get_all_prices(db)
    
    # Query actual DB objects to get updated_at timestamps if available
    result = await db.execute(select(ProductPrice))
    db_items = {item.item_type: item for item in result.scalars().all()}
    
    response = []
    for item_type, price_val in prices_map.items():
        db_item = db_items.get(item_type)
        response.append(
            PriceResponse(
                item_type=item_type,
                price_per_kg=float(price_val),
                updated_at=db_item.updated_at if db_item else datetime.now(timezone.utc)
            )
        )
    return response


@router.api_route("/resolve", methods=["GET", "POST"])
async def resolve_pricing(
    product: str = "Live Bird",
    quantity: float = 1.0,
    db: AsyncSession = Depends(get_db)
):
    """Resolve current price for a product and compute wholesale total for WhatsApp/n8n."""
    prices_map = await get_all_prices(db)
    
    # Normalize product name mapping
    prod_lower = str(product).lower()
    item_type = "Live Bird"
    if "dress" in prod_lower:
        item_type = "Dressed"
    elif "skinless" in prod_lower:
        item_type = "Skinless"
    elif "live" in prod_lower or "bird" in prod_lower or "chicken" in prod_lower:
        item_type = "Live Bird"
    elif product in prices_map:
        item_type = product

    unit_price = float(prices_map.get(item_type, 180.0))
    qty = float(quantity) if quantity and float(quantity) > 0 else 1.0
    total = round(unit_price * qty, 2)

    return {
        "product": item_type,
        "quantity": qty,
        "unit": "kg",
        "unit_price": unit_price,
        "currency": "₹",
        "total": total
    }


@router.put("/{item_type}", response_model=PriceResponse)
async def set_price(
    item_type: str, 
    payload: PriceUpdate, 
    tenant_id: str = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db)
):
    """Update price per kg for a specific product item type (e.g. 'Live Bird', 'Dressed', 'Skinless')."""
    valid_items = {"Live Bird", "Dressed", "Skinless"}
    if item_type not in valid_items:
        # We allow custom items too if needed, but let's format cleanly
        pass

    updated_obj = await update_price(db, item_type=item_type, new_price=Decimal(str(payload.price_per_kg)))
    return PriceResponse(
        item_type=updated_obj.item_type,
        price_per_kg=float(updated_obj.price_per_kg),
        updated_at=updated_obj.updated_at
    )
