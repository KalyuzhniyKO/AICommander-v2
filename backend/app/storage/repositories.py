"""Repository helpers for orchestrator persistence."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(row) if row else None


class Repository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create_task(self, description: str) -> dict[str, Any]:
        title = description.strip().splitlines()[0][:120] or "Untitled task"
        cur = self.conn.execute("INSERT INTO tasks(title, description) VALUES(?, ?)", (title, description))
        self.conn.commit()
        return self.get_task(cur.lastrowid) or {}

    def get_task(self, task_id: int) -> dict[str, Any] | None:
        task = row_to_dict(self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())
        if not task:
            return None
        rounds = [dict(row) for row in self.conn.execute("SELECT * FROM rounds WHERE task_id=? ORDER BY round_number", (task_id,))]
        for rnd in rounds:
            rnd["selected_roles"] = json.loads(rnd.get("selected_roles") or "[]")
            rnd["role_outputs"] = [dict(row) for row in self.conn.execute("SELECT * FROM role_outputs WHERE round_id=? ORDER BY id", (rnd["id"],))]
            for out in rnd["role_outputs"]:
                out["model_errors"] = [dict(row) for row in self.conn.execute("SELECT * FROM model_errors WHERE round_id=? AND role=? ORDER BY id", (rnd["id"], out["role"]))]
        task["rounds"] = rounds
        return task

    def get_round(self, round_id: int) -> dict[str, Any] | None:
        row = row_to_dict(self.conn.execute("SELECT * FROM rounds WHERE id=?", (round_id,)).fetchone())
        if not row:
            return None
        row["selected_roles"] = json.loads(row.get("selected_roles") or "[]")
        row["role_outputs"] = [dict(item) for item in self.conn.execute("SELECT * FROM role_outputs WHERE round_id=? ORDER BY id", (round_id,))]
        return row

    def create_round(self, task_id: int, selected_roles: list[str], user_comment: str) -> dict[str, Any]:
        last = self.conn.execute("SELECT COALESCE(MAX(round_number), 0) FROM rounds WHERE task_id=?", (task_id,)).fetchone()[0]
        cur = self.conn.execute(
            "INSERT INTO rounds(task_id, round_number, user_comment, selected_roles) VALUES(?, ?, ?, ?)",
            (task_id, int(last) + 1, user_comment or "", json.dumps(selected_roles, ensure_ascii=False)),
        )
        self.conn.commit()
        return self.get_round(cur.lastrowid) or {}

    def save_role_output(self, round_id: int, role: str, output: str, provider: str, model_id: str, status: str, response_time_ms: int | None) -> None:
        self.conn.execute(
            """INSERT INTO role_outputs(round_id, role, output, provider, model_id, status, response_time_ms)
               VALUES(?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(round_id, role) DO UPDATE SET output=excluded.output, provider=excluded.provider,
               model_id=excluded.model_id, status=excluded.status, response_time_ms=excluded.response_time_ms,
               updated_at=CURRENT_TIMESTAMP""",
            (round_id, role, output, provider, model_id, status, response_time_ms),
        )
        self.conn.commit()

    def add_model_error(self, round_id: int | None, role: str, provider: str, model_id: str, error: str) -> None:
        self.conn.execute(
            "INSERT INTO model_errors(round_id, role, provider, model_id, error) VALUES(?, ?, ?, ?, ?)",
            (round_id, role, provider, model_id, error),
        )
        self.conn.commit()

    def update_model_status(self, provider: str, model_id: str, role: str, status: str, last_error: str = "", response_time_ms: int | None = None) -> None:
        if status == "available":
            self.conn.execute(
                """INSERT INTO model_status(provider, model_id, role, status, last_error, last_success_at, response_time_ms)
                   VALUES(?, ?, ?, ?, '', CURRENT_TIMESTAMP, ?)
                   ON CONFLICT(provider, model_id, role) DO UPDATE SET status=excluded.status, last_error='',
                   last_success_at=CURRENT_TIMESTAMP, response_time_ms=excluded.response_time_ms""",
                (provider, model_id, role, status, response_time_ms),
            )
        else:
            self.conn.execute(
                """INSERT INTO model_status(provider, model_id, role, status, last_error, last_failure_at, response_time_ms)
                   VALUES(?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                   ON CONFLICT(provider, model_id, role) DO UPDATE SET status=excluded.status, last_error=excluded.last_error,
                   last_failure_at=CURRENT_TIMESTAMP, response_time_ms=excluded.response_time_ms""",
                (provider, model_id, role, status, last_error, response_time_ms),
            )
        self.conn.commit()

    def list_model_status(self) -> list[dict[str, Any]]:
        return [dict(row) for row in self.conn.execute("SELECT * FROM model_status ORDER BY role, provider, model_id")]

    def update_round_summary(self, round_id: int, summary: str) -> None:
        self.conn.execute("UPDATE rounds SET summary=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (summary, round_id))
        self.conn.commit()

    def update_premium_review(self, round_id: int, status: str, output: str = "", model: str = "") -> None:
        self.conn.execute(
            "UPDATE rounds SET premium_review_status=?, premium_review_output=?, premium_review_model=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (status, output, model, round_id),
        )
        self.conn.commit()
