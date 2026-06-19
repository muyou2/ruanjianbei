import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Iterator

from .config import get_settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
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
  resource_id INTEGER NOT NULL, score REAL NOT NULL,
  weak_points TEXT NOT NULL, suggestions TEXT NOT NULL,
  detail TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  role TEXT NOT NULL, content TEXT NOT NULL, citations TEXT NOT NULL,
  created_at TEXT NOT NULL
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


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


def json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def json_load(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default
