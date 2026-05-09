# AICommander-v2

AICommander-v2 currently contains the cleaned backend migration baseline for a provider-based Python orchestration backend. The repository is intentionally **not** implementing the next AI-team orchestrator feature yet; that work is planned separately after this cleanup.

Current baseline:

```text
GUI / existing app flow
  -> backend CLI / integration bridge
  -> provider-based role configuration
  -> final_auditor final audit stage
  -> run-folder artifacts and next-route decision
```

## What is implemented now

- `backend/` Python package with provider-based role configuration.
- CLI entrypoint: `python -m backend.cli`.
- Final audit stage: `final_auditor` is the current final stage after `judge`.
- Health checks for provider config, role config, workspace writability, and expected run-folder artifacts.
- Run-folder artifact helpers for existing legacy outputs plus `final_audit.json`.
- Legacy/main-app bridge helpers so the existing GUI can call the backend after `judge` without a full UI rewrite.
- Main-app MVI integration documentation in `docs/MAIN_APP_MVI_INTEGRATION.md`.

## Backend package structure

```text
backend/
  __init__.py
  config.py
  artifacts.py
  final_auditor.py
  health.py
  pipeline.py
  cli.py
  bridge.py
  app_flow_bridge.py
  legacy_app_flow_integration.py
  main_app_integration.py
```

## Roles in the current backend baseline

The current backend baseline uses these roles:

- `director`
- `coder`
- `reviewer`
- `qa`
- `judge`
- `final_auditor`

`final_auditor` runs after `judge`, writes `final_audit.json`, and maps the final verdict to the next route:

- `approve -> done`
- `revise -> revision_loop`
- `reject -> stakeholder_reject`

## Environment variables

Do **not** commit `.env` files, API keys, or real tokens.

Required/primary variables:

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
```

Optional mode-specific model overrides:

```bash
AICOMMANDER_CODER_MODEL_CHEAP=...
AICOMMANDER_CODER_MODEL_BALANCED=...
AICOMMANDER_CODER_MODEL_PREMIUM=...
```

Optional `final_auditor` provider override:

```bash
AICOMMANDER_FINAL_AUDITOR_PROVIDER=...
AICOMMANDER_FINAL_AUDITOR_BASE_URL=...
AICOMMANDER_FINAL_AUDITOR_API_KEY=...
```

For non-OpenRouter providers, use `AICOMMANDER_PROVIDER_API_KEY` instead of `OPENROUTER_API_KEY`.

## Backend CLI commands

Show CLI help:

```bash
python -m backend.cli --help
```

Run health checks:

```bash
python -m backend.cli --health-check --execution-mode balanced --run-folder runs/current
```

Canonical post-judge transition: run `final_auditor`, write `final_audit.json`, and return integration outcome:

```bash
python -m backend.cli --run-post-judge-transition --execution-mode premium --run-folder runs/current
```

Backward-compatible alias for the same post-judge flow:

```bash
python -m backend.cli --run-final-audit --execution-mode premium --run-folder runs/current
```

Read the canonical post-judge route:

```bash
python -m backend.cli --read-post-judge-route --run-folder runs/current
```

Backward-compatible alias for route reading:

```bash
python -m backend.cli --read-final-audit-route --run-folder runs/current
```

Print GUI-facing health payload:

```bash
python -m backend.cli --gui-health-status --run-folder runs/current
```

Print legacy bridge contract:

```bash
python -m backend.cli --bridge-status --run-folder runs/current
```

## Smoke test

There is no full automated test suite yet. Before opening follow-up feature work, run at least:

```bash
python -m backend.cli --help
python - <<'PY'
import backend
print(backend.__all__)
PY
```

`--health-check` can also be used without secrets; it should return JSON with config errors instead of leaking secrets.

## Documentation

- `docs/MAIN_APP_MVI_INTEGRATION.md` — minimal integration plan for the existing app flow.
- `docs/ROADMAP_AI_TEAM_ORCHESTRATOR.md` — planned AI team orchestrator architecture.
- `docs/BRANCHING_STRATEGY.md` — branch/PR baseline rules after cleanup.

## PR baseline decision

- PR #3 is the backend baseline for this cleanup: backend package, provider-based role configuration, CLI, `final_auditor`, health checks, artifacts, pipeline, README updates, and MVI integration docs.
- PR #1 and PR #2 are treated as deprecated/duplicative when covered by PR #3.
- PR #4 is a separate macOS integration documentation task and is not mixed into this backend cleanup.

## Next planned feature

The next planned feature is a universal AI team orchestrator through OpenRouter with optional Premium Review. It should be developed from `chore/cleanup-repo-structure` or from `main` after this cleanup branch is merged.
