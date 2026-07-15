from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from uuid import UUID


@dataclass(frozen=True, slots=True)
class ResolvedSkillStepTarget:
    skill_config_step_target_id: UUID
    skill_config_target_id: UUID
    projection_experience_graph_identity_id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class ResolvedSkillExecutionStep:
    skill_config_step_id: UUID
    position: int
    instruction: str
    skill_config_api_endpoint_id: UUID
    api_capability_endpoint_id: UUID
    endpoint_requirement_name: str
    capability_name: str
    targets: tuple[ResolvedSkillStepTarget, ...]
    api_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class ResolvedSkillExecutionPlan:
    skill_config_id: UUID
    skill_name: str
    steps: tuple[ResolvedSkillExecutionStep, ...]


@dataclass(frozen=True, slots=True)
class SkillStepApiCallInput:
    skill_config_step_id: UUID
    request_payload: Mapping[str, object] = field(default_factory=dict)
    call_key: UUID | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "request_payload", MappingProxyType(dict(self.request_payload))
        )


@dataclass(frozen=True, slots=True)
class SkillStepApiCallMaterialization:
    skill_config_step_id: UUID
    api_call_id: UUID
    api_capability_endpoint_id: UUID
    call_key: UUID
    request_hash: str
    request_model_id: UUID
    request_class_config_id: UUID
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    head_commit_id: UUID


@dataclass(frozen=True, slots=True)
class SkillRunHarnessRequest:
    skill_config_id: UUID
    run_key: str
    step_inputs: tuple[SkillStepApiCallInput, ...] = ()
    run_status: str = "succeeded"
    step_status: str = "succeeded"
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SkillInvocationContext:
    actor_id: UUID | None = None
    api_call_branch_id: UUID | None = None
    skill_run_branch_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SkillRunHarnessStepReceipt:
    skill_config_step_id: UUID
    skill_run_step_id: UUID
    api_call: SkillStepApiCallMaterialization
    status: str


@dataclass(frozen=True, slots=True)
class SkillRunHarnessResult:
    skill_config_id: UUID
    skill_run_id: UUID
    run_key: str
    status: str
    branch_id: UUID
    projection_hash: str
    commit_id: UUID
    head_commit_id: UUID
    steps: tuple[SkillRunHarnessStepReceipt, ...]
