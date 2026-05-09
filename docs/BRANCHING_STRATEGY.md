# Branching Strategy

## Stable branch

`main` is the stable branch. It should contain reviewed, coherent repository structure and should not receive experimental orchestrator work directly.

## Cleanup branch

`chore/cleanup-repo-structure` is limited to repository cleanup and normalization:

- choose the backend baseline;
- remove or avoid duplicate/contradictory docs;
- normalize README and docs;
- keep the backend importable and CLI discoverable;
- do not implement the future AI team orchestrator feature.

## Future feature branch

`feature/free-ai-team-orchestrator` is reserved for the future universal AI team orchestrator through OpenRouter with optional Premium Review.

Create it from either:

1. `chore/cleanup-repo-structure`, if development starts before cleanup is merged; or
2. `main`, after `chore/cleanup-repo-structure` is merged.

## PR baseline decisions

- PR #1 (`Migration pack #1`) is deprecated as a standalone base because its backend foundation is covered by PR #3.
- PR #2 (`Provider-based orchestration backend`) is deprecated as duplicate/overlapping work because its migration-pack updates are covered by PR #3.
- PR #3 (`Backend migration pack, CLI, final auditor, health checks`) is the backend baseline for cleanup and follow-up backend work.
- PR #4 (`macOS backend CLI integration guide`) is a separate macOS integration documentation task. Do not mix it into backend cleanup unless a later docs-only branch explicitly adopts it.

## Rule of thumb

Use PR #3 concepts and file layout as the backend baseline. Do not resurrect PR #1 or PR #2 as new development bases. Keep PR #4 isolated from backend implementation cleanup.
