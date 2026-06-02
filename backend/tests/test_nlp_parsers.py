import pytest
from app.parsers.section_extractor import SectionExtractor

@pytest.fixture
def strong_resume():
    return """
    SREERAM M
    Email: sreeram@example.com | Phone: +1 123 456 7890
    LinkedIn: linkedin.com/in/sreeram | GitHub: github.com/sreeram

    SUMMARY
    Senior Software Engineer with 5+ years of experience in Python and NLP.

    EXPERIENCE
    Google
    Senior Software Engineer | 2020 - Present
    • Led a team of 10 to build a massive NLP pipeline.
    • Improved latency by 50% using FastAPI.

    EDUCATION
    Stanford University
    Master of Science in Computer Science | 2018 - 2020
    GPA: 3.9

    SKILLS
    Python, FastAPI, SpaCy, Docker, Kubernetes, Leadership
    """

@pytest.fixture
def weak_resume():
    return """
    John Doe
    johndoe@email.com

    Work
    Some Company - 2022
    Worked on stuff.

    Skills
    Communication
    """

@pytest.fixture
def incomplete_resume():
    return """
    Just a bunch of text without any clear structure or headers.
    I like to code but I don't follow any format.
    """

def test_strong_resume_extraction(strong_resume):
    data = SectionExtractor.extract(strong_resume)
    assert data.contact_info.name == "SREERAM M"
    assert "sreeram@example.com" in data.contact_info.email
    assert len(data.experience) > 0
    assert data.experience[0].company == "Google"
    assert data.education[0].institution == "Stanford University"
    assert data.completeness_score >= 0.8

def test_weak_resume_extraction(weak_resume):
    data = SectionExtractor.extract(weak_resume)
    assert data.contact_info.email == "johndoe@email.com"
    assert data.completeness_score < 0.6

def test_incomplete_resume_extraction(incomplete_resume):
    data = SectionExtractor.extract(incomplete_resume)
    assert data.section_count == 0
    assert data.completeness_score < 0.3
