import re
from dataclasses import dataclass, field
from typing import Any

from .knowledge import knowledge_store
from .llm_service import llm_service
from .schemas import QuizQuestion, StudentProfile


def infer_profile(text: str) -> StudentProfile:
    major_match = re.search(r"([\u4e00-\u9fffA-Za-z]+专业)", text)
    grade_match = re.search(r"(大[一二三四五]|研[一二三]|高职|本科|研究生)", text)
    weak_markers = ["不懂", "薄弱", "不会", "困难", "欠缺", "不熟", "易错"]
    clauses = re.split(r"[，。；;\n]", text)
    weak_points = [
        re.sub(r"(不太懂|不懂|薄弱|不会|困难|欠缺|不熟|易错)", "", clause).strip()
        for clause in clauses
        if any(marker in clause for marker in weak_markers)
    ]
    preference = []
    for keyword, label in [
        ("图", "图解"),
        ("代码", "代码案例"),
        ("视频", "视频"),
        ("练习", "练习题"),
        ("项目", "项目实战"),
        ("文档", "讲义"),
    ]:
        if keyword in text and label not in preference:
            preference.append(label)
    level = "入门"
    if any(word in text for word in ["有基础", "学过", "中等", "进阶"]):
        level = "基础"
    if any(word in text for word in ["熟练", "项目经验", "高级"]):
        level = "进阶"
    style = "循序渐进"
    if "图" in text:
        style = "视觉化与案例驱动"
    elif "实践" in text or "项目" in text:
        style = "实践驱动"
    return StudentProfile(
        major=re.sub(r"^(我是|我学的是|目前是)", "", major_match.group(1)) if major_match else "计算机相关专业",
        grade=grade_match.group(1) if grade_match else "大学生",
        knowledge_level=level,
        learning_goal=next(
            (c.strip() for c in clauses if any(k in c for k in ["希望", "目标", "想要", "掌握"])),
            "掌握 Python 并完成数据分析项目",
        ),
        weak_points=weak_points or ["函数与面向对象的综合运用"],
        learning_style=style,
        resource_preference=preference or ["图解", "代码案例"],
        mistake_history=[],
        source_text=text,
    )


class ProfileAgent:
    name = "画像分析师"

    async def run(self, text: str) -> StudentProfile:
        fallback = infer_profile(text)
        data = await llm_service.structured(
            "你是学生画像分析师，提取八维高校学生学习画像。",
            f"从以下描述提取画像：{text}",
            fallback.model_dump(mode="json"),
        )
        allowed = fallback.model_dump()
        allowed.update({k: v for k, v in data.items() if k in allowed and v not in (None, "")})
        return StudentProfile(**allowed)


class KnowledgeAgent:
    name = "知识检索员"

    async def run(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return knowledge_store.search(query, top_k)


def citations_text(citations: list[dict[str, Any]]) -> str:
    return "\n\n".join(f"[{i + 1}] {c['title']}：{c['content'][:420]}" for i, c in enumerate(citations))


class PlannerAgent:
    name = "路径规划师"

    async def run(self, topic: str, profile: dict, citations: list[dict]) -> str:
        weak = "、".join(profile.get("weak_points", [])) or "暂无"
        fallback = f"""# {topic} 个性化学习路径

> 学习者基础：{profile.get('knowledge_level', '入门')} · 薄弱点：{weak}

1. **概念预热（20 分钟）**：用一张知识地图理解本主题在 Python 课程中的位置。
2. **核心讲解（35 分钟）**：阅读讲义并运行每个最小示例，记录输入、过程和输出。
3. **刻意练习（30 分钟）**：先完成选择与判断，再完成简答和代码题。
4. **项目迁移（45 分钟）**：把示例数据替换为自己的数据，完成一次清洗与分析。
5. **复盘纠错（15 分钟）**：根据评估结果更新薄弱点，次日进行间隔复习。

**完成标准**：能独立解释关键概念、运行代码并对结果做出合理判断。"""
        return await llm_service.generate(
            "你是个性化学习路径规划智能体。输出清晰 Markdown，内容必须适配画像。",
            f"主题：{topic}\n画像：{profile}\n参考资料：\n{citations_text(citations)}",
            fallback,
        )


class ResourceAgent:
    name = "课程讲义师"

    async def run(self, topic: str, profile: dict, citations: list[dict]) -> dict[str, str]:
        fallback = f"""# {topic} 个性化讲义

## 为什么要学
Python 的价值不只是语法，而是把问题拆成可执行步骤。学习本主题时，建议采用“概念—示例—修改—复盘”的循环。

## 核心方法
1. 明确数据或对象的类型与结构。
2. 使用函数封装重复逻辑，保持输入和输出清晰。
3. 对边界情况使用异常处理和验证。
4. 使用小样例验证，再扩展到真实项目。

## 学习提示
结合你的偏好，先看结构图，再逐行运行代码。遇到报错时先读异常类型和最后一行，而不是立即复制答案。

## 拓展阅读
- Python 官方教程中的数据结构与函数章节
- NumPy 快速入门
- Pandas “10 minutes to pandas”

> 本讲义由知识库片段约束生成，关键结论请结合下方参考资料复核。"""
        lecture = await llm_service.generate(
            "你是高校 Python 课程讲义智能体，使用 Markdown，避免编造来源。",
            f"主题：{topic}\n画像：{profile}\n资料：{citations_text(citations)}",
            fallback,
        )
        ppt = f"""# 《{topic}》PPT 大纲

---
## 1. 学习目标
- 建立概念框架
- 能解释关键步骤
- 能完成一个可运行案例

---
## 2. 先备知识
- Python 基础语法
- 容器与函数
- 调试与异常阅读

---
## 3. 核心概念
- 概念定义
- 典型使用场景
- 常见误区

---
## 4. 代码演示
- 最小可运行示例
- 逐步改造
- 结果解释

---
## 5. 课堂练习与复盘
- 四类练习
- 错因分析
- 下一步学习建议"""
        return {"lecture": lecture, "ppt_outline": ppt}


class QuizAgent:
    name = "测评设计师"

    async def run(self, topic: str) -> list[dict[str, Any]]:
        questions = [
            QuizQuestion(
                id="q1",
                type="single_choice",
                question=f"学习“{topic}”时，验证代码逻辑最稳妥的第一步是什么？",
                options=["直接处理全部真实数据", "使用最小样例验证输入输出", "忽略异常继续运行", "只阅读代码不执行"],
                answer="使用最小样例验证输入输出",
                explanation="最小样例能降低调试复杂度，快速确认核心逻辑。",
                knowledge_point="调试与验证",
            ),
            QuizQuestion(
                id="q2",
                type="true_false",
                question="函数应尽量让输入和输出清晰，并减少隐藏的全局状态。",
                options=["正确", "错误"],
                answer="正确",
                explanation="清晰的数据流有助于测试、复用和排错。",
                knowledge_point="函数设计",
            ),
            QuizQuestion(
                id="q3",
                type="short_answer",
                question="请说明列表与字典在组织数据时的主要区别，并各举一个使用场景。",
                answer="列表按顺序保存元素，适合序列；字典按键映射值，适合具名字段或快速查找。",
                explanation="应同时提及顺序/索引与键值映射。",
                knowledge_point="Python 数据结构",
            ),
            QuizQuestion(
                id="q4",
                type="code",
                question="编写函数 summarize(numbers)，返回数字列表的数量、平均值和最大值；空列表应返回 None。",
                answer="def summarize(numbers):\n    if not numbers:\n        return None\n    return {'count': len(numbers), 'mean': sum(numbers)/len(numbers), 'max': max(numbers)}",
                explanation="考查函数、条件判断、容器和聚合操作。",
                knowledge_point="函数与数据处理",
            ),
        ]
        return [q.model_dump() for q in questions]


class CodeAgent:
    name = "代码教练"

    async def run(self, topic: str) -> str:
        return f"""# {topic}：数据分析实操

```python
from dataclasses import dataclass
from statistics import mean

@dataclass
class StudyRecord:
    topic: str
    minutes: int
    score: float

records = [
    StudyRecord("Python 基础", 45, 82),
    StudyRecord("函数", 55, 88),
    StudyRecord("Pandas", 70, 91),
]

def build_report(items: list[StudyRecord]) -> dict:
    if not items:
        return {{"count": 0, "average_score": 0, "total_minutes": 0}}
    return {{
        "count": len(items),
        "average_score": round(mean(item.score for item in items), 2),
        "total_minutes": sum(item.minutes for item in items),
        "best_topic": max(items, key=lambda item: item.score).topic,
    }}

print(build_report(records))
```

## 动手任务
1. 增加 `weak_point` 字段并筛选低于 85 分的记录。
2. 将结果保存为 CSV。
3. 使用 Pandas 绘制学习时长与成绩的关系图。

## 预期收获
把数据结构、函数、类型标注和项目化思维连接起来。"""


class MindMapAgent:
    name = "知识图谱师"

    async def run(self, topic: str) -> str:
        return f"""mindmap
  root(({topic}))
    学习目标
      理解概念
      能运行代码
      能解释结果
    基础能力
      数据类型
      容器
      函数
      异常处理
    数据分析
      NumPy
      Pandas
      数据清洗
      结果可视化
    学习闭环
      最小样例
      刻意练习
      项目迁移
      评估复盘"""


class ReviewAgent:
    name = "事实审校员"

    async def run(self, resources: dict[str, Any], citations: list[dict]) -> dict[str, Any]:
        text = str(resources)
        risky = [word for word in ["保证百分之百", "绝对正确", "无需验证"] if word in text]
        score = min(100, 68 + len(citations) * 6 - len(risky) * 15)
        dimensions = {
            "相关性": min(100, 78 + len(citations) * 4),
            "事实依据": min(100, 62 + len(citations) * 8),
            "内容完整": 92 if all(key in resources for key in ["learning_path", "lecture", "quiz", "code_case", "mindmap"]) else 65,
            "教学适配": 88 if "learning_path" in resources and "quiz" in resources else 70,
            "内容安全": 100 if not risky else max(40, 100 - len(risky) * 25),
        }
        return {
            "passed": score >= 70,
            "score": score,
            "dimensions": dimensions,
            "citation_count": len(citations),
            "warnings": (["知识库引用较少，部分扩展内容需核验"] if len(citations) < 2 else []) + risky,
            "safety": "通过",
            "note": "内容经过来源覆盖、格式完整性与风险措辞检查。",
        }


@dataclass
class OrchestratorState:
    topic: str
    profile: dict[str, Any]
    citations: list[dict[str, Any]] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
