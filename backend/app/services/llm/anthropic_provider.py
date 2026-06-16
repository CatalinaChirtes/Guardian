import time
from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from app.config import settings
from app.services.llm.base import LLMResponse


class AnthropicProvider:
    provider_name = "anthropic"

    _NO_TEMPERATURE_MODELS = {"claude-opus-4-8", "claude-opus-4-7", "claude-fable-5"}

    def __init__(self, model: str = "claude-haiku-4-5"):
        self.model = model
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    def _extract_system(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system = None
        filtered = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                filtered.append(msg)
        return system, filtered

    def _build_params(self, messages: list[dict], temperature: float, max_tokens: int) -> dict:
        system, filtered = self._extract_system(messages)
        params = {
            "model": self.model,
            "messages": filtered,
            "max_tokens": max_tokens,
        }
        if self.model not in self._NO_TEMPERATURE_MODELS:
            params["temperature"] = temperature
        if system:
            params["system"] = system
        return params

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
        response = await self.client.messages.create(
            **self._build_params(messages, temperature, max_tokens)
        )
        latency = (time.monotonic() - start) * 1000

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            provider=self.provider_name,
            model=self.model,
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
            latency_ms=latency,
        )

    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        params = self._build_params(messages, temperature, max_tokens)
        async with self.client.messages.stream(**params) as stream:
            async for text in stream.text_stream:
                yield text
