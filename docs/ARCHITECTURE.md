# 系统架构说明

```mermaid
flowchart LR
  UI[React Web] --> API[FastAPI]
  API --> DB[(SQLite)]
  DB --> EVT[学习事件 / 掌握度 / 资源反馈]
  API --> KB[Knowledge Store]
  KB --> CH[(Chroma / BGE Semantic)]
  KB --> HASH[Hashing Fallback]
  API --> ORCH[Orchestrator]
  ORCH --> P[Profile Agent]
  ORCH --> K[Knowledge Agent]
  ORCH --> G[Planner / Resource / Quiz / Code / MindMap]
  G --> R[Review Agent]
  ORCH --> LLM[LLMService]
  LLM --> S[讯飞星火]
  LLM --> O[OpenAI-compatible / DeepSeek / Qwen]
  LLM --> M[Mock Fallback]
  API --> TEST[LLM Test / 状态验收]
```

资源生成使用 LangGraph 风格状态对象，但 MVP 不强依赖 LangGraph。当前保存并展示以下真实状态：

```text
profile_loaded
→ knowledge_retrieved
→ plan_generated
→ resources_generated
→ quiz_generated
→ review_completed
→ saved
```

资源包同时保存 `profile_snapshot`、`citations`、`workflow` 和 `agent_outputs`，可以追溯每类资源由哪个 Agent 生成。

长任务通过 SSE 返回 `progress`、`citations`、`resource`、`review` 和 `done` 事件，避免页面长时间白屏。

当前优先使用 `sentence-transformers` 加载 `BAAI/bge-small-zh-v1.5`，模型或依赖不可用时自动切换 Hashing MVP 检索。两种模式均由前端和 `/api/config/status` 如实展示。

模型调用统一经过 `LLMService`。`/api/config/llm-test` 使用同一调用链测试当前 Provider；真实调用失败会返回 `fallback_used=true` 和错误摘要，不会将 Mock 响应伪装为真实模型结果。

学习分析层新增三类可审计数据：

- `learning_events`：采用轻量 actor（当前画像）—verb—object 结构记录真实学习行为，设计思想参考 xAPI，但不宣称完整兼容。
- `mastery_records`：按知识点累计真实逐题得分、尝试次数和最近得分。
- `resource_feedback`：记录资源包是否有帮助，为后续推荐策略提供学生反馈证据。
- `learning_tasks`：把学习路径落成“讲义—导图—代码—练习—复盘”五步任务，保存完成时间与剩余学习时长。

Resource Center 和 Dashboard 读取同一份任务状态，因此学生刷新页面或重新打开项目后可以继续学习，而不是重新从资源列表中寻找下一步。
