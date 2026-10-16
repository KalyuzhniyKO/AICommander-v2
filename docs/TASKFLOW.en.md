# Offline taskflow v1

**#14 update, 16 October 2026:** [Hermes planning v2](HERMES_TASKFLOW.en.md)
uses the installed runtime and the same journal/lifecycle. Mock-only statements
below describe preserved v1 and its offline implementation. Real-result import
through resolve_unknown is rejected; only explicit failed-attempt resolution
is supported after confirming worker shutdown.

[Russian primary documentation](TASKFLOW.md) · [Issue #27](https://github.com/KalyuzhniyKO/AICommander-v3/issues/27)

The `/taskflow` namespace implements a persisted, deterministic Mock Director workflow only. Analyst requirements are passed as typed content into Architect design and then Developer plan. No real model, Hermes, OmniRouter, Codex, shell execution or QA occurs. Parent issue #14 remains open.

Runs have planned, running, failed, blocked, awaiting_owner, done and cancelled states. Role calculation, artifacts, timeline, version and idempotency response commit atomically in SQLite. Commands require an idempotency key and expected version. Duplicate commands replay their original response; stale versions and key reuse with a different body conflict. Step attempts, including mock failures, are bounded. Cancellation is terminal. Completion requires an explicit owner decision.

`done` means approved **mock artifacts**, not completed software. Every snapshot declares `director: mock`, `simulated: true`, `completion_scope: mock_artifacts_only`. Developer plans declare `execution: not_executed`. This localhost prototype does not authenticate the owner.

Frozen UI artifacts: [response schema](contracts/taskflow-v1.schema.json), [request schemas](contracts/taskflow-v1.requests.json), [example](contracts/taskflow-v1.example.json). Export using `python -m backend.app.taskflow.export_contract`; the exporter uses in-memory SQLite. The Russian documentation specifies routes, transition rules, error handling, replay semantics, additive migration and best-effort redaction limitations.

Run `python -m compileall backend`, `python -m pytest -q` and `python -m pip check`. Actual verification output is recorded in [qa-issue-27.json](qa-issue-27.json).

## Owner panel integration (PR #30)

The main app protects every taskflow route with HTTP Basic and CSRF/Origin/Host checks. The reusable router alone does not authenticate callers when mounted in another app. The panel uses the existing versioned/idempotent taskflow contract, reads current snapshots after conflicts/replays, and keeps legacy rounds separate. See [Russian panel runbook](MACBOOK_PANEL.md). Completion still means mock artifacts only; no real executor, models, QA or deployment is invoked.

## Offline operation protocol before #14

Step calculation now runs outside SQLite write transactions. A durable operation
reservation prevents duplicate dispatch; result_ready preserves computed output
across a final-commit failure. Unknown outcomes are not retried automatically.
Cancellation/version fencing discards late results. Migration 2 is additive;
RunSnapshot v1 still marks all artifacts mock/simulated. Protected
`GET /taskflow/runs/{run_id}/operations` exposes metadata only.
[Protocol and recovery (EN)](OPERATIONS.en.md). No real transport is connected.
