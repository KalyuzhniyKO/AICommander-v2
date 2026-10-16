"""Интеграция аутентификации, панели, taskflow и совместимых миграций."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import sqlite3
from threading import Barrier

import pytest

from backend.app.storage.db import SCHEMA, connect, init_db
from backend.app.storage.migrations import migrate_panel, migrate_taskflow
from backend.app.storage.repositories import Repository
from backend.app.taskflow.models import Command, CreateRun
from backend.app.taskflow.service import Taskflow


@pytest.mark.parametrize('method,path', [
    ('get','/taskflow/tasks/1/runs'), ('get','/taskflow/runs/1'),
    ('post','/taskflow/tasks/1/runs'), ('post','/taskflow/runs/1/commands'),
    ('post','/taskflow/runs/1/owner-decision'),
])
def test_taskflow_requires_auth_and_mutations_require_csrf(client, method, path):
    assert getattr(client,method)(path,headers={'Authorization':''}).status_code == 401
    if method == 'post':
        for headers in [{'X-AICommander-Request':''}, {'Origin':'https://evil.example'}]:
            assert client.post(path,json={},headers=headers).status_code == 403


def test_panel_list_uses_latest_flow_without_overwriting_legacy_status(client):
    task=client.post('/tasks',json={'description':'Приёмка товара'}).json()
    path=f"/taskflow/tasks/{task['id']}/runs"
    run=client.post(path,json={'idempotency_key':'first'}).json()
    run=client.post(f"/taskflow/runs/{run['run_id']}/commands",json={'idempotency_key':'start','expected_version':run['version'],'action':'start'}).json()
    listed=client.get('/tasks').json()[0]
    assert listed['flow_status']=='running' and listed['latest_run_id']==run['run_id']
    assert listed['status']=='active'
    latest=client.post(path,json={'idempotency_key':'second'}).json()
    assert client.get('/tasks').json()[0]['latest_run_id']==latest['run_id']
    assert client.get(f"/taskflow/runs/{run['run_id']}").json()['status']=='running'


@pytest.mark.parametrize('layout', ['legacy','taskflow','panel'])
def test_migrations_preserve_all_three_database_layouts(tmp_path,layout):
    with closing(connect(tmp_path/'migration.db')) as conn:
        conn.executescript(SCHEMA)
        if layout=='panel':
            conn.execute('PRAGMA foreign_keys=OFF')
        conn.execute("INSERT INTO tasks(title,description,status) VALUES('Старый проект','Сохранить артефакты','active')")
        conn.execute("INSERT INTO rounds(task_id,round_number,summary) VALUES(1,1,'Исходный раунд')")
        conn.commit()
        snapshot=None
        if layout=='taskflow':
            migrate_taskflow(conn)
            flow=Taskflow(conn)
            snapshot=flow.create(1,CreateRun(idempotency_key='old-run'))
            snapshot=flow.apply(snapshot.run_id,Command(action='start',expected_version=snapshot.version,idempotency_key='old-start'))
            snapshot=flow.apply(snapshot.run_id,Command(action='step',expected_version=snapshot.version,idempotency_key='old-step'))
        if layout=='panel':
            # Схема первоначального PR #30 до появления версионированной миграции.
            conn.execute('CREATE TABLE projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE)')
            conn.execute("INSERT INTO projects(id,name) VALUES(1,'Foundation'),(2,'Склад')")
            conn.execute('ALTER TABLE tasks ADD COLUMN project_id INTEGER NOT NULL DEFAULT 1 REFERENCES projects(id)')
            conn.execute('UPDATE tasks SET project_id=2')
            conn.execute("CREATE TABLE owner_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,action TEXT NOT NULL,comment TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(task_id) REFERENCES tasks(id))")
            conn.execute("INSERT INTO owner_decisions(task_id,action,comment) VALUES(1,'reject','Прежнее решение')")
            conn.commit()
            conn.execute('PRAGMA foreign_keys=ON')
        for _ in range(2):
            init_db(conn)
        task=Repository(conn).get_task(1)
        assert task['description']=='Сохранить артефакты' and task['status']=='active'
        assert task['rounds'][0]['summary']=='Исходный раунд'
        if layout=='panel':
            assert task['project_id']==2 and task['decisions'][0]['comment']=='Прежнее решение'
        if snapshot:
            assert Taskflow(conn).get(snapshot.run_id)==snapshot
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        assert conn.execute('SELECT version FROM panel_migrations').fetchone()[0]==1
        assert conn.execute('SELECT version FROM taskflow_migrations').fetchone()[0]==1


def test_panel_migration_rolls_back_schema_on_failure(tmp_path):
    with closing(connect(tmp_path/'rollback.db')) as conn:
        conn.executescript(SCHEMA)
        conn.set_authorizer(lambda action,*args: sqlite3.SQLITE_DENY if action==sqlite3.SQLITE_ALTER_TABLE else sqlite3.SQLITE_OK)
        with pytest.raises(sqlite3.DatabaseError):
            migrate_panel(conn)
        conn.set_authorizer(None)
        assert conn.execute("SELECT name FROM sqlite_master WHERE name IN ('projects','owner_decisions','panel_migrations')").fetchall()==[]
        assert 'project_id' not in {r[1] for r in conn.execute('PRAGMA table_info(tasks)')}
        init_db(conn)


def test_concurrent_initialization_is_repeatable(tmp_path):
    path=tmp_path/'concurrent.db'
    barrier=Barrier(2)
    def initialize():
        with closing(connect(path)) as conn:
            barrier.wait(timeout=5)
            init_db(conn)
            return [conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ('projects','panel_migrations','taskflow_migrations')]
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert list(pool.map(lambda _: initialize(),range(2)))==[[1,1,3],[1,1,3]]  # taskflow migrations 1 + 2 + 3


def test_taskflow_response_redacts_configured_password(client,monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','otherwise-unrecognizable-credential')
    task=client.post('/tasks',json={'description':'otherwise-unrecognizable-credential'}).json()
    run=client.post(f"/taskflow/tasks/{task['id']}/runs",json={'idempotency_key':'create'}).json()
    for action in ['start','step']:
        run=client.post(f"/taskflow/runs/{run['run_id']}/commands",json={'idempotency_key':action,'expected_version':run['version'],'action':action}).json()
    assert 'otherwise-unrecognizable-credential' not in str(run)
    assert '[REDACTED]' in str(run['artifacts'])


def test_startup_does_not_reset_persisted_taskflow(client):
    from backend.app import main
    task=client.post('/tasks',json={'description':'Продолжить после перезапуска'}).json()
    run=client.post(f"/taskflow/tasks/{task['id']}/runs",json={'idempotency_key':'create'}).json()
    run=client.post(f"/taskflow/runs/{run['run_id']}/commands",json={'idempotency_key':'start','expected_version':run['version'],'action':'start'}).json()
    main.recover_interrupted()
    assert client.get(f"/taskflow/runs/{run['run_id']}").json()==run


def test_validation_errors_do_not_echo_configured_credentials(client,monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','unrecognizable-validation-credential')
    result=client.post('/taskflow/tasks/1/runs',json={'idempotency_key':'valid-key','unexpected':'unrecognizable-validation-credential'})
    assert result.status_code==422
    assert 'unrecognizable-validation-credential' not in result.text
    assert '[REDACTED]' in result.text
