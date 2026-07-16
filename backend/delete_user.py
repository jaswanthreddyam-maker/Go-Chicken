import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import text

async def delete_user(phone_number):
    async with AsyncSessionLocal() as session:
        # Get user id
        result = await session.execute(
            text("SELECT id, name, phone FROM users WHERE phone LIKE :phone"),
            {"phone": f"%{phone_number}"}
        )
        user = result.fetchone()
        
        if not user:
            print(f"User with phone ending in {phone_number} not found.")
            return

        user_id, name, phone = user
        print(f"Found user: {name} ({phone}), id: {user_id}. Proceeding to delete...")

        # Delete user. Related tables like conversation_state should cascade if configured,
        # but just in case, let's explicitly delete conversation_state first.
        await session.execute(
            text("DELETE FROM conversation_state WHERE user_id = :id"),
            {"id": user_id}
        )
        
        await session.execute(
            text("DELETE FROM users WHERE id = :id"),
            {"id": user_id}
        )
        
        await session.commit()
        print("Successfully deleted user and conversation state.")

if __name__ == "__main__":
    asyncio.run(delete_user("9908128167"))
