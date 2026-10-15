[Русская версия](IMPLEMENTATION.md)

# Audit of the v3 foundation (2026-10-14)

### Preserved from AICommander-v2
FastAPI local REST endpoints; SQLite tasks, rounds, agent outputs and model errors; minimal browser interface; basic text role prompts and keyword router; OpenRouter-compatible transport; model fallback and availability test; pytest fixtures. These are MVP foundations only.

### Not yet supported
- No Hermes Director and no tested OmniRouter API connection.
- No separate Analyst or executing QA agent; existing `coder` supplies text plans.
- `round_runner` builds context before role loop; next role does not automatically see previous role's same-round output.
- An offline worktree executor is available as a separate library (PR #33); it is not connected to taskflow and is not an OS sandbox. Real Codex execution, QA and automatic PR integration remain unavailable.
- PR #30 protects the main app with HTTP Basic, CSRF and loopback Host checks; use an SSH tunnel.
- Free model IDs are placeholders, not confirmed active models.

### Not copied from v2
Old CLI/bridge for macOS, Director/Judge/Final Auditor migration modules, premium OpenAI review logic/API, redundant role wrappers and old plans. v3's paid ChatGPT web review is a **manual** step; API usage is a separate product/cost.

### Research and pending UI PR

- [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) merged (OSS research / ADR-001); #12 remains open until #11 verifies Zorin integration contracts.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) is an open Draft for the MacBook UI. This feature branch integrates the panel with the merged taskflow; main receives it only after PR review and merge.
- [#27](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27) and [#29](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) are offline packages; [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28) overlaps PR #30.

### Stage 00 verification
Issue #10 removes the broken legacy bridge import, closes API SQLite connections and HTTPError handles, and refreshes round summaries after role reruns. 40 offline tests cover API behavior, resources, config and bounded fallback attempts. GitHub Actions covers Python 3.11–3.13 on Linux/Windows.

Actual local exit codes and output: [Python 3.13](qa-foundation-python-3.13.14.json), [Python 3.12](qa-foundation-python-3.12.10.json). Compilation, pytest and pip check exited 0 in both environments; a separate uvicorn HTTP smoke passed using temporary SQLite. Pytest emits one Starlette dependency deprecation warning about migrating from httpx to httpx2. Python 3.11 is not installed locally; verify its result in GitHub Actions.

### Panel/taskflow integration (2026-10-15)
The panel uses existing taskflow commands, typed artifacts, stages and timeline. It preserves expected_version and idempotency keys, refreshes after conflicts and replays, and keeps legacy rounds separate. Additive panel migrations preserve legacy, taskflow and early panel databases. See [runbook](MACBOOK_PANEL.md) and [actual QA](QA_PANEL.md). All completion remains mock artifacts only.
