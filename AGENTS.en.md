[Русская версия](AGENTS.md)

# AICommander-v3 / Instructions for Codex
Read `README.md` and `docs/{PRODUCT_SPEC,IMPLEMENTATION,ROADMAP,OPEN_SOURCE_REVIEW}.md` before working.

- Each [V3] GitHub Issue is a bounded independent PR. No unrequested scope creep; include tests and explicit evidence.
- **Do not recreate OmniRouter or Hermes.** Inspect the deployed Zorin configuration READ-ONLY (no keys in logs), document supported integration methods and use a narrow adapter.
- Current v3 foundation is **not** a completed Hermes/Codex agent system. Don't claim planned features are implemented.
- Separate planner output, git changes, test execution and reviewer verdict with typed artifacts; do not infer test success from LLM text.
- No access to production warehouse DB, productive servers or secrets; all code execution in worktrees/containers with disposable databases.
- No automatic merge, deploy, destructive operations or access outside approved workspace. Explicit user approval required.
- Don't automate the paid ChatGPT web UI or harvest session cookies to turn it into an API; web expert escalation is manual. OpenAI API is billed separately.
- Preserve attribution and full required licence texts if copying external open-source code (see `docs/OPEN_SOURCE_REVIEW.md`). No third-party code was copied in the foundation.
- Evaluate before adopting CrewAI, LangGraph, OpenHands or Microsoft Agent Framework: they may duplicate Hermes. Prefer one workflow owner.
- Re-run `pytest -q` and smoke tests before PR; never invent a passing run.
