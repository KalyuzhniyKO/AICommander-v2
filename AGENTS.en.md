# AICommander 3.0 / Instructions for Codex
[Русский](AGENTS.md)

Read `README.en.md`, `docs/PRODUCT_SPEC.en.md`, `docs/IMPLEMENTATION.en.md`, `docs/ROADMAP.en.md`, `docs/MODEL_SELECTION.en.md` and `docs/OPEN_SOURCE_REVIEW.en.md` before work.

- Execute the [V3] GitHub Issues in explicit order, one issue per feature branch and PR. Provide **actual** tests and evidence.
- Reuse existing Hermes and OmniRouter installed on Zorin OS. First verify their actual interfaces READ-ONLY; never invent APIs or log secrets.
- Do not claim features are implemented until running verified tests; the v3 foundation is deliberately minimal.
- Hand structured artifacts between roles. A Developer must edit actual test worktree files; QA must report process exit codes; Reviewer must inspect git diff.
- No access to production warehouse databases, servers, unrelated directories, passwords or SSH keys. No auto merge, deployment or destructive commands.
- ChatGPT Web is a manual expert escalation, never a scraped API. OpenAI API is a separate paid product.
- Credit upstream authors and include complete mandatory license notices for copied third-party code; no external code was copied into this foundation.
- Avoid a second router/orchestrator engine until the OSS ADR demonstrates a distinct missing capability.
- If blocked by connector/tool limits, create a GitHub Issue with exact acceptance criteria instead of silently abandoning the operation.
