# 讯飞星火 API 配置与验收

## 配置

复制 `backend/.env.example` 为 `backend/.env`：

```env
LLM_PROVIDER=xfyun
LLM_TIMEOUT_SECONDS=60
XFYUN_API_KEY=你的 API Key
XFYUN_BASE_URL=https://spark-api-open.xf-yun.com/v1
XFYUN_MODEL=generalv3.5
```

配置名称与 `backend/app/config.py` 完全一致。密钥不得提交到 Git。

## 重启

```powershell
cd F:\软件杯
.\start.ps1
```

## 验收

打开 Dashboard 点击“测试当前模型连接”，或访问：

```text
GET http://localhost:8000/api/config/llm-test
```

成功标准：

- `provider` 为 `xfyun`
- `model` 为配置模型
- `success` 为 `true`
- `tested_real_model` 为 `true`
- `fallback_used` 为 `false`
- `error_message` 为空

如果密钥、地址或模型错误，接口会返回 `fallback_used=true` 与错误摘要；系统仍使用 Mock 保证演示流程，但不能宣称真实模型已接入成功。

