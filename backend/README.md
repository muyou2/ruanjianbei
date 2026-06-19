# 智学方舟后端

## 手动启动

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

复制 `.env.example` 为 `.env` 可配置模型。优先顺序为讯飞星火、OpenAI-compatible、DeepSeek、Qwen，均未配置时使用 Mock。

Mock 模式只替代大模型文本生成。SQLite、Chroma、top-k 检索、Agent 状态流、判分和画像回写仍真实执行。讯飞接入细节见 [../docs/SPARK_INTEGRATION.md](../docs/SPARK_INTEGRATION.md)。

运行数据保存在 `backend/runtime/`，包括 SQLite、上传文件和 Chroma 数据。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pytest
```
