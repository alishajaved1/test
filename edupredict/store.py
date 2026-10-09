"""User-scoped prediction and AI history, with SQLite demo fallback."""
import json, sqlite3, uuid
from pathlib import Path
from datetime import datetime, timezone
from edupredict.config import AppConfig, get_config

class HistoryStore:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or get_config()
        self.use_cloud = self.config.supabase_configured and self.config.supabase_url_valid
        self._supabase = None
        if self.use_cloud:
            try:
                from supabase import create_client
                self._supabase = create_client(self.config.supabase_url, self.config.supabase_anon_key)
            except Exception:
                self.use_cloud = False
        if not self.use_cloud:
            path = Path(self.config.database_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._init_sqlite()

    def _connect(self):
        return sqlite3.connect(self.config.database_path)

    def _init_sqlite(self):
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE, user_id TEXT NOT NULL,
                created_at TEXT NOT NULL, student_label TEXT, predicted_grade REAL NOT NULL,
                risk_level TEXT NOT NULL, inputs_json TEXT, model_method TEXT, notes TEXT)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS ai_chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE, user_id TEXT NOT NULL,
                created_at TEXT NOT NULL, student_label TEXT, prompt TEXT, response TEXT, context_json TEXT)""")

    def save_prediction(self, user_id, student_label, predicted_grade, risk_level, inputs,
                        model_method="Ridge regression", notes="", event_id=None):
        event_id = event_id or str(uuid.uuid4())
        record = {"event_id": event_id, "user_id": str(user_id),
                  "created_at": datetime.now(timezone.utc).isoformat(),
                  "student_label": student_label, "predicted_grade": float(predicted_grade),
                  "risk_level": risk_level, "inputs_json": inputs, "model_method": model_method, "notes": notes}
        if self.use_cloud and self._supabase:
            try:
                self._supabase.table("prediction_history").upsert(record, on_conflict="event_id").execute()
                return True
            except Exception:
                return False
        try:
            with self._connect() as conn:
                conn.execute("""INSERT OR IGNORE INTO prediction_history
                    (event_id,user_id,created_at,student_label,predicted_grade,risk_level,inputs_json,model_method,notes)
                    VALUES (:event_id,:user_id,:created_at,:student_label,:predicted_grade,:risk_level,:inputs_json,:model_method,:notes)""",
                    {**record, "inputs_json": json.dumps(inputs, ensure_ascii=False)})
            return True
        except Exception:
            return False

    def get_predictions(self, user_id, limit=100):
        if self.use_cloud and self._supabase:
            try:
                response = self._supabase.table("prediction_history").select(
                    "event_id,created_at,student_label,predicted_grade,risk_level,inputs_json,model_method,notes"
                ).eq("user_id", str(user_id)).order("created_at", desc=True).limit(limit).execute()
                return response.data or []
            except Exception:
                return []
        with self._connect() as conn:
            rows = conn.execute("""SELECT event_id,created_at,student_label,predicted_grade,risk_level,
                inputs_json,model_method,notes FROM prediction_history WHERE user_id=?
                ORDER BY created_at DESC LIMIT ?""", (str(user_id), int(limit))).fetchall()
        keys = ["event_id","created_at","student_label","predicted_grade","risk_level","inputs_json","model_method","notes"]
        output = []
        for row in rows:
            item = dict(zip(keys, row))
            try: item["inputs_json"] = json.loads(item["inputs_json"] or "{}")
            except Exception: pass
            output.append(item)
        return output

    def clear_predictions(self, user_id):
        if self.use_cloud and self._supabase:
            try:
                self._supabase.table("prediction_history").delete().eq("user_id", str(user_id)).execute()
                return
            except Exception:
                return
        with self._connect() as conn:
            conn.execute("DELETE FROM prediction_history WHERE user_id=?", (str(user_id),))

    def save_chat(self, user_id, prompt, response, context=None, student_label="", event_id=None):
        event_id = event_id or str(uuid.uuid4())
        record = {"event_id": event_id, "user_id": str(user_id),
                  "created_at": datetime.now(timezone.utc).isoformat(), "student_label": student_label,
                  "prompt": prompt, "response": response, "context_json": context or {}}
        if self.use_cloud and self._supabase:
            try:
                self._supabase.table("ai_chat_history").upsert(record, on_conflict="event_id").execute()
                return True
            except Exception:
                return False
        try:
            with self._connect() as conn:
                conn.execute("""INSERT OR IGNORE INTO ai_chat_history
                    (event_id,user_id,created_at,student_label,prompt,response,context_json)
                    VALUES (:event_id,:user_id,:created_at,:student_label,:prompt,:response,:context_json)""",
                    {**record, "context_json": json.dumps(context or {})})
            return True
        except Exception:
            return False
