# OmniRoute: изолированная подготовка адаптера

[English](OMNIROUTE_ADAPTER.en.md) · [Issue #13](https://github.com/KalyuzhniyKO/AICommander-v3/issues/13)

**Статус: offline-подготовка, не завершение интеграции #13.** По запросу владельца
взят следующий этап; реализован отдельный транспорт с synthetic mock-тестами.
Решение не проверять авторизованный inventory сохранено. Модуль не подключён
к FastAPI, панели, legacy-раундам, taskflow или Hermes. Импорт не вызывает сеть.
Настройки приложения и существующий OpenRouterProvider не изменены.

## Подтверждённое и предполагаемое

Основание — [Zorin-аудит](ZORIN_INTEGRATION.md) и [ADR-001](ADR-001-ORCHESTRATION.md).
В установленном OmniRoute 3.8.51 подтверждены исходные пути `/api/health`,
`/v1/models`, `/v1/chat/completions`. Live health вернул HTTP 200, `status=ok`;
models без авторизации вернул 401. **Формат авторизованного inventory и успешного
inference не проверен.** Парсинг `data[].id` и `choices[0].message.content` —
гипотеза OpenAI-compatible JSON, а не снятый контракт установленного сервера.
Все IDs и ответы в `tests/test_omniroute.py` искусственные. Цены, провайдеры,
доступность `auto`, tool calling и streaming не заявляются.

## Интерфейс и настройки

`backend.app.providers.omniroute` содержит `OmniRouteConfig`, `OmniRouteProvider`
и `OmniRouteError`. `health()` возвращает только разрешённое поле status,
`models()` — список уникальных ID (пустой список допустим), `chat()` — ChatResult
без raw-ответа. `chat()` принимает один точный model ID, текстовые сообщения
system/user/assistant и `stream=false`. Модуль не выбирает другую модель или
провайдера при ошибке: маршрутизация остаётся задачей OmniRoute.

Настройки читаются **только из окружения**, без `.env`, CLI contexts, salt-файлов,
пользовательских конфигов, OAuth и БД:

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `OMNIROUTE_ENABLED` | `false` | Только `true` разрешает запросы этого отдельно созданного клиента |
| `OMNIROUTE_BASE_URL` | пусто | Явный service root либо root + `/v1`; обязательна при enabled |
| `OMNIROUTE_API_KEY` | пусто | Bearer credential для models/chat; не пароль Dashboard и не SSH-пароль |
| `OMNIROUTE_TIMEOUT_SECONDS` | `10` | Socket timeout попытки, >0 и ≤60 секунд |
| `OMNIROUTE_MAX_GET_ATTEMPTS` | `2` | Общее число GET-попыток, 1–3 |

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

После отдельного решения владельца о live-проверке и принятия #11/#12:

1. Подтвердить механизм auth и форму models/inference ответов на установленной
   версии, передав credentials через защищённое окружение, без чтения stores
   этим модулем. Корректировать парсер по фактам, а не считать mocks контрактом.
2. В изолированном сеансе явно создать enabled-клиент и выполнить opt-in health/
   models smoke через согласованный endpoint. В отчёт вывести только разрешённые
   поля; этот smoke **не выполнен** в текущей работе.
3. Отдельно разрешить ограниченный inference с реальным model ID и бюджетом.
   Проверить error semantics и решить, нужны ли streaming/tools и адаптация schema.
4. Только затем согласовать factory/config wiring приложения, Hermes transport,
   протокол внешних эффектов и политику retries. Простая подмена MockDirector
   сетевым клиентом внутри SQLite-транзакции запрещена архитектурным ADR.

#11/#12/#13 остаются открытыми. Этот модуль не сбрасывает пароль панели,
не изменяет службы и не предоставляет обход авторизации.
