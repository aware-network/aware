from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_meta.materialization import MaterializationLaneContext
from aware_meta.runtime import MetaGraphRuntimeIndex
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_enums import ServiceOperationAdmissionMode
from aware_service_ontology.service.service_enums import ServiceOperationFulfillmentKind
from aware_service_ontology.service.service_enums import ServiceOperationReceiptPolicy
from aware_service_ontology.service.service_enums import (
    ServiceOperationSettlementPolicy,
)
from aware_service_ontology.service.service_operation_config import (
    ServiceOperationConfig,
)
from aware_service_ontology.service.service_operation_config_api_endpoint import (
    ServiceOperationConfigApiEndpoint,
)
from aware_service_ontology.service.service_operation_config_api_endpoint_function import (
    ServiceOperationConfigApiEndpointFunction,
)
from aware_service_ontology.service.service_operation_config_api_view import (
    ServiceOperationConfigApiView,
)
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)

from ._lane_hydration import (
    bind_service_runtime_lane,
    hydrate_committed_lane_object,
    resolve_committed_target_lane,
)


class _RuntimeProtocol(Protocol):
    @property
    def invoker(self) -> object: ...


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationConfigBinding:
    service_operation_config_id: UUID
    service_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigMaterializationResult:
    binding: MaterializedServiceOperationConfigBinding
    service_operation_config: ServiceOperationConfig


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationConfigApiEndpointBinding:
    service_operation_config_api_endpoint_id: UUID
    service_operation_config_id: UUID
    service_config_api_id: UUID
    api_capability_endpoint_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigApiEndpointMaterializationResult:
    binding: MaterializedServiceOperationConfigApiEndpointBinding
    service_operation_config_api_endpoint: ServiceOperationConfigApiEndpoint


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationConfigApiEndpointFunctionBinding:
    service_operation_config_api_endpoint_function_id: UUID
    service_operation_config_api_endpoint_id: UUID
    api_capability_endpoint_function_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigApiEndpointFunctionMaterializationResult:
    binding: MaterializedServiceOperationConfigApiEndpointFunctionBinding
    service_operation_config_api_endpoint_function: (
        ServiceOperationConfigApiEndpointFunction
    )


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationConfigApiViewBinding:
    service_operation_config_api_view_id: UUID
    service_operation_config_id: UUID
    service_config_api_id: UUID
    api_view_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigApiViewMaterializationResult:
    binding: MaterializedServiceOperationConfigApiViewBinding
    service_operation_config_api_view: ServiceOperationConfigApiView


@dataclass(frozen=True, slots=True)
class MaterializedServiceOperationConfigRoleRequirementBinding:
    service_operation_config_role_requirement_id: UUID
    service_operation_config_id: UUID
    role_config_id: UUID
    commit_id: UUID | None
    head_commit_id: UUID | None
    branch_id: UUID
    projection_hash: str


@dataclass(frozen=True, slots=True)
class ServiceOperationConfigRoleRequirementMaterializationResult:
    binding: MaterializedServiceOperationConfigRoleRequirementBinding
    service_operation_config_role_requirement: ServiceOperationConfigRoleRequirement


async def materialize_service_operation_config(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_config_id: UUID,
    name: str,
    description: str | None = None,
    price_id: UUID | None = None,
    admission_mode: str = "contract_required",
    fulfillment_kind: str = "coordination",
    receipt_policy: ServiceOperationReceiptPolicy = ServiceOperationReceiptPolicy.committed,
    settlement_policy: ServiceOperationSettlementPolicy = ServiceOperationSettlementPolicy.none,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationConfigMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_config_ref = ServiceConfig.model_construct(id=service_config_id)
    resolved_admission_mode = ServiceOperationAdmissionMode(admission_mode)
    resolved_fulfillment_kind = ServiceOperationFulfillmentKind(fulfillment_kind)

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        create_annotations = getattr(
            service_config_ref.create_service_operation_config,
            "__annotations__",
            {},
        )
        create_kwargs = {
            "name": name,
            "description": description,
            "price_id": price_id,
            "receipt_policy": receipt_policy,
            "settlement_policy": settlement_policy,
        }
        if "admission_mode" in create_annotations:
            create_kwargs["admission_mode"] = resolved_admission_mode
        if "fulfillment_kind" in create_annotations:
            create_kwargs["fulfillment_kind"] = resolved_fulfillment_kind
        service_operation_config = (
            await service_config_ref.create_service_operation_config(**create_kwargs)
        )

    service_operation_config_id = service_operation_config.id
    if service_operation_config_id is None:
        raise RuntimeError(
            "ServiceOperationConfig materialization must produce service_operation_config.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceOperationConfigMaterializationResult(
        binding=MaterializedServiceOperationConfigBinding(
            service_operation_config_id=service_operation_config_id,
            service_config_id=service_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_operation_config=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceOperationConfig,
            object_id=service_operation_config_id,
            error_context="ServiceOperationConfig materialization",
        ),
    )


async def materialize_service_operation_config_api_view(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_operation_config_id: UUID,
    service_config_api_id: UUID,
    api_view_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationConfigApiViewMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_operation_config_ref = ServiceOperationConfig.model_construct(
        id=service_operation_config_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=True,
    ):
        view_binding = await service_operation_config_ref.create_api_view(
            service_config_api_id=service_config_api_id,
            api_view_id=api_view_id,
            description=description,
        )

    view_binding_id = view_binding.id
    if view_binding_id is None:
        raise RuntimeError(
            "ServiceOperationConfigApiView materialization must produce "
            "service_operation_config_api_view.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceOperationConfigApiViewMaterializationResult(
        binding=MaterializedServiceOperationConfigApiViewBinding(
            service_operation_config_api_view_id=view_binding_id,
            service_operation_config_id=service_operation_config_id,
            service_config_api_id=service_config_api_id,
            api_view_id=api_view_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_operation_config_api_view=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceOperationConfigApiView,
            object_id=view_binding_id,
            error_context="ServiceOperationConfigApiView materialization",
        ),
    )


async def materialize_service_operation_config_role_requirement(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_operation_config_id: UUID,
    role_config_id: UUID,
    access_scope: str = "operation",
    scope_kind: str = "operation",
    scope_ref: str = "default",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationConfigRoleRequirementMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_operation_config_ref = ServiceOperationConfig.model_construct(
        id=service_operation_config_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=True,
    ):
        role_requirement = await service_operation_config_ref.require_role(
            role_config_id=role_config_id,
            access_scope=access_scope,
            scope_kind=scope_kind,
            scope_ref=scope_ref,
            class_instance_identity_required=class_instance_identity_required,
            role_assignment_binding_required=role_assignment_binding_required,
            description=description,
        )

    role_requirement_id = role_requirement.id
    if role_requirement_id is None:
        raise RuntimeError(
            "ServiceOperationConfigRoleRequirement materialization must produce "
            "service_operation_config_role_requirement.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceOperationConfigRoleRequirementMaterializationResult(
        binding=MaterializedServiceOperationConfigRoleRequirementBinding(
            service_operation_config_role_requirement_id=role_requirement_id,
            service_operation_config_id=service_operation_config_id,
            role_config_id=role_config_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_operation_config_role_requirement=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceOperationConfigRoleRequirement,
            object_id=role_requirement_id,
            error_context="ServiceOperationConfigRoleRequirement materialization",
        ),
    )


async def materialize_service_operation_config_api_endpoint(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_operation_config_id: UUID,
    service_config_api_id: UUID,
    api_capability_endpoint_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationConfigApiEndpointMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    service_operation_config_ref = ServiceOperationConfig.model_construct(
        id=service_operation_config_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        api_endpoint = await service_operation_config_ref.create_api_endpoint(
            service_config_api_id=service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            description=description,
        )

    service_operation_config_api_endpoint_id = api_endpoint.id
    if service_operation_config_api_endpoint_id is None:
        raise RuntimeError(
            "ServiceOperationConfigApiEndpoint materialization must produce "
            "service_operation_config_api_endpoint.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceOperationConfigApiEndpointMaterializationResult(
        binding=MaterializedServiceOperationConfigApiEndpointBinding(
            service_operation_config_api_endpoint_id=service_operation_config_api_endpoint_id,
            service_operation_config_id=service_operation_config_id,
            service_config_api_id=service_config_api_id,
            api_capability_endpoint_id=api_capability_endpoint_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_operation_config_api_endpoint=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceOperationConfigApiEndpoint,
            object_id=service_operation_config_api_endpoint_id,
            error_context="ServiceOperationConfigApiEndpoint materialization",
        ),
    )


async def materialize_service_operation_config_api_endpoint_function(
    *,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_operation_config_api_endpoint_id: UUID,
    api_capability_endpoint_function_id: UUID,
    description: str | None = None,
    commit: bool = True,
    publish: bool = False,
) -> ServiceOperationConfigApiEndpointFunctionMaterializationResult:
    runtime_lane = bind_service_runtime_lane(
        runtime=runtime,
        index=index,
        branch_id=target_lane.branch_id,
        projection=target_lane.projection_hash,
        actor_id=actor_id,
    )
    api_endpoint_ref = ServiceOperationConfigApiEndpoint.model_construct(
        id=service_operation_config_api_endpoint_id
    )

    with runtime_lane.activate(
        commit=commit,
        publish=publish,
        hydrate_portal_targets=False,
    ):
        endpoint_function = await api_endpoint_ref.create_function(
            api_capability_endpoint_function_id=api_capability_endpoint_function_id,
            description=description,
        )

    endpoint_function_id = endpoint_function.id
    if endpoint_function_id is None:
        raise RuntimeError(
            "ServiceOperationConfigApiEndpointFunction materialization must produce "
            "service_operation_config_api_endpoint_function.id"
        )
    committed_lane = resolve_committed_target_lane(
        target_lane=target_lane,
        runtime_lane=runtime_lane,
    )

    return ServiceOperationConfigApiEndpointFunctionMaterializationResult(
        binding=MaterializedServiceOperationConfigApiEndpointFunctionBinding(
            service_operation_config_api_endpoint_function_id=endpoint_function_id,
            service_operation_config_api_endpoint_id=service_operation_config_api_endpoint_id,
            api_capability_endpoint_function_id=api_capability_endpoint_function_id,
            commit_id=runtime_lane.last_commit_id,
            head_commit_id=runtime_lane.last_head_commit_id,
            branch_id=committed_lane.branch_id,
            projection_hash=committed_lane.projection_hash,
        ),
        service_operation_config_api_endpoint_function=await hydrate_committed_lane_object(
            index=index,
            target_lane=committed_lane,
            orm_class=ServiceOperationConfigApiEndpointFunction,
            object_id=endpoint_function_id,
            error_context="ServiceOperationConfigApiEndpointFunction materialization",
        ),
    )


__all__ = [
    "MaterializedServiceOperationConfigApiEndpointBinding",
    "MaterializedServiceOperationConfigApiEndpointFunctionBinding",
    "MaterializedServiceOperationConfigApiViewBinding",
    "MaterializedServiceOperationConfigBinding",
    "MaterializedServiceOperationConfigRoleRequirementBinding",
    "ServiceOperationConfigApiEndpointMaterializationResult",
    "ServiceOperationConfigApiEndpointFunctionMaterializationResult",
    "ServiceOperationConfigApiViewMaterializationResult",
    "ServiceOperationConfigMaterializationResult",
    "ServiceOperationConfigRoleRequirementMaterializationResult",
    "materialize_service_operation_config",
    "materialize_service_operation_config_api_endpoint",
    "materialize_service_operation_config_api_endpoint_function",
    "materialize_service_operation_config_api_view",
    "materialize_service_operation_config_role_requirement",
]
