# AICommander 3.0 — Pull Request template (English)

[Русский шаблон](../../.github/pull_request_template.md) · [Russian workflow](../GITHUB_WORKFLOW.md)

## Changes
Summarize the implemented change.

## Linked work
Issue number, dependencies, overlapping PRs and target `v3-foundation`.

## Actual verification
| Command / workflow | Exit code and result | Log / CI URL |
|---|---|---|
| `python -m pytest -q` | | |
| `python -m compileall backend` | | |
| GitHub Actions | | |

## Scope
Files and modules, API/database changes, new dependencies and licensing attribution.

## Security, evidence and owner approval
- [ ] No secrets, private user data or production warehouse databases.
- [ ] Changes were exercised only in approved test environments.
- [ ] Do not modify original v2 `main`.
- [ ] No automatic merge or deployment.
- [ ] Clearly separate mock, live and unverified integration results.
- [ ] Owner review is required before merge or deployment.

List any limitations and actions the owner must approve.
