import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

from .agents import (
    CodeAgent,
    KnowledgeAgent,
    MindMapAgent,
    OrchestratorState,
    PlannerAgent,
    QuizAgent,
    ResourceAgent,
    ReviewAgent,
)
from .repositories import save_resource


def sse(event: str, data: Any) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


class Orchestrator:
    def __init__(self) -> None:
        self.knowledge = KnowledgeAgent()
        self.planner = PlannerAgent()
        self.resource = ResourceAgent()
        self.quiz = QuizAgent()
        self.code = CodeAgent()
        self.mindmap = MindMapAgent()
        self.review = ReviewAgent()

    async def stream(self, topic: str, profile: dict[str, Any]) -> AsyncIterator[str]:
        state = OrchestratorState(topic=topic, profile=profile)
        yield sse("progress", {"agent": "知识检索员", "stage": "检索课程知识库", "progress": 10})
        state.citations = await self.knowledge.run(topic, 5)
        yield sse("citations", state.citations)

        yield sse("progress", {"agent": "路径规划师", "stage": "生成个性化学习路径", "progress": 24})
        state.resources["learning_path"] = await self.planner.run(topic, profile, state.citations)
        yield sse("resource", {"type": "learning_path", "content": state.resources["learning_path"]})

        yield sse("progress", {"agent": "资源协作组", "stage": "并行生成讲义、题库、代码和思维导图", "progress": 42})
        material, quiz, code, mindmap = await asyncio.gather(
            self.resource.run(topic, profile, state.citations),
            self.quiz.run(topic),
            self.code.run(topic),
            self.mindmap.run(topic),
        )
        state.resources.update(material)
        state.resources["quiz"] = quiz
        state.resources["code_case"] = code
        state.resources["mindmap"] = mindmap
        for resource_type in ["lecture", "mindmap", "quiz", "code_case", "ppt_outline"]:
            yield sse("resource", {"type": resource_type, "content": state.resources[resource_type]})

        yield sse("progress", {"agent": "事实审校员", "stage": "检查引用、安全与内容一致性", "progress": 86})
        state.review = await self.review.run(state.resources, state.citations)
        state.resources["citations"] = state.citations
        resource_id = save_resource(topic, profile.get("id"), state.resources, state.review)
        yield sse("review", state.review)
        yield sse("done", {"resource_id": resource_id, "progress": 100, "message": "资源包生成完成"})


orchestrator = Orchestrator()
