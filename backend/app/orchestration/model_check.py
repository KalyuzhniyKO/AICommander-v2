"""Manual model availability checks for configured role fallback chains."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.app.config import DEFAULT_MODELS_PATH, EXAMPLE_MODELS_PATH, Settings, load_model_config
from backend.app.orchestration.fallback import split_model_ref
from backend.app.providers.base import ChatMessage, ProviderError
from backend.app.providers.openrouter import OpenRouterProvider
from backend.app.storage.repositories import Repository

CHECK_PROMPT = "Ответь одним словом: OK"
CONFIG_MISSING_MESSAGE = (
    "Файл config/models.json не найден. Скопируйте config/models.example.json в config/models.json "
    "и при необходимости отредактируйте список моделей."
)
OPENROUTER_KEY_MISSING_MESSAGE = "OPENROUTER_API_KEY отсутствует. Добавьте ключ в .env или переменные окружения."


def _friendly_error(error: str, category: str = "api_error") -> str:
    text = error.strip() or "Модель вернула неизвестную ошибку."
    lower = text.lower()
    if category == "not_configured" or "api_key" in lower:
        return OPENROUTER_KEY_MISSING_MESSAGE
    if category == "timeout" or "timed out" in lower or "timeout" in lower:
        return "Модель недоступна: запрос превысил timeout. Попробуйте позже или выберите другую модель."
    if category == "quota_or_tokens" or "429" in text or "402" in text or "quota" in lower or "rate" in lower:
        return "Закончились лимиты или сработал rate limit провайдера. Проверьте баланс/лимиты OpenRouter."
    if "unavailable" in lower or "not found" in lower:
        return "Модель недоступна или указанный model_id больше не поддерживается."
    return f"Модель вернула ошибку: {text}"


def check_models(settings: Settings, repository: Repository, config_path: Path | None = None) -> dict[str, Any]:
    """Check each openrouter model from config/models.json and persist status rows."""
    model_path = config_path or DEFAULT_MODELS_PATH
    if not model_path.exists():
        return {
            "ok": False,
            "status": "config_missing",
            "error": CONFIG_MISSING_MESSAGE,
            "hint": f"cp {EXAMPLE_MODELS_PATH.relative_to(EXAMPLE_MODELS_PATH.parents[1])} {DEFAULT_MODELS_PATH.relative_to(DEFAULT_MODELS_PATH.parents[1])}",
            "results": [],
        }

    try:
        model_config = load_model_config(model_path)
    except Exception as exc:
        return {
            "ok": False,
            "status": "config_invalid",
            "error": f"Не удалось прочитать config/models.json: {exc}",
            "hint": "Проверьте JSON-синтаксис или заново скопируйте config/models.example.json.",
            "results": [],
        }
    configured_openrouter = []
    for role, refs in model_config.items():
        for ref in refs:
            provider, model_id = split_model_ref(ref)
            if provider == "openrouter":
                configured_openrouter.append((role, provider, model_id))

    if not settings.openrouter_api_key:
        results = []
        for role, provider, model_id in configured_openrouter:
            repository.update_model_status(provider, model_id, role, "failed", last_error=OPENROUTER_KEY_MISSING_MESSAGE)
            results.append({
                "role": role,
                "provider": provider,
                "model_id": model_id,
                "status": "failed",
                "last_error": OPENROUTER_KEY_MISSING_MESSAGE,
                "response_time_ms": None,
            })
        return {
            "ok": False,
            "status": "openrouter_key_missing",
            "error": OPENROUTER_KEY_MISSING_MESSAGE,
            "results": results,
        }

    provider = OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_base_url)
    messages = [ChatMessage("user", CHECK_PROMPT)]
    results: list[dict[str, Any]] = []
    for role, provider_name, model_id in configured_openrouter:
        try:
            result = provider.chat(model_id=model_id, messages=messages, timeout_seconds=settings.default_timeout_seconds)
            repository.update_model_status(provider_name, model_id, role, "available", response_time_ms=result.response_time_ms)
            results.append({
                "role": role,
                "provider": provider_name,
                "model_id": model_id,
                "status": "available",
                "last_error": "",
                "response_time_ms": result.response_time_ms,
            })
        except ProviderError as exc:
            friendly = _friendly_error(str(exc), exc.category)
            repository.update_model_status(provider_name, model_id, role, "failed", last_error=friendly)
            results.append({
                "role": role,
                "provider": provider_name,
                "model_id": model_id,
                "status": "failed",
                "last_error": friendly,
                "response_time_ms": None,
            })
        except Exception as exc:
            friendly = _friendly_error(str(exc))
            repository.update_model_status(provider_name, model_id, role, "failed", last_error=friendly)
            results.append({
                "role": role,
                "provider": provider_name,
                "model_id": model_id,
                "status": "failed",
                "last_error": friendly,
                "response_time_ms": None,
            })

    return {"ok": all(item["status"] == "available" for item in results), "status": "completed", "results": results}
