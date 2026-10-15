# Zorin integration audit — English summary

[Full Russian report](ZORIN_INTEGRATION.md) · [Issue #11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11)

Initial read-only audit followed by explicitly authorized live probes on 2026-10-15.
**Connection inventory and minimal runtime paths for #11 are now verified.**
This is not a claim of a complete AI team, OS sandbox or reboot recovery.

### Authorized live follow-up

Management API confirmed 7 connections, 67 catalog records and 6 configured
combos. Active provider types include antigravity/codex/gemini; the Codex catalog
alias is `cx`. Catalog entries and stored active status are not successful tests
of every model/provider or of automatic fallback. Management CLI auth accepted
management GETs but not inference `/v1/models` (401).

Temporary inference Bearer keys scoped to `gemini/gemini-2.5-flash-lite`, expiring
in 10 minutes with 0.02–0.05 USD daily caps, validated `data[].id` inventory (200)
and nonempty Chat Completions `OK`. The adapter, opt-in smoke CLI and isolated
application legacy round succeeded; the round produced 2 completed OmniRoute
role outputs in temporary Python 3.12/SQLite. All temporary keys were revoked.
No credentials left Zorin or appeared in public artifacts.

Installed Hermes also returned `OK` in text and streaming modes from a temporary
HERMES_HOME with tools disabled. A direct call to its built-in `delegate_task`
completed one child: parent/child used the same custom model and loopback gateway,
zero tools and one iteration. This tests the mechanism, not LLM selection of the
tool. A Python audit guard blocked external connects; this is not an OS sandbox.
Existing PM-selected dependencies were explicitly selected for the isolated home;
user chats/config and installed Hermes source/dependencies were not changed.

The earlier choice to skip inventory was superseded by the owner's live-check
request for these bounded probes. Dashboard password and persistent services were
not changed. Reboot recovery, arbitrary tools and all provider/fallback routes
remain later-stage work. [Live evidence](qa-issue-13-live.json),
[inventory projection](contracts/omniroute-live-inventory.json),
[transport documentation](OMNIROUTE_ADAPTER.en.md).

The following sections describe historical observations and limitations **before**
the authorized live follow-up; they do not override the results above.

### Codex SSH follow-up — 2026-10-15

The follow-up supersedes the initial bus/socket limitations **for the current SSH
session**. An existing SSH alias worked with BatchMode and strict saved-host-key
checking; no password or known_hosts change was needed. This verifies the saved
key, not a new independent fingerprint attestation. Private connection details
are omitted.

- Zorin OS 18.1 confirmed. OmniRoute **user** unit is loaded/active/running/enabled
  with a nonzero PID; the system unit is absent. Both named Hermes units are
  absent, which does not rule out CLI or other launch mechanisms.
- Loopback health GETs returned 200 (`ok`, `healthy`); both model-list GETs returned
  401 without credentials. MacBook LAN probes independently returned health 200
  and models 401. One listener binds all interfaces; Internet exposure is unknown.
- Installed OmniRoute is 3.8.51. Its service uses the launcher Node v24.20.0;
  the noninteractive shell resolves Node v20.20.0, below the package requirement.
  Hermes/OmniRoute launchers exist but are outside that shell's PATH. Missing
  CLI commands in PATH do not prove that packages are absent.
- Hermes install stamp and four source hashes match the first audit. CLI custom
  Chat Completions, resume and delegation source contracts remain confirmed,
  but no bootstrap or model execution was performed.
- The owner explicitly chose to leave **authenticated inventory unverified**.
  No credential store, token salt, private config, database or chat was opened.
  Source inspection shows the official CLI token helper may create a salt file;
  it was not executed. No inference, login, service/configuration change occurred.
- Issue #11 stays open; authenticated inventory and a separately authorized
  Hermes-to-OmniRoute runtime check remain outstanding. This does not authorize #13.

[Sanitized observations](contracts/zorin-live-probes.json) are an allowlist projection,
not full response fixtures or an inventory schema. [Follow-up QA](qa-issue-11-live.json).
The statements below about no SSH and denied sockets describe the **first** audit.

### Initial owner observations (historical; follow-up above retests selected probes)

On 2026-10-15 the owner ran restricted read-only probes directly in the ordinary Zorin terminal and on a MacBook connected to the same home LAN. These findings were **reported by the owner** in PR discussion; private IP addresses, credentials and configurations were not shared:

- Zorin: `omniroute.service` reported `loaded`, `active`, `running`, `enabled`, with a nonzero `MainPID`. This does not prove restart/recovery after reboot.
- Zorin: local `GET /api/health` and `/api/monitoring/health` returned **HTTP 200**. The response bodies were not examined.
- Zorin: unauthenticated `GET /v1/models` and `/api/v1/models` returned **HTTP 401**. This is not evidence that no models are configured.
- Zorin: TCP 20128 was bound to **ALL_INTERFACES**, not just loopback.
- MacBook on home LAN: TCP connect succeeded; `GET /api/health` returned **200** and unauthenticated `GET /v1/models` returned **401**.

The service was reachable from the MacBook **within the LAN**; public Internet reachability, firewall/NAT, TLS, authenticated model/provider inventory, Hermes-to-OmniRoute inference, fallback and restart behaviour remain unknown. Do not send Dashboard passwords or API keys over unencrypted LAN HTTP. Consider loopback bind plus a secure SSH tunnel or narrow firewall rules **only after verifying the supported configuration method and separately authorizing changes**.


- Confirmed locally: Zorin OS 18.1; Linux 7.0.0-38-generic; Hermes install stamp
  `0.21.5+5343.ga3b56ca`, revision `a3b56cac95488242856b6fb1f121842a38c3e391`;
  OmniRoute package `3.8.51`; Node `24.20.0`, npm `11.19.0`, system Python `3.12.3`,
  Hermes launcher Python `3.14.7`, systemd `255`.
- OmniRoute user unit, wants symlink and user linger entry exist. They establish
  a possible boot mechanism by themselves; subsequent owner-reported runtime checks
  confirmed that the user unit was active/running at the time tested. No Hermes unit
  was found in the inspected locations; other launch mechanisms remain possible.
- Source contracts: Hermes custom Chat Completions backend and built-in
  `delegate_task`; OmniRoute `/v1/models`, `/v1/chat/completions`, CLI health paths
  `/api/health` and `/api/monitoring/health`. Default `localhost:20128` comes from
  installed source; a later owner-reported probe did receive HTTP 200 on port 20128. CLI may access credentials or
  fall back to SQLite, so it was not used for inventory.
- System and user systemd bus access failed with exit 1 (`Operation not permitted`).
  Socket creation failed with errno 1. These steps stopped without escalation;
  service availability cannot be inferred from this restricted process view alone;
  see independent owner-reported checks above.
- Configured providers/models, effective Hermes SDK versions, current auth,
  fallback, delegation routing and reboot recovery remain unverified.
  Live health status codes were observed by the owner, not by sandbox Codex.
  Historical Hermes 0.21.0 / OmniRoute 3.8.50 and OAuth login are historical only.
- Decision ZORIN-001: retain the existing router and Hermes delegation as integration
  candidates. Do not start #13 integration until runtime evidence is reviewed.
  First validate mocks; any real inference or configuration change needs separate
  authorization. No services, credentials, private configs or databases were modified
  or opened; no inference, install, sudo, SSH, merge or deployment occurred.
- No captured fixtures are claimed. Local pytest failed with exit 1 because pytest
  is absent. See [QA evidence](qa-issue-11.json). Merging this partial documentation
  does not close #11 or authorize integration #13.
