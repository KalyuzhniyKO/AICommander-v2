"""Dummy configured keys without sk-/Bearer syntax must not appear in JSON."""
from backend.app.security import redact


SECRET = 'fixture-omni-credential-without-standard-prefix'


def test_configured_omniroute_key_is_masked_in_json_values(client, monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    assert redact({'nested': ['before '+SECRET+' after']}) == {'nested': ['before [REDACTED] after']}
    response = client.post('/tasks', json={'description': 'do not echo '+SECRET})
    assert response.status_code == 200
    assert SECRET not in response.text and '[REDACTED]' in response.text


def test_configured_omniroute_key_is_masked_in_validation_errors(client, monkeypatch):
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    response = client.post('/taskflow/tasks/1/runs', json={'idempotency_key': 'test', 'unknown_field': SECRET})
    assert response.status_code == 422
    assert SECRET not in response.text and '[REDACTED]' in response.text


def test_longer_credential_is_masked_before_overlapping_prefix(monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'fixture')
    monkeypatch.setenv('OMNIROUTE_API_KEY', SECRET)
    assert redact(SECRET) == '[REDACTED]'
