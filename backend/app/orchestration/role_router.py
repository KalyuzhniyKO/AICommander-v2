"""Local role selection heuristics for human-in-the-loop rounds."""

from __future__ import annotations

VALID_ROLES = ["manager", "architect", "designer", "coder", "reviewer"]


def detect_task_type(text: str) -> str:
    value = text.lower()
    if any(word in value for word in ["code review", "ревью", "review this", "проверь код", "audit code"]):
        return "code_review"
    if any(word in value for word in ["документац", "readme", "manual", "инструкц", "docs"]):
        return "documentation"
    if any(word in value for word in ["website", "landing", "лендинг", "сайт-визит", "визитка"]):
        return "website"
    if any(word in value for word in ["app", "прилож", "api", "database", "бд", "склад", "crm", "erp", "dashboard", "web app"]):
        return "web_app"
    return "general"


def select_roles(task_text: str) -> list[str]:
    task_type = detect_task_type(task_text)
    if task_type in {"code_review", "documentation"}:
        return ["manager", "reviewer"]
    if task_type == "website":
        return ["manager", "designer", "coder", "reviewer"]
    if task_type == "web_app":
        return ["manager", "architect", "designer", "coder", "reviewer"]
    return ["manager", "coder", "reviewer"]
