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
        resource_id = int(cursor.lastrowid)
    if profile_id is not None:
        create_learning_tasks(resource_id, profile_id, topic, content)
    record_learning_event(
        profile_id,
        "generated",
        "resource_package",
        str(resource_id),
        {"topic": topic, "review_status": review.get("status")},
    )
    return resource_id


def create_learning_tasks(
    resource_id: int,
    profile_id: int,
    topic: str,
    content: dict[str, Any],
) -> list[dict[str, Any]]:
    profile = content.get("profile_snapshot", {})
    style = str(profile.get("learning_style", "循序渐进"))
    weak_points = profile.get("weak_points", [])
    focus = "、".join(weak_points[:3]) or topic
    durations = {"lecture": 25, "mindmap": 10, "code": 35, "quiz": 20, "review": 10}
    if "基础" in style or "循序渐进" in style:
        durations["lecture"] += 10
        durations["quiz"] += 5
    elif "项目" in style or "实践" in style:
        durations["code"] += 15
    elif "考试" in style or "考点" in style:
        durations["quiz"] += 10
        durations["code"] = max(20, durations["code"] - 10)
    tasks = [
        ("lecture", "阅读个性化讲义", f"带着“{focus}”问题阅读讲义，并记录一个仍不理解的点。"),
        ("mindmap", "查看思维导图", "用自己的话复述知识结构，确认各步骤之间的关系。"),
        ("code", "完成代码实操", f"运行并修改“{topic}”代码案例，保留一次调试记录。"),
        ("quiz", "完成针对性练习", "完成资源包中的选择、判断、简答和代码题。"),
        ("review", "测评与错题复盘", "提交测评，查看薄弱点写回，并确定下一次复习目标。"),
    ]
    now = utc_now()
    with connect() as conn:
        conn.executemany(
            """INSERT OR IGNORE INTO learning_tasks
            (profile_id,resource_id,task_type,title,description,estimated_minutes,status,
             order_index,created_at,completed_at)
            VALUES(?,?,?,?,?,?, 'pending', ?, ?, NULL)""",
            [
                (
                    profile_id,
                    resource_id,
                    task_type,
                    title,
                    description,
                    durations[task_type],
                    index,
                    now,
                )
                for index, (task_type, title, description) in enumerate(tasks, 1)
            ],
        )
    return list_learning_tasks(profile_id, resource_id)


def list_learning_tasks(
    profile_id: int | None,
    resource_id: int | None = None,
) -> list[dict[str, Any]]:
    if profile_id is None:
        return []
    if resource_id is None:
        resources = list_resources(profile_id)
        resource_id = resources[0]["id"] if resources else None
    if resource_id is None:
        return []
    with connect() as conn:
        rows = conn.execute(
            """SELECT * FROM learning_tasks
            WHERE profile_id=? AND resource_id=? ORDER BY order_index, id""",
            (profile_id, resource_id),
        ).fetchall()
    if not rows:
        resource = get_resource(resource_id)
        if resource and resource.get("profile_id") == profile_id:
            return create_learning_tasks(
                resource_id,
                profile_id,
                resource["topic"],
                resource["content"],
            )
    return [dict(row) for row in rows]


def learning_task_summary(
    profile_id: int | None,
    resource_id: int | None = None,
) -> dict[str, Any] | None:
    tasks = list_learning_tasks(profile_id, resource_id)
    if not tasks:
        return None
    resource_id = int(tasks[0]["resource_id"])
    resource = get_resource(resource_id)
    completed = sum(item["status"] == "completed" for item in tasks)
    total_minutes = sum(int(item["estimated_minutes"]) for item in tasks)
    remaining_minutes = sum(
        int(item["estimated_minutes"]) for item in tasks if item["status"] != "completed"
    )
    return {
        "resource_id": resource_id,
        "topic": resource["topic"] if resource else "",
        "tasks": tasks,
        "completed": completed,
        "total": len(tasks),
        "progress": round(completed / len(tasks) * 100),
        "total_minutes": total_minutes,
        "remaining_minutes": remaining_minutes,
        "next_task": next(
            (item for item in tasks if item["status"] != "completed"),
            None,
        ),
    }


def update_learning_task(
    task_id: int,
    profile_id: int,
    completed: bool,
) -> dict[str, Any] | None:
    status = "completed" if completed else "pending"
    completed_at = utc_now() if completed else None
    changed = False
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM learning_tasks WHERE id=? AND profile_id=?",
            (task_id, profile_id),
        ).fetchone()
        if not row:
            return None
        resource_id = int(row["resource_id"])
        if row["status"] != status:
            conn.execute(
                "UPDATE learning_tasks SET status=?, completed_at=? WHERE id=?",
                (status, completed_at, task_id),
            )
            changed = True
    if changed:
        record_learning_event(
            profile_id,
            "progressed",
            "learning_task",
            str(task_id),
            {
                "resource_id": resource_id,
                "title": row["title"],
                "status": status,
            },
        )
    return learning_task_summary(profile_id, resource_id)


def complete_learning_tasks(
    profile_id: int | None,
    resource_id: int,
    task_types: list[str],
) -> dict[str, Any] | None:
    if profile_id is None:
        return None
    tasks = list_learning_tasks(profile_id, resource_id)
    for task in tasks:
        if task["task_type"] in task_types and task["status"] != "completed":
            update_learning_task(task["id"], profile_id, True)
    return learning_task_summary(profile_id, resource_id)


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
        evaluation_id = int(cursor.lastrowid)
    record_learning_event(
        profile_id,
        "completed",
        "evaluation",
        str(evaluation_id),
        {"resource_id": resource_id, "score": score, "weak_points": weak_points},
    )
    return evaluation_id


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
    if role == "user":
        record_learning_event(
            profile_id,
            "asked",
            "tutor_question",
            None,
            {"question": content[:160], "citation_count": len(citations or [])},
        )


def record_learning_event(
    profile_id: int | None,
    verb: str,
    object_type: str,
    object_id: str | None = None,
    result: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> int:
    with connect() as conn:
        cursor = conn.execute(
            """INSERT INTO learning_events
            (profile_id,verb,object_type,object_id,result,context,created_at)
            VALUES(?,?,?,?,?,?,?)""",
            (
                profile_id,
                verb,
                object_type,
                object_id,
                json_dump(result or {}),
                json_dump(context or {}),
                utc_now(),
            ),
        )
        return int(cursor.lastrowid)


def list_learning_events(profile_id: int | None, limit: int = 12) -> list[dict[str, Any]]:
    if profile_id is None:
        return []
    with connect() as conn:
        rows = conn.execute(
            """SELECT * FROM learning_events WHERE profile_id=?
            ORDER BY id DESC LIMIT ?""",
            (profile_id, limit),
        ).fetchall()
    events = []
    for row in rows:
        item = dict(row)
        item["result"] = json_load(item["result"], {})
        item["context"] = json_load(item["context"], {})
        events.append(item)
    return events


def update_mastery(
    profile_id: int | None,
    detail: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if profile_id is None:
        return []
    now = utc_now()
    with connect() as conn:
        for item in detail:
            knowledge_point = item.get("knowledge_point")
            if not knowledge_point:
                continue
            percentage = round(
                float(item.get("points", 0)) / max(float(item.get("max_points", 25)), 1) * 100,
                1,
            )
            current = conn.execute(
                """SELECT * FROM mastery_records
                WHERE profile_id=? AND knowledge_point=?""",
                (profile_id, knowledge_point),
            ).fetchone()
            if current:
                attempts = int(current["attempts"]) + 1
                mastery = round(
                    (float(current["mastery"]) * int(current["attempts"]) + percentage) / attempts,
                    1,
                )
                conn.execute(
                    """UPDATE mastery_records SET mastery=?, attempts=?,
                    correct_count=?, last_score=?, updated_at=?
                    WHERE profile_id=? AND knowledge_point=?""",
                    (
                        mastery,
                        attempts,
                        int(current["correct_count"]) + int(bool(item.get("correct"))),
                        percentage,
                        now,
                        profile_id,
                        knowledge_point,
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO mastery_records
                    (profile_id,knowledge_point,mastery,attempts,correct_count,last_score,updated_at)
                    VALUES(?,?,?,?,?,?,?)""",
                    (
                        profile_id,
                        knowledge_point,
                        percentage,
                        1,
                        int(bool(item.get("correct"))),
                        percentage,
                        now,
                    ),
                )
    return list_mastery(profile_id)


def list_mastery(profile_id: int | None) -> list[dict[str, Any]]:
    if profile_id is None:
        return []
    with connect() as conn:
        rows = conn.execute(
            """SELECT knowledge_point,mastery,attempts,correct_count,last_score,updated_at
            FROM mastery_records WHERE profile_id=?
            ORDER BY mastery ASC, updated_at DESC""",
            (profile_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def save_resource_feedback(
    profile_id: int,
    resource_id: int,
    rating: int,
    comment: str = "",
) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """INSERT INTO resource_feedback(profile_id,resource_id,rating,comment,created_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(profile_id,resource_id) DO UPDATE SET
            rating=excluded.rating, comment=excluded.comment, created_at=excluded.created_at""",
            (profile_id, resource_id, rating, comment, utc_now()),
        )
    record_learning_event(
        profile_id,
        "rated",
        "resource_package",
        str(resource_id),
        {"rating": rating, "comment": comment},
    )
    return {"resource_id": resource_id, "rating": rating, "comment": comment}


def feedback_summary(profile_id: int | None) -> dict[str, Any]:
    if profile_id is None:
        return {"total": 0, "helpful": 0, "needs_adjustment": 0}
    with connect() as conn:
        row = conn.execute(
            """SELECT COUNT(*) AS total,
            SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS helpful,
            SUM(CASE WHEN rating < 0 THEN 1 ELSE 0 END) AS needs_adjustment
            FROM resource_feedback WHERE profile_id=?""",
            (profile_id,),
        ).fetchone()
    return {
        "total": int(row["total"] or 0),
        "helpful": int(row["helpful"] or 0),
        "needs_adjustment": int(row["needs_adjustment"] or 0),
    }
