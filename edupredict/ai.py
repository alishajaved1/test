"""Gemini integration via Google's official google-genai SDK."""
import json
from edupredict.config import AppConfig, get_config

class GeminiError(RuntimeError):
    pass

_ALLOWED_MODELS = {"gemini-3.5-flashlite", "gemini-3.1-flashlite"}

def _client(config):
    if not config.gemini_api_key:
        raise GeminiError("Gemini is not configured. Add GEMINI_API_KEY to your environment.")
    if config.gemini_model not in _ALLOWED_MODELS:
        raise GeminiError(f"Model {config.gemini_model!r} is not in the approved model list. Set GEMINI_MODEL to an approved model.")
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=config.gemini_api_key,
            http_options=types.HttpOptions(timeout=config.gemini_timeout_seconds * 1000))
        return client
    except Exception as exc:
        raise GeminiError("Could not initialise the Gemini SDK. Check installation and configuration.") from exc

def _generate(prompt, config=None):
    config = config or get_config()
    client = _client(config)
    try:
        response = client.models.generate_content(
            model=config.gemini_model,
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": config.max_ai_output_tokens},
        )
        text = getattr(response, "text", None)
        if not text:
            raise GeminiError("Gemini returned an empty response. Try again.")
        return text.strip()
    except GeminiError:
        raise
    except Exception as exc:
        msg = str(exc).lower()
        if "api key" in msg or "unauthorized" in msg or "permission" in msg:
            raise GeminiError("Gemini authentication failed. Check GEMINI_API_KEY and API access.") from exc
        if "quota" in msg or "rate" in msg:
            raise GeminiError("Gemini request limit reached. Wait and try again.") from exc
        raise GeminiError("Gemini request failed. Check network access, model availability, and API settings.") from exc

def test_gemini_connection(config=None):
    text = _generate("Reply with exactly: EduPredict AI connection successful.", config)
    return text

def anonymize_student_record(record):
    allowed = {"AttendanceRate", "StudyHoursPerWeek", "PreviousGrade",
               "ExtracurricularActivities", "ParentalSupport", "Gender", "LearningGoals"}
    result = {}
    for key, value in record.items():
        if key in allowed:
            if isinstance(value, (str, int, float, bool)) or value is None:
                result[key] = str(value)[:500] if isinstance(value, str) else value
    return result

def generate_study_recommendations(record, config=None):
    safe_record = anonymize_student_record(record)
    prompt = (
        "You are an educational study coach. Provide supportive, practical, non-diagnostic "
        "advice. Do not make high-stakes judgments. Use only the anonymized academic context below. "
        "Return valid JSON with keys summary (string), strengths (array of strings), "
        "focus_areas (array of strings), weekly_plan (array of strings), encouragement (string). "
        "Keep each item concise. Context: " + json.dumps(safe_record, ensure_ascii=False)
    )
    raw = _generate(prompt, config)
    try:
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start:end+1])
        for key in ("strengths", "focus_areas", "weekly_plan"):
            if not isinstance(data.get(key), list):
                data[key] = []
        for key in ("summary", "encouragement"):
            if not isinstance(data.get(key), str):
                data[key] = ""
        return data
    except Exception:
        return {"summary": raw[:1500], "strengths": [], "focus_areas": [],
                "weekly_plan": [], "encouragement": "Choose one small action and practise consistently."}

def answer_study_question(question, config=None):
    question = str(question).strip()
    if not question:
        raise GeminiError("Enter a study question first.")
    if len(question) > 1500:
        question = question[:1500]
    return _generate("Act as a supportive study coach. Give a practical, concise answer. "
                     "Avoid medical, legal, or high-stakes claims. Question: " + question, config)
