import pytest
from app.parsers.schemas import ParseResult, ATSFlags
from app.parsers.resume_schema import ResumeData, ContactInfo, ExperienceEntry, EducationEntry
from app.features.ats_features import ATSFeatureExtractor
from app.features.content_features import ContentFeatureExtractor

@pytest.fixture
def sample_resume_data():
    return ResumeData(
        contact_info=ContactInfo(
            name="Test User",
            email="test@example.com",
            phone="123-456-7890",
            linkedin_url="linkedin.com/in/test",
            github_url="github.com/test",
            website="test.com"
        ),
        summary="Experienced engineer.",
        education=[EducationEntry(institution="Test Univ", degree="B.S.")],
        experience=[
            ExperienceEntry(
                company="Company A",
                title="SWE",
                start_date="2020",
                end_date="Present",
                bullets=[
                    "Developed a new scalable backend increasing performance by 50%.",
                    "Led a team of 5 engineers.",
                    "Improved latency by 200ms."
                ]
            ),
            ExperienceEntry(
                company="Company B",
                title="Intern",
                start_date="2018",
                end_date="2020",
                bullets=[
                    "Built an internal tool for data processing.",
                    "Saved $10K annually by reducing cloud costs."
                ]
            )
        ],
        skills=["Python", "AWS"],
        projects=[],
        certifications=[],
        achievements=[]
    )

@pytest.fixture
def sample_parse_result():
    return ParseResult(
        text="Sample text",
        word_count=400,
        page_count=1,
        ats_flags=ATSFlags(
            tables_detected=False,
            columns_detected=False,
            images_detected=False,
            is_scanned_pdf=False
        ),
        parser_used="txt",
        warnings=[]
    )

def test_ats_features(sample_parse_result, sample_resume_data):
    features = ATSFeatureExtractor.extract(sample_parse_result, sample_resume_data)
    
    # Contact maxed out
    assert features.contact_score == 1.0
    
    # 4 sections found (summary, education, experience, skills) out of 7 -> 4/7
    assert features.section_completeness == pytest.approx(4/7)
    
    # Word count 400 -> score 1.0
    assert features.word_count_score == 1.0
    
    # Page count 1 -> score 1.0
    assert features.page_score == 1.0
    
    # 5 total bullets / 2 jobs = 2.5 bullets/job -> score 2.5/5.0 = 0.5
    assert features.bullets_score == 0.5
    
    # Zero penalties
    assert features.total_format_penalty == 0.0
    
    # Check overall ATS score > 50
    assert features.ats_score > 50.0
    assert features.ats_score <= 100.0

def test_ats_features_penalties(sample_parse_result, sample_resume_data):
    sample_parse_result.ats_flags.is_scanned_pdf = True
    sample_parse_result.ats_flags.tables_detected = True
    
    features = ATSFeatureExtractor.extract(sample_parse_result, sample_resume_data)
    assert features.total_format_penalty == -20.0
    
def test_content_features(sample_resume_data):
    features = ContentFeatureExtractor.extract(sample_resume_data)
    
    # Action verbs check
    # 'developed', 'led', 'improved', 'built', 'saved' - all are in the list (or most of them)
    assert features.action_verb_count > 0
    assert features.starts_with_action_verb > 0.0
    assert "developed" in features.unique_action_verbs_used
    
    # Quantifications: "50%", "5", "200ms", "$10K"
    assert features.quantified_bullets > 0
    assert features.has_quantified_achievements is True
    
    # Total content score > 50
    assert features.content_score > 50.0

def test_empty_content_features():
    empty_resume = ResumeData(contact_info=ContactInfo())
    features = ContentFeatureExtractor.extract(empty_resume)
    
    assert features.action_verb_count == 0
    assert features.starts_with_action_verb == 0.0
    assert features.quantified_bullets == 0
    assert features.tense_consistency_score == 1.0 # default if no jobs
    assert features.content_score == 15.0 # tense score kicks in
