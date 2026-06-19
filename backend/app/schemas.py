from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "ok"


class StudentProfile(BaseModel):
    id: int | None = None
    major: str = "计算机相关专业"
    grade: str = "大学生"
    knowledge_level: str = "入门"
    learning_goal: str = "掌握 Python 并完成数据分析项目"
    weak_points: list[str] = Field(default_factory=list)
    learning_style: str = "循序渐进"
    resource_preference: list[str] = Field(default_factory=lambda: ["图解", "代码案例"])
    mistake_history: list[str] = Field(default_factory=list)
    source_text: str = ""
    updated_at: datetime | None = None


class ProfileGenerateRequest(BaseModel):
    text: str = Field(min_length=2, max_length=4000)


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=4, ge=1, le=10)


class Citation(BaseModel):
    chunk_id: str
    document_id: int | None = None
    title: str
    content: str
    score: float


class ResourceGenerateRequest(BaseModel):
    topic: str = Field(default="Python 数据分析综合实践", min_length=2, max_length=200)


class TutorRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    mode: Literal["socratic", "explain"] = "socratic"


class QuizQuestion(BaseModel):
    id: str
    type: Literal["single_choice", "true_false", "short_answer", "code"]
    question: str
    options: list[str] = Field(default_factory=list)
    answer: str
    explanation: str
    knowledge_point: str


class EvaluationAnswer(BaseModel):
    question_id: str
    answer: str


class EvaluationSubmitRequest(BaseModel):
    resource_id: int
    answers: list[EvaluationAnswer]
