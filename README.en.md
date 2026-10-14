# AICommander 3.0 — Virtual AI Development Team

[**Русский / Russian version**](README.md)

**Status:** lean foundation MVP prepared. This is **not yet** a working integration of Hermes, OmniRouter, Codex execution or QA. The original [AICommander-v2](https://github.com/KalyuzhniyKO/AICommander-v2) is preserved unchanged.

## Vision
The human owner enters tasks from a MacBook and approves the final changes. Existing Hermes and OmniRouter run on Zorin OS. AICommander should coordinate a team without re-implementing their existing responsibilities:

**Owner → Director (Hermes) → Analyst → Architect (if needed) → Developer (Codex for complex work) → real QA tests → independent Reviewer → GitHub draft PR → owner approval.**

The goal is real, test-backed software changes, not several independent textual responses.

## Retained from v2
Local FastAPI, minimal web UI, tasks and rounds, SQLite history, simple role prompts and keyword role routing, an OpenRouter-compatible transport with fallback and model availability checks, and credential-free test scaffolding.

**Planned, not implemented:** verified Hermes/OmniRouter integration, Analyst and executing QA roles, Codex CLI tool execution, safe git worktrees, PR generation, authenticated MacBook dashboard and budget policy. Runtime test success has not yet been confirmed.

**Deliberately excluded:** legacy macOS integration bridges, old Director/Judge/Final Auditor migration pack, obsolete roadmaps and role wrappers, and the optional OpenAI API Premium Review. ChatGPT web is an optional **manual** expert handoff; ChatGPT subscription access does not imply API entitlements.

## Development principles
1. Reuse deployed Hermes and OmniRouter; no redundant directors or model routers.
2. Free/cheap models for routine roles; Codex for complex coding; ChatGPT web only by manual escalation.
3. QA executes actual commands and records exit status; reviewer examines actual Git diff.
4. Keep production warehouse databases, production secrets and files outside the approved workspace inaccessible.
5. One sequential GitHub Issue → one feature branch → one PR; no automatic merge or deployment.

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

## Local test bootstrap
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cp config/models.example.json config/models.json
pytest -q
python -m backend.app.main
```
Open `http://127.0.0.1:8000` locally. Model IDs are placeholders. The prototype is unauthenticated: do **not** expose it outside localhost.

## Repository status
The GitHub integration currently cannot create a dedicated repository. Foundation lives temporarily on [`v3-foundation`](https://github.com/KalyuzhniyKO/AICommander-v2/tree/v3-foundation), leaving v2 `main` intact. [Migration Issue #23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23).

The task queue starts at [Issue #10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10); see [Epic #24](https://github.com/KalyuzhniyKO/AICommander-v2/issues/24) for the sequential checklist and recommended models.
