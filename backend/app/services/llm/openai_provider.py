import time
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from app.config import settings
from app.services.llm.base import LLMResponse


class OpenAIProvider:
    provider_name = "openai"

    _FIXED_TEMPERATURE_MODELS = {"gpt-5.5", "gpt-5.5-pro"}

    def __init__(self, model: str = "gpt-5.4-mini"):
        self.model = model
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    def _build_params(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
        params = {
            "model": self.model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
        }
        if self.model not in self._FIXED_TEMPERATURE_MODELS:
            params["temperature"] = temperature
        return params

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
        response = await self.client.chat.completions.create(
            **self._build_params(messages, temperature, max_tokens)
        )
        latency = (time.monotonic() - start) * 1000

        return LLMResponse(
            content=response.choices[0].message.content or "",
            provider=self.provider_name,
            model=self.model,
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
            latency_ms=latency,
        )

    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        params = self._build_params(messages, temperature, max_tokens)
        params["stream"] = True
        stream = await self.client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
