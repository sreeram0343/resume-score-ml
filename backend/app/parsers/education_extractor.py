import re
from .contact_extractor import get_nlp
from .resume_schema import EducationEntry

class EducationExtractor:
    DEGREE_PATTERN = re.compile(r'\b(Bachelor|B\.S\.|B\.A\.|Master|M\.S\.|M\.A\.|MBA|PhD|Ph\.D\.|Associate)\b', re.I)
    YEAR_PATTERN = re.compile(r'\b(19|20)\d{2}\b')
    GPA_PATTERN = re.compile(r'GPA:?\s*(\d\.\d{1,2})', re.I)

    @classmethod
    def extract(cls, text: str) -> list[EducationEntry]:
        nlp = get_nlp()
        blocks = re.split(r'\n\s*\n', text.strip())
        entries = []

        for block in blocks:
            if not block.strip(): continue
            entry = EducationEntry()
            
            # Institution (ORG)
            doc = nlp(block)
            orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            if orgs:
                entry.institution = orgs[0].split('\n')[0].strip()
            
            # Degree
            degree_match = cls.DEGREE_PATTERN.search(block)
            if degree_match:
                entry.degree = degree_match.group(0)

            # Year
            year_match = cls.YEAR_PATTERN.search(block)
            if year_match:
                entry.graduation_year = int(year_match.group(0))

            # GPA
            gpa_match = cls.GPA_PATTERN.search(block)
            if gpa_match:
                entry.gpa = float(gpa_match.group(1))

            if entry.institution or entry.degree:
                entries.append(entry)

        return entries
