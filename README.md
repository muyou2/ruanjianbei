# 智学方舟

面向中国软件杯赛题“基于大模型的个性化资源生成与学习多智能体系统开发”的可运行 Web MVP。系统以 Python 高校课程为示范，通过八个智能体完成学生画像、知识检索、资源生成、RAG 答疑、事实审校和学习评估闭环。

## 一键启动

Windows 双击 `start.bat`，或在 PowerShell 中执行：

```powershell
.\start.ps1
```

首次启动会创建 Python 虚拟环境并安装依赖。启动后访问：

- Web：http://localhost:5173
- OpenAPI：http://localhost:8000/docs

没有配置 API Key 时，系统进入 Mock 演示模式：数据库、检索、智能体流程、测评和画像回写仍真实执行；需要大模型生成的文本使用“画像驱动模板”，不会冒充真实模型结果。

## 当前功能状态表

| 功能 | 状态 | 当前真实实现 |
| --- | --- | --- |
| 自然语言学生画像 | MVP 实现 | 无 Key 时根据输入文本规则抽取八维画像；有 Key 时通过 `LLMService` 结构化抽取 |
| 三类演示学生切换 | 已实现 | `demo_basic`、`demo_practice`、`demo_exam` 独立保存并可切换 |
| 画像 SQLite 持久化 | 已实现 | 每个画像独立保存，当前画像通过 `is_active` 管理 |
| 课程资料上传与切块 | 已实现 | TXT、MD、可提取文本的 PDF |
| Chroma 持久化 | 已实现 | 文档片段和 384 维 Hashing 向量真实写入 Chroma |
| 语义检索 | MVP 实现 | 当前是 Hashing + Chroma，不是 sentence-transformers 强语义模型 |
| 八智能体 | MVP 实现 | 八个独立 Python Agent 类和明确状态流；尚未接入真实 LangGraph |
| 六类资源生成 | Mock 演示 / 待接入真实模型 | 无 Key 时使用画像、薄弱点、偏好、主题和知识库驱动模板；配置模型后走真实生成 |
| RAG 答疑 | MVP 实现 | 真实执行 top-k 检索、引用展示和证据阈值；无 Key 时回答文本为模板 |
| 证据不足阻断 | 已实现 | 检索证据不足时停止扩展回答并提示人工核验 |
| 选择/判断题评分 | 已实现 | 精确匹配自动判分 |
| 简答题评分 | MVP 实现 | 关键词覆盖度评分，前端明确标注 |
| 代码题评分 | MVP 实现 | 关键语句检查，不执行代码，要求人工核验 |
| 测评保存与画像回写 | 已实现 | 评估写入 SQLite，错误知识点写回 `weak_points` 和 `mistake_history` |
| Dashboard 动态变化 | 已实现 | 仅展示当前学生画像、资源、最近测评、错题与薄弱点 |
| 知识点掌握度 | MVP 实现 | 逐题得分按知识点滚动写入 SQLite，不只保留一次总分 |
| 学习行为轨迹 | 已实现 | 画像、资源生成、答疑、测评和反馈记录为轻量 xAPI 风格事件 |
| 资源使用反馈 | MVP 实现 | 学生可标记“有帮助/需要调整”，结果真实持久化并进入 Dashboard |
| ReviewAgent | MVP 实现 | 实时规则检查完整性、引用、证据、夸大表达、画像适配和人工核验需求 |
| 讯飞星火 | 待接入真实模型 | 已预留 OpenAI-compatible 网关配置；官方非兼容鉴权需新增适配器 |
| 视频/动画生成 | 待扩展 | 当前未实现，前端和 README 不宣传为已完成 |
| UCI 数据集 | 扩展分析 Demo | 非核心闭环，不参与当前学生推荐、测评或画像 |

## 项目结构

```text
├─ frontend/       React + Vite + TypeScript + Tailwind CSS
├─ backend/        FastAPI + SQLite + Chroma + 多智能体
├─ course_data/    内置 Python 课程知识库
├─ docs/           架构、API、测试与演示说明
├─ start.ps1
└─ start.bat
```

## 演示顺序

1. 在“学生画像”输入自然语言学习需求。
2. 在“课程知识库”查看内置资料或上传自定义资料。
3. 在“资源生成”观察智能体协作并生成六类资源。
4. 在“智能答疑”提问并查看知识库引用。
5. 在“学习评估”答题，查看薄弱点回写画像。

UCI Student Performance 仅保留在知识库页的“扩展分析 Demo”，不是本系统真实高校 Python 学习数据。研究依据与竞品调研见 [docs/RESEARCH.md](docs/RESEARCH.md)。

赛题要求与代码证据的逐项映射见 [docs/REQUIREMENT_TRACEABILITY.md](docs/REQUIREMENT_TRACEABILITY.md)，AI Coding 使用边界见 [docs/AI_CODING_DISCLOSURE.md](docs/AI_CODING_DISCLOSURE.md)。详细配置见 [backend/README.md](backend/README.md) 与 [frontend/README.md](frontend/README.md)。
