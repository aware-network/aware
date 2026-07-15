from __future__ import annotations

from dataclasses import dataclass
from typing import ContextManager, Protocol
from uuid import UUID

from aware_api_runtime.invocation import ApiInvocationRuntimeProtocol
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_skill_ontology.skill.skill_config import SkillConfig
from aware_skill_ontology.skill.skill_config_api import SkillConfigApi
from aware_skill_ontology.skill.skill_config_api_endpoint import SkillConfigApiEndpoint
from aware_skill_ontology.skill.skill_config_step import SkillConfigStep
from aware_skill_ontology.skill.skill_package import SkillPackage
from aware_skill_ontology.skill.skill_package_api_package import SkillPackageApiPackage

from ._lane_hydration import hydrate_committed_lane_object


class _MetaRuntimeLaneProtocol(Protocol):
    @property
    def last_commit_id(self) -> UUID | None: ...

    @property
    def last_head_commit_id(self) -> UUID | None: ...

    def activate(
        self,
        *,
        commit: bool = True,
        publish: bool = False,
    ) -> ContextManager[object]: ...


@dataclass(frozen=True, slots=True)
class MaterializedSkillConfigBinding:
    skill_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillConfigMaterializationResult:
    binding: MaterializedSkillConfigBinding
    skill_config: SkillConfig


@dataclass(frozen=True, slots=True)
class MaterializedSkillConfigApiBinding:
    skill_config_api_id: UUID
    skill_config_id: UUID
    api_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillConfigApiMaterializationResult:
    binding: MaterializedSkillConfigApiBinding
    skill_config_api: SkillConfigApi


@dataclass(frozen=True, slots=True)
class MaterializedSkillConfigApiEndpointBinding:
    skill_config_api_endpoint_id: UUID
    skill_config_api_id: UUID
    api_endpoint_id: UUID
    capability_name: str
    name: str
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillConfigApiEndpointMaterializationResult:
    binding: MaterializedSkillConfigApiEndpointBinding
    skill_config_api_endpoint: SkillConfigApiEndpoint


@dataclass(frozen=True, slots=True)
class MaterializedSkillConfigStepBinding:
    skill_config_step_id: UUID
    skill_config_id: UUID
    skill_config_api_endpoint_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillConfigStepMaterializationResult:
    binding: MaterializedSkillConfigStepBinding
    skill_config_step: SkillConfigStep


@dataclass(frozen=True, slots=True)
class MaterializedSkillPackageBinding:
    skill_package_id: UUID
    skill_config_id: UUID
    skill_config_object_instance_graph_commit_id: UUID | None
    source_code_package_id: UUID | None
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillPackageMaterializationResult:
    binding: MaterializedSkillPackageBinding
    skill_package: SkillPackage


@dataclass(frozen=True, slots=True)
class MaterializedSkillPackageApiPackageBinding:
    skill_package_api_package_id: UUID
    skill_package_id: UUID
    api_package_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class SkillPackageApiPackageMaterializationResult:
    binding: MaterializedSkillPackageApiPackageBinding
    skill_package_api_package: SkillPackageApiPackage


def _bind_skill_config_lane(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
) -> _MetaRuntimeLaneProtocol:
    return runtime.bind(
        projection=target_lane.projection_hash,
        branch_id=target_lane.branch_id,
        actor_id=actor_id,
    )


async def materialize_skill_config(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    name: str,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillConfigMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_config = await SkillConfig.build(
            name=name,
            description=description,
        )

    skill_config_id = skill_config.id
    if skill_config_id is None:
        raise RuntimeError("SkillConfig materialization must produce skill_config.id")
    committed_lane = target_lane

    return SkillConfigMaterializationResult(
        binding=MaterializedSkillConfigBinding(
            skill_config_id=skill_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_config=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillConfig,
            object_id=skill_config_id,
            error_context="SkillConfig materialization",
        ),
    )


async def materialize_skill_config_api(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    skill_config_id: UUID,
    api_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillConfigApiMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )
    skill_config_ref = SkillConfig.model_construct(id=skill_config_id)

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_config_api = await skill_config_ref.add_api(
            api_id=api_id,
            description=description,
        )

    skill_config_api_id = skill_config_api.id
    if skill_config_api_id is None:
        raise RuntimeError(
            "SkillConfigApi materialization must produce skill_config_api.id"
        )
    committed_lane = target_lane

    return SkillConfigApiMaterializationResult(
        binding=MaterializedSkillConfigApiBinding(
            skill_config_api_id=skill_config_api_id,
            skill_config_id=skill_config_id,
            api_id=api_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_config_api=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillConfigApi,
            object_id=skill_config_api_id,
            error_context="SkillConfigApi materialization",
        ),
    )


async def materialize_skill_config_api_endpoint(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    skill_config_api_id: UUID,
    api_endpoint_id: UUID,
    capability_name: str,
    name: str,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillConfigApiEndpointMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )
    skill_config_api_ref = SkillConfigApi.model_construct(id=skill_config_api_id)

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_config_api_endpoint = await skill_config_api_ref.add_api_endpoint(
            api_endpoint_id=api_endpoint_id,
            capability_name=capability_name,
            name=name,
            description=description,
        )

    skill_config_api_endpoint_id = skill_config_api_endpoint.id
    if skill_config_api_endpoint_id is None:
        raise RuntimeError(
            "SkillConfigApiEndpoint materialization must produce skill_config_api_endpoint.id"
        )
    committed_lane = target_lane

    return SkillConfigApiEndpointMaterializationResult(
        binding=MaterializedSkillConfigApiEndpointBinding(
            skill_config_api_endpoint_id=skill_config_api_endpoint_id,
            skill_config_api_id=skill_config_api_id,
            api_endpoint_id=api_endpoint_id,
            capability_name=capability_name,
            name=name,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_config_api_endpoint=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillConfigApiEndpoint,
            object_id=skill_config_api_endpoint_id,
            error_context="SkillConfigApiEndpoint materialization",
        ),
    )


async def materialize_skill_config_step(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    skill_config_id: UUID,
    position: int,
    skill_config_api_endpoint_id: UUID,
    instruction: str,
    commit: bool = True,
    publish: bool = False,
) -> SkillConfigStepMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )
    skill_config_ref = SkillConfig.model_construct(id=skill_config_id)

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_config_step = await skill_config_ref.add_step(
            position=position,
            skill_config_api_endpoint_id=skill_config_api_endpoint_id,
            instruction=instruction,
        )

    skill_config_step_id = skill_config_step.id
    if skill_config_step_id is None:
        raise RuntimeError(
            "SkillConfigStep materialization must produce skill_config_step.id"
        )
    committed_lane = target_lane

    return SkillConfigStepMaterializationResult(
        binding=MaterializedSkillConfigStepBinding(
            skill_config_step_id=skill_config_step_id,
            skill_config_id=skill_config_id,
            skill_config_api_endpoint_id=skill_config_api_endpoint_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_config_step=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillConfigStep,
            object_id=skill_config_step_id,
            error_context="SkillConfigStep materialization",
        ),
    )


async def materialize_skill_package(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    name: str,
    skill_config_id: UUID,
    skill_config_object_instance_graph_commit_id: UUID | None = None,
    source_code_package_id: UUID | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillPackageMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_package = await SkillPackage.build(
            name=name,
            skill_config_id=skill_config_id,
            skill_config_object_instance_graph_commit_id=skill_config_object_instance_graph_commit_id,
            source_code_package_id=source_code_package_id,
        )

    skill_package_id = skill_package.id
    if skill_package_id is None:
        raise RuntimeError("SkillPackage materialization must produce skill_package.id")
    committed_lane = target_lane

    return SkillPackageMaterializationResult(
        binding=MaterializedSkillPackageBinding(
            skill_package_id=skill_package_id,
            skill_config_id=skill_config_id,
            skill_config_object_instance_graph_commit_id=skill_config_object_instance_graph_commit_id,
            source_code_package_id=source_code_package_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_package=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillPackage,
            object_id=skill_package_id,
            error_context="SkillPackage materialization",
        ),
    )


async def materialize_skill_package_api_package(
    *,
    runtime: ApiInvocationRuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    skill_package_id: UUID,
    api_package_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> SkillPackageApiPackageMaterializationResult:
    runtime_lane = _bind_skill_config_lane(
        runtime=runtime,
        actor_id=actor_id,
        target_lane=target_lane,
    )
    skill_package_ref = SkillPackage.model_construct(id=skill_package_id)

    with runtime_lane.activate(commit=commit, publish=publish):
        skill_package_api_package = await skill_package_ref.attach_api_package(
            api_package_id=api_package_id,
            description=description,
        )

    skill_package_api_package_id = skill_package_api_package.id
    if skill_package_api_package_id is None:
        raise RuntimeError(
            "SkillPackageApiPackage materialization must produce skill_package_api_package.id"
        )
    committed_lane = target_lane

    return SkillPackageApiPackageMaterializationResult(
        binding=MaterializedSkillPackageApiPackageBinding(
            skill_package_api_package_id=skill_package_api_package_id,
            skill_package_id=skill_package_id,
            api_package_id=api_package_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        skill_package_api_package=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=SkillPackageApiPackage,
            object_id=skill_package_api_package_id,
            error_context="SkillPackageApiPackage materialization",
        ),
    )


__all__ = [
    "MaterializedSkillConfigApiBinding",
    "MaterializedSkillConfigApiEndpointBinding",
    "MaterializedSkillConfigBinding",
    "MaterializedSkillConfigStepBinding",
    "MaterializedSkillPackageApiPackageBinding",
    "MaterializedSkillPackageBinding",
    "SkillConfigApiEndpointMaterializationResult",
    "SkillConfigApiMaterializationResult",
    "SkillConfigMaterializationResult",
    "SkillConfigStepMaterializationResult",
    "SkillPackageApiPackageMaterializationResult",
    "SkillPackageMaterializationResult",
    "materialize_skill_config",
    "materialize_skill_config_api",
    "materialize_skill_config_api_endpoint",
    "materialize_skill_config_step",
    "materialize_skill_package",
    "materialize_skill_package_api_package",
]
