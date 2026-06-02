from dataclasses import dataclass, field

@dataclass
class ATSFeatures:
    # Granular flags for model
    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_github: bool = False
    has_summary: bool = False
    has_education: bool = False
    has_experience: bool = False
    has_skills: bool = False
    has_projects: bool = False
    
    contact_score: float = 0.0
    section_completeness: float = 0.0
    tables_penalty: float = 0.0
    images_penalty: float = 0.0
    columns_penalty: float = 0.0
    scanned_penalty: float = 0.0
    total_format_penalty: float = 0.0
    word_count: int = 0
    word_count_score: float = 0.0
    page_count: int = 0
    page_score: float = 0.0
    bullets_per_job: float = 0.0
    bullets_score: float = 0.0
    ats_score: float = 0.0

@dataclass
class ContentFeatures:
    action_verb_count: int = 0
    action_verb_count_norm: float = 0.0
    starts_with_action_verb: float = 0.0
    unique_action_verbs_used: list[str] = field(default_factory=list)
    variety_score: float = 0.0
    quantified_bullets: int = 0
    quantification_rate: float = 0.0
    has_quantified_achievements: bool = False
    tense_consistency_score: float = 0.0
    content_score: float = 0.0

@dataclass
class KeywordFeatures:
    matched_keywords: list[str] = field(default_factory=list)
    missing_keywords: list[str] = field(default_factory=list)
    exact_match_score: float = 0.0
    weighted_match_score: float = 0.0
    coverage_by_category: dict[str, float] = field(default_factory=dict)
    
    lang_coverage: float = 0.0
    framework_coverage: float = 0.0
    tools_coverage: float = 0.0
    
    keyword_score: float = 0.0

@dataclass
class SemanticFeatures:
    job_similarity: float = 0.0
    industry_fit: float = 0.0
    skills_coherence: float = 0.0
    semantic_score: float = 0.0
