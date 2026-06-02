import re

class SkillsExtractor:
    SKILL_CATEGORIES = {
        "languages": ["python", "java", "javascript", "typescript", "c++", "ruby", "go", "sql"],
        "frameworks": ["react", "angular", "vue", "django", "fastapi", "flask", "spring", "pytorch", "tensorflow"],
        "tools": ["git", "docker", "kubernetes", "aws", "azure", "gcp", "linux", "jenkins"],
        "soft_skills": ["leadership", "communication", "teamwork", "problem solving", "agile"]
    }

    @classmethod
    def extract(cls, text: str) -> list[str]:
        # Split on common separators
        raw_skills = re.split(r'[,|•\n*]', text)
        clean_skills = set()
        
        for s in raw_skills:
            s = s.strip()
            if s and len(s) < 50: # Avoid long sentences being treated as skills
                clean_skills.add(s)

        return sorted(list(clean_skills))

    @classmethod
    def classify(cls, skills: list[str]) -> dict[str, list[str]]:
        classified = {cat: [] for cat in cls.SKILL_CATEGORIES}
        classified["other"] = []

        for skill in skills:
            found = False
            for cat, seeds in cls.SKILL_CATEGORIES.items():
                if any(seed.lower() in skill.lower() for seed in seeds):
                    classified[cat].append(skill)
                    found = True
                    break
            if not found:
                classified["other"].append(skill)
        
        return classified
