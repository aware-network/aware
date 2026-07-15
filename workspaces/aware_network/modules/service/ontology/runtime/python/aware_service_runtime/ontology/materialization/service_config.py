from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_code.types import JsonObject
from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_branch import ServiceBranch
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_config_api_projection import (
    ServiceConfigApiProjection,
)
from aware_service_ontology.service.service_config_experience import (
    ServiceConfigExperience,
)
from aware_service_ontology.service.service_contract_config import ServiceContractConfig
from aware_service_ontology.service.service_contract_config_actor_role_grant import (
    ServiceContractConfigActorRoleGrant,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import ServiceContractKind

from ._lane_hydration import (
    bind_service_runtime_lane,
    hydrate_committed_lane_object,
    resolve_committed_target_lane,
)


class _RuntimeProtocol(Protocol):
    @property
    def invoker(self) -> object: ...


@dataclass(frozen=True, slots=True)
class MaterializedServiceConfigBinding:
    service_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceConfigMaterializationResult:
    binding: MaterializedServiceConfigBinding
    service_config: ServiceConfig


@dataclass(frozen=True, slots=True)
class MaterializedServiceConfigApiBinding:
    service_config_api_id: UUID
    service_config_id: UUID
    api_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceConfigApiMaterializationResult:
    binding: MaterializedServiceConfigApiBinding
    service_config_api: ServiceConfigApi


@dataclass(frozen=True, slots=True)
class MaterializedServiceConfigExperienceBinding:
    service_config_experience_id: UUID
    service_config_id: UUID
    projection_experience_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceConfigExperienceMaterializationResult:
    binding: MaterializedServiceConfigExperienceBinding
    service_config_experience: ServiceConfigExperience


@dataclass(frozen=True, slots=True)
class MaterializedServiceContractConfigBinding:
    service_contract_config_id: UUID
    service_config_id: UUID
    projection_experience_id: UUID | None
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceContractConfigMaterializationResult:
    binding: MaterializedServiceContractConfigBinding
    service_contract_config: ServiceContractConfig


@dataclass(frozen=True, slots=True)
class MaterializedServiceContractConfigOperationGrantBinding:
    service_contract_config_operation_grant_id: UUID
    service_contract_config_id: UUID
    service_operation_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceContractConfigOperationGrantMaterializationResult:
    binding: MaterializedServiceContractConfigOperationGrantBinding
    service_contract_config_operation_grant: ServiceContractConfigOperationGrant


@dataclass(frozen=True, slots=True)
class MaterializedServiceContractConfigActorRoleGrantBinding:
    service_contract_config_actor_role_grant_id: UUID
    service_contract_config_id: UUID
    role_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceContractConfigActorRoleGrantMaterializationResult:
    binding: MaterializedServiceContractConfigActorRoleGrantBinding
    service_contract_config_actor_role_grant: ServiceContractConfigActorRoleGrant


@dataclass(frozen=True, slots=True)
class MaterializedServiceConfigApiProjectionBinding:
    service_config_api_projection_id: UUID
    service_config_api_id: UUID
    api_graph_projection_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceConfigApiProjectionMaterializationResult:
    binding: MaterializedServiceConfigApiProjectionBinding
    service_config_api_projection: ServiceConfigApiProjection


@dataclass(frozen=True, slots=True)
class MaterializedServiceBinding:
    service_id: UUID
    service_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceMaterializationResult:
    binding: MaterializedServiceBinding
    service: Service


@dataclass(frozen=True, slots=True)
class MaterializedServiceBranchBinding:
    service_branch_id: UUID
    service_id: UUID
    service_config_api_projection_id: UUID
    object_instance_graph_branch_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceBranchMaterializationResult:
    binding: MaterializedServiceBranchBinding
    service_branch: ServiceBranch


async def materialize_service_config(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    name: str,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceConfigMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service_config = await ServiceConfig.build(
            name=name,
            description=description,
        )

    service_config_id = service_config.id
    if service_config_id is None:
        raise RuntimeError(
            "ServiceConfig materialization must produce service_config.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceConfigMaterializationResult(
        binding=MaterializedServiceConfigBinding(
            service_config_id=service_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_config=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceConfig,
            object_id=service_config_id,
            error_context="ServiceConfig materialization",
        ),
    )


async def materialize_service_config_api(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_id: UUID,
    api_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceConfigApiMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_config_ref = ServiceConfig.model_construct(id=service_config_id)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service_config_api = await service_config_ref.create_api(
            api_id=api_id,
            description=description,
        )

    service_config_api_id = service_config_api.id
    if service_config_api_id is None:
        raise RuntimeError(
            "ServiceConfigApi materialization must produce service_config_api.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceConfigApiMaterializationResult(
        binding=MaterializedServiceConfigApiBinding(
            service_config_api_id=service_config_api_id,
            service_config_id=service_config_id,
            api_id=api_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_config_api=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceConfigApi,
            object_id=service_config_api_id,
            error_context="ServiceConfigApi materialization",
        ),
    )


async def materialize_service_config_experience(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_id: UUID,
    projection_experience_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceConfigExperienceMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_config_ref = ServiceConfig.model_construct(id=service_config_id)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service_config_experience = await service_config_ref.create_experience(
            projection_experience_id=projection_experience_id,
            description=description,
        )

    service_config_experience_id = service_config_experience.id
    if service_config_experience_id is None:
        raise RuntimeError(
            "ServiceConfigExperience materialization must produce service_config_experience.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceConfigExperienceMaterializationResult(
        binding=MaterializedServiceConfigExperienceBinding(
            service_config_experience_id=service_config_experience_id,
            service_config_id=service_config_id,
            projection_experience_id=projection_experience_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_config_experience=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceConfigExperience,
            object_id=service_config_experience_id,
            error_context="ServiceConfigExperience materialization",
        ),
    )


async def materialize_service_contract_config(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_id: UUID,
    name: str,
    default_kind: ServiceContractKind = ServiceContractKind.subscription,
    projection_experience_id: UUID | None = None,
    description: str | None = None,
    metadata_json: JsonObject | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceContractConfigMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_config_ref = ServiceConfig.model_construct(id=service_config_id)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=True,
    ):
        service_contract_config = await service_config_ref.create_contract_config(
            name=name,
            default_kind=default_kind,
            projection_experience_id=projection_experience_id,
            description=description,
            metadata_json=metadata_json or JsonObject(),
        )

    service_contract_config_id = service_contract_config.id
    if service_contract_config_id is None:
        raise RuntimeError(
            "ServiceContractConfig materialization must produce service_contract_config.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceContractConfigMaterializationResult(
        binding=MaterializedServiceContractConfigBinding(
            service_contract_config_id=service_contract_config_id,
            service_config_id=service_config_id,
            projection_experience_id=projection_experience_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_contract_config=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceContractConfig,
            object_id=service_contract_config_id,
            error_context="ServiceContractConfig materialization",
        ),
    )


async def materialize_service_contract_config_operation_grant(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_contract_config_id: UUID,
    service_operation_config_id: UUID,
    access_scope: str = "operation",
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceContractConfigOperationGrantMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    contract_config_ref = ServiceContractConfig.model_construct(
        id=service_contract_config_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        operation_grant = await contract_config_ref.grant_operation(
            service_operation_config_id=service_operation_config_id,
            access_scope=access_scope,
            description=description,
        )

    operation_grant_id = operation_grant.id
    if operation_grant_id is None:
        raise RuntimeError(
            "ServiceContractConfigOperationGrant materialization must produce "
            "service_contract_config_operation_grant.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceContractConfigOperationGrantMaterializationResult(
        binding=MaterializedServiceContractConfigOperationGrantBinding(
            service_contract_config_operation_grant_id=operation_grant_id,
            service_contract_config_id=service_contract_config_id,
            service_operation_config_id=service_operation_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_contract_config_operation_grant=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceContractConfigOperationGrant,
            object_id=operation_grant_id,
            error_context="ServiceContractConfigOperationGrant materialization",
        ),
    )


async def materialize_service_contract_config_actor_role_grant(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_contract_config_id: UUID,
    role_config_id: UUID,
    scope_kind: str = "service",
    scope_ref: str = "default",
    access_scope: str = "service",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceContractConfigActorRoleGrantMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    contract_config_ref = ServiceContractConfig.model_construct(
        id=service_contract_config_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=True,
    ):
        actor_role_grant = await contract_config_ref.grant_actor_role(
            role_config_id=role_config_id,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            access_scope=access_scope,
            class_instance_identity_required=class_instance_identity_required,
            role_assignment_binding_required=role_assignment_binding_required,
            description=description,
        )

    actor_role_grant_id = actor_role_grant.id
    if actor_role_grant_id is None:
        raise RuntimeError(
            "ServiceContractConfigActorRoleGrant materialization must produce "
            "service_contract_config_actor_role_grant.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceContractConfigActorRoleGrantMaterializationResult(
        binding=MaterializedServiceContractConfigActorRoleGrantBinding(
            service_contract_config_actor_role_grant_id=actor_role_grant_id,
            service_contract_config_id=service_contract_config_id,
            role_config_id=role_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_contract_config_actor_role_grant=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceContractConfigActorRoleGrant,
            object_id=actor_role_grant_id,
            error_context="ServiceContractConfigActorRoleGrant materialization",
        ),
    )


async def materialize_service_config_api_projection(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_api_id: UUID,
    api_graph_projection_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceConfigApiProjectionMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_config_api_ref = ServiceConfigApi.model_construct(id=service_config_api_id)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service_config_api_projection = await service_config_api_ref.create_projection(
            api_graph_projection_id=api_graph_projection_id,
            description=description,
        )

    service_config_api_projection_id = service_config_api_projection.id
    if service_config_api_projection_id is None:
        raise RuntimeError(
            "ServiceConfigApiProjection materialization must produce service_config_api_projection.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceConfigApiProjectionMaterializationResult(
        binding=MaterializedServiceConfigApiProjectionBinding(
            service_config_api_projection_id=service_config_api_projection_id,
            service_config_api_id=service_config_api_id,
            api_graph_projection_id=api_graph_projection_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_config_api_projection=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceConfigApiProjection,
            object_id=service_config_api_projection_id,
            error_context="ServiceConfigApiProjection materialization",
        ),
    )


async def materialize_service(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_id: UUID,
    name: str,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service = await Service.build_via_service_config(
            service_config_id=service_config_id,
            name=name,
            description=description,
        )

    service_id = service.id
    if service_id is None:
        raise RuntimeError("Service materialization must produce service.id")
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceMaterializationResult(
        binding=MaterializedServiceBinding(
            service_id=service_id,
            service_config_id=service_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=Service,
            object_id=service_id,
            error_context="Service materialization",
        ),
    )


async def materialize_service_branch(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_id: UUID,
    service_config_api_projection_id: UUID,
    object_instance_graph_branch_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceBranchMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_ref = Service.model_construct(id=service_id)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        service_branch = await service_ref.create_branch(
            service_config_api_projection_id=service_config_api_projection_id,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            description=description,
        )

    service_branch_id = service_branch.id
    if service_branch_id is None:
        raise RuntimeError(
            "ServiceBranch materialization must produce service_branch.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceBranchMaterializationResult(
        binding=MaterializedServiceBranchBinding(
            service_branch_id=service_branch_id,
            service_id=service_id,
            service_config_api_projection_id=service_config_api_projection_id,
            object_instance_graph_branch_id=object_instance_graph_branch_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_branch=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceBranch,
            object_id=service_branch_id,
            error_context="ServiceBranch materialization",
        ),
    )


__all__ = [
    "MaterializedServiceContractConfigActorRoleGrantBinding",
    "MaterializedServiceContractConfigBinding",
    "MaterializedServiceContractConfigOperationGrantBinding",
    "MaterializedServiceBranchBinding",
    "MaterializedServiceBinding",
    "MaterializedServiceConfigApiBinding",
    "MaterializedServiceConfigApiProjectionBinding",
    "MaterializedServiceConfigBinding",
    "MaterializedServiceConfigExperienceBinding",
    "ServiceBranchMaterializationResult",
    "ServiceContractConfigActorRoleGrantMaterializationResult",
    "ServiceContractConfigMaterializationResult",
    "ServiceContractConfigOperationGrantMaterializationResult",
    "ServiceConfigApiMaterializationResult",
    "ServiceConfigApiProjectionMaterializationResult",
    "ServiceConfigMaterializationResult",
    "ServiceConfigExperienceMaterializationResult",
    "ServiceMaterializationResult",
    "materialize_service_branch",
    "materialize_service",
    "materialize_service_config",
    "materialize_service_config_api",
    "materialize_service_config_api_projection",
    "materialize_service_config_experience",
    "materialize_service_contract_config",
    "materialize_service_contract_config_actor_role_grant",
    "materialize_service_contract_config_operation_grant",
]
