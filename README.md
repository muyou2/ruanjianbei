# 智学方舟

面向中国软件杯赛题“基于大模型的个性化资源生成与学习多智能体系统开发”的高校 Python 个性化学习平台。

```text
画像构建 → 知识检索 → 多智能体资源生成 → RAG 智能辅导
→ 学习评估 → 薄弱点与掌握度更新 → 动态调整
```

## 一键启动

双击 `start.bat`，或运行：

```powershell
.\start.ps1
```

- Web：http://localhost:5173
- OpenAPI：http://localhost:8000/docs

无 API Key 时自动进入 Mock 模式；数据库、检索、PPT 导出、测评、画像写回和学习轨迹仍真实执行。

## 功能真实性说明表

| 功能 | 状态 | 实现边界 |
| --- | --- | --- |
| 八维画像与 SQLite | 已实现 | 离线规则抽取；配置模型后优先真实结构化抽取 |
| 文档上传、切块、Chroma | 已实现 | TXT、MD、可提取文本 PDF |
| sentence-transformers 语义检索 | 已实现 / 可回退 | 默认 BGE 中文模型；失败自动回退 Hashing MVP |
| 八智能体流水线 | 已实现 | 七阶段 SSE、输出归因和资源包持久化 |
| 统一真实模型调用 | 已实现 | xfyun、OpenAI-compatible、DeepSeek、Qwen；失败显式回退 |
| 个性化资源与 RAG 答疑 | 已实现 | 显示智能体、生成来源、知识库证据和核验状态 |
| 无 Key 时的文本生成 | Mock 演示 | 使用输入驱动规则与课程模板；页面明确标注 Mock |
| PPTX 文件导出 | 已实现 | 生成六页个性化演示文稿 |
| HTML 动态流程图 | MVP 实现 | Resource Center 直接预览 Pandas 清洗动画 |
| 选择/判断题评分 | 已实现 | 精确匹配 |
| 简答题、代码题 | MVP 实现 | 关键词/关键语句检查，不执行代码 |
| 掌握度、推荐 | MVP 实现 | 基于逐题得分、轨迹与资源反馈 |
| 画像更新与 Dashboard | 已实现 | 薄弱点、掌握度和学习事件真实写回 |
| 视频、语音、Docker 沙箱 | 待扩展 | 当前不宣传为已完成 |
| 教师端、登录、DKT/BKT、复杂 checkpoint | 待扩展 | 不属于初赛版本 |

“真实实现”表示代码、数据库或文件输出可现场验证；“MVP 实现”表示功能真实运行但算法较轻量；“Mock”只替代无 Key 时的大模型文本，不替代检索、编排、评分、PPTX 或画像写回。

## 技术架构

- React + Vite + TypeScript + Tailwind CSS
- FastAPI + SQLite + Chroma
- sentence-transformers + `BAAI/bge-small-zh-v1.5`
- python-pptx
- 统一 `LLMService`，Agent 不直接请求外部 API

## 多智能体与 RAG

```text
profile_loaded → knowledge_retrieved → plan_generated
→ resources_generated → quiz_generated → review_completed → saved
```

```text
用户问题 → 语义向量/Hashing → Chroma top-k → 证据阈值
→ LLMService → 带来源、相关度和检索模式的回答
```

证据不足时，系统停止确定性生成并提示补充课程资料或人工核验。

## 配置真实大模型

复制 `backend/.env.example` 为 `backend/.env`。

讯飞星火：

```env
LLM_PROVIDER=xfyun
XFYUN_API_KEY=你的 API Key
XFYUN_BASE_URL=https://spark-api-open.xf-yun.com/v1
XFYUN_MODEL=generalv3.5
```

还支持：

```env
LLM_PROVIDER=mock
LLM_PROVIDER=openai_compatible
LLM_PROVIDER=deepseek
LLM_PROVIDER=qwen
```

真实调用失败时自动回退，并在前端标记“Mock 规则生成 / 真实模型失败后回退 Mock”。

### 验证真实模型是否接入成功

1. 配置 `backend/.env` 并重启。
2. 打开 Dashboard，检查 Provider、模型名称和 Mock 状态。
3. 点击“测试当前模型连接”，或访问：

```text
GET http://localhost:8000/api/config/llm-test
```

真实接入成功应满足：

```json
{
  "success": true,
  "fallback_used": false,
  "tested_real_model": true
}
```

若 `fallback_used=true`，说明系统已明确回退 Mock，应根据 `error_message` 检查密钥、地址或模型名。

## 语义检索

```powershell
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements-semantic.txt
```

```env
EMBEDDING_PROVIDER=auto
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DEVICE=cpu
```

知识库页会如实显示“语义向量检索”或“Hashing MVP 检索”。

## PPT 与轻量多模态

- 在资源页的“PPT 大纲”Tab 下载 `.pptx`。
- PPT 包含标题、目标、知识讲解、代码、练习和下一步建议。
- “动态流程图”Tab 展示 Pandas 数据清洗六步 HTML/CSS 动画。
- 视频生成和讯飞语音合成为待扩展能力。

## 七分钟演示

1. 切换 `demo_basic` 并输入指定学生描述。
2. 展示八维画像和课程知识库。
3. 检索 `dropna 和 fillna 如何选择`，展示 top-k、来源和模式。
4. 生成“Pandas 数据清洗与分析综合实践”资源包。
5. 展示七阶段时间线、七类资源和生成来源。
6. 下载 PPTX，预览动态流程图。
7. Tutor Chat 提问并展开引用。
8. 完成测评，展示逐题得分与画像写回。
9. 返回 Dashboard 展示掌握度和学习轨迹变化。

## 内置课程与不足

`course_data/` 为项目原创示例资料，覆盖 17 个 Python 与数据分析主题，不声称来自真实高校教材。

当前不足：真实模型质量依赖外部服务；首次下载 BGE 需要网络；简答、代码题、掌握度仍为 MVP；HTML 动画不等于真实视频；教师审核端、账号体系、安全代码沙箱和复杂知识追踪尚未实现。

更多资料：[赛题追踪](docs/REQUIREMENT_TRACEABILITY.md) · [演示脚本](docs/DEMO_SCRIPT.md) · [讯飞配置](docs/XFYUN_SETUP.md) · [当前不足](docs/LIMITATIONS.md) · [AI Coding 说明](docs/AI_CODING_DISCLOSURE.md)
