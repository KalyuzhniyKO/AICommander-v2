"""Integration helpers for embedding v2 backend into existing AICommander app flow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

from .artifacts import collect_execution_inputs, load_json_if_exists, save_json
from .config import load_config
from .final_auditor import run_final_auditor
from .health import health_check
from .pipeline import resolve_terminal_stage


@dataclass(frozen=True)
class GuiHealthStatusModel:
    provider_status: Dict[str, Any]
    director_role: Dict[str, Any]
    coder_role: Dict[str, Any]
    reviewer_role: Dict[str, Any]
    qa_role: Dict[str, Any]
    judge_role: Dict[str, Any]
    final_auditor_role: Dict[str, Any]
    workspace_status: Dict[str, Any]
    orchestration_status: Dict[str, Any]


def _route_from_verdict(verdict: str) -> str:
    terminal = resolve_terminal_stage(verdict).value
    if terminal == "done":
        return "done"
    if terminal == "reject":
        return "stakeholder_reject"
    return "revision_loop"


def run_post_judge_flow(run_folder: Path, execution_mode: str | None = None) -> Dict[str, Any]:
    """
    Existing app integration point:
    invoke immediately after judge stage to produce final_audit.json and route.
    """
    config = load_config(strict=False, mode_override=execution_mode)
    payload = collect_execution_inputs(run_folder)

    final_audit = run_final_auditor(config.roles["final_auditor"], payload)
    final_audit["pipeline_terminal_stage"] = resolve_terminal_stage(final_audit.get("final_verdict", "revise")).value
    final_audit["execution_mode"] = config.execution_mode

    out_path = run_folder / "final_audit.json"
    save_json(out_path, final_audit)

    return {
        "status": "ok",
        "final_audit_path": str(out_path.resolve()),
        "final_verdict": final_audit.get("final_verdict", "revise"),
        "next_route": _route_from_verdict(final_audit.get("final_verdict", "revise")),
        "pipeline_terminal_stage": final_audit.get("pipeline_terminal_stage", "revise"),
    }


def load_post_judge_route(run_folder: Path) -> Dict[str, Any]:
    payload = load_json_if_exists(run_folder / "final_audit.json", default={})
    verdict = payload.get("final_verdict", "revise") if isinstance(payload, dict) else "revise"

    return {
        "status": "ok" if isinstance(payload, dict) and payload else "missing_final_audit",
        "final_verdict": verdict,
        "next_route": _route_from_verdict(verdict),
        "final_audit_path": str((run_folder / "final_audit.json").resolve()),
    }


def build_gui_health_status(run_folder: Path, execution_mode: str | None = None) -> GuiHealthStatusModel:
    config = load_config(strict=False, mode_override=execution_mode)
    payload = health_check(config=config, run_folder=run_folder)

    return GuiHealthStatusModel(
        provider_status=payload["provider_status"],
        director_role=payload["director_role"],
        coder_role=payload["coder_role"],
        reviewer_role=payload["reviewer_role"],
        qa_role=payload["qa_role"],
        judge_role=payload["judge_role"],
        final_auditor_role=payload["final_auditor_role"],
        workspace_status=payload["workspace_status"],
        orchestration_status=payload["orchestration_status"],
    )


def gui_health_status_payload(run_folder: Path, execution_mode: str | None = None) -> Dict[str, Any]:
    return asdict(build_gui_health_status(run_folder=run_folder, execution_mode=execution_mode))
