# Taskflow: операции без вычислений под write lock

[English](OPERATIONS.en.md) · часть [#14](https://github.com/KalyuzhniyKO/AICommander-v3/issues/14)

**Offline-основа #14, не интеграция Hermes Director.** Все штатные step по-прежнему
используют MockDirector; RunSnapshot v1, simulated=true и scope mock_artifacts_only
сохраняются. Здесь нет клиента Hermes/OmniRoute, shell или автоматического фонового
worker. Zorin и модели для реализации/тестов не используются.

## Фазы

1. Короткая write-транзакция проверяет run/version/state/max_steps, namespace ключа
   и отсутствие active-operation. Сохраняются correlation ID, hash ключа/запроса,
   hash случайного worker token, роль и редактированный снимок входов.
2. После commit Director.produce работает **вне SQLite-транзакции**. Другие
   соединения могут писать в БД, запрашивать состояние или отменять процесс.
3. Типизированный редактированный результат (либо безопасный failed flag) отдельно
   сохраняется в result_ready. Неверная схема, исключение или слишком большой
   результат не превращаются в успешный артефакт. Вход/результат ограничены 1 MiB.
4. Короткая финальная транзакция проверяет ownership, version и отмену. Только
   чистый _SavedDirector воспроизводит уже сохранённый результат под lock.
   Артефакт, steps_done, новая версия, event, idempotency response и terminal
   operation state фиксируются вместе. Это не повтор внешнего вызова.

До финальной транзакции RunSnapshot.version/steps_done/артефакты не меняются.
Состояние выполняющейся попытки смотрят отдельно через операции. Один run имеет
не более одной active-operation (running/result_ready/unknown); другой run или
посторонняя запись в БД не блокируются длительным вычислением.

## Повторы и отмена

- Завершённый одинаковый ключ/запрос возвращает сохранённый response как раньше.
- Пока шаг running: повтор получает HTTP 409 operation_pending. Новая команда
  step/block/resume/owner-decision не обходит active-operation. Ключ с другим
  телом/action даёт idempotency_conflict, включая попытку отмены с ключом step.
- Пока result_ready: тот же ключ завершает фиксацию без Director. Это работает и
  после SQL rollback финальной транзакции/нового Python-процесса.
- Отмена с отдельным ключом и актуальной версией разрешена во время вычисления.
  Она сохраняет cancel_requested. Поздний результат discarded, не становится
  артефактом; повтор step возвращает сохранённый cancelled snapshot.
- Отмена не гарантирует, что вычисление ещё не началось, и не возвращает стоимость
  будущего inference. Ошибка чтения/записи результата после вызова может оставить
  неопределённый исход; автоматического повторного запуска нет.

## Crash/recovery

Если процесс погиб до durable result, операция остаётся running. Нельзя считать
возраст записи доказательством смерти worker и автоматически перевыдавать lease.
Нет timer retry, auto-resume, TTL takeover или обещания exactly-once внешней оплаты.

После **внешнего подтверждения остановки worker** доверенный оператор может
использовать backend-интерфейс `StepOperations(flow).mark_unknown(operation_id)`.
Это fencing: прежний worker уже не сможет сохранить результат. Сам операторский
вызов не проверяет PID и не должен применяться к работающему процессу.

`resolve_unknown(operation_id, result=<typed role data>)` импортирует отдельно
проверенный результат. Без result попытка фиксируется failed и учитывается в
steps_done; resume/следующий step требуют отдельной команды и оставшегося лимита.
Неправильная схема отклоняется без изменений. У cancelled/stale run импорт не
добавляет артефакт. Нет HTTP endpoint, через который модель могла бы разрешить
unknown или выдать себе owner approval.

## API и хранение

Защищённый `GET /taskflow/runs/{run_id}/operations` возвращает id, run_id, role,
expected_version, state, cancel_requested и timestamps. Prompt, результат,
worker_hash и idempotency/request hashes не возвращаются. Авторизация совпадает
с остальными /taskflow маршрутами. Контракт RunSnapshot v1 не изменён.

Миграция taskflow 2 добавляет таблицу и partial unique index внутри транзакции.
Повтор безопасен; при ошибке новая схема откатывается, v1/legacy данные остаются.
Откат к старому коду технически оставляет таблицу неиспользуемой, **но** старый код
не знает active-operation: нельзя запускать его с незавершёнными операциями.
Перед downgrade остановить workers и явно разрешить running/result_ready/unknown.

Goal/входы/результаты редактируются по существующим best-effort правилам; это не
универсальное распознавание любых секретов. Не вводите credentials в тексты.
Секретов или адресов серверов в тестовых артефактах нет.

## Доказательства и остаток #14

[QA](qa-issue-14-offline.json). Тесты используют реальные временные SQLite, второй
writer, отдельный Python-процесс с os._exit, задержанный Director и поздний ответ.
Проверены replay, SQL rollback, idempotency namespace, cancellation/fencing,
ручное разрешение unknown, redaction, metadata API и миграция старой v1 БД.

Для полного #14 ещё нужны проверенный transport установленного Hermes, реальные
типизированные role artifacts с честными флагами, error/timeout/cancel semantics
и live-тесты после включения Zorin. Этот PR не закрывает #14 и не меняет цели #15.
