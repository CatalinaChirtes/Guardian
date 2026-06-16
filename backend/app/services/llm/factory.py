from app.services.llm.anthropic_provider import AnthropicProvider
from app.services.llm.base import LLMProvider
from app.services.llm.gemini_provider import GeminiProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.openai_provider import OpenAIProvider

_PROVIDERS: dict[str, type] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "anthropic": AnthropicProvider,
}

_OLLAMA_MODELS: dict[str, str] = {
    "ollama-qwen": "qwen2.5:3b",
    "ollama-gemma": "gemma3:4b",
}

_cache: dict[str, LLMProvider] = {}


def get_provider(name: str, **kwargs) -> LLMProvider:
    cache_key = name
    if cache_key in _cache:
        return _cache[cache_key]

    if name in _OLLAMA_MODELS:
        provider = OllamaProvider(model=_OLLAMA_MODELS[name])
    else:
        provider_class = _PROVIDERS.get(name)
        if provider_class is None:
            raise ValueError(f"Unknown LLM provider: {name}. Available: {list(_PROVIDERS) + list(_OLLAMA_MODELS)}")
        provider = provider_class(**kwargs)

    _cache[cache_key] = provider
    return provider
