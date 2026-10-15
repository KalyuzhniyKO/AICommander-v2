# AICommander 3.0 — виртуальная команда ИИ-разработчиков

[**English version / Английская версия**](README.en.md)

**Статус на 15.10.2026:** это тестовая основа AICommander 3.0, **не готовая автономная AI-команда**. Подтверждённое состояние и ограничения: [аудит проекта](docs/AUDIT_2026-10-15.md).

- Репозиторий **[AICommander-v3](https://github.com/KalyuzhniyKO/AICommander-v3)** уже переименован.
- [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35) перенёс версию 3 в **основную ветку `main`**; [все шесть CI-проверок](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156) прошли.
- Исходная v2 сохранена **в этом же репозитории** в [`v2-legacy`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/v2-legacy). Ветка `v3-foundation` теперь историческая; новые PR направлять в `main`.
- [PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) (offline taskflow) и [PR #33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) (offline Git worktree executor) объединены. Их части **ещё не интегрированы** с Hermes/OmniRouter/Codex.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) (защищённый интерфейс MacBook) остаётся **Draft, конфликтует с актуальным `main`, не объединён**.

## Что мы создаём

Ты ставишь задачу **с MacBook** и принимаешь результат. На домашнем **Zorin OS** уже установлены Hermes и OmniRouter. AICommander управляет прозрачным процессом разработки, **не дублируя** их собственные функции.

**Цепочка работы:** владелец → директор (Hermes) → аналитик → архитектор (если нужен) → программист (Codex для сложных работ) → автоматические тесты/QA → независимый ревьюер → GitHub Pull Request → твоё подтверждение.

Цель — настоящие изменения в Git-ветке и проверенные тесты, а не пять текстовых советов от разных моделей.

## Что реализовано в `main`

- FastAPI, SQLite, простой локальный веб-интерфейс, текстовые роли и раунды, fallback и **прямой OpenRouter** (не установленный OmniRouter).
- **Отдельный offline taskflow:** `/taskflow/*`, MockDirector, аналитик → архитектор → разработчик, типизированные артефакты, состояния, идемпотентность и owner approve/reject. **Нет реальных вызовов Hermes, моделей, Git/QA.**
- **OfflineExecutor:** библиотека для доверенных одноразовых репозиториев, worktree, утверждённые команды, diff и exit code. **Не подключён к API/UI и не является OS/network sandbox.**
- Шесть успешных проверок GitHub Actions для Python 3.11–3.13 на Linux/Windows; это **не** тестирование на Zorin, macOS и с живыми моделями.

**Пока отсутствует:** работающий Hermes → OmniRouter, Codex CLI executor, QA/Reviewer, автоматические GitHub PR, защищённый MacBook UI и контроль бюджета. Все текущие endpoints, включая `owner-decision`, **не требуют аутентификации**; не открывайте сервер в LAN или интернет. `owner_approve` — только mock-статус БД, а не разрешение на реальный merge/deploy.

**Не переносили из v2:** устаревшие мосты macOS, Director/Judge/Final Auditor migration pack, старые планы и отдельную интеграцию OpenAI API Premium Review. ChatGPT Web — ручной экспертный этап.

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

## Текущая организация работы

Разработка ведётся в [`main`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/main); для новых изменений используем feature-ветки и PR в `main`. Старое состояние сохранено в [`v2-legacy`](https://github.com/KalyuzhniyKO/AICommander-v3/tree/v2-legacy). [GitHub workflow](docs/GITHUB_WORKFLOW.md) и [дорожная карта](docs/ROADMAP.md) описывают зависимости. [Аудит](docs/AUDIT_2026-10-15.md) отделяет реализованное от планируемого.
