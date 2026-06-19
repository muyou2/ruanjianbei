# API 摘要

| 方法 | 地址 | 用途 |
| --- | --- | --- |
| GET | `/api/health` | 服务健康检查 |
| GET | `/api/config/status` | 模型与向量后端状态 |
| GET | `/api/analytics/overview` | 个人学习信号与开放数据基准 |
| GET/POST/PUT | `/api/profiles` | 查询、生成、更新画像 |
| GET/POST | `/api/documents` | 列表、上传资料 |
| DELETE | `/api/documents/{id}` | 删除资料 |
| POST | `/api/knowledge/search` | 课程片段检索 |
| POST | `/api/resources/generate` | SSE 生成资源包 |
| GET | `/api/resources` | 历史资源包 |
| POST | `/api/tutor/chat` | SSE RAG 答疑 |
| GET | `/api/quizzes` | 获取题目 |
| POST | `/api/evaluations/submit` | 批改与画像回写 |

完整交互模型以运行时 `/docs` 为准。
