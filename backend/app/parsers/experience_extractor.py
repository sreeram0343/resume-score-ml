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
            
            lines = [l.strip() for l in block.split('\n') if l.strip()]

            # Extract Company (ORG)
            orgs = []
            for ent in doc.ents:
                if ent.label_ == "ORG":
                    # Check if the entity text is in a line that is NOT a bullet line
                    ent_first_line = ent.text.split('\n')[0].strip()
                    if ent_first_line:
                        ent_line = ""
                        for line in lines:
                            if ent_first_line in line:
                                ent_line = line
                                break
                        if ent_line and not ent_line.startswith(('•', '-', '*')):
                            orgs.append(ent_first_line)

            if orgs:
                entry.company = orgs[0]

            if not entry.company:
                # Fallback: check first line
                first_line = lines[0] if lines else ""
                if (first_line and 
                    not first_line.startswith(('•', '-', '*')) and 
                    not any(title.lower() in first_line.lower() for title in cls.COMMON_TITLES) and
                    not any(date_word in first_line.lower() for date_word in ["present", "current", "20"]) and
                    len(first_line.split()) <= 6):
                    entry.company = first_line

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
            for line in lines:
                if any(title.lower() in line.lower() for title in cls.COMMON_TITLES):
                    entry.title = line
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
