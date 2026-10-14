# AICommander 3.0 — Virtual AI Development Team

[**Русский / Russian version**](README.md)

**Status:** lean foundation MVP prepared. This is **not yet** a working integration of Hermes, OmniRouter, Codex execution or QA. The original [AICommander-v2](https://github.com/KalyuzhniyKO/AICommander-v2) is preserved unchanged.

## Verified status — 15 October 2026

- [PR #25](https://github.com/KalyuzhniyKO/AICommander-v2/pull/25) **merged**: foundation fixes, tests and [green CI](https://github.com/KalyuzhniyKO/AICommander-v2/actions/runs/38635577007).
- [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) **merged**: OSS research and ADR-001; [Issue #12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) remains open until #11 confirms real compatibility.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) is an **open Draft** proposing the MacBook panel, not yet merged.
- **Without Zorin:** independent [#29 — Git worktree](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) work and [#27 — taskflow](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27) contract design may proceed; coordinate implementation with PR #30 backend changes. **Pause [#28 — UI](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28)** to avoid duplicating PR #30. Live Hermes/OmniRoute requires owner booting Zorin and read-only #11.

## Vision
The human owner enters tasks from a MacBook and approves the final changes. Existing Hermes and OmniRouter run on Zorin OS. AICommander should coordinate a team without re-implementing their existing responsibilities:

**Owner → Director (Hermes) → Analyst → Architect (if needed) → Developer (Codex for complex work) → real QA tests → independent Reviewer → GitHub draft PR → owner approval.**

The goal is real, test-backed software changes, not several independent textual responses.

## Retained from v2
Local FastAPI, minimal web UI, tasks and rounds, SQLite history, simple role prompts and keyword role routing, an OpenRouter-compatible transport with fallback and model availability checks, and credential-free test scaffolding.

**Planned, not implemented:** verified Hermes/OmniRouter integration, Analyst and executing QA roles, Codex CLI tool execution, safe git worktrees, PR generation, authenticated MacBook dashboard and budget policy. Local foundation tests and HTTP smoke have passed; see the implementation status for recorded results.

**Deliberately excluded:** legacy macOS integration bridges, old Director/Judge/Final Auditor migration pack, obsolete roadmaps and role wrappers, and the optional OpenAI API Premium Review. ChatGPT web is an optional **manual** expert handoff; ChatGPT subscription access does not imply API entitlements.

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
| GitHub Issues | [English descriptions](docs/ISSUES_EN.md) | [Russian-first issues](https://github.com/KalyuzhniyKO/AICommander-v2/issues/24) |
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
The GitHub integration currently cannot create a dedicated repository. Foundation lives temporarily on [`v3-foundation`](https://github.com/KalyuzhniyKO/AICommander-v2/tree/v3-foundation), leaving v2 `main` intact. [Migration Issue #23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23).

[Stage #10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) is complete. See the [parallel roadmap](docs/ROADMAP.en.md) and [Issue #24](https://github.com/KalyuzhniyKO/AICommander-v2/issues/24).
