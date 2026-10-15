# AICommander 3.0 — реализация и ограничения (15.10.2026)

[English](IMPLEMENTATION.en.md) · [Аудит исходников и CI](AUDIT_2026-10-15.md)

**Подтверждение:** код `main` после [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35); [GitHub Actions — 6/6 success](https://github.com/KalyuzhniyKO/AICommander-v3/actions/runs/38708568156). Это **не** проверка реальной интеграции Zorin/Hermes/Codex.

| Модуль | Реализовано | Предел |
|---|---|---|
| FastAPI/SQLite | Локальные `/tasks`, раунды, ответы, ошибки, простой UI | Нет аутентификации; нельзя открывать в сеть |
| Старые роли | keyword-router, Manager/Architect/Designer/Coder/Reviewer, прямой OpenRouter, fallback | Роли дают текст; внутри одного раунда не передают фактические ответы друг другу |
| Offline taskflow | `/taskflow/*`, MockDirector, Analyst/Architect/Developer, структурированные артефакты, версии, идемпотентность, миграция БД, owner approve/reject | Только mock, без Hermes/моделей/Git/Codex |
| Offline executor | `backend/app/execution/*`: доверенные Git fixtures, worktree, allowlist команд, реальные exit codes/timeout/diff | Библиотека без HTTP/API/taskflow; **не sandbox ОС/сети** |
| CI | Python 3.11–3.13 на Linux/Windows, pytest, compileall, pip check | Нет macOS/Zorin/browser E2E в `main` |

## Не реализовано / не проверено

- Реальный AI-директор Hermes, действующий OmniRouter, inventory подключённых моделей, выбор по стоимости и бюджетные ограничения. **OpenRouterProvider не равен OmniRouter**.
- Реальное исполнение Codex CLI, QA/reviewer и генерация draft PR внутри AICommander.
- Защищённая MacBook-панель, аутентификация `/taskflow/*` и идентификация владельца. `owner_approve` — mock-переход в БД, не разрешение на merge.
- Системная изоляция недоверенного кода, пилот на warehouse_config, деплой/восстановление в production.
- Сквозное подтверждение работающих Hermes/OmniRouter/Zorin. [Аудит Zorin](ZORIN_INTEGRATION.md) частичный и отделяет owner-reported результаты от проверенного по исходникам.

## PR и ветки

- [PR #31](https://github.com/KalyuzhniyKO/AICommander-v3/pull/31) (offline taskflow) и [PR #33](https://github.com/KalyuzhniyKO/AICommander-v3/pull/33) (offline executor) **merged** в текущий `main` через [#35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35). Это не означает завершения реальных интеграционных Issues #14/#15.
- [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) — защищённая панель MacBook **Draft и с конфликтами**, не объединена; её старый зелёный CI не годится для нового `main`.
- Репозиторий переименован в AICommander-v3. v2 сохранён **в `v2-legacy` этого же репозитория**. Новые PR — в `main`.

**Безопасность:** до авторизации не открывать нынешнее приложение по LAN/интернету, не передавать секреты и production DB.
