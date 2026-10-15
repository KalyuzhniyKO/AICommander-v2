# OFFLINE-C: disposable worktrees and local tests

[Russian primary documentation](EXECUTION.md)

The independent `backend.app.execution` package creates a per-task branch/worktree in an explicitly allowed fixture root, captures actual Git status and a base-to-working-tree diff, and runs owner-approved immutable argv tuples with exit codes, timeouts and cancellation. No shell, user-supplied arguments, network/provider calls, Codex CLI or taskflow/frontend integration are added.

Use `OfflineExecutor.create`, `write_text`, `snapshot`, `run` and `cleanup`; see the Russian example and dataclass field table. A successful result requires both `outcome == "exited"` and `exit_code == 0`. Untracked file names appear in status; their content is not included in the tracked diff. Explicit secret literals and common credential patterns are redacted from returned logs/diffs, not from files.

Cleanup requires explicit discard for changed, ignored, untracked or committed data. Only worktrees registered by this manager instance may be removed. A crash/restart retains worktrees for manual inspection. Original branch/HEAD/index/files are preserved; Git necessarily adds owned worktree/ref metadata. One manager serializes operations and requires exclusive control of its fixture directories.

This is **not an OS security sandbox**. Approved programs retain the user's OS privileges, including filesystem/network access, and must be trusted. POSIX process groups and Windows kill-on-close Job Objects reap ordinary descendants. Windows Store brokered aliases/venv launchers are rejected; stdlib fixtures use the direct `sys.base_prefix/python.exe`. A future real executor needs an OS/container isolation boundary, authenticated integrations, resource limits and network denial. Parent #15 remains open.

Run `python -m pytest tests/test_execution.py -q` for real local disposable-repository tests; `python -m pytest -q` runs the full suite. Actual evidence is in [qa-issue-29.json](qa-issue-29.json). Deliver as a draft PR into `v3-foundation`, without automatic merge/deployment.
