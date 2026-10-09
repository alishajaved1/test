"""Baseline Ridge regression model with leave-one-out cross-validation."""
from typing import Any
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import LeaveOneOut, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from edupredict.data import classify_risk

TARGET = "FinalGrade"
EXCLUDED = {"StudentID", "Name", TARGET}

def _prepare_features(df: pd.DataFrame):
    if TARGET not in df:
        raise ValueError("Dataset must contain FinalGrade.")
    y = pd.to_numeric(df[TARGET], errors="coerce")
    valid = y.notna()
    frame = df.loc[valid].drop(columns=[c for c in EXCLUDED if c in df.columns]).copy()
    y = y.loc[valid].astype(float)
    if len(frame) < 3:
        raise ValueError("At least 3 rows with a numeric FinalGrade are required.")
    if frame.shape[1] == 0:
        raise ValueError("No usable feature columns remain after excluding identifiers and target.")
    numeric = frame.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical = [c for c in frame.columns if c not in numeric]
    transformers = []
    if numeric:
        transformers.append(("num", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ]), numeric))
    if categorical:
        transformers.append(("cat", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical))
    preprocessor = ColumnTransformer(transformers)
    pipeline = Pipeline([("preprocessor", preprocessor), ("model", Ridge(alpha=1.0))])
    return frame, y, pipeline

def train_and_evaluate(df: pd.DataFrame) -> dict[str, Any]:
    X, y, pipeline = _prepare_features(df)
    if len(X) < 3:
        raise ValueError("At least 3 complete target values are required.")
    try:
        predicted = cross_val_predict(pipeline, X, y, cv=LeaveOneOut())
    except Exception as exc:
        raise ValueError(f"Model evaluation failed: {exc}") from exc
    mae = float(mean_absolute_error(y, predicted))
    r2 = float(r2_score(y, predicted)) if len(y) > 1 and float(np.var(y)) > 0 else None
    predictions = pd.DataFrame({
        "ActualGrade": y.to_numpy(),
        "PredictedGrade": np.clip(predicted, 0, 100),
        "Error": y.to_numpy() - predicted,
    })
    pipeline.fit(X, y)
    return {"pipeline": pipeline, "mae": mae, "r2": r2, "predictions": predictions,
            "features": list(X.columns), "method": "Ridge regression + Leave-One-Out CV"}

def predict_grade(df: pd.DataFrame, inputs: dict[str, Any]) -> dict[str, Any]:
    X, y, pipeline = _prepare_features(df)
    row = {}
    for col in X.columns:
        row[col] = inputs.get(col, X[col].mode(dropna=True).iloc[0] if not X[col].mode(dropna=True).empty else np.nan)
    pipeline.fit(X, y)
    prediction = float(np.clip(pipeline.predict(pd.DataFrame([row], columns=X.columns))[0], 0, 100))
    return {"predicted_grade": prediction, "risk_level": classify_risk(prediction),
            "model_method": "Ridge regression", "disclaimer": "Experimental estimate, not a guarantee."}

def get_model_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {"method": result.get("method", "Unknown"), "mae": result.get("mae"),
            "r2": result.get("r2"), "evaluated_rows": len(result.get("predictions", []))}
