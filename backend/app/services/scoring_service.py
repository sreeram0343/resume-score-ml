import os
from typing import Any
from app.db.models import Resume
from app.parsers.section_extractor import SectionExtractor
from app.parsers.schemas import ParseResult, ATSFlags
from app.features.ats_features import ATSFeatureExtractor
from app.features.content_features import ContentFeatureExtractor
from app.features.keyword_features import KeywordFeatureExtractor
from app.features.semantic_features import SemanticFeatureExtractor
from app.models.feature_assembler import FeatureAssembler
from app.models.xgboost_scorer import ResumeScorer
from app.models.explainer import ResumeSHAPExplainer
from app.services.suggestion_engine import SuggestionEngine
from app.core.config import settings

class ScoringService:
    _scorer = None
    _explainer = None
    
    def __init__(self):
        if ScoringService._scorer is None:
            model_path = settings.model_path
            if os.path.exists(model_path):
                ScoringService._scorer = ResumeScorer.load(model_path)
                ScoringService._explainer = ResumeSHAPExplainer()
                ScoringService._explainer.initialize(
                    ScoringService._scorer.model, 
                    ScoringService._scorer.feature_names
                )

    async def process(self, resume: Resume, job_description: str | None, target_role: str) -> dict:
        # 1. NLP Extraction
        resume_data = SectionExtractor.extract(resume.raw_text)
        
        # 2. Simulate ParseResult for features
        pr = ParseResult(
            text=resume.raw_text,
            word_count=resume.word_count,
            page_count=resume.page_count,
            ats_flags=ATSFlags(**resume.ats_flags),
            parser_used=resume.file_type
        )

        # 3. Feature Extraction
        ats_f = ATSFeatureExtractor.extract(pr, resume_data)
        content_f = ContentFeatureExtractor.extract(resume_data)
        keyword_f = KeywordFeatureExtractor.extract(resume.raw_text, target_role, job_description)
        semantic_f = SemanticFeatureExtractor.extract(
            resume.raw_text, target_role, job_description,
            skills_text=", ".join(resume_data.skills),
            experience_text="\n".join([f"{e.company} {e.title}" for e in resume_data.experience])
        )

        # 4. Assembly & Scoring
        feat_vec = FeatureAssembler.assemble(ats_f, content_f, keyword_f, semantic_f)
        
        if ScoringService._scorer:
            overall_score = ScoringService._scorer.predict(feat_vec)
            explanation = ScoringService._explainer.explain(feat_vec, overall_score, target_role, bool(job_description))
        else:
            # Fallback
            sub_scores = {
                "ats": ats_f.ats_score,
                "content": content_f.content_score,
                "keyword": keyword_f.keyword_score,
                "semantic": semantic_f.semantic_score
            }
            overall_score = ResumeScorer().predict_with_fallback(feat_vec, sub_scores)
            explanation = ResumeSHAPExplainer().fallback_explain(sub_scores, overall_score, target_role, bool(job_description))

        # 5. Suggestions
        engine = SuggestionEngine()
        shap_dict = {f.feature_name: f.shap_value for f in explanation.positive_factors + explanation.negative_factors}
        suggestions = engine.get_suggestions(ats_f, content_f, keyword_f, pr, shap_dict)

        return {
            "overall_score": round(overall_score, 1),
            "ats_score": ats_f.ats_score,
            "content_score": content_f.content_score,
            "keyword_score": keyword_f.keyword_score,
            "semantic_score": semantic_f.semantic_score,
            "grade": self._get_grade(overall_score),
            "explanation_text": explanation.explanation_text,
            "positive_factors": explanation.positive_factors,
            "negative_factors": explanation.negative_factors,
            "suggestions": suggestions,
            "keyword_gaps": keyword_f.missing_keywords,
            "waterfall_data": explanation.waterfall_data,
            "feature_vector": {name: float(val) for name, val in zip(FeatureAssembler.get_feature_names(), feat_vec)},
            "shap_values": shap_dict
        }

    @staticmethod
    def _get_grade(score: float) -> str:
        if score >= 90: return "A+"
        if score >= 85: return "A"
        if score >= 80: return "B+"
        if score >= 75: return "B"
        if score >= 70: return "C+"
        if score >= 65: return "C"
        if score >= 55: return "D"
        return "F"
