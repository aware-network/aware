from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TypeVar
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_code.types import JsonArray, JsonObject
from aware_code_ontology.code.code_enums import CodeLanguage
from aware_identity_ontology.role.role_config import RoleConfig
from aware_identity_ontology.stable_ids import stable_role_config_id
from aware_meta.graph.instance.builder import build_rooted_object_instance_graph_base
from aware_meta.graph.instance.commit.committer import FSLaneCommitter
from aware_meta.graph.instance.commit.contract import CommitActionDescriptor
from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore
from aware_meta.graph.instance.commit.materializer import OIGMaterializer
from aware_meta.graph.instance.diff_orm import (
    build_object_instance_graph_changes_from_orm_change_set,
)
from aware_meta_ontology.stable_ids import (
    stable_object_instance_graph_commit_id,
    stable_object_instance_graph_id,
    stable_object_instance_graph_identity_id,
)
from aware_orm.models.base_model import BaseORMModel
from aware_orm.session.change_collector import ORMChangeSet
from aware_meta.runtime.author import resolve_meta_author_id
from aware_meta.runtime.graph_identity import resolve_meta_graph_ocgi_opgi
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_post import materialize_meta_oig_post
from aware_meta.runtime.value_resolvers import default_meta_enum_option_resolver
from aware_service_ontology.service.service_api_provider_set import (
    ServiceApiProviderSet,
)
from aware_service_ontology.service.service_api_provider_set_service_package import (
    ServiceApiProviderSetServicePackage,
)
from aware_service_ontology.service.service_config import ServiceConfig
from aware_service_ontology.service.service_config_api import ServiceConfigApi
from aware_service_ontology.service.service_config_api_projection import (
    ServiceConfigApiProjection,
)
from aware_service_ontology.service.service_config_code_package_config import (
    ServiceConfigCodePackageConfig,
)
from aware_service_ontology.service.service_config_experience import (
    ServiceConfigExperience,
)
from aware_service_ontology.service.service_contract import ServiceContract
from aware_service_ontology.service.service_contract_config import (
    ServiceContractConfig,
)
from aware_service_ontology.service.service_contract_config_actor_role_grant import (
    ServiceContractConfigActorRoleGrant,
)
from aware_service_ontology.service.service_contract_config_operation_grant import (
    ServiceContractConfigOperationGrant,
)
from aware_service_ontology.service.service_enums import (
    ServiceConfigCodePackageConfigCardinality,
    ServiceContractKind,
    ServiceContractStatus,
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
    ServiceOperationStatus,
    ServiceSubscriptionStatus,
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
from aware_service_ontology.service.service import Service
from aware_service_ontology.service.service_operation import ServiceOperation
from aware_service_ontology.service.service_package import ServicePackage
from aware_service_ontology.service.service_package_implementation_package import (
    ServicePackageImplementationPackage,
)
from aware_service_ontology.service.service_package_ontology_package import (
    ServicePackageOntologyPackage,
)
from aware_service_ontology.service.service_package_object_config_graph_package import (
    ServicePackageObjectConfigGraphPackage,
)
from aware_service_ontology.service.service_package_provided_api_package import (
    ServicePackageProvidedApiPackage,
)
from aware_service_ontology.service.service_package_required_api_package import (
    ServicePackageRequiredApiPackage,
)
from aware_service_ontology.service.service_subscription import ServiceSubscription
from aware_service_ontology.stable_ids import (
    stable_service_api_provider_set_id,
    stable_service_api_provider_set_service_package_id,
    stable_service_commercial_profile_id,
    stable_service_config_api_id,
    stable_service_config_api_projection_id,
    stable_service_config_code_package_config_id,
    stable_service_config_experience_id,
    stable_service_config_id,
    stable_service_contract_config_actor_role_grant_id,
    stable_service_contract_config_id,
    stable_service_contract_config_operation_grant_id,
    stable_service_contract_id,
    stable_service_id,
    stable_service_operation_id,
    stable_service_operation_config_api_endpoint_function_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_api_view_id,
    stable_service_operation_config_id,
    stable_service_operation_config_role_requirement_id,
    stable_service_package_id,
    stable_service_package_implementation_package_id,
    stable_service_package_ontology_package_id,
    stable_service_package_object_config_graph_package_id,
    stable_service_package_provided_api_package_id,
    stable_service_package_required_api_package_id,
    stable_service_subscription_id,
)

from ..api_ingress.telemetry import (
    await_with_service_api_trace,
    service_api_trace_phase,
)

_TModel = TypeVar("_TModel", bound=BaseORMModel)


@dataclass(frozen=True, slots=True)
class ServiceDefinitionApiSnapshot:
    api_id: UUID
    api_graph_projection_ids: tuple[UUID, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceDefinitionExperienceSnapshot:
    projection_experience_id: UUID


@dataclass(frozen=True, slots=True)
class ServiceDefinitionCodePackageConfigSnapshot:
    slot_key: str
    code_package_config_id: UUID
    cardinality: str = "many"
    required: bool = False
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceDefinitionEndpointFunctionSnapshot:
    api_capability_endpoint_function_id: UUID


@dataclass(frozen=True, slots=True)
class ServiceDefinitionEndpointSnapshot:
    service_config_api_id: UUID
    api_capability_endpoint_id: UUID
    endpoint_functions: tuple[ServiceDefinitionEndpointFunctionSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceDefinitionApiViewSnapshot:
    service_config_api_id: UUID
    api_view_id: UUID


@dataclass(frozen=True, slots=True)
class ServiceDefinitionRoleRequirementSnapshot:
    role_config_id: UUID
    access_scope: str = "operation"
    scope_kind: str = "operation"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceDefinitionOperationSnapshot:
    name: str
    price_id: UUID | None
    settlement_policy: ServiceOperationSettlementPolicy
    admission_mode: str = "contract_required"
    fulfillment_kind: ServiceOperationFulfillmentKind = (
        ServiceOperationFulfillmentKind.coordination
    )
    receipt_policy: ServiceOperationReceiptPolicy = (
        ServiceOperationReceiptPolicy.committed
    )
    endpoints: tuple[ServiceDefinitionEndpointSnapshot, ...] = ()
    api_views: tuple[ServiceDefinitionApiViewSnapshot, ...] = ()
    role_requirements: tuple[ServiceDefinitionRoleRequirementSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceDefinitionOperationGrantSnapshot:
    service_operation_config_id: UUID
    access_scope: str = "operation"


@dataclass(frozen=True, slots=True)
class ServiceDefinitionActorRoleGrantSnapshot:
    role_config_id: UUID
    access_scope: str = "service"
    scope_kind: str = "service"
    scope_ref: str = "default"
    class_instance_identity_required: bool = False
    role_assignment_binding_required: bool = True


@dataclass(frozen=True, slots=True)
class ServiceDefinitionContractSnapshot:
    name: str
    default_kind: ServiceContractKind
    projection_experience_id: UUID | None
    operation_grants: tuple[ServiceDefinitionOperationGrantSnapshot, ...] = ()
    actor_role_grants: tuple[ServiceDefinitionActorRoleGrantSnapshot, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceConfigDefinitionSnapshotCommitResult:
    service_config: ServiceConfig
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ServiceInstanceSnapshotCommitResult:
    service: Service
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ServiceOperationSnapshotCommitResult:
    service_operation: ServiceOperation
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ServiceContractAccessSnapshotCommitResult:
    service_contract_config: ServiceContractConfig
    service_contract: ServiceContract
    service_subscription: ServiceSubscription
    service_contract_config_commit_id: UUID
    service_contract_commit_id: UUID
    service_subscription_commit_id: UUID
    service_contract_config_head_commit_id: UUID
    service_contract_head_commit_id: UUID
    service_subscription_head_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ServicePackageImplementationSnapshot:
    code_package_id: UUID
    package_name: str
    language: CodeLanguage
    import_root: str
    manifest_relative_path: str
    package_root: str = "."
    entrypoint: str | None = None
    role: str = "service_bindings"
    include_paths: JsonArray = field(default_factory=JsonArray)
    exclude_paths: JsonArray = field(default_factory=JsonArray)


@dataclass(frozen=True, slots=True)
class ServicePackageApiPackageSnapshot:
    api_package_id: UUID
    package_name: str | None = None
    api_package_object_instance_graph_commit_id: UUID | None = None
    service_protocol_package_id: UUID | None = None
    service_protocol_code_package_id: UUID | None = None
    service_protocol_code_package_object_instance_graph_commit_id: UUID | None = None
    service_protocol_plan_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ServicePackageOntologyPackageSnapshot:
    ontology_package_id: UUID
    package_name: str
    fqn_prefix: str
    role: str = "replica"
    requirement_mode: str = "required"
    ontology_package_object_instance_graph_commit_id: UUID | None = None
    expected_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ServicePackageObjectConfigGraphPackageSnapshot:
    object_config_graph_package_id: UUID
    manifest_relative_path: str
    role: str = "local_state"
    package_kind: str = "state"
    object_config_graph_package_object_instance_graph_commit_id: UUID | None = None
    expected_hash_sha256: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class ServicePackageManifestSnapshotCommitResult:
    service_package: ServicePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class ServiceApiProviderSetSnapshotCommitResult:
    provider_set: ServiceApiProviderSet
    membership: ServiceApiProviderSetServicePackage
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


@dataclass(frozen=True, slots=True)
class RoleConfigReferenceSnapshotCommitResult:
    role_configs: tuple[RoleConfig, ...]
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


_SERVICE_CONFIG_DEFINITION_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/config/definition-snapshot-commit/v1",
)
_SERVICE_INSTANCE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/instance/snapshot-commit/v1",
)
_SERVICE_OPERATION_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/operation/snapshot-commit/v1",
)
_SERVICE_CONTRACT_ACCESS_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/contract-access/snapshot-commit/v1",
)
_LOCAL_SERVICE_CONTRACT_ACCESS_ID_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/contract-access/local-ids/v1",
)
_SERVICE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/package/manifest-snapshot-commit/v1",
)
_SERVICE_API_PROVIDER_SET_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://service/api-provider-set/snapshot-commit/v1",
)
_ROLE_CONFIG_REFERENCE_SNAPSHOT_COMMIT_NAMESPACE = uuid5(
    NAMESPACE_URL,
    "aware://identity/role-config/reference-snapshot-commit/v1",
)


async def commit_service_config_definition_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    apis: Sequence[ServiceDefinitionApiSnapshot],
    experiences: Sequence[ServiceDefinitionExperienceSnapshot],
    code_package_configs: Sequence[ServiceDefinitionCodePackageConfigSnapshot],
    operations: Sequence[ServiceDefinitionOperationSnapshot],
    contract_configs: Sequence[ServiceDefinitionContractSnapshot],
) -> ServiceConfigDefinitionSnapshotCommitResult:
    service_config, objects_by_id = _build_service_config_definition_snapshot_objects(
        name=name,
        apis=apis,
        experiences=experiences,
        code_package_configs=code_package_configs,
        operations=operations,
        contract_configs=contract_configs,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=service_config.id,
        root_object=service_config,
        objects_by_id=objects_by_id,
        operation_label="ServiceConfig.materialize_definition_snapshot",
        commit_id_namespace=_SERVICE_CONFIG_DEFINITION_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ServiceConfigDefinitionSnapshotCommitResult(
        service_config=service_config,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_service_instance_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    service_config_id: UUID,
    name: str,
    description: str | None = None,
) -> ServiceInstanceSnapshotCommitResult:
    service_name = (name or "").strip()
    if not service_name:
        raise RuntimeError("Service instance snapshot requires non-empty name")
    service = Service(
        id=stable_service_id(
            service_config_id=service_config_id,
            name=service_name,
        ),
        service_config_id=service_config_id,
        name=service_name,
        description=description,
    )
    service_id = service.id
    if service_id is None:
        raise RuntimeError("Service instance snapshot produced Service without id")
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=service_id,
        root_object=service,
        objects_by_id={service_id: service},
        operation_label="Service.materialize_instance_snapshot",
        commit_id_namespace=_SERVICE_INSTANCE_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ServiceInstanceSnapshotCommitResult(
        service=service,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_service_contract_access_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_config_branch_id: UUID,
    service_config_projection_hash: str,
    service_contract_branch_id: UUID,
    service_contract_projection_hash: str,
    service_subscription_branch_id: UUID,
    service_subscription_projection_hash: str,
    service_config_id: UUID,
    service_name: str,
    service_id: UUID,
    consumer_finance_entity_id: UUID,
    service_contract_config_name: str,
    service_contract_config_id: UUID | None = None,
    service_contract_id: UUID | None = None,
    service_subscription_id: UUID | None = None,
    smart_contract_id: UUID | None = None,
    commercial_profile_id: UUID | None = None,
    producer_finance_entity_id: UUID | None = None,
    service_plan_id: UUID | None = None,
    effective_from: datetime | None = None,
    metadata_json: JsonObject | None = None,
) -> ServiceContractAccessSnapshotCommitResult:
    contract_config_name = (service_contract_config_name or "").strip() or "local_dev"
    contract_config_id = (
        service_contract_config_id
        or stable_service_contract_config_id(
            service_config_id=service_config_id,
            name=contract_config_name,
        )
    )
    effective_smart_contract_id = smart_contract_id or _local_service_access_uuid(
        "smart_contract",
        str(service_id),
        str(consumer_finance_entity_id),
    )
    effective_service_contract_id = service_contract_id or stable_service_contract_id(
        service_id=service_id,
        service_contract_config_id=contract_config_id,
        smart_contract_id=effective_smart_contract_id,
    )
    effective_service_subscription_id = (
        service_subscription_id
        or stable_service_subscription_id(
            consumer_finance_entity_id=consumer_finance_entity_id,
            service_id=service_id,
        )
    )
    effective_metadata = JsonObject(
        {
            "source": "aware.service.contract_access.local_snapshot.v0",
            "service_id": str(service_id),
            "consumer_finance_entity_id": str(consumer_finance_entity_id),
            **dict(metadata_json or {}),
        }
    )
    started_at = effective_from or datetime.now(UTC)
    contract_config = ServiceContractConfig(
        id=contract_config_id,
        service_config_id=service_config_id,
        name=contract_config_name,
        default_kind=ServiceContractKind.subscription,
        projection_experience_id=None,
        description="Local Service contract access config.",
        metadata_json=effective_metadata,
    )
    service_config = ServiceConfig(
        id=service_config_id,
        name=(service_name or "").strip(),
        description=None,
    )
    service_config.contract_configs.append(contract_config)
    service_contract = ServiceContract(
        id=effective_service_contract_id,
        service_id=service_id,
        service_contract_config_id=contract_config_id,
        commercial_profile_id=commercial_profile_id
        or stable_service_commercial_profile_id(service_id=service_id),
        producer_finance_entity_id=producer_finance_entity_id
        or _local_service_access_uuid("producer_finance_entity", str(service_id)),
        consumer_finance_entity_id=consumer_finance_entity_id,
        smart_contract_id=effective_smart_contract_id,
        kind=ServiceContractKind.subscription,
        effective_from=started_at,
        effective_until=None,
        status=ServiceContractStatus.active,
        metadata_json=effective_metadata,
    )
    service_subscription = ServiceSubscription(
        id=effective_service_subscription_id,
        consumer_finance_entity_id=consumer_finance_entity_id,
        service_id=service_id,
        plan_id=service_plan_id
        or _local_service_access_uuid("service_plan", str(service_id)),
        contract_id=effective_smart_contract_id,
        external_subscription_handle=(
            "aware-local:"
            f"{service_id}:"
            f"{consumer_finance_entity_id}:"
            f"{contract_config_name}"
        ),
        status=ServiceSubscriptionStatus.active,
        current_period_start=started_at,
        current_period_end=None,
        cancel_at_period_end=False,
        metadata_json=effective_metadata,
    )
    contract_config_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=service_config_branch_id,
        projection_hash=service_config_projection_hash,
        root_object_id=service_config_id,
        root_object=service_config,
        objects_by_id={
            service_config_id: service_config,
            contract_config_id: contract_config,
        },
        operation_label="ServiceContractConfig.ensure_local_access_snapshot",
        commit_id_namespace=_SERVICE_CONTRACT_ACCESS_SNAPSHOT_COMMIT_NAMESPACE,
    )
    service_contract_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=service_contract_branch_id,
        projection_hash=service_contract_projection_hash,
        root_object_id=effective_service_contract_id,
        root_object=service_contract,
        objects_by_id={effective_service_contract_id: service_contract},
        operation_label="ServiceContract.ensure_local_access_snapshot",
        commit_id_namespace=_SERVICE_CONTRACT_ACCESS_SNAPSHOT_COMMIT_NAMESPACE,
    )
    service_subscription_commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=service_subscription_branch_id,
        projection_hash=service_subscription_projection_hash,
        root_object_id=effective_service_subscription_id,
        root_object=service_subscription,
        objects_by_id={effective_service_subscription_id: service_subscription},
        operation_label="ServiceSubscription.ensure_local_access_snapshot",
        commit_id_namespace=_SERVICE_CONTRACT_ACCESS_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ServiceContractAccessSnapshotCommitResult(
        service_contract_config=contract_config,
        service_contract=service_contract,
        service_subscription=service_subscription,
        service_contract_config_commit_id=contract_config_commit.commit_id,
        service_contract_commit_id=service_contract_commit.commit_id,
        service_subscription_commit_id=service_subscription_commit.commit_id,
        service_contract_config_head_commit_id=contract_config_commit.head_commit_id,
        service_contract_head_commit_id=service_contract_commit.head_commit_id,
        service_subscription_head_commit_id=service_subscription_commit.head_commit_id,
        object_count=(
            contract_config_commit.object_count
            + service_contract_commit.object_count
            + service_subscription_commit.object_count
        ),
        change_count=(
            contract_config_commit.change_count
            + service_contract_commit.change_count
            + service_subscription_commit.change_count
        ),
    )


async def commit_service_operation_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    service: Service,
    service_operation_config_id: UUID,
    operation_key: str,
    api_call_id: UUID | None,
    api_endpoint_id: UUID | None,
    status: ServiceOperationStatus,
    result_info: str | None,
    execution_context: JsonObject | None,
) -> ServiceOperationSnapshotCommitResult:
    service_id = service.id
    if service_id is None:
        raise RuntimeError("ServiceOperation snapshot requires Service.id")
    normalized_operation_key = (operation_key or "").strip()
    if not normalized_operation_key:
        raise RuntimeError("ServiceOperation snapshot requires non-empty operation_key")

    service_operation = ServiceOperation(
        id=stable_service_operation_id(
            service_id=service_id,
            service_operation_config_id=service_operation_config_id,
            operation_key=normalized_operation_key,
        ),
        service_id=service_id,
        api_call_id=api_call_id,
        api_endpoint_id=api_endpoint_id,
        service_operation_config_id=service_operation_config_id,
        operation_key=normalized_operation_key,
        status=status,
        result_info=result_info,
        execution_context=JsonObject(dict(execution_context or {})),
    )
    service_operation_id = service_operation.id
    if service_operation_id is None:
        raise RuntimeError(
            "ServiceOperation snapshot produced ServiceOperation without id"
        )

    preserved_operations = [
        existing
        for existing in service.service_operations
        if existing.id != service_operation_id
    ]
    service.service_operations = [*preserved_operations, service_operation]
    objects_by_id: dict[UUID, BaseORMModel] = {
        service_id: service,
        service_operation_id: service_operation,
    }
    for existing in preserved_operations:
        existing_id = existing.id
        if existing_id is not None:
            objects_by_id[existing_id] = existing

    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=service_id,
        root_object=service,
        objects_by_id=objects_by_id,
        operation_label="ServiceOperation.materialize_snapshot",
        commit_id_namespace=_SERVICE_OPERATION_SNAPSHOT_COMMIT_NAMESPACE,
        commit_action_object_id=service_operation_id,
    )
    return ServiceOperationSnapshotCommitResult(
        service_operation=service_operation,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_service_package_manifest_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    name: str,
    service_config_id: UUID,
    service_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_service_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    service_surface: str,
    activation_mode: str,
    materialize_on_start: bool,
    dependencies: JsonArray,
    implementation_packages: Sequence[ServicePackageImplementationSnapshot],
    ontology_packages: Sequence[ServicePackageOntologyPackageSnapshot],
    object_config_graph_packages: Sequence[
        ServicePackageObjectConfigGraphPackageSnapshot
    ],
    provided_api_packages: Sequence[ServicePackageApiPackageSnapshot],
    required_api_packages: Sequence[ServicePackageApiPackageSnapshot],
) -> ServicePackageManifestSnapshotCommitResult:
    service_package, objects_by_id = _build_service_package_manifest_snapshot_objects(
        name=name,
        service_config_id=service_config_id,
        service_config_object_instance_graph_commit_id=(
            service_config_object_instance_graph_commit_id
        ),
        source_code_package_id=source_code_package_id,
        fqn_prefix=fqn_prefix,
        version_number=version_number,
        title=title,
        description=description,
        aware_service_version=aware_service_version,
        manifest_relative_path=manifest_relative_path,
        package_root=package_root,
        sources_root=sources_root,
        include_paths=include_paths,
        exclude_paths=exclude_paths,
        force_fresh_scan=force_fresh_scan,
        compilation_mode=compilation_mode,
        service_surface=service_surface,
        activation_mode=activation_mode,
        materialize_on_start=materialize_on_start,
        dependencies=dependencies,
        implementation_packages=implementation_packages,
        ontology_packages=ontology_packages,
        object_config_graph_packages=object_config_graph_packages,
        provided_api_packages=provided_api_packages,
        required_api_packages=required_api_packages,
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=service_package.id,
        root_object=service_package,
        objects_by_id=objects_by_id,
        operation_label="ServicePackage.materialize_manifest_snapshot",
        commit_id_namespace=_SERVICE_PACKAGE_MANIFEST_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ServicePackageManifestSnapshotCommitResult(
        service_package=service_package,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_service_api_provider_set_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    key: str,
    title: str | None,
    description: str | None,
    version_number: int,
    service_package_id: UUID,
    membership_key: str | None,
    membership_description: str | None,
) -> ServiceApiProviderSetSnapshotCommitResult:
    provider_set, membership, objects_by_id = (
        _build_service_api_provider_set_snapshot_objects(
            key=key,
            title=title,
            description=description,
            version_number=version_number,
            service_package_id=service_package_id,
            membership_key=membership_key,
            membership_description=membership_description,
        )
    )
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=provider_set.id,
        root_object=provider_set,
        objects_by_id=objects_by_id,
        operation_label="ServiceApiProviderSet.materialize_snapshot",
        commit_id_namespace=_SERVICE_API_PROVIDER_SET_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return ServiceApiProviderSetSnapshotCommitResult(
        provider_set=provider_set,
        membership=membership,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


async def commit_role_config_reference_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    role_refs: Sequence[str],
) -> RoleConfigReferenceSnapshotCommitResult:
    role_configs, objects_by_id = _build_role_config_reference_snapshot_objects(
        role_refs=role_refs,
    )
    root_role_config = role_configs[0]
    commit = await _commit_snapshot(
        index=index,
        actor_id=actor_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        root_object_id=root_role_config.id,
        root_object=root_role_config,
        objects_by_id=objects_by_id,
        operation_label="RoleConfig.materialize_reference_snapshot",
        commit_id_namespace=_ROLE_CONFIG_REFERENCE_SNAPSHOT_COMMIT_NAMESPACE,
    )
    return RoleConfigReferenceSnapshotCommitResult(
        role_configs=role_configs,
        commit_id=commit.commit_id,
        head_commit_id=commit.head_commit_id,
        object_instance_graph_commit_id=commit.object_instance_graph_commit_id,
        object_count=commit.object_count,
        change_count=commit.change_count,
    )


def _build_role_config_reference_snapshot_objects(
    *,
    role_refs: Sequence[str],
) -> tuple[tuple[RoleConfig, ...], dict[UUID, BaseORMModel]]:
    normalized_refs = tuple(
        sorted({(role_ref or "").casefold().strip() for role_ref in role_refs})
    )
    if not normalized_refs or any(not role_ref for role_ref in normalized_refs):
        raise RuntimeError("RoleConfig reference snapshot requires role refs")

    objects_by_id: dict[UUID, BaseORMModel] = {}
    role_configs: list[RoleConfig] = []
    for role_ref in normalized_refs:
        role_configs.append(
            _remember(
                objects_by_id,
                RoleConfig(
                    id=stable_role_config_id(name=role_ref),
                    name=role_ref,
                    description=f"Service contract role reference {role_ref}.",
                ),
            )
        )
    return tuple(role_configs), objects_by_id


def _build_service_config_definition_snapshot_objects(
    *,
    name: str,
    apis: Sequence[ServiceDefinitionApiSnapshot],
    experiences: Sequence[ServiceDefinitionExperienceSnapshot],
    code_package_configs: Sequence[ServiceDefinitionCodePackageConfigSnapshot],
    operations: Sequence[ServiceDefinitionOperationSnapshot],
    contract_configs: Sequence[ServiceDefinitionContractSnapshot],
) -> tuple[ServiceConfig, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServiceConfig snapshot requires non-empty name")
    service_config = _remember(
        objects_by_id,
        ServiceConfig(
            id=stable_service_config_id(name=normalized_name),
            name=normalized_name,
            description=None,
        ),
    )
    for api in apis:
        service_config_api = _remember(
            objects_by_id,
            ServiceConfigApi(
                id=stable_service_config_api_id(
                    service_config_id=service_config.id,
                    api_id=api.api_id,
                ),
                service_config_id=service_config.id,
                api_id=api.api_id,
                description=None,
            ),
        )
        service_config.apis.append(service_config_api)
        for api_graph_projection_id in api.api_graph_projection_ids:
            projection = _remember(
                objects_by_id,
                ServiceConfigApiProjection(
                    id=stable_service_config_api_projection_id(
                        service_config_api_id=service_config_api.id,
                        api_graph_projection_id=api_graph_projection_id,
                    ),
                    service_config_api_id=service_config_api.id,
                    api_graph_projection_id=api_graph_projection_id,
                    description=None,
                ),
            )
            service_config_api.api_projections.append(projection)
    for experience in experiences:
        service_experience = _remember(
            objects_by_id,
            ServiceConfigExperience(
                id=stable_service_config_experience_id(
                    service_config_id=service_config.id,
                    projection_experience_id=experience.projection_experience_id,
                ),
                service_config_id=service_config.id,
                projection_experience_id=experience.projection_experience_id,
                description=None,
            ),
        )
        service_config.experiences.append(service_experience)
    for code_package_config_snapshot in code_package_configs:
        slot_key = (code_package_config_snapshot.slot_key or "").casefold().strip()
        if not slot_key:
            raise RuntimeError(
                f"ServiceConfig snapshot contains empty package slot: {normalized_name}"
            )
        service_config_code_package_config = _remember(
            objects_by_id,
            ServiceConfigCodePackageConfig(
                id=stable_service_config_code_package_config_id(
                    service_config_id=service_config.id,
                    code_package_config_id=(
                        code_package_config_snapshot.code_package_config_id
                    ),
                    slot_key=slot_key,
                ),
                service_config_id=service_config.id,
                slot_key=slot_key,
                code_package_config_id=(
                    code_package_config_snapshot.code_package_config_id
                ),
                cardinality=ServiceConfigCodePackageConfigCardinality(
                    code_package_config_snapshot.cardinality
                ),
                required=code_package_config_snapshot.required,
                description=code_package_config_snapshot.description,
            ),
        )
        service_config.code_package_configs.append(service_config_code_package_config)
    for operation_snapshot in operations:
        operation_name = (operation_snapshot.name or "").strip()
        if not operation_name:
            raise RuntimeError(
                f"ServiceConfig snapshot contains empty operation name: {normalized_name}"
            )
        operation = ServiceOperationConfig(
            id=stable_service_operation_config_id(
                service_config_id=service_config.id,
                name=operation_name,
            ),
            service_config_id=service_config.id,
            name=operation_name,
            description=None,
            price_id=operation_snapshot.price_id,
            admission_mode=ServiceOperationAdmissionMode(
                operation_snapshot.admission_mode
            ),
            fulfillment_kind=operation_snapshot.fulfillment_kind,
            receipt_policy=operation_snapshot.receipt_policy,
            settlement_policy=operation_snapshot.settlement_policy,
        )
        if not hasattr(operation, "admission_mode"):
            object.__setattr__(
                operation,
                "admission_mode",
                operation_snapshot.admission_mode,
            )
        if not hasattr(operation, "fulfillment_kind"):
            object.__setattr__(
                operation,
                "fulfillment_kind",
                operation_snapshot.fulfillment_kind,
            )
        operation = _remember(
            objects_by_id,
            operation,
        )
        service_config.service_operation_configs.append(operation)
        _build_operation_children(
            objects_by_id=objects_by_id,
            operation=operation,
            operation_snapshot=operation_snapshot,
        )
    for contract_snapshot in contract_configs:
        contract_name = (contract_snapshot.name or "").strip()
        if not contract_name:
            raise RuntimeError(
                f"ServiceConfig snapshot contains empty contract name: {normalized_name}"
            )
        contract = _remember(
            objects_by_id,
            ServiceContractConfig(
                id=stable_service_contract_config_id(
                    service_config_id=service_config.id,
                    name=contract_name,
                ),
                service_config_id=service_config.id,
                name=contract_name,
                default_kind=contract_snapshot.default_kind,
                projection_experience_id=contract_snapshot.projection_experience_id,
                description=None,
                metadata_json=JsonObject({}),
            ),
        )
        service_config.contract_configs.append(contract)
        for grant_snapshot in contract_snapshot.operation_grants:
            grant = _remember(
                objects_by_id,
                ServiceContractConfigOperationGrant(
                    id=stable_service_contract_config_operation_grant_id(
                        service_contract_config_id=contract.id,
                        service_operation_config_id=(
                            grant_snapshot.service_operation_config_id
                        ),
                    ),
                    service_contract_config_id=contract.id,
                    service_operation_config_id=(
                        grant_snapshot.service_operation_config_id
                    ),
                    access_scope=(grant_snapshot.access_scope or "").strip()
                    or "operation",
                    quota_policy_json=JsonObject({}),
                    permit_policy_json=JsonObject({}),
                    price_policy_json=JsonObject({}),
                    description=None,
                ),
            )
            contract.operation_grants.append(grant)
        for grant_snapshot in contract_snapshot.actor_role_grants:
            actor_grant = _remember(
                objects_by_id,
                ServiceContractConfigActorRoleGrant(
                    id=stable_service_contract_config_actor_role_grant_id(
                        service_contract_config_id=contract.id,
                        role_config_id=grant_snapshot.role_config_id,
                        scope_kind=grant_snapshot.scope_kind,
                        scope_ref=grant_snapshot.scope_ref,
                    ),
                    service_contract_config_id=contract.id,
                    role_config_id=grant_snapshot.role_config_id,
                    scope_kind=(grant_snapshot.scope_kind or "").strip() or "service",
                    scope_ref=(grant_snapshot.scope_ref or "").strip() or "default",
                    access_scope=(grant_snapshot.access_scope or "").strip()
                    or "service",
                    class_instance_identity_required=(
                        grant_snapshot.class_instance_identity_required
                    ),
                    role_assignment_binding_required=(
                        grant_snapshot.role_assignment_binding_required
                    ),
                    grant_policy_json=JsonObject({}),
                    description=None,
                ),
            )
            contract.actor_role_grants.append(actor_grant)
    return service_config, objects_by_id


def _build_operation_children(
    *,
    objects_by_id: dict[UUID, BaseORMModel],
    operation: ServiceOperationConfig,
    operation_snapshot: ServiceDefinitionOperationSnapshot,
) -> None:
    for view_snapshot in operation_snapshot.api_views:
        view = _remember(
            objects_by_id,
            ServiceOperationConfigApiView(
                id=stable_service_operation_config_api_view_id(
                    service_operation_config_id=operation.id,
                    api_view_id=view_snapshot.api_view_id,
                    service_config_api_id=view_snapshot.service_config_api_id,
                ),
                service_operation_config_id=operation.id,
                service_config_api_id=view_snapshot.service_config_api_id,
                api_view_id=view_snapshot.api_view_id,
                description=None,
            ),
        )
        operation.api_views.append(view)
    for role_snapshot in operation_snapshot.role_requirements:
        role = _remember(
            objects_by_id,
            ServiceOperationConfigRoleRequirement(
                id=stable_service_operation_config_role_requirement_id(
                    service_operation_config_id=operation.id,
                    role_config_id=role_snapshot.role_config_id,
                    access_scope=role_snapshot.access_scope,
                    scope_kind=role_snapshot.scope_kind,
                    scope_ref=role_snapshot.scope_ref,
                ),
                service_operation_config_id=operation.id,
                role_config_id=role_snapshot.role_config_id,
                access_scope=(role_snapshot.access_scope or "").strip() or "operation",
                scope_kind=(role_snapshot.scope_kind or "").strip() or "operation",
                scope_ref=(role_snapshot.scope_ref or "").strip() or "default",
                class_instance_identity_required=(
                    role_snapshot.class_instance_identity_required
                ),
                role_assignment_binding_required=(
                    role_snapshot.role_assignment_binding_required
                ),
                description=None,
            ),
        )
        operation.role_requirements.append(role)
    for endpoint_snapshot in operation_snapshot.endpoints:
        endpoint = _remember(
            objects_by_id,
            ServiceOperationConfigApiEndpoint(
                id=stable_service_operation_config_api_endpoint_id(
                    service_operation_config_id=operation.id,
                    api_capability_endpoint_id=(
                        endpoint_snapshot.api_capability_endpoint_id
                    ),
                    service_config_api_id=endpoint_snapshot.service_config_api_id,
                ),
                service_operation_config_id=operation.id,
                api_capability_endpoint_id=(
                    endpoint_snapshot.api_capability_endpoint_id
                ),
                service_config_api_id=endpoint_snapshot.service_config_api_id,
                description=None,
            ),
        )
        operation.api_endpoints.append(endpoint)
        for function_snapshot in endpoint_snapshot.endpoint_functions:
            endpoint_function = _remember(
                objects_by_id,
                ServiceOperationConfigApiEndpointFunction(
                    id=stable_service_operation_config_api_endpoint_function_id(
                        service_operation_config_api_endpoint_id=endpoint.id,
                        api_capability_endpoint_function_id=(
                            function_snapshot.api_capability_endpoint_function_id
                        ),
                    ),
                    service_operation_config_api_endpoint_id=endpoint.id,
                    api_capability_endpoint_function_id=(
                        function_snapshot.api_capability_endpoint_function_id
                    ),
                    description=None,
                ),
            )
            endpoint.endpoint_functions.append(endpoint_function)


def _build_service_package_manifest_snapshot_objects(
    *,
    name: str,
    service_config_id: UUID,
    service_config_object_instance_graph_commit_id: UUID | None,
    source_code_package_id: UUID | None,
    fqn_prefix: str | None,
    version_number: int,
    title: str | None,
    description: str | None,
    aware_service_version: int,
    manifest_relative_path: str | None,
    package_root: str,
    sources_root: str,
    include_paths: JsonArray,
    exclude_paths: JsonArray,
    force_fresh_scan: bool,
    compilation_mode: str,
    service_surface: str,
    activation_mode: str,
    materialize_on_start: bool,
    dependencies: JsonArray,
    implementation_packages: Sequence[ServicePackageImplementationSnapshot],
    ontology_packages: Sequence[ServicePackageOntologyPackageSnapshot],
    object_config_graph_packages: Sequence[
        ServicePackageObjectConfigGraphPackageSnapshot
    ],
    provided_api_packages: Sequence[ServicePackageApiPackageSnapshot],
    required_api_packages: Sequence[ServicePackageApiPackageSnapshot],
) -> tuple[ServicePackage, dict[UUID, BaseORMModel]]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_name = (name or "").strip()
    if not normalized_name:
        raise RuntimeError("ServicePackage snapshot requires non-empty name")
    service_package = _remember(
        objects_by_id,
        ServicePackage(
            id=stable_service_package_id(name=normalized_name),
            name=normalized_name,
            service_config_id=service_config_id,
            service_config_object_instance_graph_commit_id=(
                service_config_object_instance_graph_commit_id
            ),
            source_code_package_id=source_code_package_id,
            fqn_prefix=(fqn_prefix or "").strip() or None,
            version_number=version_number,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
            aware_service_version=aware_service_version,
            manifest_relative_path=(manifest_relative_path or "").strip() or None,
            package_root=(package_root or "").strip() or ".",
            sources_root=(sources_root or "").strip() or "services",
            include_paths=JsonArray(include_paths or []),
            exclude_paths=JsonArray(exclude_paths or []),
            force_fresh_scan=force_fresh_scan,
            compilation_mode=(compilation_mode or "").strip() or "raw_xor",
            service_surface=(service_surface or "").strip() or "service",
            activation_mode=(activation_mode or "").strip()
            or "materialize_and_load_committed",
            materialize_on_start=materialize_on_start,
            dependencies=JsonArray(dependencies or []),
        ),
    )
    for implementation in implementation_packages:
        bridge = _remember(
            objects_by_id,
            ServicePackageImplementationPackage(
                id=stable_service_package_implementation_package_id(
                    service_package_id=service_package.id,
                    code_package_id=implementation.code_package_id,
                ),
                service_package_id=service_package.id,
                code_package_id=implementation.code_package_id,
                package_name=(implementation.package_name or "").strip(),
                language=implementation.language,
                import_root=(implementation.import_root or "").strip(),
                manifest_relative_path=(
                    implementation.manifest_relative_path or ""
                ).strip(),
                package_root=(implementation.package_root or "").strip() or ".",
                entrypoint=(implementation.entrypoint or "").strip() or None,
                role=(implementation.role or "").strip() or "service_bindings",
                include_paths=JsonArray(implementation.include_paths or []),
                exclude_paths=JsonArray(implementation.exclude_paths or []),
            ),
        )
        service_package.implementation_packages.append(bridge)
    for ontology_package in ontology_packages:
        normalized_package_name = (ontology_package.package_name or "").strip()
        normalized_fqn_prefix = (ontology_package.fqn_prefix or "").strip()
        if not normalized_package_name:
            raise RuntimeError(
                "ServicePackage OntologyPackage snapshot requires package_name"
            )
        if not normalized_fqn_prefix:
            raise RuntimeError(
                "ServicePackage OntologyPackage snapshot requires fqn_prefix"
            )
        role = (ontology_package.role or "").strip() or "replica"
        if role != "replica":
            raise RuntimeError(
                "ServicePackage OntologyPackage snapshot only supports role='replica'"
            )
        requirement_mode = (
            ontology_package.requirement_mode or ""
        ).strip() or "required"
        if requirement_mode != "required":
            raise RuntimeError(
                "ServicePackage OntologyPackage snapshot only supports "
                "requirement_mode='required'"
            )
        expected_hash = ontology_package.expected_hash_sha256
        if expected_hash is not None:
            expected_hash = expected_hash.strip().lower()
            if len(expected_hash) != 64 or any(
                ch not in "0123456789abcdef" for ch in expected_hash
            ):
                raise RuntimeError(
                    "ServicePackage OntologyPackage expected_hash_sha256 must "
                    "be a lowercase 64-character SHA-256 hex digest"
                )
        bridge = _remember(
            objects_by_id,
            ServicePackageOntologyPackage(
                id=stable_service_package_ontology_package_id(
                    service_package_id=service_package.id,
                    ontology_package_id=ontology_package.ontology_package_id,
                ),
                service_package_id=service_package.id,
                ontology_package_id=ontology_package.ontology_package_id,
                ontology_package_object_instance_graph_commit_id=(
                    ontology_package.ontology_package_object_instance_graph_commit_id
                ),
                role=role,
                requirement_mode=requirement_mode,
                package_name=normalized_package_name,
                fqn_prefix=normalized_fqn_prefix,
                expected_hash_sha256=expected_hash,
                description=(ontology_package.description or "").strip() or None,
            ),
        )
        service_package.ontology_packages.append(bridge)
    for ocg_package in object_config_graph_packages:
        manifest_path = (ocg_package.manifest_relative_path or "").strip()
        if not manifest_path:
            raise RuntimeError(
                "ServicePackage ObjectConfigGraphPackage snapshot requires "
                "manifest_relative_path"
            )
        expected_hash = ocg_package.expected_hash_sha256
        if expected_hash is not None:
            expected_hash = expected_hash.strip().lower()
            if len(expected_hash) != 64 or any(
                ch not in "0123456789abcdef" for ch in expected_hash
            ):
                raise RuntimeError(
                    "ServicePackage ObjectConfigGraphPackage "
                    "expected_hash_sha256 must be a lowercase 64-character "
                    "SHA-256 hex digest"
                )
        bridge = _remember(
            objects_by_id,
            ServicePackageObjectConfigGraphPackage(
                id=stable_service_package_object_config_graph_package_id(
                    service_package_id=service_package.id,
                    object_config_graph_package_id=(
                        ocg_package.object_config_graph_package_id
                    ),
                ),
                service_package_id=service_package.id,
                object_config_graph_package_id=(
                    ocg_package.object_config_graph_package_id
                ),
                object_config_graph_package_object_instance_graph_commit_id=(
                    ocg_package.object_config_graph_package_object_instance_graph_commit_id
                ),
                role=(ocg_package.role or "").strip() or "local_state",
                manifest_relative_path=manifest_path,
                package_kind=(ocg_package.package_kind or "").strip() or "state",
                expected_hash_sha256=expected_hash,
                description=(ocg_package.description or "").strip() or None,
            ),
        )
        service_package.object_config_graph_packages.append(bridge)
    for api_package in provided_api_packages:
        if api_package.api_package_object_instance_graph_commit_id is None:
            raise RuntimeError(
                "ServicePackage provided API snapshot requires an exact "
                "ApiPackage commit pin"
            )
        if api_package.service_protocol_package_id is None:
            raise RuntimeError(
                "ServicePackage provided API snapshot requires a selected "
                "ApiPackageLanguagePackage"
            )
        protocol_hash = (
            (api_package.service_protocol_plan_hash_sha256 or "").strip().lower()
        )
        if len(protocol_hash) != 64 or any(
            character not in "0123456789abcdef" for character in protocol_hash
        ):
            raise RuntimeError(
                "ServicePackage provided API snapshot requires a lowercase "
                "64-character service protocol plan digest"
            )
        bridge = _remember(
            objects_by_id,
            ServicePackageProvidedApiPackage(
                id=stable_service_package_provided_api_package_id(
                    service_package_id=service_package.id,
                    api_package_id=api_package.api_package_id,
                ),
                service_package_id=service_package.id,
                api_package_id=api_package.api_package_id,
                api_package_object_instance_graph_commit_id=(
                    api_package.api_package_object_instance_graph_commit_id
                ),
                service_protocol_package_id=(api_package.service_protocol_package_id),
                service_protocol_plan_hash_sha256=protocol_hash,
                description=api_package.description,
            ),
        )
        service_package.provided_api_packages.append(bridge)
    for api_package in required_api_packages:
        bridge = _remember(
            objects_by_id,
            ServicePackageRequiredApiPackage(
                id=stable_service_package_required_api_package_id(
                    service_package_id=service_package.id,
                    api_package_id=api_package.api_package_id,
                ),
                service_package_id=service_package.id,
                api_package_id=api_package.api_package_id,
                description=api_package.description,
            ),
        )
        service_package.required_api_packages.append(bridge)
    return service_package, objects_by_id


def _build_service_api_provider_set_snapshot_objects(
    *,
    key: str,
    title: str | None,
    description: str | None,
    version_number: int,
    service_package_id: UUID,
    membership_key: str | None,
    membership_description: str | None,
) -> tuple[
    ServiceApiProviderSet,
    ServiceApiProviderSetServicePackage,
    dict[UUID, BaseORMModel],
]:
    objects_by_id: dict[UUID, BaseORMModel] = {}
    normalized_key = (key or "").strip()
    if not normalized_key:
        raise RuntimeError("ServiceApiProviderSet snapshot requires non-empty key")
    provider_set = _remember(
        objects_by_id,
        ServiceApiProviderSet(
            id=stable_service_api_provider_set_id(key=normalized_key),
            key=normalized_key,
            title=(title or "").strip() or None,
            description=(description or "").strip() or None,
            version_number=version_number,
        ),
    )
    membership = _remember(
        objects_by_id,
        ServiceApiProviderSetServicePackage(
            id=stable_service_api_provider_set_service_package_id(
                service_api_provider_set_id=provider_set.id,
                service_package_id=service_package_id,
            ),
            service_api_provider_set_id=provider_set.id,
            service_package_id=service_package_id,
            membership_key=(membership_key or "").strip() or None,
            description=(membership_description or "").strip() or None,
        ),
    )
    provider_set.service_packages.append(membership)
    return provider_set, membership, objects_by_id


@dataclass(frozen=True, slots=True)
class _SnapshotCommit:
    commit_id: UUID
    head_commit_id: UUID
    object_instance_graph_commit_id: UUID
    object_count: int
    change_count: int


async def _commit_snapshot(
    *,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    root_object: BaseORMModel,
    objects_by_id: Mapping[UUID, BaseORMModel],
    operation_label: str,
    commit_id_namespace: UUID,
    commit_action_object_id: UUID | None = None,
) -> _SnapshotCommit:
    trace_fields = {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "operation_label": operation_label,
        "root_object_id": str(root_object_id),
        "object_count": len(objects_by_id),
    }
    with service_api_trace_phase(
        "service_snapshot.commit.resolve_projection_identity",
        **trace_fields,
    ):
        opg = index.opg_by_hash.get(projection_hash)
        if opg is None:
            raise RuntimeError(
                "Service snapshot commit missing projection hash: " f"{projection_hash}"
            )
        domain_oig_id = stable_object_instance_graph_id(
            object_projection_graph_id=opg.id,
            key=str(branch_id),
        )
        _ocgi, opgi = resolve_meta_graph_ocgi_opgi(
            index=index,
            projection_hash=projection_hash,
        )
        if opgi is None:
            raise RuntimeError(
                "Service snapshot commit missing ObjectProjectionGraphIdentity: "
                f"projection_hash={projection_hash}"
            )
        oigi_id = stable_object_instance_graph_identity_id(
            object_projection_graph_identity_id=opgi.id,
            object_instance_graph_id=domain_oig_id,
        )
    before_oig, parent_commit_id = await await_with_service_api_trace(
        _load_before_oig(
            index=index,
            branch_id=branch_id,
            projection_hash=projection_hash,
            domain_oig_id=domain_oig_id,
            root_object_id=root_object_id,
        ),
        phase="service_snapshot.commit.load_before_oig",
        fields=trace_fields,
    )
    with service_api_trace_phase(
        "service_snapshot.commit.build_change_set",
        **trace_fields,
    ):
        object_ids = frozenset(objects_by_id)
        change_set = ORMChangeSet(
            collected_at=datetime.now(UTC),
            created_ids=object_ids,
            touched_ids=object_ids,
            deleted_ids=frozenset(),
            objects_by_id=dict(objects_by_id),
            scalar_fields_by_id={},
            list_fields_by_id={},
            scalar_baseline={},
            list_baseline={},
            list_added={},
            list_removed={},
        )
    with service_api_trace_phase(
        "service_snapshot.commit.build_changes",
        **trace_fields,
    ):
        changes = build_object_instance_graph_changes_from_orm_change_set(
            before_oig=before_oig,
            object_instance_graph_identity_id=oigi_id,
            ocg=index.ocg,
            opg=opg,
            change_set=change_set,
            class_configs_by_id=index.class_configs_by_id,
            relationships_by_id=index.relationships_by_id,
            enum_option_resolver=default_meta_enum_option_resolver,
            class_instance_resolver=None,
            union_selections=None,
        )
    if not changes:
        head = await await_with_service_api_trace(
            FSCommitStore().head(
                branch_id=branch_id,
                projection_hash=projection_hash,
            ),
            phase="service_snapshot.commit.no_changes_head_lookup",
            fields=trace_fields,
        )
        raw_head_commit_id = None if head is None else head.get("commit_id")
        if raw_head_commit_id is None:
            raise RuntimeError(
                "Service snapshot commit produced no OIG changes and no "
                f"existing lane head: operation_label={operation_label!r}"
            )
        head_commit_id = (
            raw_head_commit_id
            if isinstance(raw_head_commit_id, UUID)
            else UUID(str(raw_head_commit_id))
        )
        with service_api_trace_phase(
            "service_snapshot.commit.build_no_change_result",
            **trace_fields,
        ):
            return _SnapshotCommit(
                commit_id=head_commit_id,
                head_commit_id=head_commit_id,
                object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
                    object_instance_graph_identity_id=oigi_id,
                    commit_id=head_commit_id,
                ),
                object_count=len(objects_by_id),
                change_count=0,
            )
    with service_api_trace_phase(
        "service_snapshot.commit.materialize_post_oig",
        **trace_fields,
    ):
        after_oig = materialize_meta_oig_post(
            before_oig=before_oig,
            changes=changes,
            attribute_configs_by_id=index.attribute_configs_by_id,
            class_configs_by_id=index.class_configs_by_id,
        )
    with service_api_trace_phase(
        "service_snapshot.commit.build_commit_id",
        **trace_fields,
    ):
        commit_id = _snapshot_commit_id(
            namespace=commit_id_namespace,
            branch_id=branch_id,
            projection_hash=projection_hash,
            root_object_id=root_object_id,
            parent_commit_id=parent_commit_id,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
        )
        commit_action = CommitActionDescriptor(
            operation_label=operation_label,
            call_target="generated_materialization",
            object_id=commit_action_object_id or root_object.id,
        )
    commit = await await_with_service_api_trace(
        FSLaneCommitter().commit(
            branch_id=branch_id,
            projection_hash=projection_hash,
            object_instance_graph_identity_id=oigi_id,
            object_instance_graph_id=domain_oig_id,
            before_oig=before_oig,
            root_object_id=root_object_id,
            changes=changes,
            graph_hash_pre=before_oig.hash,
            graph_hash_post=after_oig.hash,
            author_id=resolve_meta_author_id(actor_id),
            commit_id=commit_id,
            commit_action=commit_action,
        ),
        phase="service_snapshot.commit.append_lane_commit",
        fields=trace_fields,
    )
    if commit is None or commit.commit is None:
        raise RuntimeError(
            "Service snapshot commit did not append a lane commit: "
            f"operation_label={operation_label!r} root_object_id={root_object_id}"
        )
    with service_api_trace_phase(
        "service_snapshot.commit.build_result",
        **trace_fields,
    ):
        return _SnapshotCommit(
            commit_id=commit.commit.id,
            head_commit_id=commit.commit.id,
            object_instance_graph_commit_id=stable_object_instance_graph_commit_id(
                object_instance_graph_identity_id=(
                    commit.object_instance_graph_identity_id
                ),
                commit_id=commit.commit.id,
            ),
            object_count=len(objects_by_id),
            change_count=len(changes),
        )


async def _load_before_oig(
    *,
    index: MetaGraphRuntimeIndex,
    branch_id: UUID,
    projection_hash: str,
    domain_oig_id: UUID,
    root_object_id: UUID,
):
    trace_fields = {
        "branch_id": str(branch_id),
        "projection_hash": projection_hash,
        "domain_oig_id": str(domain_oig_id),
        "root_object_id": str(root_object_id),
    }
    with service_api_trace_phase(
        "service_snapshot.load_before_oig.resolve_projection",
        **trace_fields,
    ):
        opg = index.opg_by_hash[projection_hash]
    head = await await_with_service_api_trace(
        FSCommitStore().head(
            branch_id=branch_id,
            projection_hash=projection_hash,
        ),
        phase="service_snapshot.load_before_oig.head_lookup",
        fields=trace_fields,
    )
    if head is not None and head.get("commit_id") is not None:
        oig, _ = await await_with_service_api_trace(
            OIGMaterializer().get(
                branch_id=branch_id,
                ocg=index.ocg,
                opg=opg,
                commit_id=None,
                attribute_configs_by_id=index.attribute_configs_by_id,
                class_configs_by_id=index.class_configs_by_id,
            ),
            phase="service_snapshot.load_before_oig.materializer_get",
            fields=trace_fields,
        )
        return oig, UUID(str(head["commit_id"]))
    with service_api_trace_phase(
        "service_snapshot.load_before_oig.build_rooted_base",
        **trace_fields,
    ):
        return build_rooted_object_instance_graph_base(
            key=str(branch_id),
            name=f"OIG_{branch_id.hex[:8]}",
            description="ROOTED_BASE",
            object_config_graph=index.ocg,
            object_projection_graph=opg,
            root_source_object_id=root_object_id,
            oig_id=domain_oig_id,
        ), None


def _snapshot_commit_id(
    *,
    namespace: UUID,
    branch_id: UUID,
    projection_hash: str,
    root_object_id: UUID,
    parent_commit_id: UUID | None,
    graph_hash_pre: str,
    graph_hash_post: str,
) -> UUID:
    return uuid5(
        namespace,
        f"{branch_id}:{projection_hash}:{root_object_id}:"
        f"{parent_commit_id or ''}:{graph_hash_pre}:{graph_hash_post}",
    )


def _remember(
    objects_by_id: dict[UUID, BaseORMModel],
    obj: _TModel,
) -> _TModel:
    obj_id = obj.id
    previous = objects_by_id.get(obj_id)
    if previous is not None and previous is not obj:
        raise RuntimeError(f"Service snapshot duplicate object id: {obj_id}")
    objects_by_id[obj_id] = obj
    return obj


def _local_service_access_uuid(*parts: str) -> UUID:
    return uuid5(
        _LOCAL_SERVICE_CONTRACT_ACCESS_ID_NAMESPACE,
        ":".join(part.strip() for part in parts),
    )


__all__ = [
    "ServiceApiProviderSetSnapshotCommitResult",
    "ServiceConfigDefinitionSnapshotCommitResult",
    "ServiceContractAccessSnapshotCommitResult",
    "ServiceDefinitionActorRoleGrantSnapshot",
    "ServiceDefinitionApiSnapshot",
    "ServiceDefinitionCodePackageConfigSnapshot",
    "ServiceDefinitionContractSnapshot",
    "ServiceDefinitionEndpointFunctionSnapshot",
    "ServiceDefinitionEndpointSnapshot",
    "ServiceDefinitionExperienceSnapshot",
    "ServiceDefinitionOperationGrantSnapshot",
    "ServiceDefinitionOperationSnapshot",
    "ServiceDefinitionRoleRequirementSnapshot",
    "ServiceDefinitionApiViewSnapshot",
    "ServiceInstanceSnapshotCommitResult",
    "ServiceOperationSnapshotCommitResult",
    "ServicePackageApiPackageSnapshot",
    "ServicePackageImplementationSnapshot",
    "ServicePackageManifestSnapshotCommitResult",
    "ServicePackageOntologyPackageSnapshot",
    "ServicePackageObjectConfigGraphPackageSnapshot",
    "RoleConfigReferenceSnapshotCommitResult",
    "commit_service_api_provider_set_snapshot",
    "commit_role_config_reference_snapshot",
    "commit_service_contract_access_snapshot",
    "commit_service_config_definition_snapshot",
    "commit_service_instance_snapshot",
    "commit_service_operation_snapshot",
    "commit_service_package_manifest_snapshot",
]
