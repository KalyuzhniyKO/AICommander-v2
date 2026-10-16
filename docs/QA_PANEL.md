# Проверка PR #30: панель и offline taskflow

Дата: **15.10.2026**. Репозиторий AICommander-v3, целевая ветка `main` с объединёнными PR #31 (taskflow) и #33 (executor). Старые 62 теста и CI от 14.10 не используются как доказательство этой интеграции.

Локально: macOS arm64, Python 3.13.12, Playwright 1.64.0 / Chromium. [Полный stdout, exit codes и SHA базы](qa-panel.json), [проверенный снимок панели](qa-panel.png).

| Проверка | Результат | Exit code |
|---|---|---|
| `RUN_UI_TESTS=1 PANEL_SCREENSHOT=docs/qa-panel.png ../AICommander-v2/.venv/bin/python -m pytest -q -rs` | **150 passed, 1 skipped**, 37.58 s | 0 |
| `../AICommander-v2/.venv/bin/python -m compileall -q backend` | Успешно | 0 |
| `../AICommander-v2/.venv/bin/python -m pip check` | No broken requirements found | 0 |
| `node --check frontend/app.js` | Успешно | 0 |

Путь interpreter относится к локальному соседнему checkout; при обычной установке используется `.venv/bin/python`. Единственный skip — существующий `Windows app alias guard`, предназначенный только для Windows; он проверяется в Windows CI. Остаётся одно предупреждение Starlette о переходе с httpx на httpx2. Исходники standalone executor и контракт/машина состояний taskflow не изменены.

## Проверенные сценарии

**Сервер:** все прежние foundation/taskflow/executor тесты; auth и CSRF на каждом `/taskflow/*`; настроенные credentials не отражаются в snapshot и HTTP 422; список задач показывает последний taskflow, сохраняя отдельный legacy-status; startup сохраняет версии/артефакты taskflow. Миграции проверены на трёх схемах: legacy, объединённый taskflow, ранняя панель PR #30. Проверены сохранение проектов/решений/раундов/артефактов, повторный запуск, конкурентный init, foreign_key_check и rollback DDL при ошибке.

**Шесть Chromium-сценариев** на настоящем uvicorn и временной SQLite:

1. Создание проекта/задачи/процесса → три шага с передачей типизированных артефактов → reject → resume без пересоздания → approve. История сохраняется после перезагрузки; ширина 390 px не создаёт горизонтальный скролл. Legacy model endpoints из панели не вызываются.
2. Cancel после первого артефакта → новый процесс → max_steps=1 → blocked. Невозможное продолжение отключено; старый отменённый процесс доступен в истории.
3. Изменение версии другим клиентом → stale_version → перечитывание без повторного шага.
4. Потеря ответа после успешного commit → повтор того же ключа/тела → чтение более нового snapshot, без дублирования артефактов.
5. HTTP 503 после commit → тот же безопасный повтор и актуальный snapshot.
6. Ошибка Mock Director → failed → resume с оставшимся бюджетом; HTML в артефактах не исполняется; состояние сохраняется после перезагрузки.

Снимок desktop интерфейса просмотрен визуально. JS ошибок в сценариях нет. Diff проверен на сохранение существующих taskflow/executor и отсутствие изменений frozen JSON Schema.

## Пределы

Это интеграция панели с **Mock Director**: `done` означает согласованные mock-артефакты. Реальные модели, Hermes/OmniRouter/Codex, исполнение задачи отдельным executor из UI, git diff/QA задач, стоимость, Zorin и SSH/VPN не запускались. Внешняя сеть моделей блокировалась fixture, данные и репозитории тестов — временные. Production, merge и deploy не выполнялись. Новый CI запускается на обновлённом head PR; его результат публикуется в описании PR, без приписывания старого зелёного CI новому коду.

## CI кода интеграции

[GitHub Actions 38715547848](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38715547848), commit `8d68ce4`: **7/7 success** (Python 3.11–3.13 / Linux и Windows, Chromium). Последующее уточнение статуса PR и документации не меняет исходники или тесты. Ссылки на повторный CI итогового head — в описании PR.

## Локальная визуальная приёмка #28

После RU/EN и mock-chat добавлены [четыре реальные Chromium-снимка](UI_PREVIEW.md)
и воспроизводимый тест desktop/mobile без Zorin или моделей. Это локальные
viewport-проверки, не подтверждение на физических устройствах владельца.
[Отдельный QA-отчёт](qa-issue-28-visual.json).
