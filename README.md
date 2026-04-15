# AICommander-v2

Migration pack #1 introduces provider-based role orchestration as the primary backend architecture:

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

AICOMMANDER_DIRECTOR_MODEL=...
AICOMMANDER_CODER_MODEL=...
AICOMMANDER_REVIEWER_MODEL=...
AICOMMANDER_QA_MODEL=...
AICOMMANDER_JUDGE_MODEL=...
AICOMMANDER_FINAL_AUDITOR_MODEL=...

AICOMMANDER_FINAL_AUDITOR_PROVIDER=...
AICOMMANDER_FINAL_AUDITOR_BASE_URL=...
AICOMMANDER_FINAL_AUDITOR_API_KEY=...
```

## CLI

```bash
python -m backend.cli --health-check --run-folder runs/current
python -m backend.cli --run-final-audit --run-folder runs/current
```

## Artifacts

Existing artifacts remain supported:

- director_response.json
- execution.json
- manual_review.json
- team_summary.json
- final_report.docx

New artifact:

- final_audit.json
