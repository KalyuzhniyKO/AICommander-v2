"""Migration 3 preserves old mock IDs, FK constraints and a durable pending result."""
from contextlib import closing
import json

import pytest

from backend.app.storage.db import connect, SCHEMA
from backend.app.storage import migrations
from backend.app.taskflow.models import Command, Requirements, Design, RunSnapshot
from backend.app.taskflow.service import Taskflow, digest
from backend.app.taskflow.operations import StepOperations


def test_upgrade_v2_with_artifact_and_pending_result_rolls_back_then_recovers(tmp_path,monkeypatch):
    with closing(connect(tmp_path/'old-v2.db')) as conn:
        conn.executescript(SCHEMA)
        conn.execute('CREATE TABLE taskflow_migrations(version INTEGER PRIMARY KEY)')
        for statement in (*migrations.STATEMENTS,*migrations.OPERATION_STATEMENTS):conn.execute(statement)
        conn.executemany('INSERT INTO taskflow_migrations VALUES(?)',[(1,),(2,)]);conn.commit()
        migrations.migrate_panel(conn)
        conn.execute("INSERT INTO tasks(id,title,description) VALUES(1,'old','old goal')")
        conn.execute("INSERT INTO taskflow_runs(id,task_id,status,version,max_steps,steps_done,creation_key_hash,creation_request_hash) VALUES(1,1,'running',3,3,1,'old','old')")
        conn.executemany('INSERT INTO taskflow_stages(run_id,role,position,status) VALUES(1,?,?,?)',[
            ('analyst',0,'completed'),('architect',1,'ready'),('developer',2,'pending')])
        requirements=Requirements(objective='old goal',acceptance_criteria=['old criterion'])
        conn.execute("INSERT INTO taskflow_artifacts(id,run_id,task_id,role,type,content,input_artifact_ids) VALUES(7,1,1,'analyst','requirements',?,'[]')",(requirements.model_dump_json(),))
        command=Command(idempotency_key='pending',expected_version=3,action='step')
        conn.execute("""INSERT INTO taskflow_operations(id,run_id,key_hash,request_hash,expected_version,role,goal,input_json,reason,state,worker_hash,result_json)
            VALUES('pending-op',1,?,?,3,'architect','old goal','{}','','result_ready','old',?)""",
            (digest('pending'),digest({'endpoint':'commands',**command.model_dump()}),Design(requirements=requirements,components=['old design']).model_dump_json()))
        conn.commit()
        original=migrations.migrate_hermes_tables
        def fail_after_copy(connection):
            original(connection)
            raise RuntimeError('fixture migration failure')
        monkeypatch.setattr(migrations,'migrate_hermes_tables',fail_after_copy)
        with pytest.raises(RuntimeError):migrations.migrate_taskflow(conn)
        assert 'director_mode' not in {r[1] for r in conn.execute('PRAGMA table_info(taskflow_runs)')}
        assert conn.execute('SELECT id FROM taskflow_artifacts').fetchone()[0]==7
        assert conn.execute('SELECT state FROM taskflow_operations').fetchone()[0]=='result_ready'
        assert [r[0] for r in conn.execute('SELECT version FROM taskflow_migrations ORDER BY version')]==[1,2]
        monkeypatch.setattr(migrations,'migrate_hermes_tables',original)
        migrations.migrate_taskflow(conn);migrations.migrate_taskflow(conn)
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
        before=Taskflow(conn).get(1)
        assert isinstance(before,RunSnapshot) and before.simulated is True and before.artifacts[0].artifact_id==7
        after=StepOperations(Taskflow(conn)).finish('pending-op')
        assert after.version==4 and after.steps_done==2 and [a.artifact_id for a in after.artifacts]==[7,8]
        assert Taskflow(conn).apply(1,command)==after
        assert conn.execute('PRAGMA foreign_key_check').fetchall()==[]
