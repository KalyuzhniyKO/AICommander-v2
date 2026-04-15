"""Minimal viable integration API for the existing AICommander main app."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from .legacy_app_flow_integration import gui_health_status_for_existing_app, run_post_judge_transition


@dataclass(frozen=True)
class AppNextStep:
    status: str
    next_route: str
    final_verdict: str
    final_audit_path: str
    final_audit: Dict[str, Any]


def run_after_judge_and_resolve_next_step(run_folder: Path, execution_mode: str | None = None) -> AppNextStep:
    """
    Main-app hook for migration pack #2.

    Call this right after judge stage in the legacy AICommander flow.
    It triggers v2 final auditor, persists final_audit.json and returns mapped route.
    """
    transition = run_post_judge_transition(run_folder=run_folder, execution_mode=execution_mode)
    integration = transition.get("integration", {}) if isinstance(transition, dict) else {}

    return AppNextStep(
        status=transition.get("status", "unknown") if isinstance(transition, dict) else "unknown",
        next_route=integration.get("next_route", "revision_loop"),
        final_verdict=integration.get("final_verdict", "revise"),
        final_audit_path=integration.get("final_audit_path", str((run_folder / "final_audit.json").resolve())),
        final_audit=transition.get("final_audit", {}) if isinstance(transition, dict) else {},
    )


def get_gui_status_model_for_app(run_folder: Path, execution_mode: str | None = None) -> Dict[str, Any]:
    """
    Main-app hook to replace machine-based GUI status payloads with provider-based roles.
    """
    return gui_health_status_for_existing_app(run_folder=run_folder, execution_mode=execution_mode)
