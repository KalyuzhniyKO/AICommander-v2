# Main App MVI Integration

This document defines the minimal integration path for the current backend baseline. The goal is to connect the existing AICommander app flow to the Python backend without a large GUI rewrite.

## Integration contract

The legacy app continues to create and update the existing run folder. After the existing `judge` stage completes, the app calls the backend post-judge transition.

```bash
python -m backend.cli --run-post-judge-transition --run-folder <run_folder>
```

The backend then:

1. Loads existing run-folder artifacts.
2. Runs `final_auditor` as the current final audit stage.
3. Writes `<run_folder>/final_audit.json`.
4. Returns a next-route payload for the GUI/app state machine.

## Expected inputs

The bridge supports these existing artifacts when present:

- `director_response.json`
- `execution.json`
- `manual_review.json`
- `team_summary.json`
- `final_report.docx`
- `stakeholder_task.json`
- `stakeholder_comment.json`

Missing JSON inputs are handled as empty/default values so the bridge can be added incrementally.

## Output

The new backend output is:

- `final_audit.json`

The route mapping is:

- `approve -> done`
- `revise -> revision_loop`
- `reject -> stakeholder_reject`

Read the route with:

```bash
python -m backend.cli --read-post-judge-route --run-folder <run_folder>
```

Backward-compatible aliases remain available:

```bash
python -m backend.cli --run-final-audit --run-folder <run_folder>
python -m backend.cli --read-final-audit-route --run-folder <run_folder>
```

## Python entrypoints

New integrations should import from `backend.main_app_integration`:

```python
from backend.main_app_integration import (
    get_gui_status_model_for_app,
    run_after_judge_and_resolve_next_step,
)

result = run_after_judge_and_resolve_next_step(run_folder)
status = get_gui_status_model_for_app(run_folder)
```

Older references can temporarily import the same wrappers from `backend.legacy_app_flow_integration`.

## GUI health model

The GUI can request a stable health/status payload with:

```bash
python -m backend.cli --gui-health-status --run-folder <run_folder>
```

Stable top-level keys:

- `provider_status`
- `director_role`
- `coder_role`
- `reviewer_role`
- `qa_role`
- `judge_role`
- `final_auditor_role`
- `workspace_status`
- `orchestration_status`
