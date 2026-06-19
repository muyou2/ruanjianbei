import json
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .agents import DEMO_PROFILES, KnowledgeAgent, ProfileAgent, citations_text
from .analytics import local_learning_signals, public_dataset_overview
from .config import PROJECT_DIR, get_settings
from .database import init_db
from .evaluation import score_question
from .knowledge import extract_text, knowledge_store, split_text
from .llm_service import llm_service
from .orchestrator import orchestrator, sse
from .repositories import (
    create_document,
    delete_document,
    finish_document,
    activate_profile,
    get_profile,
    get_resource,
    list_documents,
    list_profiles,
    list_resources,
    list_learning_events,
    list_mastery,
    record_learning_event,
    save_evaluation,
    save_message,
    save_profile,
    save_resource_feedback,
    update_mastery,
)
from .schemas import (
    EvaluationSubmitRequest,
    KnowledgeSearchRequest,
    ProfileGenerateRequest,
    ProfileSelectRequest,
    ResourceFeedbackRequest,
    ResourceGenerateRequest,
    StudentProfile,
    TutorRequest,
)


settings = get_settings()


def response(data=None, message: str = "ok") -> dict:
    return {"success": True, "data": data, "message": message}


def ingest_path(path: Path, original_name: str) -> dict:
    suffix = path.suffix.lower()
    text = extract_text(path, suffix)
    if not text.strip():
        raise ValueError("文档未提取到有效文本")
    document_id = create_document(original_name, path.stem, suffix.lstrip("."), path.stat().st_size)
    chunks = split_text(text, path.stem)
    finish_document(document_id, chunks)
    knowledge_store.upsert(document_id, chunks)
    return {"id": document_id, "filename": original_name, "chunk_count": len(chunks), "status": "ready"}


def seed_course() -> None:
    existing = {item["filename"] for item in list_documents()}
    course_dir = PROJECT_DIR / "course_data"
    for source in sorted(course_dir.glob("*.md")):
        if source.name not in existing:
            ingest_path(source, source.name)


def seed_demo_profiles() -> None:
    active = get_profile()
    for demo_key, demo in DEMO_PROFILES.items():
        if not get_profile(demo_key=demo_key):
            save_profile(demo, activate=False)
    if not active:
        first = get_profile(demo_key="demo_basic")
        if first:
            activate_profile(first["id"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_course()
    seed_demo_profiles()
    yield


app = FastAPI(
    title=settings.app_name,
    description="面向高校 Python 课程的个性化资源生成与学习多智能体系统。",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return response({"status": "healthy", "database": str(settings.database_path)})


@app.get("/api/config/status")
def config_status():
    return response(
        {
            "provider": llm_service.provider_name,
            "mock_mode": llm_service.is_mock,
            "vector_backend": knowledge_store.backend,
            "retrieval_status": "MVP 实现：本地 Hashing 向量 + Chroma 持久化，非 sentence-transformers 强语义模型",
            "course": "Python 基础到数据分析项目实战",
        }
    )


@app.get("/api/analytics/overview")
def analytics_overview():
    return response(
        {
            "public_benchmark": public_dataset_overview(),
            "personal_signals": local_learning_signals(),
        }
    )


@app.get("/api/profiles")
def profile_get():
    return response(get_profile())


@app.get("/api/profiles/all")
def profiles_all():
    return response(list_profiles())


@app.post("/api/profiles/select")
def profile_select(payload: ProfileSelectRequest):
    selected = activate_profile(payload.profile_id)
    if not selected:
        raise HTTPException(404, "学生画像不存在")
    return response(selected, "已切换当前学习者")


@app.post("/api/profiles")
async def profile_generate(payload: ProfileGenerateRequest):
    before = get_profile()
    profile = await ProfileAgent().run(payload.text, payload.display_name)
    saved = save_profile(profile)
    record_learning_event(
        saved.get("id"),
        "created",
        "student_profile",
        str(saved.get("id")),
        {"display_name": saved.get("display_name"), "weak_points": saved.get("weak_points")},
    )
    return response(
        {
            "profile": saved,
            "before": before,
            "changes": profile_changes(before, saved),
        },
        "学生画像已根据输入文本生成并保存",
    )


@app.put("/api/profiles")
def profile_update(payload: StudentProfile):
    return response(save_profile(payload), "学生画像已更新")


@app.get("/api/documents")
def documents_get():
    return response(list_documents())


@app.post("/api/documents")
async def documents_upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md", ".pdf"}:
        raise HTTPException(400, "仅支持 txt、md、pdf 文件")
    target = settings.uploads_dir / Path(file.filename or f"upload{suffix}").name
    with target.open("wb") as output:
        shutil.copyfileobj(file.file, output)
    try:
        return response(ingest_path(target, file.filename or target.name), "文档解析完成")
    except ValueError as error:
        target.unlink(missing_ok=True)
        raise HTTPException(400, str(error)) from error


@app.delete("/api/documents/{document_id}")
def documents_delete(document_id: int):
    knowledge_store.delete_document(document_id)
    if not delete_document(document_id):
        raise HTTPException(404, "文档不存在")
    return response({"id": document_id}, "文档已删除")


@app.post("/api/knowledge/search")
async def knowledge_search(payload: KnowledgeSearchRequest):
    items = await KnowledgeAgent().run(payload.query, payload.top_k)
    return response(items)


@app.post("/api/resources/generate")
async def resources_generate(payload: ResourceGenerateRequest):
    profile = get_profile(profile_id=payload.profile_id) if payload.profile_id else get_profile()
    if not profile:
        profile = save_profile(StudentProfile(source_text="系统默认学习者画像"))
    return StreamingResponse(
        orchestrator.stream(payload.topic, profile),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/resources")
def resources_get():
    profile = get_profile()
    return response(list_resources(profile.get("id") if profile else None))


@app.get("/api/resources/{resource_id}")
def resource_get(resource_id: int):
    item = get_resource(resource_id)
    if not item:
        raise HTTPException(404, "资源包不存在")
    return response(item)


@app.post("/api/resources/{resource_id}/feedback")
def resource_feedback(resource_id: int, payload: ResourceFeedbackRequest):
    resource = get_resource(resource_id)
    if not resource:
        raise HTTPException(404, "资源包不存在")
    profile = get_profile()
    if not profile or resource.get("profile_id") != profile.get("id"):
        raise HTTPException(403, "只能评价当前学生自己的资源包")
    saved = save_resource_feedback(profile["id"], resource_id, payload.rating, payload.comment)
    return response(saved, "资源反馈已保存，将用于后续学习建议")


@app.get("/api/learning/progress")
def learning_progress():
    profile = get_profile()
    profile_id = profile.get("id") if profile else None
    return response(
        {
            "profile_id": profile_id,
            "mastery": list_mastery(profile_id),
            "events": list_learning_events(profile_id, 20),
        }
    )


@app.get("/api/quizzes")
def quizzes_get(resource_id: int | None = None):
    profile = get_profile()
    available = list_resources(profile.get("id") if profile else None)
    item = get_resource(resource_id) if resource_id else (available[0] if available else None)
    return response({"resource_id": item["id"], "questions": item["content"].get("quiz", [])} if item else None)


@app.post("/api/tutor/chat")
async def tutor_chat(payload: TutorRequest):
    profile = get_profile()
    profile_id = profile.get("id") if profile else None
    citations = await KnowledgeAgent().run(payload.question, 4)
    evidence_sufficient = bool(citations) and max(
        (item.get("score", 0) for item in citations), default=0
    ) >= 0.08
    if payload.mode == "socratic":
        fallback = f"""我们先不急着给最终结论。针对“{payload.question}”，请先想一想：

1. 这个问题的**输入是什么、期望输出是什么**？
2. 你能否构造一个只有 2～3 个元素的最小示例？
3. 如果把关键语句拆成两步，中间变量会是什么？

**提示一**：先根据参考资料找到相关数据类型或语法规则。

**提示二**：运行最小示例后，告诉我实际输出与你的预期差在哪里，我再给下一层提示。

> 这种模式优先训练问题拆解与自我解释，而不是直接替你完成答案。"""
        system = "你是采用苏格拉底教学法的 Python 助教。优先提问、分层提示和检查理解，仅依据资料，不直接替学生完成整道题。使用 Markdown。"
    else:
        fallback = f"""根据课程资料，针对“{payload.question}”可以从输入、处理过程和预期输出三个部分理解。

先用最小可运行示例复现，再逐步增加条件。若出现错误，请优先查看异常类型与堆栈最后一行，并对照参考片段核验概念。

**建议步骤**
1. 用自己的话复述概念。
2. 修改示例中的一个变量并观察结果。
3. 完成一道同知识点练习题。

以上回答基于当前课程知识库生成。"""
        system = "你是 Python 课程助教。直接、清晰地讲解问题，仅依据资料回答；证据不足时明确说明。使用 Markdown。"

    async def stream():
        save_message("user", payload.question, profile_id=profile_id)
        yield sse("citations", citations)
        yield sse(
            "evidence",
            {
                "sufficient": evidence_sufficient,
                "message": "知识库证据充足" if evidence_sufficient else "知识库证据不足，需要人工核验",
            },
        )
        if not evidence_sufficient:
            answer = "## 知识库证据不足\n\n当前课程知识库没有检索到足够相关的内容，因此系统不生成确定性答案。请补充课程资料，或由教师/助教人工核验后再回答。"
            yield sse("delta", {"text": answer})
            save_message("assistant", answer, citations, profile_id=profile_id)
            yield sse("done", {"message": "证据不足，已停止扩展生成"})
            return
        answer = ""
        async for chunk in llm_service.stream(
            system,
            f"问题：{payload.question}\n资料：\n{citations_text(citations)}",
            fallback,
        ):
            answer += chunk
            yield sse("delta", {"text": chunk})
        save_message("assistant", answer, citations, profile_id=profile_id)
        yield sse("done", {"message": "回答完成"})

    return StreamingResponse(stream(), media_type="text/event-stream")


@app.post("/api/evaluations/submit")
def evaluation_submit(payload: EvaluationSubmitRequest):
    resource = get_resource(payload.resource_id)
    if not resource:
        raise HTTPException(404, "资源包不存在")
    questions = {q["id"]: q for q in resource["content"].get("quiz", [])}
    detail = []
    weak_points = []
    earned = 0.0
    profile = get_profile(profile_id=resource.get("profile_id")) or get_profile()
    profile_before = dict(profile) if profile else None
    for item in payload.answers:
        question = questions.get(item.question_id)
        if not question:
            continue
        scored = score_question(question, item.answer)
        scored["knowledge_point"] = question["knowledge_point"]
        earned += scored["points"]
        if not scored["correct"]:
            weak_points.append(question["knowledge_point"])
        detail.append(scored)
    score = round(earned, 1)
    weak_points = list(dict.fromkeys(weak_points))
    suggestions = [
        f"优先复习：{'、'.join(weak_points)}" if weak_points else "当前知识点掌握良好，可进入项目迁移练习",
        "根据错题重新运行对应代码示例，并在 24 小时后进行一次间隔复习",
    ]
    if profile and weak_points:
        merged = list(dict.fromkeys(profile["weak_points"] + weak_points))
        wrong_records = [
            f"{question['knowledge_point']}：{question['question']}"
            for question in questions.values()
            if any(item["question_id"] == question["id"] and not item["correct"] for item in detail)
        ]
        history = profile["mistake_history"] + [f"测评 {score} 分"] + wrong_records
        profile = save_profile(
            StudentProfile(**{**profile, "weak_points": merged, "mistake_history": history})
        )
    evaluation_id = save_evaluation(
        payload.resource_id,
        profile.get("id") if profile else None,
        score,
        weak_points,
        suggestions,
        detail,
    )
    mastery = update_mastery(profile.get("id") if profile else None, detail)
    profile_after = profile or profile_before
    return response(
        {
            "id": evaluation_id,
            "score": score,
            "correct_count": sum(1 for item in detail if item["correct"]),
            "total": 100,
            "question_count": len(questions),
            "weak_points": weak_points,
            "suggestions": suggestions,
            "detail": detail,
            "mastery": mastery,
            "profile_before": profile_before,
            "profile_after": profile_after,
            "profile_changes": profile_changes(profile_before, profile_after),
        },
        "评估完成，学生画像已动态更新",
    )


def profile_changes(before: dict | None, after: dict | None) -> list[dict]:
    if not after:
        return []
    changes = []
    for field in ["major", "grade", "knowledge_level", "learning_goal", "weak_points", "learning_style", "resource_preference", "mistake_history"]:
        old_value = before.get(field) if before else None
        new_value = after.get(field)
        if old_value != new_value:
            changes.append({"field": field, "before": old_value, "after": new_value})
    return changes
