from dataclasses import dataclass
import numpy as np
import xgboost as xgb
import shap

@dataclass
class Factor:
    feature_name: str
    human_label: str       
    shap_value: float      
    impact_label: str      
    category: str          
    direction: str         

@dataclass
class Explanation:
    base_score: float              
    predicted_score: float
    positive_factors: list[Factor]  
    negative_factors: list[Factor]  
    explanation_text: str           
    waterfall_data: dict            

class ResumeSHAPExplainer:
    FEATURE_LABELS = {
        "has_email": ("Email address present", "ats"),
        "has_phone": ("Phone number present", "ats"),
        "has_linkedin": ("LinkedIn profile included", "ats"),
        "has_github": ("GitHub profile included", "ats"),
        "has_summary": ("Professional summary included", "ats"),
        "has_projects": ("Projects section present", "ats"),
        "tables_penalty": ("Tables detected — ATS unfriendly", "ats"),
        "images_penalty": ("Images detected — ATS unfriendly", "ats"),
        "columns_penalty": ("Multi-column layout detected", "ats"),
        "word_count_score": ("Resume length", "ats"),
        "starts_with_action_verb": ("Action verb bullet points", "content"),
        "quantification_rate": ("Quantified achievements", "content"),
        "variety_score": ("Action verb variety", "content"),
        "exact_match_score": ("Keyword match rate", "keyword"),
        "weighted_match_score": ("Weighted keyword coverage", "keyword"),
        "lang_coverage": ("Programming languages coverage", "keyword"),
        "framework_coverage": ("Frameworks & libraries coverage", "keyword"),
        "job_similarity": ("Semantic match to job description", "semantic"),
        "industry_fit": ("Industry fit for target role", "semantic"),
        "skills_coherence": ("Skills-experience coherence", "semantic"),
    }

    def __init__(self):
        self.explainer = None
        self.feature_names = []
        self._is_initialized = False

    def initialize(self, model: xgb.XGBRegressor, feature_names: list[str]):
        # TreeExplainer works with XGBoost out of the box
        self.explainer = shap.TreeExplainer(model)
        self.feature_names = feature_names
        self._is_initialized = True

    def explain(self, feature_vector: np.ndarray, predicted_score: float, role: str = "Software Engineer", has_jd: bool = False) -> Explanation:
        if not self._is_initialized:
            raise ValueError("Explainer not initialized")

        if feature_vector.ndim == 1:
            feature_vector = feature_vector.reshape(1, -1)

        # Get SHAP values
        shap_values_obj = self.explainer(feature_vector)
        shap_values = shap_values_obj.values[0]
        base_score = float(shap_values_obj.base_values[0])

        factors = []
        for i, name in enumerate(self.feature_names):
            val = float(shap_values[i])
            if abs(val) < 1e-4:
                continue
            
            label_info = self.FEATURE_LABELS.get(name, (name.replace("_", " ").capitalize(), "other"))
            direction = "positive" if val > 0 else "negative"
            impact_label = f"+{val:.1f} pts" if val > 0 else f"{val:.1f} pts"
            
            factors.append(Factor(
                feature_name=name,
                human_label=label_info[0],
                shap_value=val,
                impact_label=impact_label,
                category=label_info[1],
                direction=direction
            ))

        positive_factors = sorted([f for f in factors if f.direction == "positive"], key=lambda x: x.shap_value, reverse=True)[:5]
        negative_factors = sorted([f for f in factors if f.direction == "negative"], key=lambda x: x.shap_value)[:5]

        exp = Explanation(
            base_score=base_score,
            predicted_score=predicted_score,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            explanation_text="",
            waterfall_data={}
        )

        exp.explanation_text = self.generate_explanation_text(exp, role, has_jd)
        exp.waterfall_data = self.generate_waterfall_data(exp, factors)

        return exp

    def generate_explanation_text(self, explanation: Explanation, role: str, has_jd: bool) -> str:
        score = explanation.predicted_score
        grade = self._get_grade(score)
        
        pos_labels = [f.human_label.lower() for f in explanation.positive_factors[:2]]
        neg_labels = [f.human_label.lower() for f in explanation.negative_factors[:2]]
        
        top2_positive = ", ".join(pos_labels) if pos_labels else "general layout"
        top2_negative = ", ".join(neg_labels) if neg_labels else "none specifically"

        text = f"Your resume scored {score:.0f}/100 (grade: {grade}). Key strengths: {top2_positive}. Main areas to improve: {top2_negative}."
        if not has_jd:
            text += f" No job description was provided, so keyword scoring used default {role} keywords."
            
        return text

    def generate_waterfall_data(self, explanation: Explanation, all_factors: list[Factor]) -> dict:
        cat_sums = {}
        for f in all_factors:
            cat_sums[f.category] = cat_sums.get(f.category, 0.0) + f.shap_value

        steps = []
        for cat, val in cat_sums.items():
            if abs(val) > 0.1:
                direction = "positive" if val > 0 else "negative"
                steps.append({
                    "label": cat.capitalize(),
                    "value": round(val, 1),
                    "direction": direction
                })

        return {
            "base": round(explanation.base_score, 1),
            "steps": steps,
            "final": round(explanation.predicted_score, 1)
        }

    def fallback_explain(self, scores: dict, predicted_score: float, role: str = "Software Engineer", has_jd: bool = False) -> Explanation:
        exp = Explanation(
            base_score=50.0,
            predicted_score=predicted_score,
            positive_factors=[],
            negative_factors=[],
            explanation_text="",
            waterfall_data={}
        )
        exp.explanation_text = self.generate_explanation_text(exp, role, has_jd)
        exp.waterfall_data = {
            "base": 50.0,
            "steps": [{"label": k.capitalize(), "value": round(v - 50, 1), "direction": "positive" if v > 50 else "negative"} for k, v in scores.items() if isinstance(v, (int, float))],
            "final": round(predicted_score, 1)
        }
        return exp

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
