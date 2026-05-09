"""Optional paid/expert Premium Review stage."""

from __future__ import annotations

from backend.app.config import Settings
from backend.app.orchestration.fallback import run_with_fallback
from backend.app.providers.base import ChatMessage
from backend.app.providers.openai import OpenAIProvider
from backend.app.providers.openrouter import OpenRouterProvider
from backend.app.storage.repositories import Repository


def run_premium_review(round_id: int, settings: Settings, model_config: dict[str, list[str]], repository: Repository, manual: bool = True) -> dict:
    round_row = repository.get_round(round_id)
    if not round_row:
        raise ValueError(f"Round {round_id} not found")
    if not settings.enable_premium_review:
        repository.update_premium_review(round_id, "skipped_disabled", "Premium Review is disabled. Set ENABLE_PREMIUM_REVIEW=true to allow paid review.")
        return repository.get_round(round_id) or round_row
    if not settings.openai_api_key:
        repository.update_premium_review(round_id, "skipped_not_configured", "OPENAI_API_KEY is not configured.")
        return repository.get_round(round_id) or round_row
    task = repository.get_task(round_row["task_id"])
    content = [f"Task: {task['description'] if task else ''}", f"Round summary: {round_row.get('summary', '')}"]
    for output in round_row.get("role_outputs", []):
        content.append(f"{output['role']}: {output.get('output', '')}")
    messages = [
        ChatMessage("system", "You are a senior paid expert reviewer. Check feasibility, missing requirements, risks, architecture, UX, implementation, and next user questions. Be concise and actionable."),
        ChatMessage("user", "\n\n".join(content)),
    ]
    outcome = run_with_fallback(
        role="premium_reviewer",
        model_refs=model_config.get("premium_reviewer", []),
        messages=messages,
        timeout_seconds=settings.default_timeout_seconds,
        max_attempts_per_model=settings.max_model_retries,
        repository=repository,
        round_id=round_id,
        openrouter=OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_base_url),
        openai=OpenAIProvider(settings.openai_api_key, settings.openai_base_url),
        provider_filter=lambda provider: provider == "openai",
    )
    if outcome.success:
        repository.update_premium_review(round_id, "completed", outcome.output, f"{outcome.provider}/{outcome.model_id}")
    else:
        joined = "\n".join(item["error"] for item in outcome.errors) or "Premium Review failed."
        status = "skipped_quota_or_tokens" if any("quota" in item["error"].lower() or "429" in item["error"] or "402" in item["error"] for item in outcome.errors) else "skipped_api_error"
        repository.update_premium_review(round_id, status, joined)
    return repository.get_round(round_id) or round_row
