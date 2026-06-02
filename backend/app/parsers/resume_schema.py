from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ContactInfo:
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    website: str | None = None

@dataclass
class ExperienceEntry:
    company: str | None = None
    title: str | None = None
    start_date: str | None = None
    end_date: str | None = None      # "Present" or date string
    duration_months: int | None = None
    bullets: list[str] = field(default_factory=list)

@dataclass
class EducationEntry:
    institution: str | None = None
    degree: str | None = None        # "Bachelor of Science", "M.S.", etc.
    field: str | None = None
    graduation_year: int | None = None
    gpa: float | None = None

@dataclass
class ResumeData:
    contact_info: ContactInfo
    summary: str | None = None
    education: list[EducationEntry] = field(default_factory=list)
    experience: list[ExperienceEntry] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    projects: list[dict] = field(default_factory=list)
    certifications: list[dict] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    section_count: int = 0        # how many sections were found
    completeness_score: float = 0.0  # 0.0–1.0
