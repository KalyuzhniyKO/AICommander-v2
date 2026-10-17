# QA runner — offline preparation for #16

[Русский](QA_RUNNER.md)

An explicit library over the existing `OfflineExecutor`, for trusted disposable
fixture repositories only. No HTTP/taskflow/panel/Hermes/GitHub wiring, model
calls, automatic installation or independent Reviewer execution. Full #16 stays
open pending #15 and integration acceptance.

`python_commands()` creates fixed isolated Python commands for real pytest
(no third-party plugin autoload or cacheprovider) and, when explicitly configured,
Django system checks (WARNING threshold) and migration checks (`check=True`,
`dry_run=True`, noninteractive). Django is a dev/CI dependency only. Before
`django.setup()`, configured databases are replaced with SQLite `:memory:` and
routers cleared. No migrate command runs. Settings import can already execute
code: inspect settings, AppConfig, tests, conftest and dependencies beforehand;
never pass production settings. This checks missing migrations, not successful
application/rollback on a target database.

Required checks are pytest plus both Django checks when `django=True`.
Owner configuration is trusted, never derived from model/HTTP input. Missing
commands fail closed. No collected tests, nonzero exit, timeout, cancellation,
truncation or execution/evidence error block `qa_passed`. Ordinary test failures
allow other checks for diagnostics; evidence errors/cancellation stop later checks.

Before/after each check, evidence binds workspace/base/HEAD/status/real Git diff
and raw hashes of tracked contents (including tracked ignored files). New files
must be staged first. Assume-unchanged/skip-worktree entries are refused. Limits:
4096 files, 8 MiB total tracked contents, executor Git time/output limits. Raw
command configuration is hashed, not exported. Logs/status/diff use the existing
best-effort redactor; arbitrary/encoded secrets are not guaranteed detectable.

Ignored untracked outputs are excluded. Inputs must not rely on them or external
files. Transient changes restored between snapshots, hostile races, interpreter
and dependency changes are not contained. Worktrees/minimal environments are not
an OS sandbox or network boundary. Do not execute untrusted code here.

`write_report(report, directory=existing_path)` exclusively creates
`qa-report.json` outside the worktree, refuses linked directories and overwrite,
and uses POSIX mode 0600. A crash can leave a partial file: validate JSON and its
`report_sha256`. Hashes are integrity evidence, not signatures or permissions.
Reports can contain private code; do not publish automatically.

**`ready_for_pr` is always False**; independent review and owner approval remain
required even after successful QA. A future trusted Reviewer must inspect the
actual diff, security, requirements, test coverage and applicability of checks,
bind its decision to evidence/report/command-plan hashes, and revalidate current
code before promotion. No saved JSON is trusted authority. Binary changes need
additional review evidence. No integration or independent review is claimed here.

See the [Russian guide](QA_RUNNER.md) for the explicit API example and operational
limits, [pytest docs](https://docs.pytest.org/en/stable/how-to/plugins.html) and
[Django docs](https://docs.djangoproject.com/en/5.2/ref/django-admin/) for command
contracts. Run `python -m pytest -q tests/test_qa.py tests/test_execution.py` for
real subprocess integration tests against temporary synthetic repositories.

The [failing report example](contracts/qa-report-v1-failing.example.json) comes
from a real intentionally failing pytest fixture, not a live Hermes/Zorin run.
