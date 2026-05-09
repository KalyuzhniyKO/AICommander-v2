"""Stable integration entrypoints for the existing AICommander main app.

These helpers keep the GUI integration surface small: call the backend once after
legacy `judge` finishes, then read a GUI-friendly health model when needed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .app_flow_bridge import gui_health_status_payload, run_post_judge_flow


def run_after_judge_and_resolve_next_step(run_folder: str | Path, execution_mode: str | None = None) -> Dict[str, Any]:
    """Run the final audit stage after judge and return the next legacy route."""
    return run_post_judge_flow(run_folder=Path(run_folder), execution_mode=execution_mode)


def get_gui_status_model_for_app(run_folder: str | Path, execution_mode: str | None = None) -> Dict[str, Any]:
    """Return the stable GUI-facing backend health/status payload."""
    return gui_health_status_payload(run_folder=Path(run_folder), execution_mode=execution_mode)
