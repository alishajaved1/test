import pandas as pd
import pytest
from edupredict.data import validate_dataframe, classify_risk, add_risk_column, DataValidationError
from edupredict.model import train_and_evaluate, predict_grade
from edupredict.auth import validate_email, validate_password

SAMPLE = pd.DataFrame({
    "StudentID": ["a","b","c","d","e"],
    "Name": ["A","B","C","D","E"],
    "Gender": ["F","M","F","M","F"],
    "AttendanceRate": [90,70,60,95,80],
    "StudyHoursPerWeek": [10,5,3,12,8],
    "PreviousGrade": [85,68,55,90,76],
    "ExtracurricularActivities": [1,0,0,1,1],
    "ParentalSupport": ["High","Medium","Low","High","Medium"],
    "FinalGrade": [88,70,57,94,78],
})

def test_validate_dataframe():
    assert validate_dataframe(SAMPLE)["rows"] == 5

def test_required_columns():
    with pytest.raises(DataValidationError):
        validate_dataframe(pd.DataFrame({"FinalGrade": [50]}))

def test_risk_bands():
    assert classify_risk(60) == "High Risk"
    assert classify_risk(75) == "Moderate"
    assert classify_risk(90) == "On Track"

def test_add_risk_column_does_not_mutate_input():
    result = add_risk_column(SAMPLE)
    assert "RiskLevel" in result.columns
    assert "RiskLevel" not in SAMPLE.columns

def test_model_eval_and_prediction():
    result = train_and_evaluate(SAMPLE)
    assert result["mae"] >= 0
    prediction = predict_grade(SAMPLE, {"AttendanceRate": 85, "StudyHoursPerWeek": 8, "PreviousGrade": 75})
    assert 0 <= prediction["predicted_grade"] <= 100

def test_auth_validators():
    assert validate_email("student@example.com")
    assert not validate_email("not-an-email")
    assert validate_password("study1234")[0]
    assert not validate_password("short")
