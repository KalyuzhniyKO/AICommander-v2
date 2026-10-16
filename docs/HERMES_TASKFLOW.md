# Hermes Director: реальное планирование, контракт v2

[English](HERMES_TASKFLOW.en.md) · [Issue #14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14)

Установленный на Zorin Hermes выполняет встроенный `delegate_task` для каждой
роли через OmniRoute. AICommander сохраняет состояния и типизированные результаты
в существующем taskflow и журнале операций. Второго agent loop или маршрутизатора
нет. Обычная цепочка — Analyst → Developer → Reviewer; `include_architect=true`
добавляет Architect между аналитиком и программистом. Выбор делает вызывающий
клиент при создании процесса, а не скрытая эвристика сложности.

**Это планирование:** Developer возвращает шаги реализации, Reviewer проверяет
этот план. Код, shell, Codex CLI, тесты и Git diff ещё не выполняются; это #15/#16.
`done` означает только согласование владельцем артефактов планирования:
`schema_version=2.0`, `director=hermes`, `simulated=false`,
`completion_scope=real_planning_artifacts_only`, `code_executed=false`,
`qa_verified=false`. Поле review.scope равно `planning_only`.

Контракт v1 и текущая веб-панель сохраняют Mock Director и `simulated=true`.
Панель пока показывает только mock-процессы; интеграция real-процессов с UI — #19.
Общие `/health` connectivity-флаги остаются консервативными и не выполняют проб.
Настроенность real transport смотрят в защищённом v2 capabilities; это не live health.

## Настройка на сервере

По умолчанию транспорт выключен. Приложение запускается на том же POSIX-хосте,
где установлен доверенный Hermes. Укажите в серверном окружении:

| Переменная | Значение |
|---|---|
| `HERMES_ENABLED` | `true` |
| `HERMES_PYTHON` | Абсолютный путь к существующему Python установленного Hermes |
| `HERMES_SOURCE` | Абсолютный путь к установленному исходному дереву Hermes |
| `HERMES_EXPECTED_COMMIT` | 40 символов commit из проверенного install-stamp |
| `HERMES_MODEL` | Один точный OmniRoute model ID, без префикса `omniroute/` |
| `HERMES_TIMEOUT_SECONDS` | Общий бюджет процесса, 1–120, по умолчанию 90 секунд |
| `HERMES_MAX_OUTPUT_TOKENS` | 64–2048, по умолчанию 768 |

Также нужны `OMNIROUTE_ENABLED=true`, разрешённый `OMNIROUTE_BASE_URL` и
`OMNIROUTE_API_KEY` из [настройки адаптера](OMNIROUTE_ADAPTER.md).
Создание процесса и capabilities не вызывают модель. Отсутствующая конфигурация
даёт 503 на create. Конфигурация маршрута/SDK привязывается к run; её изменение
блокирует новый step этого run. Уже сохранённый result_ready можно зафиксировать
без доступного Hermes. Ключ не входит в binding и может быть ротирован оператором.

Bridge использует существующее PM-окружение Hermes; bootstrap/update/install не
запускаются. Install-stamp сверяется перед dispatch. Это проверка метаданных
доверенной установки, а не криптографическая аттестация всего дерева исходников.
Python 3.11–3.13 используется приложением; Python Hermes может отличаться.
Windows поддерживает mock и контракты, но local Hermes bridge требует POSIX.

## API и передача артефактов

Все маршруты защищены существующими Basic auth, Host и CSRF-проверками.
Создайте задачу через `/tasks`, затем:

```text
GET  /taskflow/v2/capabilities
POST /taskflow/v2/tasks/{task_id}/runs
     {"idempotency_key":"create-1","max_steps":4,"include_architect":true}
GET  /taskflow/v2/tasks/{task_id}/runs
GET  /taskflow/v2/runs/{run_id}
POST /taskflow/v2/runs/{run_id}/commands
     {"idempotency_key":"start-1","expected_version":1,"action":"start"}
POST /taskflow/v2/runs/{run_id}/commands
     {"idempotency_key":"step-1","expected_version":2,"action":"step"}
GET  /taskflow/v2/runs/{run_id}/operations
POST /taskflow/v2/runs/{run_id}/owner-decision
     {"idempotency_key":"approve-1","expected_version":6,"decision":"approve"}
```

Каждый step — один синхронный вызов роли; актуальную версию берите из ответа.
Нет автоматического фонового продолжения. Поддерживаются существующие команды
block/resume/fail/cancel. Лимит считает попытки, в том числе известные ошибки.
Нельзя обойти лимит через resume. Реальный run нельзя прочитать через v1 и наоборот.

Модель получает goal и полное содержимое всех предыдущих артефактов. На границе
HTTP bridge проверяет наличие точного контекста, model ID, отсутствие tools и
JSON Schema роли в запросе. Программист получает требования и опциональный дизайн;
ревьюер — предыдущие артефакты и план. Модель выдаёт только новые поля своей роли.
Backend валидирует JSON и оборачивает его неизменёнными предыдущими типизированными
артефактами. Неверная форма не превращается в успешный результат.

Каждый real-артефакт хранит provenance: operation ID, запрошенный model ID,
SDK commit, parent/child session IDs, SHA-256 отправленного контекста,
`tools_count=0`, `inference_requests=1`. Это метаданные bridge, не заявление модели
и не доказательство конкретной модели за внутренним маршрутом OmniRoute.
[Schema](contracts/taskflow-v2.schema.json) · [Requests](contracts/taskflow-v2.requests.json).

## Отмена, повторы и восстановление

Используется тот же [журнал операций](OPERATIONS.md): резервирование → внешний
вызов вне SQLite-транзакции → durable result → короткая фиксация с fencing/version.
Повтор завершённого ключа возвращает сохранённый ответ; result_ready после rollback
или нового процесса фиксируется без нового inference.

Bridge ограничивает ввод/вывод, время и process group. Ключ передаётся через stdin,
не argv/окружение/файл; профиль Hermes временный, память и trajectory выключены,
SDK stdout/stderr не публикуются. Разрешены только настроенный gateway и маршруты
models/chat-completions. SDK/client retry, fallback и повторный POST заблокированы.
Используется JSON Schema в request overrides и output contract в контексте;
автоматическая correction turn Hermes не включается.

Отмена во время процесса завершает process group, поздний ответ discarded.
Она не возвращает уже потраченную стоимость. Timeout/обрыв после старта bridge
считается `unknown`, пока нет подтверждённого завершения; HTTP 409 не запускает
модель повторно. Полностью полученный, но невалидный ответ фиксируется как failed.
После падения приложения running не перезапускается автоматически.

После внешнего подтверждения остановки прежнего worker доверенный оператор может
вызвать `StepOperations(flow).mark_unknown(id)`, затем `resolve_unknown(id)` для
фиксации неудачной попытки. Произвольный импорт real-result запрещён: нет протокола
независимой проверки provenance. Recovery mutations не доступны по HTTP.
Процессная группа и сетевые проверки не являются песочницей ОС; доверенный SDK
и его зависимости исполняются с правами пользователя. Не передавайте секреты
через тексты задач; redaction остаётся best-effort.

## SQLite и проверка

Миграция 3 сохраняет mock-записи, artifact IDs и result_ready операций из версии 2,
добавляет mode/binding/provenance и reviewer. Перестройка FK-таблиц атомарна;
ошибка откатывается. Старый код не поддерживает real-записи и новую схему:
перед возвратом старого кода остановите workers и восстановите совместимую копию
БД. Автоматического downgrade нет.

[Live QA](qa-issue-14-live.json) отделяет реальные пробы Zorin от fixture-тестов.
Используются только синтетические задачи, временные SQLite/профили и ограниченные
временные ключи с удалением в finally. Постоянная установка Hermes, рабочая БД,
пользовательские чаты и пароль dashboard не изменяются.


## Текущая граница live-приёмки

В пробах 16.10.2026 короткая цепочка из трёх ролей завершилась с owner approval;
цепочка из четырёх ролей дошла до awaiting_owner, после чего проверочный скрипт
ошибся при повторном открытии БД. Ошибка скрипта исправлена. Более поздние пробы
подтвердили отмену реального процесса, unknown при timeout и отсутствие повторной
отправки, но полный итоговый прогон заблокирован квотами: Gemini сообщает
rate_limit, другой маршрут Antigravity вернул 429/quota после успешного аналитика.
Даже прямой запрос к первому маршруту без Hermes получил ReadTimeout при общем
health=ok. Эти ограничения не устраняются изменением lifecycle.

**#14 остаётся открытой** до повторного полного live-прогона текущего кода после
восстановления квот: обе цепочки, owner approval, reopen/replay и max_steps.
Финальные изменения обработки ошибок cancellation probe и privacy-флаги обоих
агентов проверены fixture-тестами; повторного inference после обнаружения quota
не выполнялось. Не объявлять эти последние изменения полностью принятыми live.
Транспорт по умолчанию выключен; постоянного развёртывания приложения не было.
