import json
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from typing import Any

import httpx

from .config import Settings, get_settings


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    model: str


@dataclass
class GenerationResult:
    content: str
    provider: str
    model: str
    source: str
    used_real_model: bool
    fallback_used: bool
    error: str | None = None

    def metadata(self, rag: bool = False) -> dict[str, Any]:
        data = asdict(self)
        data.pop("content")
        data["rag_enhanced"] = rag
        data["label"] = (
            "真实模型失败后回退 Mock"
            if self.fallback_used
            else "知识库检索增强生成"
            if rag and self.used_real_model
            else "真实大模型生成"
            if self.used_real_model
            else "Mock 规则生成"
        )
        return data


class LLMService:
    """所有 Agent 共用的模型网关；真实调用失败时显式回退 Mock。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.requested_provider = self.settings.llm_provider.lower().strip() or "mock"
        self.provider = self._resolve_provider()
        self.configuration_error = self._configuration_error()
        self.last_test_result: dict[str, Any] | None = None

    def _resolve_provider(self) -> ProviderConfig | None:
        requested = self.settings.llm_provider.lower().strip()
        if requested in {"", "mock"}:
            return None
        candidates = {
            "xfyun": ProviderConfig(
                "xfyun",
                self.settings.xfyun_api_key,
                self.settings.xfyun_base_url,
                self.settings.xfyun_model,
            ),
            "openai_compatible": ProviderConfig(
                "openai_compatible",
                self.settings.openai_compatible_api_key,
                self.settings.openai_compatible_base_url,
                self.settings.openai_compatible_model,
            ),
            "deepseek": ProviderConfig(
                "deepseek",
                self.settings.deepseek_api_key,
                self.settings.deepseek_base_url,
                self.settings.deepseek_model,
            ),
            "qwen": ProviderConfig(
                "qwen",
                self.settings.qwen_api_key,
                self.settings.qwen_base_url,
                self.settings.qwen_model,
            ),
        }
        item = candidates.get(requested)
        return item if item and item.api_key and item.base_url and item.model else None

    def _configuration_error(self) -> str | None:
        if self.requested_provider == "mock":
            return None
        if self.requested_provider not in {
            "xfyun",
            "openai_compatible",
            "deepseek",
            "qwen",
        }:
            return f"不支持的 LLM_PROVIDER：{self.requested_provider}"
        if self.provider is None:
            return f"{self.requested_provider} 配置不完整，请检查 API Key、Base URL 和模型名"
        return None

    @property
    def is_mock(self) -> bool:
        return self.provider is None

    @property
    def provider_name(self) -> str:
        return self.provider.name if self.provider else self.requested_provider

    @property
    def model_name(self) -> str:
        if self.provider:
            return self.provider.model
        configured = {
            "xfyun": self.settings.xfyun_model,
            "openai_compatible": self.settings.openai_compatible_model,
            "deepseek": self.settings.deepseek_model,
            "qwen": self.settings.qwen_model,
        }
        return configured.get(self.requested_provider) or "mock-rules"

    async def generate_result(
        self,
        system: str,
        prompt: str,
        fallback: str,
    ) -> GenerationResult:
        if not self.provider:
            fallback_used = self.requested_provider != "mock"
            return GenerationResult(
                fallback,
                self.provider_name,
                self.model_name,
                "mock_fallback" if fallback_used else "mock",
                False,
                fallback_used,
                self.configuration_error,
            )
        url = self.provider.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.provider.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.35,
        }
        try:
            async with httpx.AsyncClient(timeout=self.settings.llm_timeout_seconds) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.provider.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                if not isinstance(content, str) or not content.strip():
                    raise ValueError("模型返回空内容")
                return GenerationResult(
                    content,
                    self.provider.name,
                    self.provider.model,
                    "real_model",
                    True,
                    False,
                )
        except Exception as error:
            return GenerationResult(
                fallback,
                self.provider.name,
                self.provider.model,
                "mock_fallback",
                False,
                True,
                f"{type(error).__name__}: {str(error)[:180]}",
            )

    async def test_connection(self) -> dict[str, Any]:
        result = await self.generate_result(
            "你是模型连通性测试助手。只需简短确认服务可用。",
            "请回复：智学方舟模型连接正常。",
            "Mock 模式可用；当前未获得真实模型响应。",
        )
        is_mock_request = self.requested_provider == "mock"
        test = {
            "provider": self.provider_name,
            "model": self.model_name,
            "success": is_mock_request or result.used_real_model,
            "response_preview": result.content[:120],
            "fallback_used": result.fallback_used,
            "error_message": result.error,
            "mock_mode": self.is_mock,
            "tested_real_model": result.used_real_model,
        }
        self.last_test_result = test
        return test

    async def generate(self, system: str, prompt: str, fallback: str) -> str:
        return (await self.generate_result(system, prompt, fallback)).content

    async def structured_result(
        self,
        system: str,
        prompt: str,
        fallback: dict[str, Any],
    ) -> tuple[dict[str, Any], GenerationResult]:
        result = await self.generate_result(
            system + "\n只返回合法 JSON，不要使用 Markdown 代码块。",
            prompt,
            json.dumps(fallback, ensure_ascii=False),
        )
        try:
            start, end = result.content.index("{"), result.content.rindex("}") + 1
            return json.loads(result.content[start:end]), result
        except (ValueError, json.JSONDecodeError):
            result.content = json.dumps(fallback, ensure_ascii=False)
            result.fallback_used = True
            result.used_real_model = False
            result.source = "mock_fallback"
            result.error = result.error or "模型未返回合法 JSON"
            return fallback, result

    async def structured(
        self,
        system: str,
        prompt: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        data, _ = await self.structured_result(system, prompt, fallback)
        return data

    async def stream_result(
        self,
        system: str,
        prompt: str,
        fallback: str,
    ) -> tuple[GenerationResult, AsyncIterator[str]]:
        result = await self.generate_result(system, prompt, fallback)

        async def iterator() -> AsyncIterator[str]:
            step = 24
            for index in range(0, len(result.content), step):
                yield result.content[index:index + step]

        return result, iterator()

    async def stream(self, system: str, prompt: str, fallback: str) -> AsyncIterator[str]:
        _, iterator = await self.stream_result(system, prompt, fallback)
        async for chunk in iterator:
            yield chunk


llm_service = LLMService()
