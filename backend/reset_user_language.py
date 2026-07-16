import asyncio
import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import select, update
from models.user import User
from models.conversation_state import ConversationState

async def reset_user(phone_number):
    async with AsyncSessionLocal() as session:
        # Raw SQL to bypass any model schema mismatches
        from sqlalchemy import text
        
        # 1. Get user id
        result = await session.execute(
            text("SELECT id, name, phone FROM users WHERE phone LIKE :phone"),
            {"phone": f"%{phone_number}"}
        )
        user = result.fetchone()
        
        if not user:
            print(f"User with phone ending in {phone_number} not found.")
            return

        user_id, name, phone = user
        print(f"Found user: {name} ({phone}), id: {user_id}")

        # 2. Reset user language
        await session.execute(
            text("UPDATE users SET preferred_language = NULL WHERE id = :id"),
            {"id": user_id}
        )
        
        # 3. Reset conversation state
        await session.execute(
            text("UPDATE conversation_state SET language = NULL, state = 'IDLE' WHERE user_id = :id"),
            {"id": user_id}
        )
        
        await session.commit()
        print("Successfully reset language and conversation state.")

if __name__ == "__main__":
    asyncio.run(reset_user("9908128167"))
