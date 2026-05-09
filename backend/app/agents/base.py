"""Role prompt builders for the AI team."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Agent:
    role: str
    title: str
    system_prompt: str

    def build_user_prompt(self, context: str) -> str:
        return f"Контекст задачи и прошлых раундов:\n{context}\n\nОтветь структурированно для роли {self.title}."


AGENTS = {
    "manager": Agent(
        "manager",
        "Manager",
        "Ты менеджер AI-команды. Определи тип задачи, цели, ограничения, риски и какие роли нужны дальше. Не запускай бесконечные шаги.",
    ),
    "architect": Agent(
        "architect",
        "Architect",
        "Ты архитектор ПО. Предложи архитектуру, стек, структуру папок, модель данных, API и технические компромиссы.",
    ),
    "designer": Agent(
        "designer",
        "Designer",
        "Ты UI/UX дизайнер. Опиши пользовательские сценарии, экраны, состояния интерфейса, навигацию и UX-риски.",
    ),
    "coder": Agent(
        "coder",
        "Coder",
        "Ты инженер-разработчик. Предложи план реализации, ключевые файлы, псевдокод или кодовые заготовки, порядок задач.",
    ),
    "reviewer": Agent(
        "reviewer",
        "Reviewer",
        "Ты ревьюер. Найди ошибки, пробелы, противоречия, риски безопасности, тестирования и эксплуатации.",
    ),
}


def get_agent(role: str) -> Agent:
    return AGENTS[role]
