"""Atomic persisted state transitions for the offline mock workflow."""
from contextlib import contextmanager
from hashlib import sha256
import json

from .director import MockDirector, ROLES, TYPES
from .models import CreateRun, Command, OwnerDecision, RunSnapshot, Requirements, Design, Plan
from .redaction import redact


class FlowError(Exception):
    def __init__(self, code, message, status_code=409):
        super().__init__(message)
        self.code, self.status_code = code, status_code


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def redacted_content(value):
    if isinstance(value, str):
        return redact(value)
    if isinstance(value, list):
        return [redacted_content(v) for v in value]
    if isinstance(value, dict):
        return {k: redacted_content(v) for k, v in value.items()}
    return value


class Taskflow:
    def __init__(self, conn, director=None):
        self.conn = conn
        self.director = director if director is not None else MockDirector()

    @contextmanager
    def transaction(self, *, write=False):
        # Each request owns a connection. Director execution is outside this lock;
        # only reservation or pure saved-result commit runs in a write transaction.
        self.conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            yield
            self.conn.commit()
        except BaseException:
            self.conn.rollback()
            raise

    def _run(self, run_id):
        row = self.conn.execute("SELECT * FROM taskflow_runs WHERE id=?", (run_id,)).fetchone()
        if row is None:
            raise FlowError("run_not_found", "Процесс не найден", 404)
        return dict(row)

    def _snapshot(self, run_id):
        row = self._run(run_id)
        stages = [dict(s) for s in self.conn.execute(
            "SELECT role,position,status FROM taskflow_stages WHERE run_id=? ORDER BY position", (run_id,))]
        artifacts = []
        for a in self.conn.execute("SELECT * FROM taskflow_artifacts WHERE run_id=? ORDER BY id", (run_id,)):
            artifacts.append(dict(artifact_id=a['id'], task_id=a['task_id'], run_id=run_id,
                role=a['role'], type=a['type'], content=json.loads(a['content']),
                input_artifact_ids=json.loads(a['input_artifact_ids']), created_at=a['created_at']))
        timeline = [dict(e) for e in self.conn.execute(
            "SELECT id AS event_id,action,from_status,to_status,version,reason,created_at FROM taskflow_events WHERE run_id=? ORDER BY version", (run_id,))]
        fields = ('task_id','status','version','max_steps','steps_done','block_code','reason','owner_decision','created_at','updated_at')
        return RunSnapshot(run_id=run_id, **{k: row[k] for k in fields}, stages=stages, artifacts=artifacts, timeline=timeline)

    def get(self, run_id):
        with self.transaction():
            return self._snapshot(run_id)

    def list_for_task(self, task_id):
        with self.transaction():
            self._task(task_id)
            ids = [r[0] for r in self.conn.execute("SELECT id FROM taskflow_runs WHERE task_id=? ORDER BY id DESC LIMIT 100", (task_id,))]
            return [self._snapshot(i) for i in ids]

    def list_operations(self, run_id):
        from .operations import StepOperations
        return StepOperations(self).list_for_run(run_id)

    def _task(self, task_id):
        task = self.conn.execute("SELECT description FROM tasks WHERE id=?", (task_id,)).fetchone()
        if task is None:
            raise FlowError("task_not_found", "Задача не найдена", 404)
        return task['description']

    def create(self, task_id, request: CreateRun):
        key, fingerprint = digest(request.idempotency_key), digest(request.model_dump())
        with self.transaction(write=True):
            self._task(task_id)
            old = self.conn.execute("SELECT id,creation_request_hash FROM taskflow_runs WHERE task_id=? AND creation_key_hash=?", (task_id,key)).fetchone()
            if old is not None:
                if old['creation_request_hash'] != fingerprint:
                    raise FlowError("idempotency_conflict", "Ключ уже использован с другим запросом")
                return self._snapshot(old['id'])
            cur = self.conn.execute("INSERT INTO taskflow_runs(task_id,status,max_steps,creation_key_hash,creation_request_hash) VALUES(?,'planned',?,?,?)", (task_id,request.max_steps,key,fingerprint))
            run_id = cur.lastrowid
            self.conn.executemany("INSERT INTO taskflow_stages(run_id,role,position,status) VALUES(?,?,?,'pending')", [(run_id,r,i) for i,r in enumerate(ROLES)])
            self._event(run_id, 'create', None, 'planned', 1, '')
            return self._snapshot(run_id)

    def _event(self, run_id, action, previous, status, version, reason):
        self.conn.execute("INSERT INTO taskflow_events(run_id,action,from_status,to_status,version,reason) VALUES(?,?,?,?,?,?)", (run_id,action,previous,status,version,reason))

    def apply(self, run_id, request: Command | OwnerDecision):
        if isinstance(request, Command) and request.action == 'step':
            from .operations import StepOperations
            return StepOperations(self).step(run_id, request)
        with self.transaction(write=True):
            return self._apply_locked(run_id, request)

    def _apply_locked(self, run_id, request):
        owner = isinstance(request, OwnerDecision)
        action = 'owner_' + request.decision if owner else request.action
        fingerprint = digest({'endpoint': 'owner' if owner else 'commands', **request.model_dump()})
        key = digest(request.idempotency_key)
        row = self._run(run_id)
        old = self.conn.execute("SELECT request_hash,response_json FROM taskflow_commands WHERE run_id=? AND key_hash=?", (run_id,key)).fetchone()
        if old is not None:
            if old['request_hash'] != fingerprint:
                raise FlowError("idempotency_conflict", "Ключ уже использован с другим запросом")
            return RunSnapshot.model_validate_json(old['response_json'])
        operation = self.conn.execute("SELECT request_hash FROM taskflow_operations WHERE run_id=? AND key_hash=?", (run_id,key)).fetchone()
        if operation and operation['request_hash'] != fingerprint:
            raise FlowError("idempotency_conflict", "Ключ уже использован с другим запросом")
        if row['version'] != request.expected_version:
            raise FlowError("stale_version", "Версия изменилась; перечитайте состояние процесса")
        if action != 'cancel' and self.conn.execute("SELECT 1 FROM taskflow_operations WHERE run_id=? AND state IN ('running','result_ready','unknown')", (run_id,)).fetchone():
            raise FlowError("operation_pending", "Сначала завершите или разрешите сохранённую операцию")
        return self._commit_action(row, action, redact(request.reason), key, fingerprint)

    def _commit_action(self, row, action, reason, key, fingerprint):
        run_id = row['id']
        before = row['status']
        self._transition(row, action, reason)
        row['version'] += 1
        self.conn.execute("""UPDATE taskflow_runs SET status=?,version=?,steps_done=?,block_code=?,reason=?,owner_decision=?,
                updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?""", tuple(row[k] for k in ('status','version','steps_done','block_code','reason','owner_decision')) + (run_id,))
        if action == 'cancel':
            self.conn.execute("UPDATE taskflow_operations SET cancel_requested=1,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE run_id=? AND state IN ('running','result_ready','unknown')", (run_id,))
        self._event(run_id, action, before, row['status'], row['version'], row['reason'])
        snapshot = self._snapshot(run_id)
        self.conn.execute("INSERT INTO taskflow_commands(run_id,key_hash,request_hash,response_json) VALUES(?,?,?,?)", (run_id,key,fingerprint,snapshot.model_dump_json()))
        return snapshot

    def _stage_status(self, run_id, role, status):
        self.conn.execute("UPDATE taskflow_stages SET status=? WHERE run_id=? AND role=?", (status,run_id,role))

    def _next_role(self, run_id):
        row = self.conn.execute("SELECT role FROM taskflow_stages WHERE run_id=? AND status!='completed' ORDER BY position LIMIT 1", (run_id,)).fetchone()
        return row[0] if row else None

    def _require(self, row, allowed):
        if row['status'] not in allowed:
            raise FlowError("invalid_transition", "Переход недопустим в текущем состоянии")

    def _transition(self, row, action, reason):
        run_id = row['id']
        if action == 'start':
            self._require(row, {'planned'})
            row.update(status='running', reason='', block_code=None)
            self._stage_status(run_id, ROLES[0], 'ready')
        elif action == 'step':
            self._require(row, {'running'})
            self._step(row)
        elif action in {'block', 'fail'}:
            self._require(row, {'running'})
            row.update(status='blocked' if action == 'block' else 'failed', reason=reason,
                block_code='manual' if action == 'block' else 'role_failure')
            self._stage_status(run_id, self._next_role(run_id), row['status'])
        elif action == 'resume':
            self._require(row, {'blocked', 'failed'})
            role = self._next_role(run_id)
            if role is not None and row['steps_done'] >= row['max_steps']:
                raise FlowError('step_limit', 'Лимит шагов исчерпан; продолжение этого процесса запрещено')
            row.update(status='running' if role else 'awaiting_owner', reason='', block_code=None)
            if role:
                self._stage_status(run_id, role, 'ready')
        elif action == 'cancel':
            self._require(row, {'planned', 'running', 'blocked', 'failed', 'awaiting_owner'})
            row.update(status='cancelled', reason=reason, block_code=None)
            self.conn.execute("UPDATE taskflow_stages SET status='cancelled' WHERE run_id=? AND status!='completed'", (run_id,))
        elif action in {'owner_approve', 'owner_reject'}:
            self._require(row, {'awaiting_owner'})
            if action == 'owner_approve':
                row.update(status='done', owner_decision='approved', reason=reason, block_code=None)
            else:
                row.update(status='blocked', owner_decision='rejected', reason=reason, block_code='owner_rejected')
        else:
            raise FlowError('invalid_action', 'Неизвестная команда', 422)

    def _step(self, row):
        run_id = row['id']
        role = self._next_role(run_id)
        if row['steps_done'] >= row['max_steps']:
            raise FlowError('step_limit', 'Лимит шагов исчерпан')
        inputs = self._snapshot(run_id).artifacts
        row['steps_done'] += 1
        try:
            produced = self.director.produce(role, self._task(row['task_id']), inputs)
            content = produced.model_dump() if hasattr(produced, 'model_dump') else produced
            content = (Requirements, Design, Plan)[ROLES.index(role)].model_validate(redacted_content(content))
        except Exception:
            # Do not persist arbitrary exception text, credentials or tracebacks.
            row.update(status='failed', block_code='role_failure', reason='Ошибка Mock Director; реальные действия не выполнялись')
            self._stage_status(run_id, role, 'failed')
            return
        index = ROLES.index(role)
        self.conn.execute("INSERT INTO taskflow_artifacts(run_id,task_id,role,type,content,input_artifact_ids) VALUES(?,?,?,?,?,?)",
            (run_id,row['task_id'],role,TYPES[index],content.model_dump_json(),json.dumps([a.artifact_id for a in inputs])))
        self._stage_status(run_id, role, 'completed')
        role = self._next_role(run_id)
        row.update(reason='', block_code=None)
        if role is None:
            row['status'] = 'awaiting_owner'
        elif row['steps_done'] >= row['max_steps']:
            row.update(status='blocked', block_code='step_limit', reason='Исчерпан лимит шагов')
            self._stage_status(run_id, role, 'blocked')
        else:
            self._stage_status(run_id, role, 'ready')
