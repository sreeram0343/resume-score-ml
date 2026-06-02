from dataclasses import dataclass, field

@dataclass
class ATSFeatures:
    contact_score: float
    section_completeness: float
    tables_penalty: float
    images_penalty: float
    columns_penalty: float
    scanned_penalty: float
    total_format_penalty: float
    word_count: int
    word_count_score: float
    page_count: int
    page_score: float
    bullets_per_job: float
    bullets_score: float
    ats_score: float

@dataclass
class ContentFeatures:
    action_verb_count: int
    starts_with_action_verb: float
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
    keyword_score: float = 0.0

@dataclass
class SemanticFeatures:
    job_similarity: float = 0.0
    industry_fit: float = 0.0
    skills_coherence: float = 0.0
    semantic_score: float = 0.0
