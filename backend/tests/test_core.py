import asyncio

from app.agents import ProfileAgent, ReviewAgent, infer_profile
from app.analytics import public_dataset_overview
from app.knowledge import cosine, hashing_vector, split_text


def test_profile_rule_extracts_eight_dimensions():
    profile = infer_profile("我是计算机专业大二学生，函数不太懂，希望通过图解和代码案例学习 Python。")
    assert profile.major == "计算机专业"
    assert profile.grade == "大二"
    assert profile.weak_points
    assert "图解" in profile.resource_preference


def test_profile_agent_works_in_mock_mode():
    profile = asyncio.run(ProfileAgent().run("我是电子信息专业大一学生，想通过项目学习 Python。"))
    assert profile.learning_goal
    assert profile.resource_preference


def test_split_and_hashing_similarity():
    chunks = split_text("# 函数\n函数接收参数并返回结果。\n" * 100, "Python")
    assert len(chunks) > 1
    same = cosine(hashing_vector("Python 函数"), hashing_vector("Python 函数"))
    different = cosine(hashing_vector("Python 函数"), hashing_vector("天气预报"))
    assert same > different


def test_review_agent_warns_without_citations():
    result = asyncio.run(ReviewAgent().run({"lecture": "示例内容"}, []))
    assert result["citation_count"] == 0
    assert result["warnings"]
    assert len(result["dimensions"]) == 5


def test_uci_public_benchmark_is_available():
    overview = public_dataset_overview()
    assert overview["available"] is True
    assert overview["records"] == 649
    assert overview["license"] == "CC BY 4.0"
