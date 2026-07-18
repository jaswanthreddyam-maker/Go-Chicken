import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import AsyncSessionLocal
from sqlalchemy import text

async def run():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT id, invite_code, status, expires_at FROM retailer_invitations WHERE invite_code = 'M02A7257ECD05F057E'"))
        print(res.fetchall())

if __name__ == "__main__":
    asyncio.run(run())
