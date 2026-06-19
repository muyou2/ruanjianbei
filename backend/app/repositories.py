from typing import Any

from .database import connect, json_dump, json_load, row_to_dict, utc_now
from .schemas import StudentProfile


def _profile_from_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    row["weak_points"] = json_load(row["weak_points"], [])
    row["resource_preference"] = json_load(row["resource_preference"], [])
    row["mistake_history"] = json_load(row["mistake_history"], [])
    row["is_active"] = bool(row.get("is_active"))
    return row


def get_profile(profile_id: int | None = None, demo_key: str | None = None) -> dict[str, Any] | None:
    with connect() as conn:
        if profile_id is not None:
            row = conn.execute("SELECT * FROM profiles WHERE id=?", (profile_id,)).fetchone()
        elif demo_key is not None:
            row = conn.execute("SELECT * FROM profiles WHERE demo_key=?", (demo_key,)).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM profiles ORDER BY is_active DESC, updated_at DESC, id DESC LIMIT 1"
            ).fetchone()
    return _profile_from_row(row_to_dict(row))


def list_profiles() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM profiles ORDER BY is_active DESC, demo_key IS NULL, id"
        ).fetchall()
    return [_profile_from_row(dict(row)) for row in rows]


def activate_profile(profile_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        exists = conn.execute("SELECT id FROM profiles WHERE id=?", (profile_id,)).fetchone()
        if not exists:
            return None
        conn.execute("UPDATE profiles SET is_active=0")
        conn.execute("UPDATE profiles SET is_active=1, updated_at=? WHERE id=?", (utc_now(), profile_id))
    return get_profile(profile_id=profile_id)


def save_profile(profile: StudentProfile, activate: bool = True) -> dict[str, Any]:
    now = utc_now()
    current = get_profile(profile_id=profile.id) if profile.id else (
        get_profile(demo_key=profile.demo_key) if profile.demo_key else None
    )
    values = (
        profile.demo_key,
        profile.display_name,
        1 if activate else int(profile.is_active),
        profile.major,
        profile.grade,
        profile.knowledge_level,
        profile.learning_goal,
        json_dump(profile.weak_points),
        profile.learning_style,
        json_dump(profile.resource_preference),
        json_dump(profile.mistake_history),
        profile.source_text,
        now,
    )
    with connect() as conn:
        if activate:
            conn.execute("UPDATE profiles SET is_active=0")
        if current:
            conn.execute(
                """UPDATE profiles SET demo_key=?, display_name=?, is_active=?,
                major=?, grade=?, knowledge_level=?, learning_goal=?,
                weak_points=?, learning_style=?, resource_preference=?, mistake_history=?,
                source_text=?, updated_at=? WHERE id=?""",
                (*values, current["id"]),
            )
            saved_id = current["id"]
        else:
            cursor = conn.execute(
                """INSERT INTO profiles
                (demo_key,display_name,is_active,major,grade,knowledge_level,learning_goal,weak_points,learning_style,
                 resource_preference,mistake_history,source_text,created_at,updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*values[:-1], now, now),
            )
            saved_id = int(cursor.lastrowid)
    return get_profile(profile_id=saved_id) or {}


def list_documents() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


def create_document(filename: str, title: str, file_type: str, size: int) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO documents(filename,title,file_type,size,status,created_at) VALUES(?,?,?,?,?,?)",
            (filename, title, file_type, size, "processing", utc_now()),
        )
        return int(cursor.lastrowid)


def finish_document(document_id: int, chunks: list[dict[str, Any]]) -> None:
    with connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO document_chunks(id,document_id,title,content,position) VALUES(?,?,?,?,?)",
            [(c["id"], document_id, c["title"], c["content"], c["position"]) for c in chunks],
        )
        conn.execute(
            "UPDATE documents SET status='ready', chunk_count=? WHERE id=?",
            (len(chunks), document_id),
        )


def delete_document(document_id: int) -> bool:
    with connect() as conn:
        conn.execute("DELETE FROM document_chunks WHERE document_id=?", (document_id,))
        cursor = conn.execute("DELETE FROM documents WHERE id=?", (document_id,))
        return cursor.rowcount > 0


def list_chunks() -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM document_chunks ORDER BY document_id, position").fetchall()
    return [dict(row) for row in rows]


def save_resource(topic: str, profile_id: int | None, content: dict, review: dict) -> int:
    with connect() as conn:
        cursor = conn.execute(
            "INSERT INTO resources(topic,profile_id,status,content,review,created_at) VALUES(?,?,?,?,?,?)",
            (topic, profile_id, "ready", json_dump(content), json_dump(review), utc_now()),
        )
        return int(cursor.lastrowid)


def list_resources(profile_id: int | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if profile_id is None:
            rows = conn.execute("SELECT * FROM resources ORDER BY id DESC").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM resources WHERE profile_id=? ORDER BY id DESC", (profile_id,)
            ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["content"] = json_load(item["content"], {})
        item["review"] = json_load(item["review"], {})
        result.append(item)
    return result


def get_resource(resource_id: int) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM resources WHERE id=?", (resource_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["content"] = json_load(item["content"], {})
    item["review"] = json_load(item["review"], {})
    return item


def save_evaluation(
    resource_id: int,
    profile_id: int | None,
    score: float,
    weak_points: list[str],
    suggestions: list[str],
    detail: list[dict],
) -> int:
    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO evaluations
            (resource_id,profile_id,score,weak_points,suggestions,detail,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (
                resource_id,
                profile_id,
                score,
                json_dump(weak_points),
                json_dump(suggestions),
                json_dump(detail),
                utc_now(),
            ),
        )
        return int(cursor.lastrowid)


def latest_evaluation(profile_id: int | None) -> dict[str, Any] | None:
    if profile_id is None:
        return None
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM evaluations WHERE profile_id=? ORDER BY id DESC LIMIT 1",
            (profile_id,),
        ).fetchone()
    if not row:
        return None
    item = dict(row)
    item["weak_points"] = json_load(item["weak_points"], [])
    item["suggestions"] = json_load(item["suggestions"], [])
    item["detail"] = json_load(item["detail"], [])
    return item


def save_message(
    role: str,
    content: str,
    citations: list[dict] | None = None,
    profile_id: int | None = None,
) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO conversations(profile_id,role,content,citations,created_at)
            VALUES(?,?,?,?,?)""",
            (profile_id, role, content, json_dump(citations or []), utc_now()),
        )
