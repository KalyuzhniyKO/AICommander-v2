# HTTP and persisted text — offline part of #20

[Русский](SECURITY_BOUNDARY.md)

2026-10-18: bounded application security fixes, tested with synthetic credentials
and temporary SQLite only. No SSH/Zorin/services/production, new dependencies,
credential discovery or OS sandbox. Full #20 remains open.

The shared redactor now handles string JSON keys, nested lists/tuples, key
collisions without dropping values, full Bearer tokens through punctuation,
configured literal credentials and the existing taskflow assignment patterns.
It uses current environment values only, with longer literals masked first.

New Repository free text is masked before SQL: task title/description, project
name, round comment/output/summary/errors/status error and owner decision comment.
Legacy prompt context is masked after assembly, including historical text.
Taskflow uses the shared masker for new goals/reasons/artifact content. Routing
identities, statuses, versions, numeric IDs and idempotency hashes are unchanged.
Project names that collide after masking retain the existing uniqueness conflict.
No migration or historical data rewriting is performed.

HTTP middleware strictly accepts localhost/127.0.0.1/[::1] authorities with an
optional port 1–65535. Userinfo, path/query/fragment and ambiguous duplicate
security headers fail closed before dispatch. Existing security response headers
also cover early 400/401/403/503 denials; Basic challenge remains intact.

Thirty new boundary tests cover the actual regressions and controls. Before the
HTTP fixes, the first 26 tests produced 20 failures; three persistence/context
regressions were subsequently reproduced separately. The focused suite with
existing panel/taskflow/operations/foundation tests passed 107 tests. Full results:
[QA report](qa-issue-20-boundary.json), PR CI.

This is best-effort masking, not arbitrary-secret detection. Unknown, encoded,
fragmented, numeric or rotated credentials may escape matching. Old rows, WAL,
backups and logs are not scrubbed. Routing identifiers/configuration and third
party/system/uvicorn logs are outside this fix. Executor retains its explicit
literal redactor without environment credential discovery. Host validation is
not a network firewall; use the existing loopback listener through SSH. Basic
auth does not encrypt traffic. OS isolation, supply-chain audit and deployment/
reboot/live acceptance remain separate work.


[A separate local dependency audit](DEPENDENCY_AUDIT.en.md) checked 35 Python
distributions: after updating pip, no known findings remain. License metadata
is inventoried; full distribution and Zorin audits are pending.
