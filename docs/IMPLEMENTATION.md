# AICommander v3 — что уже реализовано и чего ещё нет (15.10.2026)

[English](IMPLEMENTATION.en.md)

## Перенесено из v2

Минимальный FastAPI API на localhost, веб-интерфейс, SQLite с задачами/раундами/ответами и ошибками моделей; простые роли и маршрутизация по ключевым словам; OpenRouter-compatible транспорт, fallback и проверка доступности моделей; тестовый каркас без живых API-ключей.

## Не реализовано

- **Hermes** ещё не подключён как реальный AI-директор.
- **OmniRouter** уже установлен на Zorin, но его рабочий контракт в этом репозитории не изучен и не подключён.
- Нет отдельного аналитика и настоящего тестировщика; старый `coder` генерирует текст, а не исполняет код.
- В offline taskflow роли передают типизированные артефакты; legacy-раунды по-прежнему работают отдельно без такой передачи.
- Offline `git worktree` executor объединён в PR #33 как отдельная библиотека. Он не подключён к taskflow/UI и не является изоляцией ОС. Реальные Codex CLI, QA/Reviewer и создание PR внутри AICommander ещё не подключены.
- Панель защищена HTTP Basic, CSRF, проверкой Host и redaction. Поддерживается localhost через SSH tunnel. Сквозная интеграция панели с Zorin executor ещё отсутствует.
- ID моделей — шаблоны, а не подтверждённые доступные модели.

## Что не переносили

Устаревшие мосты macOS, legacy pipeline Director/Judge/Final Auditor, пустые обёртки и старые планы, отдельную интеграцию OpenAI API Premium Review. ChatGPT Web остаётся ручным этапом.

## Исследование и PR на проверке

- [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) объединён: исследование OSS и ADR-001 готовы, но #12 открыта до проверки #11 на Zorin.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) — панель MacBook на проверке. В этой feature-ветке панель интегрирована с taskflow; в `main` появится после проверки и merge PR.
- [#27](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27) и [#29](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) — независимая подготовка без Zorin; [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28) пересекается с PR #30.

## Проверка этапа 00
[Issue #10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10): исправлен импорт удалённого legacy bridge, закрываются SQLite-соединения API и HTTPError, повторный запуск роли обновляет сводку. 40 тестов проверяют API, ресурсы, конфигурацию и ограниченные попытки fallback без живых API. Добавлена матрица GitHub Actions Python 3.11–3.13 на Linux/Windows.

Реальные локальные результаты с exit codes: [Python 3.13](qa-foundation-python-3.13.14.json), [Python 3.12](qa-foundation-python-3.12.10.json). В обоих окружениях `compileall`, `pytest` и `pip check` завершились с кодом 0, HTTP smoke отдельного uvicorn-процесса прошёл на временной SQLite БД. В pytest остаётся предупреждение зависимости Starlette о переходе с httpx на httpx2. Локально Python 3.11 не установлен; его результат нужно проверять в GitHub Actions.

## Интеграция панели и taskflow (PR #30)

Панель использует существующие `/taskflow/*`: проекты/задачи, история процессов, этапы Analyst/Architect/Developer, типизированные артефакты, timeline, start/step/block/resume/cancel и owner approve/reject. Команды используют idempotency и expected_version; конфликт требует нового снимка и явного решения, потеря ответа допускает повтор того же запроса. После replay читается актуальная версия. Legacy API сохранён и защищён той же авторизацией, его раунды показываются отдельно.

SQLite-миграции согласованы с уже объединённым taskflow и непустыми legacy/ранними panel-БД. Mock Director не выполняет внешний код и не вызывает модели; done означает согласованный mock-план. Git diff/QA задач/затраты и реальные Zorin-интеграции пока отсутствуют в панели. [Инструкции](MACBOOK_PANEL.md), [реальные проверки](QA_PANEL.md).
