# QA runner — offline-подготовка #16

[English](QA_RUNNER.en.md)

Это отдельная библиотека над существующим `OfflineExecutor`, без подключения к
HTTP API, панели, taskflow, Hermes, моделям или GitHub. Работает только с заранее
проверенным кодом в одноразовом локальном репозитории. Полная #16 остаётся
открытой: #15, OS sandbox, независимый Reviewer и сквозной процесс ещё не приняты.

## Что подтверждает отчёт

`QaRunner.run()` выполняет все обязательные проверки через allowlist исполнителя.
Для обычного Python-проекта требуется `pytest`; при явном `django=True` также
обязательны `django_check` и `django_migrations`. Пропустить Django автоматически
или заменить ошибку текстом модели нельзя. Выбор типа проекта и конфигурация —
ответственность владельца, не модели и не входящего HTTP-запроса.

`python_commands()` формирует фиксированные команды Python с `-I -B`: pytest
без автоматической загрузки установленных plugins и cacheprovider; Django `check`
с порогом WARNING и `makemigrations(check=True, dry_run=True, interactive=False)`.
Plugins проекта при необходимости требуют отдельной проверенной конфигурации
владельца. Успех не означает, что покрытие тестами достаточное.

Команды Django импортируют выбранные test settings, затем **до `django.setup()`**
заменяют все настроенные БД единственной SQLite `:memory:` и очищают routers.
`migrate` не запускается. Проверка обнаруживает отсутствующие миграции, но не
доказывает, что существующие миграции успешно применятся или откатятся на целевой БД.
Settings, AppConfig, тесты, conftest и зависимости — исполняемый доверенный код;
импорт settings может иметь побочные эффекты ещё до замены DATABASES. Их нужно
проверить заранее; production settings и пользовательские проекты сюда не передавать.

Официальные контракты: [pytest plugins](https://docs.pytest.org/en/stable/how-to/plugins.html),
[Django commands](https://docs.djangoproject.com/en/5.2/ref/django-admin/).
Django 5.2 установлен только в dev/CI-зависимостях для настоящих fixture-проверок;
новой runtime-зависимости приложения нет.

## Привязка к коду

До/после каждой команды сохраняется и сравнивается evidence: workspace ID,
исходный commit, HEAD, Git status, реальный diff относительно исходного commit,
имена и SHA-256 содержимого tracked-файлов. Это включает staged/committed
изменения и tracked-файлы, скрытые `.gitignore`. Хешируются исходные байты до
редактирования секретов. В отчёт попадают только отредактированные status/diff.
План команд хешируется отдельно; raw argv и настройки в JSON не включаются.

Новые untracked-файлы блокируют запуск: их сначала нужно добавить в index, чтобы
они вошли в настоящий diff. Assume-unchanged/skip-worktree запрещены. Лимиты:
4096 tracked-файлов, суммарно 8 MiB содержимого, ограничения Git output/time
исполнителя. Превышение или невозможность чтения блокируют результат.

Ignored untracked outputs не входят в evidence. Поэтому рабочие входы не должны
поступать через скрытые, внешние файлы или окружение. Изменение и возврат файла
между снимками, конкурентное изменение настроек/окружения/интерпретатора или
злонамеренный код библиотека надёжно не обнаруживает. Runner не является
песочницей, запретом сети или механизмом защиты от враждебного кода. Отдельная
рабочая папка и очищенное окружение не заменяют OS isolation из #15/#20.

## Использование из доверенного локального кода

```python
from pathlib import Path
from backend.app.execution import OfflineExecutor
from backend.app.qa import QaRunner, python_commands, write_report

commands = python_commands(
    '/absolute/path/to/direct/python',  # approved executable, no symlinks
    django_settings='qa_settings',     # omit for a Python-only fixture
)
executor = OfflineExecutor(
    allowed_root=Path('/explicit/fixture-root'),
    repository=Path('/explicit/fixture-root/source'),
    pool=Path('/explicit/fixture-root/worktrees'),
    commands=commands,
    secrets=(),  # known synthetic redaction literals; do not discover credentials
)
workspace = executor.create('qa-example')
# Apply the intended fixture edits; stage new files before QA.
report = QaRunner(executor, django=True).run(workspace.id)
write_report(report, directory=Path('/explicit/fixture-root/evidence'))
# Inspect evidence before explicitly discarding a disposable worktree.
```

Папки root/source/evidence должны существовать; source — одноразовый primary
checkout с `.git` directory, не рабочий репозиторий владельца. Интерпретатор и
зависимости подготовить заранее; runner ничего не устанавливает и не читает `.env`.
На Windows нужен прямой native interpreter, как требует существующий executor.
Без Django/pytest в одобренном интерпретаторе проверка завершится ошибкой.

`write_report()` создаёт только новый `qa-report.json` в явно указанной папке,
без перезаписи и обхода symlink/reparse directories; на POSIX режим 0600.
Экспортировать вне проверяемого worktree. В случае остановки записи может
остаться неполный файл: валидировать JSON и `report_sha256`, не принимать его
за завершённый отчёт. Хеш — проверка целостности, не подпись и не авторизация.
Логи используют best-effort redactor исполнителя; произвольные неизвестные или
закодированные секреты не гарантированно обнаруживаются. Реальные секреты код
получать не должен. Отчёт может содержать приватный код; не публиковать автоматически.

## Готовность и независимый Reviewer

`qa_passed=True` возможен только при неизменном полном evidence и exit code 0
всех обязательных команд, без truncation, timeout/cancel/error. Даже exit 0 с
обрезанным выводом не принимается. Отсутствие pytest-тестов (exit 5) — ошибка.
После обычного падения тестов остальные проверки выполняются для диагностики;
после изменения evidence/ошибки исполнения/отмены оставшиеся проверки не запускаются.
Начальная ошибка policy/Git поднимает `ExecutionError`, отчёт не создаётся.

**`ready_for_pr` всегда False.** `independent_review` и `owner_approval` всегда
`required`. Библиотека не исполняет Reviewer и не ставит готовность в taskflow.
Текст `qa_passed` в сохранённом JSON сам по себе не является разрешением.

Следующий интеграционный шаг должен передать независимому Reviewer реальный
`diff`, исходный/head commits, `evidence_sha256`, `command_plan_sha256`, все checks
и `report_sha256`. Reviewer проверяет требования, security, применимость команд,
покрытие и пропущенные проверки; binary diff требует отдельных доказательств.
Его решение должно ссылаться на точные хеши. Перед продвижением или PR нужно
повторно подтвердить текущий код/план и доверенную идентичность Reviewer, затем
получить решение владельца. Здесь ни такого доверенного transport, ни подписанной
аттестации, ни automatic promotion нет. Отчёты после новых изменений устаревают.

## Воспроизводимые проверки

`python -m pytest -q tests/test_qa.py tests/test_execution.py` запускает реальные
процессы на временных Git-проектах без модели/production. Проверяются успешный и
падающий pytest, отсутствие тестов, настоящие Django checks/миграции, timeout,
output limit, отмена, изменение кода, staging, скрытые index entries, redaction,
экспорт и сохранность исходного репозитория.

[Пример `qa-report.json`](contracts/qa-report-v1-failing.example.json) получен
реальным умышленно падающим pytest на **синтетическом** проекте, не Hermes/Zorin.
Перегенерация:

```bash
QA_FIXTURE_EXAMPLE=docs/contracts/qa-report-v1-failing.example.json python -m pytest -q tests/test_qa.py::test_real_pytest_failure_report_blocks_readiness
```

UUID, commit hashes и duration меняются при каждом прогоне; не сравнивать пример
побайтово. Рабочий JSON по-прежнему называется `qa-report.json`.
