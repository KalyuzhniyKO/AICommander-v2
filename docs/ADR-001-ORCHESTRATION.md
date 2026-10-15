# ADR-001: Open-source компоненты без второго директора

Дата проверки: **14.10.2026**. Задача: [#12](https://github.com/KalyuzhniyKO/AICommander-v3/issues/12).

**Статус: предложение; окончательный выбор компонентов и внедрение ожидают проверки #11.** По прямому запросу владельца исследование #12 подготовлено до завершения #11 и передано для объединения как документ исследования. Это не подтверждает выполнение зависимости и не разрешает начинать #13. [#11](https://github.com/KalyuzhniyKO/AICommander-v3/issues/11) открыт, `docs/ZORIN_INTEGRATION.md` отсутствует: текущие версии, реальные API/CLI и возможности установленного Hermes/OmniRouter не проверены.

В уточнениях #11 владелец сообщил о **dual boot Zorin OS/Windows на одном ПК**; архивная сводка называет **Hermes Agent 0.21.0 и OmniRoute 3.8.50**. Это исторические данные, а не новый аудит доступных служб. В roadmap используется название OmniRouter; связь этого названия с фактической установкой OmniRoute предстоит подтвердить в #11. Разные SSH host keys двух ОС ожидаемы, но подключаться нужно только после обычной проверки ключа доверенным способом и подтверждения загрузки Zorin. Этот ADR не устанавливает идентичность сервиса по одному названию, не обращается к хосту и не подтверждает совместимость по архивной версии.

## Решение

**Сейчас не добавлять ни один из шести рассмотренных пакетов в runtime.** Использовать описанные ниже идеи с указанием источников, без копирования кода. Hermes остаётся целевым владельцем декомпозиции и делегирования, OmniRouter — выбора моделей. Сначала подтвердить их контракты в #11. AICommander хранит требования, артефакты, фактические результаты QA и решения владельца; это не основание создавать параллельный планировщик или маршрутизатор.

LangGraph оставить кандидатом только при доказанном пробеле в сохранении/возобновлении процесса. OpenHands SDK оставить альтернативой для узкого executor, если проверка Codex CLI на этапе #15 выявит конкретную недостающую возможность. Это кандидаты на пересмотр ADR, а не выбранные зависимости и не разрешение на установку. CrewAI, MetaGPT, Microsoft Agent Framework и SWE-agent не включать в текущую архитектуру.

## Контекст и критерии

Требуемый процесс из [PRODUCT_SPEC](PRODUCT_SPEC.md): владелец → Hermes → роли → изменения в изолированном worktree → реальные QA-команды → ревью diff → draft PR → решение владельца. Текущий foundation ещё не выполняет этот процесс: `backend/app/orchestration/round_runner.py` запрашивает текстовые ответы ролей, а `backend/app/providers/openrouter.py` содержит старый совместимый транспорт. Изучение стороннего SDK не делает ни один из этих пробелов устранённым.

Решение оценивается по пяти критериям:

1. Добавляет ли компонент подтверждённую возможность, отсутствующую у установленного Hermes/OmniRouter?
2. Можно ли подключить его под одной ролью без второго владельца жизненного цикла, выбора модели и повторных попыток?
3. Совместим ли он с матрицей foundation Python **3.11–3.13**, зависимостями и будущей изоляцией executor?
4. Есть ли проверяемые LICENSE, ревизия, поддержка и способ собрать тестовые доказательства?
5. Соразмерны ли новый runtime, зависимости и сопровождение конкретному пробелу?

На первый вопрос сейчас нет проверенного ответа. Поэтому наличие похожих возможностей у upstream не является достаточным основанием для установки.

## Сравнение

Диапазоны Python взяты из package metadata на закреплённых ревизиях. Они описывают допустимую версию интерпретатора, **не результат установки или integration tests**. Все шесть репозиториев на момент проверки не архивированы; это не гарантия поддержки. Полные SHA, URL файлов, copyright и наблюдавшиеся releases сохранены в [снимке источников](research/adr-001-upstream.json).

| Проект | Версия изученного исходника / Python | Польза и пересечение с Hermes | Решение и причина |
|---|---|---|---|
| CrewAI | Семейство пакетов 1.15.28, версия проекта dynamic; `>=3.10,<3.14` | Crews распределяют роли; Flows управляют событиями и состоянием. Это ещё один слой orchestration, не только шаблон prompt. | Только идеи явных ролей и ограниченных этапов. Не добавлять Crew/Flow runtime: отсутствие такого механизма в Hermes не доказано. |
| MetaGPT | `setup.py` 1.0.0; опубликованный release v0.8.2; `>=3.9,<3.12` | SOP команды и передача результатов между продуктовыми/инженерными ролями полезны как образец требований к артефактам. | Только идея SOP. Runtime исключён: не допускает Python 3.12/3.13 и вводит собственную команду/процесс. Не считать version из main опубликованным release. |
| LangGraph | Core 1.2.15; `>=3.10` | Состояние, checkpoint, interrupts и возобновление процесса; перекрытие с persistence/approval/delegation Hermes ещё не измерено. | Отложить. Рассмотреть узкий слой deterministic persistence лишь после #11 и доказательства пробела. Не запускать второй agent graph параллельно Hermes. |
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
| Только идеи, существующие сервисы и узкие адаптеры | Сохраняет одного директора и маршрутизатор; не меняет зависимости foundation. | Конкретные возможности адаптеров остаются неизвестными до #11. | Выбран для текущего этапа. Это не поручение написать собственный аналог Hermes. |
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

Этот этап не меняет `requirements*.txt`, backend, frontend или конфигурацию моделей, не устанавливает внешние фреймворки и не обращается к Zorin/production. Откат — удаление ADR/снимка и ссылок на них; runtime и данные не меняются. Минус решения: интеграционные выводы и преимущества executor остаются неподтверждёнными до #11/#15. Польза: нет преждевременно выбранного второго директора или нового маршрута моделей.

Отчёт фактических команд и ограничений — [qa-issue-12.json](qa-issue-12.json). [PR #25](https://github.com/KalyuzhniyKO/AICommander-v3/pull/25) с исправлением импорта legacy bridge объединён в `v3-foundation` коммитом `7a5f599a19b3737cd00fc4be1c4996b551c3489c`; ветка этого исследования обновлена на эту основу. В отчёте сохранены исторический сбой старой базы и новые проверки актуальной ветки — их нельзя смешивать. Окончательное принятие интеграционных выводов ожидает проверки #11; объединение документа исследования не означает прохождение #11, установку пакетов или переход к #13.
