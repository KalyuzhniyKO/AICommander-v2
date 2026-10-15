from dataclasses import dataclass


class ExecutionError(RuntimeError):
    """A policy or Git failure; messages never contain raw subprocess output."""


@dataclass(frozen=True)
class CommandSpec:
    # Configuration supplied by the owner, never by a model or HTTP request.
    argv: tuple[str, ...]
    timeout_seconds: float = 30
    max_output_bytes: int = 64 * 1024


@dataclass(frozen=True)
class Workspace:
    id: str
    task_id: str
    branch: str
    path: str
    base_commit: str


@dataclass(frozen=True)
class Snapshot:
    workspace_id: str
    base_commit: str
    head: str
    status: str
    diff: str


@dataclass(frozen=True)
class CommandResult:
    workspace_id: str
    command_id: str
    outcome: str
    exit_code: int | None
    duration_seconds: float
    stdout: str
    stderr: str
    output_truncated: bool
