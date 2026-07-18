import asyncio
import uuid
from core.database import AsyncSessionLocal
from sqlalchemy import select
from models.user import User
from models.khata import CustomerBalanceProjection
from models.communication import ConversationState

async def main():
    async with AsyncSessionLocal() as db:
        user_id = uuid.UUID("2a817ac0-adca-4ce6-b851-363db207b1b6")
        
        # Look for user
        result = await db.execute(select(User).where(User.id == user_id, User.onboarding_status == "PENDING_APPROVAL"))
        user = result.scalar_one_or_none()
        if not user:
            print("User not found or not pending!")
            return
            
        print("User found!")
        
        # Test CustomerBalanceProjection query
        try:
            existing_khata = await db.execute(select(CustomerBalanceProjection).where(
                CustomerBalanceProjection.tenant_id == user.tenant_id,
                CustomerBalanceProjection.customer_id == user.id
            ))
            existing_khata.scalar_one_or_none()
            print("CustomerBalanceProjection check passed.")
        except Exception as e:
            print(f"CustomerBalanceProjection check failed: {e}")
            
        # Test ConversationState query
        try:
            state_res = await db.execute(select(ConversationState).where(ConversationState.phone_number == user.phone))
            state_res.scalars().first()
            print("ConversationState check passed.")
        except Exception as e:
            print(f"ConversationState check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
