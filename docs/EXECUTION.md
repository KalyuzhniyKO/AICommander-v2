# OFFLINE-C: Git worktree и локальные тесты

[English](EXECUTION.en.md) · [Issue #29](https://github.com/KalyuzhniyKO/AICommander-v2/issues/29)

`backend.app.execution` — независимый модуль для **доверенных одноразовых Git-репозиториев**. Он создаёт отдельную ветку и worktree, показывает фактический diff, запускает заранее разрешённую команду и возвращает её настоящий exit code. Нет подключения к API, taskflow, frontend, Codex CLI, Hermes или OmniRouter. Родительская #15 этим не завершена.

## Пример

В существующем разрешённом каталоге создайте локальный fixture-репозиторий `fixture` с начальным commit и тестовым `check.py`. Не указывайте рабочий или production-репозиторий.

```python
from dataclasses import asdict
from pathlib import Path
import os
import sys
import threading
from backend.app.execution import CommandSpec, OfflineExecutor

root = Path("offline-fixtures").resolve()  # уже существует
# Прямой интерпретатор для stdlib fixture, без Store app alias/venv launcher.
python = str(Path(sys.base_prefix) / "python.exe") if os.name == "nt" else sys.executable
executor = OfflineExecutor(
    allowed_root=root,
    repository=root / "fixture",
    pool=root / "worktrees",
    commands={"check": CommandSpec((python, "-I", "check.py"), timeout_seconds=10)},
    secrets=("synthetic-fixture-secret",),
)
workspace = executor.create("task-29")
executor.write_text(workspace.id, "sample.txt", "changed\n")
before = executor.snapshot(workspace.id)
cancel = threading.Event()  # другой поток может вызвать cancel.set()
report = executor.run(workspace.id, "check", cancel=cancel)
print(asdict(report))
print(asdict(executor.snapshot(workspace.id)))
# Сначала сохранить/рассмотреть результат. По умолчанию изменённые файлы сохраняются.
executor.cleanup(workspace.id, discard_changes=True)  # явное разрешение выбросить fixture
```

В allowlist задаётся **полный неизменяемый argv** с абсолютным путём к исполняемому файлу. Вызов `run` принимает только идентификатор команды и event отмены: произвольных аргументов, shell-строк, переменных окружения и cwd нет. Конфигурацию allowlist утверждает владелец; её нельзя формировать из ответа модели. Для pytest нужна отдельно утверждённая обычная Python-среда с зависимостями; пример использует только stdlib.

## Контракт результата

Объекты — frozen dataclass, сериализуются через `dataclasses.asdict`:

| Объект | Поля |
|---|---|
| Workspace | `id`, `task_id`, `branch`, `path`, `base_commit` |
| Snapshot | `workspace_id`, `base_commit`, `head`, `status`, `diff` |
| CommandResult | `workspace_id`, `command_id`, `outcome`, `exit_code`, `duration_seconds`, `stdout`, `stderr`, `output_truncated` |

`outcome`: `exited`, `timed_out`, `cancelled`, `output_limit`. Успех — **только** `outcome == "exited" and exit_code == 0`. Ненулевой код завершения не заменяется текстом «успешно». При отмене до запуска код `None`; после запуска — фактический код завершения/принудительной остановки. Ошибки политики, запуска и Git дают `ExecutionError` без сырого вывода команд.

`status` — Git porcelain v1 с untracked-файлами. `diff` сравнивает отслеживаемые файлы с сохранённым начальным commit: включает staged, unstaged и уже закоммиченные изменения. Содержимое untracked-файлов не добавляется автоматически, их имена видны в status. Для бинарных файлов Git выводит уведомление, не binary patch. Это очищенный для показа diff, не точный патч для применения.

## Границы и очистка

- Исходный checkout и pool должны быть разными каталогами строго внутри `allowed_root`; pool не может находиться внутри репозитория и наоборот. Принимается первичный checkout с локальным `.git`, без alternate object store, config includes, checkout filters, symlink/submodule в дереве commit. Системные/глобальные Git config и attributes отключены, hooks/fsmonitor/external diff/textconv не запускаются. Git не выполняет fetch, push, clone или submodule update.
- Имена задач ограничены; ветки уникальны: `codex/offline-<task>-<uuid>`. Исходные branch/HEAD/index/рабочие файлы не переключаются и не переписываются. Git закономерно добавляет служебную запись worktree и собственную временную ветку в общий `.git`.
- Управляемые операции проверяют принадлежность каталога, inode/file ID, символические/жёсткие ссылки и Windows junction/reparse points, текущую ветку и Git pointer. Запись запрещает абсолютные пути, `..`, `.git`, Windows ADS и специальные имена. Проверки рассчитаны на эксклюзивное владение fixture/pool: одновременно менять их извне нельзя.
- Менеджер сериализует операции; во время команды очистка/повторный запуск отклоняются как `busy`. Отмена передаётся отдельным `threading.Event`. Результаты не являются очередью или системой идемпотентных заданий: повторный `run` после завершения запускает тест снова.
- `cleanup(id)` удаляет только чистый worktree и его собственную ветку. Изменённые, untracked, ignored файлы, новые commits и временные файлы требуют `discard_changes=True`. Сначала сохраните доказательства QA. Другие worktree не очищаются. Чужой ID, заменённый каталог, другая ветка или ссылка блокируют очистку даже с discard.
- Реестр принадлежности находится в памяти экземпляра. После перезапуска процесса старые worktree **сохраняются для ручной проверки**; новый экземпляр не присваивает себе чужие каталоги. Частичный сбой Git также оставляет данные для проверки, не вызывает рекурсивное удаление неизвестного каталога.

## Процессы, логи и ограничения

Везде `shell=False`, stdin теста закрыт. Batch/shell-файлы и прямые shell-launcher команды отвергаются. Окружение строится заново: не наследует credentials, proxy, PATH, PYTHONPATH или Git overrides; HOME/TEMP ведут в частный каталог. Это не удаляет секреты, уже лежащие в fixture.

Timeout ограничен 300 секундами, размер stdout/stderr — 1 MiB на поток (по умолчанию 64 KiB). Захват ограничен по памяти, с небольшим запасом для редактирования секрета на границе; переполнение останавливает команду. После редактирования вывод обрезается до заданного числа UTF-8 байт. Скрываются явно заданные literal-секреты, Bearer, `sk-...`, типичные password/token/api_key/secret assignments. Произвольные или закодированные секреты автоматически не обнаруживаются; сырые файлы в worktree не редактируются.

Linux/POSIX использует отдельную session/process group; Windows — Job Object с kill-on-close и служебный запуск Python, который присоединяет **себя** к job перед исполнением команды. При timeout, отмене и нормальном выходе уничтожаются оставшиеся обычные дочерние процессы. Windows Store app aliases и связанные venv launchers запрещены: их broker может нарушить наследование Job Object. Для stdlib fixture поддерживается прямой `sys.base_prefix/python.exe`; для реальных зависимостей понадобится проверенная неброкерная среда. Невозможность закрыть pipe считается ошибкой containment.

**Это не security sandbox ОС.** Одобренный тест всё ещё обладает правами пользователя: может обращаться к сети, чужим файлам, Git metadata, запускать broker/daemon или намеренно уходить из POSIX process group. Allowlist и проверки путей защищают интерфейс менеджера, а не произвольный Python-код. Поэтому разрешены только просмотренные локальные fixture-программы. Перед интеграцией с реальным Codex нужны контейнер/VM/OS sandbox с запретом сети, отдельным пользователем, filesystem/resource limits и проверенными контрактами. Автотесты здесь используют только локальные операции; они не вызывают сеть и реальные провайдеры, но не доказывают сетевую изоляцию ОС.

Справка по механике Windows: [Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject). Сторонний исходный код не копировался.

## Проверки

`python -m pytest tests/test_execution.py -q` запускает настоящие Git и Python на временных репозиториях: diff и exit code, сохранность main/исходного index/файлов, traversal и Git metadata, allowlist, timeout/cancel, дочерние процессы, ограничение логов, redaction, очистка ignored/committed файлов, junction/symlink, hooks, filters/includes и submodules. Полная регрессия: `python -m compileall backend`, `python -m pytest -q`, `python -m pip check`. Фактические результаты — [qa-issue-29.json](qa-issue-29.json).
