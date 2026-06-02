import numpy as np
from app.features.schema import ATSFeatures, ContentFeatures, KeywordFeatures, SemanticFeatures

class FeatureAssembler:
    FEATURE_NAMES = [
        # ATS (15 features)
        "has_email", "has_phone", "has_linkedin", "has_github",
        "has_summary", "has_education", "has_experience", "has_skills", "has_projects",
        "tables_penalty", "images_penalty", "columns_penalty",
        "word_count_score", "page_score", "bullets_score",
        # Content (5 features)
        "action_verb_count_norm", "starts_with_action_verb",
        "quantification_rate", "variety_score", "tense_consistency_score",
        # Keyword (5 features)
        "exact_match_score", "weighted_match_score",
        "lang_coverage", "framework_coverage", "tools_coverage",
        # Semantic (3 features)
        "job_similarity", "industry_fit", "skills_coherence",
    ]

    @classmethod
    def assemble(
        cls, 
        ats: ATSFeatures, 
        content: ContentFeatures, 
        keyword: KeywordFeatures, 
        semantic: SemanticFeatures
    ) -> np.ndarray:
        features = [
            # ATS
            float(ats.has_email),
            float(ats.has_phone),
            float(ats.has_linkedin),
            float(ats.has_github),
            float(ats.has_summary),
            float(ats.has_education),
            float(ats.has_experience),
            float(ats.has_skills),
            float(ats.has_projects),
            ats.tables_penalty,
            ats.images_penalty,
            ats.columns_penalty,
            ats.word_count_score,
            ats.page_score,
            ats.bullets_score,
            # Content
            content.action_verb_count_norm,
            content.starts_with_action_verb,
            content.quantification_rate,
            content.variety_score,
            content.tense_consistency_score,
            # Keyword
            keyword.exact_match_score,
            keyword.weighted_match_score,
            keyword.lang_coverage,
            keyword.framework_coverage,
            keyword.tools_coverage,
            # Semantic
            semantic.job_similarity,
            semantic.industry_fit,
            semantic.skills_coherence
        ]
        return np.array(features, dtype=np.float32)

    @classmethod
    def get_feature_names(cls) -> list[str]:
        return cls.FEATURE_NAMES
