# AICommander 3.0 GitHub workflow

[Русская версия](GITHUB_WORKFLOW.md) · [Roadmap](ROADMAP.en.md)

Development targets `v3-foundation` using one feature branch and PR per bounded task. Do not modify the original AICommander-v2 `main`. The standalone repo move is tracked in [#23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23).

[Bug report](../.github/ISSUE_TEMPLATE/bug_report.md) · [Feature request](../.github/ISSUE_TEMPLATE/feature_request.md) · [Codex task](../.github/ISSUE_TEMPLATE/codex_task.md) · [PR template](../.github/pull_request_template.md) · [English issue templates](templates/ISSUE_TEMPLATES.en.md) · [English PR template](templates/PULL_REQUEST_TEMPLATE.en.md).

**GitHub UI limitation:** template forms may only be picked up from the repository default branch, currently v2 `main`. Until the standalone v3 repository is available, templates in `v3-foundation` can be copied manually. Do not overwrite v2 `main` simply to expose forms.

Procedure: write Russian-first Issues with English links, testable acceptance criteria and dependency notes. Work in separate feature branches; avoid overlapping changes without a shared contract. In particular, [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) may duplicate [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28). Include actual test commands, exit codes, CI references, changed files, data boundaries and unverified capabilities. Issue #12 remains open despite merged research PR #26, pending #11 live contract checks.

Never expose secrets, private machine details or production warehouse data; merge/deploy require explicit owner approval.
