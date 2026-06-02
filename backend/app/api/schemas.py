from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ATSFlagsSchema(BaseModel):
    tables_detected: bool
    columns_detected: bool
    images_detected: bool
    special_chars_ratio: float
    is_scanned_pdf: bool

class UploadResponse(BaseModel):
    resume_id: str
    filename: str
    word_count: int
    page_count: int
    ats_flags: ATSFlagsSchema
    preview_text: str
    warnings: List[str]

class FactorSchema(BaseModel):
    feature_name: str
    human_label: str
    shap_value: float
    impact_label: str
    category: str
    direction: str

class SuggestionSchema(BaseModel):
    category: str
    priority: str
    title: str
    message: str
    example_before: Optional[str] = None
    example_after: Optional[str] = None
    impact_estimate: str

class WaterfallStep(BaseModel):
    label: str
    value: float
    direction: str

class WaterfallData(BaseModel):
    base: float
    steps: List[WaterfallStep]
    final: float

class ScoreResponse(BaseModel):
    resume_id: str
    score_id: str
    overall_score: float
    ats_score: float
    content_score: float
    keyword_score: float
    semantic_score: float
    grade: str
    explanation_text: str
    positive_factors: List[FactorSchema]
    negative_factors: List[FactorSchema]
    suggestions: List[SuggestionSchema]
    keyword_gaps: List[str]
    waterfall_data: WaterfallData
    processing_time_ms: int
    scored_at: datetime

class ScoreRequest(BaseModel):
    job_description: Optional[str] = None
    target_role: str = "Software Engineer"
