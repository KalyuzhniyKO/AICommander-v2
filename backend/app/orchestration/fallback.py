"""Model fallback logic per role."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from backend.app.providers.base import ChatMessage, ChatProvider, ProviderError
from backend.app.providers.openai import OpenAIProvider
from backend.app.providers.openrouter import OpenRouterProvider
from backend.app.storage.repositories import Repository


@dataclass
class FallbackOutcome:
    success: bool
    output: str = ""
    provider: str = ""
    model_id: str = ""
    response_time_ms: int | None = None
    errors: list[dict[str, str]] = field(default_factory=list)


def split_model_ref(ref: str) -> tuple[str, str]:
    if "/" not in ref:
        return "openrouter", ref
    provider, model = ref.split("/", 1)
    return provider, model


def provider_for(provider_name: str, openrouter: OpenRouterProvider, openai: OpenAIProvider | None = None) -> ChatProvider:
    if provider_name == "openrouter":
        return openrouter
    if provider_name == "openai" and openai is not None:
        return openai
    raise ProviderError(f"Provider {provider_name} is not configured", "not_configured")


def run_with_fallback(
    *,
    role: str,
    model_refs: list[str],
    messages: list[ChatMessage],
    timeout_seconds: int,
    max_attempts_per_model: int,
    repository: Repository,
    round_id: int | None,
    openrouter: OpenRouterProvider,
    openai: OpenAIProvider | None = None,
    provider_filter: Callable[[str], bool] | None = None,
) -> FallbackOutcome:
    errors: list[dict[str, str]] = []
    if not model_refs:
        return FallbackOutcome(success=False, errors=[{"provider": "unknown", "model_id": "", "error": f"No models configured for role {role}"}])
    for ref in model_refs:
        provider_name, model_id = split_model_ref(ref)
        if provider_filter and not provider_filter(provider_name):
            continue
        for _ in range(max(1, max_attempts_per_model)):
            try:
                provider = provider_for(provider_name, openrouter, openai)
                result = provider.chat(model_id=model_id, messages=messages, timeout_seconds=timeout_seconds)
                repository.update_model_status(provider_name, model_id, role, "available", response_time_ms=result.response_time_ms)
                return FallbackOutcome(True, result.content, provider_name, model_id, result.response_time_ms, errors)
            except ProviderError as exc:
                error = str(exc)
            except Exception as exc:
                error = f"Unexpected provider error: {exc}"
            errors.append({"provider": provider_name, "model_id": model_id, "error": error})
            repository.add_model_error(round_id, role, provider_name, model_id, error)
            repository.update_model_status(provider_name, model_id, role, "failed", last_error=error)
            break
    return FallbackOutcome(success=False, errors=errors)
