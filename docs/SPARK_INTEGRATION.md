# 讯飞星火 API 接入说明

## 当前支持范围

`backend/app/llm_service.py` 当前支持 Bearer Token 的 OpenAI-compatible `/chat/completions` 接口。如果使用讯飞提供的兼容网关，复制 `backend/.env.example` 为 `backend/.env`：

```env
LLM_PROVIDER=spark
SPARK_API_KEY=你的密钥
SPARK_BASE_URL=兼容网关的基础地址
SPARK_MODEL=网关支持的模型名
```

重启后访问 `/api/config/status`，确认 `provider` 为 `spark`、`mock_mode` 为 `false`。

## 如果使用讯飞官方非 OpenAI-compatible 鉴权

需要修改：

1. `backend/app/llm_service.py`
   - 新增 `SparkProvider`。
   - 实现官方签名、WebSocket 或 HTTP 调用。
   - 将返回内容统一转换为 `generate()` 和 `stream()` 接口。
2. `backend/app/config.py`
   - 增加官方接口需要的 `SPARK_APP_ID`、`SPARK_API_SECRET` 等配置。
3. `backend/.env.example`
   - 增加对应环境变量占位符。
4. `backend/tests/`
   - 使用模拟响应测试鉴权、超时、错误回退和流式分片。

不要在源码、截图、提交记录或演示视频中暴露真实密钥。
