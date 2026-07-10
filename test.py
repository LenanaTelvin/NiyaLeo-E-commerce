import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def test():
    engine = create_async_engine("postgresql+asyncpg://postgres.chlzdapvkbvpturuymkb:lena%4038luvsMusiq@aws-0-eu-central-1.pooler.supabase.com:5432/postgres")
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        print(result.scalar())

asyncio.run(test())