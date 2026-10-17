# Локальный аудит Python-зависимостей — #20

[English](DEPENDENCY_AUDIT.en.md)

18.10.2026: проверено фактически установленное macOS/Python 3.13 окружение
разработки и UI, которое использовалось для тестов проекта. Не Zorin и не
переустановка приложения. Инструмент [PyPA pip-audit 2.10.1](https://github.com/pypa/pip-audit)
установлен в отдельную временную venv. Источник advisory — PyPI JSON API;
сервисам передаются публичные названия/версии пакетов, не код/БД/credentials.
Новые runtime dependencies приложения не добавлены.

## Результат и исправление

- До исправления: 35 installed distributions; scanner exit 1. В `pip 26.0`
  найдено 8 advisory entries, соответствующих **4 уникальным PYSEC IDs**.
  Остальные пакеты этого окружения не дали известных findings.
- Обновлён только установщик до [pip 26.2.1](https://pypi.org/project/pip/26.2.1/)
  из PyPI wheel. Версии runtime/dev/UI packages не менялись.
- Повторный строгий аудит тех же 35 distributions: **0 известных findings,
  exit 0**, `pip check` успешен.
- Полные version/ID/fix-version факты, исходный состав и после обновления,
  список packages и заявленная license metadata сохранены в
  [JSON evidence](research/dependency-audit-2026-10-18.json).

Это сведения из базы известных advisory на момент проверки, а не доказательство
отсутствия неизвестных проблем. Например, [GHSA-qwm4-qh6w-59xr](https://github.com/advisories/GHSA-qwm4-qh6w-59xr)
затрагивает pip до 26.2.0 при работе со специально подготовленным package index.
Установщик — инструмент поставки, не HTTP runtime приложения.

## CI

Перед установкой приложения test/UI jobs обновляют pip до `>=26.2.1`.
Отдельный read-only job `Installed Python dependency audit`:

1. Создаёт чистое Ubuntu/Python 3.13 application environment из requirements-ui.
2. Готовит scanner в отдельной `.audit-tool` venv.
3. Передаёт scanner **site-packages приложения**, а не собственные зависимости
   scanner. Проверяет фактически установленные версии с `--strict`, без `--fix`.
4. При findings/неполном сборе/сетевой ошибке job не проходит. `continue-on-error`,
   ignore-vuln allowlist и автоматическое исправление не используются.
5. Сохраняет `dependency-audit.json` как Actions artifact и при ошибке, если отчёт
   был сформирован. Отсутствующий отчёт не считается чистой проверкой.

Это дополнительный job с доступом к публичной базе advisory; обычные pytest
по-прежнему не вызывают модели. Audit не запускает сервер/приложение, deployment,
GitHub write, Hermes или inference. Он проверяет окружение своего job; разные
Python/Windows package selections в других jobs пока не являются его scope.
Прямая зависимость requirements задаёт нижние границы, не воспроизводимый lock
с хешами: будущая установка должна проходить аудит заново.

Для ручного повтора: установить зафиксированный scanner в отдельную venv и
выполнить `python -I -m pip_audit --path /explicit/application/site-packages
--strict --format json --output dependency-audit.json --progress-spinner off`
через interpreter scanner. Не сканировать пользовательские/global environments.
Не использовать `--fix` без отдельного review diff и тестов.

## License inventory и ограничения

JSON содержит metadata установленных Python distributions: имя/версия,
`License-Expression`, первую строку License, license classifiers и объявленные
License-File paths. Это **inventory, не завершённая проверка условий лицензий**.
Например, у части пакетов только общий BSD classifier; у uvloop несколько
license classifiers. Не подменять эти сведения выводом об условиях всей поставки.

Не проверены: содержимое и notices каждого wheel/native binary, bundled
Chromium/другие браузеры, OS/system packages, Hermes/OmniRoute, Zorin environment,
другие платформы и зависимости самого отдельного scanner. Upstream-код не
копировался; scanner используется как внешний инструмент (Apache-2.0).
Полная supply-chain/redistribution проверка и #20 остаются открытыми.
