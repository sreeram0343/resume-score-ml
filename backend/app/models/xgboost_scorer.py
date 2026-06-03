import pickle
from dataclasses import dataclass
from typing import Any

import numpy as np
import xgboost as xgb
from sklearn.isotonic import IsotonicRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, KFold
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

@dataclass
class TrainingResult:
    mae: float
    rmse: float
    r2: float
    feature_importances: dict[str, float]
    cv_scores: list[float]

class ResumeScorer:
    def __init__(self):
        self.model = xgb.XGBRegressor(
            n_estimators=500,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective="reg:squarederror",
            eval_metric="mae",
            early_stopping_rounds=50,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.calibrator = IsotonicRegression(out_of_bounds="clip")
        self.feature_names = []
        self._is_fitted = False

    def train(self, X: np.ndarray, y: np.ndarray, feature_names: list[str]) -> TrainingResult:
        self.feature_names = feature_names
        
        # 5-fold cross-validation
        kf = KFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = []
        for train_idx, val_idx in kf.split(X):
            X_t, X_v = X[train_idx], X[val_idx]
            y_t, y_v = y[train_idx], y[val_idx]
            
            # Temporary model for CV
            temp_scaler = StandardScaler()
            X_t_s = temp_scaler.fit_transform(X_t)
            X_v_s = temp_scaler.transform(X_v)
            
            temp_model = xgb.XGBRegressor(**self.model.get_params())
            temp_model.fit(X_t_s, y_t, eval_set=[(X_v_s, y_v)], verbose=False)
            
            preds = temp_model.predict(X_v_s)
            cv_scores.append(mean_absolute_error(y_v, preds))

        # Final training split
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        self.model.fit(
            X_train_scaled, 
            y_train, 
            eval_set=[(X_val_scaled, y_val)], 
            verbose=False
        )
        
        # Calibration
        raw_preds = self.model.predict(X_train_scaled)
        self.calibrator.fit(raw_preds, y_train)
        
        self._is_fitted = True
        
        # Evaluation
        y_pred = self.predict(X_val)
        mae = mean_absolute_error(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        r2 = r2_score(y_val, y_pred)
        
        return TrainingResult(
            mae=mae,
            rmse=rmse,
            r2=r2,
            feature_importances=self.get_feature_importance(),
            cv_scores=cv_scores
        )

    def predict(self, feature_vector: np.ndarray) -> float:
        if not self._is_fitted:
            raise ValueError("Model is not fitted yet.")
        
        if feature_vector.ndim == 1:
            feature_vector = feature_vector.reshape(1, -1)
            
        scaled = self.scaler.transform(feature_vector)
        raw_pred = self.model.predict(scaled)
        calibrated = self.calibrator.transform(raw_pred)
        return float(np.clip(calibrated[0], 0, 100))

    def predict_with_fallback(self, feature_vector: np.ndarray, scores: dict[str, float]) -> float:
        """Fallback to weighted average if model is not available."""
        if self._is_fitted:
            return self.predict(feature_vector)
        
        # 0.35*ats + 0.25*content + 0.25*keyword + 0.15*semantic
        ats = scores.get("ats", 0.0)
        content = scores.get("content", 0.0)
        keyword = scores.get("keyword", 0.0)
        semantic = scores.get("semantic", 0.0)
        
        fallback_score = (0.35 * ats) + (0.25 * content) + (0.25 * keyword) + (0.15 * semantic)
        return float(fallback_score)

    def save(self, path: str):
        artifacts = {
            "model": self.model,
            "scaler": self.scaler,
            "calibrator": self.calibrator,
            "feature_names": self.feature_names,
            "is_fitted": self._is_fitted
        }
        with open(path, "wb") as f:
            pickle.dump(artifacts, f)

    @classmethod
    def load(cls, path: str):
        with open(path, "rb") as f:
            artifacts = pickle.load(f)
        
        instance = cls()
        instance.model = artifacts["model"]
        instance.scaler = artifacts["scaler"]
        instance.calibrator = artifacts["calibrator"]
        instance.feature_names = artifacts["feature_names"]
        instance._is_fitted = artifacts["is_fitted"]
        return instance

    def get_feature_importance(self) -> dict[str, float]:
        if not self._is_fitted:
            return {}
        
        importances = self.model.get_booster().get_score(importance_type="gain")
        # XGBoost importance keys are f0, f1, etc. if feature names weren't passed to DMatrix
        # But we can map them back using self.feature_names
        
        total_gain = sum(importances.values())
        norm_importances = {}
        
        for k, v in importances.items():
            # k is usually 'f0', 'f1', ...
            idx = int(k[1:])
            if idx < len(self.feature_names):
                name = self.feature_names[idx]
                norm_importances[name] = v / total_weight if 'total_weight' in locals() else v
        
        # Proper normalization
        total = sum(norm_importances.values()) or 1.0
        final_importances = {k: v / total for k, v in norm_importances.items()}
        
        return dict(sorted(final_importances.items(), key=lambda x: x[1], reverse=True))
