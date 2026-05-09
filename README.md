# AICommander-v2

AICommander-v2 — это программа для запуска команды ИИ-агентов. Пользователь пишет большую задачу, программа сама выбирает нужные роли, запускает один круг работы, показывает результат и ждёт комментарии пользователя перед следующим кругом.

Проще говоря, это **не обычный чат**. AICommander-v2 работает как оркестратор ИИ-команды: задача делится между ролями, каждая роль делает свою часть, а пользователь после каждого круга может остановиться, уточнить требования, попросить переделать роль или запустить следующий круг.

Важно:

- платный ИИ не обязателен для основного сценария;
- OpenRouter используется как основной provider для обычных ролей;
- OpenAI используется только для необязательного этапа Premium Review;
- локальные модели и Ollama не требуются;
- результаты и ошибки сохраняются в SQLite.

## Что умеет сейчас

Текущий MVP уже поддерживает:

- создание задачи;
- автоматический выбор ролей под тип задачи;
- запуск одного круга работы AI-команды;
- OpenRouter provider для основных ролей;
- fallback между моделями внутри каждой роли;
- сохранение задач, кругов, ответов ролей и ошибок моделей в SQLite;
- просмотр ошибок и статусов моделей;
- ручной запуск следующего круга после комментария пользователя;
- повторный запуск отдельной роли;
- необязательный Premium Review;
- endpoint `GET /models/status` для проверки состояния моделей;
- endpoint `GET /health` для простой проверки backend;
- простой frontend в папке `frontend/`.

## Как работает логика

Основной поток выглядит так:

```text
Пользователь → Manager → Architect / Designer / Coder / Reviewer → результат круга → комментарий пользователя → следующий круг
```

1. Пользователь описывает большую задачу.
2. `Manager` определяет тип задачи и помогает собрать план работы.
3. Система автоматически выбирает роли, которые нужны для текущей задачи.
4. Роли выполняются через OpenRouter и возвращают свои результаты.
5. Backend сохраняет результат круга в SQLite.
6. Пользователь читает результат, добавляет комментарий или исправление.
7. Следующий круг запускается только вручную.

Такой подход нужен, чтобы человек оставался в контуре принятия решений и мог корректировать направление работы после каждого круга.

## Роли AI-команды

- **Manager** — понимает исходную задачу, определяет тип работы, координирует роли и формирует общий план.
- **Architect** — отвечает за архитектуру, технические решения, стек, API, базу данных и структуру проекта.
- **Designer** — продумывает пользовательский опыт, экраны, сценарии, интерфейс и продуктовую логику.
- **Coder** — предлагает план реализации, изменения в коде, файлах и технических деталях.
- **Reviewer** — ищет ошибки, противоречия, риски, пропущенные требования и слабые места.
- **Premium Reviewer** — необязательная платная экспертная проверка после основного круга.

Не каждая задача требует все роли. Например, для документации могут быть достаточно `manager` и `reviewer`, а для полноценного web-приложения обычно нужны `manager`, `architect`, `designer`, `coder` и `reviewer`.

## OpenRouter и fallback моделей

OpenRouter — основной provider в обычном рабочем процессе AICommander-v2.

Модели не зашиты жёстко в код. Их список задаётся в локальном файле:

```text
config/models.json
```

Для каждой роли можно указать несколько моделей в порядке приоритета. Если первая модель не отвечает, возвращает ошибку, недоступна или упирается в лимит, программа пробует следующую модель из списка.

Точные бесплатные модели OpenRouter могут меняться. Поэтому в репозитории лежит только пример `config/models.example.json`, а актуальные модели нужно проверять в кабинете OpenRouter и указывать у себя в `config/models.json`.

## Premium Review

Premium Review — это дополнительная экспертная проверка результата круга.

Он:

- выключен по умолчанию;
- не обязателен для основной работы;
- запускается после основного бесплатного круга;
- использует OpenAI только если это явно включено в настройках;
- не ломает основной процесс, если нет ключа, токенов, лимитов или доступной модели;
- может быть запущен вручную позже через API или frontend.

Если Premium Review выключен или не настроен, обычные роли всё равно продолжают работать через OpenRouter.

## Структура проекта

```text
backend/
  app/
    main.py                  # REST API, FastAPI app и stdlib fallback-сервер
    config.py                # загрузка .env, настроек и config/models.json
    schemas.py               # лёгкие helpers для схем запросов
    agents/                  # промпты и логика ролей
      manager.py
      architect.py
      designer.py
      coder.py
      reviewer.py
    orchestration/           # выбор ролей, fallback моделей, запуск кругов
      role_router.py
      fallback.py
      round_runner.py
      premium_review.py
    providers/               # OpenRouter и optional OpenAI provider
      base.py
      openrouter.py
      openai.py
    storage/                 # SQLite schema и repository helpers
      db.py
      repositories.py
frontend/
  index.html                 # простой web-интерфейс
  app.js
  style.css
config/
  models.example.json        # пример настройки моделей
.env.example                 # пример переменных окружения
requirements.txt             # зависимости Python
```

В корне `backend/` также остаются старые совместимые модули для предыдущих CLI/integration entrypoints. Основной MVP AI team orchestrator находится в `backend/app/`.

## Установка

### 1. Клонировать репозиторий

```bash
git clone https://github.com/KalyuzhniyKO/AICommander-v2.git
cd AICommander-v2
```

### 2. Создать виртуальное окружение

```bash
python -m venv .venv
```

### 3. Активировать виртуальное окружение

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows:

```bat
.venv\Scripts\activate
```

### 4. Установить зависимости

```bash
pip install -r requirements.txt
```

### 5. Создать `.env`

```bash
cp .env.example .env
```

Откройте `.env` и вставьте свой OpenRouter API key:

```env
OPENROUTER_API_KEY=ваш_openrouter_api_key
```

Не вставляйте ключ в README, frontend-код или публичные файлы.

### 6. Создать локальный файл моделей

```bash
cp config/models.example.json config/models.json
```

После этого отредактируйте `config/models.json` и укажите актуальные модели OpenRouter.

### 7. Запустить backend

```bash
python -m backend.app.main
```

По умолчанию stdlib fallback-сервер запускается на:

```text
http://127.0.0.1:8000
```

Если установлен FastAPI/Uvicorn, можно запустить backend так:

```bash
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

### 8. Открыть frontend

При запуске через FastAPI откройте:

```text
http://127.0.0.1:8000/
```

Если используется stdlib fallback-сервер, он предназначен в первую очередь для проверки API. В этом случае frontend можно открыть отдельно из папки `frontend/`, но удобнее пользоваться FastAPI/Uvicorn.

## Настройка моделей

Скопируйте пример:

```bash
cp config/models.example.json config/models.json
```

Пример структуры `config/models.json`:

```json
{
  "manager": [
    "openrouter/free-model-1",
    "openrouter/free-model-2"
  ],
  "architect": [
    "openrouter/free-model-1"
  ],
  "designer": [
    "openrouter/free-model-1"
  ],
  "coder": [
    "openrouter/free-coder-model-1"
  ],
  "reviewer": [
    "openrouter/free-model-1"
  ],
  "premium_reviewer": [
    "openai/gpt-4.1",
    "openai/gpt-4o"
  ]
}
```

Что означают ключи:

- `manager` — модели для роли Manager;
- `architect` — модели для роли Architect;
- `designer` — модели для роли Designer;
- `coder` — модели для роли Coder;
- `reviewer` — модели для роли Reviewer;
- `premium_reviewer` — модели для необязательного Premium Review.

Значения в примере — placeholders. Они показывают формат, но не гарантируют, что конкретные модели доступны или бесплатны. Список бесплатных моделей OpenRouter может меняться, поэтому проверяйте актуальные model IDs и лимиты в своём кабинете OpenRouter.

## Переменные окружения

Пример `.env`:

```env
OPENROUTER_API_KEY=
OPENAI_API_KEY=
ENABLE_PREMIUM_REVIEW=false
DEFAULT_TIMEOUT_SECONDS=60
MAX_MODEL_RETRIES=1
DATABASE_URL=sqlite:///./aicommander.db
```

Описание переменных:

- `OPENROUTER_API_KEY` — ключ OpenRouter для обычных ролей AI-команды. Для реальных ответов моделей его нужно заполнить.
- `OPENAI_API_KEY` — ключ OpenAI для Premium Review. Не нужен, если Premium Review выключен.
- `ENABLE_PREMIUM_REVIEW` — включает или выключает Premium Review. По умолчанию `false`.
- `DEFAULT_TIMEOUT_SECONDS` — timeout одного запроса к модели в секундах.
- `MAX_MODEL_RETRIES` — количество попыток для каждой модели перед переходом к следующей модели из fallback-списка.
- `DATABASE_URL` — путь к SQLite базе. Значение `sqlite:///./aicommander.db` создаёт базу в корне проекта.

Дополнительно backend поддерживает `OPENROUTER_BASE_URL` и `OPENAI_BASE_URL`, но для обычного запуска их менять не нужно.

## API endpoints

- `POST /tasks` — создать новую задачу. В теле запроса передаётся `description`.
- `GET /tasks/{task_id}` — получить задачу, её круги, ответы ролей и статусы Premium Review.
- `POST /tasks/{task_id}/rounds` — запустить новый круг работы AI-команды для задачи. Можно передать `user_comment`.
- `POST /rounds/{round_id}/roles/{role}/rerun` — повторно запустить одну роль в рамках выбранного круга.
- `POST /rounds/{round_id}/premium-review` — вручную запустить Premium Review для круга.
- `GET /models/status` — посмотреть настроенные и уже наблюдавшиеся модели, их статусы, ошибки и время ответа.
- `GET /health` — проверить, что backend отвечает.

Пример создания задачи:

```bash
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"description":"Сделай план MVP для сервиса управления задачами"}'
```

Пример запуска первого круга:

```bash
curl -X POST http://127.0.0.1:8000/tasks/1/rounds \
  -H 'Content-Type: application/json' \
  -d '{"user_comment":"Начни с простого MVP без лишних функций"}'
```

## Проверка работы

Проверить, что Python-файлы компилируются:

```bash
python -m compileall backend
```

Проверить запуск backend:

```bash
python -m backend.app.main
```

Проверить импорт основного модуля:

```bash
python -c "import backend.app.main; print('ok')"
```

Если API-ключи не настроены, проект не должен падать при запуске. Но реальные ответы моделей получены не будут: роли вернут fallback-сообщения, а ошибки моделей можно будет увидеть в сохранённых данных и через `GET /models/status`.

## Текущий статус проекта

AICommander-v2 сейчас находится в статусе **MVP**. Это рабочая основа, а не финальная версия продукта.

MVP уже показывает ключевую идею: пользователь ставит задачу, система запускает команду ролей, сохраняет результат и ждёт следующего решения пользователя. При этом интерфейс, тесты, настройки и developer experience ещё требуют развития.

## Дальнейший план

Планируемые улучшения:

- улучшить frontend;
- добавить страницу настройки моделей;
- добавить проверку доступности моделей кнопкой;
- добавить импорт и экспорт задач;
- добавить генерацию файлов проекта;
- добавить нормальные автоматические тесты;
- добавить Docker;
- добавить авторизацию позже.

## Правила безопасности

- Не коммитьте `.env`.
- Не вставляйте реальные API keys в README, issues, PR или публичные файлы.
- Не храните секреты во frontend.
- Используйте OpenAI и Premium Review только как опциональный платный этап.
- Для обычного workflow достаточно OpenRouter и корректного `config/models.json`.

## Документация в `docs/`

В папке `docs/` могут быть документы с историческим контекстом и планами развития, например roadmap или branching strategy. README описывает текущее состояние MVP в этой ветке. `docs/BRANCHING_STRATEGY.md` не меняется этой задачей, а `docs/ROADMAP_AI_TEAM_ORCHESTRATOR.md` стоит воспринимать как плановый/исторический документ, если его формулировки говорят о будущей реализации.
