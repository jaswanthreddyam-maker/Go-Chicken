import asyncio
from core.database import AsyncSessionLocal
from models.user import User
from models.profile import BusinessProfile
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User.phone, User.role))
        print("Users:", res.all())
        res2 = await db.execute(select(BusinessProfile.contact_number, BusinessProfile.business_name))
        print("Profiles:", res2.all())

if __name__ == "__main__":
    asyncio.run(main())
