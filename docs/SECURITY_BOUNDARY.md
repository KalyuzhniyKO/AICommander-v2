# HTTP и текстовые данные — offline-часть #20

[English](SECURITY_BOUNDARY.en.md)

18.10.2026: проверка и исправления без SSH, Zorin, Hermes/OmniRoute, production,
реальных ключей и новых зависимостей. Это ограниченная проверка прикладной границы,
не полный security audit, OS sandbox или завершение #20.

## Воспроизведённые проблемы и исправления

1. HTTP JSON redaction не обрабатывал имена свойств и tuple values. В частности,
   422 для неожиданного JSON-поля мог вернуть искусственный credential в `input`.
   Теперь общий `backend.app.redaction.redact()` обрабатывает строковые ключи и
   вложенные dict/list/tuple. При совпадении имён после маскирования значения не
   теряются: неизменённые ключи сохраняются, изменённому добавляется `_2`, `_3` и т.д.
2. Bearer-regex обрезал токен на `~`, `!`, `%` и других символах, оставляя хвост.
   Теперь маскируется вся непрерывная последовательность до whitespace/quote.
   Маскирование `sk-…` и taskflow assignment-patterns сохранено.
3. Маскирование JSON-ответа не защищало новые тексты в SQLite и legacy prompt
   context. Теперь Repository маскирует free text до SQL: название/описание
   задачи, название проекта, комментарий раунда, output, summary, error,
   last_error и комментарий решения владельца. Контекст legacy-раунда также
   маскируется после сборки, включая текст из старых rows. Taskflow использует
   тот же masker для целей, причин и текстов новых артефактов/операций.
4. Разбор Host как общего URL допускал userinfo/path/query/fragment и неверный
   порт рядом с localhost. Теперь принимается только authority `localhost`,
   `127.0.0.1` или `[::1]` с необязательным числовым портом 1–65535.
   Дубли Host/Authorization/Origin/X-AICommander-Request отклоняются до dispatch.
5. Ранние 400/401/403/503 не получали заголовки защиты. Теперь no-store, CSP,
   nosniff, no-referrer и frame DENY применяются и к этим отказам middleware.
   Basic challenge сохранён, неверный запрос не создаёт задачу.

Известные литералы берутся только из текущих `OPENROUTER_API_KEY`,
`OMNIROUTE_API_KEY`, `PANEL_PASSWORD` в окружении. Файлы, keychain, credential
stores и `.env` redactor не ищет и не читает. Длинный литерал маскируется до
короткого перекрывающего. Код executor продолжает использовать собственный явный
список redaction literals; его правило не читать credentials из окружения сохранено.

Идентификаторы/статусы/числа/версии/SQL keys и routing model/provider IDs не
переписываются в Repository. Нет миграции, новой таблицы или замены idempotency
hashes. Наименования проектов после маскирования могут совпасть: существующий
unique constraint вернёт conflict вместо создания второго неоднозначного имени.

## Проверки

`tests/test_security_boundary.py`: 30 новых негативных и контрольных сценариев.
Первые 26 тестов до исправления дали 20 failures/6 passed. После исправления HTTP
отдельно воспроизведены три проблемы persistence/context/taskflow; затем исправлены.
Все данные синтетические; временная SQLite проверяется напрямую, а не через
уже маскирующий HTTP-ответ. Историческая строка намеренно остаётся прежней,
но новый goal/reason/operation/artifact не получает известный литерал.

Проверены валидные localhost/IPv4/IPv6 authorities, invalid ports/URL components,
дубли security headers, отсутствие mutation после отказа, security headers на
отказах, 422 key leak, сохранность colliding JSON values, нестандартные Bearer
символы, tuple values, сохранение lifecycle и routing IDs.

Целевой набор security + существующие panel/taskflow/operations/foundation:
107 passed. Полный прогон и CI зафиксированы в PR и
[машинном отчёте](qa-issue-20-boundary.json).

## Оставшиеся границы

- Это best-effort masking, не универсальная DLP. Неизвестные/закодированные,
  разбитые на части, числовые или уже отозванные credentials могут не совпасть.
  Текущие credentials нельзя передавать коду, тестам или моделям.
- Старые SQLite rows, WAL, snapshots/backups и старые журналы автоматически не
  переписываются. Смена текущего окружения не стирает исторические секреты;
  отчёты/backup по-прежнему приватны. Нет гарантии secure deletion.
- Routing identifiers/configuration и сторонние/system/uvicorn logs не являются
  новой защищённой границей этой части. Проверка лицензий/supply chain отдельно.
- Заголовок Host не доказывает адрес TCP-клиента и не является firewall.
  Поддерживается прежний loopback listener + авторизованный SSH tunnel.
  Не публиковать backend в LAN/интернет; Basic не шифрует соединение.
- Настоящие OS/filesystem/network isolation, права процесса, доверенный Reviewer,
  deployment/reboot acceptance и live-проверка сервисов остаются #15/#20/#22.
  Retry/recovery/budget политики этим PR не меняются.
