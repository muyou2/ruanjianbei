# 竞品、研究与数据调研

## 调研来源

1. [OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)：多智能体课堂、两阶段资源生成、流式进度和交互场景。
2. [Khanmigo](https://www.khanacademy.org/khan-labs)：强调通过引导与追问帮助学生思考，而不是简单交付答案。
3. [A Multi-Agent Framework for Personalized Learning](https://arxiv.org/abs/2504.11761)：通过多个教学角色和反思环节提高个性化内容质量。
4. [Personalized Adaptive Learning](https://arxiv.org/abs/2511.11309)：强调动态策略、记忆和教师可控的个性化学习过程。
5. [UCI Student Performance](https://archive.ics.uci.edu/dataset/320/student+performance)：649 条公开学习表现记录，CC BY 4.0。

## 已落实的产品改造

- 智能答疑提供“启发式引导”和“直接讲解”两种教学策略。
- 个性化建议使用“近期学习行为 > 历史测评 > 静态画像”的证据优先级。
- ReviewAgent 输出相关性、事实依据、内容完整、教学适配、内容安全五维评分。
- Dashboard 仅展示当前学生的画像、资源、测评、错题和薄弱点。
- UCI 数据集降级为知识库页的扩展分析 Demo，明确相关性不等于因果。
- 所有外部数据展示来源、许可证和适用边界。

## 本轮针对赛题的设计依据

1. [OpenMAIC](https://github.com/THU-MAIC/OpenMAIC)：借鉴其课程内容先规划后生成、异步进度、持久测验状态和交互式学习思路；本项目仍为独立 FastAPI + React 实现。
2. [MAIC 论文](https://arxiv.org/abs/2409.03512)：强调多智能体课堂在规模化与适应性之间的平衡，以及用真实学习记录分析学习过程。
3. [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)：借鉴 thread/checkpoint 的状态持久化与可观测性思想；当前项目使用轻量状态对象和 SQLite，未宣传为真实 LangGraph。
4. [xAPI Specification](https://github.com/adlnet/xAPI-Spec)：参考学习活动与学习体验的事件化表达，新增轻量 actor—verb—object 学习记录；当前并非完整 xAPI 实现。
5. [Sentence Transformers Semantic Search](https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html)：作为下一步中文语义检索与 retrieve-and-rerank 升级依据；当前仍明确标注为 Hashing MVP。

据此，本轮没有增加装饰性资源类型，而是补充知识点掌握度、学习事件、资源反馈、课程先修关系和赛题要求追踪矩阵，让“动态调整”有真实数据库证据。

## 后续可扩展

- 引入真实高校 Python 课程的匿名化点击流与代码提交记录。
- 使用知识追踪模型估计知识点掌握概率。
- 增加教师端审核、人工修订与资源发布工作流。
- 在用户授权后采集更细粒度学习事件，并提供数据删除与导出。
