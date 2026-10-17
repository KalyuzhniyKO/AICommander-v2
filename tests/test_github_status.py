"""Injected HTTP fixtures only: application tests never call public GitHub."""
from copy import deepcopy
import io
import json
import urllib.error

import pytest

from backend.app.github_status import PublicGitHubStatus

SHA = 'a' * 40
REPO = 'fixture/repository'


def payloads():
    pull = {'number': 7, 'state': 'open', 'draft': True, 'merged': False,
            'head': {'sha': SHA}, 'base': {'ref': 'main', 'repo': {'full_name': REPO}}}
    checks = {'total_count': 1, 'check_runs': [{'head_sha': SHA, 'name': 'tests', 'status': 'completed', 'conclusion': 'success', 'app': {'id': 15368}}]}
    status = {'sha': SHA, 'total_count': 0, 'statuses': []}
    return [pull, checks, status, deepcopy(pull)]


class Response(io.BytesIO):
    status = 200
    def __init__(self, value, headers=None):
        super().__init__(value if isinstance(value, bytes) else json.dumps(value).encode())
        self.headers = headers or {}


class Opener:
    def __init__(self, values):
        self.values, self.calls = list(values), []
    def open(self, request, timeout):
        self.calls.append((request, timeout))
        value = self.values.pop(0)
        if isinstance(value, Exception):
            raise value
        return value if isinstance(value, Response) else Response(value)


def client(values):
    from unittest.mock import patch
    opener = Opener(values)
    # Inject before construction: fixtures must not initialize a real HTTPS
    # context (including repeated Windows system-certificate enumeration).
    with patch('urllib.request.build_opener', return_value=opener):
        return PublicGitHubStatus(REPO, expected_checks=('tests',), expected_app_id=15368)


def test_exact_head_snapshot_is_read_only_and_never_merge_permission(monkeypatch):
    monkeypatch.setenv('GH_TOKEN', 'synthetic-must-not-load')
    reader = client(payloads())
    result = reader.snapshot(7)
    assert result['state'] == 'passed' and result['complete']
    assert result['all_expected_checks_passed'] and not result['ready_for_merge']
    assert result['draft'] and not result['merged']
    assert len(reader._opener.calls) == 4
    paths = [r.full_url for r, _ in reader._opener.calls]
    assert paths[0] == paths[-1] == 'https://api.github.com/repos/fixture/repository/pulls/7'
    assert all(SHA in url for url in paths[1:3])
    for request, timeout in reader._opener.calls:
        assert request.get_method() == 'GET' and request.data is None
        assert request.get_header('Authorization') is None
        assert 'synthetic-must-not-load' not in str(request.headers)
        assert timeout == 10


@pytest.mark.parametrize('field,value', [('conclusion', 'failure'), ('conclusion', 'skipped'), ('conclusion', 'neutral'), ('conclusion', None), ('status', 'queued')])
def test_failed_pending_skipped_or_neutral_checks_not_green(field, value):
    values = payloads()
    values[1]['check_runs'][0][field] = value
    result = client(values).snapshot(7)
    assert result['state'] == 'not_passed' and not result['all_expected_checks_passed']


@pytest.mark.parametrize('kind', ['head_moved', 'base_changed', 'draft_changed', 'wrong_head', 'foreign_app', 'missing', 'legacy_failure', 'pagination_count', 'pagination_link'])
def test_incomplete_stale_or_untrusted_evidence_never_passes(kind):
    values = payloads()
    if kind == 'head_moved': values[3]['head']['sha'] = 'b' * 40
    elif kind == 'base_changed': values[3]['base']['ref'] = 'other'
    elif kind == 'draft_changed': values[3]['draft'] = False
    elif kind == 'wrong_head': values[1]['check_runs'][0]['head_sha'] = 'b' * 40
    elif kind == 'foreign_app': values[1]['check_runs'][0]['app']['id'] = 999
    elif kind == 'missing': values[1] = {'total_count': 0, 'check_runs': []}
    elif kind == 'legacy_failure': values[2].update(total_count=1, statuses=[{'context':'legacy', 'state':'failure'}])
    elif kind == 'pagination_count': values[1]['total_count'] = 101
    elif kind == 'pagination_link': values[1] = Response(values[1], {'Link':'<https://untrusted.invalid>; rel="next"'})
    result = client(values).snapshot(7)
    assert result['state'] != 'passed' and not result['all_expected_checks_passed']
    assert not result['ready_for_merge']


@pytest.mark.parametrize('raw', [b'not json', b'[]', b'{"number":7,"number":8}', b'x'*(1024*1024+1)])
def test_invalid_duplicate_or_oversized_payload_is_safe_unavailable(raw):
    reader = client([raw])
    result = reader.snapshot(7)
    assert result['state'] == 'unavailable' and not result['complete']
    assert 'not json' not in str(result)
    assert len(reader._opener.calls) == 1


@pytest.mark.parametrize('code', [301, 302, 401, 403, 404, 429, 500])
def test_http_errors_no_retry_and_no_body_echo(code):
    error = urllib.error.HTTPError('https://api.github.com/synthetic', code, 'synthetic-sensitive', {}, io.BytesIO(b'synthetic-sensitive-body'))
    reader = client([error])
    result = reader.snapshot(7)
    assert result['state'] == 'unavailable' and result['reason'] == f'http_{code}'
    assert 'synthetic-sensitive' not in str(result) and len(reader._opener.calls) == 1
    assert error.fp.closed


@pytest.mark.parametrize('location', ['state', 'conclusion', 'status', 'app'])
def test_wrong_json_types_fail_closed(location):
    values = payloads()
    if location == 'state': values[0]['state'] = {}
    else: values[1]['check_runs'][0][location] = []
    result = client(values).snapshot(7)
    assert result['state'] == 'unavailable'


@pytest.mark.parametrize('repository', ['../owner/repo', 'owner/repo?x', 'https://github.com/owner/repo', 'owner/repo/more', 'owner/repo#fragment'])
def test_invalid_repository_configuration(repository):
    with pytest.raises(ValueError):
        PublicGitHubStatus(repository, expected_checks=('tests',), expected_app_id=15368)


@pytest.mark.parametrize('number', [True, 0, -1, '7', '../7'])
def test_invalid_pull_number_has_no_http_effect(number):
    reader = client(payloads())
    with pytest.raises(ValueError): reader.snapshot(number)
    assert not reader._opener.calls


def test_no_proxy_and_no_cross_host_redirect(monkeypatch):
    from backend.app.github_status import _NoRedirect
    captured = []
    monkeypatch.setattr('urllib.request.build_opener', lambda *handlers: captured.extend(handlers))
    PublicGitHubStatus(REPO, expected_checks=('tests',), expected_app_id=15368)
    assert captured[0].proxies == {}
    assert isinstance(captured[1], _NoRedirect)
    assert captured[1].redirect_request(None, None, 302, '', {}, 'https://untrusted.invalid') is None


@pytest.mark.parametrize('options', [
    {'expected_checks': ()}, {'expected_checks': ('tests', 'tests')},
    {'expected_checks': ('bad\nname',)}, {'expected_app_id': True},
    {'timeout': float('nan')}, {'timeout': 0}, {'timeout': True},
])
def test_invalid_policy_before_any_io(options):
    policy = {'expected_checks': ('tests',), 'expected_app_id': 15368}
    policy.update(options)
    with pytest.raises(ValueError): PublicGitHubStatus(REPO, **policy)


def test_network_failure_no_exception_detail_echo_or_retry():
    reader = client([TimeoutError('synthetic-sensitive')])
    result = reader.snapshot(7)
    assert result['state'] == 'unavailable' and result['reason'] == 'transport_or_payload_error'
    assert 'synthetic-sensitive' not in str(result) and len(reader._opener.calls) == 1
