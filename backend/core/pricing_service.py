"""Service layer for dynamic pricing management.

Handles database lookups for product prices, seeding default prices from config
if the DB table is empty, and updating prices from the admin dashboard.
"""

import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config import get_settings
from models.pricing import ProductPrice

logger = logging.getLogger("go_chicken.pricing")
settings = get_settings()


def get_default_prices() -> dict[str, Decimal]:
    """Return default pricing from config/.env settings."""
    return {
        "Live Bird": Decimal(str(settings.PRICE_LIVE_BIRD)),
        "Dressed": Decimal(str(settings.PRICE_DRESSED)),
        "Skinless": Decimal(str(settings.PRICE_SKINLESS)),
    }


async def get_all_prices(db: AsyncSession) -> dict[str, Decimal]:
    """Fetch all product prices from the DB.
    
    If the table is empty, seeds it with default prices from config.
    """
    try:
        result = await db.execute(select(ProductPrice))
        rows = result.scalars().all()
        prices = {row.item_type: Decimal(str(row.price_per_kg)) for row in rows}

        defaults = get_default_prices()

        if not prices:
            logger.info("🌱 Seeding default product prices into DB from config...")
            for item_type, price in defaults.items():
                db.add(ProductPrice(item_type=item_type, price_per_kg=price))
            await db.commit()
            return defaults.copy()

        # Ensure any missing default product categories exist in the dict
        for item_type, default_price in defaults.items():
            if item_type not in prices:
                prices[item_type] = default_price

        return prices
    except Exception as e:
        logger.error(f"❌ Error fetching prices from DB, falling back to defaults: {e}")
        return get_default_prices()


async def get_price_for_item(db: AsyncSession, item_type: str) -> Decimal:
    """Fetch the current price per kg for a specific item type from DB."""
    prices = await get_all_prices(db)
    return prices.get(item_type, get_default_prices().get(item_type, Decimal(str(settings.PRICE_LIVE_BIRD))))


async def update_price(db: AsyncSession, item_type: str, new_price: Decimal) -> ProductPrice:
    """Update or insert the price for an item type in DB."""
    result = await db.execute(select(ProductPrice).where(ProductPrice.item_type == item_type))
    price_obj = result.scalar_one_or_none()

    if not price_obj:
        price_obj = ProductPrice(item_type=item_type, price_per_kg=new_price)
        db.add(price_obj)
        logger.info(f"💰 Created new product price: {item_type} = ₹{new_price}/kg")
    else:
        old_price = price_obj.price_per_kg
        price_obj.price_per_kg = new_price
        logger.info(f"💰 Updated price for {item_type}: ₹{old_price}/kg -> ₹{new_price}/kg")

    await db.commit()
    await db.refresh(price_obj)
    return price_obj
