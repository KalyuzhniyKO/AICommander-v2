# Offline taskflow v1

[Russian primary documentation](TASKFLOW.md) · [Issue #27](https://github.com/KalyuzhniyKO/AICommander-v3/issues/27)

The `/taskflow` namespace implements a persisted, deterministic Mock Director workflow only. Analyst requirements are passed as typed content into Architect design and then Developer plan. No real model, Hermes, OmniRouter, Codex, shell execution or QA occurs. Parent issue #14 remains open.

Runs have planned, running, failed, blocked, awaiting_owner, done and cancelled states. Role calculation, artifacts, timeline, version and idempotency response commit atomically in SQLite. Commands require an idempotency key and expected version. Duplicate commands replay their original response; stale versions and key reuse with a different body conflict. Step attempts, including mock failures, are bounded. Cancellation is terminal. Completion requires an explicit owner decision.

`done` means approved **mock artifacts**, not completed software. Every snapshot declares `director: mock`, `simulated: true`, `completion_scope: mock_artifacts_only`. Developer plans declare `execution: not_executed`. This localhost prototype does not authenticate the owner.

Frozen UI artifacts: [response schema](contracts/taskflow-v1.schema.json), [request schemas](contracts/taskflow-v1.requests.json), [example](contracts/taskflow-v1.example.json). Export using `python -m backend.app.taskflow.export_contract`; the exporter uses in-memory SQLite. The Russian documentation specifies routes, transition rules, error handling, replay semantics, additive migration and best-effort redaction limitations.

Run `python -m compileall backend`, `python -m pytest -q` and `python -m pip check`. Actual verification output is recorded in [qa-issue-27.json](qa-issue-27.json).
