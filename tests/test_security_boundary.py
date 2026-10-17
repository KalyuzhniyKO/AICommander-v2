"""Negative HTTP boundary checks with synthetic credentials, no live services."""
import base64

import pytest

from backend.app.security import RedactedJSONResponse, redact

SECRET = 'synthetic-boundary-credential-value'


def test_validation_error_never_echoes_secret_json_property_name(client, monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    response = client.post('/taskflow/tasks/1/runs', json={SECRET: 'synthetic'})
    assert response.status_code == 422
    assert SECRET not in response.text
    assert '[REDACTED]' in response.text


def test_redaction_of_nested_keys_preserves_colliding_values(monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    content = {SECRET: ['one'], '[REDACTED]': ['two'], '[REDACTED]_2': ['three']}
    response = RedactedJSONResponse({'nested': content})
    assert SECRET.encode() not in response.body
    import json
    values = json.loads(response.body)['nested'].values()
    assert sorted(item[0] for item in values) == ['one', 'three', 'two']


@pytest.mark.parametrize('token', ['fixture~suffix:tail', 'fixture!suffix@tail', 'fixture%2Ftail'])
def test_bearer_redaction_masks_entire_synthetic_token(token):
    assert token not in redact('Authorization: Bearer ' + token)
    assert 'suffix' not in redact('Authorization: Bearer ' + token)
    assert 'tail' not in redact('Authorization: Bearer ' + token)


@pytest.mark.parametrize('host', [
    'user@localhost', 'localhost/path', 'localhost?query', 'localhost#fragment',
    'localhost:invalid', 'localhost:0', 'localhost:65536', 'localhost:',
])
def test_malformed_local_authorities_are_rejected(client, host):
    assert client.get('/health', headers={'Host': host}).status_code == 400


@pytest.mark.parametrize('host', ['localhost', 'localhost:8000', '127.0.0.1:8000', '[::1]:8000', 'LOCALHOST:8000'])
def test_valid_local_authorities_remain_available(client, host):
    assert client.get('/health', headers={'Host': host}).status_code == 200


@pytest.mark.parametrize('name,values', [
    ('Host', ['localhost', 'evil.invalid']),
    ('Authorization', ['Basic invalid', 'Basic invalid']),
    ('Origin', ['http://127.0.0.1', 'https://evil.invalid']),
    ('X-AICommander-Request', ['1', '0']),
])
def test_duplicate_security_headers_fail_closed(client, name, values):
    headers = [(name, value) for value in values]
    response = client.post('/tasks', json={'description': 'no mutation'}, headers=headers)
    assert response.status_code in {400, 401, 403}
    assert client.get('/tasks').json() == []


@pytest.mark.parametrize('mode', ['auth', 'host', 'csrf', 'password'])
def test_denials_receive_security_headers_without_echoing_credentials(client, monkeypatch, mode):
    kwargs = {}
    if mode == 'auth':
        kwargs['headers'] = {'Authorization': 'Basic ' + base64.b64encode(b'owner:synthetic-wrong').decode()}
    elif mode == 'host':
        kwargs['headers'] = {'Host': 'evil.invalid'}
    elif mode == 'csrf':
        kwargs['headers'] = {'Origin': 'https://evil.invalid'}
    else:
        monkeypatch.setenv('PANEL_PASSWORD', 'short-synthetic')
    response = client.post('/tasks', json={'description': 'no mutation'}, **kwargs)
    assert response.status_code in {400, 401, 403, 503}
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-content-type-options'] == 'nosniff'
    assert response.headers['x-frame-options'] == 'DENY'
    assert "frame-ancestors 'none'" in response.headers['content-security-policy']
    assert 'synthetic-wrong' not in response.text and 'short-synthetic' not in response.text


def test_known_credentials_not_persisted_in_new_free_text(repository, monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    project = repository.create_project('project ' + SECRET)
    task = repository.create_task('task ' + SECRET, project['id'])
    rnd = repository.create_round(task['id'], ['manager'], 'comment ' + SECRET)
    repository.save_role_output(rnd['id'], 'manager', 'output ' + SECRET, 'openrouter', 'fixture', 'completed', 1)
    repository.add_model_error(rnd['id'], 'manager', 'openrouter', 'fixture', 'error ' + SECRET)
    repository.update_model_status('openrouter', 'fixture', 'manager', 'failed', 'error ' + SECRET)
    repository.update_round_summary(rnd['id'], 'summary ' + SECRET)
    repository.transition(task['id'], ('active',), 'rejected', 'reject', 'decision ' + SECRET)
    text = '\n'.join(repository.conn.iterdump())
    assert SECRET not in text
    assert '[REDACTED]' in text
    # Stable routing identifiers and lifecycle are not changed by text masking.
    saved = repository.get_task(task['id'])
    assert saved['status'] == 'rejected'
    assert saved['rounds'][0]['role_outputs'][0]['model_id'] == 'fixture'


def test_known_credentials_not_sent_in_legacy_context(monkeypatch):
    from backend.app.orchestration.round_runner import build_round_context
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    context = build_round_context({'description': SECRET, 'rounds': []}, 'comment ' + SECRET)
    assert SECRET not in context
    assert context.count('[REDACTED]') == 2


def test_taskflow_masks_known_literals_when_reading_old_goal_and_new_reason(repository, monkeypatch):
    from backend.app.taskflow.service import Taskflow
    from backend.app.taskflow.models import CreateRun, Command
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    task = repository.create_task('synthetic task')
    # Simulate a historical row; this change must not silently rewrite old data.
    repository.conn.execute('UPDATE tasks SET description=? WHERE id=?', (SECRET, task['id']))
    repository.conn.commit()
    flow = Taskflow(repository.conn)
    run = flow.create(task['id'], CreateRun(idempotency_key='create'))
    started = flow.apply(run.run_id, Command(action='start', idempotency_key='start', expected_version=run.version, reason=SECRET))
    flow.apply(run.run_id, Command(action='step', idempotency_key='step', expected_version=started.version, reason=SECRET))
    assert repository.conn.execute('SELECT description FROM tasks WHERE id=?', (task['id'],)).fetchone()[0] == SECRET
    for table in ('taskflow_events', 'taskflow_commands', 'taskflow_operations', 'taskflow_artifacts'):
        assert SECRET not in str([tuple(row) for row in repository.conn.execute('SELECT * FROM ' + table)])


def test_tuple_values_are_redacted_before_json_rendering(monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    assert SECRET.encode() not in RedactedJSONResponse({'values': (SECRET,)}).body
