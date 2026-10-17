"""Explicit offline QA for trusted disposable repositories; no runtime wiring."""

from .runner import QaRunner, python_commands, write_report

__all__ = ["QaRunner", "python_commands", "write_report"]
