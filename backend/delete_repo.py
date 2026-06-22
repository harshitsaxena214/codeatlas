import asyncio
import uuid
from sqlalchemy import delete
from app.database import async_session_factory
from app.models.ingestion_job import IngestionJob
from app.models.repository import Repository

async def main():
    repo_id = uuid.UUID("2b0a28a5-3b92-442d-b260-a008a0776925")
    async with async_session_factory() as db:
        await db.execute(delete(IngestionJob).where(IngestionJob.repository_id == repo_id))
        await db.execute(delete(Repository).where(Repository.id == repo_id))
        await db.commit()
    print("Deleted successfully!")

if __name__ == "__main__":
    asyncio.run(main())
