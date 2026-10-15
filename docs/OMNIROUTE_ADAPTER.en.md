# OmniRoute offline transport preparation

[Full Russian documentation](OMNIROUTE_ADAPTER.md) · [Issue #13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13)

This is a disabled-by-default, isolated transport scaffold with synthetic tests,
not completed live integration. The owner's choice to leave authenticated inventory
unverified is preserved. No FastAPI/panel/taskflow/Hermes or legacy provider wiring
was changed; import performs no network request or credential discovery.

Source-confirmed paths are `/api/health`, `/v1/models`, `/v1/chat/completions`.
Observed live results are health 200/ok and unauthenticated models 401.
Authenticated `data[].id` inventory and `choices[0].message.content` parsing are
OpenAI-compatible hypotheses, not captured server contracts. All test IDs are synthetic.

Explicit env settings: `OMNIROUTE_ENABLED=false`, empty `OMNIROUTE_BASE_URL` and
`OMNIROUTE_API_KEY`, `OMNIROUTE_TIMEOUT_SECONDS=10` (>0, ≤60),
`OMNIROUTE_MAX_GET_ATTEMPTS=2` (1–3 total). The key is an inference credential,
not the Dashboard or SSH password. No .env/context/salt/credential-store access.
Root and `/v1` URLs normalize without duplicate paths; HTTP is loopback-only,
HTTPS supports an explicitly configured host. Credentials in URLs, query/fragment,
redirects and ambient proxies are rejected/disabled. Health sends no key.

GET retries transport errors, timeout and 429/500/502/503/504 within the budget.
Retry-After accepts seconds or HTTP-date and caps waiting at 2 seconds.
POST is never automatically retried; there is no model/provider fallback loop.
OmniRoute remains responsible for model routing. Only non-streaming text chat is
supported. A socket timeout is not a strict total deadline; Event cancellation
checks before/after I/O and interrupts retry waits, not active server inference.
Responses are capped at 1 MiB; invalid schemas and empty chat fail safely.

Errors expose static categories/numeric metadata only, no response bodies, headers,
URLs, prompts or chained transport text. Responses/errors close; raw JSON is not
returned and the exact configured credential is masked if echoed in chat.
This does not detect arbitrary secrets in user content.

Run `python -m pytest tests/test_omniroute.py -q` offline. Tests fake the entire
transport; no Zorin connection, authenticated inventory or inference occurred.
[QA evidence](qa-issue-13-offline.json). Live health/models smoke and inference
require separately authorized execution after #11/#12 acceptance; no automatic
integration tests or production wiring are provided. #13 remains open.
