import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import AsyncSessionLocal
from sqlalchemy import text

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id, name FROM tenants LIMIT 1"))
        tenant = res.fetchone()
        if tenant:
            print(f"Tenant ID: {tenant[0]}")
        else:
            print("No tenants found!")

if __name__ == "__main__":
    asyncio.run(check())
