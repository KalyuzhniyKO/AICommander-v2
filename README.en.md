# AICommander 3.0 — Virtual AI Development Team

[**Русский / Russian version**](README.md)

**Verified status — 15 October 2026:** this is a **development foundation**, not an operational Hermes/Codex AI team. See the [evidence-based audit (RU)](docs/AUDIT_2026-10-15.md) and [implementation status (EN)](docs/IMPLEMENTATION.en.md).

- Repository was renamed [AICommander-v3](https://github.com/KalyuzhniyKO/AICommander-v3); [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35) merged v3 into the default **`main`** branch after [six passing CI jobs](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156).
- Original v2 is preserved in **`v2-legacy`** in the same repository. `v3-foundation` is historical; new PRs target `main`.
- [PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) mock taskflow and [PR #33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) offline Git worktree executor are merged, but **not** wired into live Hermes/Codex.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) for the MacBook panel remains a **conflicting Draft**, not merged.

## Vision
The human owner enters tasks from a MacBook and approves the final changes. Existing Hermes and OmniRouter run on Zorin OS. AICommander should coordinate a team without re-implementing their existing responsibilities:

**Owner → Director (Hermes) → Analyst → Architect (if needed) → Developer (Codex for complex work) → real QA tests → independent Reviewer → GitHub draft PR → owner approval.**

The goal is real, test-backed software changes, not several independent textual responses.

## Implemented in `main`

FastAPI, SQLite, a simple localhost UI, text role rounds and bounded fallback via **direct OpenRouter** (not the installed OmniRouter). A separate **offline mock taskflow** supports typed Analyst → Architect → Developer artifacts, states, idempotency and owner decision, without real models or code changes. An independent **OfflineExecutor library** manages trusted disposable Git worktrees, approved commands, diffs and actual exit codes; it is **not connected to taskflow/UI** and is **not an OS/network sandbox**.

**Not implemented or verified:** live Hermes → OmniRouter, Codex CLI, independent QA/Reviewer, GitHub PR automation, cost controls, authenticated MacBook dashboard, and a real Zorin E2E test. All current endpoints, including taskflow owner decisions, **have no authentication**. Do not expose this prototype to LAN/internet or use production data. Mock approval is not authorization for actual Git merge/deploy.

**Deliberately excluded from v2:** obsolete macOS bridges, legacy Director/Judge/Final Auditor migration pack, outdated roadmaps and the optional OpenAI API Premium Review. ChatGPT Web remains a manual expert step.

## Development principles
1. Reuse deployed Hermes and OmniRouter; no redundant directors or model routers.
2. Free/cheap models for routine roles; Codex for complex coding; ChatGPT web only by manual escalation.
3. QA executes actual commands and records exit status; reviewer examines actual Git diff.
4. Keep production warehouse databases, production secrets and files outside the approved workspace inaccessible.
5. Each Codex task gets its own feature branch and PR; **independent tasks may run in parallel**. No auto-merge or deployment.

## Documentation

| Topic | English | Russian |
|---|---|---|
| Product specification | [Spec](docs/PRODUCT_SPEC.en.md) | [ТЗ](docs/PRODUCT_SPEC.md) |
| Implementation status | [Status](docs/IMPLEMENTATION.en.md) | [Реализовано](docs/IMPLEMENTATION.md) |
| Codex stages | [Roadmap](docs/ROADMAP.en.md) | [Этапы](docs/ROADMAP.md) |
| Model and reasoning effort | [Selection](docs/MODEL_SELECTION.en.md) | [Выбор моделей](docs/MODEL_SELECTION.md) |
| Open-source reuse | [Review](docs/OPEN_SOURCE_REVIEW.en.md) | [Источники](docs/OPEN_SOURCE_REVIEW.md) |
| Codex rules | [AGENTS](AGENTS.en.md) | [Правила](AGENTS.md) |
| GitHub Issues | [English descriptions](docs/ISSUES_EN.md) | [Russian-first issues](https://github.com/KalyuzhniyKO/AICommander-v3/issues/24) |
| GitHub templates and workflow | [Workflow](docs/GITHUB_WORKFLOW.en.md) | [Процесс](docs/GITHUB_WORKFLOW.md) |

## Local test bootstrap
Python **3.11–3.13**; Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
cp config/models.example.json config/models.json
python -m compileall backend
python -m pytest -q
python -m backend.app.main
```
Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
Copy-Item config/models.example.json config/models.json
.\.venv\Scripts\python.exe -m compileall backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m backend.app.main
```

Tests use temporary databases/configuration, ignore the local `.env`, and block live model HTTP calls. GitHub Actions runs compilation and tests on Python 3.11–3.13 on Linux and Windows. `MAX_MODEL_RETRIES` is the total attempts per model, including the first; exhausted attempts advance to the next model. Tests require no API key.

Smoke endpoints: `GET /health`, `POST /tasks` with JSON `{"description":"Check documentation"}`, `GET /tasks/1`, `GET /models/status`. `POST /models/check` and round creation call models when a key is configured; replace placeholder IDs before using them.

Open `http://127.0.0.1:8000` locally. Model IDs are placeholders. The prototype is unauthenticated: do **not** expose it outside localhost.

## Repository status

The current v3 code is on [`main`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/main), with v2 preserved on [`v2-legacy`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/v2-legacy). New PRs target `main`. Review the [roadmap](docs/ROADMAP.en.md), [GitHub workflow](docs/GITHUB_WORKFLOW.en.md) and [audit](docs/AUDIT_2026-10-15.md).
