# AICommander-v2

Migration packs introduce provider-based role orchestration as the primary backend architecture:

`GUI -> Python orchestration backend -> provider-based roles`

## Roles

- director
- coder
- reviewer
- qa
- judge
- final_auditor

## Environment configuration

```bash
AICOMMANDER_PROVIDER=openrouter
AICOMMANDER_PROVIDER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_API_KEY=...

# execution profile: cheap|balanced|premium
AICOMMANDER_EXECUTION_MODE=balanced

AICOMMANDER_DIRECTOR_MODEL=...
AICOMMANDER_CODER_MODEL=...
AICOMMANDER_REVIEWER_MODEL=...
AICOMMANDER_QA_MODEL=...
AICOMMANDER_JUDGE_MODEL=...
AICOMMANDER_FINAL_AUDITOR_MODEL=...

# optional mode-specific overrides
AICOMMANDER_CODER_MODEL_CHEAP=...
AICOMMANDER_CODER_MODEL_BALANCED=...
AICOMMANDER_CODER_MODEL_PREMIUM=...

AICOMMANDER_FINAL_AUDITOR_PROVIDER=...
AICOMMANDER_FINAL_AUDITOR_BASE_URL=...
AICOMMANDER_FINAL_AUDITOR_API_KEY=...
```

## CLI

```bash
python -m backend.cli --health-check --execution-mode balanced --run-folder runs/current
python -m backend.cli --run-final-audit --execution-mode premium --run-folder runs/current
python -m backend.cli --run-post-judge-transition --execution-mode premium --run-folder runs/current
python -m backend.cli --read-final-audit-route --run-folder runs/current
python -m backend.cli --read-post-judge-route --run-folder runs/current
python -m backend.cli --gui-health-status --run-folder runs/current
python -m backend.cli --bridge-status --run-folder runs/current
```

## Migration pack #2: integration into existing AICommander app flow

No giant GUI rewrite is required.

1. Existing GUI and stakeholder approve/comment/reject flow stay untouched.
2. Legacy execution keeps writing existing run-folder artifacts.
3. After `judge`, app invokes:
   - `python -m backend.cli --run-post-judge-transition --run-folder <run_folder>`
4. Backend writes `final_audit.json` and updates route snapshot inside `execution.json`.
5. App reads route via:
   - `python -m backend.cli --read-post-judge-route --run-folder <run_folder>`
6. Route mapping:
   - `approve -> done`
   - `revise -> revision_loop`
   - `reject -> stakeholder_reject`

### GUI-facing health status model

`--gui-health-status` returns stable keys for GUI state:

- provider_status
- director_role
- coder_role
- reviewer_role
- qa_role
- judge_role
- final_auditor_role
- workspace_status
- orchestration_status

### Existing main app integration files (MVI)

See exact file-by-file integration plan and pseudo-diffs in:

- `docs/MAIN_APP_MVI_INTEGRATION.md`

Also available as Python integration hooks for the main app:

- `run_after_judge_and_resolve_next_step(...)`
- `get_gui_status_model_for_app(...)`

## Artifacts

Existing artifacts remain supported:

- director_response.json
- execution.json
- manual_review.json
- team_summary.json
- final_report.docx

New artifact:

- final_audit.json
