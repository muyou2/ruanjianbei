# 智学方舟后端

## 手动启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

复制 `.env.example` 为 `.env`，通过 `LLM_PROVIDER=mock|xfyun|openai_compatible|deepseek|qwen` 显式选择模型。真实调用失败时自动回退 Mock，并保存来源与错误摘要。

Mock 模式只替代大模型文本生成。SQLite、Chroma、top-k 检索、Agent 状态流、PPTX 导出、判分和画像回写仍真实执行。讯飞接入细节见 [../docs/SPARK_INTEGRATION.md](../docs/SPARK_INTEGRATION.md)。

安装本地语义检索：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-semantic.txt
```

若 sentence-transformers 或模型不可用，系统自动回退 Hashing MVP 检索。

运行数据保存在 `backend/runtime/`，包括 SQLite、上传文件和 Chroma 数据。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
```
