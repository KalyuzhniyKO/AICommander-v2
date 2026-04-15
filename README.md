# AICommander-v2

Migration pack introduces provider-based role orchestration as the primary backend architecture:

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
python -m backend.cli --bridge-status --run-folder runs/current
```

## Bridge to existing AICommander flow

No GUI rewrite is required for migration pack:

1. Existing GUI and stakeholder approve/comment/reject flow stay untouched.
2. Legacy execution still writes existing run-folder artifacts.
3. After `judge`, legacy flow invokes:
   - `python -m backend.cli --run-final-audit --run-folder <run_folder>`
4. Backend writes `final_audit.json`.
5. Legacy flow maps:
   - `approve -> done`
   - `revise -> revision loop`
   - `reject -> stakeholder reject path`

## Artifacts

Existing artifacts remain supported:

- director_response.json
- execution.json
- manual_review.json
- team_summary.json
- final_report.docx

New artifact:

- final_audit.json
