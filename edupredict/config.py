"""Central configuration. Secrets are read from environment or Streamlit secrets."""
from dataclasses import dataclass
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def _read_setting(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name, None)
        if value is not None and str(value).strip():
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, default).strip()

@dataclass(frozen=True)
class AppConfig:
    app_name: str = "EduPredict AI"
    app_version: str = "1.0.0"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flashlite"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    data_path: str = "data/student_performance.csv"
    database_path: str = "data/edupredict_demo.sqlite3"
    gemini_timeout_seconds: int = 20
    max_upload_size_mb: int = 5
    max_ai_output_tokens: int = 700

    @property
    def gemini_configured(self):
        return bool(self.gemini_api_key)

    @property
    def supabase_configured(self):
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def supabase_url_valid(self):
        return self.supabase_url.startswith("https://") and ".supabase.co" in self.supabase_url

    @property
    def gemini_model_valid(self):
        return self.gemini_model in {"gemini-3.5-flashlite", "gemini-3.1-flashlite"}

def get_config() -> AppConfig:
    def integer(name, default, low, high):
        try:
            return max(low, min(high, int(_read_setting(name, str(default)))))
        except (TypeError, ValueError):
            return default
    return AppConfig(
        gemini_api_key=_read_setting("GEMINI_API_KEY"),
        gemini_model=_read_setting("GEMINI_MODEL", "gemini-3.5-flashlite"),
        supabase_url=_read_setting("SUPABASE_URL"),
        supabase_anon_key=_read_setting("SUPABASE_ANON_KEY"),
        data_path=_read_setting("DATA_PATH", "data/student_performance.csv"),
        database_path=_read_setting("DATABASE_PATH", "data/edupredict_demo.sqlite3"),
        gemini_timeout_seconds=integer("GEMINI_TIMEOUT_SECONDS", 20, 5, 60),
        max_upload_size_mb=integer("MAX_UPLOAD_SIZE_MB", 5, 1, 25),
        max_ai_output_tokens=integer("MAX_AI_OUTPUT_TOKENS", 700, 100, 2000),
    )
