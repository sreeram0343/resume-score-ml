import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from app.features.keyword_features import KeywordFeatureExtractor
from app.features.semantic_features import SemanticFeatureExtractor

def test_keyword_extractor_defaults():
    resume = "I am a Python developer with experience in Docker and AWS."
    features = KeywordFeatureExtractor.extract(resume, "Software Engineer")
    
    assert "Python" in features.matched_keywords
    assert "AWS" in features.matched_keywords
    assert "Docker" in features.matched_keywords
    assert features.keyword_score > 0
    assert features.coverage_by_category["languages"] > 0

def test_keyword_extractor_with_jd():
    resume = "Expert in React and FastAPI."
    jd = "We need a React developer who knows FastAPI."
    features = KeywordFeatureExtractor.extract(resume, "Software Engineer", job_description=jd)
    
    # JD keywords should be extracted and matched
    assert any("react" in k.lower() for k in features.matched_keywords)
    assert any("fastapi" in k.lower() for k in features.matched_keywords)

@patch("app.features.semantic_features.SentenceTransformer")
def test_semantic_extractor(mock_transformer_class):
    # Mock model and its encode method
    mock_model = MagicMock()
    mock_transformer_class.return_value = mock_model
    
    # Return dummy embeddings (normalized to avoid similarity issues)
    def mock_encode(text):
        return np.array([1.0, 0.0, 0.0])
    mock_model.encode.side_effect = mock_encode
    
    # Reset singleton model for test
    SemanticFeatureExtractor._model = None
    
    resume = "Experienced ML engineer"
    features = SemanticFeatureExtractor.extract(resume, "Machine Learning Engineer")
    
    assert features.industry_fit == 1.0 # Due to identical mock embeddings
    assert features.semantic_score > 0
    mock_model.encode.assert_called()

def test_semantic_extractor_fallback():
    # Force model load failure
    with patch("app.features.semantic_features.SentenceTransformer", side_effect=Exception("Failed")):
        SemanticFeatureExtractor._model = None
        features = SemanticFeatureExtractor.extract("some text", "Software Engineer")
        assert features.semantic_score == 50.0
