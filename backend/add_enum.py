import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine
from app.config import get_settings

settings = get_settings()

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        try:
            await conn.execute(sa.text("ALTER TYPE ingestionstep ADD VALUE 'RELEASES'"))
            print("Enum RELEASES added successfully")
        except Exception as e:
            print("Error adding RELEASES:", e)

asyncio.run(main())
