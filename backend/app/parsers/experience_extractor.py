import re
from datetime import datetime
from dateutil import parser as date_parser
from .contact_extractor import get_nlp
from .resume_schema import ExperienceEntry

class ExperienceExtractor:
    COMMON_TITLES = {
        "Software Engineer", "Developer", "Manager", "Analyst", "Intern", 
        "Director", "Lead", "Consultant", "Specialist", "Architect"
    }

    @classmethod
    def extract(cls, text: str) -> list[ExperienceEntry]:
        nlp = get_nlp()
        # Split by blocks (common pattern: date on its own line or blank lines)
        blocks = re.split(r'\n\s*\n', text.strip())
        entries = []

        for block in blocks:
            if not block.strip(): continue
            
            entry = ExperienceEntry()
            doc = nlp(block)
            
            # Extract Company (ORG)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                entry.company = orgs[0]

            # Extract Dates
            dates = [ent.text for ent in doc.ents if ent.label_ == "DATE"]
            if dates:
                entry.start_date = dates[0]
                if len(dates) > 1:
                    entry.end_date = dates[1]
                else:
                    if "Present" in block or "Current" in block:
                        entry.end_date = "Present"

            # Calculate Duration
            if entry.start_date and entry.end_date:
                entry.duration_months = cls._calculate_duration(entry.start_date, entry.end_date)

            # Title Heuristics
            lines = block.split('\n')
            for line in lines:
                if any(title.lower() in line.lower() for title in cls.COMMON_TITLES):
                    entry.title = line.strip()
                    break

            # Bullets
            entry.bullets = [l.strip()[1:].strip() for l in lines if l.strip().startswith(('•', '-', '*'))]
            
            if entry.company or entry.title:
                entries.append(entry)

        return entries

    @staticmethod
    def _calculate_duration(start: str, end: str) -> int | None:
        try:
            s_dt = date_parser.parse(start, fuzzy=True)
            if end.lower() in ["present", "current", "now"]:
                e_dt = datetime.now()
            else:
                e_dt = date_parser.parse(end, fuzzy=True)
            
            return (e_dt.year - s_dt.year) * 12 + (e_dt.month - s_dt.month)
        except Exception:
            return None
