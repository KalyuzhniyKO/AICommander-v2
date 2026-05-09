"""Run one human-approved round of the AI team."""

from __future__ import annotations

from backend.app.agents.base import get_agent
from backend.app.config import Settings
from backend.app.orchestration.fallback import run_with_fallback
from backend.app.orchestration.role_router import select_roles, detect_task_type
from backend.app.providers.base import ChatMessage
from backend.app.providers.openrouter import OpenRouterProvider
from backend.app.storage.repositories import Repository


def build_round_context(task: dict, user_comment: str = "") -> str:
    parts = [f"Исходная задача:\n{task['description']}"]
    previous_rounds = task.get("rounds", [])[-2:]
    for rnd in previous_rounds:
        parts.append(f"Раунд {rnd['round_number']} summary:\n{rnd.get('summary', '')}")
        for output in rnd.get("role_outputs", []):
            parts.append(f"{output['role']} ({output.get('provider')}/{output.get('model_id')}):\n{output.get('output', '')}")
        if rnd.get("premium_review_output"):
            parts.append(f"Premium Review:\n{rnd['premium_review_output']}")
    if user_comment:
        parts.append(f"Комментарий пользователя для текущего раунда:\n{user_comment}")
    return "\n\n---\n\n".join(parts)


def fallback_local_output(role: str, task_text: str) -> str:
    task_type = detect_task_type(task_text)
    if role == "manager":
        return f"Тип задачи: {task_type}. Рекомендуемые роли: {', '.join(select_roles(task_text))}. Следующий шаг: дождаться комментария пользователя после этого раунда."
    return f"Роль {role} не получила ответ модели. Проверьте OPENROUTER_API_KEY и config/models.json, затем перезапустите роль."


def run_round(task_id: int, user_comment: str, settings: Settings, model_config: dict[str, list[str]], repository: Repository) -> dict:
    task = repository.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    selected_roles = select_roles(task["description"] + "\n" + (user_comment or ""))
    round_row = repository.create_round(task_id, selected_roles, user_comment)
    openrouter = OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_base_url)
    context = build_round_context(task, user_comment)
    outputs = []
    for role in selected_roles:
        agent = get_agent(role)
        messages = [ChatMessage("system", agent.system_prompt), ChatMessage("user", agent.build_user_prompt(context))]
        outcome = run_with_fallback(
            role=role,
            model_refs=model_config.get(role, []),
            messages=messages,
            timeout_seconds=settings.default_timeout_seconds,
            max_attempts_per_model=settings.max_model_retries,
            repository=repository,
            round_id=round_row["id"],
            openrouter=openrouter,
            provider_filter=lambda provider: provider == "openrouter",
        )
        output = outcome.output if outcome.success else fallback_local_output(role, task["description"])
        status = "completed" if outcome.success else "failed"
        repository.save_role_output(round_row["id"], role, output, outcome.provider, outcome.model_id, status, outcome.response_time_ms)
        outputs.append(f"{role}: {output[:500]}")
    repository.update_round_summary(round_row["id"], "\n".join(outputs))
    return repository.get_round(round_row["id"]) or round_row


def rerun_role(round_id: int, role: str, settings: Settings, model_config: dict[str, list[str]], repository: Repository) -> dict:
    round_row = repository.get_round(round_id)
    if not round_row:
        raise ValueError(f"Round {round_id} not found")
    task = repository.get_task(round_row["task_id"])
    if not task:
        raise ValueError(f"Task {round_row['task_id']} not found")
    if role not in {"manager", "architect", "designer", "coder", "reviewer"}:
        raise ValueError(f"Unsupported role {role}")
    openrouter = OpenRouterProvider(settings.openrouter_api_key, settings.openrouter_base_url)
    context = build_round_context(task, round_row.get("user_comment", ""))
    agent = get_agent(role)
    outcome = run_with_fallback(
        role=role,
        model_refs=model_config.get(role, []),
        messages=[ChatMessage("system", agent.system_prompt), ChatMessage("user", agent.build_user_prompt(context))],
        timeout_seconds=settings.default_timeout_seconds,
        max_attempts_per_model=settings.max_model_retries,
        repository=repository,
        round_id=round_id,
        openrouter=openrouter,
        provider_filter=lambda provider: provider == "openrouter",
    )
    output = outcome.output if outcome.success else fallback_local_output(role, task["description"])
    repository.save_role_output(round_id, role, output, outcome.provider, outcome.model_id, "completed" if outcome.success else "failed", outcome.response_time_ms)
    return repository.get_round(round_id) or round_row
