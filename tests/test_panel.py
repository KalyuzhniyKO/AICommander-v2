"""Проверки доступа, решений владельца и реальной конкурентной остановки."""
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Event

import pytest

from backend.app.providers.base import ChatResult, ProviderError


@pytest.mark.parametrize('path', ['/', '/app.js', '/style.css', '/health', '/tasks', '/projects', '/panel/status', '/models/status', '/openapi.json'])
def test_every_resource_requires_auth(client, path):
    response = client.get(path, headers={'Authorization': ''})
    assert response.status_code == 401
    assert 'Basic' in response.headers['www-authenticate']


@pytest.mark.parametrize('password', ['', 'short'])
def test_fail_closed_without_server_password(client, monkeypatch, password):
    monkeypatch.setenv('PANEL_PASSWORD', password)
    assert client.get('/').status_code == 503
    assert client.post('/tasks', json={'description': 'x'}).status_code == 503


def test_wrong_and_malformed_credentials(client):
    for value in ['Basic !!!', 'Bearer token', 'Basic ' + base64.b64encode(b'owner:wrong').decode()]:
        assert client.get('/tasks', headers={'Authorization': value}).status_code == 401


def test_csrf_and_dns_rebinding_are_rejected(client):
    for headers in [{'Origin': 'https://evil.example'}, {'X-AICommander-Request': ''}, {'Origin': 'null'}]:
        assert client.post('/tasks', json={'description':'x'}, headers=headers).status_code == 403
    assert client.get('/', headers={'Host': 'evil.example'}).status_code == 400
    assert client.post('/tasks', json={'description':'x'}, headers={'Origin':'http://127.0.0.1'}).status_code == 200
    assert len(client.get('/tasks').json()) == 1
    assert client.get('/').headers['content-security-policy'].startswith("default-src 'self'")


def test_projects_decisions_and_invalid_transitions(client):
    project = client.post('/projects', json={'name':'Проект склада'}).json()
    assert client.post('/projects', json={'name':'Проект склада'}).status_code == 409
    assert client.post('/tasks', json={'description':'x','project_id':9999}).status_code == 400
    task = client.post('/tasks', json={'description':'Склад','project_id':project['id']}).json()
    path = f"/tasks/{task['id']}"
    assert client.post(path+'/decision', json={'action':'approve'}).status_code == 409
    assert client.post(path+'/decision', json={'action':'stop'}).status_code == 409
    for action in ['bad', [], {}, None]:
        assert client.post(path+'/decision', json={'action':action}).status_code == 400
    rejected = client.post(path+'/decision', json={'action':'reject','comment':'Уточнить'}).json()
    assert rejected['status'] == 'rejected'
    assert rejected['decisions'][0]['comment'] == 'Уточнить'
    assert client.post(path+'/run').status_code == 202
    saved = client.get(path).json()
    assert saved['status'] == 'failed'  # Нет ключа: не изображаем успех.
    assert [d['action'] for d in saved['decisions']] == ['reject', 'retry']
    assert saved['project_id'] == project['id']


def test_success_approval_and_legacy_routes_cannot_bypass(client, monkeypatch, write_models_config):
    from backend.app.orchestration import round_runner
    write_models_config({'manager':['openrouter/test'], 'reviewer':['openrouter/test']})
    class Provider:
        def chat(self, **kwargs):
            return ChatResult('openrouter', 'test', 'Проверенный текст', 1)
    monkeypatch.setattr(round_runner, 'OpenRouterProvider', lambda *a: Provider())
    task = client.post('/tasks', json={'description':'Документация'}).json()
    path = f"/tasks/{task['id']}"
    assert client.post(path+'/run').status_code == 202
    ready = client.get(path).json()
    assert ready['status'] == 'awaiting_owner'
    assert client.post(path+'/decision', json={'action':'approve','comment':'Принимаю текст'}).json()['status'] == 'approved'
    assert client.post(path+'/run').status_code == 409
    assert client.post(path+'/rounds').status_code == 409
    assert client.post(f"/rounds/{ready['rounds'][0]['id']}/roles/manager/rerun").status_code == 409
    assert client.get(path).json()['decisions'][-1]['action'] == 'approve'


def test_stop_during_provider_call_blocks_next_roles_retries_and_duplicate_runs(client, monkeypatch, write_models_config):
    from backend.app.orchestration import round_runner
    from backend.app import main
    from dataclasses import replace
    monkeypatch.setattr(main, 'settings', replace(main.settings, max_model_retries=3))
    write_models_config({'manager':['openrouter/first','openrouter/fallback'], 'reviewer':['openrouter/reviewer']})
    started, release = Event(), Event()
    calls = []
    class Provider:
        def chat(self, **kwargs):
            calls.append(kwargs['model_id'])
            started.set()
            assert release.wait(5)
            raise ProviderError('timeout', 'timeout')
    monkeypatch.setattr(round_runner, 'OpenRouterProvider', lambda *a: Provider())
    task = client.post('/tasks', json={'description':'Документация'}).json()
    path = f"/tasks/{task['id']}"
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.post, path+'/run')
        try:
            assert started.wait(5)
            assert client.get(path).json()['status'] == 'running'
            assert client.post(path+'/run').status_code == 409
            assert client.post(path+'/decision', json={'action':'stop'}).json()['status'] == 'stopping'
            assert client.post(path+'/run').status_code == 409
        finally:
            release.set()
        assert future.result(timeout=5).status_code == 202
    assert client.get(path).json()['status'] == 'stopped'
    assert calls == ['first']
    assert client.get(path).json()['rounds'][0]['role_outputs'] == []
    assert client.post(path+'/decision', json={'action':'approve'}).status_code == 409


def test_redaction_and_unknown_cost(client, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY','private-provider-secret')
    task = client.post('/tasks', json={'description':'private-provider-secret Bearer abc123 sk-example123'}).json()
    assert 'private-provider-secret' not in str(task)
    assert 'abc123' not in str(task)
    assert 'sk-example123' not in str(task)
    assert '[REDACTED]' in task['description']
    status = client.get('/panel/status').json()
    assert status['cost']['total'] is None
    assert status['git_diff'] is None and status['qa'] is None
    source = client.get('/app.js').text
    assert 'localStorage' not in source and 'PANEL_PASSWORD' not in source


def test_existing_database_migration_and_restart_recovery(client):
    from backend.app import main
    with closing(main.connect(main.settings.database_path)) as conn:
        repo = main.Repository(conn)
        task = repo.create_task('Прерванная задача')
        assert repo.transition(task['id'], ('active',), 'running')
    main.recover_interrupted()
    assert client.get(f"/tasks/{task['id']}").json()['status'] == 'failed'
    with closing(main.connect(main.settings.database_path)) as conn:
        main.init_db(conn)
        assert main.Repository(conn).get_task(task['id'])['project_id'] == 1


def test_pre_panel_database_is_migrated_without_losing_history(tmp_path):
    import sqlite3
    from backend.app.storage.db import init_db
    with closing(sqlite3.connect(tmp_path / 'old.db')) as conn:
        conn.executescript("CREATE TABLE tasks(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,description TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'active',created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP); INSERT INTO tasks(title,description) VALUES('Старая задача','Сохранённый текст');")
        init_db(conn)
        init_db(conn)
        assert conn.execute('SELECT title,description,project_id FROM tasks').fetchone() == ('Старая задача', 'Сохранённый текст', 1)
        assert conn.execute('SELECT name FROM projects WHERE id=1').fetchone() == ('Foundation',)
