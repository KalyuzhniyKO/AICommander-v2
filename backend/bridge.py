"""Bridge helpers to embed migration backend into existing AICommander flow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


def build_bridge_plan(run_folder: Path) -> Dict[str, object]:
    """
    Integration contract for legacy GUI/stakeholder flow without frontend rewrite.

    Existing flow keeps producing run-folder artifacts.
    New backend pack is invoked after judge output using:
      python -m backend.cli --run-final-audit --run-folder <run_folder>
    """

    return {
        "status": "ok",
        "integration_points": {
            "before": "legacy pipeline ends after judge",
            "after": "legacy pipeline calls --run-final-audit before done/reject UI state",
            "gui_changes_required": "minimal",
        },
        "required_inputs": [
            str((run_folder / "director_response.json").resolve()),
            str((run_folder / "execution.json").resolve()),
            str((run_folder / "manual_review.json").resolve()),
            str((run_folder / "team_summary.json").resolve()),
            str((run_folder / "stakeholder_task.json").resolve()),
            str((run_folder / "stakeholder_comment.json").resolve()),
        ],
        "outputs": {
            "final_audit": str((run_folder / "final_audit.json").resolve()),
            "legacy_compatible": True,
        },
        "routing": {
            "approve": "done",
            "revise": "manual revision loop",
            "reject": "stakeholder reject path",
        },
    }
