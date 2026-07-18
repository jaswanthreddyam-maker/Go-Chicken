import asyncio
from core.database import AsyncSessionLocal
from models.pricing import PriceBookEntry
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(PriceBookEntry.sku, PriceBookEntry.base_unit_price))
        print(res.all())

if __name__ == "__main__":
    asyncio.run(main())
