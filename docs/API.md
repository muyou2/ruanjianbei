# API 摘要

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/config/status` | 模型与向量后端状态 |
| GET | `/api/config/llm-test` | 测试当前模型并返回成功、回退和错误信息 |
| GET | `/api/analytics/overview` | 个人学习信号与开放数据基准 |
| GET/POST/PUT | `/api/profiles` | 查询、生成、更新画像 |
| GET | `/api/profiles/all` | 查询全部演示/自定义画像 |
| POST | `/api/profiles/select` | 切换当前学习者 |
| GET/POST | `/api/documents` | 列表、上传资料 |
| DELETE | `/api/documents/{id}` | 删除资料 |
| POST | `/api/knowledge/search` | 课程片段检索 |
| POST | `/api/resources/generate` | SSE 生成资源包 |
| GET | `/api/resources` | 历史资源包 |
| GET | `/api/resources/{id}/pptx` | 导出个性化 PPTX 文件 |
| POST | `/api/resources/{id}/feedback` | 保存当前学生的资源使用反馈 |
| POST | `/api/tutor/chat` | SSE RAG 答疑 |
| GET | `/api/quizzes` | 获取题目 |
| POST | `/api/evaluations/submit` | 批改与画像回写 |
| GET | `/api/learning/progress` | 知识点掌握度与学习行为轨迹 |

完整交互模型以运行时 `/docs` 为准。
