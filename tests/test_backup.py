"""Real temporary app/ledger files and ZIPs only; no production data, SDK or network."""
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
import struct
import subprocess
import sys
from threading import Event, Thread
import time
import zipfile

import pytest

from backend.app.storage import backup
from backend.app.storage.db import connect, init_db
from backend.app.storage.repositories import Repository
from backend.app.taskflow.models import CreateRun, Command
from backend.app.taskflow.service import Taskflow


def app_db(root,name='source.sqlite3'):
    path=root/name
    with closing(connect(path)) as conn:
        init_db(conn)
        task=Repository(conn).create_task('SYNTHETIC: preserve task/artifacts and pending operation')
        flow=Taskflow(conn)
        run=flow.create(task['id'],CreateRun(idempotency_key='fixture-create'))
        run=flow.apply(run.run_id,Command(idempotency_key='start',expected_version=1,action='start'))
        run=flow.apply(run.run_id,Command(idempotency_key='step',expected_version=run.version,action='step'))
        conn.execute("""INSERT INTO taskflow_operations(id,run_id,key_hash,request_hash,expected_version,role,goal,input_json,reason,state,worker_hash)
            VALUES('pending',?,'fixture-key','fixture-request',?,'architect','synthetic',?,'','unknown','fixture-worker')""",(run.run_id,run.version,run.model_dump_json()))
        conn.commit()
    return path


def rows(path):
    with closing(sqlite3.connect(path)) as conn:
        tables=[r[0] for r in conn.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name")]
        return {name:conn.execute('SELECT * FROM "'+name.replace('"','""')+'" ORDER BY rowid').fetchall() for name in tables}


def rewrite_archive(path,change):
    with zipfile.ZipFile(path) as z:contents={i.filename:z.read(i.filename) for i in z.infolist()}
    change(contents)
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED) as z:
        for name,content in contents.items():z.writestr(name,content)


def assert_no_staging(root):
    assert not list(root.glob('.aicommander-*'))


def test_app_backup_verify_restore_preserves_rows_ids_pending_state_and_permissions(tmp_path):
    source=app_db(tmp_path);before=rows(source);snapshot=tmp_path/'fixture.aic-backup.zip'
    result=backup.create_backup(source,snapshot,root=tmp_path)
    assert result['manifest']['metadata']['versions']['taskflow']==[1,2,3]
    assert result['manifest']['metadata']['unresolved_counts']['taskflow_operations.unknown']==1
    assert result['manifest']['metadata']['operator_recovery_required']
    assert backup.verify_backup(snapshot,root=tmp_path)['manifest']==result['manifest']
    restored=tmp_path/'restored.sqlite3'
    report=backup.restore_backup(snapshot,restored,root=tmp_path)
    assert report['workers_must_be_stopped_before_use'] is True
    assert rows(restored)==before==rows(source)
    assert hashlib.sha256(restored.read_bytes()).hexdigest()==report['manifest']['sqlite_sha256']
    if os.name=='posix':
        assert stat.S_IMODE(snapshot.stat().st_mode)==0o600
        assert stat.S_IMODE(restored.stat().st_mode)==0o600
    assert_no_staging(tmp_path)
    if os.environ.get('SQLITE_BACKUP_EXAMPLE'):
        Path(os.environ['SQLITE_BACKUP_EXAMPLE']).write_text(json.dumps({'kind':'synthetic_fixture_only','service_calls':0,'verified':True,'rows_identical_after_restore':True,'manifest':result['manifest']},ensure_ascii=False,indent=2)+'\n')


def test_budget_restore_keeps_unknown_funds_and_one_time_claim(tmp_path):
    from backend.app.budgets.ledger import BudgetLedger, BudgetError
    from backend.app.budgets.models import Policy, Route, Tariff, Request, Outcome
    source=tmp_path/'budget.sqlite3';ledger=BudgetLedger(source,clock_ms=lambda:1000);ledger.initialize()
    ledger.create_account('fixture',Policy(routes=(Route(role='analyst',model_id='fixture/model',tariff=Tariff(input_micro_usd_per_million=0,output_micro_usd_per_million=0)),)))
    ledger.reserve('fixture',Request(operation_id='unknown',role='analyst',model_id='fixture/model',input_tokens=80,output_tokens=20,timeout_seconds=10))
    ledger.claim('unknown');ledger.record('unknown',Outcome(kind='unknown'))
    expected=ledger.report('fixture')
    backup.create_backup(source,'budget.aic-backup.zip',root=tmp_path)
    backup.restore_backup('budget.aic-backup.zip','restored.sqlite3',root=tmp_path)
    restored=BudgetLedger(tmp_path/'restored.sqlite3',clock_ms=lambda:1000)
    assert restored.report('fixture')==expected
    with pytest.raises(BudgetError,match='dispatch_already_claimed'):restored.claim('unknown')
    assert expected['tokens_committed']==100 and expected['reported_cost_micro_usd'] is None


def test_wal_commits_are_included_even_without_checkpoint(tmp_path):
    source=app_db(tmp_path)
    with closing(sqlite3.connect(source)) as writer:
        assert writer.execute('PRAGMA journal_mode=WAL').fetchone()[0]=='wal'
        writer.execute('PRAGMA wal_autocheckpoint=0')
        writer.execute("UPDATE tasks SET description='SYNTHETIC COMMITTED ONLY IN WAL'");writer.commit()
        assert Path(str(source)+'-wal').is_file()
        backup.create_backup(source,'wal.aic-backup.zip',root=tmp_path)
        backup.restore_backup('wal.aic-backup.zip','restored.sqlite3',root=tmp_path)
        with closing(sqlite3.connect(tmp_path/'restored.sqlite3')) as restored:
            assert restored.execute('SELECT description FROM tasks').fetchone()[0]=='SYNTHETIC COMMITTED ONLY IN WAL'
            assert restored.execute('PRAGMA journal_mode').fetchone()[0]=='delete'


def test_wal_snapshot_is_consistent_during_concurrent_atomic_writes(tmp_path):
    source=app_db(tmp_path)
    with closing(sqlite3.connect(source)) as conn:
        conn.execute('PRAGMA journal_mode=WAL');conn.execute('PRAGMA wal_autocheckpoint=0')
        conn.execute('CREATE TABLE cohorts(n INTEGER,part INTEGER,PRIMARY KEY(n,part))')
        conn.execute('CREATE TABLE padding(data BLOB)');conn.execute('INSERT INTO padding VALUES(zeroblob(1000000))');conn.commit()
    started=Event();stop=Event();errors=[]
    def write():
        try:
            with closing(sqlite3.connect(source,timeout=5)) as conn:
                for n in range(100):
                    conn.executemany('INSERT INTO cohorts VALUES(?,?)',[(n,1),(n,2)]);conn.commit();started.set()
                    if stop.wait(.001):break
        except Exception as exc:errors.append(type(exc).__name__)
    thread=Thread(target=write);thread.start()
    try:
        assert started.wait(5)
        backup.create_backup(source,'concurrent.aic-backup.zip',root=tmp_path,timeout_seconds=10)
    finally:stop.set();thread.join(5)
    assert not thread.is_alive() and not errors
    backup.restore_backup('concurrent.aic-backup.zip','restored.sqlite3',root=tmp_path)
    with closing(sqlite3.connect(tmp_path/'restored.sqlite3')) as conn:
        counts=conn.execute('SELECT COUNT(*) FROM cohorts GROUP BY n').fetchall()
        assert counts and all(value==(2,) for value in counts)


@pytest.mark.parametrize('suffix',['','-wal','-shm','-journal'])
def test_restore_never_overwrites_existing_destination_or_sidecar(tmp_path,suffix):
    source=app_db(tmp_path);backup.create_backup(source,'fixture.aic-backup.zip',root=tmp_path)
    protected=tmp_path/('restored.sqlite3'+suffix);protected.write_bytes(b'synthetic keep unchanged')
    with pytest.raises(backup.BackupError,match='destination_exists' if not suffix else 'destination_sidecar_exists'):
        backup.restore_backup('fixture.aic-backup.zip','restored.sqlite3',root=tmp_path)
    assert protected.read_bytes()==b'synthetic keep unchanged'
    assert_no_staging(tmp_path)


def test_create_never_overwrites_archive_or_source(tmp_path):
    source=app_db(tmp_path);expected=source.read_bytes()
    with pytest.raises(backup.BackupError,match='destination_exists'):backup.create_backup(source,source,root=tmp_path)
    target=tmp_path/'existing.aic-backup.zip';target.write_bytes(b'synthetic existing')
    with pytest.raises(backup.BackupError,match='destination_exists'):backup.create_backup(source,target,root=tmp_path)
    assert source.read_bytes()==expected and target.read_bytes()==b'synthetic existing'


@pytest.mark.parametrize('where',['source','output','parent'])
def test_symlinks_are_rejected(tmp_path,where):
    source=app_db(tmp_path);link=tmp_path/'link'
    try:
        if where=='parent':link.symlink_to(tmp_path,target_is_directory=True)
        else:link.symlink_to(source if where=='source' else tmp_path/'missing')
    except OSError:pytest.skip('Host does not allow creating symlinks')
    with pytest.raises(backup.BackupError,match='symlink_not_allowed'):
        backup.create_backup(link if where=='source' else source,link/'snapshot.zip' if where=='parent' else link if where=='output' else 'snapshot.zip',root=tmp_path)
    assert source.is_file()


def test_paths_cannot_escape_root_or_use_home_as_root(tmp_path):
    source=app_db(tmp_path)
    for output in ('../outside.zip',tmp_path.parent/'outside.zip'):
        with pytest.raises(backup.BackupError,match='path_outside_workspace'):backup.create_backup(source,output,root=tmp_path)
    with pytest.raises(backup.BackupError,match='invalid_workspace'):backup.verify_backup('nothing',root=Path.home())


@pytest.mark.parametrize('change,code',[
    (lambda data:data.update({'../escape':b'no'}),'invalid_archive_members'),
    (lambda data:data.pop('state.sqlite3'),'invalid_archive_members'),
    (lambda data:data.update({'state.sqlite3':data['state.sqlite3'][:-1]+b'!'}),'checksum_mismatch'),
    (lambda data:data.update({'manifest.json':b'{"schema_version":"future"}'}),'invalid_manifest'),
    (lambda data:data.update({'manifest.json':b'{"schema_version":"1.0","schema_version":"1.0"}'}),'invalid_manifest'),
])
def test_invalid_archive_does_not_publish_any_restore(tmp_path,change,code):
    source=app_db(tmp_path);snapshot=tmp_path/'fixture.aic-backup.zip';backup.create_backup(source,snapshot,root=tmp_path)
    rewrite_archive(snapshot,change)
    with pytest.raises(backup.BackupError,match=code):backup.restore_backup(snapshot,'restored.sqlite3',root=tmp_path)
    assert not (tmp_path/'restored.sqlite3').exists();assert_no_staging(tmp_path)


def test_manifest_metadata_mismatch_and_future_format_are_rejected(tmp_path):
    source=app_db(tmp_path);snapshot=tmp_path/'fixture.aic-backup.zip';backup.create_backup(source,snapshot,root=tmp_path)
    def change(data):
        manifest=json.loads(data['manifest.json']);manifest['metadata']['row_counts']['model_errors']=False
        data['manifest.json']=json.dumps(manifest).encode()
    rewrite_archive(snapshot,change)
    with pytest.raises(backup.BackupError,match='metadata_mismatch'):backup.verify_backup(snapshot,root=tmp_path)
    def future(data):
        manifest=json.loads(data['manifest.json']);manifest['schema_version']='2.0';data['manifest.json']=json.dumps(manifest).encode()
    rewrite_archive(snapshot,future)
    with pytest.raises(backup.BackupError,match='unsupported_snapshot_version'):backup.verify_backup(snapshot,root=tmp_path)


def test_compressed_archives_and_zip_symlinks_are_not_extracted(tmp_path):
    source=app_db(tmp_path);snapshot=tmp_path/'fixture.aic-backup.zip';backup.create_backup(source,snapshot,root=tmp_path)
    with zipfile.ZipFile(snapshot) as archive:data={i.filename:archive.read(i.filename) for i in archive.infolist()}
    for symbolic in (False,True):
        path=tmp_path/('symlink.zip' if symbolic else 'compressed.zip')
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_STORED if symbolic else zipfile.ZIP_DEFLATED) as archive:
            for name,content in data.items():
                if symbolic and name==backup.DB_NAME:
                    info=zipfile.ZipInfo(name);info.external_attr=(stat.S_IFLNK|0o777)<<16;archive.writestr(info,content)
                else:archive.writestr(name,content)
        with pytest.raises(backup.BackupError,match='invalid_archive_members'):backup.verify_backup(path,root=tmp_path)


def test_database_corruption_foreign_keys_and_unknown_schema_fail_closed(tmp_path):
    corrupt=tmp_path/'corrupt.sqlite3';corrupt.write_bytes(b'SYNTHETIC PRIVATE DATA')
    with pytest.raises(backup.BackupError) as exc:backup.create_backup(corrupt,'invalid.zip',root=tmp_path)
    assert 'SYNTHETIC PRIVATE DATA' not in str(exc.value)
    source=app_db(tmp_path)
    with closing(sqlite3.connect(source)) as conn:
        conn.execute('PRAGMA foreign_keys=OFF');conn.execute("INSERT INTO rounds(task_id,round_number) VALUES(99999,1)");conn.commit()
    with pytest.raises(backup.BackupError,match='foreign_key_check_failed'):backup.create_backup(source,'fk.zip',root=tmp_path)
    with closing(sqlite3.connect(source)) as conn:
        conn.execute('DELETE FROM rounds WHERE task_id=99999');conn.execute('INSERT INTO taskflow_migrations VALUES(99)');conn.commit()
    with pytest.raises(backup.BackupError,match='unsupported_schema'):backup.create_backup(source,'future.zip',root=tmp_path)
    assert not (tmp_path/'invalid.zip').exists() and not (tmp_path/'fk.zip').exists() and not (tmp_path/'future.zip').exists()
    assert_no_staging(tmp_path)


def test_size_timeout_and_publication_race_leave_no_partial_files(tmp_path,monkeypatch):
    source=app_db(tmp_path)
    with pytest.raises(backup.BackupError,match='database_too_large'):backup.create_backup(source,'large.zip',root=tmp_path,max_bytes=1)
    calls=[0]
    def fast_clock():calls[0]+=2;return calls[0]
    with monkeypatch.context() as patch:
        patch.setattr(backup,'_monotonic',fast_clock)
        with pytest.raises(backup.BackupError,match='operation_timeout'):backup.create_backup(source,'timeout.zip',root=tmp_path,timeout_seconds=1)
    original=backup.os.link
    def raced_link(src,dst,**kwargs):
        Path(dst).write_bytes(b'synthetic concurrent winner')
        return original(src,dst,**kwargs)
    monkeypatch.setattr(backup.os,'link',raced_link)
    with pytest.raises(backup.BackupError,match='destination_exists'):backup.create_backup(source,'race.zip',root=tmp_path)
    assert (tmp_path/'race.zip').read_bytes()==b'synthetic concurrent winner'
    assert not (tmp_path/'large.zip').exists() and not (tmp_path/'timeout.zip').exists()
    assert_no_staging(tmp_path)


def test_cli_create_verify_restore_and_safe_json_errors(tmp_path):
    source=app_db(tmp_path)
    def cli(*args):return subprocess.run([sys.executable,'-m','backend.app.storage.backup',*args],capture_output=True,text=True,timeout=15)
    for action,extra in (('create',['--output','cli.aic-backup.zip']),('verify',[]),('restore',['--output','restored.sqlite3'])):
        result=cli(action,'--root',str(tmp_path),'--source',str(source) if action=='create' else 'cli.aic-backup.zip',*extra)
        assert result.returncode==0 and json.loads(result.stdout)['verified']
        assert str(tmp_path) not in result.stdout and not result.stderr
    assert rows(tmp_path/'restored.sqlite3')==rows(source)
    result=cli('verify','--root',str(tmp_path),'--source','cli.aic-backup.zip','--timeout-seconds','synthetic-private-argument')
    assert result.returncode==2 and json.loads(result.stdout)['code']=='invalid_arguments'
    assert 'synthetic-private-argument' not in result.stdout+result.stderr


def test_v2_planning_artifact_and_provenance_survive_restore(tmp_path):
    from backend.app.taskflow.models import HermesCreateRun
    from backend.app.taskflow.ports import ProducedArtifact
    source=app_db(tmp_path)
    class SyntheticDirector:
        binding='synthetic-backup-test'
        def produce_with_context(self,role,goal,inputs,context):
            return ProducedArtifact({'objective':'SYNTHETIC v2 planning','acceptance_criteria':['Preserve exact metadata']},
                {'operation_id':context.operation_id,'model_id':'fixture/model','sdk_commit':'f'*40,
                 'parent_session_id':'fixture-parent','child_session_id':'fixture-child','input_sha256':'0'*64})
    with closing(connect(source)) as conn:
        task=Repository(conn).create_task('SYNTHETIC v2 history')
        flow=Taskflow(conn,SyntheticDirector(),mode='hermes')
        run=flow.create(task['id'],HermesCreateRun(idempotency_key='create-v2'))
        run=flow.apply(run.run_id,Command(idempotency_key='start-v2',expected_version=1,action='start'))
        run=flow.apply(run.run_id,Command(idempotency_key='step-v2',expected_version=2,action='step'))
    assert run.simulated is False and run.artifacts[0].provenance.model_id=='fixture/model'
    backup.create_backup(source,'v2.aic-backup.zip',root=tmp_path)
    backup.restore_backup('v2.aic-backup.zip','restored.sqlite3',root=tmp_path)
    with closing(connect(tmp_path/'restored.sqlite3')) as conn:
        restored=Taskflow(conn,mode='hermes').get(run.run_id)
    assert restored==run and restored.code_executed is False and restored.qa_verified is False


def test_source_hardlink_is_not_treated_as_an_independent_workspace_file(tmp_path):
    source=app_db(tmp_path);alias=tmp_path/'alias.sqlite3'
    try:os.link(source,alias)
    except OSError:pytest.skip('Host filesystem does not support hardlinks')
    with pytest.raises(backup.BackupError,match='invalid_source'):backup.create_backup(alias,'alias.zip',root=tmp_path)
    assert not (tmp_path/'alias.zip').exists() and rows(alias)==rows(source)



def test_oversized_member_directory_is_rejected_before_zipfile_allocation(tmp_path,monkeypatch):
    source=app_db(tmp_path);snapshot=tmp_path/'fixture.aic-backup.zip';backup.create_backup(source,snapshot,root=tmp_path)
    data=bytearray(snapshot.read_bytes());end=list(struct.unpack('<4s4H2LH',data[-22:]));end[4]=65535
    data[-22:]=struct.pack('<4s4H2LH',*end);snapshot.write_bytes(data)
    def forbidden_zip(*args,**kwargs):raise AssertionError('ZipFile must not allocate this directory')
    monkeypatch.setattr(backup.zipfile,'ZipFile',forbidden_zip)
    with pytest.raises(backup.BackupError,match='invalid_archive_members'):backup.restore_backup(snapshot,'restored.sqlite3',root=tmp_path)
    assert not (tmp_path/'restored.sqlite3').exists();assert_no_staging(tmp_path)


def test_restored_saved_result_commits_explicitly_without_new_director_call(tmp_path,monkeypatch):
    from backend.app.taskflow.director import MockDirector
    from backend.app.taskflow.models import Design
    from backend.app.taskflow.operations import StepOperations
    source=app_db(tmp_path)
    with closing(connect(source)) as conn:
        original=Taskflow(conn).get(1)
        result=Design(requirements=original.artifacts[0].content,components=['SYNTHETIC saved design'])
        conn.execute("UPDATE taskflow_operations SET state='result_ready',result_json=? WHERE id='pending'",(result.model_dump_json(),));conn.commit()
    backup.create_backup(source,'saved.aic-backup.zip',root=tmp_path)
    backup.restore_backup('saved.aic-backup.zip','restored.sqlite3',root=tmp_path)
    def forbidden(*args):pytest.fail('Recovery must not call a Director')
    monkeypatch.setattr(MockDirector,'produce',forbidden)
    with closing(connect(tmp_path/'restored.sqlite3')) as conn:
        flow=Taskflow(conn)
        before=flow.get(1)
        assert len(before.artifacts)==1 # Restore itself did not commit or resume anything.
        completed=StepOperations(flow).finish('pending')
        assert completed.version==before.version+1 and completed.artifacts[-1].content==result
        assert StepOperations(flow).finish('pending')==completed
    with closing(connect(source)) as conn:
        assert len(Taskflow(conn).get(1).artifacts)==1 # The original database is independent/unchanged.


def test_stale_snapshot_always_requires_external_reconciliation_even_with_no_live_worker(tmp_path):
    from backend.app.budgets.ledger import BudgetLedger
    from backend.app.budgets.models import Policy, Route, Tariff, Request, Outcome, Usage
    source=tmp_path/'budget.sqlite3';ledger=BudgetLedger(source,clock_ms=lambda:1000);ledger.initialize()
    ledger.create_account('fixture',Policy(routes=(Route(role='analyst',model_id='fixture/model',tariff=Tariff(input_micro_usd_per_million=0,output_micro_usd_per_million=0)),)))
    backup.create_backup(source,'earlier.aic-backup.zip',root=tmp_path)
    ledger.reserve('fixture',Request(operation_id='later',role='analyst',model_id='fixture/model',input_tokens=80,output_tokens=20,timeout_seconds=10))
    # This synthetic receipt happens AFTER the snapshot. No network is sent.
    ledger.claim('later');ledger.record('later',Outcome(kind='completed',http_status=200,usage=Usage(input_tokens=1,output_tokens=1,cost_micro_usd=0)))
    report=backup.restore_backup('earlier.aic-backup.zip','restored.sqlite3',root=tmp_path)
    assert report['external_effects_reconciliation_required'] is True
    assert ledger.report('fixture')['states']=={'completed':1}
    restored=BudgetLedger(tmp_path/'restored.sqlite3',clock_ms=lambda:1000)
    assert restored.report('fixture')['states']=={}
    assert report['manifest']['metadata']['operator_recovery_required'] is False
    # The snapshot has no receipt of the later request: do not infer it is safe to send again.


@pytest.mark.parametrize('suffix',['-wal','-shm','-journal'])
def test_sqlite_source_sidecars_cannot_redirect_reads_outside_workspace(tmp_path,suffix):
    workspace=tmp_path/'workspace';source=app_db(workspace)
    outside=tmp_path/'synthetic-outside';outside.write_bytes(b'SYNTHETIC PRIVATE OUTSIDE DATA')
    sidecar=Path(str(source)+suffix)
    try:sidecar.symlink_to(outside)
    except OSError:pytest.skip('Host does not permit symlinks')
    with pytest.raises(backup.BackupError,match='symlink_not_allowed'):backup.create_backup(source,'blocked.zip',root=workspace)
    assert outside.read_bytes()==b'SYNTHETIC PRIVATE OUTSIDE DATA'
    assert not (workspace/'blocked.zip').exists()
