"""
ML Preprocessing: Feature Transformers, Encoders, Imputers, and Clinical Scalers.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler


class ClinicalFeatureTransformer:
    """Transforms raw dictionary health records into scaled NumPy feature matrices."""

    def __init__(self, feature_names: List[str]):
        self.feature_names = feature_names
        self.scaler = StandardScaler()
        self.is_fitted = False

    def fit(self, X: np.ndarray) -> 'ClinicalFeatureTransformer':
        """Fit the standard scaler on training data."""
        self.scaler.fit(X)
        self.is_fitted = True
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Scale features using fitted scaler."""
        if not self.is_fitted:
            return X
        return self.scaler.transform(X)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """Fit and transform feature matrix."""
        self.fit(X)
        return self.transform(X)

    @staticmethod
    def extract_features_from_dict(record: Dict[str, Any], required_features: List[str]) -> np.ndarray:
        """Extract ordered numeric vector from dictionary with default fallbacks."""
        vector = []
        for feat in required_features:
            val = record.get(feat, 0.0)
            if isinstance(val, (int, float)):
                vector.append(float(val))
            elif isinstance(val, bool):
                vector.append(1.0 if val else 0.0)
            elif isinstance(val, str):
                # Simple string encodings
                val_lower = val.lower()
                if val_lower in ["male", "yes", "true", "heavy", "high", "active"]:
                    vector.append(1.0)
                elif val_lower in ["moderate", "former", "occasional"]:
                    vector.append(0.5)
                else:
                    vector.append(0.0)
            else:
                vector.append(0.0)

        return np.array(vector, dtype=np.float64).reshape(1, -1)
