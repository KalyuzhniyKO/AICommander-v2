"""Run-folder artifact utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

# Existing artifacts that must remain supported.
ARTIFACT_NAMES = {
    "director_response": "director_response.json",
    "execution": "execution.json",
    "manual_review": "manual_review.json",
    "team_summary": "team_summary.json",
    "final_report": "final_report.docx",
    "final_audit": "final_audit.json",
}


def load_json_if_exists(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _value_as_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("summary", "message", "text", "result", "content", "response"):
            raw = value.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()
        return fallback
    return fallback


def _bool_from(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "required"}
    return default


def collect_execution_inputs(run_folder: Path) -> Dict[str, Any]:
    stakeholder_task = load_json_if_exists(run_folder / "stakeholder_task.json", default={})
    stakeholder_comment = load_json_if_exists(run_folder / "stakeholder_comment.json", default={})
    director_response = load_json_if_exists(run_folder / ARTIFACT_NAMES["director_response"], default={})
    execution = load_json_if_exists(run_folder / ARTIFACT_NAMES["execution"], default={})
    manual_review = load_json_if_exists(run_folder / ARTIFACT_NAMES["manual_review"], default={})
    team_summary = load_json_if_exists(run_folder / ARTIFACT_NAMES["team_summary"], default={})

    coder_summary = _value_as_text(team_summary.get("coder") if isinstance(team_summary, dict) else None)
    reviewer_summary = _value_as_text(team_summary.get("reviewer") if isinstance(team_summary, dict) else None)
    qa_summary = _value_as_text(team_summary.get("qa") if isinstance(team_summary, dict) else None)
    judge_summary = _value_as_text(team_summary.get("judge") if isinstance(team_summary, dict) else None)

    if isinstance(execution, dict):
        execution_status = _value_as_text(execution.get("status"), fallback="unknown") or "unknown"
    else:
        execution_status = "unknown"

    if isinstance(manual_review, dict):
        manual_review_required = _bool_from(
            manual_review.get("required", manual_review.get("manual_review_required", False)),
            default=False,
        )
    else:
        manual_review_required = False

    return {
        "stakeholder_task": _value_as_text(stakeholder_task, fallback=""),
        "stakeholder_comment": _value_as_text(stakeholder_comment, fallback=""),
        "director_summary": _value_as_text(director_response, fallback=""),
        "next_action": _value_as_text(
            director_response.get("next_action") if isinstance(director_response, dict) else None,
            fallback="",
        ),
        "coder_summary": coder_summary,
        "reviewer_summary": reviewer_summary,
        "qa_summary": qa_summary,
        "judge_summary": judge_summary,
        "execution_status": execution_status,
        "manual_review_required": manual_review_required,
        "artifact_paths": {
            key: str((run_folder / value).resolve()) for key, value in ARTIFACT_NAMES.items()
        },
        "run_folder": str(run_folder.resolve()),
    }
