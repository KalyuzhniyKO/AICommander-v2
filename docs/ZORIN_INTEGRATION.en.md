# Zorin integration audit — English summary

[Full Russian report](ZORIN_INTEGRATION.md) · [Issue #11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11)

Read-only audit, 2026-10-15. **Partial evidence; Issue #11 runtime acceptance criteria remain unmet.**

### Additional observations supplied by the owner (not retested by Codex)

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
