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

    @staticmethod
    def transition(
        state: OrchestratorState,
        name: str,
        agent: str,
        description: str,
        progress: int,
    ) -> dict[str, Any]:
        state.current_state = name
        item = {
            "state": name,
            "agent": agent,
            "description": description,
            "progress": progress,
        }
        state.state_history.append(item)
        return item

    async def stream(self, topic: str, profile: dict[str, Any]) -> AsyncIterator[str]:
        state = OrchestratorState(topic=topic, profile=profile)
        state.agent_outputs["ProfileAgent"] = {"profile": profile}

        yield sse(
            "progress",
            self.transition(state, "profile_loaded", "ProfileAgent", "已加载当前学生画像与历史薄弱点", 5),
        )

        state.citations = await self.knowledge.run(topic, 5)
        state.agent_outputs["KnowledgeAgent"] = {
            "query": topic,
            "top_k": 5,
            "citations": state.citations,
        }
        yield sse(
            "progress",
            self.transition(state, "knowledge_retrieved", "KnowledgeAgent", "已检索课程知识库片段", 18),
        )
        yield sse("citations", state.citations)

        learning_path = await self.planner.run(topic, profile, state.citations)
        state.resources["learning_path"] = learning_path
        state.agent_outputs["PlannerAgent"] = {"learning_path": learning_path}
        yield sse(
            "progress",
            self.transition(state, "plan_generated", "PlannerAgent", "已生成个性化学习路径", 32),
        )
        yield sse(
            "resource",
            {"type": "learning_path", "content": learning_path, "generated_by": "PlannerAgent"},
        )

        material, code_case, mindmap = await asyncio.gather(
            self.resource.run(topic, profile, state.citations),
            self.code.run(topic, profile),
            self.mindmap.run(topic, profile),
        )
        state.resources.update(material)
        state.resources["code_case"] = code_case
        state.resources["mindmap"] = mindmap
        state.agent_outputs["ResourceAgent"] = material
        state.agent_outputs["CodeAgent"] = {"code_case": code_case}
        state.agent_outputs["MindMapAgent"] = {"mindmap": mindmap}
        yield sse(
            "progress",
            self.transition(
                state,
                "resources_generated",
                "ResourceAgent + CodeAgent + MindMapAgent",
                "讲义、代码案例、思维导图和 PPT 大纲已生成",
                62,
            ),
        )
        attribution = {
            "lecture": "ResourceAgent",
            "ppt_outline": "ResourceAgent",
            "code_case": "CodeAgent",
            "mindmap": "MindMapAgent",
        }
        for resource_type in ["lecture", "mindmap", "code_case", "ppt_outline"]:
            yield sse(
                "resource",
                {
                    "type": resource_type,
                    "content": state.resources[resource_type],
                    "generated_by": attribution[resource_type],
                },
            )

        quiz = await self.quiz.run(topic, profile, state.citations)
        state.resources["quiz"] = quiz
        state.agent_outputs["QuizAgent"] = {"quiz": quiz}
        yield sse(
            "progress",
            self.transition(state, "quiz_generated", "QuizAgent", "已生成四类针对性练习题", 76),
        )
        yield sse("resource", {"type": "quiz", "content": quiz, "generated_by": "QuizAgent"})

        state.review = await self.review.run(state.resources, state.citations, profile)
        state.agent_outputs["ReviewAgent"] = state.review
        yield sse(
            "progress",
            self.transition(state, "review_completed", "ReviewAgent", "已完成规则审校与证据检查", 90),
        )
        yield sse("review", state.review)

        state.resources["citations"] = state.citations
        state.resources["agent_outputs"] = state.agent_outputs
        state.resources["workflow"] = state.state_history
        state.resources["profile_snapshot"] = profile
        resource_id = save_resource(topic, profile.get("id"), state.resources, state.review)
        yield sse(
            "progress",
            self.transition(state, "saved", "Orchestrator", "资源包及全部智能体输出已保存", 100),
        )
        yield sse(
            "done",
            {
                "resource_id": resource_id,
                "progress": 100,
                "message": "资源包生成完成",
                "workflow": state.state_history,
            },
        )


orchestrator = Orchestrator()
