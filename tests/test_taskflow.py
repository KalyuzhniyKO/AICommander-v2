from contextlib import closing, ExitStack
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Barrier

import pytest
from fastapi.testclient import TestClient

from backend.app.taskflow.director import MockDirector
from backend.app.taskflow.models import CreateRun, Command, OwnerDecision, RunSnapshot
from backend.app.taskflow.service import FlowError, Taskflow
from backend.app.storage.db import connect, init_db, SCHEMA


def create(client, max_steps=3):
    task = client.post('/tasks', json={'description': 'Добавить приёмку товара'}).json()
    result = client.post(f"/taskflow/tasks/{task['id']}/runs", json={'idempotency_key': 'create-1', 'max_steps': max_steps})
    assert result.status_code == 200
    return result.json()


def command(client, run, action, key=None, **extra):
    return client.post(f"/taskflow/runs/{run['run_id']}/commands", json={
        'action': action, 'expected_version': run['version'],
        'idempotency_key': key or f"{action}-{run['version']}", **extra,
    })


def decision(client, run, value):
    return client.post(f"/taskflow/runs/{run['run_id']}/owner-decision", json={
        'decision': value, 'expected_version': run['version'], 'idempotency_key': f"owner-{run['version']}",
    })


def finish_roles(client, run):
    run = command(client, run, 'start').json()
    for _ in range(3):
        response = command(client, run, 'step')
        assert response.status_code == 200
        run = response.json()
    return run


def test_offline_handoff_requires_explicit_owner_approval(client):
    run = create(client)
    assert run['status'] == 'planned' and run['version'] == 1
    assert [s['status'] for s in run['stages']] == ['pending'] * 3
    assert decision(client, run, 'approve').status_code == 409
    run = finish_roles(client, run)
    assert run['status'] == 'awaiting_owner' and run['steps_done'] == 3
    requirements, design, plan = run['artifacts']
    assert requirements['content']['objective'] == 'Добавить приёмку товара'
    assert design['content']['requirements'] == requirements['content']
    assert plan['content']['design'] == design['content']
    assert design['input_artifact_ids'] == [requirements['artifact_id']]
    assert plan['input_artifact_ids'] == [requirements['artifact_id'], design['artifact_id']]
    assert all(a['task_id'] == run['task_id'] and a['run_id'] == run['run_id'] for a in run['artifacts'])
    assert all(a['redacted'] and a['simulated'] and a['created_at'] for a in run['artifacts'])
    assert command(client, run, 'step').status_code == 409
    done = decision(client, run, 'approve').json()
    assert done['status'] == 'done' and done['owner_decision'] == 'approved'
    assert done['simulated'] and done['completion_scope'] == 'mock_artifacts_only'
    assert plan['content']['execution'] == 'not_executed'
    assert command(client, done, 'resume').status_code == 409
    assert command(client, done, 'cancel').status_code == 409
    legacy = client.get(f"/tasks/{run['task_id']}").json()
    assert legacy['status'] == 'active' and legacy['rounds'] == []
    listed = client.get(f"/taskflow/tasks/{run['task_id']}/runs").json()
    assert listed == [done]


@pytest.mark.parametrize('action', ['step', 'resume', 'block', 'fail'])
def test_invalid_transition_does_not_mutate(client, action):
    run = create(client)
    response = command(client, run, action)
    assert response.status_code == 409 and response.json()['detail']['code'] == 'invalid_transition'
    assert client.get(f"/taskflow/runs/{run['run_id']}").json() == run


def test_block_failure_resume_and_owner_reject(client):
    run = command(client, create(client), 'start').json()
    run = command(client, run, 'block', reason='Уточнить критерии').json()
    assert run['status'] == 'blocked' and run['stages'][0]['status'] == 'blocked'
    run = command(client, run, 'resume').json()
    run = command(client, run, 'fail', reason='Проверяемый сбой').json()
    assert run['status'] == 'failed' and run['stages'][0]['status'] == 'failed'
    run = command(client, run, 'resume').json()
    for _ in range(3):
        run = command(client, run, 'step').json()
    run = decision(client, run, 'reject').json()
    assert run['status'] == 'blocked' and run['block_code'] == 'owner_rejected'
    assert run['owner_decision'] == 'rejected'
    run = command(client, run, 'resume').json()
    assert run['status'] == 'awaiting_owner' and len(run['artifacts']) == 3
    assert decision(client, run, 'approve').json()['status'] == 'done'


@pytest.mark.parametrize('steps_before_cancel', [0, 1, 3])
def test_cancel_is_terminal_without_deleting_history(client, steps_before_cancel):
    run = create(client)
    if steps_before_cancel:
        run = command(client, run, 'start').json()
        for _ in range(steps_before_cancel):
            run = command(client, run, 'step').json()
    run = command(client, run, 'cancel').json()
    assert run['status'] == 'cancelled' and len(run['artifacts']) == steps_before_cancel
    assert all(s['status'] in {'completed','cancelled'} for s in run['stages'])
    for action in ['start','step','resume']:
        assert command(client, run, action).status_code == 409
    assert decision(client, run, 'approve').status_code == 409


def test_step_limit_cannot_be_bypassed_by_resume_or_new_key(client):
    run = command(client, create(client, 1), 'start').json()
    run = command(client, run, 'step').json()
    assert run['status'] == 'blocked' and run['block_code'] == 'step_limit'
    assert run['steps_done'] == 1 and len(run['artifacts']) == 1
    assert command(client, run, 'resume').json()['detail']['code'] == 'step_limit'
    assert command(client, run, 'step', key='another-step').status_code == 409
    assert client.get(f"/taskflow/runs/{run['run_id']}").json() == run


def test_creation_commands_idempotency_and_optimistic_version(client):
    run = create(client)
    url = f"/taskflow/tasks/{run['task_id']}/runs"
    assert client.post(url, json={'idempotency_key':'create-1','max_steps':3}).json() == run
    assert client.post(url, json={'idempotency_key':'create-1','max_steps':4}).status_code == 409
    started = command(client, run, 'start', key='same-key').json()
    assert command(client, run, 'start', key='same-key').json() == started
    assert command(client, started, 'step', key='same-key').json()['detail']['code'] == 'idempotency_conflict'
    assert command(client, run, 'step', key='stale-key').json()['detail']['code'] == 'stale_version'
    stepped = command(client, started, 'step', key='single-step').json()
    assert command(client, started, 'step', key='single-step').json() == stepped
    assert len(stepped['artifacts']) == 1 and stepped['steps_done'] == 1
    # Replay returns the original response even when the current state has advanced.
    assert command(client, run, 'start', key='same-key').json() == started
    assert client.get(f"/taskflow/runs/{run['run_id']}").json() == stepped


def test_reopen_app_and_connection_preserves_progress_and_replay(client):
    from backend.app import main
    run = command(client, create(client), 'start').json()
    before = run
    run = command(client, run, 'step', key='saved-step').json()
    # A fresh FastAPI object and TestClient, with the same persisted SQLite file.
    from fastapi import FastAPI
    from backend.app.taskflow.api import create_router
    fresh = FastAPI()
    fresh.include_router(create_router(main.repository))
    with TestClient(fresh) as restarted:
        assert restarted.get(f"/taskflow/runs/{run['run_id']}").json() == run
        assert command(restarted, before, 'step', key='saved-step').json() == run
        for _ in range(2):
            run = command(restarted, run, 'step').json()
        assert run['status'] == 'awaiting_owner'


@pytest.mark.parametrize('limit', [0, -1, 101, True, '3'])
def test_invalid_limits_are_rejected(client, limit):
    task = client.post('/tasks', json={'description':'test'}).json()
    assert client.post(f"/taskflow/tasks/{task['id']}/runs", json={'idempotency_key':'key','max_steps':limit}).status_code == 422


def test_unknown_ids_and_owner_cannot_be_spoofed_as_command(client):
    assert client.get('/taskflow/runs/999').status_code == 404
    assert client.get('/taskflow/tasks/999/runs').status_code == 404
    assert client.post('/taskflow/tasks/999/runs', json={'idempotency_key':'k'}).status_code == 404
    run = create(client)
    assert command(client, run, 'approve').status_code == 422
    assert client.post(f"/taskflow/runs/{run['run_id']}/commands", json={'action':'step','expected_version':1,'idempotency_key':'x','director':'hermes'}).status_code == 422


def test_redaction_happens_before_flow_storage(client):
    secret = 'sk-unit-secret-value'
    task = client.post('/tasks', json={'description':f'password="unit pass" api_key=unit-key Bearer unit-bearer {secret}'}).json()
    run = client.post(f"/taskflow/tasks/{task['id']}/runs", json={'idempotency_key':'redact'}).json()
    run = finish_roles(client, run)
    run = decision(client, run, 'reject').json()
    run = command(client, run, 'cancel', reason='token=unit-token').json()
    serialized = json.dumps(run)
    for value in [secret, 'unit pass', 'unit-key', 'unit-bearer', 'unit-token']:
        assert value not in serialized
    from backend.app import main
    with closing(connect(main.settings.database_path)) as conn:
        for table in ['taskflow_runs','taskflow_artifacts','taskflow_events','taskflow_commands']:
            saved = json.dumps([tuple(r) for r in conn.execute(f'SELECT * FROM {table}')])
            assert 'unit-key' not in saved and 'unit-token' not in saved and secret not in saved


@pytest.mark.parametrize('text,secret', [
    ('{"api_key":"private-json"}', 'private-json'),
    ("{'password': 'private password'}", 'private password'),
    ('OPENROUTER_API_KEY=private-env', 'private-env'),
    ('access_token: private-token', 'private-token'),
    ('Authorization: Bearer private-bearer', 'private-bearer'),
])
def test_documented_secret_patterns(text, secret):
    from backend.app.taskflow.redaction import redact
    assert secret not in redact(text)
    assert '[REDACTED]' in redact(text)


def test_director_failure_is_safe_counted_and_replayable(repository):
    class Broken:
        calls = 0
        def produce(self, *args):
            self.calls += 1
            raise RuntimeError('password=must-not-persist')

    task = repository.create_task('test')
    broken = Broken()
    service = Taskflow(repository.conn, broken)
    run = service.create(task['id'], CreateRun(idempotency_key='create',max_steps=4))
    run = service.apply(run.run_id, Command(idempotency_key='start',expected_version=run.version,action='start'))
    request = Command(idempotency_key='step',expected_version=run.version,action='step')
    failed = service.apply(run.run_id, request)
    assert failed.status == 'failed' and failed.steps_done == 1 and failed.artifacts == []
    assert 'must-not-persist' not in failed.model_dump_json()
    assert service.apply(run.run_id, request) == failed and broken.calls == 1
    service.director = MockDirector()
    run = service.apply(run.run_id, Command(idempotency_key='resume',expected_version=failed.version,action='resume'))
    for i in range(3):
        run = service.apply(run.run_id, Command(idempotency_key=f'retry-{i}',expected_version=run.version,action='step'))
    assert run.status == 'awaiting_owner' and run.steps_done == 4


def test_sql_failure_rolls_back_artifact_state_event_and_idempotency(repository):
    service = Taskflow(repository.conn)
    run = service.create(repository.create_task('test')['id'], CreateRun(idempotency_key='create'))
    run = service.apply(run.run_id, Command(idempotency_key='start',expected_version=1,action='start'))
    repository.conn.execute("CREATE TRIGGER fail_event BEFORE INSERT ON taskflow_events WHEN NEW.action='step' BEGIN SELECT RAISE(ABORT,'test rollback'); END")
    request = Command(idempotency_key='step',expected_version=run.version,action='step')
    with pytest.raises(sqlite3.IntegrityError, match='test rollback'):
        service.apply(run.run_id, request)
    assert service.get(run.run_id) == run
    assert repository.conn.execute('SELECT COUNT(*) FROM taskflow_artifacts').fetchone()[0] == 0
    repository.conn.execute('DROP TRIGGER fail_event')
    result = service.apply(run.run_id, request)
    assert len(result.artifacts) == 1 and result.steps_done == 1


@pytest.mark.parametrize('same_key', [True, False])
def test_concurrent_same_version_commits_once(repository, tmp_path, same_key):
    service = Taskflow(repository.conn)
    run = service.create(repository.create_task('test')['id'], CreateRun(idempotency_key='create'))
    run = service.apply(run.run_id, Command(idempotency_key='start',expected_version=1,action='start'))
    class CountingDirector(MockDirector):
        calls = 0
        def produce(self, *args):
            self.calls += 1
            return super().produce(*args)
    director = CountingDirector()
    barrier = Barrier(2)
    with ExitStack() as stack:
        conns = [stack.enter_context(closing(connect(tmp_path / 'repository.db'))) for _ in range(2)]
        def invoke(index):
            barrier.wait(timeout=5)
            request = Command(idempotency_key='race' if same_key else f'race-{index}',expected_version=run.version,action='step')
            try:
                return Taskflow(conns[index], director).apply(run.run_id, request)
            except FlowError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(invoke, range(2)))
    if same_key:
        assert results[0] == results[1]
    else:
        assert sum(r == 'stale_version' for r in results) == 1
    assert director.calls == 1
    assert len(service.get(run.run_id).artifacts) == 1


def test_new_python_process_resumes_saved_run(repository, tmp_path):
    service = Taskflow(repository.conn)
    run = service.create(repository.create_task('restart proof')['id'], CreateRun(idempotency_key='create'))
    run = service.apply(run.run_id, Command(idempotency_key='start',expected_version=1,action='start'))
    request = Command(idempotency_key='step-before-restart',expected_version=run.version,action='step')
    saved = service.apply(run.run_id, request)
    program = '''
from contextlib import closing
from pathlib import Path
import sys
from backend.app.storage.db import connect, init_db
from backend.app.taskflow.service import Taskflow
from backend.app.taskflow.models import Command
sys.stdout.reconfigure(encoding='utf-8')
with closing(connect(Path(sys.argv[1]))) as conn:
    init_db(conn)
    flow = Taskflow(conn)
    replay = flow.apply(int(sys.argv[2]), Command.model_validate_json(sys.argv[3]))
    run = flow.apply(replay.run_id, Command(idempotency_key='after-process-restart', expected_version=replay.version, action='step'))
    print(run.model_dump_json())
'''
    result = subprocess.run([sys.executable, '-c', program, str(tmp_path / 'repository.db'), str(run.run_id), request.model_dump_json()],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, encoding='utf-8', timeout=15)
    assert result.returncode == 0, result.stderr
    restarted = RunSnapshot.model_validate_json(result.stdout)
    assert restarted.steps_done == 2 and restarted.version == saved.version + 1
    assert len(restarted.artifacts) == 2 and restarted.artifacts[0] == saved.artifacts[0]
    assert service.get(run.run_id) == restarted


def test_additive_migration_preserves_old_database_and_is_repeatable(tmp_path):
    with closing(connect(tmp_path / 'old.db')) as conn:
        conn.executescript(SCHEMA)
        conn.execute("INSERT INTO tasks(title,description,status) VALUES('old','original','active')")
        conn.execute("INSERT INTO rounds(task_id,round_number) VALUES(1,1)")
        conn.commit()
        for _ in range(2):
            init_db(conn)
        assert tuple(conn.execute('SELECT title,description,status FROM tasks').fetchone()) == ('old','original','active')
        assert conn.execute('SELECT COUNT(*) FROM rounds').fetchone()[0] == 1
        assert conn.execute('SELECT version FROM taskflow_migrations').fetchall()[0][0] == 1
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
        assert Taskflow(conn).create(1, CreateRun(idempotency_key='existing')).task_id == 1


def test_migration_failure_rolls_back_new_schema(tmp_path, monkeypatch):
    from backend.app.storage import migrations
    with closing(connect(tmp_path / 'bad.db')) as conn:
        conn.executescript(SCHEMA)
        monkeypatch.setattr(migrations, 'STATEMENTS', migrations.STATEMENTS + ('INVALID SQL',))
        with pytest.raises(sqlite3.OperationalError):
            migrations.migrate_taskflow(conn)
        assert conn.execute("SELECT name FROM sqlite_master WHERE name LIKE 'taskflow_%'").fetchall() == []


def test_frozen_ui_contract_and_fixture():
    contracts = Path(__file__).resolve().parents[1] / 'docs/contracts'
    assert json.loads((contracts / 'taskflow-v1.schema.json').read_text(encoding='utf-8')) == RunSnapshot.model_json_schema()
    requests = {model.__name__: model.model_json_schema() for model in (CreateRun, Command, OwnerDecision)}
    assert json.loads((contracts / 'taskflow-v1.requests.json').read_text(encoding='utf-8')) == requests
    example = RunSnapshot.model_validate_json((contracts / 'taskflow-v1.example.json').read_text(encoding='utf-8'))
    assert example.status == 'awaiting_owner' and len(example.artifacts) == 3
