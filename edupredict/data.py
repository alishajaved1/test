"""CSV loading, validation, and dataset summaries."""
from pathlib import Path
from typing import Any
import pandas as pd

EXPECTED_COLUMNS = [
    "StudentID", "Name", "Gender", "AttendanceRate", "StudyHoursPerWeek",
    "PreviousGrade", "ExtracurricularActivities", "ParentalSupport", "FinalGrade",
]
NUMERIC_COLUMNS = [
    "AttendanceRate", "StudyHoursPerWeek", "PreviousGrade",
    "ExtracurricularActivities", "FinalGrade",
]
IDENTIFIER_COLUMNS = ["StudentID", "Name"]

class DataValidationError(ValueError):
    """Raised when uploaded data cannot be used safely."""

def validate_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    errors, warnings = [], []
    if not isinstance(df, pd.DataFrame):
        raise DataValidationError("The uploaded content is not a valid table.")
    if df.empty:
        errors.append("The dataset contains no rows.")
    if len(df) > 100_000:
        errors.append("The dataset exceeds the 100,000-row limit.")
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        errors.append("Missing required columns: " + ", ".join(missing))
    if errors:
        raise DataValidationError(" ".join(errors))
    if df.columns.duplicated().any():
        errors.append("Duplicate column names are not allowed.")
    for col in NUMERIC_COLUMNS:
        numeric = pd.to_numeric(df[col], errors="coerce")
        if numeric.isna().any():
            warnings.append(f"{col} contains missing or non-numeric values.")
    for col in ["AttendanceRate", "PreviousGrade", "FinalGrade"]:
        vals = pd.to_numeric(df[col], errors="coerce").dropna()
        if ((vals < 0) | (vals > 100)).any():
            errors.append(f"{col} must be between 0 and 100.")
    hours = pd.to_numeric(df["StudyHoursPerWeek"], errors="coerce").dropna()
    if (hours < 0).any():
        errors.append("StudyHoursPerWeek cannot be negative.")
    if df.duplicated().any():
        warnings.append("Duplicate rows were found.")
    if df.isna().any().any():
        warnings.append("Some cells are empty; supported model pipelines may impute missing values.")
    if errors:
        raise DataValidationError(" ".join(errors))
    return {"rows": len(df), "columns": len(df.columns), "warnings": warnings, "errors": []}

def load_dataset(path: str | Path) -> pd.DataFrame:
    file = Path(path)
    if not file.exists():
        raise DataValidationError(f"Dataset not found: {file}. Add the sample CSV or upload your own.")
    try:
        df = pd.read_csv(file)
    except Exception as exc:
        raise DataValidationError("Could not read the CSV file. Check its encoding and delimiter.") from exc
    validate_dataframe(df)
    return df

def validate_upload(uploaded_file, max_size_mb: int = 5):
    name = getattr(uploaded_file, "name", "")
    if not name.lower().endswith(".csv"):
        raise DataValidationError("Please upload a .csv file.")
    raw = uploaded_file.getvalue()
    if len(raw) > max_size_mb * 1024 * 1024:
        raise DataValidationError(f"File exceeds the {max_size_mb} MB upload limit.")
    try:
        from io import BytesIO
        df = pd.read_csv(BytesIO(raw))
    except Exception as exc:
        raise DataValidationError("Could not parse this CSV file.") from exc
    report = validate_dataframe(df)
    return df, report

def get_dataset_statistics(df: pd.DataFrame) -> dict[str, Any]:
    def mean(col):
        return float(pd.to_numeric(df[col], errors="coerce").mean()) if col in df else 0.0
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "average_grade": mean("FinalGrade"),
        "average_attendance": mean("AttendanceRate"),
        "average_study_hours": mean("StudyHoursPerWeek"),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }

def classify_risk(grade: float) -> str:
    if grade < 70:
        return "High Risk"
    if grade < 85:
        return "Moderate"
    return "On Track"

def add_risk_column(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "FinalGrade" in out:
        out["RiskLevel"] = pd.to_numeric(out["FinalGrade"], errors="coerce").apply(
            lambda x: classify_risk(x) if pd.notna(x) else "Unknown"
        )
    return out

def get_numeric_features(df: pd.DataFrame, target: str = "FinalGrade") -> list[str]:
    excluded = set(IDENTIFIER_COLUMNS + [target])
    return [c for c in df.select_dtypes(include="number").columns if c not in excluded]

def filter_dataframe(df: pd.DataFrame, column: str, values: list) -> pd.DataFrame:
    if column not in df.columns:
        raise ValueError(f"Unknown column: {column}")
    return df[df[column].isin(values)].copy()

def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")
