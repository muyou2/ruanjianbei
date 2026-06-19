# 讯飞星火 API 接入说明

所有智能体统一经过 `backend/app/llm_service.py`，不会直接请求外部模型。

复制 `backend/.env.example` 为 `backend/.env`：

```env
LLM_PROVIDER=xfyun
XFYUN_API_KEY=你的密钥
XFYUN_BASE_URL=https://spark-api-open.xf-yun.com/v1
XFYUN_MODEL=generalv3.5
```

重启后访问 `/api/config/status`，确认：

- `provider` 为 `xfyun`
- `mock_mode` 为 `false`
- `model` 为配置的模型名称

当前适配 OpenAI-compatible `/chat/completions` 形式。若账号使用其他讯飞鉴权形式，应在 `LLMService` 内增加 Provider 适配，但 Agent 接口无需修改。

真实请求超时、鉴权失败、返回空内容或 JSON 不合法时，系统自动使用 Mock fallback，并把 `fallback_used`、错误摘要和生成来源保存到资源包、展示在前端。
