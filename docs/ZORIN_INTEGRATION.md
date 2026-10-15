# Zorin: read-only аудит Hermes и OmniRoute

[English summary](ZORIN_INTEGRATION.en.md) · [Issue #11](https://github.com/KalyuzhniyKO/AICommander-v2/issues/11)

Дата: 15.10.2026. **Аудит частичный: runtime-критерии Issue #11 не выполнены.**
Установленные исходники дают основу для проектирования #13, но запуск интеграции
остаётся заблокирован до проверки служб, авторизации и доступного inventory.

## Дополнительные runtime-проверки владельца (вне sandbox Codex)

После ограниченного аудита владелец самостоятельно выполнил read-only проверки
**15.10.2026** в обычном терминале Zorin и с MacBook в той же домашней LAN.
Ниже — **сообщённые владельцем результаты**, не результаты исполнения Codex.
Приватный IP, ключи и содержимое конфигурации не публикуются.

| Проверка владельца | Результат / предел подтверждения |
|---|---|
| Zorin: `systemctl --user show omniroute.service` с ограниченными полями | `LoadState=loaded`, `ActiveState=active`, `SubState=running`, `UnitFileState=enabled`; `MainPID` ненулевой. Это подтверждает состояние службы на момент выполнения, **не** перезапуск после reboot. |
| Zorin: `GET /api/health` и `GET /api/monitoring/health` | Оба **HTTP 200** на локальном OmniRoute. Содержимое ответов не анализировалось. |
| Zorin: `GET /v1/models`, `GET /api/v1/models` без credentials | Оба **HTTP 401**. Требование авторизации не означает отсутствия доступных моделей. |
| Zorin: `ss` для TCP 20128 | `ALL_INTERFACES`: сервис слушает не только loopback. |
| MacBook → Zorin по домашней LAN, TCP 20128 | TCP connect **succeeded**; `GET /api/health` → **200**, `GET /v1/models` без credentials → **401**. |

**Вывод:** работоспособность user-службы OmniRoute и доступность её HTTP endpoint
с MacBook внутри LAN подтверждены **со слов владельца**. Доступность из интернета,
firewall/NAT, TLS, доступность Hermes, provider/model inventory с авторизацией,
фактический Hermes → OmniRoute inference, fallback и восстановление после reboot
**не проверены**. `ALL_INTERFACES` вместе с доступностью по LAN — повод для
security review, но не доказательство интернет-экспозиции.

**Мера предосторожности:** до настройки защищённого канала не вводить пароль
Dashboard или API-ключ в незашифрованный HTTP по LAN. Рекомендуем рассмотреть
loopback bind + SSH-туннель с MacBook либо ограничение сетевого доступа firewall,
**только после проверки реально поддерживаемого способа настройки и отдельного
разрешения владельца на изменение конфигурации**.

## Границы и достоверность

Владелец подтвердил локальную загрузку Zorin на dual-boot ПК Windows/Zorin.
`/etc/os-release` независимо показывает Zorin OS 18.1, Ubuntu noble;
`uname -sr` — Linux 7.0.0-38-generic. Смена SSH host key при загрузке другой ОС
не означает замену устройства. SSH в этом аудите не использовался, fingerprints
не проверялись и не публикуются.

Сессия выполняет команды через ограниченное окружение: обе проверки systemd
завершились `Failed to connect to bus: Operation not permitted`, exit 1;
создание обычного socket завершилось `PermissionError`, errno 1.
Эти шаги остановлены без повышения прав. Это ограничение инструмента,
**не свидетельство остановки служб или неисправности Zorin**.
Наблюдаемый `/proc` содержит только подходящий процесс `python3`; отсутствие
Hermes/Node в этой выборке не доказывает их отсутствия на хосте.

Прочитаны только правила проекта, публичные описания GitHub, исходники пакетов,
launcher-файлы и выбранные несекретные поля unit. Не читались приватные `.env`,
OAuth/credential stores, пользовательские конфиги Hermes, чаты, журналы,
OmniRoute runtime DB и production DB. Ни службы, ни настройки не изменялись.
LLM-запросов, входа в аккаунты, установки пакетов, sudo и SSH не было.

## Подтверждено сейчас

| Объект | Наблюдение | Источник / предел вывода |
|---|---|---|
| Hermes | `0.21.5+5343.ga3b56ca`, base `0.21.5` | `install-stamp.json`, не версия запущенного процесса |
| Hermes revision | `a3b56cac95488242856b6fb1f121842a38c3e391`, stamp `dirty=false` | Самоописание установки; независимая проверка чистоты дерева не выполнялась |
| OmniRoute | `3.8.51` | `package.json` и путь launcher; runtime не проверен |
| Node / npm | `v24.20.0` / `11.19.0` | Фактические `node --version`, `npm --version`, exit 0 |
| Python системы | `3.12.3` | `python3 --version`, exit 0 |
| Python launcher Hermes | `3.14.7` | Прямой запуск указанного launcher интерпретатора с `-I -B`, без bootstrap Hermes |
| systemd | `255 (255.4-1ubuntu8.18)` | `systemctl --version`; manager недоступен |
| Требования OmniRoute | Node `>=22.22.2 <23 || >=24.0.0 <27` | `package.json`; обнаруженный Node удовлетворяет диапазону |
| Требования Hermes | Python `>=3.11,<3.15` | `pyproject.toml`; базовая версия проекта `0.0.0` здесь placeholder, не версия релиза |
| OmniRoute autostart | user unit `omniroute.service`, ссылка в `default.target.wants` | Файловая проверка; manager state не проверен |
| User lingering | Запись текущего пользователя в `/var/lib/systemd/linger` существует | Файловый признак, не подтверждение работающего user manager |

Версии SDK в эффективном окружении Hermes **не установлены**. Прямое чтение
`importlib.metadata` базовым Python 3.14.7 не нашло `openai` и завершилось exit 1;
это не доказывает поломку Hermes: launcher импортирует bootstrap, который может
подключать отдельное окружение. Bootstrap не запускался, чтобы исключить
инициализацию, загрузку зависимостей и изменения вне workspace. Наличие pinned
зависимостей в pyproject не выдаётся за доказательство установленных версий.

## Реальные способы запуска и автозапуск

Локальный `hermes` — shell wrapper в пользовательском bin, вызывающий
`<HERMES_SOURCE>/.hermes/bin/hermes`. Второй wrapper запускает отдельный Python
3.14.7, затем `hermes_bootstrap` и `hermes_cli.main.main`. Простое выполнение
`hermes --version` не использовалось: `main.py` передаёт `check_updates=True`.

Локальный `omniroute` — wrapper, вызывающий Node 24.20.0 и
`<OMNIROUTE_PACKAGE>/bin/omniroute.mjs`. README установленного пакета описывает
запуск `omniroute` как gateway + Dashboard. Эта команда **не выполнялась**.

В найденном user unit OmniRoute подтверждены:

```ini
After=network-online.target graphical-session.target
Type=notify
Restart=on-failure
WantedBy=default.target
```

ExecStart использует отдельный Node 24.20.0; полный argv и Environment не
публикуются. Ссылка в wants и lingering делают запуск user manager после загрузки
принципиально возможным. Они не доказывают успешный старт: нужны доступный manager,
зависимости unit, корректная readiness-нотификация и проверка после реальной
перезагрузки владельцем. `After=` задаёт порядок и само по себе не подтягивает target.

В проверенных именах `/etc/systemd/system`, `/usr/lib/systemd/system`,
`~/.config/systemd/user` и `~/.config/autostart` Hermes unit/desktop entry не найден.
Другие имена unit, transient units, system-wide autostart, cron и другие supervisors
не исключены. Автозапуск Hermes не подтверждён.

Парсер Hermes поддерживает `chat --resume SESSION_ID|latest`, `--continue` и
`--no-restore-cwd`; это контракт возобновления сессии, а не доказательство
автоматического продолжения задачи после reboot. Сессии не открывались.
Для AICommander ещё нужны persistence этапов, reconciliation с незавершённым QA/PR
и защита от повторных действий. В рамках #11 ничего из этого не включено.

## Контракты установленной версии

Пути ниже относительны корням исходников установок. Это безопасные ориентиры;
домашние абсолютные пути и сетевые адреса хоста в публичный отчёт не включены.

| Компонент | Подтверждённый контракт | Локальное основание |
|---|---|---|
| Hermes CLI | `chat --provider NAME --model MODEL`, `--format text|stream-json`, `--resume` | `hermes_cli/_parser.py:248–274`; команды не исполнялись |
| Hermes custom backend | `model.provider=custom`, `model.base_url`, выбор `api_mode`; обычный custom по умолчанию `chat_completions` | `hermes_cli/runtime_provider.py:183`, `runtime_provider_backends.py:116` |
| Endpoint precedence | explicit > `CUSTOM_BASE_URL` > доверенный `model.base_url` > `OPENROUTER_BASE_URL` > default | `runtime_provider_backends.py`, `_resolve_openrouter_runtime`; есть дополнительные условия доверия/provider matching |
| Именованные custom providers | `providers:` и legacy `custom_providers:`, `key_env`, `api_mode` | `runtime_provider_custom.py`; не содержимое пользовательского config |
| Делегирование | Встроенный `delegate_task`; дочерняя модель наследуется либо задаётся `delegation.provider` / `delegation.model` | `tools/delegate_tool.py`; фактическая доступность tool в сессии не проверена |
| OmniRoute base URL | Явный override, `OMNIROUTE_BASE_URL`, active context, затем `http://localhost:20128` (порт может переопределяться) | `bin/cli/api.mjs:getBaseUrl` |
| OmniRoute inference | `GET /v1/models`, `POST /v1/chat/completions`; клиентская base URL с `/v1` | Установленный `README.md:220,1024,1032`, rewrites в `dist/server.js` |
| Models CLI/API | `GET /api/v1/models`; management `GET /api/models`; provider models `GET /api/v1/providers/{provider}/models` | `bin/cli/api-commands/models.mjs` |
| Health CLI/API | `omniroute health [--json] [--verbose]`, `GET /api/monitoring/health`; предварительная проверка `GET /api/health` | `bin/cli/commands/health.mjs`, `bin/cli/api.mjs:isServerUp` |
| Авторизация OmniRoute CLI | Bearer token + локальный machine-derived CLI token; active contexts могут хранить отдельный scoped access token | `bin/cli/api.mjs:buildHeaders`; credentials не читались |

`http://localhost:20128` — документированный default; позднее владелец подтвердил живые HTTP-ответы OmniRoute на локальном порту 20128 и с MacBook по LAN (см. дополнительный раздел выше).
Ограниченное окружение Codex само ответов сервера не получило. В `isServerUp` любой HTTP <500 считается признаком доступности,
поэтому даже успешное выполнение этой функции не доказывает healthy состояние.
Не добавлять придуманные `/health` или `/healthz` в адаптер.

Hermes имеет web backend (`hermes_cli/web_server.py`), auth gate и ссылку в коде
на public `/api/status`. Привязка, активный сервер, полный HTTP-контракт и
авторизация не подтверждены. Не использовать этот комментарий как проверенное
API директора. Для #14 отдельно выбрать и проверить CLI/HTTP transport.

Не запускались OmniRoute `providers list`, `models`, `status`, `health`: CLI может
читать contexts/credentials, добавлять локальный credential, а часть команд через
`withRuntime` переходит к SQLite fallback. Нельзя считать любой CLI GET чистым
чтением без анализа его полного пути выполнения.

## Провайдеры, модели и Hermes → OmniRoute

Настроенные provider IDs, model IDs, combos, auto/fallback и пригодность credentials
**не проверены**. Статический каталог и README не являются inventory установки.
Исторический вход в openai-codex также не подтверждает текущую авторизацию.

Принципиальная совместимость есть на уровне исходников: custom OpenAI-compatible
backend Hermes может адресовать Chat Completions OmniRoute. Рабочая цепочка,
tool calling, streaming и маршрутизация дочерних агентов не доказаны.

**Decision record ZORIN-001:** использовать существующий OmniRoute как кандидата
для inference transport #13 и встроенное делегирование Hermes для #14. Второй
router/director и новые orchestration frameworks не добавлять. ADR-001 остаётся
предложением до runtime-проверки; этот аудит его не утверждает.

Перед реализацией #13 необходимы следующие проверки в разрешённой среде:

1. Владелец предоставляет доступный read-only канал к system/user manager;
   получить только `LoadState`, `ActiveState`, `SubState`, `UnitFileState`, `MainPID`
   для обнаруженных unit, без `systemctl status`/journal и без Environment/argv.
2. Установить фактический bind/port и изоляцию сети без публикации адресов.
   Проверить документированные health GET без credentials, cookies и redirects;
   записать только HTTP status и allowlist полей. При отказе прав остановиться.
3. Через отдельно одобренный механизм авторизации получить только provider ID,
   model ID, enabled/state; не читать хранилища целиком. Различать inference key,
   management token и локальный CLI token. Не передавать ключ в argv/URL.
4. Проверить model inventory и правила стоимости; `auto` не гарантирует бесплатный
   маршрут. До отдельного разрешения не делать inference даже для «free» модели.
5. В #13 сначала использовать mock transport: точный `/v1` path без дублирования,
   timeout, 401/403, 429/Retry-After, 5xx, пустой каталог, SSE и отмена. Ответы ошибок
   и headers должны очищаться от секретов. Ограничить retries и бюджет.
6. После отдельного разрешения на конфигурацию и LLM-запрос проверить ограниченный
   Hermes → OmniRoute вызов, tool-call и stream. Для delegation проверить маршрут
   каждого ребёнка, отсутствие обхода proxy и непредусмотренного direct fallback.
7. После отдельного согласования reboot проверить start/readiness и восстановление
   сессий/задач без повторного изменения файлов или создания PR.

При запрете systemd/socket следующие шаги не обходятся через sudo, SSH, иной
network namespace или изменение firewall. Требуется решение владельца о новом
разрешённом канале проверки. Реализация #13 в этом аудите не начата.

## Известно исторически

Источник — полное описание Issue #11 и сводка владельца, не повторное наблюдение:
OmniRoute 3.8.50 запускался через systemd с Dashboard; `/v1/*` требовали ключ;
Hermes 0.21.0 был установлен, openai-codex сообщал logged in;
Hermes Desktop использовался с Mac через SSH. Dual boot объясняет разные SSH keys.
Эти сведения не подтверждают текущие службы, credentials или рабочую интеграцию.

## Не удалось проверить

- Ограниченный sandbox Codex не смог самостоятельно получить ActiveState/PID и live health из-за запрета bus/socket; эти результаты отдельно сообщил владелец (см. выше).
- Текущие provider/model inventory, auth и auto/fallback — секретные хранилища
  исключены, безопасный авторизованный HTTP-канал недоступен.
- Эффективные SDK Hermes, работоспособность CLI/web/delegation — bootstrap не запускался.
- Успешный Hermes → OmniRoute запрос — нет отдельного разрешения на inference.
- Доступность OmniRoute по домашней LAN и bind на все интерфейсы подтверждены владельцем; доступ извне LAN, firewall/NAT, TLS, Dashboard auth и SSH host key не проверялись.
- Автоматический startup после boot и resume задачи — reboot/перенастройка запрещены.

## Воспроизводимость и QA

Исходники не копировались; fixtures не добавлены: без ответа живого сервера они
не были бы снятым контрактом. Будущие synthetic mocks должны явно отличаться
от capture установленного сервера. Ниже SHA-256 выбранных прочитанных источников;
они фиксируют локальные артефакты, но не доказывают поведение процесса.

| Источник | SHA-256 |
|---|---|
| Hermes `hermes_cli/_parser.py` | `80326cbf3558f22150c8c0fe11daf8997153ee89174a7e1d5f8a2a12bd808b0b` |
| Hermes `hermes_cli/runtime_provider.py` | `6fa7cf555a6924fabac01212fdc38a88d1bae951b6a3a7be2ee85b9418020dda` |
| Hermes `tools/delegate_tool.py` | `91df0e5c338fa2212f7aac8ff96aaf7d7406b644185ad75129b3ee5ae3d25fc0` |
| OmniRoute `package.json` | `b002c54561bd762f41c7f4cafe6809ac5d5e58bbe175ce0399eb7c1df5b0baf6` |
| OmniRoute `bin/cli/api.mjs` | `46d7693864f13814d04f47537c4f447f25eeac6d337f37ac5302cc4f6285b7dd` |
| OmniRoute `bin/cli/commands/health.mjs` | `33297c216ee635149771ace599f59ac4a68a1b38afbba09c5d33bf0ba98b6b22` |
| OmniRoute `bin/cli/api-commands/models.mjs` | `13de5646493d441b0ea52f75ebfbb669d7a4f16f42c12a026155642b9d303e72` |

Реальные результаты проверок проекта: [qa-issue-11.json](qa-issue-11.json).
`python3 -m pytest -q` завершился exit 1: `No module named pytest`.
Пакеты не устанавливались. Синтаксис backend проверяется через builtin `compile`
без создания pyc и без импорта приложения. Это не заменяет pytest и integration QA.
Это частичный отчёт: даже если документационный PR объединён, Issue #11 нельзя закрывать без авторизованного inventory и проверки фактической интеграции Hermes → OmniRoute.
