import json

from fastapi.testclient import TestClient

from app.main import app


def parse_sse(text: str) -> list[tuple[str, dict]]:
    events = []
    for block in text.split("\n\n"):
        event = None
        data = None
        for line in block.splitlines():
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        if event and data is not None:
            events.append((event, data))
    return events


def test_complete_python_learning_loop():
    with TestClient(app) as client:
        status = client.get("/api/config/status").json()["data"]
        assert len(status["course_topics"]) == 17
        llm_test = client.get("/api/config/llm-test")
        assert llm_test.status_code == 200
        llm_report = llm_test.json()["data"]
        assert llm_report["provider"] == "mock"
        assert llm_report["success"] is True
        assert llm_report["fallback_used"] is False

        generated = client.post(
            "/api/profiles",
            json={
                "display_name": "闭环测试学生",
                "text": "我是计算机专业大二学生，Python 基础一般，函数、Pandas 和数据分析项目不熟，希望通过图解、代码案例和项目练习学习。",
            },
        )
        assert generated.status_code == 200
        profile = generated.json()["data"]["profile"]
        assert profile["major"] == "计算机专业"
        assert "Pandas" in profile["weak_points"]

        search = client.post(
            "/api/knowledge/search",
            json={"query": "Pandas dropna 和 fillna 应该怎么选择？", "top_k": 4},
        )
        assert search.status_code == 200
        assert len(search.json()["data"]) >= 3
        assert search.json()["data"][0]["retrieval_mode"] in {
            "语义向量检索",
            "Hashing MVP 检索",
        }

        generated_resource = client.post(
            "/api/resources/generate",
            json={
                "topic": "Pandas 数据清洗与分析综合实践",
                "profile_id": profile["id"],
            },
        )
        assert generated_resource.status_code == 200
        events = parse_sse(generated_resource.text)
        state_names = [
            data["state"]
            for event, data in events
            if event == "progress"
        ]
        assert state_names == [
            "profile_loaded",
            "knowledge_retrieved",
            "plan_generated",
            "resources_generated",
            "quiz_generated",
            "review_completed",
            "saved",
        ]
        done = next(data for event, data in events if event == "done")
        resource = client.get(f"/api/resources/{done['resource_id']}").json()["data"]
        for key in [
            "learning_path",
            "lecture",
            "mindmap",
            "quiz",
            "code_case",
            "ppt_outline",
            "multimodal_resource",
        ]:
            assert resource["content"][key]
        assert resource["content"]["generation_metadata"]
        assert resource["content"]["multimodal_resource"]["type"] == "html_animation"
        assert len(resource["content"]["workflow"]) == 7
        assert resource["content"]["workflow"][-1]["state"] == "saved"
        for agent in [
            "ProfileAgent",
            "KnowledgeAgent",
            "PlannerAgent",
            "ResourceAgent",
            "QuizAgent",
            "CodeAgent",
            "MindMapAgent",
            "ReviewAgent",
        ]:
            assert agent in resource["content"]["agent_outputs"]

        pptx = client.get(f"/api/resources/{resource['id']}/pptx")
        assert pptx.status_code == 200
        assert pptx.content[:2] == b"PK"
        assert client.get("/api/resources/999999/pptx").status_code == 404

        tutor = client.post(
            "/api/tutor/chat",
            json={
                "question": "Pandas 里 dropna 和 fillna 应该怎么选择？",
                "mode": "socratic",
            },
        )
        tutor_events = parse_sse(tutor.text)
        assert any(event == "citations" and data for event, data in tutor_events)
        assert any(event == "evidence" for event, _ in tutor_events)
        assert any(event == "generation" for event, _ in tutor_events)
        tutor_answer = "".join(
            data["text"] for event, data in tutor_events if event == "delta"
        )
        assert "dropna" in tutor_answer
        assert "fillna" in tutor_answer

        quiz = resource["content"]["quiz"]
        answers = [
            {"question_id": quiz[0]["id"], "answer": "直接删除所有空值"},
            {"question_id": quiz[1]["id"], "answer": "正确"},
            {"question_id": quiz[2]["id"], "answer": "直接删除即可"},
            {"question_id": quiz[3]["id"], "answer": "df = pd.read_csv('data.csv')"},
        ]
        evaluation = client.post(
            "/api/evaluations/submit",
            json={"resource_id": resource["id"], "answers": answers},
        )
        assert evaluation.status_code == 200
        report = evaluation.json()["data"]
        assert report["score"] < 100
        assert report["weak_points"]
        assert report["profile_changes"]
        assert any(item["manual_review"] for item in report["detail"])
        assert report["mastery"]
        assert all("knowledge_point" in item for item in report["detail"])

        feedback = client.post(
            f"/api/resources/{resource['id']}/feedback",
            json={"rating": 1, "comment": "图解与代码案例对当前学习有帮助"},
        )
        assert feedback.status_code == 200

        progress = client.get("/api/learning/progress").json()["data"]
        assert progress["mastery"]
        verbs = {item["verb"] for item in progress["events"]}
        assert {"created", "generated", "asked", "completed", "rated"}.issubset(verbs)

        updated = client.get("/api/profiles").json()["data"]
        assert len(updated["mistake_history"]) > len(profile["mistake_history"])

        dashboard = client.get("/api/analytics/overview").json()["data"]["personal_signals"]
        assert dashboard["latest_evaluation"]["score"] == report["score"]
        assert dashboard["mastery"]
        assert dashboard["resource_feedback"]["helpful"] >= 1
