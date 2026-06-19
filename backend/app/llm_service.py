import json
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings, get_settings


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str
    model: str


class LLMService:
    """统一模型调用层。未配置密钥时自动进入稳定的 Mock 模式。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.provider = self._resolve_provider()

    def _resolve_provider(self) -> ProviderConfig | None:
        candidates = [
            ProviderConfig("spark", self.settings.spark_api_key, self.settings.spark_base_url, self.settings.spark_model),
            ProviderConfig("openai", self.settings.openai_api_key, self.settings.openai_base_url, self.settings.openai_model),
            ProviderConfig("deepseek", self.settings.deepseek_api_key, self.settings.deepseek_base_url, self.settings.deepseek_model),
            ProviderConfig("qwen", self.settings.qwen_api_key, self.settings.qwen_base_url, self.settings.qwen_model),
        ]
        requested = self.settings.llm_provider.lower()
        for item in candidates:
            if item.api_key and item.base_url and (requested in {"auto", item.name}):
                return item
        return None

    @property
    def is_mock(self) -> bool:
        return self.provider is None

    @property
    def provider_name(self) -> str:
        return self.provider.name if self.provider else "mock"

    async def generate(self, system: str, prompt: str, fallback: str) -> str:
        if not self.provider:
            return fallback
        url = self.provider.base_url.rstrip("/") + "/chat/completions"
        payload = {
            "model": self.provider.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "temperature": 0.35,
        }
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {self.provider.api_key}"},
                    json=payload,
                )
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception:
            return fallback

    async def structured(self, system: str, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
        text = await self.generate(
            system + "\n只返回合法 JSON，不要使用 Markdown 代码块。",
            prompt,
            json.dumps(fallback, ensure_ascii=False),
        )
        try:
            start, end = text.index("{"), text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return fallback

    async def stream(self, system: str, prompt: str, fallback: str) -> AsyncIterator[str]:
        text = await self.generate(system, prompt, fallback)
        step = 24
        for index in range(0, len(text), step):
            yield text[index:index + step]


llm_service = LLMService()
