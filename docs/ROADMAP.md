# Codex roadmap (each issue = a separate PR)

| Phase | Work | Dependency | Acceptance |
|---|---|---|---|
| 00 | Bootstrap lean v3, clean tests/CI, remove remaining dead code | none | reproducible pytest+smoke, docs match runtime |
| 01 | Inspect installed Zorin Hermes + OmniRouter READ-ONLY | 00 | documented actual transport/auth/model metadata; no secrets in Git |
| 02 | Evaluate OSS components and licence compliance | 00 | ADR: keep Hermes vs integrate selected library; no duplicate director/router |
| 03 | Implement OmniRouter provider adapter (mocked) | 01 | real health/models checks via config; fallback and errors tested |
| 04 | Hermes Director, Analyst and typed task handoffs | 01,03 | role-to-role artifacts and bounded retries; owner checkpoints |
| 05 | Isolated Codex / coding executor | 04 | edits only test worktree, no production access |
| 06 | Deterministic QA and independent Reviewer | 05 | exit-code backed report and PR diff review |
| 07 | GitHub branches, Issues, draft PR and CI integration | 06 | verifiable PR, never auto merge |
| 08 | Cost, quotas, fallback and paid escalation | 03,04 | free-first policy, budget caps, manual ChatGPT browser handoff |
| 09 | MacBook-friendly authenticated dashboard | 04,07 | owner can control tasks and review artifacts securely |
| 10 | Security/hardening/recovery | 05,09 | sandbox, redaction, RBAC, audit logs, backup |
| 11 | E2E warehouse_config staging acceptance | 06,07,10 | safe test task -> draft PR -> explicit approval |
| 12 | Zorin operations/manual and optional Lenovo worker | 11 | runbook, reproducible restore, optional worker |

Do not pull full CrewAI/OpenHands/MetaGPT repo. Research, choose specific interfaces, then incorporate only needed components with licence notices, ideally via dependency rather than copied code.
