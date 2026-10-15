# ADR-001: Open-source компоненты без второго директора

[English summary](ADR-001-ORCHESTRATION.en.md)

Upstream-проверка: **14.10.2026**, закреплённые ревизии ниже. Сопоставление с
Zorin и кодом `main`: **15.10.2026**. Задача: [#12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12).

**Статус: принято решение о составе runtime — не добавлять шесть рассмотренных frameworks.**
Владелец разрешил завершить live-проверки и объединить готовую работу. На основе
[аудита Zorin](ZORIN_INTEGRATION.md) и [live QA](qa-issue-13-live.json) подтверждены
авторизованный inventory, текстовый inference через OmniRoute, streaming Hermes
и один вызов встроенного делегирования с тем же маршрутом у parent/child.
Это достаточное основание сохранить существующие сервисы и узкий адаптер #13;
необходимость второго orchestration runtime не доказана. Следующие интеграционные
этапы требуют собственных тестов и не объявляются выполненными этим ADR.

Исследование шести upstream-проектов остаётся закреплённым на ревизиях
14.10.2026. Сопоставление #38 и его QA — исторические артефакты до live-разрешения;
новая верификация описана здесь и в отчёте #13. Новые frameworks не устанавливались,
чужой исходный код не копировался. #13 подключает явный transport к ручным legacy
round/check; taskflow по-прежнему использует Mock Director.

В проектных документах используется название OmniRouter; реально проверенный
установленный пакет — **OmniRoute 3.8.51**. Hermes install stamp —
**0.21.5+5343.ga3b56ca**, commit `a3b56cac95488242856b6fb1f121842a38c3e391`.
Это текущие метаданные установки, не исторические версии 0.21.0/3.8.50 и не
доказательство активной сессии Hermes. SSH использовал сохранённый ключ со строгой
проверкой; пароль и конфигурации доступа не менялись. Во время первоначального продолжения #38 повторных обращений к серверу не было;
последующие авторизованные пробы описаны в live-отчёте #13.

## Решение

**Сейчас не добавлять ни один из шести рассмотренных пакетов в runtime.** Использовать описанные ниже идеи с указанием источников, без копирования кода. Hermes остаётся целевым владельцем декомпозиции и делегирования, OmniRouter — выбора моделей. Подтверждённые контракты и оставшиеся интеграционные пробелы перечислены ниже. AICommander хранит требования, артефакты, фактические результаты QA и решения владельца; это не основание создавать параллельный планировщик или маршрутизатор.

LangGraph оставить кандидатом только при доказанном пробеле в сохранении/возобновлении процесса. OpenHands SDK оставить альтернативой для узкого executor, если проверка Codex CLI на этапе #15 выявит конкретную недостающую возможность. Это кандидаты на пересмотр ADR, а не выбранные зависимости и не разрешение на установку. CrewAI, MetaGPT, Microsoft Agent Framework и SWE-agent не включать в текущую архитектуру.

## Контекст и критерии

Требуемый процесс из [PRODUCT_SPEC](PRODUCT_SPEC.md): владелец → Hermes → роли → изменения в изолированном worktree → реальные QA-команды → ревью diff → draft PR → решение владельца. Текущий `main` ещё не выполняет этот процесс сквозным образом. Legacy
`backend/app/orchestration/round_runner.py` запрашивает текстовые ответы ролей,
`backend/app/providers/openrouter.py` содержит старый совместимый транспорт.
Новый `backend/app/taskflow` уже сохраняет mock-артефакты, версии и решения
владельца; `backend/app/execution` отдельно проверяет worktree/команды для
доверенных fixture-программ. Панель использует taskflow, но реальный Hermes,
Codex и executor в него не подключены. Отдельные ручные legacy-раунды и проверки
моделей теперь умеют явно использовать проверенный адаптер OmniRoute. Изучение SDK не устраняет эти пробелы.

Решение оценивается по пяти критериям:

1. Добавляет ли компонент подтверждённую возможность, отсутствующую у установленного Hermes/OmniRouter?
2. Можно ли подключить его под одной ролью без второго владельца жизненного цикла, выбора модели и повторных попыток?
3. Совместим ли он с матрицей foundation Python **3.11–3.13**, зависимостями и будущей изоляцией executor?
4. Есть ли проверяемые LICENSE, ревизия, поддержка и способ собрать тестовые доказательства?
5. Соразмерны ли новый runtime, зависимости и сопровождение конкретному пробелу?

На первый вопрос сейчас нет проверенного ответа. Поэтому наличие похожих возможностей у upstream не является достаточным основанием для установки.

## Сопоставление с проверенным Zorin и текущим foundation

Этот раздел основан на локальных артефактах #11 и исходниках `main`, а не на
новой оценке актуальных upstream-релизов. Снимок от 14.10.2026 сохранён без
изменения даты, SHA и сведений о лицензиях. Полное runtime-соответствие ни одного
внешнего фреймворка не заявляется.

| Область | Что подтверждено | Архитектурное следствие / чего ещё нет |
|---|---|---|
| OmniRoute | User service active/running/enabled, health 200; models без credentials 401 | Сохраняем существующий router. Авторизованный inventory и один text route проверены live; стоимость/доступность остальных моделей не установлены, 401 без credentials не означает пустой каталог. |
| Hermes | Исходники custom Chat Completions backend, CLI provider/model/stream-json/resume, встроенный delegate_task | Сохраняем Hermes как целевого директора. Live text, streaming и один child route проверены; произвольные tools и полный ролевой workflow не проверены. |
| Taskflow | Типизированные артефакты, версии, idempotency, SQLite-транзакции, owner approve/reject/cancel и ручное продолжение | Уже есть журнал процесса приложения. Это не доказательство надёжного возобновления внешнего Hermes или exactly-once исполнения. |
| Панель | PR #30 подключил UI к taskflow, auth/CSRF, отображению артефактов | Панель остаётся клиентом команд и снимков; не назначаем ей собственного директора или планировщик retries. |
| Offline executor | Отдельный worktree, diff, exit code, timeout/cancel для доверенных тестовых программ | Не подключён к taskflow и Codex; не является OS sandbox. OpenHands пока не закрывает измеренный пробел. |
| Окружение | Node службы v24.20.0, SSH shell v20.20.0; пользовательские launchers вне неинтерактивного PATH | В интеграционных этапах явно выбрать runtime/launcher, проверить transport. Отсутствие команды в PATH не считать отсутствием пакета. |

Источники: [Zorin-аудит](ZORIN_INTEGRATION.md),
[наблюдения #11](contracts/zorin-live-probes.json),
[taskflow v1](TASKFLOW.md), [executor](EXECUTION.md),
[панель](MACBOOK_PANEL.md),
[машиночитаемое сопоставление](research/adr-001-zorin-followup.json).

### Границы ответственности для будущей интеграции

Следующая таблица — **предложение для #13–#16**, а не описание готовых адаптеров.

| Владелец | Ответственность | Условие перед внедрением |
|---|---|---|
| OmniRoute | Каталог и маршрутизация моделей, provider fallback | Проверенные inventory/auth и политика стоимости. Не дублировать его fallback полным вторым роутером в AICommander. |
| Hermes | Декомпозиция и делегирование ролей | Проверить CLI/HTTP transport, формат результата, остановку и маршрут каждого дочернего агента через OmniRoute. |
| AICommander taskflow | Задача, версия, типизированные доказательства, история, решение владельца | Сопоставить run/stage с внешним operation/session ID; хранить согласование отдельно от вывода модели. |
| Executor / QA | Изменения в разрешённом workspace, фактический diff и результаты команд | Проверить Codex transport и изоляцию ОС. Артефакт plan не считается выполнением; done в текущем mock-процессе не означает успешный QA. |
| Панель | Показать состояние и отправить команду владельца | После конфликта версии перечитать snapshot; не повторять внешнее действие автоматически. |

**Критичная граница транзакции:** сейчас `Taskflow.command()` держит
`BEGIN IMMEDIATE` во время вызова `MockDirector.produce()`. Это допустимо для
чистой локальной mock-функции. Нельзя просто заменить её сетевым вызовом Hermes
или запуском executor: rollback SQLite не отменит запрос/изменение файла, а
долгая операция удержит write lock. Для #14 предложить резервирование операции,
вызов вне write-транзакции и отдельную фиксацию результата с проверкой версии.
Нужны correlation ID и reconciliation после сбоя; повтор команды не должен
повторно оплачивать inference или изменять файлы. Такой протокол ещё не реализован.

Retries необходимо распределить по слоям: ограниченные transport retries не
должны превращаться в повтор полного этапа поверх Hermes/OmniRoute retries.
До подтверждения provider semantics нельзя обещать exactly-once или отсутствие
повторной оплаты. Конкретные лимиты и поведение задаются в #13/#14/#18.

### Передача от архитектурного решения к реализации

Live-критерии выбора существующего транспорта и делегирования проверены в #13
по прямому разрешению владельца. Консервативное решение «существующие сервисы +
узкие адаптеры» принято; обещания полной совместимости любого стороннего framework
по-прежнему нет. В #14 нужны отдельные операции вне SQLite write lock, связь с
session/operation ID, идемпотентность внешних эффектов, отмена и обработка сбоев.
Сброс пароля панели, persistent deployment и reboot recovery не входили в эти пробы.

## Сравнение

Диапазоны Python взяты из package metadata на закреплённых ревизиях. Они описывают допустимую версию интерпретатора, **не результат установки или integration tests**. Все шесть репозиториев на момент проверки не архивированы; это не гарантия поддержки. Полные SHA, URL файлов, copyright и наблюдавшиеся releases сохранены в [снимке источников](research/adr-001-upstream.json).

| Проект | Версия изученного исходника / Python | Польза и пересечение с Hermes | Решение и причина |
|---|---|---|---|
| CrewAI | Семейство пакетов 1.15.28, версия проекта dynamic; `>=3.10,<3.14` | Crews распределяют роли; Flows управляют событиями и состоянием. Это ещё один слой orchestration, не только шаблон prompt. | Только идеи явных ролей и ограниченных этапов. Не добавлять Crew/Flow runtime: отсутствие такого механизма в Hermes не доказано. |
| MetaGPT | `setup.py` 1.0.0; опубликованный release v0.8.2; `>=3.9,<3.12` | SOP команды и передача результатов между продуктовыми/инженерными ролями полезны как образец требований к артефактам. | Только идея SOP. Runtime исключён: не допускает Python 3.12/3.13 и вводит собственную команду/процесс. Не считать version из main опубликованным release. |
| LangGraph | Core 1.2.15; `>=3.10` | Состояние, checkpoint, interrupts и возобновление процесса; перекрытие с persistence/approval/delegation Hermes ещё не измерено. | Отложить. Рассмотреть узкий слой deterministic persistence лишь после #11 и доказательства пробела, не закрываемого уже существующим taskflow. Не запускать второй agent graph параллельно Hermes. |
| OpenHands Software Agent SDK | 1.54.0; `>=3.12` | Кодовые инструменты, conversation/events, локальные и удалённые workspace, Agent Server. Может служить executor, но содержит собственный agent loop и LLM client. | Отложенная альтернатива для #15. Не встраивать в backend Python 3.11. Возможный отдельный Python 3.12+ процесс потребует отдельного ADR, изоляции и испытаний. |
| Microsoft Agent Framework | Python core 1.21.0; `>=3.10` | Agents, workflows, handoff, checkpoints и human-in-the-loop; пересечение с директором и процессом Hermes. | Только идеи typed events/handoff. Не подключать framework или meta-package без доказанного пробела; наличие интеграционных протоколов не доказывает совместимость с установленным сервисом. |
| SWE-agent | 1.1.0; `>=3.11`; classifiers явно перечисляют 3.11/3.12 | Issue → инструменты → diff/trajectory, полезно как пример доказательств исполнения. Собственный coding loop и окружение. | Только идеи журнала действий и результатов команд. README сообщает перенос основной разработки в mini-SWE-agent; не выбирать старый harness новым executor по умолчанию. mini-SWE-agent отдельно здесь не оценивался. |

### Поддержка и неизменяемые источники

Дата коммита ниже относится к выбранной default branch, а не к последнему push во всём репозитории. Release — наблюдённая публикация, не обещание maintenance/SLA. Для монорепозитория версия одного пакета не применяется ко всем пакетам.

| Проект / автор | Изученная ревизия, дата UTC | Сигнал поддержки | Документация и лицензия на той же ревизии |
|---|---|---|---|
| CrewAI / crewAI, Inc.; Joao Moura | [`aa5f2acd9b48782b6b6a756bcef24cc54ac0530b`](https://github.com/crewAIInc/crewAI/commit/aa5f2acd9b48782b6b6a756bcef24cc54ac0530b), 2026-10-14 | Release [1.15.28](https://github.com/crewAIInc/crewAI/releases/tag/1.15.28), 2026-10-14; main обновлялся в день проверки. | [README](https://github.com/crewAIInc/crewAI/blob/aa5f2acd9b48782b6b6a756bcef24cc54ac0530b/README.md), [metadata](https://github.com/crewAIInc/crewAI/blob/aa5f2acd9b48782b6b6a756bcef24cc54ac0530b/lib/crewai/pyproject.toml), [MIT LICENSE](https://github.com/crewAIInc/crewAI/blob/aa5f2acd9b48782b6b6a756bcef24cc54ac0530b/LICENSE). |
| MetaGPT / FoundationAgents; Chenglin Wu | [`11cdf466d042aece04fc6cfd13b28e1a70341b1f`](https://github.com/FoundationAgents/MetaGPT/commit/11cdf466d042aece04fc6cfd13b28e1a70341b1f), 2026-01-21 | Release [v0.8.2](https://github.com/FoundationAgents/MetaGPT/releases/tag/v0.8.2), 2025-03-09; default branch существенно старше даты проверки. Это риск актуальности, не заявление о прекращении проекта. | [README](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/README.md), [setup.py](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/setup.py), [MIT LICENSE](https://github.com/FoundationAgents/MetaGPT/blob/11cdf466d042aece04fc6cfd13b28e1a70341b1f/LICENSE). |
| LangGraph / LangChain, Inc. | [`d4149cc1f5384364d1a21092b4c2f582a6e7af8f`](https://github.com/langchain-ai/langgraph/commit/d4149cc1f5384364d1a21092b4c2f582a6e7af8f), 2026-10-14 | Core metadata 1.2.15; наблюдавшиеся releases монорепозитория относятся также к CLI/checkpoint-postgres, не выдаются за release core. Main обновлялся в день проверки. | [README](https://github.com/langchain-ai/langgraph/blob/d4149cc1f5384364d1a21092b4c2f582a6e7af8f/README.md), [metadata](https://github.com/langchain-ai/langgraph/blob/d4149cc1f5384364d1a21092b4c2f582a6e7af8f/libs/langgraph/pyproject.toml), [MIT LICENSE core](https://github.com/langchain-ai/langgraph/blob/d4149cc1f5384364d1a21092b4c2f582a6e7af8f/libs/langgraph/LICENSE). |
| OpenHands / OpenHands contributors | [`75105bd40936f1962d8fa91506776a0c02ba957f`](https://github.com/OpenHands/software-agent-sdk/commit/75105bd40936f1962d8fa91506776a0c02ba957f), 2026-10-14 | Release [v1.54.0](https://github.com/OpenHands/software-agent-sdk/releases/tag/v1.54.0), 2026-10-09; main обновлялся в день проверки. | [README](https://github.com/OpenHands/software-agent-sdk/blob/75105bd40936f1962d8fa91506776a0c02ba957f/README.md), [metadata](https://github.com/OpenHands/software-agent-sdk/blob/75105bd40936f1962d8fa91506776a0c02ba957f/openhands-sdk/pyproject.toml), [MIT LICENSE](https://github.com/OpenHands/software-agent-sdk/blob/75105bd40936f1962d8fa91506776a0c02ba957f/LICENSE). |
| Microsoft Agent Framework / Microsoft Corporation | [`95511ff025d81cc546c44e653d4be65de5bd7f35`](https://github.com/microsoft/agent-framework/commit/95511ff025d81cc546c44e653d4be65de5bd7f35), 2026-10-14 | Python release [python-1.21.0](https://github.com/microsoft/agent-framework/releases/tag/python-1.21.0), 2026-10-08; .NET releases учитываются отдельно. | [README](https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/README.md), [metadata core](https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/python/packages/core/pyproject.toml), [MIT LICENSE](https://github.com/microsoft/agent-framework/blob/95511ff025d81cc546c44e653d4be65de5bd7f35/LICENSE). |
| SWE-agent / John Yang, Carlos E. Jimenez, Alexander Wettig, Shunyu Yao, Karthik Narasimhan, Ofir Press | [`3ea751c087f32b16e039a2233dd6eefecef325d5`](https://github.com/SWE-agent/SWE-agent/commit/3ea751c087f32b16e039a2233dd6eefecef325d5), 2026-07-16 | Release [v1.1.0](https://github.com/SWE-agent/SWE-agent/releases/tag/v1.1.0), 2025-05-22. README рекомендует successor mini-SWE-agent. | [README](https://github.com/SWE-agent/SWE-agent/blob/3ea751c087f32b16e039a2233dd6eefecef325d5/README.md), [metadata](https://github.com/SWE-agent/SWE-agent/blob/3ea751c087f32b16e039a2233dd6eefecef325d5/pyproject.toml), [MIT LICENSE](https://github.com/SWE-agent/SWE-agent/blob/3ea751c087f32b16e039a2233dd6eefecef325d5/LICENSE). |

Дополнительно прочитана официальная документация: [CrewAI](https://docs.crewai.com/v1.15.28/en/introduction), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [OpenHands SDK](https://docs.openhands.dev/sdk), [Microsoft Agent Framework](https://learn.microsoft.com/en-us/agent-framework/overview/). Эти страницы могут обновляться; закреплённые README и metadata выше фиксируют основание решения.

## Рассмотренные варианты

| Вариант | Выгода | Цена и ограничение | Итог |
|---|---|---|---|
| Только идеи, существующие сервисы и узкие адаптеры | Сохраняет одного директора и маршрутизатор; не меняет зависимости foundation. | Исходные интерфейсы частично установлены; один runtime route и inventory проверены; протокол внешних эффектов ещё не реализован. | Выбран для текущего этапа. Это не поручение написать собственный аналог Hermes. |
| Одна небольшая зависимость | Может закрыть конкретный недостаток persistence/schema. | Среди шести проектов не доказана необходимая небольшая добавка. LangGraph тянет несколько компонентов и собственный runtime; факт одного `pip install` не делает его одной узкой функцией. | Сейчас отклонён. Пересмотреть после измеримого пробела, а не добавлять пакет ради завершения ADR. |
| SDK для executor | Готовые файловые/командные инструменты, события, удалённый workspace. | OpenHands SDK включает agent loop и LLM client, требует Python 3.12+; запуск локально сам по себе не изоляция. SWE-agent — отдельный harness с рекомендованным successor. | Отложен до #15; первичный путь проекта остаётся проверка Codex CLI. |

## Границы совместимости и условия пересмотра

**Фактическая совместимость с установленным Hermes/OmniRouter не подтверждена ни для одного кандидата.** Совпадение HTTP/OpenAI-compatible формата, наличие MCP или Python API не доказывает поддержку нужных tools, streaming, отмены, auth, ошибок quota или формата артефактов. В этом ADR не назначаются адреса/порты сервисов и не создаются выдуманные fixtures.

До изменения решения должны появиться следующие доказательства:

1. Из #11: идентификация установленных проектов, версии, read-only способ обращения, auth без значений секретов, список возможностей, делегирование, состояния задач, отмена/таймауты, ограничения и безопасные fixtures подтверждённых ответов.
2. Для LangGraph: воспроизводимый сценарий, где Hermes не сохраняет/не возобновляет нужное состояние; единственный владелец жизненного цикла и чёткая граница с журналом AICommander; сравнение с использованием уже существующего persistence Hermes. Нельзя включить два конкурирующих retry loop.
3. Для OpenHands: конкретная недостающая возможность поддерживаемого Codex CLI, отдельный процесс Python 3.12+, проверенные model/tool контракты через OmniRouter, отсутствие обходной маршрутизации SDK, изолированный workspace и явная политика доступа. Локальный workspace не даёт требуемую песочницу; контейнер тоже требует ограничений filesystem/network.
4. Для любого пакета: lock зависимостей, проверка лицензий выбранных extras и transitive packages, установка/тесты в одноразовом окружении, проверка версии Python, фиксация расходов/таймаутов/остановки и понятный rollback. Результаты запрашиваются перед принятием, сейчас они не заявлены.

Функциональные проверки будущего адаптера: передача артефакта между ролями; повтор после сбоя без двойного исполнения; остановка пользователем; исчерпание попыток/бюджета; невозможность записи вне worktree; failing pytest не становится успешным QA; PR остаётся без auto-merge. Это критерии будущего эксперимента, не готовые тесты или реализация в этом PR.

## Лицензии и заимствования

На указанных ревизиях прочитаны MIT LICENSE шести репозиториев; у LangGraph также проверен LICENSE core-пакета. Это вывод только о рассмотренных исходниках, не о всех сервисах бренда, моделях, образах, дополнительных пакетах или transitive dependencies. Коммерческие платформы и внешние сервисы нельзя автоматически считать покрытыми MIT root LICENSE.

Код, prompts, примеры и конфигурации upstream в AICommander не переносились; в PR добавлены собственный анализ, ссылки и метаданные исследования. Поэтому `THIRD_PARTY_NOTICES` с чужим кодом в этом этапе не требуется. Авторы указаны в таблице и снимке источников.

Если позднее копируется конкретный файл или существенный фрагмент: указать исходный путь и commit SHA, автора, точный текст применимой лицензии и обязательные copyright notices; добавить `THIRD_PARTY_NOTICES` и текст лицензии, проверить file-level исключения и зависимости. Перед установкой пакета аналогично проверять конкретную версию и состав поставки. Наличие MIT у репозитория не заменяет эту проверку.

## Последствия и проверка

Само архитектурное исследование не меняло runtime и не обращалось к Zorin; последующий PR #13 добавляет адаптер и авторизованные live-пробы отдельно от этого решения. Новых frameworks нет, production не затронут. Откат этого продолжения — возврат документации к предыдущему commit; runtime и данные не меняются. Минус решения: runtime-интеграция остаётся неподтверждённой до #11/#15; проверенный offline executor не заменяет проверку реального Codex или песочницы. Польза: нет преждевременно выбранного второго директора или нового маршрута моделей.

Первоначальный отчёт от 14.10.2026 — [qa-issue-12.json](qa-issue-12.json):
исторический сбой старой базы и 40 прошедших тестов после PR #25 сохранены
отдельно. Проверки этого продолжения на основе `main` после PR #30/#37 —
[qa-issue-12-followup.json](qa-issue-12-followup.json). Результаты старой базы
не выдаются за регрессию текущей панели/taskflow. Актуальные live-результаты — [qa-issue-13-live.json](qa-issue-13-live.json).
Принятие этого ADR не завершает #14–#22 и не разрешает автоматический merge/deploy
за пределами прямого поручения владельца для готовой работы #13.
