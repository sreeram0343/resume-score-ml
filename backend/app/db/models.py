import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))
    file_size_bytes: Mapped[int]
    raw_text: Mapped[str] = mapped_column(Text)
    word_count: Mapped[int]
    page_count: Mapped[int]
    contact_info: Mapped[dict | None] = mapped_column(JSONB)
    sections: Mapped[dict | None] = mapped_column(JSONB)
    ats_flags: Mapped[dict | None] = mapped_column(JSONB)
    parsing_warnings: Mapped[list | None] = mapped_column(JSONB)
    scores: Mapped[list["Score"]] = relationship(back_populates="resume", cascade="all, delete-orphan")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    expires_at: Mapped[datetime | None]

class Score(Base):
    __tablename__ = "scores"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    overall_score: Mapped[float]
    ats_score: Mapped[float]
    content_score: Mapped[float]
    keyword_score: Mapped[float]
    semantic_score: Mapped[float]
    grade: Mapped[str] = mapped_column(String(3))
    job_description: Mapped[str | None] = mapped_column(Text)
    target_role: Mapped[str | None] = mapped_column(String(100))
    feature_vector: Mapped[dict] = mapped_column(JSONB)
    shap_values: Mapped[dict] = mapped_column(JSONB)
    suggestions: Mapped[list] = mapped_column(JSONB)
    keyword_gaps: Mapped[list | None] = mapped_column(JSONB)
    waterfall_data: Mapped[dict | None] = mapped_column(JSONB)
    processing_time_ms: Mapped[int]
    resume: Mapped["Resume"] = relationship(back_populates="scores")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)

Index("ix_resumes_created_at", Resume.created_at)
Index("ix_scores_resume_id_created", Score.resume_id, Score.created_at)
