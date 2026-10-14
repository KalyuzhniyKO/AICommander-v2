import importlib
import sqlite3

import pytest


def assert_closed(connections):
    assert connections
    for conn in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            conn.execute("SELECT 1")


def test_api_closes_every_connection_on_success_and_error(client, monkeypatch):
    from backend.app import main
    connections = []
    original = main.connect

    def tracked(path):
        conn = original(path)
        connections.append(conn)
        return conn

    monkeypatch.setattr(main, "connect", tracked)
    task = client.post("/tasks", json={"description": "docs"}).json()
    assert client.get(f"/tasks/{task['id']}").status_code == 200
    assert client.get("/models/status").status_code == 200
    assert client.post("/models/check").status_code == 200
    rnd = client.post(f"/tasks/{task['id']}/rounds").json()
    assert client.post(f"/rounds/{rnd['id']}/roles/reviewer/rerun").status_code == 200
    assert client.get("/tasks/99999").status_code == 404
    assert client.post("/tasks", json={"description": " "}).status_code == 400
    assert client.post("/tasks/99999/rounds").status_code == 404
    assert client.post(f"/rounds/{rnd['id']}/roles/invalid/rerun").status_code == 400
    assert len(connections) == 10
    assert_closed(connections)


@pytest.mark.parametrize("failure", ["init_db", "create_task"])
def test_api_closes_connection_when_operation_raises(client, monkeypatch, failure):
    from backend.app import main
    connections = []
    original = main.connect

    def tracked(path):
        conn = original(path)
        connections.append(conn)
        return conn

    def fail(*args):
        raise RuntimeError("test failure")

    monkeypatch.setattr(main, "connect", tracked)
    monkeypatch.setattr(main if failure == "init_db" else main.Repository, failure, fail)
    with pytest.raises(RuntimeError, match="test failure"):
        client.post("/tasks", json={"description": "test"})
    assert_closed(connections)


def test_all_backend_modules_import_without_legacy_bridge():
    import backend
    from pathlib import Path
    for path in Path(backend.__file__).parent.rglob("*.py"):
        parts = path.relative_to(Path(backend.__file__).parent.parent).with_suffix("").parts
        module = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        importlib.import_module(module)
    assert not hasattr(backend, "run_after_judge_and_resolve_next_step")
