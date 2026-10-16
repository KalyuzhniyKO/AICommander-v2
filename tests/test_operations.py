"""Real SQLite concurrency/crash tests, pure fixture Director, no network or Zorin."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from threading import Event

import pytest

from backend.app.storage.db import connect, init_db, SCHEMA
from backend.app.taskflow.director import MockDirector
from backend.app.taskflow.models import Command, CreateRun, Requirements
from backend.app.taskflow.operations import StepOperations
from backend.app.taskflow.service import FlowError, Taskflow


def started(repository, director=None, max_steps=3):
    flow = Taskflow(repository.conn, director)
    run = flow.create(repository.create_task('offline requirements')['id'], CreateRun(idempotency_key='create',max_steps=max_steps))
    run = flow.apply(run.run_id, Command(idempotency_key='start',expected_version=run.version,action='start'))
    return flow, run, Command(idempotency_key='step',expected_version=run.version,action='step')


class SlowDirector(MockDirector):
    def __init__(self):
        self.entered, self.release = Event(), Event()
        self.calls = 0

    def produce(self, *args):
        self.calls += 1
        self.entered.set()
        assert self.release.wait(5)
        return super().produce(*args)


def test_director_runs_outside_transaction_and_unrelated_write_succeeds(repository, tmp_path):
    class Probe(MockDirector):
        def produce(self, *args):
            assert not repository.conn.in_transaction
            with closing(connect(tmp_path/'repository.db')) as other:
                other.execute("INSERT INTO projects(name) VALUES('concurrent writer')")
                other.commit()
            return super().produce(*args)
    flow, run, command = started(repository, Probe())
    result = flow.apply(run.run_id, command)
    assert result.steps_done == 1 and result.version == run.version + 1
    assert StepOperations(flow).list_for_run(run.run_id)[0]['state'] == 'succeeded'


def test_running_duplicate_conflict_and_cancel_do_not_duplicate_or_commit_late_result(repository, tmp_path):
    slow = SlowDirector()
    flow, run, request = started(repository)
    with closing(connect(tmp_path/'repository.db')) as worker_conn, ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(Taskflow(worker_conn, slow).apply, run.run_id, request)
        assert slow.entered.wait(5)
        try:
            for cmd, code in [(request,'operation_pending'),
                              (Command(idempotency_key='step',expected_version=run.version,action='step',reason='different'),'idempotency_conflict'),
                              (Command(idempotency_key='other-step',expected_version=run.version,action='step'),'operation_pending'),
                              (Command(idempotency_key='block',expected_version=run.version,action='block'),'operation_pending')]:
                with pytest.raises(FlowError) as exc:
                    flow.apply(run.run_id, cmd)
                assert exc.value.code == code
            assert flow.get(run.run_id) == run  # Reservation does not invent a new artifact/version.
            cancelled = flow.apply(run.run_id, Command(idempotency_key='cancel',expected_version=run.version,action='cancel'))
        finally:
            slow.release.set()
        assert future.result(timeout=5) == cancelled
    assert cancelled.status == 'cancelled' and cancelled.artifacts == []
    assert slow.calls == 1
    assert StepOperations(flow).list_for_run(run.run_id)[0]['state'] == 'discarded'
    assert flow.apply(run.run_id, request) == cancelled


def test_durable_result_survives_commit_failure_without_reinvoking_director(repository):
    class Count(MockDirector):
        calls = 0
        def produce(self, *args):
            self.calls += 1
            return super().produce(*args)
    director = Count()
    flow, run, request = started(repository, director)
    repository.conn.execute("CREATE TRIGGER fail_commit BEFORE INSERT ON taskflow_events WHEN NEW.action='step' BEGIN SELECT RAISE(ABORT,'fixture rollback'); END")
    with pytest.raises(sqlite3.IntegrityError):
        flow.apply(run.run_id, request)
    assert flow.get(run.run_id) == run
    assert StepOperations(flow).list_for_run(run.run_id)[0]['state'] == 'result_ready'
    repository.conn.execute('DROP TRIGGER fail_commit')
    result = flow.apply(run.run_id, request)
    assert len(result.artifacts) == 1 and director.calls == 1
    assert flow.apply(run.run_id, request) == result and director.calls == 1


def test_actual_process_crash_is_unknown_not_automatically_retried(repository, tmp_path):
    flow, run, request = started(repository)
    code = '''
import os,sys
from backend.app.storage.db import connect
from backend.app.taskflow.service import Taskflow
from backend.app.taskflow.models import Command
class Crashed:
    def produce(self,*args):os._exit(23)
conn=connect(__import__('pathlib').Path(sys.argv[1]))
Taskflow(conn,Crashed()).apply(int(sys.argv[2]),Command(idempotency_key='step',expected_version=2,action='step'))
'''
    result = subprocess.run([sys.executable,'-c',code,str(tmp_path/'repository.db'),str(run.run_id)],capture_output=True,text=True,timeout=10)
    assert result.returncode == 23
    operations = StepOperations(flow)
    record = operations.list_for_run(run.run_id)[0]
    assert record['state'] == 'running'
    with pytest.raises(FlowError, match='уже выполняется'):
        flow.apply(run.run_id, request)
    operations.mark_unknown(record['id'])
    with pytest.raises(FlowError) as exc:
        flow.apply(run.run_id, request)
    assert exc.value.code == 'operation_unknown'
    assert flow.get(run.run_id) == run
    failed = operations.resolve_unknown(record['id'])
    assert failed.status == 'failed' and failed.steps_done == 1
    assert flow.apply(run.run_id, request) == failed


def test_recovery_fences_late_worker_and_accepts_only_typed_redacted_result(repository, tmp_path):
    slow = SlowDirector()
    flow, run, request = started(repository)
    ops = StepOperations(flow)
    with closing(connect(tmp_path/'repository.db')) as conn, ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(Taskflow(conn,slow).apply,run.run_id,request)
        assert slow.entered.wait(5)
        record = ops.list_for_run(run.run_id)[0]
        try:
            ops.mark_unknown(record['id'])
            with pytest.raises(FlowError) as exc:
                ops.resolve_unknown(record['id'],result={'wrong':'password=do-not-save'})
            assert exc.value.code == 'invalid_operation_result'
            resolved = ops.resolve_unknown(record['id'],result=Requirements(objective='password=do-not-save',acceptance_criteria=['offline']))
        finally:
            slow.release.set()
        with pytest.raises(FlowError) as exc:
            future.result(timeout=5)
        assert exc.value.code == 'operation_unknown'
    assert len(resolved.artifacts) == 1 and resolved.steps_done == 1
    assert 'do-not-save' not in resolved.model_dump_json()
    assert 'do-not-save' not in repository.conn.execute('SELECT result_json FROM taskflow_operations').fetchone()[0]


def test_operation_namespace_cannot_reuse_step_key_for_cancel(repository, tmp_path):
    slow = SlowDirector()
    flow, run, request = started(repository)
    with closing(connect(tmp_path/'repository.db')) as conn, ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(Taskflow(conn,slow).apply,run.run_id,request)
        assert slow.entered.wait(5)
        try:
            with pytest.raises(FlowError) as exc:
                flow.apply(run.run_id,Command(idempotency_key='step',expected_version=run.version,action='cancel'))
            assert exc.value.code == 'idempotency_conflict'
        finally:
            slow.release.set()
        assert future.result(timeout=5).steps_done == 1


def test_operation_api_omits_inputs_results_and_worker_credentials(client):
    task = client.post('/tasks',json={'description':'password=fixture-secret'}).json()
    run = client.post(f"/taskflow/tasks/{task['id']}/runs",json={'idempotency_key':'create'}).json()
    path = f"/taskflow/runs/{run['run_id']}"
    assert client.get(path+'/operations').json() == []
    for version, action in [(1,'start'),(2,'step')]:
        assert client.post(path+'/commands',json={'idempotency_key':action,'expected_version':version,'action':action}).status_code == 200
    records = client.get(path+'/operations').json()
    assert records[0]['state'] == 'succeeded'
    assert not {'goal','input_json','result_json','worker_hash','key_hash','request_hash'} & records[0].keys()
    assert 'fixture-secret' not in json.dumps(records)
    assert client.get(path+'/operations',headers={'Authorization':''}).status_code == 401
    assert client.get('/taskflow/runs/999999/operations').status_code == 404


def test_version_two_migration_rolls_back_and_preserves_existing_v1(tmp_path, monkeypatch):
    from backend.app.storage import migrations
    with closing(connect(tmp_path/'old-v1.db')) as conn:
        conn.executescript(SCHEMA)
        conn.execute('CREATE TABLE taskflow_migrations(version INTEGER PRIMARY KEY)')
        for statement in migrations.STATEMENTS:conn.execute(statement)
        conn.execute('INSERT INTO taskflow_migrations VALUES(1)');conn.commit()
        original = migrations.OPERATION_STATEMENTS
        monkeypatch.setattr(migrations,'OPERATION_STATEMENTS',original+('INVALID SQL',))
        with pytest.raises(sqlite3.OperationalError):migrations.migrate_taskflow(conn)
        assert conn.execute('SELECT version FROM taskflow_migrations').fetchall()[0][0] == 1
        assert conn.execute("SELECT 1 FROM sqlite_master WHERE name='taskflow_operations'").fetchone() is None
        monkeypatch.setattr(migrations,'OPERATION_STATEMENTS',original)
        init_db(conn);init_db(conn)
        assert [r[0] for r in conn.execute('SELECT version FROM taskflow_migrations ORDER BY version')] == [1,2]
        assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
