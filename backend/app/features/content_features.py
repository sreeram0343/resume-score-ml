import re
import spacy
from app.parsers.resume_schema import ResumeData
from .schema import ContentFeatures

_nlp = None

def get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            import os
            os.system("python -m spacy download en_core_web_sm")
            _nlp = spacy.load("en_core_web_sm")
    return _nlp

class ContentFeatureExtractor:
    ACTION_VERBS = {
        "built", "developed", "engineered", "architected", "deployed", "optimized", "automated",
        "led", "managed", "mentored", "spearheaded", "initiated", "delivered", "reduced",
        "improved", "increased", "accelerated", "designed", "created", "launched", "analyzed",
        "evaluated", "collaborated", "implemented", "integrated", "streamlined", "scaled"
    }

    QUANTIFICATION_PATTERNS = [
        re.compile(r'\d+\s*%'),
        re.compile(r'\d+[xX](?:\s|$)'),
        re.compile(r'\$[\d,]+[KMBkmb]?'),
        re.compile(r'\d+[,\d]*\s+(?:users|customers|clients|engineers|requests)'),
        re.compile(r'(?:increased|reduced|improved|cut|saved|grew)\s+(?:by\s+)?\d+', re.IGNORECASE)
    ]

    @classmethod
    def extract(cls, resume_data: ResumeData) -> ContentFeatures:
        # Flatten all bullets
        all_bullets = []
        for exp in resume_data.experience:
            all_bullets.extend(exp.bullets)
        
        # Include project bullets if structured as dicts with "bullets" key
        for proj in resume_data.projects:
            if isinstance(proj, dict) and "bullets" in proj and isinstance(proj["bullets"], list):
                all_bullets.extend(proj["bullets"])

        total_bullets = len(all_bullets)

        # 1. ACTION VERB ANALYSIS
        action_verb_count = 0
        bullets_starting_with_action_verb = 0
        unique_action_verbs_used = set()

        for bullet in all_bullets:
            words = [w.strip() for w in re.split(r'\W+', bullet) if w.strip()]
            if not words:
                continue
            
            # Check first word
            first_word = words[0].lower()
            if first_word in cls.ACTION_VERBS:
                bullets_starting_with_action_verb += 1
            
            # Check all words
            for word in words:
                word_lower = word.lower()
                if word_lower in cls.ACTION_VERBS:
                    action_verb_count += 1
                    unique_action_verbs_used.add(word_lower)

        starts_with_action_verb = bullets_starting_with_action_verb / max(total_bullets, 1)
        variety_score = min(1.0, len(unique_action_verbs_used) / max(total_bullets, 1))

        # 2. QUANTIFICATION DETECTION
        quantified_bullets_count = 0
        for bullet in all_bullets:
            if any(p.search(bullet) for p in cls.QUANTIFICATION_PATTERNS):
                quantified_bullets_count += 1
        
        quantification_rate = quantified_bullets_count / max(total_bullets, 1)
        has_quantified_achievements = quantification_rate > 0.0

        # 3. TENSE ANALYSIS
        tense_consistency_score = cls._analyze_tenses(resume_data)

        # 4. CONTENT SCORE FORMULA
        content_score = (
            starts_with_action_verb * 30.0 +
            min(1.0, quantification_rate ** 0.5) * 35.0 +
            min(1.0, variety_score) * 20.0 +
            tense_consistency_score * 15.0
        )

        return ContentFeatures(
            action_verb_count=action_verb_count,
            starts_with_action_verb=starts_with_action_verb,
            unique_action_verbs_used=sorted(list(unique_action_verbs_used)),
            variety_score=variety_score,
            quantified_bullets=quantified_bullets_count,
            quantification_rate=quantification_rate,
            has_quantified_achievements=has_quantified_achievements,
            tense_consistency_score=tense_consistency_score,
            content_score=round(max(0.0, min(100.0, content_score)), 2)
        )

    @classmethod
    def _analyze_tenses(cls, resume_data: ResumeData) -> float:
        """Analyze if present jobs use present tense and past jobs use past tense."""
        nlp = get_nlp()
        if not resume_data.experience:
            return 1.0  # Pass if no experience

        total_analyzed = 0
        correct_tense_count = 0

        for exp in resume_data.experience:
            is_present_job = False
            if exp.end_date and exp.end_date.lower() in ["present", "current", "now"]:
                is_present_job = True

            for bullet in exp.bullets:
                doc = nlp(bullet[:150])  # Check start of bullet
                verbs = [token for token in doc if token.pos_ == "VERB"]
                if not verbs:
                    continue
                
                total_analyzed += 1
                first_verb = verbs[0]
                # Spacy tags: VBD = past tense, VBG = gerund, VBP/VBZ = present
                is_past_verb = first_verb.tag_ in ["VBD", "VBN"]
                is_present_verb = first_verb.tag_ in ["VBP", "VBZ", "VBG", "VB"]

                if is_present_job and is_present_verb:
                    correct_tense_count += 1
                elif not is_present_job and is_past_verb:
                    correct_tense_count += 1
                elif not is_present_job and not is_past_verb and not is_present_verb:
                    # Ambiguous, give benefit of doubt
                    correct_tense_count += 1

        if total_analyzed == 0:
            return 1.0
        return correct_tense_count / total_analyzed
