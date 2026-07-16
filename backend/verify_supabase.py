import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import AsyncSessionLocal
from sqlalchemy import text

async def verify():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id, role, phone, whatsapp_id FROM users WHERE phone LIKE '%9908128167'"))
        users = res.fetchall()
        print("Users found in Supabase:")
        for u in users:
            print(u)

if __name__ == "__main__":
    asyncio.run(verify())
