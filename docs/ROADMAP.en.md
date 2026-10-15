# AICommander 3.0 — Dependency-aware parallel Codex plan

[Русская версия](ROADMAP.md)

## Current status and parallel work (15 October 2026)

| Area | Task / PR | Status |
|---|---|---|
| Foundation | [#10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) / [PR #25](https://github.com/KalyuzhniyKO/AICommander-v2/pull/25) | **Done, green CI** |
| OSS research | [#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) / [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) | Documents merged; Issue remains open pending #11 |
| Live Zorin integration | [#11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11) → [#13](https://github.com/KalyuzhniyKO/AICommander-v2/issues/13) | Owner boots Zorin; read-only inventory first |
| Backend taskflow | [#27](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27) | Mock/contract design can proceed; coordinate with PR #30 |
| MacBook UI | [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) / [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28) | PR #30 is a **Draft**; pause duplicate #28 until review |
| Test worktree | [#29](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) | Can proceed now, no Zorin required |

**Start now:** review PR #30, implement #29 in a separate branch, design #27 schema with care about PR #30. **Do not start #28 as duplicate frontend implementation.**

**Later:** boot Zorin → #11 verifies contracts → finalize #12 ADR → #13 OmniRouter → #14 Hermes → #15 execution → #16 QA → #17 PR/CI, then #18–#22 with security gates.


| Stage | GitHub issue | Scope | Suggested Codex model | Reasoning effort |
|---|---|---|---|---|
| 00 | [#10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) | Проверка основы и CI | GPT-6.1 Sol | Medium |
| 01 | [#11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11) | Проверка Hermes и OmniRouter (read-only) | GPT-6.1 Sol | Medium |
| 02 | [#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) | Анализ OSS и лицензий | GPT-6.1 Sol | High |
| 03 | [#13](https://github.com/KalyuzhniyKO/AICommander-v2/issues/13) | Адаптер OmniRouter | GPT-6.1 Sol | High |
| 04 | [#14](https://github.com/KalyuzhniyKO/AICommander-v2/issues/14) | Директор и межролевой workflow | GPT-6 Astra | High |
| 05 | [#15](https://github.com/KalyuzhniyKO/AICommander-v2/issues/15) | Изолированный Codex executor | GPT-6 Astra | High |
| 06 | [#16](https://github.com/KalyuzhniyKO/AICommander-v2/issues/16) | QA и независимый Reviewer | GPT-6.1 Sol | High |
| 07 | [#17](https://github.com/KalyuzhniyKO/AICommander-v2/issues/17) | GitHub PR и CI | GPT-6.1 Sol | Medium |
| 08 | [#18](https://github.com/KalyuzhniyKO/AICommander-v2/issues/18) | Free-first, лимиты и эскалация | GPT-6.1 Sol | Medium |
| 09 | [#19](https://github.com/KalyuzhniyKO/AICommander-v2/issues/19) | Панель для MacBook | GPT-6.1 Sol | Medium |
| 10 | [#20](https://github.com/KalyuzhniyKO/AICommander-v2/issues/20) | Безопасность и восстановление | GPT-6 Astra | High |
| 11 | [#21](https://github.com/KalyuzhniyKO/AICommander-v2/issues/21) | Сквозной пилот warehouse_config | GPT-6 Astra | High |
| 12 | [#22](https://github.com/KalyuzhniyKO/AICommander-v2/issues/22) | Документация, развёртывание, бэкапы | GPT-6.1 Sol | Medium |
| MIG | [#23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23) | Перенос в отдельный репозиторий | GPT-6.1 Sol | Low |

Independent work may run in parallel in separate branches, but actual integrations remain dependency-gated; do not proceed to a blocked step without the prerequisite review. #23 is an optional repo migration when a dedicated repository can be created. Never push to production or merge without human approval. Actual models depend on Codex availability; record substitutions.
