"""Versioned UI contract and validated offline commands."""
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RunState(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    FAILED = "failed"
    BLOCKED = "blocked"
    AWAITING_OWNER = "awaiting_owner"
    DONE = "done"
    CANCELLED = "cancelled"


class StageState(StrEnum):
    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


Key = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")]


class CreateRun(Model):
    idempotency_key: Key
    max_steps: int = Field(default=3, ge=1, le=100, strict=True)


class Command(Model):
    idempotency_key: Key
    expected_version: int = Field(ge=1, strict=True)
    action: Literal["start", "step", "block", "resume", "fail", "cancel"]
    reason: str = Field(default="", max_length=2000)


class OwnerDecision(Model):
    idempotency_key: Key
    expected_version: int = Field(ge=1, strict=True)
    decision: Literal["approve", "reject"]
    reason: str = Field(default="", max_length=2000)


class Requirements(Model):
    objective: str
    acceptance_criteria: list[str] = Field(min_length=1)


class Design(Model):
    requirements: Requirements
    components: list[str] = Field(min_length=1)


class Plan(Model):
    design: Design
    steps: list[str] = Field(min_length=1)
    execution: Literal["not_executed"] = "not_executed"


class ArtifactBase(Model):
    artifact_id: int
    task_id: int
    run_id: int
    status: Literal["completed"] = "completed"
    input_artifact_ids: list[int]
    created_at: str
    redacted: Literal[True] = True
    simulated: Literal[True] = True


class RequirementsArtifact(ArtifactBase):
    role: Literal["analyst"]
    type: Literal["requirements"]
    content: Requirements


class DesignArtifact(ArtifactBase):
    role: Literal["architect"]
    type: Literal["design"]
    content: Design


class PlanArtifact(ArtifactBase):
    role: Literal["developer"]
    type: Literal["plan"]
    content: Plan


Artifact = Annotated[RequirementsArtifact | DesignArtifact | PlanArtifact, Field(discriminator="type")]


class Stage(Model):
    role: Literal["analyst", "architect", "developer"]
    position: int
    status: StageState


class Event(Model):
    event_id: int
    action: str
    from_status: RunState | None
    to_status: RunState
    version: int
    reason: str
    created_at: str


class RunSnapshot(Model):
    schema_version: Literal["1.0"] = "1.0"
    run_id: int
    task_id: int
    status: RunState
    version: int
    max_steps: int
    steps_done: int
    block_code: Literal["manual", "step_limit", "role_failure", "owner_rejected"] | None
    reason: str
    owner_decision: Literal["pending", "approved", "rejected"]
    director: Literal["mock"] = "mock"
    simulated: Literal[True] = True
    completion_scope: Literal["mock_artifacts_only"] = "mock_artifacts_only"
    created_at: str
    updated_at: str
    stages: list[Stage]
    artifacts: list[Artifact]
    timeline: list[Event]


class OperationSnapshot(Model):
    id: str
    run_id: int
    role: Literal["analyst", "architect", "developer", "reviewer"]
    expected_version: int
    state: Literal["running", "result_ready", "unknown", "succeeded", "failed", "discarded"]
    cancel_requested: bool
    created_at: str
    updated_at: str


class HermesCreateRun(CreateRun):
    max_steps: int = Field(default=4, ge=1, le=100, strict=True)
    include_architect: bool = Field(default=False, strict=True)


class RealPlan(Model):
    requirements: Requirements
    design: Design | None = None
    steps: list[str] = Field(min_length=1)
    execution: Literal["not_executed"] = "not_executed"


class PlanReview(Model):
    plan: RealPlan
    verdict: Literal["approve", "revise"]
    findings: list[str]
    scope: Literal["planning_only"] = "planning_only"


class HermesProvenance(Model):
    origin: Literal["hermes"] = "hermes"
    operation_id: str
    model_id: str
    provider: Literal["custom"] = "custom"
    route: Literal["omniroute"] = "omniroute"
    sdk_commit: str
    parent_session_id: str
    child_session_id: str
    tools_count: Literal[0] = 0
    inference_requests: Literal[1] = 1
    input_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class HermesRequirementsArtifact(RequirementsArtifact):
    simulated: Literal[False] = False
    provenance: HermesProvenance


class HermesDesignArtifact(DesignArtifact):
    simulated: Literal[False] = False
    provenance: HermesProvenance


class HermesPlanArtifact(ArtifactBase):
    role: Literal["developer"]
    type: Literal["plan"]
    content: RealPlan
    simulated: Literal[False] = False
    provenance: HermesProvenance


class HermesReviewArtifact(ArtifactBase):
    role: Literal["reviewer"]
    type: Literal["review"]
    content: PlanReview
    simulated: Literal[False] = False
    provenance: HermesProvenance


HermesArtifact = Annotated[HermesRequirementsArtifact | HermesDesignArtifact | HermesPlanArtifact | HermesReviewArtifact, Field(discriminator="type")]


class HermesStage(Stage):
    role: Literal["analyst", "architect", "developer", "reviewer"]


class HermesRunSnapshot(RunSnapshot):
    schema_version: Literal["2.0"] = "2.0"
    director: Literal["hermes"] = "hermes"
    simulated: Literal[False] = False
    completion_scope: Literal["real_planning_artifacts_only"] = "real_planning_artifacts_only"
    code_executed: Literal[False] = False
    qa_verified: Literal[False] = False
    stages: list[HermesStage]
    artifacts: list[HermesArtifact]


def content_model(mode, role):
    if mode == 'hermes':
        return {'analyst': Requirements, 'architect': Design, 'developer': RealPlan, 'reviewer': PlanReview}[role]
    return {'analyst': Requirements, 'architect': Design, 'developer': Plan}[role]
