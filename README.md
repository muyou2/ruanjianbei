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

没有配置任何 API Key 时，系统自动使用 Mock 模式，所有演示流程仍可运行。

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

Dashboard 同时展示来自 UCI Student Performance 的公开学习分析基准，并明确数据适用边界。研究依据与竞品调研见 [docs/RESEARCH.md](docs/RESEARCH.md)。

详细配置见 [backend/README.md](backend/README.md) 与 [frontend/README.md](frontend/README.md)。
