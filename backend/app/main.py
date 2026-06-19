import json
import shutil
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .agents import KnowledgeAgent, ProfileAgent, citations_text
from .analytics import local_learning_signals, public_dataset_overview
from .config import PROJECT_DIR, get_settings
from .database import init_db
from .knowledge import extract_text, knowledge_store, split_text
from .llm_service import llm_service
from .orchestrator import orchestrator, sse
from .repositories import (
    create_document,
    delete_document,
    finish_document,
    get_profile,
    get_resource,
    list_documents,
    list_resources,
    save_evaluation,
    save_message,
    save_profile,
)
from .schemas import (
    EvaluationSubmitRequest,
    KnowledgeSearchRequest,
    ProfileGenerateRequest,
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
    if list_documents():
        return
    course_dir = PROJECT_DIR / "course_data"
    for source in sorted(course_dir.glob("*.md")):
        ingest_path(source, source.name)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    seed_course()
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


@app.post("/api/profiles")
async def profile_generate(payload: ProfileGenerateRequest):
    profile = await ProfileAgent().run(payload.text)
    return response(save_profile(profile), "学生画像已生成")


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
    profile = get_profile()
    if not profile:
        profile = save_profile(StudentProfile(source_text="系统默认学习者画像"))
    return StreamingResponse(
        orchestrator.stream(payload.topic, profile),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/resources")
def resources_get():
    return response(list_resources())


@app.get("/api/resources/{resource_id}")
def resource_get(resource_id: int):
    item = get_resource(resource_id)
    if not item:
        raise HTTPException(404, "资源包不存在")
    return response(item)


@app.get("/api/quizzes")
def quizzes_get(resource_id: int | None = None):
    item = get_resource(resource_id) if resource_id else (list_resources()[0] if list_resources() else None)
    return response({"resource_id": item["id"], "questions": item["content"].get("quiz", [])} if item else None)


@app.post("/api/tutor/chat")
async def tutor_chat(payload: TutorRequest):
    citations = await KnowledgeAgent().run(payload.question, 4)
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
        save_message("user", payload.question)
        yield sse("citations", citations)
        answer = ""
        async for chunk in llm_service.stream(
            system,
            f"问题：{payload.question}\n资料：\n{citations_text(citations)}",
            fallback,
        ):
            answer += chunk
            yield sse("delta", {"text": chunk})
        save_message("assistant", answer, citations)
        yield sse("done", {"message": "回答完成"})

    return StreamingResponse(stream(), media_type="text/event-stream")


def normalize_answer(value: str) -> str:
    return "".join(value.lower().split()).replace("。", "")


@app.post("/api/evaluations/submit")
def evaluation_submit(payload: EvaluationSubmitRequest):
    resource = get_resource(payload.resource_id)
    if not resource:
        raise HTTPException(404, "资源包不存在")
    questions = {q["id"]: q for q in resource["content"].get("quiz", [])}
    detail = []
    weak_points = []
    earned = 0.0
    for item in payload.answers:
        question = questions.get(item.question_id)
        if not question:
            continue
        expected = normalize_answer(question["answer"])
        actual = normalize_answer(item.answer)
        if question["type"] in {"single_choice", "true_false"}:
            correct = actual == expected
        else:
            keywords = [word for word in re_split_keywords(question["answer"]) if len(word) > 1]
            correct = bool(keywords) and sum(word in actual for word in keywords[:5]) >= min(2, len(keywords))
        earned += 1 if correct else 0
        if not correct:
            weak_points.append(question["knowledge_point"])
        detail.append(
            {
                "question_id": item.question_id,
                "correct": correct,
                "answer": item.answer,
                "expected": question["answer"],
                "explanation": question["explanation"],
            }
        )
    score = round((earned / len(questions) * 100) if questions else 0, 1)
    weak_points = list(dict.fromkeys(weak_points))
    suggestions = [
        f"优先复习：{'、'.join(weak_points)}" if weak_points else "当前知识点掌握良好，可进入项目迁移练习",
        "根据错题重新运行对应代码示例，并在 24 小时后进行一次间隔复习",
    ]
    profile = get_profile()
    if profile and weak_points:
        merged = list(dict.fromkeys(profile["weak_points"] + weak_points))
        history = profile["mistake_history"] + [f"测评 {score} 分：{'、'.join(weak_points)}"]
        save_profile(StudentProfile(**{**profile, "weak_points": merged, "mistake_history": history}))
    evaluation_id = save_evaluation(payload.resource_id, score, weak_points, suggestions, detail)
    return response(
        {
            "id": evaluation_id,
            "score": score,
            "correct_count": int(earned),
            "total": len(questions),
            "weak_points": weak_points,
            "suggestions": suggestions,
            "detail": detail,
        },
        "评估完成，学生画像已动态更新",
    )


def re_split_keywords(text: str) -> list[str]:
    import re

    return re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z_]{2,}", normalize_answer(text))
