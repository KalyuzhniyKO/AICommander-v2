"""Typed boundaries for the existing Hermes agent runtime, not a second agent loop."""
from dataclasses import dataclass
from typing import Callable


class UncertainOperation(Exception):
    """Dispatch may have happened; never automatically replay the external call."""


@dataclass(frozen=True)
class ProducedArtifact:
    content: dict
    provenance: dict


@dataclass(frozen=True)
class OperationContext:
    operation_id: str
    cancelled: Callable[[], bool]
