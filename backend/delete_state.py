import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import text

async def remove_retailer(phone: str):
    async with AsyncSessionLocal() as session:
        # First, find the user in Postgres
        result = await session.execute(text("SELECT id, provider_user_id FROM users WHERE phone = :phone OR phone LIKE :like_phone"), {"phone": phone, "like_phone": f"%{phone}"})
        user = result.fetchone()
        
        if user:
            user_id = user.id
            provider_user_id = user.provider_user_id
            print(f"Found user in DB: ID={user_id}, Provider ID={provider_user_id}")
            
            # Delete related records from Postgres
            print("Deleting related records...")
            try:
                await session.execute(text("DELETE FROM whatsapp_states WHERE user_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            try:
                await session.execute(text("DELETE FROM khata_ledgers WHERE retailer_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            try:
                await session.execute(text("DELETE FROM quotes WHERE retailer_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            try:
                await session.execute(text("DELETE FROM orders WHERE user_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            try:
                await session.execute(text("DELETE FROM ai_forecasts WHERE user_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            # Try to delete conversation_state
            try:
                await session.execute(text("DELETE FROM conversation_state WHERE user_id = :uid"), {"uid": user_id})
                await session.commit()
            except Exception: await session.rollback()
            
            # Try by phone in conversation_state
            try:
                await session.execute(text("DELETE FROM conversation_state WHERE phone_number LIKE :phone"), {"phone": f"%{phone}%"})
                await session.commit()
            except Exception: await session.rollback()
            
            # Delete user from Postgres
            print("Deleting user from Postgres...")
            await session.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": user_id})
            await session.commit()
            print("Successfully deleted from Postgres database.")
        else:
            print(f"User with phone {phone} not found in Postgres.")
            
            # Try by phone in conversation_state
            try:
                await session.execute(text("DELETE FROM conversation_state WHERE phone_number LIKE :phone"), {"phone": f"%{phone}%"})
                await session.commit()
            except Exception:
                pass
            
        # Delete from Supabase Auth
        try:
            print("Attempting to delete from auth.users...")
            res = await session.execute(text("DELETE FROM auth.users WHERE phone LIKE :phone RETURNING id, phone"), {"phone": f"%{phone}%"})
            deleted = res.fetchall()
            print(f"Deleted {len(deleted)} auth.users rows for phone {phone}.")
            for row in deleted:
                print(f" - ID: {row[0]}, Phone: {row[1]}")
            await session.commit()
        except Exception as e:
            print(f"Failed to delete from auth.users: {e}")

if __name__ == "__main__":
    asyncio.run(remove_retailer("9908128167"))
