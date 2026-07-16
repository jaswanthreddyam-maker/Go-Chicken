import asyncio
import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import AsyncSessionLocal
from sqlalchemy import text

async def insert():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant = res.fetchone()
        if not tenant:
            print("No tenant found!")
            return
            
        tenant_id = tenant[0]
        user_id = uuid.uuid4()
        
        await db.execute(
            text("""
                INSERT INTO users 
                (id, tenant_id, role, name, phone, whatsapp_id, created_at) 
                VALUES (:id, :tenant_id, 'retailer', 'Jaswanth Reddy', '919908128167', '919908128167', NOW())
            """),
            {"id": user_id, "tenant_id": tenant_id}
        )
        await db.commit()
        print(f"Successfully inserted user Jaswanth Reddy with ID {user_id}")

if __name__ == "__main__":
    asyncio.run(insert())
