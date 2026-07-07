import asyncio
import asyncpg

import os

async def main():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:adminpassword@localhost:5435/go_chicken")
    conn = await asyncpg.connect(db_url)
    version = await conn.fetchval('SELECT version()')
    print('DB Connection successful. PG Version:', version)
    await conn.close()

asyncio.run(main())
