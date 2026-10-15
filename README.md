# AICommander 3.0 — виртуальная команда ИИ-разработчиков

[**English version / Английская версия**](README.en.md)

**Статус:** подготовлена минимальная основа (foundation MVP). Полноценная интеграция Hermes, OmniRouter, Codex и QA **ещё не реализована**. Рабочая версия 2 сохранена без изменений: [AICommander-v2](https://github.com/KalyuzhniyKO/AICommander-v2).

## Текущий статус — 15 октября 2026

- [PR #25](https://github.com/KalyuzhniyKO/AICommander-v2/pull/25) **объединён**: исправления foundation, тесты и [успешный CI](https://github.com/KalyuzhniyKO/AICommander-v2/actions/runs/38635577007).
- [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) **объединён**: исследование OSS и ADR-001. [Issue #12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) остаётся открытой до проверки совместимости через #11.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) **открыт как Draft**: панель MacBook предложена, но ещё не включена в `v3-foundation`.
- **Без Zorin:** допускается независимая работа над [#29 — Git worktree](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29) и подготовка [#27 — taskflow](https://github.com/KalyuzhniyKO/AICommander-v2/issues/27). Реализацию #27 согласовать со схемами из PR #30. [#28 — UI](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28) пока не запускать, чтобы не дублировать PR #30. Проверка Hermes/OmniRoute требует ручной загрузки Zorin и завершения #11.

## Что мы создаём

Ты ставишь задачу **с MacBook** и принимаешь результат. На домашнем **Zorin OS** уже установлены Hermes и OmniRouter. AICommander управляет прозрачным процессом разработки, **не дублируя** их собственные функции.

**Цепочка работы:** владелец → директор (Hermes) → аналитик → архитектор (если нужен) → программист (Codex для сложных работ) → автоматические тесты/QA → независимый ревьюер → GitHub Pull Request → твоё подтверждение.

Цель — настоящие изменения в Git-ветке и проверенные тесты, а не пять текстовых советов от разных моделей.

## Что уже перенесено из v2

- локальный FastAPI и минимальный веб-интерфейс;
- задачи, история раундов, результаты ролей в SQLite;
- базовые подсказки ролям и первоначальное распределение по ключевым словам;
- клиент совместимого с OpenRouter API, проверка моделей и резервные модели;
- базовые тесты без реальных API-ключей.

**Пока отсутствует:** подключение существующего Hermes/OmniRouter, отдельные аналитик и QA, исполнение Codex CLI, работа с реальными файлами, безопасная песочница, создание PR, авторизованная панель для MacBook и учёт бюджета. Проверки foundation подтверждены в [отчёте этапа 00](docs/IMPLEMENTATION.md); это не проверка интеграции с Zorin.

**Не переносим из v2:** архивные мосты для macOS, Director/Judge/Final Auditor migration pack, старые планы, пустые обёртки ролей, ненужную интеграцию с отдельным OpenAI API Premium Review. ChatGPT в браузере используется **вручную** для сложных экспертных задач.

## Принципы работы

1. Используем уже настроенные Hermes и OmniRouter, не пишем их аналоги.
2. Бесплатные или дешёвые модели — обычные этапы; сложная реализация — Codex; ChatGPT Web — ручная экспертиза.
3. QA доказывает результат реальными тестами, а ревьюер проверяет Git diff.
4. Production, реальные базы склада и секреты агентам недоступны.
5. Каждая задача Codex — отдельная feature-ветка и PR; **независимые задачи можно выполнять параллельно**. Merge и деплой — только с одобрения владельца.

## Документация

| Документ | Русский | English |
|---|---|---|
| Техническое задание | [PRODUCT_SPEC](docs/PRODUCT_SPEC.md) | [Product spec](docs/PRODUCT_SPEC.en.md) |
| Реализовано и не реализовано | [IMPLEMENTATION](docs/IMPLEMENTATION.md) | [Implementation](docs/IMPLEMENTATION.en.md) |
| Очерёдность работы Codex | [ROADMAP](docs/ROADMAP.md) | [Roadmap](docs/ROADMAP.en.md) |
| Выбор модели и уровня | [MODEL_SELECTION](docs/MODEL_SELECTION.md) | [Model selection](docs/MODEL_SELECTION.en.md) |
| Использование Open Source | [OPEN_SOURCE_REVIEW](docs/OPEN_SOURCE_REVIEW.md) | [Open-source review](docs/OPEN_SOURCE_REVIEW.en.md) |
| Решение по оркестрации (предложение, ожидает #11) | [ADR-001](docs/ADR-001-ORCHESTRATION.md) | [ADR-001 (RU)](docs/ADR-001-ORCHESTRATION.md) |
| Инструкции Codex | [AGENTS.md](AGENTS.md) | [Codex instructions](AGENTS.en.md) |
| Английские версии GitHub Issues | Основные описания — в Issues | [Issues EN](docs/ISSUES_EN.md) |
| Шаблоны GitHub и порядок работы | [WORKFLOW](docs/GITHUB_WORKFLOW.md) | [Workflow](docs/GITHUB_WORKFLOW.en.md) |

## Локальный запуск базовой версии

Python **3.11–3.13**. Команды для Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
cp config/models.example.json config/models.json
python -m compileall backend
python -m pytest -q
python -m backend.app.main
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
Copy-Item config/models.example.json config/models.json
.\.venv\Scripts\python.exe -m compileall backend
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m backend.app.main
```

Тесты используют временные БД и конфигурации, не читают локальный `.env` и блокируют реальные HTTP-вызовы моделей. GitHub Actions выполняет compileall и pytest на Python 3.11–3.13 в Linux и Windows. `MAX_MODEL_RETRIES` задаёт общее число попыток для каждой модели, включая первую; после их исчерпания используется следующая модель. Проверки не требуют API-ключа.

После запуска: `GET /health`, `POST /tasks` с JSON `{"description":"Проверить документацию"}`, `GET /tasks/1`, `GET /models/status`. `POST /models/check` и создание раунда вызывают модели, если ключ настроен; примеры ID нужно заменить перед такими запросами.

Открыть: `http://127.0.0.1:8000`. В конфигурации моделей указаны **заглушки**, их нужно заменить действительными ID. Прототип **без авторизации** — не публикуй его в интернет или домашнюю сеть.

## Где находится v3

Пока это **отдельная ветка** [`v3-foundation`](https://github.com/KalyuzhniyKO/AICommander-v2/tree/v3-foundation) в репозитории v2: подключённый GitHub не может создать новый репозиторий. [Issue переноса #23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23). **`main` v2 не затронут.**

[Этап #10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10) уже выполнен. Открытые и параллельные задачи: [дорожная карта](docs/ROADMAP.md), [Issue #24](https://github.com/KalyuzhniyKO/AICommander-v2/issues/24).
