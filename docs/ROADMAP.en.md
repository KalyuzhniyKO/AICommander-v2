# AICommander 3.0 — dependency-aware roadmap

[Русская версия](ROADMAP.md) · [Verified audit (RU)](AUDIT_2026-10-15.md)

**15 October 2026:** [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35) merged v3 into default **`main`** with [6/6 CI jobs](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156). Repo was renamed AICommander-v3, prior v2 preserved at `v2-legacy`. New PRs target `main`.

- [PR #25](https://github.com/KalyuzhniyKO/AICommander-v3/pull/25) foundation and [PR #26](https://github.com/KalyuzhniyKO/AICommander-v3/pull/26) OSS research merged. #12 remains open for live validation.
- [PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) offline mock taskflow and [PR #33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) offline worktree executor merged; they do **not** complete the actual Hermes/Codex integrations.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) authenticated MacBook UI with offline taskflow is **merged into main**, CI 7/7. Pause duplicate #28.
- [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) Zorin inventory is partial; validate live Hermes → OmniRouter first. Real integration phases remain dependency-gated, while independent offline improvements may run in parallel.
- Suggested Codex model names below are **historical preferences, not verified availability**.

## Historical parent-task plan

| Stage | GitHub issue | Scope | Suggested Codex model | Reasoning effort |
|---|---|---|---|---|
| 00 | [#10](https://github.com/KalyuzhniyKO/AICommander-v3/issues/10) | Проверка основы и CI | GPT-6.1 Sol | Medium |
| 01 | [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) | Проверка Hermes и OmniRouter (read-only) | GPT-6.1 Sol | Medium |
| 02 | [#12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12) | Анализ OSS и лицензий | GPT-6.1 Sol | High |
| 03 | [#13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13) | Адаптер OmniRouter | GPT-6.1 Sol | High |
| 04 | [#14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14) | Директор и межролевой workflow | GPT-6 Astra | High |
| 05 | [#15](https://github.com/KalyuzhniyKO/AICommander-v3/issues/15) | Изолированный Codex executor | GPT-6 Astra | High |
| 06 | [#16](https://github.com/KalyuzhniyKO/AICommander-v3/issues/16) | QA и независимый Reviewer | GPT-6.1 Sol | High |
| 07 | [#17](https://github.com/KalyuzhniyKO/AICommander-v3/issues/17) | GitHub PR и CI | GPT-6.1 Sol | Medium |
| 08 | [#18](https://github.com/KalyuzhniyKO/AICommander-v3/issues/18) | Free-first, лимиты и эскалация | GPT-6.1 Sol | Medium |
| 09 | [#19](https://github.com/KalyuzhniyKO/AICommander-v3/issues/19) | Панель для MacBook | GPT-6.1 Sol | Medium |
| 10 | [#20](https://github.com/KalyuzhniyKO/AICommander-v3/issues/20) | Безопасность и восстановление | GPT-6 Astra | High |
| 11 | [#21](https://github.com/KalyuzhniyKO/AICommander-v3/issues/21) | Сквозной пилот warehouse_config | GPT-6 Astra | High |
| 12 | [#22](https://github.com/KalyuzhniyKO/AICommander-v3/issues/22) | Документация, развёртывание, бэкапы | GPT-6.1 Sol | Medium |
| MIG | [#23](https://github.com/KalyuzhniyKO/AICommander-v3/issues/23) | Repository rename — completed | — | — |

Independent tasks may run in parallel, but real integration stages must respect dependency checks and human merge/deploy approval. The repository rename (#23) is complete; there is no remaining standalone-repo migration.

## Authorized live follow-up (#13)

[PR #41](https://github.com/KalyuzhniyKO/AICommander-v3/pull/41) supersedes earlier
inventory deferral: bounded authorized inventory/text inference, Hermes streaming
and one delegated child route are verified. The app's manual legacy round used
OmniRoute with temporary SQLite. [Evidence](qa-issue-13-live.json). The conservative
no-new-framework ADR is accepted. After this PR is verified/merged, #11/#12/#13
can close; #14 still owns real Director/external effects in taskflow. Reboot
recovery, arbitrary tools and all provider/fallback routes are not claimed.
