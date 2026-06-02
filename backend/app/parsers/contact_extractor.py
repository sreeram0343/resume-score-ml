import re
import spacy
from .resume_schema import ContactInfo

# Load spacy model lazily
_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model isn't downloaded
            import os
            os.system("python -m spacy download en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

class ContactExtractor:
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'(\+?1?\s*[\-.]?\s*\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4})')
    LINKEDIN_PATTERN = re.compile(r'(?:linkedin\.com/in/)([\w\-]+)')
    GITHUB_PATTERN = re.compile(r'(?:github\.com/)([\w\-]+)')

    @classmethod
    def extract(cls, text: str) -> ContactInfo:
        nlp = get_nlp()
        doc = nlp(text[:2000])  # Focus on beginning of resume
        
        email = cls.EMAIL_PATTERN.search(text)
        phone = cls.PHONE_PATTERN.search(text)
        linkedin = cls.LINKEDIN_PATTERN.search(text)
        github = cls.GITHUB_PATTERN.search(text)
        
        name = None
        # Try to find PERSON in first 10 lines
        lines = [l.strip() for l in text.split('\n') if l.strip()][:10]
        for line in lines:
            line_doc = nlp(line)
            for ent in line_doc.ents:
                if ent.label_ == "PERSON":
                    name = ent.text
                    break
            if name: break
        
        # Fallback for name
        if not name:
            for line in lines:
                if not any([cls.EMAIL_PATTERN.search(line), cls.PHONE_PATTERN.search(line), 
                           "linkedin.com" in line, "github.com" in line]):
                    name = line
                    break

        return ContactInfo(
            name=name,
            email=email.group(0) if email else None,
            phone=phone.group(0) if phone else None,
            linkedin_url=f"linkedin.com/in/{linkedin.group(1)}" if linkedin else None,
            github_url=f"github.com/{github.group(1)}" if github else None,
            website=None # Additional logic could go here
        )
