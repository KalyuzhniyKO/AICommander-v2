"""Minimal SQLite schema: tasks, rounds, model status and errors."""
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL UNIQUE);
INSERT OR IGNORE INTO projects(id,name) VALUES(1,'Foundation');
CREATE TABLE IF NOT EXISTS owner_decisions(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,action TEXT NOT NULL,comment TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(task_id) REFERENCES tasks(id));
CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS rounds(id INTEGER PRIMARY KEY AUTOINCREMENT,task_id INTEGER NOT NULL,round_number INTEGER NOT NULL,user_comment TEXT NOT NULL DEFAULT '',selected_roles TEXT NOT NULL DEFAULT '[]',summary TEXT NOT NULL DEFAULT '',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(task_id) REFERENCES tasks(id));
CREATE TABLE IF NOT EXISTS role_outputs(id INTEGER PRIMARY KEY AUTOINCREMENT,round_id INTEGER NOT NULL,role TEXT NOT NULL,output TEXT NOT NULL DEFAULT '',provider TEXT NOT NULL DEFAULT '',model_id TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'failed',response_time_ms INTEGER,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,UNIQUE(round_id,role),FOREIGN KEY(round_id) REFERENCES rounds(id));
CREATE TABLE IF NOT EXISTS model_errors(id INTEGER PRIMARY KEY AUTOINCREMENT,round_id INTEGER,role TEXT NOT NULL,provider TEXT NOT NULL,model_id TEXT NOT NULL,error TEXT NOT NULL,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS model_status(provider TEXT NOT NULL,model_id TEXT NOT NULL,role TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'unknown',last_error TEXT NOT NULL DEFAULT '',last_success_at TEXT,last_failure_at TEXT,response_time_ms INTEGER,PRIMARY KEY(provider,model_id,role));
"""

def connect(db_path:Path)->sqlite3.Connection:
    db_path.parent.mkdir(parents=True,exist_ok=True)
    conn=sqlite3.connect(db_path,check_same_thread=False)
    conn.row_factory=sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db(conn:sqlite3.Connection)->None:
    conn.executescript(SCHEMA)
    if "project_id" not in {row[1] for row in conn.execute("PRAGMA table_info(tasks)")}:
        conn.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER NOT NULL DEFAULT 1 REFERENCES projects(id)")
    conn.commit()
