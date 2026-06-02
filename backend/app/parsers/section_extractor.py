import re
from .resume_schema import ResumeData, ContactInfo
from .contact_extractor import ContactExtractor
from .experience_extractor import ExperienceExtractor
from .education_extractor import EducationExtractor
from .skills_extractor import SkillsExtractor

class SectionExtractor:
    SECTION_HEADERS = re.compile(
        r'^(EXPERIENCE|WORK\s+HISTORY|EMPLOYMENT|EDUCATION|SKILLS?|TECHNICAL\s+SKILLS?|'
        r'PROJECTS?|CERTIFICATIONS?|SUMMARY|OBJECTIVE|PROFILE|ACHIEVEMENTS?|'
        r'ACCOMPLISHMENTS?|AWARDS?|PUBLICATIONS?)\s*:?\s*$',
        re.MULTILINE | re.IGNORECASE
    )

    @classmethod
    def extract(cls, text: str) -> ResumeData:
        sections = cls._split_sections(text)
        
        # Contact info usually at the top, outside of specific headers sometimes
        contact_info = ContactExtractor.extract(text)
        
        data = ResumeData(contact_info=contact_info)
        data.section_count = len(sections)

        for header, content in sections.items():
            header = header.upper()
            if any(h in header for h in ["EXPERIENCE", "WORK", "EMPLOYMENT"]):
                data.experience = ExperienceExtractor.extract(content)
            elif "EDUCATION" in header:
                data.education = EducationExtractor.extract(content)
            elif "SKILL" in header:
                data.skills = SkillsExtractor.extract(content)
            elif any(h in header for h in ["SUMMARY", "OBJECTIVE", "PROFILE"]):
                data.summary = content.strip()
            elif "ACHIEVEMENT" in header or "AWARD" in header:
                data.achievements = [l.strip() for l in content.split('\n') if l.strip()]

        data.completeness_score = cls._calculate_completeness(data)
        return data

    @classmethod
    def _split_sections(cls, text: str) -> dict[str, str]:
        matches = list(cls.SECTION_HEADERS.finditer(text))
        sections = {}
        
        if not matches:
            return {}

        for i in range(len(matches)):
            start = matches[i].end()
            end = matches[i+1].start() if i + 1 < len(matches) else len(text)
            header = matches[i].group(1)
            sections[header] = text[start:end]
            
        return sections

    @staticmethod
    def _calculate_completeness(data: ResumeData) -> float:
        weights = {
            "contact_info": 0.2,
            "summary": 0.1,
            "experience": 0.3,
            "education": 0.2,
            "skills": 0.2
        }
        score = 0.0
        if data.contact_info.email and data.contact_info.phone: score += weights["contact_info"]
        if data.summary: score += weights["summary"]
        if data.experience: score += weights["experience"]
        if data.education: score += weights["education"]
        if data.skills: score += weights["skills"]
        
        return round(score, 2)
