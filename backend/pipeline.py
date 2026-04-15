"""Pipeline states for AICommander orchestration."""

from __future__ import annotations

from enum import Enum
from typing import List


class PipelineStage(str, Enum):
    DIRECTOR = "director"
    EXECUTION = "execution"
    JUDGE = "judge"
    FINAL_AUDITOR = "final_auditor"
    DONE = "done"
    REVISE = "revise"
    REJECT = "reject"


def get_default_pipeline() -> List[PipelineStage]:
    """New primary pipeline for migration pack #1."""
    return [
        PipelineStage.DIRECTOR,
        PipelineStage.EXECUTION,
        PipelineStage.JUDGE,
        PipelineStage.FINAL_AUDITOR,
    ]


def resolve_terminal_stage(final_verdict: str) -> PipelineStage:
    normalized = (final_verdict or "").strip().lower()
    if normalized == "approve":
        return PipelineStage.DONE
    if normalized == "reject":
        return PipelineStage.REJECT
    return PipelineStage.REVISE
