from dataclasses import dataclass
from typing import Callable, Any
from app.features.schema import ATSFeatures, ContentFeatures, KeywordFeatures
from app.parsers.schemas import ParseResult

@dataclass
class Suggestion:
    id: str                     
    category: str               # "ats" | "content" | "keywords" | "format" | "structure"
    priority: str               # "high" | "medium" | "low"
    title: str                  
    message: str                
    example_before: str | None = None
    example_after: str | None = None
    impact_estimate: str = ""
    shap_impact: float = 0.0

class SuggestionEngine:
    def __init__(self):
        self.rules = self._get_rules()

    def _get_rules(self) -> list[dict]:
        return [
            # ATS RULES
            {
                "id": "remove-tables",
                "category": "format",
                "priority": "high",
                "title": "Remove tables — ATS cannot parse them",
                "message": "Many ATS systems struggle to read text inside tables. Convert them to plain text bullet points.",
                "example_before": "Experience in a 3-column table",
                "example_after": "Use bullet points under plain section headers",
                "impact_estimate": "+5 to +8 points",
                "condition": lambda a, c, k, p: p.ats_flags.tables_detected
            },
            {
                "id": "remove-images",
                "category": "format",
                "priority": "high",
                "title": "Remove all images and icons",
                "message": "Images and icons can disrupt the text flow for parsers. Use text-only indicators.",
                "example_before": "Headshot photo + skill icons",
                "example_after": "Text-only resume with no graphics",
                "impact_estimate": "+6 to +10 points",
                "condition": lambda a, c, k, p: p.ats_flags.images_detected
            },
            {
                "id": "single-column",
                "category": "format",
                "priority": "medium",
                "title": "Switch to single-column layout",
                "message": "Multi-column layouts are often read incorrectly (out of order) by older ATS.",
                "impact_estimate": "+3 to +5 points",
                "condition": lambda a, c, k, p: p.ats_flags.columns_detected
            },
            {
                "id": "add-linkedin",
                "category": "ats",
                "priority": "medium",
                "title": "Add LinkedIn profile URL",
                "message": "Recruiters expect to find your LinkedIn profile easily.",
                "impact_estimate": "+3 to +5 points",
                "condition": lambda a, c, k, p: not a.has_linkedin
            },
            {
                "id": "resume-too-short",
                "category": "structure",
                "priority": "high",
                "title": "Your resume is too short",
                "message": "Resumes under 300 words often lack enough detail to rank well for keywords.",
                "impact_estimate": "+5 to +12 points",
                "condition": lambda a, c, k, p: p.word_count < 300
            },
            {
                "id": "trim-pages",
                "category": "format",
                "priority": "medium",
                "title": "Trim to 2 pages maximum",
                "message": "Keep your resume concise. 3+ pages is usually too much for most roles.",
                "impact_estimate": "+3 to +6 points",
                "condition": lambda a, c, k, p: p.page_count > 2
            },
            # CONTENT RULES
            {
                "id": "add-quantification",
                "category": "content",
                "priority": "high",
                "title": "Add measurable numbers to every job",
                "message": "Quantifying your impact shows recruiters exactly what you achieved.",
                "example_before": "Improved application performance",
                "example_after": "Reduced page load time by 40%, improving user retention by 15%",
                "impact_estimate": "+8 to +15 points",
                "condition": lambda a, c, k, p: c.quantification_rate == 0
            },
            {
                "id": "increase-quantification",
                "category": "content",
                "priority": "medium",
                "title": "Quantify more bullet points",
                "message": "Aim to have at least 50% of your bullets include metrics or numbers.",
                "impact_estimate": "+5 to +10 points",
                "condition": lambda a, c, k, p: 0 < c.quantification_rate < 0.3
            },
            {
                "id": "use-action-verbs",
                "category": "content",
                "priority": "high",
                "title": "Start every bullet point with an action verb",
                "message": "Action verbs like 'Architected' or 'Led' make your accomplishments more impactful.",
                "example_before": "Was responsible for building microservices",
                "example_after": "Architected 8 microservices handling 50K requests/day",
                "impact_estimate": "+4 to +8 points",
                "condition": lambda a, c, k, p: c.starts_with_action_verb < 0.5
            },
            {
                "id": "add-summary",
                "category": "structure",
                "priority": "medium",
                "title": "Add a professional summary",
                "message": "A 2-3 sentence summary at the top helps frame your experience.",
                "impact_estimate": "+3 to +7 points",
                "condition": lambda a, c, k, p: not a.has_summary
            },
            # KEYWORD RULES
            {
                "id": "critical-keyword-gap",
                "category": "keywords",
                "priority": "high",
                "title": "Critical keyword gap",
                "message": "Your resume is missing major technical keywords from the job description.",
                "impact_estimate": "+10 to +20 points",
                "condition": lambda a, c, k, p: k.keyword_score < 40
            },
            {
                "id": "add-tech-keywords",
                "category": "keywords",
                "priority": "medium",
                "title": "Add job-specific technical keywords",
                "message": "Matching the terminology in the JD helps you pass initial filters.",
                "impact_estimate": "+5 to +12 points",
                "condition": lambda a, c, k, p: 40 <= k.keyword_score < 60
            }
        ]

    def get_suggestions(
        self, 
        ats: ATSFeatures, 
        content: ContentFeatures, 
        keyword: KeywordFeatures, 
        parse_result: ParseResult,
        shap_values: dict[str, float] | None = None
    ) -> list[Suggestion]:
        triggered = []
        for rule in self.rules:
            if rule["condition"](ats, content, keyword, parse_result):
                suggestion = Suggestion(
                    id=rule["id"],
                    category=rule["category"],
                    priority=rule["priority"],
                    title=rule["title"],
                    message=rule["message"],
                    example_before=rule.get("example_before"),
                    example_after=rule.get("example_after"),
                    impact_estimate=rule.get("impact_estimate", "")
                )
                triggered.append(suggestion)
        
        return self.prioritize(triggered, shap_values or {})

    def prioritize(self, suggestions: list[Suggestion], shap_values: dict[str, float], max_return: int = 8) -> list[Suggestion]:
        priority_map = {"high": 0, "medium": 1, "low": 2}
        
        for s in suggestions:
            # Simple mapping from rule ID to potential feature impact
            # In a real system, this would be more direct
            s.shap_impact = shap_values.get(s.id, 0.0)

        # Sort by priority rank, then by absolute SHAP impact if available
        suggestions.sort(key=lambda x: (priority_map.get(x.priority, 3), -abs(x.shap_impact)))
        
        return suggestions[:max_return]
