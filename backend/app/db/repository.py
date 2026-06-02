from typing import Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Resume, Score

class ResumeNotFoundError(Exception):
    pass

class AsyncResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_resume(self, data: dict) -> Resume:
        resume = Resume(**data)
        if not resume.expires_at:
            resume.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def get_resume(self, id: str) -> Resume | None:
        result = await self.session.execute(select(Resume).where(Resume.id == id))
        resume = result.scalar_one_or_none()
        if not resume:
            raise ResumeNotFoundError(f"Resume {id} not found")
        return resume

    async def update_sections(self, id: str, sections: dict, ats_flags: dict) -> Resume:
        resume = await self.get_resume(id)
        resume.sections = sections
        resume.ats_flags = ats_flags
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def create_score(self, data: dict) -> Score:
        score = Score(**data)
        self.session.add(score)
        await self.session.commit()
        await self.session.refresh(score)
        return score

    async def get_latest_score(self, resume_id: str) -> Score | None:
        result = await self.session.execute(
            select(Score).where(Score.resume_id == resume_id).order_by(Score.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_score_history(self, resume_id: str, limit: int = 10) -> list[Score]:
        result = await self.session.execute(
            select(Score).where(Score.resume_id == resume_id).order_by(Score.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def delete_resume(self, id: str) -> bool:
        result = await self.session.execute(delete(Resume).where(Resume.id == id))
        await self.session.commit()
        return result.rowcount > 0

    async def delete_expired_resumes(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            delete(Resume).where(
                (Resume.expires_at < now) | (Resume.created_at < now - timedelta(hours=24))
            )
        )
        await self.session.commit()
        return result.rowcount
