import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings

settings = get_settings()

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        try:
            res = await conn.execute(sa.text("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'ingestionstep'"))
            labels = [r[0] for r in res.fetchall()]
            print("Enum labels:", labels)
        except Exception as e:
            print('Error:', e)

asyncio.run(main())
