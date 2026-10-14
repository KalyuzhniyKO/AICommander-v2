# AICommander 3.0 — Sequential Codex plan

[Русская версия](ROADMAP.md)

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

Run stages #10→#11→#12→#13→#14→#15→#16→#17→#18→#19→#20→#21→#22 in order. Each is a separate feature branch and PR; do not proceed to the next before verifying the previous result. #23 is an optional repo migration when a dedicated repository can be created. Never push to production or merge without human approval. Actual models depend on Codex availability; record substitutions.
