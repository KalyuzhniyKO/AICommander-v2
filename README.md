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
- endpoint `GET /models/status` для просмотра состояния моделей;
- endpoint `POST /models/check` для ручной проверки моделей из `config/models.json`;
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
      model_check.py
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
- `POST /models/check` — вручную проверить модели из `config/models.json` коротким prompt `Ответь одним словом: OK` и сохранить результат в `model_status`.
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


## Проверка моделей

В frontend есть блок **«Статус моделей»** и кнопка **«Проверить модели»**. Кнопка вызывает:

```bash
curl -X POST http://127.0.0.1:8000/models/check
```

Backend берёт роли и fallback-цепочки из `config/models.json`, отправляет каждой OpenRouter-модели короткий тестовый prompt:

```text
Ответь одним словом: OK
```

Результат сохраняется в таблицу `model_status` и затем отображается через `GET /models/status`:

- `role` — роль, для которой настроена модель;
- `provider` — сейчас для обычных ролей используется `openrouter`;
- `model_id` — идентификатор модели у provider;
- `status` — `available`, `failed` или `unknown`;
- `last_error` — понятная последняя ошибка;
- `last_success_at` — время последнего успешного ответа;
- `last_failure_at` — время последней ошибки;
- `response_time_ms` — время ответа в миллисекундах.

Если `OPENROUTER_API_KEY` отсутствует, endpoint не падает: он возвращает `status: openrouter_key_missing`, понятное сообщение и сохраняет `failed` для проверяемых моделей, если `config/models.json` есть.

Если `config/models.json` отсутствует, endpoint не падает: он возвращает `status: config_missing` и подсказку скопировать пример:

```bash
cp config/models.example.json config/models.json
```

## Типичные ошибки

### Что делать, если нет `OPENROUTER_API_KEY`

Основные роли используют OpenRouter. Без `OPENROUTER_API_KEY` реальные ответы моделей не будут получены, но backend и frontend должны продолжать работать.

Что сделать:

1. Создайте или откройте `.env`.
2. Добавьте ключ OpenRouter:

```env
OPENROUTER_API_KEY=ваш_openrouter_api_key
```

3. Перезапустите backend.
4. Нажмите **«Проверить модели»** во frontend или вызовите `POST /models/check`.

Не вставляйте реальные ключи в README, frontend-код, issues или commits.

### Что делать, если нет `config/models.json`

Создайте локальный файл моделей из примера:

```bash
cp config/models.example.json config/models.json
```

После копирования проверьте, что model IDs актуальны для вашего аккаунта OpenRouter. Примерный файл в репозитории показывает формат, но не гарантирует доступность конкретных бесплатных моделей.

### Что делать, если модель недоступна

Признаки:

- `POST /models/check` вернул `failed`;
- в frontend в колонке `last_error` написано, что модель недоступна или вернула ошибку;
- ответ роли заменён fallback-сообщением.

Что сделать:

1. Проверьте model ID в кабинете OpenRouter.
2. Удалите недоступную модель из `config/models.json` или поставьте ниже в fallback-цепочке.
3. Добавьте другую доступную модель для этой роли.
4. Нажмите **«Проверить модели»** ещё раз.
5. При необходимости нажмите **Rerun role** для конкретной роли в завершённом круге.

### Что делать, если закончились лимиты

Если OpenRouter вернул quota/rate-limit ошибку, статус модели будет `failed`, а `last_error` покажет сообщение про лимиты или rate limit.

Варианты действий:

- проверьте баланс и лимиты в OpenRouter;
- подождите сброса rate limit;
- поставьте другую модель в `config/models.json`;
- уменьшите частоту ручных проверок и перезапусков ролей.

### Ошибки fallback и «все модели для роли упали»

Если все модели роли упали, приложение сохраняет ошибки в `model_errors`, показывает их в карточке роли и пишет локальный fallback-ответ. Это ожидаемое graceful-поведение: круг завершается, а пользователь видит причину проблемы и может перезапустить конкретную роль после исправления ключей, лимитов или `config/models.json`.

## Как вручную запустить Premium Review

Premium Review остаётся опциональным и не обязателен для обычного workflow.

Через frontend:

1. Создайте задачу.
2. Запустите первый круг.
3. После завершения круга нажмите **Run Premium Review**.
4. Посмотрите статус в блоке **Premium Review**.

Через API:

```bash
curl -X POST http://127.0.0.1:8000/rounds/1/premium-review
```

Возможные статусы Premium Review:

- `skipped_disabled` — Premium Review выключен через `ENABLE_PREMIUM_REVIEW=false`;
- `skipped_not_configured` — нет `OPENAI_API_KEY` или не настроены `openai/...` модели в `premium_reviewer`;
- `skipped_quota_or_tokens` — OpenAI вернул ошибку лимитов, оплаты, quota или tokens;
- `skipped_api_error` — OpenAI/API вернул другую ошибку;
- `completed` — Premium Review успешно выполнен.

Чтобы включить Premium Review, явно задайте настройки:

```env
ENABLE_PREMIUM_REVIEW=true
OPENAI_API_KEY=ваш_openai_api_key
```

И добавьте `openai/<model_id>` в `premium_reviewer` в `config/models.json`. OpenAI остаётся необязательным: без этих настроек основной workflow не ломается.

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

### Smoke/manual проверки без ключей

Эти проверки нужны, чтобы убедиться, что приложение gracefully работает без секретов:

```bash
python -m backend.app.main
```

В другом терминале:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/models/status
curl -X POST http://127.0.0.1:8000/models/check
curl -X POST http://127.0.0.1:8000/tasks \
  -H 'Content-Type: application/json' \
  -d '{"description":"Smoke task без API ключей"}'
curl -X POST http://127.0.0.1:8000/tasks/1/rounds \
  -H 'Content-Type: application/json' \
  -d '{"user_comment":"Проверь graceful fallback"}'
curl -X POST http://127.0.0.1:8000/rounds/1/premium-review
```

Ожидаемое поведение без ключей:

- `GET /health` возвращает `status: ok`;
- `GET /models/status` возвращает список моделей или подсказку по конфигурации;
- `POST /models/check` возвращает понятную ошибку про `config/models.json` или `OPENROUTER_API_KEY`, а не traceback;
- запуск круга завершается fallback-ответами и сохранёнными ошибками моделей;
- Premium Review возвращает `skipped_disabled` или `skipped_not_configured`.

Frontend при FastAPI/Uvicorn открывается по адресу `http://127.0.0.1:8000/`.


## Тесты

Автоматические тесты находятся в `tests/` и рассчитаны на запуск без реальных API-ключей. Они проверяют health endpoint, статус и проверку моделей, создание задач, запуск раундов с fallback-ошибками, получение задачи с раундами и опциональный Premium Review без обязательного OpenAI.

Установка dev-зависимостей:

```bash
pip install -r requirements-dev.txt
```

Запуск тестов:

```bash
pytest
```

Тесты намеренно очищают `OPENROUTER_API_KEY`, `OPENAI_API_KEY` и используют временную SQLite-базу, чтобы не ходить во внешние API и не зависеть от локального `.env`.

## Команды разработчика

В репозитории есть `Makefile` с простыми командами:

```bash
make install  # pip install -r requirements.txt
make dev      # python -m backend.app.main
make test     # pytest
make smoke    # compileall + import backend.app.main
```

Если `make` недоступен, эти команды можно выполнить вручную:

```bash
pip install -r requirements.txt
python -m backend.app.main
pytest
python -m compileall backend
python -c "import backend.app.main; print('ok')"
```

## Проверка конфигурации моделей

Локальный файл `config/models.json` не коммитится и должен быть создан вручную из примера:

```bash
cp config/models.example.json config/models.json
```

Для проверки моделей используйте UI-кнопку проверки или API:

```bash
curl -X POST http://127.0.0.1:8000/models/check
```

Backend возвращает понятные статусы вместо traceback:

- `config_missing` — `config/models.json` отсутствует;
- `config_empty` — файл пустой или не содержит ролей;
- `config_invalid` — JSON нельзя разобрать или структура неверная;
- `role_models_empty` — роль есть, но её fallback-список пустой;
- `provider_prefix_missing` — модель указана без `openrouter/` или `openai/`;
- `provider_unknown` — указан неподдерживаемый provider;
- `openrouter_key_missing` — конфиг прочитан, но нет `OPENROUTER_API_KEY` для реальной проверки OpenRouter.

`GET /models/status` можно открывать даже без `config/models.json`: endpoint должен вернуть текущее состояние и подсказку, а не падать.

## Примеры model config

Доступные примеры:

- `config/models.example.json` — базовый пример структуры fallback-цепочек;
- `config/models.free.example.json` — пример формата для подбора моделей, которые пользователь считает подходящими по цене/лимитам на момент настройки;
- `config/README.md` — пояснения по выбору моделей, fallback-порядку и действиям при недоступности модели.

Важно: JSON-примеры не гарантируют, что конкретные model IDs бесплатны или доступны. Бесплатные модели OpenRouter могут меняться, поэтому актуальные model IDs, цены и лимиты нужно брать в OpenRouter перед запуском.

## Как понять, что проект готов к запуску

Минимальный чеклист перед разработкой или локальным использованием:

1. Установлены зависимости: `pip install -r requirements.txt` или `make install`.
2. Smoke-проверка проходит: `make smoke`.
3. Автотесты проходят: `make test` или `pytest`.
4. `GET /health` возвращает `status: ok`.
5. `config/models.json` создан из примера и содержит model refs в формате `provider/model_id`.
6. Для реальных ответов обычных ролей задан `OPENROUTER_API_KEY`.
7. Premium Review включается только намеренно через `ENABLE_PREMIUM_REVIEW=true`, `OPENAI_API_KEY` и `openai/<model_id>` в `premium_reviewer`.
8. `.env`, локальные `.db`, кеши и временные файлы не попадают в git.

Без API-ключей backend всё равно должен стартовать, создавать задачи и сохранять fallback/errors; просто реальные ответы моделей не будут получены.

## Текущий статус проекта

AICommander-v2 сейчас находится в статусе **MVP**. Это рабочая основа, а не финальная версия продукта.

MVP уже показывает ключевую идею: пользователь ставит задачу, система запускает команду ролей, сохраняет результат и ждёт следующего решения пользователя. При этом интерфейс, тесты, настройки и developer experience ещё требуют развития.

## Дальнейший план

Планируемые улучшения:

- добавить страницу настройки моделей;
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
