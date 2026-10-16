# ADR-001 follow-up: keep one Director and one router

**#14 update, 16 October 2026:** [Hermes planning v2](HERMES_TASKFLOW.en.md)
uses the installed runtime and the same journal/lifecycle. Mock-only statements
below describe preserved v1 and its offline implementation. Real-result import
through resolve_unknown is rejected; only explicit failed-attempt resolution
is supported after confirming worker shutdown.

[Full Russian ADR](ADR-001-ORCHESTRATION.md) · [Issue #12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12)

**Runtime composition decision accepted after authorized live probes, 2026-10-15.**
The owner authorized completion and merge. Existing Hermes delegation and OmniRoute
transport are retained; none of the six reviewed frameworks is added. Live text,
streaming and one built-in delegated child through the same gateway were verified.
[Live evidence](qa-issue-13-live.json) supersedes earlier inventory deferral.
The six-project upstream comparison is retained at its 2026-10-14 pinned revisions,
including authors, licences and Python constraints. No new upstream release review
or package compatibility test is claimed.

The previous statement that no Zorin report exists is obsolete. [PR #37](https://github.com/KalyuzhniyKO/AICommander-v3/pull/37)
verified SSH access, OmniRoute user-service status and health 200. The installed
package is OmniRoute 3.8.51; Hermes stamp is 0.21.5+5343.ga3b56ca. Hermes custom
Chat Completions and delegation were subsequently checked live in isolated profiles.
Authenticated inventory used temporary scoped keys; no credentials are published.

The proposal remains: add none of CrewAI, MetaGPT, LangGraph, OpenHands SDK,
Microsoft Agent Framework or SWE-agent to runtime. Keep role/SOP/event ideas
without copying source. Reconsider LangGraph only for a demonstrated persistence
gap that current Hermes and taskflow cannot cover; reconsider OpenHands only for
a measured Codex executor gap, with a separate runtime/isolation decision.

Current taskflow already persists typed mock artifacts, versions, idempotency and
owner decisions; the panel uses it. The separate offline executor runs approved
trusted-fixture programs and captures real diff/exit codes, but is neither an OS
sandbox nor connected to the taskflow/Codex. No real Director integration was added by those offline modules. The later #13
transport is now explicitly available to manual legacy rounds/model checks.

Proposed ownership: OmniRoute routes models; Hermes plans/delegates; AICommander
records task evidence, versions and owner decisions; executor/QA produce actual
file/test evidence; UI displays snapshots and sends owner commands. The current
mock `done` state means approved mock artifacts, not successful execution or QA.

Do not replace `MockDirector.produce()` directly with a network or executor call:
the original function ran inside a SQLite write transaction. [Offline operations](OPERATIONS.en.md)
now reserve and persist results around lock-free computation for MockDirector. Actual Hermes work still needs
an operation reservation, execution outside the write transaction, version-checked
completion and crash reconciliation. Correlation IDs and replay protection for
external effects are not implemented. SQLite rollback cannot undo a model charge
or file edit, and layered retries must not multiply full-stage attempts.

The service uses Node v24.20.0, while noninteractive SSH finds v20.20.0 and misses
user launchers in PATH. Integration must choose and verify its runtime explicitly.
The original documentation follow-up #38 made no remote calls. Subsequent #13
live probes used ephemeral credentials; no password/service change or framework installation.

Evidence: [Zorin report](ZORIN_INTEGRATION.md), [taskflow](TASKFLOW.md),
[executor](EXECUTION.md), [source mapping](research/adr-001-zorin-followup.json),
[follow-up QA](qa-issue-12-followup.json). The conservative composition decision is accepted; full taskflow Director integration,
external-effect recovery, Codex/sandbox and reboot recovery remain later stages.
