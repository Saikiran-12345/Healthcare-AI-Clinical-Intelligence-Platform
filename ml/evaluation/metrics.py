"""
ML Evaluation Metrics and Diagnostic Model Comparison Reports.
Calculates Accuracy, Precision, Recall, F1 Score, ROC-AUC, and Confusion Matrix.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import cross_val_score


class ModelEvaluator:
    """Computes comprehensive evaluation metrics for classification models."""

    @staticmethod
    def evaluate_model(model: Any, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Compute full suite of classification metrics."""
        y_pred = model.predict(X_test)

        # Probabilities for ROC-AUC if supported
        try:
            y_prob = model.predict_proba(X_test)[:, 1]
            roc_auc = round(float(roc_auc_score(y_test, y_prob)), 4)
        except Exception:
            roc_auc = 0.0

        acc = round(float(accuracy_score(y_test, y_pred)), 4)
        prec = round(float(precision_score(y_test, y_pred, zero_division=0)), 4)
        rec = round(float(recall_score(y_test, y_pred, zero_division=0)), 4)
        f1 = round(float(f1_score(y_test, y_pred, zero_division=0)), 4)
        cm = confusion_matrix(y_test, y_pred).tolist()

        return {
            "accuracy": acc,
            "accuracy_pct": round(acc * 100, 2),
            "precision": prec,
            "recall": rec,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "confusion_matrix": cm,
            "true_negatives": cm[0][0] if len(cm) > 0 else 0,
            "false_positives": cm[0][1] if len(cm) > 0 else 0,
            "false_negatives": cm[1][0] if len(cm) > 1 else 0,
            "true_positives": cm[1][1] if len(cm) > 1 else 0,
        }

    @staticmethod
    def evaluate_cross_validation(model: Any, X: np.ndarray, y: np.ndarray, cv: int = 5) -> Dict[str, Any]:
        """Perform k-fold cross-validation and compute mean/std accuracy."""
        scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
        return {
            "cv_folds": cv,
            "mean_accuracy": round(float(np.mean(scores)), 4),
            "std_accuracy": round(float(np.std(scores)), 4),
            "fold_scores": [round(float(s), 4) for s in scores],
        }
