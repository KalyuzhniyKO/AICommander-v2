[Русская версия](README.md)

# AICommander 3.0 — AI Development Team
**Status: Foundation MVP.** Existing working components of [AICommander-v2](https://github.com/KalyuzhniyKO/AICommander-v2) have been selectively retained, not the whole old project.

## Goal
The owner uses a MacBook to give the team tasks and accept results. On Zorin OS, an **existing** Hermes installation acts as Director and an **existing** OmniRouter selects free/affordable AI models. Agents: Director, Analyst, Architect, Developer, QA and independent Reviewer. For high-complexity coding, delegate to Codex CLI; paid ChatGPT **web** is used only as a manual expert review, never via an unsupported scraping/browser automation API.

The end-to-end workflow is: `owner -> Director -> Analyst -> Architect (if needed) -> Developer (isolated worktree) -> QA (real tests) -> Reviewer (independent diff review) -> draft PR -> owner approval`.

## Already in this foundation
- FastAPI service and minimal web UI on localhost.
- Creation and history of tasks, human-approved rounds, legacy role prompts and simple routing.
- OpenRouter-compatible model calls, retry/fallback, model status checks.
- SQLite state and baseline unit tests without live model credentials.

**Not yet implemented:** verified Hermes/OmniRouter integration; Analyst/QA roles; real code editing or Codex CLI execution; safe worktree/sandbox; GitHub PR creation; authenticated remote UI; escalation and budget tracking. An AI-written answer **is not evidence** that code ran or tests passed.

## Deliberately not imported from v2
Previous macOS app bridges, Director/Judge/Final Auditor migration pack, empty redundant agent wrapper files, obsolete roadmaps, separate OpenAI API Premium Review (not applicable to browser ChatGPT), legacy model presets.

## Local run (prototype, on test machine only)
Python **3.11–3.13**; Linux/macOS:
```bash
python3 -m venv .venv && source .venv/bin/activate
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

Open http://127.0.0.1:8000 . Configure real model IDs. The prototype is unauthenticated and **must not** be exposed to the network.

## Read before starting Codex tasks
- [Product vision and roles](docs/PRODUCT_SPEC.md)
- [Actually shipped vs planned](docs/IMPLEMENTATION.md)
- [Phased roadmap](docs/ROADMAP.md)
- [Open-source research and attribution](docs/OPEN_SOURCE_REVIEW.md)
- [Codex instructions](AGENTS.md)

**Important:** this `v3-foundation` branch is a staging area inside AICommander-v2 because the connected GitHub interface cannot create a new repository. The `main` branch of v2 is untouched. Export this *minimal tree* into a dedicated `AICommander-v3` repository when repository creation is available.
