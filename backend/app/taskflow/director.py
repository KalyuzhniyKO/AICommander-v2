"""Deterministic, side-effect-free handoff. This is not an AI agent."""
from .models import Design, Plan, Requirements
from .redaction import redact

ROLES = ("analyst", "architect", "developer")
TYPES = ("requirements", "design", "plan")


class MockDirector:
    def produce(self, role, description, inputs):
        if role == "analyst":
            return Requirements(
                objective=redact(description),
                acceptance_criteria=["Артефакты переданы последовательно; выполнение кода не имитирует успешный QA."],
            )
        if role == "architect":
            return Design(requirements=inputs[-1].content, components=["Офлайн-проект на основе требований аналитика"])
        if role == "developer":
            return Plan(design=inputs[-1].content, steps=["Реализовать проект в отдельной задаче", "Запустить реальные проверки отдельно"])
        raise ValueError("Unsupported offline role")
