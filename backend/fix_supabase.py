import asyncio
import sys
import os
import uuid
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.database import AsyncSessionLocal
from sqlalchemy import text

async def fix_supabase():
    async with AsyncSessionLocal() as db:
        print("Connected to Supabase. Cleaning up old records...")
        
        # Delete any existing user rows with that phone number to avoid conflicts
        await db.execute(text("DELETE FROM users WHERE phone LIKE '%9908128167' OR whatsapp_id LIKE '%9908128167'"))
        
        # Get a tenant
        res = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        tenant = res.fetchone()
        
        if not tenant:
            print("No tenant found in Supabase! I need to create one first.")
            tenant_id = uuid.uuid4()
            await db.execute(text("INSERT INTO tenants (id, name, created_at) VALUES (:id, 'Default Wholesaler', NOW())"), {"id": tenant_id})
        else:
            tenant_id = tenant[0]
            
        print(f"Using tenant ID: {tenant_id}")
        
        # Insert the correct user
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
        print(f"Successfully inserted clean user record with ID {user_id} into Supabase!")

if __name__ == "__main__":
    asyncio.run(fix_supabase())
