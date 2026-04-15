"""Bridge helpers to embed migration backend into existing AICommander flow."""

from __future__ import annotations

from pathlib import Path
from typing import Dict


def build_bridge_plan(run_folder: Path) -> Dict[str, object]:
    """
    Integration contract for legacy GUI/stakeholder flow without frontend rewrite.

    Existing flow keeps producing run-folder artifacts.
    New backend pack is invoked after judge output using:
      python -m backend.cli --run-post-judge-transition --run-folder <run_folder>
    """

    return {
        "status": "ok",
        "integration_points": {
            "trigger_stage": "after_judge",
            "action": "invoke --run-post-judge-transition",
            "gui_changes_required": "minimal",
        },
        "commands": {
            "post_judge": f"python -m backend.cli --run-post-judge-transition --run-folder {run_folder}",
            "read_route": f"python -m backend.cli --read-post-judge-route --run-folder {run_folder}",
            "gui_health": f"python -m backend.cli --gui-health-status --run-folder {run_folder}",
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
            "revise": "revision_loop",
            "reject": "stakeholder_reject",
        },
    }
