import asyncio, asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:adminpassword@localhost:5435/go_chicken')
    rows = await conn.fetch('SELECT * FROM error_logs ORDER BY created_at DESC LIMIT 3;')
    for row in rows:
        print(dict(row))
    await conn.close()
asyncio.run(main())
