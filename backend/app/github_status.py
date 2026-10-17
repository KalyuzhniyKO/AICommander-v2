"""Explicit read-only public GitHub status snapshots; never a merge permit."""
import json
import math
import re
import urllib.error
import urllib.request


class GitHubReadError(RuntimeError):
    """Safe category only: no response bodies, URLs, credentials or raw errors."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON property')
        result[key] = value
    return result


def _count(value):
    return type(value) is int and value >= 0


def _name(value):
    return isinstance(value, str) and 0 < len(value) <= 512 and not any(ord(c) < 32 for c in value)


class PublicGitHubStatus:
    """Owner-configured public repository, no token/environment/config discovery.

    Four GETs per snapshot, no retry/poll/write. Expected check names must come
    from trusted workflow configuration, never from a model or response body.
    The result does not prove branch protection, review, mergeability or QA.
    """

    def __init__(self, repository: str, *, expected_checks: tuple[str, ...], expected_app_id: int, timeout: float = 10):
        if (not isinstance(repository, str)
                or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', repository)):
            raise ValueError('Configure an explicit owner/repository')
        if (not isinstance(expected_checks, tuple) or not expected_checks
                or len(expected_checks) > 100 or any(not _name(n) for n in expected_checks)
                or len(set(expected_checks)) != len(expected_checks)):
            raise ValueError('Configure unique required check names')
        if type(expected_app_id) is not int or expected_app_id <= 0:
            raise ValueError('Configure a trusted check App ID')
        self.expected_app_id = expected_app_id
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 30:
            raise ValueError('Invalid HTTP timeout')
        self.repository, self.expected_checks, self.timeout = repository, expected_checks, timeout
        # No ambient proxy, credentials, cookies, netrc or cross-host redirects.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())

    def _get(self, suffix):
        request = urllib.request.Request('https://api.github.com/repos/' + self.repository + '/' + suffix,
            method='GET', headers={'Accept': 'application/vnd.github+json',
            'User-Agent': 'AICommander-public-status', 'X-GitHub-Api-Version': '2026-03-10'})
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                if response.status != 200:
                    raise GitHubReadError('http_status')
                raw = response.read(1024 * 1024 + 1)
                if len(raw) > 1024 * 1024:
                    raise GitHubReadError('response_limit')
                data = json.loads(raw.decode('utf-8'), object_pairs_hook=_object)
                if not isinstance(data, dict):
                    raise ValueError('Expected object')
                return data, 'rel="next"' in response.headers.get('Link', '')
        except urllib.error.HTTPError as exc:
            code = exc.code
            exc.close()
            raise GitHubReadError('http_' + str(code)) from None
        except GitHubReadError:
            raise
        except Exception:
            raise GitHubReadError('transport_or_payload_error') from None

    def _pull(self, number):
        data, next_page = self._get('pulls/' + str(number))
        if (next_page or data.get('number') != number or type(data.get('number')) is not int
                or data.get('state') not in ('open', 'closed') or type(data.get('draft')) is not bool
                or type(data.get('merged')) is not bool or not isinstance(data.get('head'), dict)
                or not isinstance(data.get('base'), dict)
                or not isinstance(data['base'].get('repo'), dict)
                or str(data['base']['repo'].get('full_name', '')).lower() != self.repository.lower()
                or not isinstance(data['head'].get('sha'), str)
                or not re.fullmatch('[0-9a-f]{40}', data['head']['sha'])
                or not _name(data['base'].get('ref'))):
            raise GitHubReadError('invalid_pull_payload')
        return data

    def snapshot(self, number: int):
        if type(number) is not int or not 0 < number < 2**31:
            raise ValueError('Invalid pull request number')
        result = {'repository': self.repository, 'pull_request': number,
                  'pull_url': f'https://github.com/{self.repository}/pull/{number}',
                  'diff_url': f'https://github.com/{self.repository}/pull/{number}/files',
                  'head_sha': None, 'state': 'unavailable', 'complete': False,
                  'all_expected_checks_passed': False, 'ready_for_merge': False,
                  'checks': [], 'statuses': [], 'missing_checks': list(self.expected_checks),
                  'reason': None, 'public_read_only': True}
        try:
            first = self._pull(number)
            sha = result['head_sha'] = first['head']['sha']
            result.update(pull_state=first['state'], draft=first['draft'], merged=first['merged'])
            runs, more_runs = self._get(f'commits/{sha}/check-runs?filter=all&per_page=100')
            statuses, more_statuses = self._get(f'commits/{sha}/status?per_page=100')
            checks = runs.get('check_runs')
            entries = statuses.get('statuses')
            if (not isinstance(checks, list) or not isinstance(entries, list)
                    or len(checks) > 100 or len(entries) > 100
                    or not _count(runs.get('total_count')) or not _count(statuses.get('total_count'))
                    or runs['total_count'] < len(checks) or statuses['total_count'] < len(entries)
                    or statuses.get('sha') != sha):
                raise GitHubReadError('invalid_checks_payload')
            for c in checks:
                if (not isinstance(c, dict) or c.get('head_sha') != sha or not _name(c.get('name'))
                        or c.get('status') not in ('queued', 'in_progress', 'completed', 'waiting', 'pending', 'requested')
                        or c.get('conclusion') not in (None, 'success', 'failure', 'neutral', 'cancelled', 'skipped', 'timed_out', 'action_required', 'stale', 'startup_failure')
                        or not isinstance(c.get('app'), dict) or type(c['app'].get('id')) is not int):
                    raise GitHubReadError('invalid_check_run')
                result['checks'].append({**{k: c.get(k) for k in ('name', 'status', 'conclusion')},
                                         'app_id': c['app']['id'], 'trusted_app': c['app']['id'] == self.expected_app_id})
            for s in entries:
                if not isinstance(s, dict) or not _name(s.get('context')) or s.get('state') not in ('success', 'pending', 'failure', 'error'):
                    raise GitHubReadError('invalid_commit_status')
                result['statuses'].append({k: s[k] for k in ('context', 'state')})
            last = self._pull(number)
            # PR state and commit must remain stable across the non-atomic reads.
            if any(first[k] != last[k] for k in ('state', 'draft', 'merged')) or last['head']['sha'] != sha or first['base']['ref'] != last['base']['ref']:
                result.update(state='stale', reason='pull_changed_during_read')
                return result
            names = {c['name'] for c in result['checks'] if c['trusted_app']}
            result['missing_checks'] = [n for n in self.expected_checks if n not in names]
            result['complete'] = not (more_runs or more_statuses
                or runs['total_count'] > len(checks) or statuses['total_count'] > len(entries))
            passed = (result['complete'] and not result['missing_checks']
                and all(c['trusted_app'] and c['status'] == 'completed' and c['conclusion'] == 'success' for c in result['checks'])
                and all(s['state'] == 'success' for s in result['statuses']))
            result.update(all_expected_checks_passed=passed, state='passed' if passed else 'not_passed')
            if not result['complete']:
                result['reason'] = 'pagination_incomplete'
            elif result['missing_checks']:
                result['reason'] = 'expected_checks_missing'
            else:
                result['reason'] = 'reported_snapshot_only'
        except GitHubReadError as exc:
            result.update(state='unavailable', complete=False, reason=str(exc), all_expected_checks_passed=False)
        return result
