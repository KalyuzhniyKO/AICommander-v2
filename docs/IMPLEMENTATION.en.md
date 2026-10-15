# AICommander 3.0 — verified implementation (15 October 2026)

[Русская версия](IMPLEMENTATION.md) · [Evidence-based audit (RU)](AUDIT_2026-10-15.md)

**Evidence:** `main` source after [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35), plus [six passing GitHub Actions jobs](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156) on Python 3.11–3.13 / Linux and Windows. This is **not** live Zorin/MacBook integration verification.

| Component | Present | Boundary |
|---|---|---|
| FastAPI, SQLite, UI | Tasks, rounds, simple local frontend | All API routes **unauthenticated** |
| Legacy text roles | Keyword routing, direct OpenRouter model client and fallback | Not the installed OmniRouter; no automatic same-round role-to-role outputs |
| Offline taskflow | MockDirector, Analyst → Architect → Developer typed artifacts, persistence, idempotency, owner decisions | Mock only; no real Hermes/models/Codex |
| Offline executor | Trusted disposable Git fixtures/worktrees, approved commands, actual exit codes, bounded outputs | Separate library, not linked to taskflow/UI; **not an OS/network sandbox** |
| CI | pytest, compileall, pip check on Linux/Windows | No macOS, browser E2E or live Zorin tests in `main` |

**Not implemented or verified:** Hermes Director → OmniRouter live inference, Codex CLI orchestration, independent QA/Reviewer, automatic GitHub draft PR, cost management, authenticated MacBook owner UI, production deployment or warehouse_config pilot. Model IDs in examples are not evidence of availability.

**Security:** `/taskflow/*/owner-decision` is also unauthenticated. Mock approval is a database state change, **not permission to merge or deploy**. The default CLI binds localhost but an alternative ASGI bind could expose the server; never publish it to a LAN or the internet. The [Zorin inventory](ZORIN_INTEGRATION.md) is partial with separately identified owner-reported checks.

**Branches/PR:** [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35) merged v3 to default `main`; old v2 is preserved under [`v2-legacy`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/v2-legacy). [PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) and [#33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) delivered offline components. [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) MacBook UI remains a conflicting Draft, not part of `main`. New PRs target `main`.
