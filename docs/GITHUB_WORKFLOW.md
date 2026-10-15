# GitHub-процесс AICommander 3.0

[English](GITHUB_WORKFLOW.en.md) · [Дорожная карта](ROADMAP.md) · [Аудит](AUDIT_2026-10-15.md)

## Ветки и репозиторий

- [AICommander-v3](https://github.com/KalyuzhniyKO/AICommander-v3), **основная ветка `main`**: актуальная v3 после [PR #35](https://github.com/KalyuzhniyKO/AICommander-v3/pull/35).
- **`v2-legacy`**: резерв исходной v2 в этом же репозитории.
- **`v3-foundation`**: историческая ветка интеграции. **Новые PR открывать в `main`**.
- Переименование [#23](https://github.com/KalyuzhniyKO/AICommander-v3/issues/23) выполнено, создавать второй репозиторий не нужно.

## Процесс

1. Создать Issue на русском с английской версией по ссылке, критериями приёмки, зависимостями и границами доступа.
2. Проверить существующие PR. [PR #30](https://github.com/KalyuzhniyKO/AICommander-v3/pull/30) — **объединённая панель с offline taskflow**, поэтому [#28](https://github.com/KalyuzhniyKO/AICommander-v3/issues/28) не делать отдельно как дублирующую UI-реализацию.
3. Открывать отдельные feature-ветки и PR в `main`. Независимые работы допускается выполнять параллельно; общие API/SQLite миграции согласовывать и тестировать после объединения.
4. Указывать фактически выполненные тесты и CI, изменённые файлы, риски, ограничения, отсутствие live Zorin/Hermes. **Не считать старые зелёные проверки доказательством готовности при изменившейся базе**.
5. Перед merge проверить diff, фактическое `mergeable`, актуальный head SHA и все проверки; по безопасности — закрытые endpoints, CSRF, миграции и отсутствие секретов.
6. Merge и deploy — только с разрешения владельца. **Mock owner approve в taskflow не является разрешением на Git merge/deploy.**

Шаблоны [bug report](../.github/ISSUE_TEMPLATE/bug_report.md), [feature request](../.github/ISSUE_TEMPLATE/feature_request.md), [Codex task](../.github/ISSUE_TEMPLATE/codex_task.md) и [PR](../.github/pull_request_template.md) теперь находятся в основной `main`, поэтому доступны GitHub. Подключённый к ChatGPT GitHub может помогать с review/docs/PR **без Codex**, но это не означает, что само приложение AICommander умеет автоматически управлять GitHub.

**Безопасность:** публичные Issues/PR не должны содержать production DB, credentials, домашние IP, SSH-конфигурации или данные пользователей.
