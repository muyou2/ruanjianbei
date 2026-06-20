# 第三方开源项目说明

本项目为团队独立实现，架构设计参考了 OpenMAIC 的多智能体编排、统一模型调用和流式进度理念，未复制其 Next.js 业务代码。

| 项目 | 来源 | 许可证 | 用途 |
| --- | --- | --- | --- |
| OpenMAIC | https://github.com/THU-MAIC/OpenMAIC | MIT | 架构与交互理念参考 |
| FastAPI | https://github.com/fastapi/fastapi | MIT | 后端 Web API |
| React | https://github.com/facebook/react | MIT | 前端框架 |
| Vite | https://github.com/vitejs/vite | MIT | 前端构建 |
| Tailwind CSS | https://github.com/tailwindlabs/tailwindcss | MIT | 样式系统 |
| Chroma | https://github.com/chroma-core/chroma | Apache-2.0 | 向量存储 |
| Mermaid | https://github.com/mermaid-js/mermaid | MIT | 思维导图渲染 |
| pypdf | https://github.com/py-pdf/pypdf | BSD-3-Clause | PDF 文本提取 |
| Sentence Transformers | https://github.com/huggingface/sentence-transformers | Apache-2.0 | 本地语义向量 |
| BAAI/bge-small-zh-v1.5 | https://huggingface.co/BAAI/bge-small-zh-v1.5 | MIT | 中文课程文本 Embedding |
| python-pptx | https://github.com/scanny/python-pptx | MIT | PPTX 文件导出 |
| UCI Student Performance | https://archive.ics.uci.edu/dataset/320/student+performance | CC BY 4.0 | 学习分析公开基准 |

再分发时应保留各项目原始许可证与版权声明。

本项目不将第三方模型或框架能力表述为团队自研；运行时模型服务的使用还需遵守对应平台的服务条款。
