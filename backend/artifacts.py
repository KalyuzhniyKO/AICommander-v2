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
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def collect_execution_inputs(run_folder: Path) -> Dict[str, Any]:
    stakeholder_task = load_json_if_exists(run_folder / "stakeholder_task.json", default={})
    stakeholder_comment = load_json_if_exists(run_folder / "stakeholder_comment.json", default={})

    return {
        "stakeholder_task": stakeholder_task,
        "stakeholder_comment": stakeholder_comment,
        "director_response": load_json_if_exists(run_folder / ARTIFACT_NAMES["director_response"], default={}),
        "execution": load_json_if_exists(run_folder / ARTIFACT_NAMES["execution"], default={}),
        "manual_review": load_json_if_exists(run_folder / ARTIFACT_NAMES["manual_review"], default={}),
        "team_summary": load_json_if_exists(run_folder / ARTIFACT_NAMES["team_summary"], default={}),
        "run_folder": str(run_folder.resolve()),
        "artifacts": {
            key: str((run_folder / value).resolve()) for key, value in ARTIFACT_NAMES.items()
        },
    }
