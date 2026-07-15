from __future__ import annotations

from collections.abc import Mapping, Sequence
from importlib import import_module
from typing import Any
from uuid import UUID, uuid4

from aware_api_runtime.invocation import ApiInvocationRuntimeProtocol
from aware_api_runtime.package_ref_resolution import (
    ApiRuntimePackageRef,
    ResolvedApiRuntimePackageRef,
    build_api_invocation_source_commit_from_package_ref,
    resolve_api_runtime_package_ref,
)
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex

from ..package_ref_resolution import (
    SkillRuntimePackageRef,
    resolve_committed_skill_runtime_package_ref,
)
from .api_calls import materialize_skill_step_api_call
from .models import (
    ResolvedSkillExecutionPlan,
    SkillRunHarnessRequest,
    SkillRunHarnessResult,
    SkillRunHarnessStepReceipt,
    SkillStepApiCallMaterialization,
    SkillStepApiCallInput,
)
from .resolution import (
    resolve_committed_skill_execution_plan,
    resolve_skill_execution_plan_from_commit,
)


async def materialize_skill_run(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    skill_config_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext,
    api_call_lane: MaterializationLaneContext,
    skill_run_lane: MaterializationLaneContext,
    request: SkillRunHarnessRequest,
    commit: bool = True,
    publish: bool = False,
) -> SkillRunHarnessResult:
    plan = await resolve_committed_skill_execution_plan(
        index=index,
        lane=skill_config_lane,
        skill_config_id=request.skill_config_id,
    )
    step_inputs = _step_inputs_by_id(
        planned_step_ids=tuple(step.skill_config_step_id for step in plan.steps),
        request=request,
    )
    materialized_calls = [
        await materialize_skill_step_api_call(
            runtime=runtime,
            index=index,
            actor_id=actor_id,
            api_source_lane=api_source_lane,
            api_call_lane=api_call_lane,
            step=step,
            step_input=step_inputs.get(step.skill_config_step_id)
            or SkillStepApiCallInput(skill_config_step_id=step.skill_config_step_id),
            commit=commit,
            publish=publish,
        )
        for step in plan.steps
    ]

    return await _materialize_skill_run_receipt(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        skill_run_lane=skill_run_lane,
        request=request,
        plan=plan,
        materialized_calls=tuple(materialized_calls),
        commit=commit,
        publish=publish,
    )


async def materialize_skill_run_from_package_refs(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    skill_package_ref: SkillRuntimePackageRef,
    api_package_refs: Sequence[ApiRuntimePackageRef],
    api_call_lane: MaterializationLaneContext,
    skill_run_lane: MaterializationLaneContext,
    request: SkillRunHarnessRequest,
    commit: bool = True,
    publish: bool = False,
) -> SkillRunHarnessResult:
    _require_clean_skill_package_ref(skill_package_ref)
    for api_package_ref in api_package_refs:
        _require_clean_api_package_ref(api_package_ref)

    skill_package = await resolve_committed_skill_runtime_package_ref(
        index=index,
        package_ref=skill_package_ref,
    )
    if request.skill_config_id != skill_package.skill_config_id:
        raise RuntimeError(
            "SkillRunHarnessRequest skill_config_id does not match resolved SkillPackage: "
            f"request={request.skill_config_id} package={skill_package.skill_config_id}"
        )

    api_package_bindings = tuple(
        [
            await resolve_api_runtime_package_ref(
                index=index,
                package_ref=api_package_ref,
            )
            for api_package_ref in api_package_refs
        ]
    )
    _validate_attached_api_packages(
        skill_api_package_ids=skill_package.api_package_ids,
        api_package_bindings=api_package_bindings,
    )
    source_commits_by_api_id = {
        binding.api_id: build_api_invocation_source_commit_from_package_ref(binding)
        for binding in api_package_bindings
    }
    plan = await resolve_skill_execution_plan_from_commit(
        index=index,
        branch_id=_required_uuid(
            "skill_package.semantic_branch_id", skill_package.semantic_branch_id
        ),
        projection_hash=skill_package.skill_config_projection_hash,
        commit_id=skill_package.skill_config_domain_commit_id,
        skill_config_id=skill_package.skill_config_id,
    )
    step_inputs = _step_inputs_by_id(
        planned_step_ids=tuple(step.skill_config_step_id for step in plan.steps),
        request=request,
    )
    materialized_calls: list[SkillStepApiCallMaterialization] = []
    for step in plan.steps:
        if step.api_id is None:
            raise RuntimeError(
                "Clean Skill package-ref execution requires every SkillConfigStep "
                f"to resolve its parent API id: step={step.skill_config_step_id}"
            )
        api_source_commit = source_commits_by_api_id.get(step.api_id)
        if api_source_commit is None:
            raise RuntimeError(
                "Skill package-ref execution could not resolve an attached ApiPackage "
                "for SkillConfigStep API: "
                f"step={step.skill_config_step_id} api_id={step.api_id}"
            )
        api_source_lane = MaterializationLaneContext(
            branch_id=api_source_commit.branch_id,
            projection_hash=api_source_commit.projection_hash,
        )
        materialized_calls.append(
            await materialize_skill_step_api_call(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                api_source_lane=api_source_lane,
                api_call_lane=api_call_lane,
                step=step,
                step_input=step_inputs.get(step.skill_config_step_id)
                or SkillStepApiCallInput(
                    skill_config_step_id=step.skill_config_step_id
                ),
                api_source_commit=api_source_commit,
                commit=commit,
                publish=publish,
            )
        )

    return await _materialize_skill_run_receipt(
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        skill_run_lane=skill_run_lane,
        request=request,
        plan=plan,
        materialized_calls=tuple(materialized_calls),
        commit=commit,
        publish=publish,
    )


async def _materialize_skill_run_receipt(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    skill_run_lane: MaterializationLaneContext,
    request: SkillRunHarnessRequest,
    plan: ResolvedSkillExecutionPlan,
    materialized_calls: tuple[SkillStepApiCallMaterialization, ...],
    commit: bool,
    publish: bool,
) -> SkillRunHarnessResult:
    effective_skill_run_lane = await _effective_target_lane(skill_run_lane)
    runtime_lane = runtime.bind(
        projection=effective_skill_run_lane.projection_hash,
        branch_id=effective_skill_run_lane.branch_id,
        actor_id=actor_id,
    )
    skill_run_class = _skill_run_class()
    run_status = _skill_run_status(request.run_status)
    step_status = _skill_run_status(request.step_status)

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_run = await skill_run_class.build_via_skill_config(
            skill_config_id=plan.skill_config_id,
            run_key=request.run_key,
            status=run_status,
        )
        step_receipts: list[SkillRunHarnessStepReceipt] = []
        for step, api_call in zip(plan.steps, materialized_calls, strict=True):
            skill_run_step = await skill_run.create_step(
                skill_config_step_id=step.skill_config_step_id,
                api_call_id=api_call.api_call_id,
                status=step_status,
            )
            step_receipts.append(
                SkillRunHarnessStepReceipt(
                    skill_config_step_id=step.skill_config_step_id,
                    skill_run_step_id=skill_run_step.id,
                    api_call=api_call,
                    status=request.step_status,
                )
            )

    return SkillRunHarnessResult(
        skill_config_id=plan.skill_config_id,
        skill_run_id=skill_run.id,
        run_key=request.run_key,
        status=request.run_status,
        branch_id=effective_skill_run_lane.branch_id,
        projection_hash=effective_skill_run_lane.projection_hash,
        commit_id=_required_uuid("skill_run.commit_id", runtime_lane.last_commit_id),
        head_commit_id=_required_uuid(
            "skill_run.head_commit_id", runtime_lane.last_head_commit_id
        ),
        steps=tuple(step_receipts),
    )


def _require_clean_skill_package_ref(package_ref: SkillRuntimePackageRef) -> None:
    if not _clean(package_ref.semantic_object_instance_graph_commit_id):
        raise RuntimeError(
            "Clean Skill execution requires SkillRuntimePackageRef.semantic_object_instance_graph_commit_id."
        )


def _require_clean_api_package_ref(package_ref: ApiRuntimePackageRef) -> None:
    if not _clean(package_ref.semantic_object_instance_graph_commit_id):
        raise RuntimeError(
            "Clean Skill execution requires every ApiRuntimePackageRef.semantic_object_instance_graph_commit_id."
        )


def _validate_attached_api_packages(
    *,
    skill_api_package_ids: tuple[UUID, ...],
    api_package_bindings: tuple[ResolvedApiRuntimePackageRef, ...],
) -> None:
    attached = set(skill_api_package_ids)
    provided = {binding.api_package_id for binding in api_package_bindings}
    missing = attached - provided
    extra = provided - attached
    if missing:
        raise RuntimeError(
            "Clean Skill execution missing ApiPackage refs attached to SkillPackage: "
            f"{sorted(str(item) for item in missing)!r}"
        )
    if extra:
        raise RuntimeError(
            "Clean Skill execution received ApiPackage refs not attached to SkillPackage: "
            f"{sorted(str(item) for item in extra)!r}"
        )


def _step_inputs_by_id(
    *,
    planned_step_ids: tuple[UUID, ...],
    request: SkillRunHarnessRequest,
) -> Mapping[UUID, SkillStepApiCallInput]:
    planned = set(planned_step_ids)
    inputs: dict[UUID, SkillStepApiCallInput] = {}
    for step_input in request.step_inputs:
        if step_input.skill_config_step_id not in planned:
            raise RuntimeError(
                "SkillRunHarnessRequest contains input for an unknown SkillConfigStep: "
                f"{step_input.skill_config_step_id}"
            )
        if step_input.skill_config_step_id in inputs:
            raise RuntimeError(
                "SkillRunHarnessRequest contains duplicate input for SkillConfigStep: "
                f"{step_input.skill_config_step_id}"
            )
        inputs[step_input.skill_config_step_id] = step_input
    return inputs


async def _effective_target_lane(
    lane: MaterializationLaneContext,
) -> MaterializationLaneContext:
    head = await FSCommitStore().head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if head is None or not head.get("commit_id"):
        return lane
    return MaterializationLaneContext(
        branch_id=uuid4(),
        projection_hash=lane.projection_hash,
    )


def _skill_run_class() -> Any:
    return getattr(import_module("aware_skill_ontology.skill.skill_run"), "SkillRun")


def _skill_run_status(value: str) -> Any:
    status_class = getattr(
        import_module("aware_skill_ontology.skill.skill_run_enums"), "SkillRunStatus"
    )
    return status_class(value)


def _required_uuid(label: str, value: object) -> UUID:
    if value is None:
        raise RuntimeError(
            f"{label} is required for committed Skill run materialization."
        )
    if isinstance(value, UUID):
        return value
    stripped = str(value).strip()
    if not stripped:
        raise RuntimeError(
            f"{label} is required for committed Skill run materialization."
        )
    return UUID(stripped)


def _clean(value: object) -> str | None:
    if value is None:
        return None
    stripped = str(value).strip()
    return stripped or None


__all__ = ["materialize_skill_run", "materialize_skill_run_from_package_refs"]
