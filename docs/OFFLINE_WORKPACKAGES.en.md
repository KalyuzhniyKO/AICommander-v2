# Offline work packages — historical task briefs

[Russian main README](../README.md) · [Sequential master queue](https://github.com/KalyuzhniyKO/AICommander-v3/issues/24)

**Historical brief (updated 15 October 2026):** offline taskflow PR #31 and offline worktree PR #33 are already merged into `main`; UI PR #30 remains a conflicted Draft. The tasks below are the original acceptance briefs, **not a list of remaining work**. They were originally designed to run independently from `v3-foundation`. Each uses its own git branch/worktree and produces a draft PR. Their existing parent issues remain open until real integration is proven. Never touch production warehouse data, Hermes/OmniRoute running services, real API credentials or deployments.

## offline-contracts

### Scope
Implement **only** deterministic task lifecycle/state and typed role artifacts in the AICommander FastAPI/SQLite foundation, with a mock Director instead of a real Hermes integration. Clearly distinguish planned, running, failed, blocked, awaiting_owner and done states; ensure atomic persisted transitions, role artifacts carrying task_id/run_id/role/type/created_at/status and redacted content. Derive schemas and tests first. Support cancellation and restart/resume with idempotency and a max-steps bound; no automatic LLM or shell execution. Add API contract documentation and tests, Russian first with an English link.

### Acceptance
A fully offline test creates a task, writes Analyst requirements, Architect design and Developer plan as separate artifacts, verifies role-to-role handoff, invalid transition rejection, persistence after app restart, and owner approval. No Hermes, OmniRouter, Codex CLI, worktree execution or real model calls. Limit file changes to backend/app/taskflow*, backend/app/storage*, relevant API endpoints, migrations, dedicated tests and docs; coordinate the contracts with UI via documented JSON fixtures.

### Model
GPT-6.1 Sol / High (or closest available). Parent [#14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14). Need a separate PR.

## offline-ui

### Scope
Create the first **MacBook-friendly, responsive Russian-first** AICommander frontend inside `frontend/`, without waiting for Zorin or authenticated remote deployment. Components: project/task list, AI Director chat presentation, role board/status, task details, timeline, model info, test report/diff viewer, approval buttons. Use static fixtures/mocks only for features without backend APIs; clearly mark simulation vs real. Provide English localization selectable through UI; preserve the existing local foundation endpoints and no credential exposure. Do not implement or modify backend routes under this issue.

### Acceptance
UI preview demonstrates user journey with fixtures, existing basic API endpoints still work, inaccessible actions are disabled or labeled as simulation, responsiveness checked in desktop and mobile widths, basic tests (if tooling added) and screenshots in PR. Do not enable remote access, change CORS, or expose the foundation publicly. Limit file changes to frontend, frontend fixtures/tests, UI docs. Interface to be integrated later in parent [#19](https://github.com/KalyuzhniyKO/AICommander-v3/issues/19).

### Model
GPT-6.1 Sol / Medium (or closest available). Separate PR. PWA is a later optional enhancement.

## offline-worktree

### Scope
Build a **provider-neutral, offline, sandbox-oriented Git worktree component** using a disposable fixture Git repository. Create per-task branch/worktree, capture git status/diff, execute only approved test commands with timeout and exit codes; enforce allowed workspace roots, no shell=True, no network access in automated tests, redaction of secrets, cleanup policies and cancellation. Architect the interface so Codex CLI can be wired later, but **do not start Codex or invent any Hermes/OmniRouter API**. Ensure code does not modify the original repository branch or production DB.

### Acceptance
On temporary repositories the tests demonstrate workspace creation, valid changed file diff, blocked path traversal/unsafe command, timeout, safe cleanup and redacted failure logs. Provide clear report and actual test output. No production access, no destructive command. Limit files to new independent backend/app/execution module, its tests and docs; do not change the taskflow schema or frontend. Parent [#15](https://github.com/KalyuzhniyKO/AICommander-v3/issues/15), which remains open until real Codex execution is verified.

### Model
GPT-6 Astra / High (or closest available). Separate PR.

## Integration order

Offline work packages are parallel. Once they are reviewed and merged, use the outcome of the real Zorin read-only inventory [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) to implement verified OmniRouter integration [#13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13), then Hermes Director and real role execution [#14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14). Do not close #15 or #19 based solely on offline subpackages.
