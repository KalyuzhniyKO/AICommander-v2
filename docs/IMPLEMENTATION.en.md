[Русская версия](IMPLEMENTATION.md)

# Audit of the v3 foundation (2026-10-14)

### Preserved from AICommander-v2
FastAPI local REST endpoints; SQLite tasks, rounds, agent outputs and model errors; minimal browser interface; basic text role prompts and keyword router; OpenRouter-compatible transport; model fallback and availability test; pytest fixtures. These are MVP foundations only.

### Not yet supported
- No Hermes Director and no tested OmniRouter API connection.
- No separate Analyst or executing QA agent; existing `coder` supplies text plans.
- `round_runner` builds context before role loop; next role does not automatically see previous role's same-round output.
- No real worktree, Codex CLI tool, sandboxed command executor, CI, automatic PR or production gate.
- No authentication for network access; prototype binds localhost only.
- Free model IDs are placeholders, not confirmed active models.

### Not copied from v2
Old CLI/bridge for macOS, Director/Judge/Final Auditor migration modules, premium OpenAI review logic/API, redundant role wrappers and old plans. v3's paid ChatGPT web review is a **manual** step; API usage is a separate product/cost.

### Quality caveat
Files were reviewed and composed via GitHub access. Runtime tests cannot be claimed passing until `pytest -q` runs on a machine with Python and dependencies. First Codex issue is to verify and repair that baseline. 
