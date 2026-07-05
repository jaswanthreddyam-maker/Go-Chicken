import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:adminpassword@localhost:5435/go_chicken')
    version = await conn.fetchval('SELECT version()')
    print('DB Connection successful. PG Version:', version)
    await conn.close()

asyncio.run(main())
