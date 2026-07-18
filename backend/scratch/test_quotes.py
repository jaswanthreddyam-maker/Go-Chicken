import asyncio
import sys
import os
sys.path.append(os.getcwd())
from core.database import AsyncSessionLocal
from routers.quotes import get_quotes
import uuid
from sqlalchemy import text

async def test():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text('SELECT id FROM tenants LIMIT 1'))
        tenant_id = res.scalar()
        if not tenant_id:
            tenant_id = uuid.uuid4()
            print('No tenant found, using mock')
        
        try:
            quotes = await get_quotes(tenant_id=tenant_id, db=db)
            print(f'Got {len(quotes)} quotes')
            from schemas.pricing import QuoteResponse
            for q in quotes:
                resp = QuoteResponse.model_validate(q)
            print('Validation successful')
        except Exception as e:
            import traceback
            traceback.print_exc()

asyncio.run(test())
