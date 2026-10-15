# ADR-001 follow-up: keep one Director and one router

[Full Russian ADR](ADR-001-ORCHESTRATION.md) · [Issue #12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12)

**Revised proposal, 2026-10-15. Integration acceptance is pending #11.** The owner
requested the next documentation task; this does not close #11 or authorize #13.
The six-project upstream comparison is retained at its 2026-10-14 pinned revisions,
including authors, licences and Python constraints. No new upstream release review
or package compatibility test is claimed.

The previous statement that no Zorin report exists is obsolete. [PR #37](https://github.com/KalyuzhniyKO/AICommander-v3/pull/37)
verified SSH access, OmniRoute user-service status and health 200. The installed
package is OmniRoute 3.8.51; Hermes stamp is 0.21.5+5343.ga3b56ca. Hermes custom
Chat Completions and delegation are confirmed in source, not by live inference.
Authenticated model/provider inventory remains unverified by explicit owner choice.

The proposal remains: add none of CrewAI, MetaGPT, LangGraph, OpenHands SDK,
Microsoft Agent Framework or SWE-agent to runtime. Keep role/SOP/event ideas
without copying source. Reconsider LangGraph only for a demonstrated persistence
gap that current Hermes and taskflow cannot cover; reconsider OpenHands only for
a measured Codex executor gap, with a separate runtime/isolation decision.

Current taskflow already persists typed mock artifacts, versions, idempotency and
owner decisions; the panel uses it. The separate offline executor runs approved
trusted-fixture programs and captures real diff/exit codes, but is neither an OS
sandbox nor connected to the taskflow/Codex. No real provider or Director integration
has been added by those modules.

Proposed ownership: OmniRoute routes models; Hermes plans/delegates; AICommander
records task evidence, versions and owner decisions; executor/QA produce actual
file/test evidence; UI displays snapshots and sends owner commands. The current
mock `done` state means approved mock artifacts, not successful execution or QA.

Do not replace `MockDirector.produce()` directly with a network or executor call:
the function currently runs inside a SQLite write transaction. External work needs
an operation reservation, execution outside the write transaction, version-checked
completion and crash reconciliation. Correlation IDs and replay protection for
external effects are not implemented. SQLite rollback cannot undo a model charge
or file edit, and layered retries must not multiply full-stage attempts.

The service uses Node v24.20.0, while noninteractive SSH finds v20.20.0 and misses
user launchers in PATH. Integration must choose and verify its runtime explicitly.
No server connection, credential access, password reset, service change, inference
or framework installation occurred during this documentation follow-up.

Evidence: [Zorin report](ZORIN_INTEGRATION.md), [taskflow](TASKFLOW.md),
[executor](EXECUTION.md), [source mapping](research/adr-001-zorin-followup.json),
[follow-up QA](qa-issue-12-followup.json). Finish and review #11, then accept/revise
this ADR before #13. Both issues remain open.
