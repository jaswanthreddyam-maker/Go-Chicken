import asyncio
from sqlalchemy import select
from core.database import AsyncSessionLocal
from models.user import User
from models.tenant import Tenant
from models.inventory import InventoryItem

async def main():
    async with AsyncSessionLocal() as session:
        users = await session.execute(select(User))
        for u in users.scalars():
            print(f"User: id={u.id}, name={u.name}, phone={u.phone}, email={u.email}, tenant={u.tenant_id}")
            
        items = await session.execute(select(InventoryItem))
        for i in items.scalars():
            print(f"Item: tenant={i.tenant_id}, type={i.item_type}, qty={i.available_qty}")

if __name__ == "__main__":
    asyncio.run(main())
