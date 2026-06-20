import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  demo_key TEXT, display_name TEXT NOT NULL DEFAULT '当前学习者',
  is_active INTEGER NOT NULL DEFAULT 0,
  major TEXT NOT NULL, grade TEXT NOT NULL, knowledge_level TEXT NOT NULL,
  learning_goal TEXT NOT NULL, weak_points TEXT NOT NULL,
  learning_style TEXT NOT NULL, resource_preference TEXT NOT NULL,
  mistake_history TEXT NOT NULL, source_text TEXT NOT NULL,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL, title TEXT NOT NULL, file_type TEXT NOT NULL,
  size INTEGER NOT NULL, chunk_count INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS document_chunks (
  id TEXT PRIMARY KEY, document_id INTEGER NOT NULL, title TEXT NOT NULL,
  content TEXT NOT NULL, position INTEGER NOT NULL,
  FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS resources (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topic TEXT NOT NULL, profile_id INTEGER, status TEXT NOT NULL,
  content TEXT NOT NULL, review TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS evaluations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  resource_id INTEGER NOT NULL, profile_id INTEGER, score REAL NOT NULL,
  weak_points TEXT NOT NULL, suggestions TEXT NOT NULL,
  detail TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER, role TEXT NOT NULL, content TEXT NOT NULL, citations TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS learning_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER, verb TEXT NOT NULL, object_type TEXT NOT NULL,
  object_id TEXT, result TEXT NOT NULL, context TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS mastery_records (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER NOT NULL, knowledge_point TEXT NOT NULL,
  mastery REAL NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
  correct_count INTEGER NOT NULL DEFAULT 0, last_score REAL NOT NULL DEFAULT 0,
  updated_at TEXT NOT NULL,
  UNIQUE(profile_id, knowledge_point)
);
CREATE TABLE IF NOT EXISTS resource_feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER NOT NULL, resource_id INTEGER NOT NULL,
  rating INTEGER NOT NULL, comment TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  UNIQUE(profile_id, resource_id)
);
CREATE TABLE IF NOT EXISTS learning_tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  profile_id INTEGER NOT NULL, resource_id INTEGER NOT NULL,
  task_type TEXT NOT NULL, title TEXT NOT NULL, description TEXT NOT NULL,
  estimated_minutes INTEGER NOT NULL DEFAULT 10,
  status TEXT NOT NULL DEFAULT 'pending', order_index INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, completed_at TEXT,
  UNIQUE(resource_id, task_type)
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(get_settings().database_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)
        profile_columns = {row["name"] for row in conn.execute("PRAGMA table_info(profiles)").fetchall()}
        if "demo_key" not in profile_columns:
            conn.execute("ALTER TABLE profiles ADD COLUMN demo_key TEXT")
        if "display_name" not in profile_columns:
            conn.execute("ALTER TABLE profiles ADD COLUMN display_name TEXT NOT NULL DEFAULT '当前学习者'")
        if "is_active" not in profile_columns:
            conn.execute("ALTER TABLE profiles ADD COLUMN is_active INTEGER NOT NULL DEFAULT 0")
            latest = conn.execute("SELECT id FROM profiles ORDER BY id DESC LIMIT 1").fetchone()
            if latest:
                conn.execute("UPDATE profiles SET is_active=1 WHERE id=?", (latest["id"],))
        evaluation_columns = {row["name"] for row in conn.execute("PRAGMA table_info(evaluations)").fetchall()}
        if "profile_id" not in evaluation_columns:
            conn.execute("ALTER TABLE evaluations ADD COLUMN profile_id INTEGER")
        conversation_columns = {row["name"] for row in conn.execute("PRAGMA table_info(conversations)").fetchall()}
        if "profile_id" not in conversation_columns:
            conn.execute("ALTER TABLE conversations ADD COLUMN profile_id INTEGER")
        conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_demo_key ON profiles(demo_key) WHERE demo_key IS NOT NULL")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
