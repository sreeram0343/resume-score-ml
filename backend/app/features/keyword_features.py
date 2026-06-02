import re
from collections import Counter
from typing import Any
from statistics import mean

from app.parsers.contact_extractor import get_nlp
from .schema import KeywordFeatures

class KeywordFeatureExtractor:
    DEFAULT_KEYWORDS = {
        "Machine Learning Engineer": [
            "Python", "TensorFlow", "PyTorch", "scikit-learn", "MLflow",
            "Docker", "Kubernetes", "SQL", "pandas", "numpy", "deep learning", 
            "NLP", "feature engineering", "model deployment", "A/B testing", 
            "Git", "AWS", "GCP"
        ],
        "Software Engineer": [
            "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
            "REST API", "GraphQL", "SQL", "PostgreSQL", "Docker", "Kubernetes", 
            "CI/CD", "Git", "AWS", "Linux"
        ],
        "Data Scientist": [
            "Python", "R", "SQL", "pandas", "numpy", "matplotlib", "scikit-learn",
            "statistics", "regression", "classification", "A/B testing", 
            "Tableau", "Power BI", "Spark"
        ],
        "Product Manager": [
            "roadmap", "stakeholder", "OKR", "agile", "scrum", "user research",
            "metrics", "KPI", "go-to-market", "prioritization", "Jira", "product strategy"
        ]
    }

    TECH_CATEGORIES = {
        "languages": ["python", "java", "javascript", "typescript", "ruby", "go", "c++", "rust", "php", "swift"],
        "frameworks": ["react", "angular", "vue", "django", "fastapi", "flask", "spring", "pytorch", "tensorflow", "express"],
        "tools": ["docker", "git", "kubernetes", "jenkins", "terraform", "ansible", "gradle", "maven"],
        "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "sqlite"],
        "cloud": ["aws", "azure", "gcp", "heroku", "digitalocean", "lambda", "s3", "ec2"]
    }

    @classmethod
    def extract(
        cls, 
        resume_text: str, 
        target_role: str, 
        job_description: str | None = None
    ) -> KeywordFeatures:
        nlp = get_nlp()
        resume_text_lower = resume_text.lower()
        
        # 1. JD KEYWORD EXTRACTION (or fall back to defaults)
        if job_description:
            jd_keywords = cls._extract_jd_keywords(job_description)
        else:
            default_list = cls.DEFAULT_KEYWORDS.get(target_role, cls.DEFAULT_KEYWORDS["Software Engineer"])
            jd_keywords = {k: 1.0 for k in default_list}

        # 2. KEYWORD MATCHING
        matched_keywords = []
        missing_keywords = []
        weighted_matched_sum = 0.0
        total_weight = sum(jd_keywords.values()) or 1.0

        resume_doc = nlp(resume_text_lower)
        resume_lemmas = {token.lemma_ for token in resume_doc if not token.is_stop and not token.is_punct}

        for keyword, weight in jd_keywords.items():
            keyword_lower = keyword.lower()
            
            # Exact match with word boundaries
            exact_match = re.search(rf'\b{re.escape(keyword_lower)}\b', resume_text_lower)
            
            # Fuzzy/Lemma match
            keyword_doc = nlp(keyword_lower)
            keyword_lemmas = {token.lemma_ for token in keyword_doc if not token.is_stop}
            lemma_match = keyword_lemmas.issubset(resume_lemmas) if keyword_lemmas else False

            if exact_match or lemma_match:
                matched_keywords.append(keyword)
                weighted_matched_sum += weight
            else:
                missing_keywords.append(keyword)

        exact_match_score = len(matched_keywords) / len(jd_keywords) if jd_keywords else 0.0
        weighted_match_score = weighted_matched_sum / total_weight

        # 3. TECH CATEGORY COVERAGE
        coverage_by_category = {}
        for cat, skills in cls.TECH_CATEGORIES.items():
            cat_matches = 0
            for skill in skills:
                if re.search(rf'\b{re.escape(skill)}\b', resume_text_lower):
                    cat_matches += 1
            coverage_by_category[cat] = min(1.0, cat_matches / 3.0) # Assume 3 skills per cat is good

        # 4. KEYWORD SCORE
        cat_coverage_mean = mean(coverage_by_category.values()) if coverage_by_category else 0.0
        keyword_score = (weighted_match_score * 60.0) + (cat_coverage_mean * 40.0)

        return KeywordFeatures(
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            exact_match_score=round(exact_match_score, 2),
            weighted_match_score=round(weighted_match_score, 2),
            coverage_by_category=coverage_by_category,
            lang_coverage=coverage_by_category.get("languages", 0.0),
            framework_coverage=coverage_by_category.get("frameworks", 0.0),
            tools_coverage=coverage_by_category.get("tools", 0.0),
            keyword_score=round(max(0.0, min(100.0, keyword_score)), 2)
        )

    @classmethod
    def _extract_jd_keywords(cls, jd_text: str) -> dict[str, float]:
        nlp = get_nlp()
        doc = nlp(jd_text)
        
        # Extract Nouns and Proper Nouns
        keywords = []
        for token in doc:
            if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop and len(token.text) > 2:
                keywords.append(token.lemma_.lower())
        
        # Extract Bigrams
        for i in range(len(doc) - 1):
            t1, t2 = doc[i], doc[i+1]
            if t1.pos_ in ["NOUN", "PROPN"] and t2.pos_ in ["NOUN", "PROPN"]:
                keywords.append(f"{t1.lemma_.lower()} {t2.lemma_.lower()}")

        counts = Counter(keywords)
        # Normalize weights by frequency
        if not counts:
            return {}
        
        max_count = max(counts.values())
        return {k: v / max_count for k, v in counts.most_common(20)}
