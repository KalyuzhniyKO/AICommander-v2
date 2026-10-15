# GitHub workflow — AICommander 3.0

[Русская версия](GITHUB_WORKFLOW.md) · [Roadmap](ROADMAP.en.md) · [Audit (RU)](AUDIT_2026-10-15.md)

[AICommander-v3](https://github.com/KalyuzhniyKO/AICommander-v3) was renamed and v3 merged into the default **`main`** via [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35). Old v2 is preserved in **`v2-legacy`** (same repository). **`v3-foundation` is historical; new PRs target `main`**. Issue #23 repository rename is complete.

1. Write Russian-first Issues with an English-version link, acceptance criteria and scope/dependencies.
2. Use separate branches targeting `main`. Independent tasks may run in parallel; coordinate shared API/database work.
3. [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) MacBook panel is merged and integrated with offline taskflow. Do not start duplicate [#28](https://github.com/KalyuzhniyKO/AICommander-v3/issues/28) UI implementation without resolving its relationship.
4. Report **actual** tests and CI for the current PR head/base; old green checks do not validate a conflicted PR against the new base. List unverified live Zorin/Hermes behavior and security limitations.
5. Human approval is required before merge/deploy; **mock taskflow owner approval is not Git authorization**. Keep production data, credentials and private machine details out of public repository material.

[Bug report](../.github/ISSUE_TEMPLATE/bug_report.md) · [Feature request](../.github/ISSUE_TEMPLATE/feature_request.md) · [Task template](../.github/ISSUE_TEMPLATE/codex_task.md) · [PR template](../.github/pull_request_template.md) · [English issue templates](templates/ISSUE_TEMPLATES.en.md).

Templates are now on the GitHub default branch and should be discoverable. The connected GitHub tool can directly help with reviews/docs/PRs without Codex, but **the AICommander application itself has no live GitHub PR integration**.
