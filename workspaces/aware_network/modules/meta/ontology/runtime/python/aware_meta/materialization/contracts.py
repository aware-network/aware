from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class MaterializationLaneContext:
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class MaterializationStep:
    step_id: str
    step_kind: str
    payload: Mapping[str, object]
    commit_requested: bool = True


@dataclass(frozen=True, slots=True)
class MaterializationPlan:
    module_id: str
    pipeline_id: str
    lane: MaterializationLaneContext
    steps: tuple[MaterializationStep, ...]


@dataclass(frozen=True, slots=True)
class MaterializationStepResult:
    details: Mapping[str, object]
    commit_id: UUID | None = None
    head_commit_id: UUID | None = None


class MaterializationStepRunner(Protocol):
    async def __call__(
        self,
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
    ) -> MaterializationStepResult: ...


class MaterializationExecutionObserver(Protocol):
    async def on_run_started(
        self,
        *,
        plan: MaterializationPlan,
        started_at_utc: str,
    ) -> None: ...

    async def on_step_started(
        self,
        *,
        plan: MaterializationPlan,
        step: MaterializationStep,
        started_at_utc: str,
    ) -> None: ...

    async def on_step_finished(
        self,
        *,
        plan: MaterializationPlan,
        receipt: object,
    ) -> None: ...

    async def on_run_finished(
        self,
        *,
        receipt: object,
    ) -> None: ...


def validate_materialization_plan(*, plan: MaterializationPlan) -> None:
    module_id = plan.module_id.strip()
    pipeline_id = plan.pipeline_id.strip()
    projection_hash = plan.lane.projection_hash.strip()
    if not module_id:
        raise ValueError("materialization module_id is required")
    if not pipeline_id:
        raise ValueError("materialization pipeline_id is required")
    if not projection_hash:
        raise ValueError("materialization lane projection_hash is required")

    step_ids: set[str] = set()
    for step in plan.steps:
        step_id = step.step_id.strip()
        step_kind = step.step_kind.strip()
        if not step_id:
            raise ValueError("materialization step_id is required")
        if not step_kind:
            raise ValueError(
                f"materialization step_kind is required: step_id={step_id!r}"
            )
        if step_id in step_ids:
            raise ValueError(
                f"materialization step_id must be unique: {step_id!r}"
            )
        step_ids.add(step_id)


__all__ = [
    "MaterializationExecutionObserver",
    "MaterializationLaneContext",
    "MaterializationPlan",
    "MaterializationStep",
    "MaterializationStepResult",
    "MaterializationStepRunner",
    "validate_materialization_plan",
]
