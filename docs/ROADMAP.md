# AICommander 3.0 — дорожная карта

[English](ROADMAP.en.md) · [Аудит](AUDIT_2026-10-15.md)

## Фактическое состояние на 15.10.2026

- Репозиторий переименован в **AICommander-v3**; [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35) перенёс v3 в основную ветку **`main`** после [6/6 успешных тестов CI](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156); v2 сохранена в `v2-legacy`. Новые PR направлять в `main`.
- [#10 / PR #25](https://github.com/KalyuzhniyKO/AICommander-v3/pull/25) — foundation и [#12 / PR #26](https://github.com/KalyuzhniyKO/AICommander-v3/pull/26) — OSS research/ADR merged; #12 открыта до реальной проверки совместимости.
- [#27 / PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) — **offline taskflow готов в main**. [#29 / PR #33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) — **offline worktree executor готов в main**; родительские #14/#15 этим не завершены.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) — защищённая MacBook-панель с offline taskflow **объединена в main**, CI 7/7. [#28](https://github.com/KalyuzhniyKO/AICommander-v3/issues/28) не запускать параллельно как дубль.
- [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) — **частичный** Zorin-аудит; runtime-инвентаризация моделей и фактический Hermes → OmniRouter inference ещё не выполнены.
- **Далее:** верификация #11 → #13 OmniRouter → #14 Hermes → #15–#17 реальный Codex/QA/PR → #18–#20 бюджет, панель, безопасность → #21–#22 пилот и установка. Независимые задачи можно делать параллельно с отдельными PR.
- **Рекомендованные модели в таблице ниже — исторические ориентиры, доступность конкретных названий/уровней в текущем Codex не подтверждена.**

## План интеграционных этапов

| Шаг | Issue | Что сделать | Рекомендуемая модель Codex | Уровень | Почему |
|---|---|---|---|---|---|
| 00 | [#10](https://github.com/KalyuzhniyKO/AICommander-v3/issues/10) | Проверка основы и CI | GPT-6.1 Sol | **Medium** | Проверка кода, тестов и небольшой рефакторинг |
| 01 | [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) | Проверка Hermes и OmniRouter (read-only) | GPT-6.1 Sol | **Medium** | Инвентаризация с точной фиксацией интерфейсов |
| 02 | [#12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12) | Анализ OSS и лицензий | GPT-6.1 Sol | **High** | Сравнение фреймворков и архитектурный ADR |
| 03 | [#13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13) | Адаптер OmniRouter | GPT-6.1 Sol | **High** | Контракт API, обработка ошибок, мок-тесты |
| 04 | [#14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14) | Директор и межролевой workflow | GPT-6 Astra | **High** | Сложная архитектура состояний и передач |
| 05 | [#15](https://github.com/KalyuzhniyKO/AICommander-v3/issues/15) | Изолированный Codex executor | GPT-6 Astra | **High** | Инструменты, песочница, права и выполнение кода |
| 06 | [#16](https://github.com/KalyuzhniyKO/AICommander-v3/issues/16) | QA и независимый Reviewer | GPT-6.1 Sol | **High** | Доказуемые тесты и анализ diff |
| 07 | [#17](https://github.com/KalyuzhniyKO/AICommander-v3/issues/17) | GitHub PR и CI | GPT-6.1 Sol | **Medium** | Практическая интеграция API и веток |
| 08 | [#18](https://github.com/KalyuzhniyKO/AICommander-v3/issues/18) | Free-first, лимиты и эскалация | GPT-6.1 Sol | **Medium** | Контроль бюджета, обработка rate limits |
| 09 | [#19](https://github.com/KalyuzhniyKO/AICommander-v3/issues/19) | Панель для MacBook | GPT-6.1 Sol | **Medium** | Web UI и защищённое управление |
| 10 | [#20](https://github.com/KalyuzhniyKO/AICommander-v3/issues/20) | Безопасность и восстановление | GPT-6 Astra | **High** | Security review, изоляция, отрицательные тесты |
| 11 | [#21](https://github.com/KalyuzhniyKO/AICommander-v3/issues/21) | Сквозной пилот warehouse_config | GPT-6 Astra | **High** | Интеграция нескольких систем, валидация |
| 12 | [#22](https://github.com/KalyuzhniyKO/AICommander-v3/issues/22) | Документация, развёртывание, бэкапы | GPT-6.1 Sol | **Medium** | Runbook и проверяемое восстановление |
| MIG | [#23](https://github.com/KalyuzhniyKO/AICommander-v3/issues/23) | Переименование репозитория — выполнено | — | — | `main` = v3, `v2-legacy` = резерв v2 |

## Очередность
Актуальный порядок приведён выше. Независимые этапы можно выполнять параллельно, но реальные интеграции — только после выполнения зависимостей и проверки. Создавать отдельный репозиторий v3 больше не нужно.

## Зависимости и критерии
- #10 проверяет фактический запуск и тесты foundation.
- #11 фиксирует реальные API/CLI интерфейсы Hermes/OmniRouter без выдачи секретов.
- #12 выбирает OSS компоненты и указывает авторов/лицензии.
- #13 подключает OmniRouter только через проверенный контракт.
- #14 создаёт директора и структурированные передачи задач.
- #15 включает изменения реальных файлов в изолированном worktree.
- #16 доказывает качество реальными тестами и независимым ревью.
- #17 добавляет draft PR и CI, без auto-merge.
- #18 вводит бюджет и экономичную маршрутизацию.
- #19 делает панель для MacBook с авторизацией.
- #20 проверяет безопасность, секреты и восстановление.
- #21 проводит тестовый пилот на `warehouse_config` без production.
- #22 завершает документацию Zorin и восстановление.

**Модели — рекомендации, не гарантия доступности в интерфейсе Codex.** Если недоступна указанная модель, выбрать ближайшую доступную по назначению и уровню, указав замену в PR. Затраты на вызовы моделей AI-команды через OmniRouter — отдельный вопрос от выбора модели исполнителя **Codex для разработки проекта**.
