# Как ведём GitHub-проект AICommander 3.0

[English version](GITHUB_WORKFLOW.en.md) · [Дорожная карта](ROADMAP.md)

## Рабочая ветка
Для v3 изменения идут в отдельных feature-ветках с PR **в `v3-foundation`**. Оригинальная `main` репозитория AICommander-v2 не меняется. Перенос в отдельный AICommander-v3 предусмотрен [#23](https://github.com/KalyuzhniyKO/AICommander-v2/issues/23).

## Шаблоны
- [Сообщение об ошибке](../.github/ISSUE_TEMPLATE/bug_report.md).
- [Новая функция](../.github/ISSUE_TEMPLATE/feature_request.md).
- [Задача Codex](../.github/ISSUE_TEMPLATE/codex_task.md).
- [Pull Request](../.github/pull_request_template.md).
- [Английские шаблоны Issues](templates/ISSUE_TEMPLATES.en.md) и [PR](templates/PULL_REQUEST_TEMPLATE.en.md).

**Особенность GitHub:** формы создания Issue и шаблон PR могут не появиться в интерфейсе, пока они находятся только в ветке `v3-foundation`, а ветка по умолчанию — `main`. До отдельного репозитория v3 их можно использовать вручную; ради форм не меняем оригинальную `main`.

## Порядок работы
1. Создать Issue на русском; добавить ссылку на английский текст, критерии готовности и зависимости.
2. Проверить существующие PR. В частности, [PR #30](https://github.com/KalyuzhniyKO/AICommander-v2/pull/30) пересекается с [#28](https://github.com/KalyuzhniyKO/AICommander-v2/issues/28): не выполнять обе UI-работы параллельно.
3. Не конфликтующие задачи делать в отдельных ветках. При изменениях одних API/таблиц согласовать контракт до начала работы.
4. В каждом PR указать изменённые файлы, результаты **реально выполненных** тестов, ссылку на CI и ограничения, включая отсутствие доступа к Zorin.
5. Состояния Issue и PR различаются. Например, [PR #26](https://github.com/KalyuzhniyKO/AICommander-v2/pull/26) объединён, но [#12](https://github.com/KalyuzhniyKO/AICommander-v2/issues/12) ждёт фактической проверки Hermes/OmniRoute после #11.
6. Merge и деплой — только после проверки владельцем. Не выдавать мок за работающую интеграцию.

**Безопасность:** не включать реальные секреты, токены, приватные адреса, пользовательские данные или дампы production DB в публичные Issues, PR, логи и скриншоты.
