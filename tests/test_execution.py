"""Actual local subprocesses and disposable Git repositories; no model/network calls."""
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

import pytest

from backend.app.execution import CommandSpec, ExecutionError, OfflineExecutor


GIT = shutil.which("git")
PYTHON = str(Path(sys.base_prefix) / "python.exe") if os.name == "nt" else sys.executable
pytestmark = pytest.mark.skipif(GIT is None, reason="Git is required")


def git(repo, *args):
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0", GIT_ALLOW_PROTOCOL="")
    return subprocess.run([GIT, "-c", "core.autocrlf=false", *args], cwd=repo, env=env,
                          check=True, capture_output=True, text=True, encoding="utf-8").stdout


SCRIPT = '''import os
from pathlib import Path
import subprocess
import sys
import time
mode = sys.argv[1]
if mode == "pass":
    assert Path("sample.txt").read_text() == "changed\\n"
    print("fixture assertion passed")
elif mode == "fail":
    print("api_key=fixture-key password=fixture-password", file=sys.stderr)
    print("Bearer fixture-bearer sk-fixturekey literal-sensitive")
    sys.exit(7)
elif mode == "env":
    assert "EXECUTION_TEST_SECRET" not in os.environ
    assert "PYTHONPATH" not in os.environ
    assert "GIT_SSH_COMMAND" not in os.environ
    assert "HTTP_PROXY" not in os.environ
    assert Path.home().parent == Path.cwd().parent
    print("environment isolated")
elif mode in {"sleep", "tree", "background"}:
    if mode != "sleep":
        subprocess.Popen([sys.executable, "-I", "-c",
                          "import time; from pathlib import Path; time.sleep(4); Path('escaped.txt').write_text('bad')"])
    Path("started.txt").write_text("started")
    print("started", flush=True)
    if mode != "background":
        time.sleep(30)
elif mode == "flood":
    while True:
        print("x" * 4096, flush=True)
elif mode == "boundary":
    print("x" * 250 + "literal-sensitive" + "y" * 50)
'''


@pytest.fixture
def fixture_repo(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Offline Fixture")
    git(repo, "config", "user.email", "fixture@example.invalid")
    (repo / "sample.txt").write_text("original\n", encoding="utf-8")
    (repo / "suite.py").write_text(SCRIPT, encoding="utf-8")
    (repo / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture")
    return repo


@pytest.fixture
def executor(tmp_path, fixture_repo):
    commands = {name: CommandSpec((PYTHON, "-I", "suite.py", name),
                                  1 if name in {"sleep", "tree"} else 10,
                                  256 if name in {"flood", "boundary"} else 65536)
                for name in ("pass", "fail", "env", "sleep", "tree", "background", "flood", "boundary")}
    return OfflineExecutor(allowed_root=tmp_path, repository=fixture_repo,
                           pool=tmp_path / "worktrees", commands=commands,
                           secrets=("literal-sensitive",))


def test_real_diff_command_exit_and_original_repository_unchanged(executor, fixture_repo):
    head = git(fixture_repo, "rev-parse", "HEAD")
    index = (fixture_repo / ".git" / "index").read_bytes()
    # Preserve even pre-existing owner modifications in the source checkout.
    (fixture_repo / "sample.txt").write_text("owner work\n")
    before_status = git(fixture_repo, "status", "--porcelain")
    workspace = executor.create("task-29")
    executor.write_text(workspace.id, "sample.txt", "changed\n")
    executor.write_text(workspace.id, "new.txt", "new file")
    snapshot = executor.snapshot(workspace.id)
    assert "M sample.txt" in snapshot.status and "?? new.txt" in snapshot.status
    assert "-original" in snapshot.diff and "+changed" in snapshot.diff
    result = executor.run(workspace.id, "pass")
    assert (result.outcome, result.exit_code) == ("exited", 0)
    assert "fixture assertion passed" in result.stdout
    with pytest.raises(ExecutionError, match="explicit discard"):
        executor.cleanup(workspace.id)
    executor.cleanup(workspace.id, discard_changes=True)
    assert not Path(workspace.path).exists()
    assert workspace.branch not in git(fixture_repo, "branch", "--list")
    assert git(fixture_repo, "rev-parse", "HEAD") == head
    assert git(fixture_repo, "branch", "--show-current").strip() == "main"
    assert git(fixture_repo, "status", "--porcelain") == before_status
    assert (fixture_repo / "sample.txt").read_text() == "owner work\n"
    assert (fixture_repo / ".git" / "index").read_bytes() == index


def test_clean_cleanup_and_unique_workspace_ids(executor):
    a, b = executor.create("same-task"), executor.create("same-task")
    assert a.id != b.id and a.branch != b.branch
    executor.cleanup(a.id)
    assert Path(b.path).is_dir()
    executor.cleanup(b.id)
    with pytest.raises(ExecutionError, match="Unknown workspace"):
        executor.cleanup(a.id)


@pytest.mark.parametrize("name", ["../outside", "/absolute", r"C:\outside", r"..\outside",
                                  ".git/config", ".GIT/config", "git~1/config", "x:stream",
                                  "sub/../../outside", ".", "NUL.txt", "foo. /x"])
def test_traversal_metadata_and_special_paths_rejected(executor, name):
    workspace = executor.create("paths")
    with pytest.raises(ExecutionError):
        executor.write_text(workspace.id, name, "forbidden")
    executor.cleanup(workspace.id)


@pytest.mark.parametrize("task_id", ["../main", "--force", "main x", "a/b", ""])
def test_invalid_task_identifiers(executor, task_id):
    with pytest.raises(ExecutionError):
        executor.create(task_id)


def test_allowlist_only_and_no_user_arguments(executor):
    workspace = executor.create("allowlist")
    for name in ("echo hello", "pass; echo bad", "git", "python", "../suite.py"):
        with pytest.raises(ExecutionError, match="allowlist"):
            executor.run(workspace.id, name)
    with pytest.raises(TypeError):
        executor.run(workspace.id, "pass", args=["unexpected"])
    with pytest.raises(TypeError):
        executor.commands["unsafe"] = CommandSpec(("sh",))
    executor.cleanup(workspace.id)


def test_failure_logs_and_diff_redacted(executor):
    workspace = executor.create("redaction")
    executor.write_text(workspace.id, "sample.txt", 'api_key="fixture-diff-secret"\nliteral-sensitive\n')
    result = executor.run(workspace.id, "fail")
    assert (result.outcome, result.exit_code) == ("exited", 7)
    text = result.stdout + result.stderr + executor.snapshot(workspace.id).diff
    for value in ("fixture-key", "fixture-password", "fixture-bearer", "sk-fixturekey",
                  "literal-sensitive", "fixture-diff-secret"):
        assert value not in text
    assert "[REDACTED]" in text
    executor.cleanup(workspace.id, discard_changes=True)


def test_environment_does_not_inherit_secrets(executor, monkeypatch):
    for key in ("EXECUTION_TEST_SECRET", "PYTHONPATH", "GIT_SSH_COMMAND", "HTTP_PROXY"):
        monkeypatch.setenv(key, "fixture-sensitive")
    workspace = executor.create("environment")
    result = executor.run(workspace.id, "env")
    assert result.exit_code == 0 and "environment isolated" in result.stdout
    executor.cleanup(workspace.id)


def test_timeout_reports_actual_exit_and_kills_descendants(executor):
    workspace = executor.create("timeout")
    result = executor.run(workspace.id, "tree")
    assert result.outcome == "timed_out"
    assert result.exit_code != 0 and result.duration_seconds < 6
    assert "started" in result.stdout
    time.sleep(4.2)
    assert not (Path(workspace.path) / "escaped.txt").exists()
    executor.cleanup(workspace.id, discard_changes=True)


def test_cancel_and_busy_cleanup(executor):
    workspace = executor.create("cancel")
    cancel = threading.Event()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(executor.run, workspace.id, "tree", cancel=cancel)
        deadline = time.monotonic() + 5
        while not (Path(workspace.path) / "started.txt").exists():
            assert time.monotonic() < deadline
            time.sleep(0.01)
        with pytest.raises(ExecutionError, match="busy"):
            executor.cleanup(workspace.id, discard_changes=True)
        cancel.set()
        result = future.result(timeout=5)
    assert result.outcome == "cancelled" and result.exit_code != 0
    time.sleep(4.2)
    assert not (Path(workspace.path) / "escaped.txt").exists()
    executor.cleanup(workspace.id, discard_changes=True)


def test_pre_cancel_does_not_launch(executor):
    workspace = executor.create("precancel")
    cancel = threading.Event()
    cancel.set()
    result = executor.run(workspace.id, "sleep", cancel=cancel)
    assert result.outcome == "cancelled" and result.exit_code is None
    assert not (Path(workspace.path) / "started.txt").exists()
    executor.cleanup(workspace.id)


def test_background_children_reaped_after_success(executor):
    workspace = executor.create("background")
    result = executor.run(workspace.id, "background")
    assert result.outcome == "exited" and result.exit_code == 0
    time.sleep(4.2)
    assert not (Path(workspace.path) / "escaped.txt").exists()
    executor.cleanup(workspace.id, discard_changes=True)


def test_output_bounded_and_boundary_redaction(executor):
    workspace = executor.create("output")
    result = executor.run(workspace.id, "flood")
    assert result.outcome == "output_limit" and result.output_truncated
    assert len(result.stdout) <= 256 and result.duration_seconds < 6
    result = executor.run(workspace.id, "boundary")
    assert result.output_truncated and "literal" not in result.stdout
    executor.cleanup(workspace.id)


def test_ignored_files_also_require_explicit_discard(executor):
    workspace = executor.create("ignored")
    executor.write_text(workspace.id, "ignored.txt", "test evidence")
    with pytest.raises(ExecutionError, match="explicit discard"):
        executor.cleanup(workspace.id)
    executor.cleanup(workspace.id, discard_changes=True)


def test_new_commits_require_explicit_discard(executor, fixture_repo):
    workspace = executor.create("commit")
    executor.write_text(workspace.id, "sample.txt", "committed")
    git(workspace.path, "add", "sample.txt")
    git(workspace.path, "commit", "-m", "fixture change")
    assert "+committed" in executor.snapshot(workspace.id).diff
    with pytest.raises(ExecutionError, match="explicit discard"):
        executor.cleanup(workspace.id)
    executor.cleanup(workspace.id, discard_changes=True)
    assert git(fixture_repo, "log", "-1", "--format=%s").strip() == "fixture"


def test_foreign_ids_and_changed_git_pointer_are_not_cleaned(executor, fixture_repo):
    with pytest.raises(ExecutionError, match="Unknown workspace"):
        executor.cleanup(str(fixture_repo), discard_changes=True)
    workspace = executor.create("pointer")
    metadata = Path(workspace.path) / ".git"
    original = metadata.read_text()
    # Git marks this file hidden on Windows; opening with truncation can be denied.
    with metadata.open("r+") as stream:
        stream.write("gitdir: " + str(fixture_repo / ".git"))
        stream.truncate()
    with pytest.raises(ExecutionError, match="metadata was replaced"):
        executor.cleanup(workspace.id, discard_changes=True)
    with metadata.open("r+") as stream:
        stream.write(original)
        stream.truncate()
    executor.cleanup(workspace.id)


def test_paths_outside_root_or_overlapping_repo_rejected(tmp_path, fixture_repo):
    for pool in (tmp_path.parent / "outside", fixture_repo / "nested", tmp_path):
        with pytest.raises(ExecutionError):
            OfflineExecutor(allowed_root=tmp_path, repository=fixture_repo, pool=pool, commands={})


def test_checkout_filters_and_includes_rejected(tmp_path, fixture_repo):
    config = fixture_repo / ".git" / "config"
    original = config.read_text()
    for extra in ('\n[include]\n path = ../external\n', '\n[filter "dangerous"]\n smudge = never-run\n'):
        config.write_text(original + extra)
        with pytest.raises(ExecutionError, match="includes and checkout filters"):
            OfflineExecutor(allowed_root=tmp_path, repository=fixture_repo, pool=tmp_path / "pool", commands={})
    config.write_text(original)


def test_hooks_are_not_executed(executor, fixture_repo):
    hook = fixture_repo / ".git" / "hooks" / "post-checkout"
    hook.write_text("#!/bin/sh\nexit 99\n")
    hook.chmod(0o755)
    workspace = executor.create("hook")
    executor.cleanup(workspace.id)


def test_symlink_or_junction_refused_without_deleting_target(executor, tmp_path):
    workspace = executor.create("link")
    target = tmp_path / "outside-data"
    target.mkdir()
    (target / "preserve.txt").write_text("keep")
    link = Path(workspace.path) / "link"
    if os.name == "nt":
        subprocess.run(["cmd.exe", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, capture_output=True, shell=False)
    else:
        link.symlink_to(target, target_is_directory=True)
    for action in (lambda: executor.run(workspace.id, "pass"),
                   lambda: executor.write_text(workspace.id, "link/preserve.txt", "bad"),
                   lambda: executor.cleanup(workspace.id, discard_changes=True)):
        with pytest.raises(ExecutionError, match="Symlinks and reparse"):
            action()
    assert (target / "preserve.txt").read_text() == "keep"
    # Unlink only the fixture link itself, never recursively traverse it.
    if os.name == "nt":
        link.rmdir()
    else:
        link.unlink()
    executor.cleanup(workspace.id)


@pytest.mark.parametrize("argv", [("python", "-V"), (sys.executable, "bad\0argument")])
def test_invalid_command_configuration(tmp_path, fixture_repo, argv):
    with pytest.raises(ExecutionError, match="specification"):
        OfflineExecutor(allowed_root=tmp_path, repository=fixture_repo, pool=tmp_path / "pool",
                        commands={"test": CommandSpec(argv)})


@pytest.mark.skipif(os.name != "nt", reason="Windows app alias guard")
def test_brokered_python_launcher_rejected(tmp_path, fixture_repo):
    fake = tmp_path / "venv" / "Scripts" / "python.exe"
    fake.parent.mkdir(parents=True)
    fake.write_bytes(b"not executed")
    (fake.parent.parent / "pyvenv.cfg").write_text(r"home = C:\Users\fixture\Microsoft\WindowsApps\Python")
    with pytest.raises(ExecutionError, match="Brokered Python launcher"):
        OfflineExecutor(allowed_root=tmp_path, repository=fixture_repo, pool=tmp_path / "pool",
                        commands={"test": CommandSpec((str(fake),))})


def test_committed_link_and_submodule_modes_rejected(executor, fixture_repo):
    # Write Git objects directly: no symlink privilege or submodule/network operation.
    blob = git(fixture_repo, "hash-object", "-w", "sample.txt").strip()
    git(fixture_repo, "update-index", "--add", "--cacheinfo", "120000," + blob + ",link")
    git(fixture_repo, "commit", "-m", "link fixture")
    with pytest.raises(ExecutionError, match="Symlinks and submodules"):
        executor.create("link")
    git(fixture_repo, "update-index", "--force-remove", "link")
    commit = git(fixture_repo, "rev-parse", "HEAD").strip()
    git(fixture_repo, "update-index", "--add", "--cacheinfo", "160000," + commit + ",submodule")
    git(fixture_repo, "commit", "-m", "submodule fixture")
    with pytest.raises(ExecutionError, match="Symlinks and submodules"):
        executor.create("submodule")


def test_switched_branch_refused(executor):
    workspace = executor.create("branch")
    git(workspace.path, "checkout", "--detach")
    with pytest.raises(ExecutionError):
        executor.cleanup(workspace.id, discard_changes=True)
    assert Path(workspace.path).exists()
    git(workspace.path, "checkout", workspace.branch)
    executor.cleanup(workspace.id)


def test_hard_link_cannot_modify_external_file(executor, tmp_path):
    workspace = executor.create("hardlink")
    original = tmp_path / "preserve.txt"
    original.write_text("keep")
    link = Path(workspace.path) / "hardlink.txt"
    os.link(original, link)
    with pytest.raises(ExecutionError, match="Hard-linked"):
        executor.write_text(workspace.id, "hardlink.txt", "bad")
    with pytest.raises(ExecutionError, match="Hard-linked"):
        executor.cleanup(workspace.id, discard_changes=True)
    assert original.read_text() == "keep"
    link.unlink()
    executor.cleanup(workspace.id)
