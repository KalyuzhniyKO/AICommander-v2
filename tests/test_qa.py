"""Real pytest and Django processes, disposable Git repos, synthetic data only."""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import venv
import threading

import pytest

from backend.app.execution import CommandSpec, ExecutionError, OfflineExecutor
from backend.app.qa import QaRunner, python_commands, write_report

GIT = shutil.which("git")
PYTHON = str(Path(sys.base_prefix) / "python.exe") if os.name == "nt" else str(Path(sys.executable).resolve())
pytestmark = pytest.mark.skipif(not GIT, reason="Git required")


def git(repo, *args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_ALLOW_PROTOCOL="")
    return subprocess.run([GIT, "-c", "core.autocrlf=false", *args], cwd=repo,
                          env=env, check=True, capture_output=True, text=True).stdout


@pytest.fixture(scope="session", autouse=True)
def qa_interpreter(tmp_path_factory):
    # Executor deliberately rejects symlinks. A copied venv keeps local dev
    # packages available without resolving the interpreter out of its venv.
    global PYTHON
    if os.name != "nt":
        root = tmp_path_factory.mktemp("qa-python")
        venv.EnvBuilder(symlinks=False, with_pip=False).create(root)
        packages = root / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
        (packages / "qa-dev-dependencies.pth").write_text(sysconfig.get_path("purelib") + "\n")
        PYTHON = str(root / "bin" / "python")
    yield


@pytest.fixture
def project(tmp_path):
    repo = tmp_path / "fixture"
    repo.mkdir()
    files = {
        "sample.py": "VALUE = 1\n",
        "test_sample.py": "from sample import VALUE\ndef test_value():\n    assert VALUE == 2\n",
        ".gitignore": "__pycache__/\n.pytest_cache/\n*.pyc\n",
        "qa_settings.py": "SECRET_KEY='synthetic-only'\nINSTALLED_APPS=['fixtureapp']\nDEFAULT_AUTO_FIELD='django.db.models.AutoField'\nDATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':'never-open.sqlite3'}}\n",
        "fixtureapp/__init__.py": "",
        "fixtureapp/models.py": "from django.db import models\nclass Item(models.Model):\n    name = models.CharField(max_length=10)\n",
        "fixtureapp/migrations/__init__.py": "",
        "fixtureapp/migrations/0001_initial.py": "from django.db import migrations, models\nclass Migration(migrations.Migration):\n    initial = True\n    dependencies = []\n    operations = [migrations.CreateModel(name='Item', fields=[('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),('name',models.CharField(max_length=10))])]\n",
    }
    for name, text in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "QA Fixture")
    git(repo, "config", "user.email", "qa@example.invalid")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture")
    return repo


def prepare(tmp_path, project, *, django=False, commands=None, **options):
    commands = commands or python_commands(PYTHON, django_settings="qa_settings" if django else None, **options)
    executor = OfflineExecutor(allowed_root=tmp_path, repository=project,
                               pool=tmp_path / "pool", commands=commands,
                               secrets=("literal-sensitive",))
    workspace = executor.create("qa-fixture")
    return executor, workspace, QaRunner(executor, django=django)


def report_hash(report):
    value = {k: v for k, v in report.items() if k != "report_sha256"}
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def test_real_pytest_failure_report_blocks_readiness(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project)
    executor.write_text(workspace.id, "sample.py", "VALUE = 3\n")
    report = runner.run(workspace.id)
    assert report["checks"][0]["exit_code"] == 1
    assert "1 failed" in report["checks"][0]["stdout"]
    assert not report["qa_passed"] and not report["ready_for_pr"]
    assert report["source_unchanged"] and "+VALUE = 3" in report["diff"]
    assert report_hash(report) == report["report_sha256"]
    output = tmp_path / "reports"
    output.mkdir()
    path = write_report(report, directory=output)
    assert path.name == "qa-report.json" and json.loads(path.read_text()) == report
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        write_report(report, directory=output)
    # Optionally publish this exact, real synthetic fixture report for documentation.
    example = os.environ.get("QA_FIXTURE_EXAMPLE")
    if example:
        Path(example).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    assert (project / "sample.py").read_text() == "VALUE = 1\n"
    assert git(project, "status", "--porcelain") == ""
    executor.cleanup(workspace.id, discard_changes=True)


def test_actual_pytest_django_check_and_migration_check(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project, django=True)
    executor.write_text(workspace.id, "sample.py", "VALUE = 2\n")
    report = runner.run(workspace.id)
    assert report["qa_passed"], report
    assert len(report["checks"]) == 3
    assert all(item["exit_code"] == 0 for item in report["checks"])
    assert "1 passed" in report["checks"][0]["stdout"]
    assert "System check identified no issues" in report["checks"][1]["stdout"]
    assert "No changes detected" in report["checks"][2]["stdout"]
    assert not (Path(workspace.path) / "never-open.sqlite3").exists()
    assert not report["ready_for_pr"] and report["independent_review"] == "required"
    assert report["owner_approval"] == "required"
    again = runner.run(workspace.id)
    assert again["evidence_sha256"] == report["evidence_sha256"]
    assert again["run_id"] != report["run_id"]
    executor.cleanup(workspace.id, discard_changes=True)


@pytest.mark.parametrize("kind", ["migration", "system_check"])
def test_real_django_failures_and_no_database_or_migration_writes(tmp_path, project, kind):
    executor, workspace, runner = prepare(tmp_path, project, django=True)
    executor.write_text(workspace.id, "sample.py", "VALUE = 2\n")
    original = (Path(workspace.path) / "fixtureapp/models.py").read_text()
    change = original.replace("max_length=10", "max_length=20") if kind == "migration" else original.replace("models.CharField(max_length=10)", "models.CharField(max_length=-1)")
    executor.write_text(workspace.id, "fixtureapp/models.py", change)
    report = runner.run(workspace.id)
    failed = "django_migrations" if kind == "migration" else "django_check"
    assert next(item for item in report["checks"] if item["command_id"] == failed)["exit_code"] != 0
    assert not report["qa_passed"] and not report["ready_for_pr"]
    assert not list(Path(workspace.path).rglob("*.sqlite3"))
    assert not (Path(workspace.path) / "fixtureapp/migrations/0002_alter_item_name.py").exists()
    executor.cleanup(workspace.id, discard_changes=True)


@pytest.mark.parametrize("body,options,expected", [
    ("import time\ndef test_slow():\n    time.sleep(30)\n", {"timeout_seconds": 0.5}, "timed_out"),
    ("def test_flood():\n    print('x'*50000)\n    assert False\n", {"max_output_bytes": 256}, "output_limit"),
    ("# no tests\n", {}, "exited"),
])
def test_timeout_overflow_and_no_collection_fail_closed(tmp_path, project, body, options, expected):
    executor, workspace, runner = prepare(tmp_path, project, **options)
    executor.write_text(workspace.id, "test_sample.py", body)
    report = runner.run(workspace.id)
    assert report["checks"][0]["outcome"] == expected
    assert not report["qa_passed"] and not report["ready_for_pr"]
    executor.cleanup(workspace.id, discard_changes=True)


def test_precancel_runs_no_checks(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project, django=True)
    cancel = threading.Event()
    cancel.set()
    report = runner.run(workspace.id, cancel=cancel)
    assert not report["qa_passed"]
    assert all(item["outcome"] == "not_run" for item in report["checks"])
    executor.cleanup(workspace.id)


def test_passing_test_mutating_code_invalidates_evidence(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project, django=True)
    executor.write_text(workspace.id, "test_sample.py", "from pathlib import Path\ndef test_change():\n    Path('sample.py').write_text('VALUE = 2\\n')\n")
    report = runner.run(workspace.id)
    assert report["checks"][0]["exit_code"] == 0
    assert not report["source_unchanged"] and not report["qa_passed"]
    assert all(item["outcome"] == "not_run" for item in report["checks"][1:])
    executor.cleanup(workspace.id, discard_changes=True)


def test_untracked_source_blocks_until_staged_and_appears_in_real_diff(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project)
    executor.write_text(workspace.id, "sample.py", "VALUE = 2\n")
    executor.write_text(workspace.id, "new.py", "NEW = True\n")
    report = runner.run(workspace.id)
    assert not report["evidence_complete"] and report["checks"][0]["outcome"] == "not_run"
    git(workspace.path, "add", "new.py")
    report = runner.run(workspace.id)
    assert report["qa_passed"] and "new file mode" in report["diff"] and "+NEW = True" in report["diff"]
    executor.cleanup(workspace.id, discard_changes=True)


def test_raw_content_hash_changes_even_when_redacted_diff_is_identical(tmp_path, project):
    executor, workspace, _ = prepare(tmp_path, project)
    executor.write_text(workspace.id, "sample.py", "password='first-sensitive'\n")
    first, a, _ = executor.review_evidence(workspace.id)
    executor.write_text(workspace.id, "sample.py", "password='second-sensitive'\n")
    second, b, _ = executor.review_evidence(workspace.id)
    assert "first-sensitive" not in first.diff and "second-sensitive" not in second.diff
    assert a != b
    executor.cleanup(workspace.id, discard_changes=True)


def test_output_and_diff_redaction_and_environment(tmp_path, project, monkeypatch):
    monkeypatch.setenv("QA_TEST_SECRET", "must-not-inherit")
    executor, workspace, runner = prepare(tmp_path, project)
    executor.write_text(workspace.id, "test_sample.py", "import os\ndef test_redact():\n    assert 'QA_TEST_SECRET' not in os.environ\n    print('Bearer fixture-bearer literal-sensitive')\n    print('api_key=fixture-key')\n    assert False\n")
    report = runner.run(workspace.id)
    serialized = json.dumps(report)
    for value in ("fixture-bearer", "fixture-key", "literal-sensitive", "must-not-inherit"):
        assert value not in serialized
    assert "[REDACTED]" in serialized
    assert not report["qa_passed"]
    executor.cleanup(workspace.id, discard_changes=True)


def test_launch_error_is_reported_without_raw_exception(tmp_path, project):
    commands = python_commands(PYTHON)
    executable = tmp_path / ("invalid.exe" if os.name == "nt" else "invalid")
    executable.write_bytes(b"invalid executable")
    commands["pytest"] = replace(commands["pytest"], argv=(str(executable),))
    executor, workspace, runner = prepare(tmp_path, project, commands=commands)
    report = runner.run(workspace.id)
    assert not report["qa_passed"] and report["checks"][0]["exit_code"] != 0
    assert str(executable) not in json.dumps(report)
    executor.cleanup(workspace.id)


def test_required_commands_configuration_and_unknown_workspace(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project)
    with pytest.raises(ExecutionError, match="missing"):
        QaRunner(executor, django=True)
    with pytest.raises(ExecutionError, match="Declare"):
        QaRunner(executor, django="no")
    with pytest.raises(ExecutionError, match="Unknown workspace"):
        runner.run("foreign")
    with pytest.raises(ExecutionError, match="Invalid test settings"):
        python_commands(PYTHON, django_settings="../production")
    executor.cleanup(workspace.id)


def test_evidence_size_limit_and_paths(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project)
    # A tracked ignored file still participates in evidence and its bounds.
    executor.write_text(workspace.id, "large.pyc", "x" * (8 * 1024 * 1024 + 1))
    git(workspace.path, "add", "-f", "large.pyc")
    with pytest.raises(ExecutionError):
        runner.run(workspace.id)
    executor.cleanup(workspace.id, discard_changes=True)


def test_export_refuses_linked_directory(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "linked"
    if os.name == "nt":
        # Existing executor tests exercise native junction refusal on Windows.
        pytest.skip("POSIX symlink fixture")
    link.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ExecutionError):
        write_report({}, directory=link)
    assert not list(actual.iterdir())


@pytest.mark.parametrize("flag", ["--assume-unchanged", "--skip-worktree"])
def test_hidden_index_entries_refused(tmp_path, project, flag):
    executor, workspace, runner = prepare(tmp_path, project)
    git(workspace.path, "update-index", flag, "sample.py")
    with pytest.raises(ExecutionError, match="index entries"):
        runner.run(workspace.id)
    git(workspace.path, "update-index", "--no-assume-unchanged", "--no-skip-worktree", "sample.py")
    executor.cleanup(workspace.id)


def test_committed_changes_bound_to_baseline_and_head(tmp_path, project):
    executor, workspace, runner = prepare(tmp_path, project)
    executor.write_text(workspace.id, "sample.py", "VALUE = 2\n")
    git(workspace.path, "add", "sample.py")
    git(workspace.path, "commit", "-m", "synthetic fix")
    report = runner.run(workspace.id)
    assert report["qa_passed"] and report["head"] != report["base_commit"]
    assert "+VALUE = 2" in report["diff"]
    executor.write_text(workspace.id, "sample.py", "VALUE = 3\n")
    assert executor.review_evidence(workspace.id)[1] != report["evidence_sha256"]
    executor.cleanup(workspace.id, discard_changes=True)


def test_cancel_active_qa_and_concurrent_run_rejected(tmp_path, project):
    from concurrent.futures import ThreadPoolExecutor
    import time

    executor, workspace, runner = prepare(tmp_path, project, django=True, timeout_seconds=10)
    executor.write_text(workspace.id, "test_sample.py", "from pathlib import Path\nimport time\ndef test_slow():\n    Path('__pycache__').mkdir(exist_ok=True)\n    Path('__pycache__/qa-start').write_text('started')\n    time.sleep(30)\n")
    cancel = threading.Event()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(runner.run, workspace.id, cancel=cancel)
        deadline = time.monotonic() + 8
        try:
            while not (Path(workspace.path) / "__pycache__/qa-start").exists():
                assert time.monotonic() < deadline
                time.sleep(0.01)
            with pytest.raises(ExecutionError, match="busy"):
                runner.run(workspace.id)
        finally:
            cancel.set()
        report = future.result(timeout=10)
    assert report["checks"][0]["outcome"] == "cancelled"
    assert all(item["outcome"] == "not_run" for item in report["checks"][1:])
    assert not report["qa_passed"] and "cancelled" in report["blockers"]
    executor.cleanup(workspace.id, discard_changes=True)


def test_exit_zero_with_truncated_pytest_output_is_not_success(tmp_path, project):
    commands = python_commands(PYTHON, max_output_bytes=256)
    spec = commands["pytest"]
    commands["pytest"] = replace(spec, argv=(*spec.argv[:-1], spec.argv[-1].replace("['-q',", "['-q','-s',")))
    executor, workspace, runner = prepare(tmp_path, project, commands=commands)
    executor.write_text(workspace.id, "test_sample.py", "def test_print():\n    print('x'*1000)\n")
    report = runner.run(workspace.id)
    check = report["checks"][0]
    assert check["exit_code"] == 0 and check["output_truncated"]
    assert not check["passed"] and not report["qa_passed"]
    executor.cleanup(workspace.id, discard_changes=True)
