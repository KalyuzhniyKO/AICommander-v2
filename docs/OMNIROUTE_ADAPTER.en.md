# OmniRoute transport and live validation

[Full Russian documentation](OMNIROUTE_ADAPTER.md) · [Issue #13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13)

After offline preparation the owner authorized live checks, push and merge. On
2026-10-15, real OmniRoute validated health, authenticated `data[].id` inventory
and text `choices[0].message.content`. A temporary key scoped to
`gemini/gemini-2.5-flash-lite` produced `OK`; all temporary keys were revoked.
Keys expired after 10 minutes and had 0.02–0.05 USD daily caps. This does not
claim zero cost, arbitrary models, tools, or automatic routing were validated.
Management CLI tokens are distinct from inference Bearer keys: management GETs
succeeded while inference models returned 401 for the CLI token.

The provider stays opt-in and performs no startup request. Explicit legacy model
checks, rounds and role reruns now accept `omniroute/<exact gateway model ID>`.
Only one OmniRoute route per role is allowed: no extra model fallback/retry loop.
POST inference is never automatically retried; configured GET attempts are 1–3.
Taskflow remains Mock Director; real Hermes role orchestration belongs to #14.
OpenRouter remains available as a separate explicitly selected legacy transport.

Env: `OMNIROUTE_ENABLED=false`, empty `OMNIROUTE_BASE_URL`/`OMNIROUTE_API_KEY`,
`OMNIROUTE_TIMEOUT_SECONDS=10`, `OMNIROUTE_MAX_GET_ATTEMPTS=2`,
`OMNIROUTE_MAX_OUTPUT_TOKENS=256` (1–8192). The adapter reads env only; the app
retains its existing server .env loader. No discovery of CLI/OAuth/secret stores.
Health sends no Bearer. HTTPS or HTTP loopback, no URL credentials/query/fragment,
redirects or ambient proxies. Response size capped at 1 MiB. Errors disclose
static categories/numeric metadata only; no raw body or chained transport error.
The exact configured credential is masked if echoed; arbitrary secrets are not DLP-scanned.
Cancellation checks around I/O and interrupts retry waits, not active inference.
Timeout is per socket operation, not a strict aggregate deadline. Retry-After wait
is capped at 2 seconds; POST 429/timeouts remain failures for explicit user action.

Opt-in CLI, using a separately supplied secure env:

```bash
OMNIROUTE_RUN_LIVE_SMOKE=true python -m backend.app.providers.omniroute_smoke
```

Health/models only; add `OMNIROUTE_SMOKE_INFERENCE=true` and
`OMNIROUTE_SMOKE_MODEL=<an actual permitted inventory ID>` for inference.
CLI uses 64 output tokens, 45s timeout, one GET attempt and prints summaries only.
Exit 2 without opt-in, 1 on error, 0 on success. An initial 8-token smoke returned
empty content; the adapter rejected it. At 64 tokens the response was `OK`.
`POST /models/check` performs inference per configured role, not just inventory GET.

Installed Hermes also returned `OK` through this gateway, in non-streaming and
streaming mode, using an isolated temporary HERMES_HOME, zero tools and a Python
network guard allowing only local OmniRoute. One streaming callback was observed.
A direct built-in delegate_task call also completed one child with the same
loopback route, zero tools and one iteration. This does not verify automatic LLM
tool selection or arbitrary tool routes, OS isolation, or change the user's persistent Hermes profile. Full app smoke uses temporary SQLite and Python 3.12.

[Live evidence](qa-issue-13-live.json), [inventory projection](contracts/omniroute-live-inventory.json),
[offline QA](qa-issue-13-offline.json). Password reset, real taskflow Director,
Codex/OS sandbox and reboot recovery are separate work. No production DB used.
