import functools
import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from .schema import SemanticFeatures

logger = structlog.get_logger()

class SemanticFeatureExtractor:
    _model = None
    _role_embeddings = {}
    
    ROLE_DESCRIPTIONS = {
        "Machine Learning Engineer": "Expert in Python, PyTorch, TensorFlow, and deploying ML models. Deep knowledge of algorithms, feature engineering, and MLOps.",
        "Software Engineer": "Experienced in full-stack development using Python, Java, JavaScript. Skilled in system design, APIs, and cloud infrastructure.",
        "Data Scientist": "Expert in statistical analysis, data modeling, and visualization. Proficient in Python, SQL, and communicating insights to stakeholders.",
        "Product Manager": "Leader in product roadmap strategy, stakeholder management, and agile methodologies. Focused on KPI delivery and user research."
    }

    @classmethod
    def get_model(cls):
        if cls._model is None:
            try:
                cls._model = SentenceTransformer("all-MiniLM-L6-v2")
                # Pre-calculate role embeddings
                for role, desc in cls.ROLE_DESCRIPTIONS.items():
                    cls._role_embeddings[role] = cls._model.encode(desc)
            except Exception as e:
                logger.error("Failed to load SentenceTransformer model", error=str(e))
                return None
        return cls._model

    @classmethod
    @functools.lru_cache(maxsize=128)
    def _get_embedding(cls, text: str) -> np.ndarray | None:
        model = cls.get_model()
        if model is None:
            return None
        # Max 512 tokens is usually handled by the model internally
        return model.encode(text)

    @classmethod
    def extract(
        cls, 
        resume_text: str, 
        target_role: str,
        job_description: str | None = None,
        skills_text: str | None = None,
        experience_text: str | None = None
    ) -> SemanticFeatures:
        if cls.get_model() is None:
            return SemanticFeatures(semantic_score=50.0)

        resume_emb = cls._get_embedding(resume_text)
        if resume_emb is None:
            return SemanticFeatures(semantic_score=50.0)

        # 1. Job Similarity
        job_similarity = 0.0
        if job_description:
            jd_emb = cls._get_embedding(job_description)
            if jd_emb is not None:
                job_similarity = float(cosine_similarity([resume_emb], [jd_emb])[0][0])

        # 2. Industry Fit
        role_emb = cls._role_embeddings.get(target_role)
        if role_emb is None:
            # Fallback to default Software Engineer or first available
            role_emb = list(cls._role_embeddings.values())[1]
        industry_fit = float(cosine_similarity([resume_emb], [role_emb])[0][0])

        # 3. Skills Coherence
        skills_coherence = 0.0
        if skills_text and experience_text:
            s_emb = cls._get_embedding(skills_text)
            e_emb = cls._get_embedding(experience_text)
            if s_emb is not None and e_emb is not None:
                skills_coherence = float(cosine_similarity([s_emb], [e_emb])[0][0])

        # 4. Semantic Score
        if job_description:
            raw_score = (job_similarity * 60.0) + (skills_coherence * 40.0)
        else:
            raw_score = (industry_fit * 70.0) + (skills_coherence * 30.0)

        return SemanticFeatures(
            job_similarity=round(job_similarity, 2),
            industry_fit=round(industry_fit, 2),
            skills_coherence=round(skills_coherence, 2),
            semantic_score=round(max(0.0, min(100.0, raw_score * 100.0)), 2)
        )
