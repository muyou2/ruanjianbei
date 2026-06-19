import re
from dataclasses import dataclass, field
from typing import Any

from .knowledge import knowledge_store
from .llm_service import llm_service
from .schemas import QuizQuestion, StudentProfile


DEMO_PROFILES = {
    "demo_basic": StudentProfile(
        demo_key="demo_basic",
        display_name="小林 · 基础薄弱型",
        major="计算机专业",
        grade="大一",
        knowledge_level="基础薄弱",
        learning_goal="补齐 Python 基础并能独立完成简单数据处理",
        weak_points=["变量与数据类型", "函数参数", "Pandas 基础操作"],
        learning_style="循序渐进、低认知负荷",
        resource_preference=["图解", "最小代码示例", "分步练习"],
        mistake_history=["容易混淆列表索引与字典键"],
        source_text="我是计算机专业大一学生，Python 基础比较薄弱，变量、函数参数和 Pandas 都不熟，希望从图解和最小代码例子开始学习。",
        is_active=False,
    ),
    "demo_practice": StudentProfile(
        demo_key="demo_practice",
        display_name="小周 · 实践导向型",
        major="电子信息专业",
        grade="大二",
        knowledge_level="有编程基础",
        learning_goal="通过真实数据项目掌握 Python 数据分析",
        weak_points=["Pandas 数据清洗", "异常值处理", "项目结构"],
        learning_style="项目驱动、边做边学",
        resource_preference=["代码案例", "项目实战", "调试任务"],
        mistake_history=["数据类型转换时忽略缺失值"],
        source_text="我是电子信息专业大二学生，有 Python 基础，但 Pandas 数据清洗和项目组织不熟，希望通过代码案例和项目实战学习。",
        is_active=False,
    ),
    "demo_exam": StudentProfile(
        demo_key="demo_exam",
        display_name="小陈 · 考试复习型",
        major="软件工程专业",
        grade="大二",
        knowledge_level="基础一般",
        learning_goal="系统复习 Python 课程并提高期末考试正确率",
        weak_points=["函数作用域", "面向对象", "Pandas 常用 API"],
        learning_style="考点归纳、错题复盘",
        resource_preference=["知识清单", "对比表格", "练习题"],
        mistake_history=["函数作用域判断题错误", "DataFrame 选列语法错误"],
        source_text="我是软件工程专业大二学生，准备 Python 期末考试，基础一般，函数作用域、面向对象和 Pandas API 容易错，希望通过考点和题目复习。",
        is_active=False,
    ),
}


def _extract_major(text: str) -> str:
    match = re.search(r"(计算机|软件工程|电子信息|人工智能|数据科学|自动化|通信工程)[^，。；\n]{0,6}专业", text)
    if match:
        return match.group(0).replace("我是", "")
    generic = re.search(r"([\u4e00-\u9fffA-Za-z]{2,12}专业)", text)
    return re.sub(r"^(我是|我学的是|目前是)", "", generic.group(1)) if generic else "计算机相关专业"


def _extract_weak_points(text: str) -> list[str]:
    known = [
        "变量", "数据类型", "列表", "字典", "循环", "函数", "函数参数", "函数作用域",
        "面向对象", "异常处理", "文件操作", "NumPy", "Pandas", "数据清洗",
        "缺失值", "异常值", "数据分析项目", "项目结构", "可视化",
    ]
    weakness_words = ["不熟", "不懂", "不会", "薄弱", "容易错", "易错", "一般", "欠缺"]
    weak = []
    for clause in re.split(r"[，。；;\n]", text):
        if any(word in clause for word in weakness_words):
            for topic in known:
                if topic.lower() in clause.lower() and topic not in weak:
                    weak.append(topic)
    return weak or ["函数与数据处理"]


def infer_profile(text: str, display_name: str = "自定义学习者") -> StudentProfile:
    grade_match = re.search(r"(大[一二三四五]|研[一二三]|高职|本科|研究生)", text)
    preferences = []
    for keyword, label in [
        ("图", "图解"),
        ("代码", "代码案例"),
        ("项目", "项目实战"),
        ("练习", "练习题"),
        ("考试", "知识清单"),
        ("视频", "视频讲解"),
        ("对比", "对比表格"),
    ]:
        if keyword in text and label not in preferences:
            preferences.append(label)
    if any(word in text for word in ["零基础", "很薄弱", "基础薄弱", "刚开始"]):
        level = "基础薄弱"
    elif any(word in text for word in ["有基础", "学过", "项目经验", "熟练"]):
        level = "有编程基础"
    else:
        level = "基础一般"
    if "考试" in text or "复习" in text:
        style = "考点归纳、错题复盘"
    elif "项目" in text or "实践" in text:
        style = "项目驱动、边做边学"
    elif "图" in text:
        style = "视觉化、循序渐进"
    else:
        style = "循序渐进"
    clauses = [clause.strip() for clause in re.split(r"[。；;\n]", text) if clause.strip()]
    goal = next(
        (clause for clause in clauses if any(word in clause for word in ["希望", "目标", "想要", "掌握", "准备"])),
        "掌握 Python 程序设计与数据分析",
    )
    return StudentProfile(
        display_name=display_name,
        major=_extract_major(text),
        grade=grade_match.group(1) if grade_match else "大学生",
        knowledge_level=level,
        learning_goal=goal,
        weak_points=_extract_weak_points(text),
        learning_style=style,
        resource_preference=preferences or ["图解", "代码案例"],
        mistake_history=[],
        source_text=text,
    )


def profile_strategy(profile: dict[str, Any]) -> dict[str, str]:
    style = profile.get("learning_style", "")
    preferences = profile.get("resource_preference", [])
    if "考试" in style or "知识清单" in preferences:
        return {
            "type": "exam",
            "label": "考试复习型",
            "sequence": "考点诊断 → 高频易错对比 → 限时练习 → 错题复盘",
            "tone": "突出考点、易错项、判断依据和答题速度",
            "task": "完成一组限时题，并整理一页错题清单",
        }
    if "项目" in style or "项目实战" in preferences:
        return {
            "type": "practice",
            "label": "实践导向型",
            "sequence": "项目任务 → 必要概念 → 分步实现 → 调试与复盘",
            "tone": "用真实数据任务带动概念学习，强调可运行代码",
            "task": "完成一个可复现的数据清洗报告",
        }
    return {
        "type": "basic",
        "label": "基础巩固型",
        "sequence": "概念图解 → 最小示例 → 模仿练习 → 小步测验",
        "tone": "降低认知负荷，解释术语并避免一次引入过多概念",
        "task": "修改一个最小示例并说出每一步输入输出",
    }


def citations_text(citations: list[dict[str, Any]]) -> str:
    return "\n\n".join(
        f"[{index + 1}] {item['title']}：{item['content'][:420]}"
        for index, item in enumerate(citations)
    )


class ProfileAgent:
    name = "ProfileAgent"
    display_name = "画像分析师"

    async def run(self, text: str, display_name: str = "自定义学习者") -> StudentProfile:
        fallback = infer_profile(text, display_name)
        data = await llm_service.structured(
            "你是高校学生画像分析师。只能根据用户原文提取八维画像，不得补造经历。",
            f"用户原文：{text}",
            fallback.model_dump(mode="json"),
        )
        allowed = fallback.model_dump()
        allowed.update({key: value for key, value in data.items() if key in allowed and value not in (None, "")})
        allowed["display_name"] = display_name
        allowed["source_text"] = text
        return StudentProfile(**allowed)


class KnowledgeAgent:
    name = "KnowledgeAgent"
    display_name = "知识检索员"

    async def run(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        return knowledge_store.search(query, top_k)


class PlannerAgent:
    name = "PlannerAgent"
    display_name = "路径规划师"

    async def run(self, topic: str, profile: dict, citations: list[dict]) -> str:
        strategy = profile_strategy(profile)
        weak = "、".join(profile.get("weak_points", [])) or "暂无"
        preference = "、".join(profile.get("resource_preference", []))
        fallback = f"""# {topic} 个性化学习路径

**适配对象**：{profile.get('display_name')} · {strategy['label']}

**当前基础**：{profile.get('knowledge_level')}

**重点补强**：{weak}
**资源偏好**：{preference}

## 推荐顺序
{strategy['sequence']}

1. **诊断与先备检查（15 分钟）**：围绕 {weak} 完成 3 个最小问题，确认真正卡点。
2. **核心学习（30 分钟）**：按“{strategy['tone']}”阅读讲义和思维导图。
3. **针对性练习（25 分钟）**：先做与薄弱点直接相关的选择、判断和简答题。
4. **代码任务（40 分钟）**：{strategy['task']}。
5. **复盘（10 分钟）**：记录错误原因；测评结果将写回学生画像。

**完成标准**：能够解释关键步骤、独立修改代码，并在测评中说明错误原因。"""
        return await llm_service.generate(
            "你是个性化学习路径智能体。必须显式使用画像、薄弱点、偏好和知识库证据。",
            f"主题：{topic}\n画像：{profile}\n策略：{strategy}\n知识库：{citations_text(citations)}",
            fallback,
        )


class ResourceAgent:
    name = "ResourceAgent"
    display_name = "课程讲义师"

    async def run(self, topic: str, profile: dict, citations: list[dict]) -> dict[str, str]:
        strategy = profile_strategy(profile)
        weak = "、".join(profile.get("weak_points", []))
        source_names = "、".join(dict.fromkeys(item["title"] for item in citations)) or "无可用来源"
        fallback = f"""# {topic} 个性化讲义

> 学习者：{profile.get('display_name')}｜策略：{strategy['label']}｜重点：{weak}

## 本次目标
- 理解数据清洗的输入、处理步骤和输出。
- 能针对 `{weak}` 识别常见错误。
- 按照“{strategy['sequence']}”完成练习。

## 核心方法
1. 先使用 `head()`、`info()` 和缺失值统计理解数据。
2. 明确每个字段的数据类型，再决定转换、删除或填充。
3. 对缺失值和异常值保留处理理由，不能机械删除。
4. 每次变换后检查行数、列数和关键统计量。

## 针对你的学习建议
{strategy['tone']}。优先使用你偏好的“{'、'.join(profile.get('resource_preference', []))}”形式。

## 证据来源
本讲义检索并参考：{source_names}。未被知识库覆盖的扩展结论需要人工核验。"""
        lecture = await llm_service.generate(
            "你是 Python 课程讲义智能体。必须适配学生画像，并区分知识库证据与扩展建议。",
            f"主题：{topic}\n画像：{profile}\n策略：{strategy}\n资料：{citations_text(citations)}",
            fallback,
        )
        ppt = f"""# 《{topic}》PPT 大纲

---
## 1. 学习者与目标
- {profile.get('display_name')}：{strategy['label']}
- 当前薄弱点：{weak}
- 学习顺序：{strategy['sequence']}

---
## 2. 数据清洗问题地图
- 数据类型
- 缺失值
- 重复值
- 异常值

---
## 3. 关键 API 与判断依据
- `info()` / `isna()` / `drop_duplicates()`
- 何时删除、何时填充
- 每一步如何验证结果

---
## 4. 个性化演示
- 按“{'、'.join(profile.get('resource_preference', []))}”组织
- 针对 {weak} 设置易错提醒

---
## 5. 练习、项目与复盘
- 四类题目
- {strategy['task']}
- 测评结果写回画像"""
        return {"lecture": lecture, "ppt_outline": ppt}


class QuizAgent:
    name = "QuizAgent"
    display_name = "测评设计师"

    async def run(self, topic: str, profile: dict, citations: list[dict]) -> list[dict[str, Any]]:
        weak = profile.get("weak_points", [])
        focus = weak[0] if weak else "Pandas 数据清洗"
        questions = [
            QuizQuestion(
                id="q1",
                type="single_choice",
                question=f"处理“{topic}”数据前，最合理的第一步是什么？",
                options=["直接删除所有空值", "查看数据结构、类型和缺失情况", "立即绘图", "只读取前一行"],
                answer="查看数据结构、类型和缺失情况",
                explanation="清洗策略必须建立在对字段类型、缺失和数据规模的理解上。",
                knowledge_point="数据理解与检查",
            ),
            QuizQuestion(
                id="q2",
                type="true_false",
                question="发现异常值后应该立即删除，因为异常值一定是错误数据。",
                options=["正确", "错误"],
                answer="错误",
                explanation="异常值可能是录入错误，也可能是真实罕见现象，需要回到数据来源核验。",
                knowledge_point="异常值处理",
            ),
            QuizQuestion(
                id="q3",
                type="short_answer",
                question=f"结合你的薄弱点“{focus}”，说明 Pandas 处理缺失值时为什么不能总是直接删除整行。",
                answer="删除可能造成样本损失和偏差，应结合字段含义、缺失比例和缺失机制选择删除、填充或保留。",
                explanation="关键词包括样本损失、偏差、字段含义、缺失比例、填充。",
                knowledge_point="缺失值处理",
            ),
            QuizQuestion(
                id="q4",
                type="code",
                question="补全代码：读取 data.csv，查看缺失值数量，删除重复行，并用年龄列中位数填充缺失值。",
                answer="df = pd.read_csv('data.csv')\nprint(df.isna().sum())\ndf = df.drop_duplicates()\ndf['age'] = df['age'].fillna(df['age'].median())",
                explanation="MVP 仅检查关键语句，不执行用户代码；最终正确性需要人工核验或安全沙箱。",
                knowledge_point="Pandas 数据清洗代码",
            ),
        ]
        return [question.model_dump() for question in questions]


class CodeAgent:
    name = "CodeAgent"
    display_name = "代码教练"

    async def run(self, topic: str, profile: dict) -> str:
        strategy = profile_strategy(profile)
        if strategy["type"] == "basic":
            task = "代码按读取、检查、清洗三个小步骤展开，每一步打印结果。"
        elif strategy["type"] == "exam":
            task = "代码旁标注每个 API 的作用，并整理容易混淆的 `dropna`、`fillna`、`drop_duplicates`。"
        else:
            task = "将流程封装为可复用函数，并生成清洗前后对比报告。"
        return f"""# {topic}：个性化代码实操

**适配策略**：{strategy['label']}
**本次要求**：{task}

```python
import pandas as pd

def clean_student_data(path: str) -> tuple[pd.DataFrame, dict]:
    df = pd.read_csv(path)
    before = {{"rows": len(df), "missing": int(df.isna().sum().sum())}}

    df = df.drop_duplicates()
    if "age" in df.columns:
        df["age"] = df["age"].fillna(df["age"].median())
    if "score" in df.columns:
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

    after = {{"rows": len(df), "missing": int(df.isna().sum().sum())}}
    return df, {{"before": before, "after": after}}
```

## 实操任务
{strategy['task']}。请记录每个清洗决策的理由，不要只提交最终代码。

> 代码示例未在服务器执行；运行结果需在本地 Python 环境核验。"""


class MindMapAgent:
    name = "MindMapAgent"
    display_name = "知识图谱师"

    async def run(self, topic: str, profile: dict) -> str:
        weak = profile.get("weak_points", ["数据清洗"])
        return f"""mindmap
  root(({topic}))
    学习者
      {profile.get('display_name')}
      {profile_strategy(profile)['label']}
    当前薄弱点
      {weak[0]}
      {weak[1] if len(weak) > 1 else '数据验证'}
    数据理解
      字段类型
      缺失比例
      重复记录
    数据清洗
      类型转换
      缺失值处理
      异常值核验
      去重
    结果验证
      行列数量
      统计摘要
      清洗日志
    学习闭环
      代码任务
      测评
      错题写回画像"""


class ReviewAgent:
    name = "ReviewAgent"
    display_name = "事实审校员"

    async def run(
        self,
        resources: dict[str, Any],
        citations: list[dict],
        profile: dict[str, Any],
    ) -> dict[str, Any]:
        required = ["learning_path", "lecture", "mindmap", "quiz", "code_case", "ppt_outline"]
        missing = [key for key in required if not resources.get(key)]
        text = str(resources)
        absolute_words = [word for word in ["保证百分之百", "绝对正确", "一定能", "无需核验"] if word in text]
        evidence_insufficient = not citations or max((item.get("score", 0) for item in citations), default=0) < 0.08
        profile_terms = [
            profile.get("display_name", ""),
            profile.get("knowledge_level", ""),
            *(profile.get("weak_points", [])[:2]),
            *(profile.get("resource_preference", [])[:2]),
        ]
        profile_hits = sum(bool(term and term in text) for term in profile_terms)
        adapted = profile_hits >= 2
        needs_human_review = evidence_insufficient or bool(absolute_words) or bool(missing)
        checks = {
            "resources_complete": not missing,
            "knowledge_cited": bool(citations),
            "evidence_sufficient": not evidence_insufficient,
            "no_exaggeration": not absolute_words,
            "profile_adapted": adapted,
            "human_review_required": needs_human_review,
        }
        warnings = []
        if missing:
            warnings.append(f"资源不完整：缺少 {', '.join(missing)}")
        if evidence_insufficient:
            warnings.append("知识库证据不足，需要人工核验")
        if absolute_words:
            warnings.append(f"发现绝对化表达：{'、'.join(absolute_words)}")
        if not adapted:
            warnings.append("资源对当前学生画像的适配证据不足")
        score = (
            (25 if not missing else max(0, 25 - len(missing) * 5))
            + (25 if not evidence_insufficient else 5)
            + (20 if not absolute_words else 5)
            + (20 if adapted else 8)
            + (10 if resources.get("quiz") else 0)
        )
        return {
            "passed": score >= 70 and not missing and not evidence_insufficient,
            "score": score,
            "status": "通过" if score >= 70 and not needs_human_review else "需要人工核验",
            "checks": checks,
            "missing_resources": missing,
            "citation_count": len(citations),
            "warnings": warnings,
            "note": "评分由规则实时计算，不是固定分数。",
        }


@dataclass
class OrchestratorState:
    topic: str
    profile: dict[str, Any]
    current_state: str = "profile_loaded"
    state_history: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    resources: dict[str, Any] = field(default_factory=dict)
    agent_outputs: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
