from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROVIDER = "groq"
DEFAULT_MODELS = {
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4.1-mini",
    "anthropic": "claude-3-7-sonnet-latest",
    "openrouter": "openai/gpt-4.1-mini",
    "ollama": "llama3.1:8b",
    "compatible": "gpt-4.1-mini",
}
PROVIDER_ENV_KEYS = {
    "groq": "GROQ_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "ollama": "",
    "compatible": "",
}
DEFAULT_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "ollama": "http://localhost:11434/v1",
}
SUPPORTED_PROVIDERS = tuple(DEFAULT_MODELS.keys())


class ConfigError(RuntimeError):
    """Raised when gitmortem configuration is invalid."""


@dataclass(frozen=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str | None
    base_url: str | None
    temperature: float = 0.1
    max_tokens: int = 1000


def resolve_provider(provider: str | None) -> str:
    selected = (provider or os.getenv("GITMORTEM_PROVIDER") or DEFAULT_PROVIDER).strip().lower()
    if selected not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ConfigError(f"Unsupported provider '{selected}'. Choose one of: {supported}.")
    return selected


def default_model_for(provider: str) -> str:
    return os.getenv("GITMORTEM_MODEL") or DEFAULT_MODELS[provider]


def resolve_base_url(provider: str, base_url: str | None = None) -> str | None:
    if base_url:
        return base_url
    if os.getenv("GITMORTEM_BASE_URL"):
        return os.getenv("GITMORTEM_BASE_URL")
    return DEFAULT_BASE_URLS.get(provider)


def resolve_api_key(provider: str, api_key: str | None = None) -> str | None:
    if api_key:
        return api_key

    env_key = PROVIDER_ENV_KEYS.get(provider, "")
    if env_key:
        return os.getenv(env_key)

    if provider == "compatible":
        return os.getenv("GITMORTEM_API_KEY") or os.getenv("OPENAI_API_KEY")

    return None


def build_llm_settings(
    provider: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 1000,
) -> LLMSettings:
    selected_provider = resolve_provider(provider)
    selected_model = model or default_model_for(selected_provider)
    selected_api_key = resolve_api_key(selected_provider, api_key)
    selected_base_url = resolve_base_url(selected_provider, base_url)

    if selected_provider == "compatible" and not selected_base_url:
        raise ConfigError("Provider 'compatible' requires --base-url or GITMORTEM_BASE_URL.")

    if selected_provider == "ollama" and not selected_api_key:
        selected_api_key = "ollama"

    return LLMSettings(
        provider=selected_provider,
        model=selected_model,
        api_key=selected_api_key,
        base_url=selected_base_url,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def validate_llm_settings(settings: LLMSettings) -> None:
    if settings.provider == "ollama":
        return

    if not settings.api_key:
        env_key = PROVIDER_ENV_KEYS.get(settings.provider) or "GITMORTEM_API_KEY"
        raise ConfigError(
            f"No API key configured for provider '{settings.provider}'. "
            f"Set {env_key} or pass --api-key."
        )


def resolve_output_directory() -> Path:
    raw_dir = os.getenv("GITMORTEM_OUTPUT_DIR")
    if raw_dir:
        return Path(raw_dir).expanduser().resolve()
    return Path.cwd()
