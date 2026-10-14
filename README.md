# AICommander 3.0 — виртуальная команда ИИ-разработчиков

[**English version / Английская версия**](README.en.md)

**Статус:** подготовлена минимальная основа (foundation MVP). Полноценная интеграция Hermes, OmniRouter, Codex и QA **ещё не реализована**. Рабочая версия 2 сохранена без изменений: [AICommander-v2](https://github.com/KalyuzhniyKO/AICommander-v2).

## Что мы создаём

Ты ставишь задачу **с MacBook** и принимаешь результат. На домашнем **Zorin OS** уже установлены Hermes и OmniRouter. AICommander управляет прозрачным процессом разработки, **не дублируя** их собственные функции.

**Цепочка работы:** владелец → директор (Hermes) → аналитик → архитектор (если нужен) → программист (Codex для сложных работ) → автоматические тесты/QA → независимый ревьюер → GitHub Pull Request → твоё подтверждение.

Цель — настоящие изменения в Git-ветке и проверенные тесты, а не пять текстовых советов от разных моделей.

## Что уже перенесено из v2

- локальный FastAPI и минимальный веб-интерфейс;
- задачи, история раундов, результаты ролей в SQLite;
- базовые подсказки ролям и первоначальное распределение по ключевым словам;
- клиент совместимого с OpenRouter API, проверка моделей и резервные модели;
- базовые тесты без реальных API-ключей.

**Пока отсутствует:** подключение существующего Hermes/OmniRouter, отдельные аналитик и QA, исполнение Codex CLI, работа с реальными файлами, безопасная песочница, создание PR, авторизованная панель для MacBook и учёт бюджета. Запуск и прохождение тестов новой ветки ещё не подтверждены.

**Не переносим из v2:** архивные мосты для macOS, Director/Judge/Final Auditor migration pack, старые планы, пустые обёртки ролей, ненужную интеграцию с отдельным OpenAI API Premium Review. ChatGPT в браузере используется **вручную** для сложных экспертных задач.

## Принципы работы

1. Используем уже настроенные Hermes и OmniRouter, не пишем их аналоги.
2. Бесплатные или дешёвые модели — обычные этапы; сложная реализация — Codex; ChatGPT Web — ручная экспертиза.
3. QA доказывает результат реальными тестами, а ревьюер проверяет Git diff.
4. Production, реальные базы склада и секреты агентам недоступны.
5. Каждая задача Codex — отдельный Issue и отдельный PR; никакого автоматического merge или развёртывания.

## Документация

| Документ | Русский | English |
|---|---|---|
| Техническое задание | [PRODUCT_SPEC](docs/PRODUCT_SPEC.md) | [Product spec](docs/PRODUCT_SPEC.en.md) |
| Реализовано и не реализовано | [IMPLEMENTATION](docs/IMPLEMENTATION.md) | [Implementation](docs/IMPLEMENTATION.en.md) |
| Очерёдность работы Codex | [ROADMAP](docs/ROADMAP.md) | [Roadmap](docs/ROADMAP.en.md) |
| Выбор модели и уровня | [MODEL_SELECTION](docs/MODEL_SELECTION.md) | [Model selection](docs/MODEL_SELECTION.en.md) |
| Использование Open Source | [OPEN_SOURCE_REVIEW](docs/OPEN_SOURCE_REVIEW.md) | [Open-source review](docs/OPEN_SOURCE_REVIEW.en.md) |
| Инструкции Codex | [AGENTS.md](AGENTS.md) | [Codex instructions](AGENTS.en.md) |
| Английские версии GitHub Issues | Основные описания — в Issues | [Issues EN](docs/ISSUES_EN.md) |

## Локальный запуск базовой версии

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cp config/models.example.json config/models.json
pytest -q
python -m backend.app.main
```

Открыть: `http://127.0.0.1:8000`. В конфигурации моделей указаны **заглушки**, их нужно заменить действительными ID. Прототип **без авторизации** — не публикуй его в интернет или домашнюю сеть.

## Где находится v3

Пока это **отдельная ветка** [`v3-foundation`](https://github.com/KalyuzhniyKO/AICommander-v2/tree/v3-foundation) в репозитории v2: подключённый GitHub не может создать новый репозиторий. [Issue переноса #23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23). **`main` v2 не затронут.**

[Очередь Codex](docs/ROADMAP.md) начинается с [Issue #10](https://github.com/KalyuzhniyKO/AICommander-v2/issues/10). У каждой задачи есть зависимость, подходящая модель и уровень рассуждения.
