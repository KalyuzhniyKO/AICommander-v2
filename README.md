# AICommander-v2

AICommander-v2 is a human-in-the-loop AI team orchestrator MVP. A user enters a large product or engineering task, the backend chooses the needed roles, runs **one** AI-team round, stores the role outputs, and then stops until the user adds a correction/comment and explicitly starts the next round.

The main free workflow uses **OpenRouter** chat-completion models. OpenAI or other paid AI is not required for the main workflow and is only used by the optional **Premium Review / Expert Check** stage when explicitly enabled.

## Branch for this feature

This implementation is intended to be developed from `main` on:

```bash
feature/free-ai-team-orchestrator
```

It is not part of older migration-pack branches, `codex/cleanup-repository-structure-for-next-feature`, or the separate macOS integration work.

## MVP capabilities

- Create a task/project with `POST /tasks`.
- Automatically detect the task type and select roles for a single round.
- Run role prompts through OpenRouter with per-role model fallback.
- Store selected roles, outputs, provider/model, model errors, comments, Premium Review status, and timestamps in SQLite.
- Add a user correction/comment and run the next round manually.
- Rerun a specific role manually.
- Run or repeat Premium Review manually later.
- Inspect model availability/failure status with `GET /models/status`.
- Use a minimal frontend in `frontend/`.

## Role routing

The MVP roles are:

- `manager` — understands the task, task type, goals, and role plan.
- `architect` — proposes architecture, stack, folders, database, and API.
- `designer` — proposes UI/UX, screens, and user flows.
- `coder` — proposes implementation plan and code/file changes.
- `reviewer` — checks errors, gaps, contradictions, and risks.

Roles are not always all executed:

- Website/landing: `manager`, `designer`, `coder`, `reviewer`.
- Web app/product/API/database task: `manager`, `architect`, `designer`, `coder`, `reviewer`.
- Code review: `manager`, `reviewer`.
- Documentation: `manager`, `reviewer`.
- General task fallback: `manager`, `coder`, `reviewer`.

## Repository structure

```text
backend/
  app/
    main.py                  # REST API, FastAPI app, stdlib HTTP fallback
    config.py                # .env, settings, model config loading
    schemas.py               # lightweight request schema helpers
    providers/
      base.py                # provider abstraction
      openrouter.py          # required free-workflow provider
      openai.py              # optional Premium Review provider
    agents/
      base.py                # role prompts
      manager.py
      architect.py
      designer.py
      coder.py
      reviewer.py
    orchestration/
      role_router.py         # automatic role selection
      fallback.py            # model fallback and model status updates
      round_runner.py        # one-round human-in-the-loop execution
      premium_review.py      # optional paid expert review
    storage/
      db.py                  # SQLite schema
      repositories.py        # persistence helpers
frontend/
  index.html
  app.js
  style.css
config/
  models.example.json
.env.example
requirements.txt
```

The older migration-baseline modules under `backend/` remain in place for compatibility with previous CLI/integration entrypoints.

## Install dependencies

The backend uses the Python standard library for provider HTTP calls and SQLite. FastAPI/Uvicorn are recommended for serving the REST API and static frontend:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

If FastAPI is not installed, `python -m backend.app.main` starts a small stdlib development server for smoke testing.

## Environment setup

Create a local `.env` from the example:

```bash
cp .env.example .env
```

Then edit `.env`:

```bash
OPENROUTER_API_KEY=your_openrouter_key
OPENAI_API_KEY=
ENABLE_PREMIUM_REVIEW=false
DEFAULT_TIMEOUT_SECONDS=60
MAX_MODEL_RETRIES=1
DATABASE_URL=sqlite:///./aicommander.db
```

Do not commit `.env`, API keys, or secrets.

## Model configuration

Copy the editable model example:

```bash
cp config/models.example.json config/models.json
```

Edit `config/models.json` to use current OpenRouter free model IDs for normal roles. Placeholder model IDs are intentionally used in the example because the free OpenRouter model list changes over time.

Example shape:

```json
{
  "manager": ["openrouter/free-model-1", "openrouter/free-model-2"],
  "architect": ["openrouter/free-model-1"],
  "designer": ["openrouter/free-model-1"],
  "coder": ["openrouter/free-coder-model-1"],
  "reviewer": ["openrouter/free-model-1"],
  "premium_reviewer": ["openai/gpt-4.1", "openai/gpt-4o"]
}
```

No code change is required when changing models.

## Run the backend

Recommended FastAPI mode:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Stdlib fallback mode:

```bash
python -m backend.app.main
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

## Open the frontend

When running through FastAPI, open:

```text
http://127.0.0.1:8000/
```

The frontend supports:

1. New task input.
2. `Run AI team` first round.
3. Per-role round results.
4. Used provider/model for every role.
5. Model/API errors.
6. User correction/comment input.
7. `Run next round`.
8. Role rerun.
9. Manual `Run Premium Review`.
10. Premium Review status/output.
11. Model status table.

## API endpoints

- `GET /health`
- `POST /tasks`
- `GET /tasks/{task_id}`
- `POST /tasks/{task_id}/rounds`
- `POST /rounds/{round_id}/roles/{role}/rerun`
- `POST /rounds/{round_id}/premium-review`
- `GET /models/status`

Example no-key smoke flow (provider calls fail gracefully and are stored):

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"description":"Сделай складскую программу с остатками, приходом, расходом, пользователями и отчетами."}'

curl -X POST http://127.0.0.1:8000/tasks/1/rounds \
  -H 'Content-Type: application/json' \
  -d '{"user_comment":""}'
```

## Fallback behavior

For each role:

1. Load model IDs from `config/models.json` or `config/models.example.json`.
2. Try the first configured OpenRouter model.
3. On timeout, rate limit, quota/token error, unavailable model, API error, empty/bad response, or missing API key, store the error and mark the model failed.
4. Try the next model.
5. Store all model errors in SQLite.
6. Store the provider/model that succeeded.
7. Keep the round alive even if every model for one role fails.

When no model succeeds, the role output records a clear local fallback message so the user can fix configuration and manually rerun the role.

## Model status

`GET /models/status` returns configured and observed models with:

- `provider`
- `model_id`
- `role`
- `status`: `available`, `failed`, or `unknown`
- `last_error`
- `last_success_at`
- `last_failure_at`
- `response_time_ms`

## Premium Review / Expert Check

Premium Review is optional and disabled by default:

```bash
ENABLE_PREMIUM_REVIEW=false
```

Rules:

- It runs only when manually requested with `POST /rounds/{round_id}/premium-review`.
- It does not block the free OpenRouter round workflow.
- It uses configured `premium_reviewer` models, filtered to OpenAI in this MVP.
- If disabled, status becomes `skipped_disabled`.
- If enabled but `OPENAI_API_KEY` is missing, status becomes `skipped_not_configured`.
- If quota/tokens/rate-limit errors occur, status becomes `skipped_quota_or_tokens`.
- Other paid-provider API failures become `skipped_api_error`.
- Success becomes `completed` and stores the review output/model.

Manual repeat:

```bash
curl -X POST http://127.0.0.1:8000/rounds/1/premium-review
```

## Smoke checks

Minimum local checks that do not require real API keys:

```bash
python -m compileall backend
python - <<'PY'
from backend.app.main import api_health
print(api_health())
PY
python - <<'PY'
from backend.app.main import app
print('app import ok', app is not None)
PY
```

With FastAPI/Uvicorn installed, also check:

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health
```

Live model calls are expected to fail gracefully when keys or valid model IDs are absent; these failures should be stored in `model_errors` and `model_status`, not crash the workflow.
