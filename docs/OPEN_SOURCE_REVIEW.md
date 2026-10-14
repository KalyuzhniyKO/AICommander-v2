# Заимствование проверенных решений с GitHub

[English](OPEN_SOURCE_REVIEW.en.md)

**Цель:** брать только полезные компоненты и паттерны. Hermes/OmniRouter уже действуют на Zorin OS, поэтому ещё один оркестратор без необходимости не нужен. **В foundation не копировался чужой код.**

| Проект и автор | Лицензия в проверенном репозитории | Что изучить | Решение |
|---|---|---|---|
| [CrewAI — crewAIInc](https://github.com/crewAIInc/crewAI) | MIT | Роли и цепочки задач | Идеи/адаптер при необходимости |
| [MetaGPT — FoundationAgents](https://github.com/FoundationAgents/MetaGPT) | MIT | SOP команды Analyst→Architect→Developer | Паттерн, не весь фреймворк |
| [LangGraph — LangChain](https://github.com/langchain-ai/langgraph) | MIT для основного пакета; проверить конкретный код | Состояния, checkpoints, human approvals | Возможно узкая зависимость после ADR |
| [OpenHands SDK — сообщество OpenHands](https://github.com/OpenHands/software-agent-sdk) | MIT в проверенной версии; перепроверить commit | Изолированное исполнение и инструменты | Сравнить с Codex CLI |
| [Microsoft Agent Framework — Microsoft](https://github.com/microsoft/agent-framework) | MIT | Типизированные процессы, делегирование | Исследовать, может дублировать Hermes |
| [SWE-agent — авторы SWE-agent](https://github.com/SWE-agent/SWE-agent) | MIT | GitHub Issue → исправление → тест | Идеи для pipeline |

**Правила использования:** перед копированием указать точный путь/commit, автора, полный текст разрешающей лицензии и нужные copyright notices. Проверить лицензии файла и зависимостей, включая исключения внутри репозитория. Предпочитать поддерживаемую библиотеку копированию большого объёма исходников; фиксировать версию и проверки. Решение принимается в [Issue #12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12). Источник идей и факт копирования — разные вещи: авторство обязательно указывать для реально скопированного кода, а ссылки на идеи сохранять в этом документе.
