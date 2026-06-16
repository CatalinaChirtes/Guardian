import time
from collections.abc import AsyncIterator

from google import genai
from google.genai.types import GenerateContentConfig

from app.config import settings
from app.services.llm.base import LLMResponse


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, model: str = "gemini-2.5-flash"):
        self.model = model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def _convert_messages(self, messages: list[dict]) -> tuple[str | None, list[dict]]:
        system = None
        contents = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg["content"]}]})
        return system, contents

    async def generate(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        system, contents = self._convert_messages(messages)
        start = time.monotonic()

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        latency = (time.monotonic() - start) * 1000

        prompt_tokens = 0
        completion_tokens = 0
        if response.usage_metadata:
            prompt_tokens = response.usage_metadata.prompt_token_count or 0
            completion_tokens = response.usage_metadata.candidates_token_count or 0

        return LLMResponse(
            content=response.text or "",
            provider=self.provider_name,
            model=self.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=latency,
        )

    async def generate_stream(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        system, contents = self._convert_messages(messages)

        response = await self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=GenerateContentConfig(
                system_instruction=system,
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
        )
        async for chunk in response:
            if chunk.text:
                yield chunk.text
