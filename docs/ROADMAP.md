# Поэтапная разработка AICommander 3.0 через Codex

[English](ROADMAP.en.md) · [Рекомендации по моделям](MODEL_SELECTION.md)

Каждый ограниченный этап — отдельная GitHub Issue, ветка и PR с реальными проверками. **Независимые работы допускается выполнять параллельно**, интеграции выполняются по зависимостям. В текущем коде Hermes/OmniRouter ещё не подключены.

## Фактическое состояние и параллельные работы (15.10.2026)

| Направление | Задача / PR | Состояние |
|---|---|---|
| Основа | [#10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) / [PR #25](https://github.com/KalyuzhniyKO/AICommander-v2/pull/25) | **Готово, CI зелёный** |
| Исследование OSS | [#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) / [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) | Документы объединены; Issue открыта до проверки #11 |
| Zorin-интеграция | [#11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11) → [#13](https://github.com/KalyuzhniyKO/AICommander-v2/issues/13) | Ожидает загрузки Zorin и read-only проверки |
| Backend-логика | [#27](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27) | Контракты и mock-часть можно разрабатывать; учесть PR #30 |
| MacBook UI | [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) / [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28) | PR #30 — **Draft**; #28 приостановить до его оценки |
| Git worktree | [#29](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) | Можно выполнять сейчас без Zorin |

**Рекомендуемая волна сейчас:** ревью PR #30 + отдельная работа #29; исследование контрактов #27 параллельно, реализацию и миграции согласовать после ревью PR #30. Интерфейс #28 не запускать как отдельную дублирующую реализацию.

**Следующая интеграционная волна:** после загрузки Zorin #11 → подтверждение решения ADR #12 → #13 OmniRouter → #14 Hermes → #15 исполнение кода → #16 QA → #17 PR/CI. Дальше #18–#22 по фактическим зависимостям, безопасности и требованиям владельца.



| Шаг | Issue | Что сделать | Рекомендуемая модель Codex | Уровень | Почему |
|---|---|---|---|---|---|
| 00 | [#10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) | Проверка основы и CI | GPT-6.1 Sol | **Medium** | Проверка кода, тестов и небольшой рефакторинг |
| 01 | [#11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11) | Проверка Hermes и OmniRouter (read-only) | GPT-6.1 Sol | **Medium** | Инвентаризация с точной фиксацией интерфейсов |
| 02 | [#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) | Анализ OSS и лицензий | GPT-6.1 Sol | **High** | Сравнение фреймворков и архитектурный ADR |
| 03 | [#13](https://github.com/KalyuzhniyKO/AICommander-v2/issues/13) | Адаптер OmniRouter | GPT-6.1 Sol | **High** | Контракт API, обработка ошибок, мок-тесты |
| 04 | [#14](https://github.com/KalyuzhniyKO/AICommander-v2/issues/14) | Директор и межролевой workflow | GPT-6 Astra | **High** | Сложная архитектура состояний и передач |
| 05 | [#15](https://github.com/KalyuzhniyKO/AICommander-v2/issues/15) | Изолированный Codex executor | GPT-6 Astra | **High** | Инструменты, песочница, права и выполнение кода |
| 06 | [#16](https://github.com/KalyuzhniyKO/AICommander-v2/issues/16) | QA и независимый Reviewer | GPT-6.1 Sol | **High** | Доказуемые тесты и анализ diff |
| 07 | [#17](https://github.com/KalyuzhniyKO/AICommander-v2/issues/17) | GitHub PR и CI | GPT-6.1 Sol | **Medium** | Практическая интеграция API и веток |
| 08 | [#18](https://github.com/KalyuzhniyKO/AICommander-v2/issues/18) | Free-first, лимиты и эскалация | GPT-6.1 Sol | **Medium** | Контроль бюджета, обработка rate limits |
| 09 | [#19](https://github.com/KalyuzhniyKO/AICommander-v2/issues/19) | Панель для MacBook | GPT-6.1 Sol | **Medium** | Web UI и защищённое управление |
| 10 | [#20](https://github.com/KalyuzhniyKO/AICommander-v2/issues/20) | Безопасность и восстановление | GPT-6 Astra | **High** | Security review, изоляция, отрицательные тесты |
| 11 | [#21](https://github.com/KalyuzhniyKO/AICommander-v2/issues/21) | Сквозной пилот warehouse_config | GPT-6 Astra | **High** | Интеграция нескольких систем, валидация |
| 12 | [#22](https://github.com/KalyuzhniyKO/AICommander-v2/issues/22) | Документация, развёртывание, бэкапы | GPT-6.1 Sol | **Medium** | Runbook и проверяемое восстановление |
| MIG | [#23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23) | Перенос в отдельный репозиторий | GPT-6.1 Sol | **Low** | Рутинный перенос только минимальных файлов |

## Очередность
См. таблицу параллельных работ выше: последовательный запуск всех задач больше не является обязательным, но интеграционные блокировки сохраняются.

**Дополнительное действие:** [#23 — перенести v3 в самостоятельный репозиторий](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23) при появлении возможности создать репозиторий. Оно не блокирует работу с `v3-foundation`.

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
