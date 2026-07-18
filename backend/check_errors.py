import asyncio
import sys
import os
import uuid
from decimal import Decimal

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import select
from models.user import User
from models.khata import KhataLedger
from models.pricing import PriceBook

async def run():
    async with AsyncSessionLocal() as session:
        # 1. Find the pending user
        result = await session.execute(select(User).where(User.onboarding_status == "PENDING_APPROVAL"))
        user = result.scalars().first()
        if not user:
            print("No pending user found.")
            return

        print(f"Found pending user: {user.id}")
        
        try:
            # Code from approve route
            user.onboarding_status = "ACTIVE"
            user.zone = "North"
            
            khata = KhataLedger(
                tenant_id=user.tenant_id,
                customer_id=user.id,
                credit_limit=Decimal("50000"),
                balance=0
            )
            session.add(khata)
            
            book_res = await session.execute(select(PriceBook).where(PriceBook.tenant_id == user.tenant_id).limit(1))
            book = book_res.scalar_one_or_none()
            
            await session.commit()
            print("Approval succeeded locally!")
        except Exception as e:
            await session.rollback()
            print(f"Exception caught: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run())
