# 赛题要求追踪矩阵

本文件把赛题要求映射到可验证代码与演示证据，避免只用文案宣称功能。

| 赛题要求 | 当前状态 | 实现位置 | 演示证据 |
| --- | --- | --- | --- |
| 不少于 6 维动态画像 | 已实现 | `backend/app/agents.py`、`profiles` 表 | 输入自然语言后展示八维画像 |
| 画像随学随新 | 已实现 | 测评接口、`mastery_records`、`learning_events` | 测评前后对比画像和掌握度 |
| 多智能体协作 | MVP 实现 | `backend/app/orchestrator.py` | SSE 展示七阶段、八智能体归因 |
| 至少 5 类资源 | Mock 演示 / 待接入模型 | `backend/app/agents.py` | 展示六类资源及生成者 |
| 动态学习路径 | MVP 实现 | PlannerAgent、掌握度与 Dashboard 推荐 | 低掌握知识点驱动下一步建议 |
| 资源精准推送与反馈 | MVP 实现 | `resource_feedback`、资源反馈接口 | 对资源点击“有帮助/需要调整” |
| 智能辅导 | MVP 实现 | `/api/tutor/chat` | 展示 top-k 引用与证据不足阻断 |
| 学习效果评估 | MVP 实现 | `evaluation.py`、`mastery_records` | 逐题判分、薄弱点、掌握度更新 |
| 学习行为跟踪 | 已实现 | `learning_events` 表 | Dashboard 学习轨迹 |
| 防幻觉与安全审校 | MVP 实现 | ReviewAgent、RAG 阈值 | 空证据时要求人工核验 |
| 生成进度追踪 | 已实现 | SSE 状态流 | 资源页实时阶段与进度 |
| 完整课程知识库 | MVP 实现 | `course_data/` | 课程大纲、模块先修关系与项目量规 |
| 轻量多模态资源 | MVP 实现 | HTML/CSS 数据清洗动画 | Resource Center 直接预览 |
| PPT 文件导出 | 已实现 | `python-pptx` 导出接口 | 下载并使用 PowerPoint/WPS 打开 |
| 真实视频/语音 | 待扩展 | 未宣传为已实现 | 演示中明确边界 |

## 评分项对应

- 创新价值与实用性：画像、真实测评、掌握度、资源反馈形成可解释闭环。
- 功能实现与技术要求：SQLite、Chroma、SSE、多智能体状态和 RAG 引用均可现场验证。
- 配套文档：README、架构、API、测试、演示脚本、来源与本追踪矩阵。
- 演示效果：七分钟内围绕一个学生完成“输入—学习—评估—变化”。
