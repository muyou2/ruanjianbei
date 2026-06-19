import asyncio

from app.agents import (
    DEMO_PROFILES,
    PlannerAgent,
    ProfileAgent,
    ReviewAgent,
    infer_profile,
)
from app.analytics import public_dataset_overview
from app.evaluation import score_question
from app.knowledge import cosine, hashing_vector, split_text


def test_profile_rule_is_driven_by_input():
    first = infer_profile(
        "我是计算机专业大二学生，Python 基础一般，函数和 Pandas 不熟，希望通过图解和代码案例学习。"
    )
    second = infer_profile(
        "我是软件工程专业大二学生，准备考试，面向对象容易错，希望多做练习题。"
    )
    assert first.major == "计算机专业"
    assert first.grade == "大二"
    assert "函数" in first.weak_points
    assert "Pandas" in first.weak_points
    assert "图解" in first.resource_preference
    assert second.major == "软件工程专业"
    assert second.learning_style == "考点归纳、错题复盘"
    assert first.model_dump() != second.model_dump()


def test_profile_agent_works_in_mock_mode_without_fixed_profile():
    profile = asyncio.run(
        ProfileAgent().run(
            "我是电子信息专业大一学生，变量和函数参数很薄弱，想通过项目和代码学习。",
            "测试学生",
        )
    )
    assert profile.display_name == "测试学生"
    assert profile.major == "电子信息专业"
    assert "函数参数" in profile.weak_points


def test_three_demo_profiles_produce_different_paths():
    citations = [{"title": "Pandas", "content": "缺失值应根据字段含义处理。", "score": 0.8}]
    planner = PlannerAgent()
    outputs = [
        asyncio.run(planner.run("Pandas 数据清洗", profile.model_dump(), citations))
        for profile in DEMO_PROFILES.values()
    ]
    assert len(set(outputs)) == 3
    assert "基础巩固型" in outputs[0]
    assert "实践导向型" in outputs[1]
    assert "考试复习型" in outputs[2]


def test_split_and_hashing_similarity():
    chunks = split_text("# 函数\n函数接收参数并返回结果。\n" * 100, "Python")
    assert len(chunks) > 1
    same = cosine(hashing_vector("Python 函数"), hashing_vector("Python 函数"))
    different = cosine(hashing_vector("Python 函数"), hashing_vector("天气预报"))
    assert same > different


def test_review_agent_detects_missing_evidence_and_resources():
    profile = DEMO_PROFILES["demo_basic"].model_dump()
    result = asyncio.run(ReviewAgent().run({"lecture": "示例内容"}, [], profile))
    assert result["passed"] is False
    assert result["checks"]["evidence_sufficient"] is False
    assert result["checks"]["resources_complete"] is False
    assert result["status"] == "需要人工核验"


def test_realistic_evaluation_methods():
    choice = {
        "id": "q1",
        "type": "single_choice",
        "answer": "B",
        "explanation": "解析",
    }
    code = {
        "id": "q4",
        "type": "code",
        "answer": "参考答案",
        "explanation": "解析",
    }
    assert score_question(choice, "B")["points"] == 25
    code_result = score_question(code, "df = pd.read_csv('a.csv')\ndf = df.drop_duplicates()")
    assert code_result["manual_review"] is True
    assert code_result["points"] < 25
    assert "未执行代码" in code_result["scoring_method"]


def test_uci_is_only_an_extension_dataset():
    overview = public_dataset_overview()
    assert overview["available"] is True
    assert overview["records"] == 649
    assert any("并非中国高校" in item for item in overview["limitations"])
