"""
Cartly Customer Churn Prediction Module
Trains and compares Logistic Regression and Random Forest models.
Evaluates using Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC, and Confusion Matrix.
Persists models with Joblib and generates individual risk scores.
"""

import os
from typing import Dict, Any, Tuple, Optional, List
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
    roc_curve,
    precision_recall_curve
)

from ..features.churn_features import FEATURE_COLUMNS

DEFAULT_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "models")
DEFAULT_MODEL_PATH = os.path.join(DEFAULT_MODEL_DIR, "cartly_churn_model.joblib")


def evaluate_model_performance(
    model: Any,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """Calculate comprehensive evaluation metrics for a trained classifier."""
    # Predict probabilities
    if hasattr(model, "predict_proba"):
        y_proba = model.predict_proba(X_test)[:, 1]
    else:
        y_proba = model.decision_function(X_test)

    y_pred = (y_proba >= threshold).astype(int)

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))

    try:
        roc_auc = float(roc_auc_score(y_test, y_proba))
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = float(average_precision_score(y_test, y_proba))
    except Exception:
        pr_auc = 0.0

    cm = confusion_matrix(y_test, y_pred).tolist()

    # ROC curve points
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    # PR curve points
    precision_pts, recall_pts, _ = precision_recall_curve(y_test, y_proba)

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "confusion_matrix": cm,
        "y_true": y_test.tolist(),
        "y_proba": y_proba.tolist(),
        "fpr": fpr.tolist(),
        "tpr": tpr.tolist(),
        "precision_pts": precision_pts.tolist(),
        "recall_pts": recall_pts.tolist()
    }


def train_and_compare_models(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    save_best_model: bool = True,
    model_save_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Train Logistic Regression and Random Forest on train_df and evaluate on test_df.
    Returns full evaluation metrics, feature importances, and model comparison.
    """
    features = feature_cols or FEATURE_COLUMNS

    # Ensure feature columns exist
    X_train = train_df[features].fillna(0)
    y_train = train_df["is_churned"].astype(int)

    X_test = test_df[features].fillna(0)
    y_test = test_df["is_churned"].astype(int)

    # 1. Logistic Regression Pipeline with StandardScaler
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_metrics = evaluate_model_performance(lr_pipeline, X_test, y_test)

    # Logistic Regression feature coefficients
    lr_coefs = lr_pipeline.named_steps["classifier"].coef_[0]
    lr_importance = pd.DataFrame({
        "feature": features,
        "importance": np.abs(lr_coefs),
        "raw_coefficient": lr_coefs
    }).sort_values("importance", ascending=False).to_dict(orient="records")

    # 2. Random Forest Classifier
    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_split=10,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_classifier.fit(X_train, y_train)
    rf_metrics = evaluate_model_performance(rf_classifier, X_test, y_test)

    # Random Forest feature importance
    rf_importances = rf_classifier.feature_importances_
    rf_importance = pd.DataFrame({
        "feature": features,
        "importance": rf_importances
    }).sort_values("importance", ascending=False).to_dict(orient="records")

    # Determine best model based on F1-Score and ROC-AUC
    if rf_metrics["f1_score"] >= lr_metrics["f1_score"]:
        best_name = "Random Forest"
        best_model = rf_classifier
        best_metrics = rf_metrics
    else:
        best_name = "Logistic Regression"
        best_model = lr_pipeline
        best_metrics = lr_metrics

    result = {
        "best_model_name": best_name,
        "features": features,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "train_churn_rate": float(y_train.mean()),
        "test_churn_rate": float(y_test.mean()),
        "logistic_regression": {
            "metrics": lr_metrics,
            "feature_importance": lr_importance
        },
        "random_forest": {
            "metrics": rf_metrics,
            "feature_importance": rf_importance
        }
    }

    if save_best_model:
        save_p = model_save_path or DEFAULT_MODEL_PATH
        os.makedirs(os.path.dirname(save_p), exist_ok=True)
        bundle = {
            "model_name": best_name,
            "model": best_model,
            "features": features,
            "metrics": best_metrics,
            "lr_model": lr_pipeline,
            "rf_model": rf_classifier,
            "full_comparison": result
        }
        joblib.dump(bundle, save_p)
        result["saved_path"] = save_p

    return result


def load_model_bundle(model_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load persisted model bundle from disk."""
    p = model_path or DEFAULT_MODEL_PATH
    if not os.path.exists(p):
        return None
    try:
        return joblib.load(p)
    except Exception:
        return None


def assign_risk_tier(prob: float, low_cut: float = 0.35, high_cut: float = 0.70) -> str:
    """Assign risk tier based on churn probability."""
    if prob >= high_cut:
        return "High"
    elif prob >= low_cut:
        return "Medium"
    else:
        return "Low"


def predict_customer_churn_probabilities(
    model_bundle: Dict[str, Any],
    features_df: pd.DataFrame,
    low_cut: float = 0.35,
    high_cut: float = 0.70
) -> pd.DataFrame:
    """
    Generate churn probability predictions and risk levels for customer features.
    """
    if features_df.empty or not model_bundle:
        return pd.DataFrame()

    model = model_bundle["model"]
    features = model_bundle.get("features", FEATURE_COLUMNS)

    X = features_df[features].fillna(0)
    probs = model.predict_proba(X)[:, 1]

    pred_df = features_df.copy()
    pred_df["churn_probability"] = probs.round(4)
    pred_df["predicted_churn"] = (pred_df["churn_probability"] >= 0.5).astype(int)
    pred_df["risk_tier"] = pred_df["churn_probability"].apply(lambda p: assign_risk_tier(p, low_cut, high_cut))

    return pred_df
