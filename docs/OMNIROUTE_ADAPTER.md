# OmniRoute: изолированная подготовка адаптера

[English](OMNIROUTE_ADAPTER.en.md) · [Issue #13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13)

**Статус: текстовый адаптер проверен на живом OmniRoute; включение явное.**
После offline-подготовки владелец разрешил live-проверки, push и merge готовой
работы. Авторизованные management/inference GET, реальный chat и отдельный
Hermes custom backend теперь проверены. Значения credentials не публикуются.
По умолчанию модуль по-прежнему выключен; никаких запросов при импорте/старте.

В приложении добавлен явный provider prefix `omniroute/` для ручных legacy-раундов,
повтора роли и `POST /models/check`. Taskflow остаётся **Mock Director**:
этот PR не подключает Hermes-директора к `/taskflow/*` и не выполняет код.
Настройки служб Zorin и текущий профиль Hermes не менялись.

## Подтверждённое и предполагаемое

Основание — [Zorin-аудит](ZORIN_INTEGRATION.md) и [ADR-001](ADR-001-ORCHESTRATION.md).
В установленном OmniRoute 3.8.51 подтверждены исходные пути `/api/health`,
`/v1/models`, `/v1/chat/completions`. Live health вернул HTTP 200, `status=ok`;
models без авторизации вернул 401. Повторный авторизованный live smoke подтвердил `object/data` и `data[].id`,
а успешный chat — `choices[0].message.content` (строка). Отдельный metadata GET
`/api/models` имеет **другую** форму `models[]`; он не используется этим inference
адаптером. Проверен реальный ID `gemini/gemini-2.5-flash-lite`. Это результат
конкретной версии/конфигурации, не гарантия всех провайдеров и будущих версий.
Все IDs и ответы в `tests/test_omniroute.py` искусственные. Цены и доступность `auto` не выводятся из названия модели. Streaming проверен
отдельно через установленный Hermes, но этот текстовый адаптер SSE не реализует.
Штатный delegate_task проверен прямым вызовом: один child completed с тем же
loopback маршрутом, нулём tools и одной итерацией. Автоматический выбор tool
моделью и произвольные инструменты не проверялись.

## Интерфейс и настройки

`backend.app.providers.omniroute` содержит `OmniRouteConfig`, `OmniRouteProvider`
и `OmniRouteError`. `health()` возвращает только разрешённое поле status,
`models()` — список уникальных ID (пустой список допустим), `chat()` — ChatResult
без raw-ответа. `chat()` принимает один точный model ID, текстовые сообщения
system/user/assistant и `stream=false`. Модуль не выбирает другую модель или
провайдера при ошибке: маршрутизация остаётся задачей OmniRoute.

`OmniRouteConfig.from_env()` читает **только окружение**. Приложение сохраняет
существующий механизм загрузки серверного `.env`, который наполняет окружение;
сам адаптер не читает `.env`, CLI contexts/salt, OAuth или БД. Для разового smoke
окружение задаётся отдельно, без пользовательских конфигов.

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OMNIROUTE_ENABLED` | `false` | Только `true` разрешает запросы этого отдельно созданного клиента |
| `OMNIROUTE_BASE_URL` | пусто | Явный service root либо root + `/v1`; обязательна при enabled |
| `OMNIROUTE_API_KEY` | пусто | Bearer credential для models/chat; не пароль Dashboard и не SSH-пароль |
| `OMNIROUTE_TIMEOUT_SECONDS` | `10` | Socket timeout попытки, >0 и ≤60 секунд |
| `OMNIROUTE_MAX_GET_ATTEMPTS` | `2` | Общее число GET-попыток, 1–3 |
| `OMNIROUTE_MAX_OUTPUT_TOKENS` | `256` | Передаётся как max_tokens, 1–8192; smoke использует 64 |

HTTPS допускается для явно настроенного хоста; HTTP — только loopback
(`localhost`, loopback IPv4/IPv6), например SSH tunnel. URL с credentials,
query, fragment, произвольным path или дублированным `/v1` отклоняются.
Service root и `/v1/` нормализуются без `/v1/v1`. Ambient proxy отключён,
redirects не следуются: Bearer не пересылается на другой адрес. `health()`
не отправляет Bearer даже при настроенном ключе.

## Ошибки, повторы и отмена

- 401 → `auth_required`, 403 → `forbidden`, 402 → `quota_or_tokens`,
  429 → `rate_limited`; статус доступен отдельно в `status_code`.
- GET повторяет только transport/timeout и 429/500/502/503/504 в пределах
  заданного числа попыток. `Retry-After` (секунды или HTTP-date) ограничен
  **2 секундами ожидания**; при отсутствии/невалидном значении backoff 0.25/0.5 с.
- **POST не повторяется**, в том числе при timeout/429/5xx: неизвестно,
  исполнил ли сервер inference. Нет прямого fallback на OpenRouter или другого
  полного retry loop поверх OmniRoute. На ошибке вызывающая сторона принимает
  решение отдельно, а не повторяет этап автоматически.
- Timeout ограничивает socket operations, не является строгим общим дедлайном
  на весь response/все GET-попытки. Ответ ограничен 1 MiB; плохой JSON, неверная
  форма и пустой chat не превращаются в успешный результат.
- Необязательный `threading.Event` проверяется перед попыткой, после чтения и
  между retries; ожидание backoff прерывается. Уже блокирующий I/O остаётся
  ограниченным socket timeout. Отмена не означает отмену inference на сервере.
- Исключения содержат только статическую категорию и числовые метаданные;
  bodies/headers/URL/prompt и текст transport exceptions не включаются.
  Ошибки и responses закрываются. Raw JSON не возвращается; точное значение
  настроенного ключа маскируется в успешном chat. Это не универсальная DLP:
  произвольные другие секреты в пользовательском тексте не распознаются.

## Проверка и оставшийся этап

Offline: `python -m pytest tests/test_omniroute.py -q`. Fake transport проверяет
точные URL/методы, заголовки, closure, 401/403/quota/429/5xx, Retry-After, timeout,
отмену, запрет redirects/proxy, лимит тела и отсутствие секретов в traceback.
Тесты не соединяются с Zorin и не используют настоящий credential.
Полная регрессия и exit codes: [qa-issue-13-offline.json](qa-issue-13-offline.json).

## Явное включение и live smoke

Задать `OMNIROUTE_ENABLED=true`, проверенный base URL и inference-ключ в защищённом
окружении сервера. В `config/models.json` — одна цель на роль, например:

```json
{"manager":["omniroute/gemini/gemini-2.5-flash-lite"],"reviewer":["omniroute/gemini/gemini-2.5-flash-lite"]}
```

Внешний prefix `omniroute/` выбирает транспорт AICommander, оставшийся ID
передаётся OmniRoute **без изменений**. Две цели или смесь OmniRoute/OpenRouter
для одной роли запрещены; fallback оставлен установленному router. Ошибка
OmniRoute не запускает запасной прямой провайдер и не повторяется orchestration
loop, даже если `MAX_MODEL_RETRIES` больше 1. Разные роли могут отдельно
использовать legacy OpenRouter, если это явно указано в их конфигурации.
`POST /models/check` — **inference для каждой роли**, а не бесплатный GET inventory.
Существующая авторизация панели и CSRF обязательны, новые публичные API не добавлены.

Отдельный запуск из workspace (не при старте приложения):

```bash
OMNIROUTE_RUN_LIVE_SMOKE=true python -m backend.app.providers.omniroute_smoke
```

Это health + авторизованный models GET. Для отдельно разрешённого inference:

```bash
OMNIROUTE_RUN_LIVE_SMOKE=true OMNIROUTE_SMOKE_INFERENCE=true OMNIROUTE_SMOKE_MODEL=gemini/gemini-2.5-flash-lite python -m backend.app.providers.omniroute_smoke
```

CLI использует одну GET-попытку, timeout 45 секунд и max_tokens 64; печатает
только безопасные сводки, без ключа/URL/ответа модели. Отсутствие opt-in → exit 2,
ошибка → exit 1, успешная проверка → exit 0. Малый max_tokens может целиком уйти
на reasoning: первый опыт с лимитом 8 дал пустой content. Такой ответ правильно
отклоняется адаптером; повтор с лимитом 64 дал `OK`, 37 total tokens.

## Фактические live-проверки — 15.10.2026

- Management API: 7 подключений, 67 записей каталога. Это **не** 67 успешно
  проверенных моделей. Активные provider types — antigravity, codex и gemini;
  alias каталога для Codex — `cx`, не `codex`.
- Management CLI token не является inference credential: `/api/providers` и
  `/api/models` приняли его, `/v1/models` вернул 401. Для inference использовались
  созданные штатным API **временные** ключи, ограниченные одним model ID,
  сроком 10 минут и дневным лимитом 0.02–0.05 USD. Все отозваны после тестов.
  Отсутствие утечек не означает нулевую стоимость inference.
- Адаптер и smoke CLI: health ok, models 200, выбранный ID присутствует,
  chat 200 с непустым content/`OK`; raw-ответ не возвращается.
- Установленный Hermes 0.21.5+5343.ga3b56ca: custom backend, тот же маршрут,
  отдельный временный HERMES_HOME, tools выключены, ответы `OK` в non-streaming
  и streaming режиме (получен callback). Python network guard разрешал только
  loopback OmniRoute; попытки фонового внешнего соединения блокировались.
  Это проверка данного процесса, не OS sandbox или проверка всех возможных tools.
- Full application smoke использует отдельную временную SQLite и изолированный
  Python 3.12 venv на Zorin. Результат указан в JSON live-отчёте ниже.

Артефакты: [live QA](qa-issue-13-live.json),
[проекция inventory](contracts/omniroute-live-inventory.json).
Пользовательские чаты, production БД и текущая конфигурация Hermes не использовались.
Временные ключи отозваны, тестовые профили/venv/SQLite удалены.

Осталось для следующих этапов: настоящий Hermes Director и внешние эффекты в
#14, автоматические решения о tools/делегировании и сложные маршруты детей, sandbox/Codex, восстановление
после reboot. Это не результат текстового smoke и не повод подменить MockDirector
сетевым вызовом внутри SQLite-транзакции. Пароль Dashboard этим PR не сбрасывается.
