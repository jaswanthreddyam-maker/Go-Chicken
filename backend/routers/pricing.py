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
from core.pricing_service import get_all_prices, update_price
from models.pricing import ProductPrice
from schemas.pricing import PriceUpdate, PriceResponse

router = APIRouter(
    prefix="/api/v1/pricing",
    tags=["Pricing Management"]
)


@router.get("/", response_model=List[PriceResponse])
async def get_prices(db: AsyncSession = Depends(get_db)):
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


@router.put("/{item_type}", response_model=PriceResponse)
async def set_price(item_type: str, payload: PriceUpdate, db: AsyncSession = Depends(get_db)):
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
