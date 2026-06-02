import pytest
import numpy as np
import xgboost as xgb
from app.models.explainer import ResumeSHAPExplainer

def test_shap_explainer():
    # Create dummy model and data
    X = np.random.rand(100, 20)
    y = np.random.rand(100) * 100
    model = xgb.XGBRegressor(n_estimators=10, max_depth=3)
    model.fit(X, y)
    
    feature_names = [f"feat_{i}" for i in range(20)]
    feature_names[0] = "has_email"
    feature_names[1] = "quantification_rate"
    
    explainer = ResumeSHAPExplainer()
    explainer.initialize(model, feature_names)
    
    test_vector = np.random.rand(20)
    predicted = float(model.predict(test_vector.reshape(1, -1))[0])
    
    explanation = explainer.explain(test_vector, predicted)
    
    assert explanation.base_score > 0
    assert len(explanation.positive_factors) <= 5
    assert len(explanation.negative_factors) <= 5
    
    for f in explanation.positive_factors:
        assert f.shap_value > 0
        assert f.direction == "positive"
        
    for f in explanation.negative_factors:
        assert f.shap_value < 0
        assert f.direction == "negative"
        
    # Check waterfall approximation
    step_sum = sum(s["value"] for s in explanation.waterfall_data["steps"])
    assert np.isclose(explanation.waterfall_data["base"] + step_sum, explanation.waterfall_data["final"], atol=1.0)
