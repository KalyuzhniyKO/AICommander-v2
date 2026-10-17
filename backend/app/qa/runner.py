"""QA evidence is distinct from independent review and owner approval."""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import re
import threading
import uuid

from ..execution import CommandSpec, ExecutionError, OfflineExecutor
from ..execution.executor import _no_links, _within


def python_commands(python: str, *, django_settings: str | None = None,
                    timeout_seconds: float = 30, max_output_bytes: int = 65536):
    """Owner configuration only. Settings and project code must be inspected first.

    Isolated Python ignores PYTHONPATH/user site; cwd is then explicitly trusted.
    Django's configured databases are replaced before django.setup(). Import-time
    effects in project code are NOT contained by this library.
    """
    prefix = "import os,sys; sys.path.insert(0,os.getcwd()); "
    pytest_code = (prefix + "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'; "
                   "import pytest; sys.exit(pytest.main(['-q','-p','no:cacheprovider']))")
    commands = {"pytest": CommandSpec((python, "-I", "-B", "-c", pytest_code),
                                      timeout_seconds, max_output_bytes)}
    if django_settings is not None:
        if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", django_settings, flags=re.ASCII):
            raise ExecutionError("Invalid test settings module")
        django_code = (prefix + f"os.environ['DJANGO_SETTINGS_MODULE']={django_settings!r}; "
                       "from django.conf import settings; "
                       "settings.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}; "
                       "settings.DATABASE_ROUTERS=[]; "
                       "import django; django.setup(); "
                       "from django.core.management import call_command; ")
        for name, call in (
            ("django_check", "call_command('check', fail_level='WARNING')"),
            ("django_migrations", "call_command('makemigrations',check=True,dry_run=True,interactive=False)"),
        ):
            commands[name] = CommandSpec((python, "-I", "-B", "-c", django_code + call),
                                         timeout_seconds, max_output_bytes)
    return commands


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    ensure_ascii=True).encode()).hexdigest()


class QaRunner:
    """Synchronous, session-scoped adapter over the existing executor.

    This does not execute a Reviewer, infer security from a model's text, or
    promote taskflow state. A successful QA report still requires independent
    review and owner approval. A caller must not accept saved JSON as authority.
    """

    def __init__(self, executor: OfflineExecutor, *, django: bool):
        if type(django) is not bool:
            raise ExecutionError("Declare whether Django checks are required")
        self.executor = executor
        self.required = ("pytest", "django_check", "django_migrations") if django else ("pytest",)
        if any(name not in executor.commands for name in self.required):
            raise ExecutionError("Required QA command is missing from owner allowlist")
        self._lock = threading.Lock()

    def run(self, workspace_id: str, *, cancel: threading.Event | None = None):
        if not self._lock.acquire(blocking=False):
            raise ExecutionError("QA runner is busy")
        try:
            return self._run(workspace_id, cancel or threading.Event())
        finally:
            self._lock.release()

    def _run(self, key, cancel):
        # Initial policy/Git failures raise; there is no valid evidence to report.
        before, digest, complete = self.executor.review_evidence(key)
        commands = self.executor.commands
        plan = {name: asdict(commands[name]) for name in self.required}
        report = {
            "schema_version": 1, "run_id": uuid.uuid4().hex,
            "scope": "offline_trusted_fixture", "workspace_id": key,
            "base_commit": before.base_commit, "head": before.head,
            "evidence_sha256": digest, "command_plan_sha256": _hash(plan),
            "evidence_complete": complete, "source_unchanged": True,
            "diff": before.diff, "git_status": before.status,
            "required_checks": list(self.required), "checks": [],
            "qa_passed": False, "ready_for_pr": False,
            "independent_review": "required", "owner_approval": "required",
            "blockers": [],
        }
        if not complete:
            report["blockers"].append("untracked_files_require_staging_for_diff_review")
        stopped = not complete
        for name in self.required:
            if stopped or cancel.is_set():
                report["checks"].append({"command_id": name, "outcome": "not_run",
                                         "exit_code": None, "passed": False})
                continue
            try:
                # Recheck immediately before/after every check, not only at the end.
                _, current, current_complete = self.executor.review_evidence(key)
                if current != digest or not current_complete or self.executor.commands is not commands:
                    raise ExecutionError("QA evidence changed")
                result = self.executor.run(key, name, cancel=cancel)
                item = asdict(result)
                item["passed"] = (result.outcome == "exited" and result.exit_code == 0
                                  and not result.output_truncated)
                report["checks"].append(item)
                _, current, current_complete = self.executor.review_evidence(key)
                if current != digest or not current_complete or self.executor.commands is not commands:
                    raise ExecutionError("QA evidence changed")
            except (ExecutionError, OSError):
                # Never copy exception details that could contain raw paths/data.
                report["source_unchanged"] = False
                report["blockers"].append("execution_or_evidence_error")
                if not report["checks"] or report["checks"][-1]["command_id"] != name:
                    report["checks"].append({"command_id": name, "outcome": "error",
                                             "exit_code": None, "passed": False})
                stopped = True
        if cancel.is_set():
            report["blockers"].append("cancelled")
        if not all(item["passed"] for item in report["checks"]):
            report["blockers"].append("required_checks_not_passed")
        report["qa_passed"] = not report["blockers"]
        # The digest binds review to this report, including logs, checks and plan.
        report["report_sha256"] = _hash(report)
        return report


def write_report(report: dict, *, directory: Path) -> Path:
    """Export to an owner-selected existing directory, exclusively, without overwrite.

    Call outside the worktree after QA. This JSON is evidence, not a signed permit.
    Raw argv/settings/secret configuration is deliberately not exported.
    """
    directory = Path(directory).absolute()
    _no_links(directory)
    if not directory.is_dir():
        raise ExecutionError("Report directory must already exist")
    target = directory / "qa-report.json"
    _within(target, directory)
    # Apply no further redaction: report hash must remain verifiable. Logs/diff
    # have already been redacted by the executor before reaching this adapter.
    payload = (json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    fd = os.open(target, flags, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return target
