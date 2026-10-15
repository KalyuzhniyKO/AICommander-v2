# AICommander v3 — English descriptions of Codex tasks

[Русская дорожная карта](ROADMAP.md) · [English roadmap](ROADMAP.en.md)

Each section corresponds to a GitHub Issue whose **primary description is in Russian**. English descriptions here are intended as scope-equivalent reference for Codex. Execute them sequentially on separate branches and PRs. Respect `AGENTS.md`.

### V3-00
**[#10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) — Stabilize the minimal v3 foundation.** Run clean installation, `compileall`, `pytest`, FastAPI health/tasks/model-status endpoints; fix regressions, proper SQLite lifecycle and fallback retries. Add GitHub Actions CI for supported Python versions. DoD: repeatable green tests without real API credentials. Dependency: none.

### V3-01
**[#11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11) — Read-only inventory of Hermes and OmniRouter on Zorin.** Inspect actual installations, supported CLI/API contracts, authentication, model metadata, delegation mechanisms, service status and logging boundaries. Never reveal secrets or change installed services. Deliver `docs/ZORIN_INTEGRATION.md` with verified contracts and mock fixtures. Dependency: 00.

### V3-02
**[#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) — Select OSS reuse by ADR.** Compare CrewAI, MetaGPT, LangGraph, OpenHands SDK, Microsoft Agent Framework and SWE-agent, checking license and version. Avoid duplicating Hermes. Deliver an explicit decision record and required upstream attribution for any copied source. Dependency: 01.

### V3-03
**[#13](https://github.com/KalyuzhniyKO/AICommander-v2/issues/13) — Existing OmniRouter adapter.** Connect to verified interface from Stage 01, no invented endpoints; configuration via environment, health/model inventory, bounded timeout/fallback, 429/quota handling, redacted logs, mocked tests plus opt-in integration smoke. Dependency: 02.

### V3-04
**[#14](https://github.com/KalyuzhniyKO/AICommander-v2/issues/14) — Hermes Director and typed role handoffs.** Implement explicit task/round state, Director coordination through installed Hermes, Analyst requirements, Architect plans, Developer access to prior artifacts, independent Reviewer inputs, approval checkpoints, max rounds and migrations. DoD: end-to-end mocked handoff tests. Dependency: 03.

### V3-05
**[#15](https://github.com/KalyuzhniyKO/AICommander-v2/issues/15) — Safe Codex executor.** Verify supported Codex CLI interface, run only in disposable git worktrees, enforce bounded commands, approvals, timeouts, sanitized environment and test-only data. Collect actual diff/exit status. DoD: safe file edit in test repository; unauthorized command blocked. Dependency: 04.

### V3-06
**[#16](https://github.com/KalyuzhniyKO/AICommander-v2/issues/16) — Real QA and independent code review.** Run pytest and Django checks, log exit codes and redacted evidence, verify migrations without production changes; Reviewer reads actual diff and test report. Failed tests block readiness. Dependency: 05.

### V3-07
**[#17](https://github.com/KalyuzhniyKO/AICommander-v2/issues/17) — GitHub issues, branches, draft PR and CI.** Least-privilege GitHub integration links task/run to issue, creates branch and draft PR with evidence, checks CI and never auto-merges. DoD: safe test-repo example. Dependency: 06.

### V3-08
**[#18](https://github.com/KalyuzhniyKO/AICommander-v2/issues/18) — Free-first routing and budget caps.** Add role-specific selections through verified OmniRouter, token/request/time ceilings, rate limits, fallback, cost reporting and escalation. Codex CLI is a supported coding route; paid ChatGPT web handoff is manual only and must not scrape sessions. Dependency: 07.

### V3-09
**[#19](https://github.com/KalyuzhniyKO/AICommander-v2/issues/19) — Authenticated MacBook control dashboard.** Show projects, role statuses, test reports, diffs, cost and approvals. VPN/SSH or authenticated access; no frontend secrets or unauthenticated public API. Dependency: 08.

### V3-10
**[#20](https://github.com/KalyuzhniyKO/AICommander-v2/issues/20) — Security, auditing and recovery.** Scope executor privileges, sandbox working directory/network, protect production DB, require dangerous-operation approval, redact logs, add task resume/idempotency and negative security tests. Dependency: 09.

### V3-11
**[#21](https://github.com/KalyuzhniyKO/AICommander-v2/issues/21) — Safe end-to-end warehouse_config pilot.** From MacBook task via Hermes, Analyst/Developer/QA/Reviewer to draft GitHub PR; show true logs, approvals, model usage and outcomes; only isolated test database. DoD: owner-approved or rejected draft PR, no production change. Dependency: 10.

### V3-12
**[#22](https://github.com/KalyuzhniyKO/AICommander-v2/issues/22) — Zorin operations, backup and optional Lenovo worker.** Document reproducible setup without disturbing existing Hermes/OmniRouter, backup/restore and operational checks. Remote MacBook access via VPN/SSH. Lenovo Omarchy remains optional. Dependency: 11.

### V3-migration
**[#23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23) — Move lean v3 into separate repository.** When the owner creates an empty `AICommander-v3` repository, copy only the minimal branch tree with proper attribution and updated URLs. Preserve existing v2 history/main and prove tests. Does not block stages on the foundation branch.
