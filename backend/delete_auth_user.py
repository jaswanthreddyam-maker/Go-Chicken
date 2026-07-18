import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import text

async def delete_auth_user(phone_number):
    async with AsyncSessionLocal() as session:
        try:
            # Delete from auth.users (Supabase internal table)
            res = await session.execute(
                text("DELETE FROM auth.users WHERE phone LIKE :phone RETURNING id, phone"),
                {"phone": f"%{phone_number}"}
            )
            deleted = res.fetchall()
            print(f"Deleted {len(deleted)} auth.users rows for phone {phone_number}.")
            for row in deleted:
                print(f" - ID: {row[0]}, Phone: {row[1]}")
            await session.commit()
        except Exception as e:
            print("Failed to delete from auth.users (you might lack permissions on the auth schema):", str(e))

if __name__ == "__main__":
    asyncio.run(delete_auth_user("9908128167"))
