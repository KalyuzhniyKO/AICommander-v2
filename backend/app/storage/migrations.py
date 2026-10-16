"""Additive migrations for offline taskflow. Never rewrite legacy task data."""

STATEMENTS = (
    """CREATE TABLE taskflow_runs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL REFERENCES tasks(id),
        status TEXT NOT NULL CHECK(status IN ('planned','running','failed','blocked','awaiting_owner','done','cancelled')),
        version INTEGER NOT NULL DEFAULT 1 CHECK(version >= 1),
        max_steps INTEGER NOT NULL CHECK(max_steps BETWEEN 1 AND 100),
        steps_done INTEGER NOT NULL DEFAULT 0 CHECK(steps_done BETWEEN 0 AND max_steps),
        block_code TEXT CHECK(block_code IN ('manual','step_limit','role_failure','owner_rejected')),
        reason TEXT NOT NULL DEFAULT '',
        owner_decision TEXT NOT NULL DEFAULT 'pending' CHECK(owner_decision IN ('pending','approved','rejected')),
        creation_key_hash TEXT NOT NULL, creation_request_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        UNIQUE(task_id,creation_key_hash), UNIQUE(id,task_id))""",
    """CREATE TABLE taskflow_stages(
        run_id INTEGER NOT NULL REFERENCES taskflow_runs(id),
        role TEXT NOT NULL CHECK(role IN ('analyst','architect','developer')),
        position INTEGER NOT NULL CHECK(position BETWEEN 0 AND 2),
        status TEXT NOT NULL CHECK(status IN ('pending','ready','completed','failed','blocked','cancelled')),
        PRIMARY KEY(run_id,role), UNIQUE(run_id,position))""",
    """CREATE TABLE taskflow_artifacts(
        id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL, task_id INTEGER NOT NULL,
        role TEXT NOT NULL, type TEXT NOT NULL,
        content TEXT NOT NULL, input_artifact_ids TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        UNIQUE(run_id,role),
        FOREIGN KEY(run_id,task_id) REFERENCES taskflow_runs(id,task_id),
        FOREIGN KEY(run_id,role) REFERENCES taskflow_stages(run_id,role),
        CHECK((role='analyst' AND type='requirements') OR (role='architect' AND type='design') OR (role='developer' AND type='plan')))""",
    """CREATE TABLE taskflow_events(
        id INTEGER PRIMARY KEY AUTOINCREMENT, run_id INTEGER NOT NULL REFERENCES taskflow_runs(id),
        action TEXT NOT NULL, from_status TEXT, to_status TEXT NOT NULL,
        version INTEGER NOT NULL, reason TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        UNIQUE(run_id,version))""",
    """CREATE TABLE taskflow_commands(
        run_id INTEGER NOT NULL REFERENCES taskflow_runs(id), key_hash TEXT NOT NULL,
        request_hash TEXT NOT NULL, response_json TEXT NOT NULL,
        PRIMARY KEY(run_id,key_hash))""",
)

OPERATION_STATEMENTS = (
    """CREATE TABLE taskflow_operations(
        id TEXT PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES taskflow_runs(id),
        key_hash TEXT NOT NULL, request_hash TEXT NOT NULL, expected_version INTEGER NOT NULL,
        role TEXT NOT NULL, goal TEXT NOT NULL, input_json TEXT NOT NULL, reason TEXT NOT NULL,
        state TEXT NOT NULL CHECK(state IN ('running','result_ready','unknown','succeeded','failed','discarded')),
        worker_hash TEXT NOT NULL, result_json TEXT, failed INTEGER NOT NULL DEFAULT 0,
        cancel_requested INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        UNIQUE(run_id,key_hash))""",
    """CREATE UNIQUE INDEX taskflow_one_active_operation ON taskflow_operations(run_id)
        WHERE state IN ('running','result_ready','unknown')""",
)


def migrate_taskflow(conn):
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS taskflow_migrations(version INTEGER PRIMARY KEY)")
        if conn.execute("SELECT 1 FROM taskflow_migrations WHERE version=1").fetchone() is None:
            for statement in STATEMENTS:
                conn.execute(statement)
            conn.execute("INSERT INTO taskflow_migrations(version) VALUES(1)")
        if conn.execute("SELECT 1 FROM taskflow_migrations WHERE version=2").fetchone() is None:
            for statement in OPERATION_STATEMENTS:
                conn.execute(statement)
            conn.execute("INSERT INTO taskflow_migrations(version) VALUES(2)")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise


def migrate_panel(conn):
    """Добавить панель атомарно к legacy, taskflow или ранней БД PR #30."""
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("CREATE TABLE IF NOT EXISTS panel_migrations(version INTEGER PRIMARY KEY)")
        if conn.execute("SELECT 1 FROM panel_migrations WHERE version=1").fetchone() is None:
            conn.execute("CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE)")
            conn.execute("INSERT OR IGNORE INTO projects(id,name) VALUES(1,'Foundation')")
            conn.execute("CREATE TABLE IF NOT EXISTS owner_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,action TEXT NOT NULL,comment TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(task_id) REFERENCES tasks(id))")
            if "project_id" not in {r[1] for r in conn.execute("PRAGMA table_info(tasks)")}:
                # SQLite запрещает ненулевой DEFAULT для нового FK в непустой таблице.
                conn.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER REFERENCES projects(id)")
                conn.execute("UPDATE tasks SET project_id=1 WHERE project_id IS NULL")
            conn.execute("CREATE TRIGGER IF NOT EXISTS tasks_default_project AFTER INSERT ON tasks WHEN NEW.project_id IS NULL BEGIN UPDATE tasks SET project_id=1 WHERE id=NEW.id; END")
            conn.execute("INSERT INTO panel_migrations(version) VALUES(1)")
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
