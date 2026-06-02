import asyncio
import structlog
from app.db.session import AsyncSessionLocal
from app.db.repository import AsyncResumeRepository

logger = structlog.get_logger()

async def cleanup_expired_resumes():
    logger.info("Starting background cleanup of expired resumes...")
    try:
        async with AsyncSessionLocal() as session:
            repo = AsyncResumeRepository(session)
            deleted_count = await repo.delete_expired_resumes()
            logger.info("Background cleanup finished", deleted_count=deleted_count)
    except Exception as e:
        logger.error("Failed to cleanup resumes", error=str(e))
