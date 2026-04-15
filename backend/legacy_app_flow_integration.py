"""Minimal bridge to wire v2 post-judge flow into the existing AICommander app flow."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .app_flow_bridge import gui_health_status_payload, run_post_judge_flow
from .artifacts import load_json_if_exists, save_json

EXECUTION_ARTIFACT = "execution.json"
FINAL_AUDIT_ARTIFACT = "final_audit.json"


def _load_execution_payload(run_folder: Path) -> Dict[str, Any]:
    payload = load_json_if_exists(run_folder / EXECUTION_ARTIFACT, default={})
    return payload if isinstance(payload, dict) else {}


def _route_mapping(verdict: str) -> str:
    mapping = {
        "approve": "done",
        "revise": "revision_loop",
        "reject": "stakeholder_reject",
    }
    return mapping.get(str(verdict).lower(), "revision_loop")


def run_post_judge_transition(run_folder: Path, execution_mode: str | None = None) -> Dict[str, Any]:
    """
    MVI integration entrypoint for existing app flow.

    Intended call site: right after judge stage completion.
    """
    outcome = run_post_judge_flow(run_folder=run_folder, execution_mode=execution_mode)
    final_audit = load_json_if_exists(run_folder / FINAL_AUDIT_ARTIFACT, default={})

    execution_payload = _load_execution_payload(run_folder)
    execution_payload["post_judge_transition"] = {
        "final_verdict": outcome.get("final_verdict", "revise"),
        "next_route": outcome.get("next_route", "revision_loop"),
        "pipeline_terminal_stage": outcome.get("pipeline_terminal_stage", "revise"),
        "final_audit_path": outcome.get("final_audit_path", str((run_folder / FINAL_AUDIT_ARTIFACT).resolve())),
    }

    save_json(run_folder / EXECUTION_ARTIFACT, execution_payload)

    return {
        "status": "ok",
        "integration": outcome,
        "final_audit": final_audit if isinstance(final_audit, dict) else {},
        "execution": execution_payload,
    }


def read_post_judge_route(run_folder: Path) -> Dict[str, Any]:
    final_audit = load_json_if_exists(run_folder / FINAL_AUDIT_ARTIFACT, default={})
    if isinstance(final_audit, dict) and final_audit:
        verdict = final_audit.get("final_verdict", "revise")
    else:
        verdict = "revise"

    return {
        "status": "ok" if isinstance(final_audit, dict) and final_audit else "missing_final_audit",
        "final_verdict": verdict,
        "next_route": _route_mapping(verdict),
        "final_audit_path": str((run_folder / FINAL_AUDIT_ARTIFACT).resolve()),
    }


def gui_health_status_for_existing_app(run_folder: Path, execution_mode: str | None = None) -> Dict[str, Any]:
    return gui_health_status_payload(run_folder=run_folder, execution_mode=execution_mode)

