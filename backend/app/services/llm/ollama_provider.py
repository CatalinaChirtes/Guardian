import json
import time
from collections.abc import AsyncIterator

import httpx

from app.config import settings
from app.services.llm.base import LLMResponse


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model
        self.base_url = settings.ollama_base_url
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=300.0)

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        start = time.monotonic()
        response = await self._client.post(
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        )
        response.raise_for_status()
        data = response.json()

        latency = (time.monotonic() - start) * 1000
        return LLMResponse(
            content=data["message"]["content"],
            provider=self.provider_name,
            model=self.model,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0),
            latency_ms=latency,
        )

    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        async with self._client.stream(
            "POST",
            "/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            },
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    if not data.get("done", False):
                        yield data["message"]["content"]
