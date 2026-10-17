# Hermes Director: real planning, contract v2

[Русский](HERMES_TASKFLOW.md) · [Issue #14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14)

The installed Hermes runtime executes its built-in `delegate_task` for each role
through OmniRoute. AICommander retains the existing lifecycle and operation journal.
Default roles: Analyst → Developer → Reviewer. `include_architect=true` inserts
Architect after Analyst; the caller explicitly chooses this at creation.
There is no second agent loop or model router.

**Planning only:** Developer returns implementation steps; Reviewer reviews that
plan. Code execution, Codex CLI, tests and diff review belong to #15/#16.
`done` means owner-approved planning artifacts: `schema_version=2.0`,
`director=hermes`, `simulated=false`, `completion_scope=real_planning_artifacts_only`,
`code_executed=false`, `qa_verified=false`, review `scope=planning_only`.
The frozen v1 contract retains Mock Director. The panel defaults to mock runs;
[panel preparation](HERMES_PANEL.en.md) adds separate saved v2 history/cancellation
without model launch/approval. Full integration still belongs to #19. Generic `/health` does not
probe connectivity; protected v2 capabilities reports configuration, not live health.

## Server configuration

Disabled by default. The app runs on the same trusted POSIX host as Hermes.
Set `HERMES_ENABLED=true`, absolute `HERMES_PYTHON` and `HERMES_SOURCE` paths,
`HERMES_EXPECTED_COMMIT` (40-character verified install-stamp revision), and one
exact `HERMES_MODEL` OmniRoute ID without an `omniroute/` prefix.
`HERMES_TIMEOUT_SECONDS` defaults to 90 (1–120);
`HERMES_MAX_OUTPUT_TOKENS` defaults to 768 (64–2048).
Also configure the opt-in [OmniRoute adapter](OMNIROUTE_ADAPTER.en.md).

Capabilities/create do not invoke a model. Unconfigured create returns 503.
Each run binds the model, gateway, SDK revision and runtime paths; changing them
blocks fresh steps. A saved result_ready can still commit without Hermes.
The key is excluded from the binding and can be rotated by an operator.

The bridge selects Hermes's existing PM environment; it never bootstraps, installs
or updates dependencies. The stamp is checked before dispatch. This checks trusted
installation metadata, not cryptographic integrity of the entire source tree.
App Python 3.11–3.13 and installed Hermes Python may differ. Windows supports mock
and contract tests; this local subprocess transport requires POSIX.

## API and handoffs

Existing Basic auth, Host and CSRF rules apply. Create a task with `/tasks`, then:

```text
GET  /taskflow/v2/capabilities
POST /taskflow/v2/tasks/{task_id}/runs
     {"idempotency_key":"create-1","max_steps":4,"include_architect":true}
GET  /taskflow/v2/tasks/{task_id}/runs
GET  /taskflow/v2/runs/{run_id}
POST /taskflow/v2/runs/{run_id}/commands
     {"idempotency_key":"start-1","expected_version":1,"action":"start"}
POST /taskflow/v2/runs/{run_id}/commands
     {"idempotency_key":"step-1","expected_version":2,"action":"step"}
GET  /taskflow/v2/runs/{run_id}/operations
POST /taskflow/v2/runs/{run_id}/owner-decision
     {"idempotency_key":"approve-1","expected_version":6,"decision":"approve"}
```

Each step synchronously runs one role. Read the current version from each response.
There is no automatic background continuation. Existing block/resume/fail/cancel
commands apply. Known failed attempts count against max_steps; resume cannot bypass
it. Cross-mode access is rejected. [Schema](contracts/taskflow-v2.schema.json) ·
[Requests](contracts/taskflow-v2.requests.json).

The model receives the goal and every preceding artifact's full content. The HTTP
boundary checks the exact handoff context, requested model, absent tools and role
JSON Schema. The model produces only new role fields; the backend validates JSON
and wraps it with unchanged typed requirements/design/plan. Invalid responses fail.

Provenance records operation ID, requested model, SDK commit, parent/child session
IDs, input SHA-256, zero tools and one inference POST. This is bridge metadata, not
model testimony or proof of the model ultimately served behind OmniRoute routing.

## Cancellation and recovery

The shared [operation journal](OPERATIONS.en.md) reserves, calls outside SQLite
transactions, saves a durable result, then commits with fencing/version checks.
Completed replay and result_ready after rollback/restart do not invoke inference.

The bridge bounds input/output, time and process-group lifetime. Keys travel over
stdin, never argv/environment/files. The Hermes profile is temporary; memory and
trajectories are disabled; SDK stdout/stderr are suppressed. Network access is
limited to the configured gateway and models/chat-completions paths. SDK/client
retries, fallback and a second inference POST are blocked. JSON Schema is passed
in request overrides and an output contract is appended to context; Hermes's
automatic correction turn is not enabled.

Cancel terminates the process group and discards late results; it cannot refund
already dispatched inference. Timeout/incomplete outcomes become unknown (HTTP409),
with no automatic retry. A fully received invalid response becomes failed. A crash
leaves running operations for explicit operator recovery.

After independently confirming the old worker stopped, a trusted operator may call
`StepOperations(flow).mark_unknown(id)`, then `resolve_unknown(id)` to record failure.
Arbitrary real-result imports are rejected because no independent provenance
verification protocol exists. Recovery mutations have no HTTP endpoint.
Process groups/network guards are not an OS sandbox. The trusted SDK executes
with the user's permissions; do not put credentials in task text. Redaction is
best-effort.

## Migration and evidence

Migration 3 atomically preserves v2 mock records, artifact IDs and saved operations,
adding mode/binding/provenance and reviewer. FK-table reconstruction rolls back on
failure. Old code does not support real records/the new schema: stop workers and
restore a compatible database backup before downgrade. No automatic downgrade.

[Live QA](qa-issue-14-live.json) distinguishes Zorin probes from fixture tests.
Only synthetic tasks, temporary databases/profiles and restricted expiring keys
are used; keys are deleted in finally. Persistent Hermes configuration, warehouse
DBs, user chats and dashboard passwords are unchanged.


## Remaining live acceptance

On 16 October, the three-role chain completed with owner approval; four roles
reached awaiting_owner before the probe script failed while reopening SQLite.
The harness was fixed. Later probes verified process cancellation, timeout/unknown
and replay without redispatch. The final complete run is blocked by provider
quotas: Gemini reports rate_limit; Antigravity returned 429/quota after a successful
Analyst. A direct request without Hermes also timed out while global health was ok.

**#14 stays open** for a complete rerun of the current source after quota recovery:
both role chains, owner approval, reopen/replay and max_steps. Final cancellation-
probe error handling and privacy flags for both agents passed fixture tests;
no inference rerun followed the quota failure. The opt-in transport remains disabled
by default; the persistent app installation was not deployed.
