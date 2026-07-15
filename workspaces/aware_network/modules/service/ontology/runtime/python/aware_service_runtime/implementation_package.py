from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
from typing import Protocol, cast
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from pydantic import BaseModel
from aware_code.types import JsonObject
from aware_api.invocation import (
    ApiInvocationEndpointBinding,
    LoadedApiInvocationManifest,
    load_api_invocation_manifest_file,
)
from aware_api_ontology.stable_ids import (
    stable_api_call_id,
    stable_api_capability_endpoint_id,
    stable_api_capability_id,
    stable_api_id,
)
from aware_api_runtime.invocation import (
    ApiInvocationIR,
    ResolvedApiInvocationFulfillmentBinding,
    ResolvedApiInvocationStream,
    ResolvedApiInvocationStreamEvent,
    dispatch_api_invocation,
)
from aware_api_runtime.invocation.materialization.telemetry import (
    collect_api_invocation_trace_timings,
)
from aware_api_runtime.invocation.materialization.context import (
    should_use_compact_api_receipt_payload,
)
from aware_api_runtime.ir import decode_api_compile_plan_payload
from aware_api_ontology.api.api_graph_projection import ApiGraphProjection
from aware_service_runtime.manifest.spec import (
    AwareServiceImplementationLanguage,
    AwareServiceImplementationRole,
    AwareServiceTomlImplementationPackageSpec,
)
from aware_service_runtime.runtime_secrets import configure_service_runtime_secrets
from aware_service_runtime.runtime_resolution import (
    load_committed_service_activation_dependency_payloads,
    resolve_service_protocol_runtime_manifest,
)
from aware_service_runtime.workspace_dependency_roots import (
    api_service_protocol_dependency_roots,
)
from aware_api_runtime.service_protocol import (
    ApiServiceDispatchFulfillmentBinding,
    ApiServiceDispatchPlan,
    ApiServiceProtocolExecutionFactory,
    ApiServiceProtocolEndpointBinding,
    LoadedApiServiceProtocolPackage,
    build_api_service_dispatch_plan_from_invocation_ir,
    build_api_service_dispatch_plan_from_materialized_call,
    load_api_service_protocol_package,
    resolve_api_service_dispatch_instance_target_plans,
    resolve_api_service_protocol_package_roots,
)
from aware_api_runtime.service_protocol.runtime import (
    ApiServiceProtocolInvoker,
    ApiServiceProtocolStreamInvoker,
)
from aware_api_runtime.invocation import ResolvedApiInvocationEnvelope
from aware_api_runtime.request_hash import compute_api_request_hash_from_mapping
from aware_meta.materialization.contracts import MaterializationLaneContext
from aware_meta.graph.config.stable_ids import stable_object_instance_graph_branch_id
from aware_meta.graph.instance.projection_readiness import (
    ProjectionReadinessModes,
    ProjectionReadinessRequirement,
    ensure_projection_readiness,
)
from aware_meta.runtime.graph_context import find_meta_graph_projection_hash_by_name
from aware_meta.runtime.handler_executor import MetaGraphRuntimeIndex
from aware_meta.runtime.oig_model_reifier import reify_oig_session
from aware_meta_ontology.stable_ids import stable_inline_value_instance_id
from aware_orm.session.session import Session
from aware_service_ontology.stable_ids import (
    stable_service_branch_id,
    stable_service_config_api_id,
    stable_service_config_api_projection_id,
    stable_service_config_id,
    stable_service_id,
    stable_service_operation_config_api_endpoint_id,
    stable_service_operation_config_id,
)
from aware_service_ontology.service.service_enums import (
    ServiceOperationAdmissionMode,
    ServiceOperationFulfillmentKind,
    ServiceOperationReceiptPolicy,
    ServiceOperationSettlementPolicy,
)
from aware_utils.logging import logger
from aware_utils.string_transform import to_snake_case

from aware_service_runtime.api_ingress.execution import (
    ExecutedServiceApiDispatch,
    ServiceApiActorRoleEvidence,
    ServiceApiDispatchReceiptPolicy,
    ServiceApiOperationAccessContext,
    ServiceApiStreamEventSink,
    execute_service_api_dispatch_plan,
)
from aware_service_runtime.api_ingress.telemetry import (
    await_with_service_api_trace,
    record_service_api_trace_timing,
    service_api_trace_phase,
)
from aware_service_runtime.api_ingress.economy_settlement import (
    ServiceOperationEconomySettlementAdapter,
)
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackend,
    ServiceApiExecutionBackendMode,
)
from aware_service_runtime.api_ingress.host_context import (
    ServiceEnvironmentCommitReceiptSource,
)
from aware_service_runtime.api_ingress.ontology_replica_context import (
    ServiceOntologyReplicaQueryProtocol,
)
from aware_service_runtime.api_ingress.ontology_replica_orm_context import (
    ServiceOntologyReplicaOrmSessionProtocol,
)
from aware_service_runtime.compile import (
    ServiceCompileResult,
    compile_committed_service_package_workspace,
    compile_service_workspace,
)
from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
)
from aware_service_runtime.materialization.service import (
    _CommittedAPIReferenceContext,
    _hydrate_committed_api_reference_contexts,
    _resolve_committed_api_graph_projection_id,
    materialize_service_definition_ontology,
    service_activation_lane,
    stable_service_role_reference_branch_id,
)
from aware_service_runtime.materialization.snapshot_commit import (
    commit_service_instance_snapshot,
)
from aware_service_runtime.ontology.materialization import (
    materialize_service_branch,
)
from aware_service_runtime.contracts import (
    MetaTemporalGraphRoute,
    ServiceApiDispatchEnvelope,
    ServiceApiDispatchFulfillmentBinding,
    ServiceApiDispatchRequest,
    ServiceGraphGateway,
    ServiceLaneSubscriptionBinding,
    ServiceOperationContext,
    ServiceOperationRequest,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
)


class _RuntimeProtocol(Protocol):
    @property
    def manifest_path(self) -> Path: ...

    @property
    def invoker(self) -> object: ...


class ProjectionSessionResolver(Protocol):
    def __call__(self, lane: MaterializationLaneContext) -> Session | None: ...


class _BindingModuleProtocol(Protocol):
    def build_service_bindings(self) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class ServicePackageDependencyBinding:
    package_name: str
    runtime_package_dir: Path
    service_protocol_plan_path: Path
    service_protocol_plan_hash_sha256: str
    endpoint_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PreparedServicePackageBinding:
    compile_result: ServiceCompileResult
    compile_plan_artifact_hash_sha256: str
    dependencies: tuple[ServicePackageDependencyBinding, ...]
    service_bindings: Mapping[str, object]
    service_endpoint_refs: Mapping[str, tuple[str, ...]]
    service_stream_endpoint_refs: Mapping[str, tuple[str, ...]]
    endpoint_dependencies: Mapping[str, ServicePackageDependencyBinding]


@dataclass(frozen=True, slots=True)
class _ReadModelDispatchTemplateCacheKey:
    prepared_identity: int
    runtime_index_identity: int
    runtime_package_dir: str
    service_protocol_plan_hash_sha256: str
    service_name: str
    endpoint_ref: str
    discriminant: str


@dataclass(frozen=True, slots=True)
class _ReadModelDispatchTemplate:
    ir_template: ApiInvocationIR
    loaded_package: LoadedApiServiceProtocolPackage
    endpoint_binding: ApiServiceProtocolEndpointBinding
    request_model_cls: type[BaseModel]


_READ_MODEL_DISPATCH_TEMPLATE_CACHE: dict[
    _ReadModelDispatchTemplateCacheKey,
    _ReadModelDispatchTemplate,
] = {}


@dataclass(frozen=True, slots=True)
class _DeferredDispatchTemplateCacheKey:
    prepared_identity: int
    runtime_index_identity: int
    runtime_package_dir: str
    service_protocol_plan_hash_sha256: str
    service_name: str
    endpoint_ref: str
    discriminant: str


@dataclass(frozen=True, slots=True)
class _DeferredDispatchTemplate:
    api_capability_endpoint_id: UUID
    api_name: str
    capability_name: str
    endpoint_name: str
    endpoint_ref: str
    discriminant: str
    source_path: str
    request_class_config_id: UUID
    request_class_ref: str
    request_source_path: str
    request_type_ref: str
    response_class_ref: str | None
    response_source_path: str | None
    response_type_ref: str | None
    stream_event_type_refs: tuple[str, ...]
    execution_protocol_ref: str | None
    description: str | None
    public_package_import_root: str
    service_protocol_import_root: str
    build_execution: ApiServiceProtocolExecutionFactory | None
    stream_invoke: ApiServiceProtocolStreamInvoker | None
    request_model_cls: type[BaseModel]
    invoke: ApiServiceProtocolInvoker


_DEFERRED_DISPATCH_TEMPLATE_CACHE: dict[
    _DeferredDispatchTemplateCacheKey,
    _DeferredDispatchTemplate,
] = {}


@dataclass(frozen=True, slots=True)
class ActivatedServicePackageBinding:
    prepared: PreparedServicePackageBinding
    service_ids_by_name: Mapping[str, UUID]
    service_subscriptions_by_name: Mapping[
        str, tuple[ServiceLaneSubscriptionBinding, ...]
    ]
    api_reference_branch_ids_by_api_name: Mapping[str, UUID]
    experience_reference_branch_ids_by_experience_name: Mapping[str, UUID] = field(
        default_factory=dict
    )
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] = field(
        default_factory=dict
    )
    service_config_lanes_by_name: Mapping[str, MaterializationLaneContext] = field(
        default_factory=dict
    )
    service_lanes_by_name: Mapping[str, MaterializationLaneContext] = field(
        default_factory=dict
    )


def _service_package_name_for_activated_binding(
    activated: ActivatedServicePackageBinding,
) -> str | None:
    package_name = (
        activated.prepared.compile_result.snapshot.spec.service.package_name or ""
    ).strip()
    return package_name or None


class ServiceActivationRequiresMaterialization(RuntimeError):
    """Raised when activation cannot reuse committed Service/API lane receipts."""


def prepare_service_package_binding(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None = None,
    dependency_payloads: Sequence[Mapping[str, object]] | None = None,
) -> PreparedServicePackageBinding:
    compile_result = compile_service_workspace(
        toml_path=toml_path,
        repo_root=repo_root,
        emit_compile_plan=True,
    )
    return _prepare_service_package_binding_from_compile_result(
        compile_result=compile_result,
        dependency_payloads=dependency_payloads,
    )


def prepare_committed_service_package_binding(
    *,
    package_ref: ResolvedServiceRuntimePackageRef,
) -> PreparedServicePackageBinding:
    service_package = package_ref.service_package
    if service_package is None:
        raise RuntimeError(
            "Committed Service package activation requires a hydrated ServicePackage "
            f"root: package_name={package_ref.package_name!r}"
        )
    compile_result = compile_committed_service_package_workspace(
        service_package=service_package,
        materialized_workspace_root=package_ref.materialized_workspace_root,
        emit_compile_plan=True,
    )
    return _prepare_service_package_binding_from_compile_result(
        compile_result=compile_result,
        dependency_payloads=package_ref.dependency_payloads,
        dependency_workspace_roots=package_ref.dependency_workspace_roots,
    )


def _prepare_service_package_binding_from_compile_result(
    *,
    compile_result: ServiceCompileResult,
    dependency_payloads: Sequence[Mapping[str, object]] | None = None,
    dependency_workspace_roots: Sequence[str | Path] = (),
) -> PreparedServicePackageBinding:
    compile_plan = compile_result.compile_plan
    compile_plan_artifact = compile_result.compile_plan_artifact
    activation_plan = compile_result.activation_plan
    if compile_plan is None or compile_plan_artifact is None or activation_plan is None:
        raise RuntimeError(
            "Service package binding requires service_ontology compilation mode "
            "with compile-plan emission enabled."
        )

    compile_plan_artifact_hash_sha256 = _hash_json_artifact(compile_plan_artifact.path)
    if (
        compile_plan_artifact_hash_sha256
        != activation_plan.compile_plan_artifact_hash_sha256
    ):
        raise RuntimeError(
            "Service activation plan compile-plan hash does not match emitted artifact: "
            f"expected={activation_plan.compile_plan_artifact_hash_sha256} "
            f"actual={compile_plan_artifact_hash_sha256}"
        )

    dependencies = _resolve_api_service_protocol_dependencies(
        repo_root=compile_result.snapshot.repo_root,
        compile_result=compile_result,
        dependency_payloads=dependency_payloads,
        dependency_workspace_roots=dependency_workspace_roots,
    )
    if not dependencies:
        raise RuntimeError(
            "Service implementation package binding requires at least one "
            "committed api_service_protocol dependency lock."
        )

    protocol_runtime = resolve_service_protocol_runtime_manifest(
        toml_paths=(compile_result.snapshot.spec_path,),
        dependency_payloads=(
            tuple(dependency_payloads) if dependency_payloads is not None else None
        ),
        repo_root=compile_result.snapshot.repo_root,
        kernel_repo_root=(
            dependency_workspace_roots[0]
            if dependency_workspace_roots
            else compile_result.snapshot.repo_root
        ),
        use_cache=False,
    )
    if protocol_runtime is None:
        raise RuntimeError(
            "Service implementation package binding requires resolved API runtime "
            "dependency roots."
        )
    package_roots = _dependency_import_roots(
        dependencies=dependencies,
        runtime_python_roots=protocol_runtime.runtime_resolution.python_roots,
    )
    implementation_package = _resolve_service_binding_implementation_package(
        compile_result=compile_result,
    )
    configure_service_runtime_secrets(compile_result.snapshot.spec.runtime)
    service_bindings = _load_service_bindings(
        package_root=(
            compile_result.snapshot.package_root / implementation_package.package_root
        ).resolve(),
        import_root=implementation_package.import_root,
        entrypoint=implementation_package.entrypoint,
        dependency_import_roots=package_roots,
    )
    service_endpoint_refs = _build_service_endpoint_ref_map(
        compile_result=compile_result
    )
    _validate_service_bindings(
        service_bindings=service_bindings,
        expected_service_names=tuple(sorted(service_endpoint_refs)),
    )
    endpoint_dependencies = _build_endpoint_dependency_map(dependencies=dependencies)
    _validate_bound_service_endpoint_refs(
        service_endpoint_refs=service_endpoint_refs,
        endpoint_dependencies=endpoint_dependencies,
    )
    service_stream_endpoint_refs = _build_service_stream_endpoint_ref_map(
        service_endpoint_refs=service_endpoint_refs,
        endpoint_dependencies=endpoint_dependencies,
    )

    return PreparedServicePackageBinding(
        compile_result=compile_result,
        compile_plan_artifact_hash_sha256=compile_plan_artifact_hash_sha256,
        dependencies=dependencies,
        service_bindings=service_bindings,
        service_endpoint_refs=service_endpoint_refs,
        service_stream_endpoint_refs=service_stream_endpoint_refs,
        endpoint_dependencies=endpoint_dependencies,
    )


async def activate_service_package_binding(
    *,
    toml_path: str | Path,
    repo_root: str | Path | None,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    dependency_payloads: Sequence[Mapping[str, object]] | None = None,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None = None,
    experience_reference_commit_store_root: Path | None = None,
    allow_materialization: bool = True,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    activation_commit_store_root: Path | None = None,
) -> ActivatedServicePackageBinding:
    prepared = prepare_service_package_binding(
        toml_path=toml_path,
        repo_root=repo_root,
        dependency_payloads=dependency_payloads,
    )
    return await _activate_prepared_service_package_binding(
        prepared=prepared,
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
        experience_reference_commit_store_root=experience_reference_commit_store_root,
        allow_materialization=allow_materialization,
        projection_session_resolver=projection_session_resolver,
        activation_commit_store_root=activation_commit_store_root,
    )


async def activate_committed_service_package_binding(
    *,
    package_ref: ResolvedServiceRuntimePackageRef,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None = None,
    experience_reference_commit_store_root: Path | None = None,
    allow_materialization: bool = True,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    activation_commit_store_root: Path | None = None,
) -> ActivatedServicePackageBinding:
    prepared = prepare_committed_service_package_binding(package_ref=package_ref)
    return await _activate_prepared_service_package_binding(
        prepared=prepared,
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        experience_reference_branch_ids_by_experience_name=(
            experience_reference_branch_ids_by_experience_name
        ),
        role_reference_branch_ids_by_role_name=role_reference_branch_ids_by_role_name,
        experience_reference_commit_store_root=experience_reference_commit_store_root,
        allow_materialization=allow_materialization,
        projection_session_resolver=projection_session_resolver,
        activation_commit_store_root=activation_commit_store_root,
    )


async def _activate_prepared_service_package_binding(
    *,
    prepared: PreparedServicePackageBinding,
    runtime: _RuntimeProtocol,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None = None,
    experience_reference_branch_ids_by_experience_name: (
        Mapping[str, UUID] | None
    ) = None,
    role_reference_branch_ids_by_role_name: Mapping[str, UUID] | None = None,
    experience_reference_commit_store_root: Path | None = None,
    allow_materialization: bool = True,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    activation_commit_store_root: Path | None = None,
) -> ActivatedServicePackageBinding:
    activation_plan = prepared.compile_result.activation_plan
    compile_plan = prepared.compile_result.compile_plan
    compile_plan_artifact = prepared.compile_result.compile_plan_artifact
    if activation_plan is None or compile_plan is None or compile_plan_artifact is None:
        raise RuntimeError(
            "Prepared Service package binding is missing compile artifacts."
        )

    service_names = tuple(sorted(prepared.service_bindings))
    service_config_lanes_by_name = {
        name: _service_activation_lane_for_name(
            lane=service_config_lane,
            lane_kind="service-config",
            service_name=name,
        )
        for name in service_names
    }
    service_lanes_by_name = {
        name: _service_activation_lane_for_name(
            lane=service_lane,
            lane_kind="service",
            service_name=name,
        )
        for name in service_names
    }
    if activation_plan.materialize_on_start:
        compile_plan_payload = _load_json_mapping(compile_plan_artifact.path)
        service_ids_by_name: dict[str, UUID] = {}
        for service_name in service_names:
            service_specific_service_config_lane = service_config_lanes_by_name[
                service_name
            ]
            service_specific_service_lane = service_lanes_by_name[service_name]
            service_specific_compile_plan_payload = _compile_plan_payload_for_service(
                compile_plan_payload,
                service_name=service_name,
            )
            committed_service_ids = await _load_committed_service_ids_if_available(
                index=index,
                lane=service_specific_service_lane,
                service_names=(service_name,),
                projection_session_resolver=projection_session_resolver,
                commit_store_root=activation_commit_store_root,
            )
            committed_service_config_head_commit_id = (
                await _load_committed_service_config_head_if_available(
                    index=index,
                    lane=service_specific_service_config_lane,
                    service_name=service_name,
                    projection_session_resolver=projection_session_resolver,
                    commit_store_root=activation_commit_store_root,
                )
            )
            if (
                committed_service_ids is not None
                and committed_service_config_head_commit_id is not None
            ):
                service_ids_by_name.update(committed_service_ids)
                continue
            if not allow_materialization:
                raise ServiceActivationRequiresMaterialization(
                    "Service activation requires ServiceConfig/Service lane "
                    "materialization before it can use read-only committed "
                    f"package-ref activation: service={service_name!r} "
                    "service_config_head_available="
                    f"{committed_service_config_head_commit_id is not None} "
                    f"service_head_available={committed_service_ids is not None}."
                )
            _ = await materialize_service_definition_ontology(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                lane=service_specific_service_config_lane,
                compile_plan_payloads=[
                    service_specific_compile_plan_payload,
                ],
                api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
                experience_reference_branch_ids_by_experience_name=(
                    _experience_reference_branch_ids_for_activation(
                        provided=experience_reference_branch_ids_by_experience_name,
                        payload=service_specific_compile_plan_payload,
                        fallback_branch_id=service_config_lane.branch_id,
                    )
                ),
                experience_reference_commit_store_root=(
                    experience_reference_commit_store_root
                ),
                role_reference_branch_ids_by_role_name=(
                    _role_reference_branch_ids_for_activation(
                        provided=role_reference_branch_ids_by_role_name,
                        payload=service_specific_compile_plan_payload,
                    )
                ),
            )
            materialized_service_ids = await _materialize_service_instances(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                service_lane=service_specific_service_lane,
                service_names=(service_name,),
            )
            service_config_catchup = (
                await _ensure_service_activation_lane_projection_caught_up(
                    index=index,
                    lane=service_specific_service_config_lane,
                    projection_session_resolver=projection_session_resolver,
                    commit_store_root=activation_commit_store_root,
                )
            )
            service_catchup = (
                await _ensure_service_activation_lane_projection_caught_up(
                    index=index,
                    lane=service_specific_service_lane,
                    projection_session_resolver=projection_session_resolver,
                    commit_store_root=activation_commit_store_root,
                )
            )
            if service_config_catchup is None or service_catchup is None:
                raise RuntimeError(
                    "Service activation materialization did not commit both required "
                    "ServiceConfig/Service lane heads: "
                    f"service={service_name!r} "
                    f"service_config_head_available={service_config_catchup is not None} "
                    f"service_head_available={service_catchup is not None}."
                )
            logger.info(
                "Service activation projected materialized Service lanes "
                "service_name=%s service_config_projection_catchup_commits=%s "
                "service_config_projection_catchup_skipped=%s "
                "service_projection_catchup_commits=%s "
                "service_projection_catchup_skipped=%s",
                service_name,
                (
                    service_config_catchup.commits_applied
                    if service_config_catchup is not None
                    else 0
                ),
                (
                    service_config_catchup.skipped_reason
                    if service_config_catchup is not None
                    else "missing_head"
                ),
                service_catchup.commits_applied if service_catchup is not None else 0,
                (
                    service_catchup.skipped_reason
                    if service_catchup is not None
                    else "missing_head"
                ),
            )
            service_ids_by_name.update(materialized_service_ids)
    else:
        service_ids_by_name = {}
        for service_name in service_names:
            committed_service_config_head_commit_id = (
                await _load_committed_service_config_head_if_available(
                    index=index,
                    lane=service_config_lanes_by_name[service_name],
                    service_name=service_name,
                    projection_session_resolver=projection_session_resolver,
                    commit_store_root=activation_commit_store_root,
                )
            )
            committed_service_ids = await _load_committed_service_ids_if_available(
                index=index,
                lane=service_lanes_by_name[service_name],
                service_names=(service_name,),
                projection_session_resolver=projection_session_resolver,
                commit_store_root=activation_commit_store_root,
            )
            if (
                committed_service_config_head_commit_id is None
                or committed_service_ids is None
            ):
                raise ServiceActivationRequiresMaterialization(
                    "Service activation requires committed ServiceConfig/Service "
                    "lane heads when materialize_on_start is false: "
                    f"service={service_name!r} "
                    "service_config_head_available="
                    f"{committed_service_config_head_commit_id is not None} "
                    f"service_head_available={committed_service_ids is not None}."
                )
            service_ids_by_name.update(committed_service_ids)

    service_subscriptions_by_name = await _materialize_service_subscriptions(
        prepared=prepared,
        runtime=runtime,
        index=index,
        actor_id=actor_id,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        service_ids_by_name=service_ids_by_name,
        service_config_lanes_by_name=service_config_lanes_by_name,
        service_lanes_by_name=service_lanes_by_name,
        api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        allow_materialization=allow_materialization,
        commit_store_root=activation_commit_store_root,
    )

    return ActivatedServicePackageBinding(
        prepared=prepared,
        service_ids_by_name=service_ids_by_name,
        service_subscriptions_by_name=service_subscriptions_by_name,
        api_reference_branch_ids_by_api_name=_normalize_api_reference_branch_ids_by_api_name(
            api_reference_branch_ids_by_api_name
        ),
        experience_reference_branch_ids_by_experience_name=(
            _normalize_experience_reference_branch_ids_by_experience_name(
                experience_reference_branch_ids_by_experience_name
            )
        ),
        role_reference_branch_ids_by_role_name=(
            _normalize_role_reference_branch_ids_by_role_name(
                role_reference_branch_ids_by_role_name
            )
        ),
        service_config_lanes_by_name=service_config_lanes_by_name,
        service_lanes_by_name=service_lanes_by_name,
    )


def _service_activation_lane_for_name(
    *,
    lane: MaterializationLaneContext,
    lane_kind: str,
    service_name: str,
) -> MaterializationLaneContext:
    return service_activation_lane(
        projection_hash=lane.projection_hash,
        lane_kind=lane_kind,
        service_name=service_name,
    )


def _compile_plan_payload_for_service(
    payload: Mapping[str, object],
    *,
    service_name: str,
) -> dict[str, object]:
    normalized_name = service_name.strip().casefold()
    if not normalized_name:
        raise RuntimeError("Service activation requires non-empty service_name.")
    raw_service_configs = payload.get("service_configs", ())
    if not isinstance(raw_service_configs, list):
        raise RuntimeError(
            "Service compile plan payload must contain a service_configs list."
        )
    service_configs = [
        item
        for item in raw_service_configs
        if isinstance(item, Mapping)
        and str(item.get("name") or "").strip().casefold() == normalized_name
    ]
    if not service_configs:
        raise RuntimeError(
            "Service activation could not find compile-plan ServiceConfig for "
            f"service={service_name!r}."
        )
    if len(service_configs) != 1:
        raise RuntimeError(
            "Service activation found multiple compile-plan ServiceConfigs for "
            f"service={service_name!r}."
        )
    service_payload = dict(payload)
    service_payload["service_configs"] = [dict(service_configs[0])]
    return service_payload


def _experience_reference_branch_ids_from_compile_plan_payload(
    payload: Mapping[str, object],
    *,
    branch_id: UUID,
) -> Mapping[str, UUID]:
    raw_service_configs = payload.get("service_configs", ())
    if not isinstance(raw_service_configs, list):
        return {}

    branch_ids: dict[str, UUID] = {}
    for service_config in raw_service_configs:
        if not isinstance(service_config, Mapping):
            continue
        raw_experiences = service_config.get("experiences", ())
        if not isinstance(raw_experiences, list):
            continue
        for item in raw_experiences:
            if not isinstance(item, Mapping):
                continue
            experience_ref = str(item.get("experience_ref") or "").strip()
            if not experience_ref:
                continue
            branch_ids[experience_ref] = branch_id
            branch_ids[experience_ref.casefold()] = branch_id
    return branch_ids


def _experience_reference_branch_ids_for_activation(
    *,
    provided: Mapping[str, UUID] | None,
    payload: Mapping[str, object],
    fallback_branch_id: UUID,
) -> Mapping[str, UUID]:
    normalized = _normalize_experience_reference_branch_ids_by_experience_name(provided)
    if normalized:
        return normalized
    return _experience_reference_branch_ids_from_compile_plan_payload(
        payload,
        branch_id=fallback_branch_id,
    )


def _role_reference_branch_ids_from_compile_plan_payload(
    payload: Mapping[str, object],
) -> Mapping[str, UUID]:
    raw_service_configs = payload.get("service_configs", ())
    if not isinstance(raw_service_configs, list):
        return {}

    branch_ids: dict[str, UUID] = {}
    for service_config in raw_service_configs:
        if not isinstance(service_config, Mapping):
            continue
        for role_ref in _role_refs_from_service_config_payload(service_config):
            branch_id = stable_service_role_reference_branch_id(
                role_ref=role_ref,
            )
            branch_ids[role_ref] = branch_id
            branch_ids[role_ref.casefold()] = branch_id
    return branch_ids


def _role_refs_from_service_config_payload(
    service_config: Mapping[str, object],
) -> tuple[str, ...]:
    refs: set[str] = set()
    raw_operations = service_config.get("service_operation_configs", ())
    if isinstance(raw_operations, list):
        for operation in raw_operations:
            if not isinstance(operation, Mapping):
                continue
            raw_requirements = operation.get("role_requirements", ())
            if not isinstance(raw_requirements, list):
                continue
            for requirement in raw_requirements:
                if not isinstance(requirement, Mapping):
                    continue
                role_ref = str(requirement.get("role_ref") or "").strip()
                if role_ref:
                    refs.add(role_ref)

    raw_contracts = service_config.get("contract_configs", ())
    if isinstance(raw_contracts, list):
        for contract in raw_contracts:
            if not isinstance(contract, Mapping):
                continue
            raw_grants = contract.get("actor_role_grants", ())
            if not isinstance(raw_grants, list):
                continue
            for grant in raw_grants:
                if not isinstance(grant, Mapping):
                    continue
                role_ref = str(grant.get("role_ref") or "").strip()
                if role_ref:
                    refs.add(role_ref)

    return tuple(sorted(refs, key=str.casefold))


def _role_reference_branch_ids_for_activation(
    *,
    provided: Mapping[str, UUID] | None,
    payload: Mapping[str, object],
) -> Mapping[str, UUID]:
    normalized = _normalize_role_reference_branch_ids_by_role_name(provided)
    if normalized:
        return normalized
    return _role_reference_branch_ids_from_compile_plan_payload(
        payload,
    )


def _normalize_experience_reference_branch_ids_by_experience_name(
    value: Mapping[str, UUID] | None,
) -> Mapping[str, UUID]:
    if not value:
        return {}
    normalized: dict[str, UUID] = {}
    for name, branch_id in value.items():
        token = str(name or "").strip()
        if not token:
            continue
        normalized[token] = branch_id
        normalized[token.casefold()] = branch_id
    return normalized


def _normalize_role_reference_branch_ids_by_role_name(
    value: Mapping[str, UUID] | None,
) -> Mapping[str, UUID]:
    if not value:
        return {}
    normalized: dict[str, UUID] = {}
    for name, branch_id in value.items():
        token = str(name or "").strip()
        if not token:
            continue
        normalized[token] = branch_id
        normalized[token.casefold()] = branch_id
    return normalized


async def _load_committed_service_ids_if_available(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    service_names: tuple[str, ...],
    projection_session_resolver: ProjectionSessionResolver | None = None,
    commit_store_root: Path | None = None,
) -> Mapping[str, UUID] | None:
    head_commit_id = await _committed_lane_head_commit_id(
        lane=lane,
        commit_store_root=commit_store_root,
    )
    if head_commit_id is None:
        return None
    catchup = await _ensure_committed_service_lane_projection_caught_up(
        index=index,
        lane=lane,
        head_commit_id=head_commit_id,
        projection_session_resolver=projection_session_resolver,
        commit_store_root=commit_store_root,
    )
    try:
        service_ids = await _load_committed_service_ids(
            index=index,
            lane=lane,
            service_names=service_names,
            commit_store_root=commit_store_root,
        )
    except RuntimeError as exc:
        if "expected committed Service instances" not in str(exc):
            raise
        return None
    logger.info(
        "Service activation reused committed Service lane identity "
        "service_names=%s branch_id=%s projection_hash=%s head_commit_id=%s "
        "projection_catchup_commits=%s projection_catchup_skipped=%s",
        service_names,
        lane.branch_id,
        lane.projection_hash,
        head_commit_id,
        catchup.commits_applied,
        catchup.skipped_reason,
    )
    return service_ids


async def _load_committed_service_config_head_if_available(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    service_name: str,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    commit_store_root: Path | None = None,
) -> UUID | None:
    head_commit_id = await _committed_lane_head_commit_id(
        lane=lane,
        commit_store_root=commit_store_root,
    )
    if head_commit_id is None:
        return None
    catchup = await _ensure_committed_service_lane_projection_caught_up(
        index=index,
        lane=lane,
        head_commit_id=head_commit_id,
        projection_session_resolver=projection_session_resolver,
        commit_store_root=commit_store_root,
    )
    logger.info(
        "Service activation reused committed ServiceConfig lane identity "
        "service_name=%s branch_id=%s projection_hash=%s head_commit_id=%s "
        "projection_catchup_commits=%s projection_catchup_skipped=%s",
        service_name,
        lane.branch_id,
        lane.projection_hash,
        head_commit_id,
        catchup.commits_applied,
        catchup.skipped_reason,
    )
    return head_commit_id


async def _ensure_committed_service_lane_projection_caught_up(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    head_commit_id: UUID,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    commit_store_root: Path | None = None,
):
    projection_session = (
        projection_session_resolver(lane)
        if projection_session_resolver is not None
        else None
    )
    return await ensure_projection_readiness(
        index=index,
        requirement=ProjectionReadinessRequirement(
            name="service.activation",
            branch_id=lane.branch_id,
            projection_hash=lane.projection_hash,
            head_commit_id=head_commit_id,
            mode=ProjectionReadinessModes.REQUIRED_DB,
        ),
        session=projection_session,
        commit_store=_explicit_commit_store(commit_store_root=commit_store_root),
    )


async def _ensure_service_activation_lane_projection_caught_up(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    projection_session_resolver: ProjectionSessionResolver | None = None,
    commit_store_root: Path | None = None,
):
    head_commit_id = await _committed_lane_head_commit_id(
        lane=lane,
        commit_store_root=commit_store_root,
    )
    if head_commit_id is None:
        return None
    return await _ensure_committed_service_lane_projection_caught_up(
        index=index,
        lane=lane,
        head_commit_id=head_commit_id,
        projection_session_resolver=projection_session_resolver,
        commit_store_root=commit_store_root,
    )


async def _committed_lane_head_commit_id(
    *,
    lane: MaterializationLaneContext,
    commit_store_root: Path | None = None,
) -> UUID | None:
    target_head = await _commit_store(commit_store_root=commit_store_root).head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        return None
    return UUID(str(target_head["commit_id"]))


def _commit_store(*, commit_store_root: Path | None):
    from aware_meta.graph.instance.commit.fs_commit_store import FSCommitStore

    if commit_store_root is None:
        return FSCommitStore()
    return FSCommitStore(root_dir=commit_store_root.expanduser().resolve())


def _explicit_commit_store(*, commit_store_root: Path | None):
    if commit_store_root is None:
        return None
    return _commit_store(commit_store_root=commit_store_root)


def _stable_service_ids_for_names(
    *,
    service_names: tuple[str, ...],
) -> Mapping[str, UUID]:
    return {
        service_name: stable_service_id(
            service_config_id=stable_service_config_id(name=service_name),
            name=service_name,
        )
        for service_name in service_names
    }


def _service_protocol_request_payload(request_object: object) -> object:
    if isinstance(request_object, BaseModel):
        return request_object.model_dump(mode="json")
    return request_object


async def invoke_prepared_service_endpoint_binding(
    *,
    prepared: PreparedServicePackageBinding,
    service_name: str,
    endpoint_ref: str,
    request_object: object,
) -> object | None:
    dependency = _resolve_service_endpoint_dependency(
        prepared=prepared,
        service_name=service_name,
        endpoint_ref=endpoint_ref,
    )
    loaded_package = load_api_service_protocol_package(
        runtime_package_dir=dependency.runtime_package_dir
    )
    binding = loaded_package.endpoint_bindings.get(endpoint_ref)
    if binding is None:
        raise RuntimeError(
            f"API dispatch package {dependency.package_name!r} does not expose endpoint_ref {endpoint_ref!r}."
        )
    handler = prepared.service_bindings[service_name]
    return await binding.invoke(
        handler,
        cast(BaseModel, _service_protocol_request_payload(request_object)),
        None,
    )


async def execute_activated_service_api_dispatch(
    *,
    activated: ActivatedServicePackageBinding,
    runtime,
    index: MetaGraphRuntimeIndex,
    session,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    api_source_lane: MaterializationLaneContext | None = None,
    execution_target_lane: MaterializationLaneContext | None = None,
    service_package_id: UUID | None = None,
    service_package_name: str | None = None,
    service_name: str,
    operation_key: str,
    dispatch_plan: ApiServiceDispatchPlan,
    execution_backend: ServiceApiExecutionBackend | None = None,
    execution_backend_mode: ServiceApiExecutionBackendMode | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None = None,
    workspace_root: Path | None = None,
    stream_requested: bool = False,
    stream_event_sink: ServiceApiStreamEventSink | None = None,
    economy_settlement_adapter: ServiceOperationEconomySettlementAdapter | None = None,
    operation_access_context: ServiceApiOperationAccessContext | None = None,
    actor_role_evidence: tuple[ServiceApiActorRoleEvidence, ...] = (),
    invocation_context: Mapping[str, object] | None = None,
    ontology_authority_package_names: tuple[str, ...] = (),
    ontology_authority_source_kind: str | None = None,
    ontology_authority_root: Path | None = None,
    receipt_policy: ServiceApiDispatchReceiptPolicy = (
        ServiceApiDispatchReceiptPolicy.committed
    ),
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = (),
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...] = (),
    environment_commit_receipt_source: (
        ServiceEnvironmentCommitReceiptSource | None
    ) = None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None = None,
    ontology_replica_orm_session: (
        ServiceOntologyReplicaOrmSessionProtocol | None
    ) = None,
) -> ExecutedServiceApiDispatch:
    _ = _resolve_service_endpoint_dependency(
        prepared=activated.prepared,
        service_name=service_name,
        endpoint_ref=dispatch_plan.endpoint_ref,
    )
    service_id = activated.service_ids_by_name.get(service_name)
    if service_id is None:
        raise RuntimeError(
            f"Activated Service package is missing committed service_id for {service_name!r}."
        )
    handler = activated.prepared.service_bindings[service_name]
    if dispatch_plan.build_execution is not None:
        if execution_backend is None and execution_backend_mode is None:
            raise RuntimeError(
                "Service implementation-package dispatch requires explicit host-owned execution routing "
                "when the compiled API dispatch contract exposes an execution surface."
            )
    return await execute_service_api_dispatch_plan(
        runtime=runtime,
        index=index,
        session=session,
        actor_id=actor_id,
        target_lane=target_lane,
        api_source_lane=api_source_lane,
        execution_target_lane=execution_target_lane,
        dispatch_plan=dispatch_plan,
        service_id=service_id,
        operation_key=operation_key,
        handler=handler,
        execution_backend=execution_backend,
        execution_backend_mode=(
            execution_backend_mode
            if execution_backend_mode is not None
            else ServiceApiExecutionBackendMode.auto
        ),
        graph_gateway=graph_gateway,
        meta_temporal_graph_route=meta_temporal_graph_route,
        workspace_root=workspace_root,
        service_name=service_name,
        service_package_id=service_package_id,
        service_package_name=(
            service_package_name
            or _service_package_name_for_activated_binding(activated)
        ),
        lane_subscriptions=activated.service_subscriptions_by_name.get(
            service_name, ()
        ),
        service_api_dependency_routes=service_api_dependency_routes,
        service_view_provider_routes=service_view_provider_routes,
        environment_commit_receipt_source=environment_commit_receipt_source,
        experience_reference_branch_ids_by_experience_name=(
            activated.experience_reference_branch_ids_by_experience_name
        ),
        stream_requested=stream_requested,
        stream_event_sink=stream_event_sink,
        economy_settlement_adapter=economy_settlement_adapter,
        operation_access_context=operation_access_context,
        actor_role_evidence=actor_role_evidence,
        invocation_context=(
            cast(JsonObject, dict(invocation_context or {}))
            if invocation_context
            else None
        ),
        ontology_replica_query=ontology_replica_query,
        ontology_replica_orm_session=ontology_replica_orm_session,
        ontology_authority_package_names=ontology_authority_package_names,
        ontology_authority_source_kind=ontology_authority_source_kind,
        ontology_authority_root=ontology_authority_root,
        receipt_policy=receipt_policy,
    )


def build_service_api_dispatch_request(
    *,
    operation_key: str,
    dispatch_plan: ApiServiceDispatchPlan,
) -> ServiceApiDispatchRequest:
    request_payload = dispatch_plan.request_object.model_dump(mode="json")
    if not isinstance(request_payload, dict):
        raise RuntimeError(
            "Service network-operation API dispatch requires a JSON-object request payload."
        )
    return ServiceApiDispatchRequest(
        operation_key=operation_key,
        envelope=ServiceApiDispatchEnvelope(
            api_call_id=dispatch_plan.envelope.api_call_id,
            api_capability_endpoint_id=dispatch_plan.envelope.api_capability_endpoint_id,
            call_key=dispatch_plan.envelope.call_key,
            request_hash=dispatch_plan.envelope.request_hash,
            commit_id=dispatch_plan.envelope.commit_id,
            head_commit_id=dispatch_plan.envelope.head_commit_id,
            branch_id=dispatch_plan.envelope.branch_id,
            projection_hash=dispatch_plan.envelope.projection_hash,
            api_name=dispatch_plan.envelope.api_name,
            capability_name=dispatch_plan.envelope.capability_name,
            endpoint_name=dispatch_plan.envelope.endpoint_name,
            endpoint_ref=dispatch_plan.envelope.endpoint_ref,
            discriminant=dispatch_plan.envelope.discriminant,
            source_path=dispatch_plan.envelope.source_path,
            request_model_id=dispatch_plan.envelope.request_model_id,
            request_class_config_id=dispatch_plan.envelope.request_class_config_id,
            request_class_ref=dispatch_plan.envelope.request_class_ref,
            request_source_path=dispatch_plan.envelope.request_source_path,
            response_class_ref=dispatch_plan.envelope.response_class_ref,
            response_source_path=dispatch_plan.envelope.response_source_path,
        ),
        request_payload=cast(JsonObject, request_payload),
        fulfillment_bindings=[
            ServiceApiDispatchFulfillmentBinding(
                name=binding.name,
                graph_target=binding.graph_target,
                graph_capability_function_name=binding.graph_capability_function_name,
                graph_function_python_ref=binding.graph_function_python_ref,
                graph_function_runtime_target=binding.graph_function_runtime_target,
                method_name=binding.method_name,
                request_type_ref=binding.request_type_ref,
                response_type_ref=binding.response_type_ref,
                source_path=binding.source_path,
                api_capability_endpoint_function_id=binding.api_capability_endpoint_function_id,
            )
            for binding in dispatch_plan.fulfillment_bindings
        ],
    )


def build_service_operation_request_for_api_dispatch(
    *,
    context: ServiceOperationContext,
    service_name: str,
    operation_key: str,
    dispatch_plan: ApiServiceDispatchPlan,
    stream_target_id: UUID | None = None,
    stream_correlation_id: UUID | None = None,
    network_request_id: UUID | None = None,
) -> ServiceOperationRequest:
    return ServiceOperationRequest(
        context=context,
        service=service_name,
        operation=None,
        api_dispatch=build_service_api_dispatch_request(
            operation_key=operation_key,
            dispatch_plan=dispatch_plan,
        ),
        stream_target_id=stream_target_id,
        stream_correlation_id=stream_correlation_id,
        network_request_id=network_request_id,
    )


def _coerce_service_operation_settlement_policy(
    value: object,
) -> ServiceOperationSettlementPolicy | None:
    if isinstance(value, ServiceOperationSettlementPolicy):
        return value
    token = str(value or "").strip()
    if not token:
        return ServiceOperationSettlementPolicy.none
    try:
        return ServiceOperationSettlementPolicy(token)
    except ValueError:
        return None


def _coerce_service_operation_receipt_policy(
    value: object,
) -> ServiceOperationReceiptPolicy | None:
    if isinstance(value, ServiceOperationReceiptPolicy):
        return value
    token = str(value or "").strip()
    if not token:
        return ServiceOperationReceiptPolicy.committed
    try:
        return ServiceOperationReceiptPolicy(token)
    except ValueError:
        return None


def resolve_prepared_service_api_receipt_policy(
    *,
    activated: ActivatedServicePackageBinding,
    service_name: str,
    endpoint_ref: str,
) -> ServiceOperationReceiptPolicy:
    compile_plan = activated.prepared.compile_result.compile_plan
    if compile_plan is None:
        return ServiceOperationReceiptPolicy.committed

    operation_matches = tuple(
        operation_config
        for service_config in compile_plan.service_configs
        if service_config.name.strip().casefold() == service_name.strip().casefold()
        for operation_config in service_config.service_operation_configs
        for endpoint_plan in operation_config.api_endpoints
        if endpoint_plan.endpoint_ref.strip().casefold()
        == endpoint_ref.strip().casefold()
    )
    if len(operation_matches) != 1:
        return ServiceOperationReceiptPolicy.committed
    receipt_policy = _coerce_service_operation_receipt_policy(
        operation_matches[0].receipt_policy
    )
    return receipt_policy or ServiceOperationReceiptPolicy.committed


def build_prepared_service_config_session_for_api_dispatch(
    *,
    activated: ActivatedServicePackageBinding,
    service_name: str,
    dispatch_plan: ApiServiceDispatchPlan,
    service_config_lane: MaterializationLaneContext,
) -> object | None:
    """Build a minimal ServiceConfig session from compiled package evidence.

    This is intentionally narrow: endpoint-only API dispatch can use stable
    Service-owned IDs already present in the compiled package plan. Dispatches
    with Service-owned fulfillment grants or settlement metadata still hydrate
    the committed lane so canonical committed objects remain the authority.
    """
    if dispatch_plan.fulfillment_bindings:
        return None

    compile_plan = activated.prepared.compile_result.compile_plan
    if compile_plan is None:
        return None

    service_configs = tuple(
        item
        for item in compile_plan.service_configs
        if item.name.strip().casefold() == service_name.strip().casefold()
    )
    if len(service_configs) != 1:
        return None
    service_config = service_configs[0]

    operation_matches = tuple(
        (operation_config, endpoint_plan)
        for operation_config in service_config.service_operation_configs
        for endpoint_plan in operation_config.api_endpoints
        if endpoint_plan.endpoint_ref.strip().casefold()
        == dispatch_plan.endpoint_ref.strip().casefold()
    )
    if len(operation_matches) != 1:
        return None
    operation_config, endpoint_plan = operation_matches[0]

    settlement_policy = _coerce_service_operation_settlement_policy(
        operation_config.settlement_policy
    )
    receipt_policy = _coerce_service_operation_receipt_policy(
        operation_config.receipt_policy
    )
    if settlement_policy is None:
        return None
    if receipt_policy is None:
        return None
    if (
        settlement_policy.value != "none"
        or operation_config.price is not None
        or str(operation_config.price_ref or "").strip()
    ):
        return None

    endpoint_api_ref = endpoint_plan.api_ref.strip()
    if not endpoint_api_ref:
        endpoint_api_ref = dispatch_plan.api_name.strip()
    if (
        dispatch_plan.api_name.strip()
        and endpoint_api_ref.casefold() != dispatch_plan.api_name.strip().casefold()
    ):
        return None

    from aware_orm.session.session import Session
    from aware_service_ontology.service.service_config_api import ServiceConfigApi
    from aware_service_ontology.service.service_operation_config import (
        ServiceOperationConfig,
    )
    from aware_service_ontology.service.service_operation_config_api_endpoint import (
        ServiceOperationConfigApiEndpoint,
    )

    service_config_id = stable_service_config_id(name=service_config.name)
    service_config_api_id = stable_service_config_api_id(
        service_config_id=service_config_id,
        api_id=stable_api_id(name=endpoint_api_ref),
    )
    service_operation_config_id = stable_service_operation_config_id(
        service_config_id=service_config_id,
        name=operation_config.name,
    )
    endpoint_binding_id = stable_service_operation_config_api_endpoint_id(
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=dispatch_plan.envelope.api_capability_endpoint_id,
    )

    service_config_api = ServiceConfigApi(
        id=service_config_api_id,
        service_config_id=service_config_id,
        api_id=stable_api_id(name=endpoint_api_ref),
        description=None,
    )
    service_operation_config = ServiceOperationConfig(
        id=service_operation_config_id,
        service_config_id=service_config_id,
        name=operation_config.name,
        description=None,
        admission_mode=ServiceOperationAdmissionMode(operation_config.admission_mode),
        fulfillment_kind=ServiceOperationFulfillmentKind(
            operation_config.fulfillment_kind
        ),
        receipt_policy=receipt_policy,
        settlement_policy=settlement_policy,
        price_id=None,
    )
    if not hasattr(service_operation_config, "admission_mode"):
        object.__setattr__(
            service_operation_config,
            "admission_mode",
            operation_config.admission_mode,
        )
    if not hasattr(service_operation_config, "fulfillment_kind"):
        object.__setattr__(
            service_operation_config,
            "fulfillment_kind",
            operation_config.fulfillment_kind,
        )
    endpoint_binding = ServiceOperationConfigApiEndpoint(
        id=endpoint_binding_id,
        service_operation_config_id=service_operation_config_id,
        service_config_api_id=service_config_api_id,
        api_capability_endpoint_id=dispatch_plan.envelope.api_capability_endpoint_id,
        description=None,
    )
    service_operation_config.api_endpoints.append(endpoint_binding)

    session = Session(branch_id=service_config_lane.branch_id, skip_db=True)
    session.imap_add(service_config_api)
    session.imap_add(service_operation_config)
    session.imap_add(endpoint_binding)
    return session


async def build_activated_service_api_dispatch_plan_from_ingress(
    *,
    activated: ActivatedServicePackageBinding,
    runtime,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    api_source_lane: MaterializationLaneContext,
    api_call_lane: MaterializationLaneContext,
    service_name: str,
    endpoint_ref: str,
    discriminant: str,
    request_payload: Mapping[str, object],
    call_key: UUID | None = None,
    receipt_projection_backend: str | None = None,
) -> ApiServiceDispatchPlan:
    trace_fields = {
        "endpoint_ref": endpoint_ref,
        "service_name": service_name,
        "discriminant": discriminant,
    }
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.resolve_dependency",
        **trace_fields,
    ):
        dependency = _resolve_service_endpoint_dependency(
            prepared=activated.prepared,
            service_name=service_name,
            endpoint_ref=endpoint_ref,
        )
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.resolve_api_source_lane",
        runtime_package_dir=dependency.runtime_package_dir.as_posix(),
        **trace_fields,
    ):
        resolved_api_source_lane = _resolve_api_source_lane_for_endpoint_ref(
            default_lane=api_source_lane,
            endpoint_ref=endpoint_ref,
            api_reference_branch_ids_by_api_name=(
                activated.api_reference_branch_ids_by_api_name
            ),
        )
        resolved_api_call_lane = MaterializationLaneContext(
            branch_id=resolved_api_source_lane.branch_id,
            projection_hash=api_call_lane.projection_hash,
        )
    compact_deferred_payload = should_use_compact_api_receipt_payload(
        payload=request_payload,
        commit=True,
    )
    cache_key = _deferred_dispatch_template_cache_key(
        activated=activated,
        index=index,
        dependency=dependency,
        service_name=service_name,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.deferred_template_cache_lookup",
        compact_deferred_payload=compact_deferred_payload,
        **trace_fields,
    ):
        deferred_template = (
            _DEFERRED_DISPATCH_TEMPLATE_CACHE.get(cache_key)
            if compact_deferred_payload
            else None
        )
    if deferred_template is not None:
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.load_invocation_manifest",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            pass
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.build_invocation_ir",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            pass
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.build_deferred_invocation_plan",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            deferred_plan = _deferred_dispatch_plan_from_template(
                template=deferred_template,
                request_payload=request_payload,
                projection_hash=resolved_api_call_lane.projection_hash,
                call_key=call_key,
            )
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.payload_field_guard",
            request_type_ref=deferred_plan.request_type_ref,
            deferred_api_call=True,
            cache_hit=True,
            **trace_fields,
        ):
            _raise_if_api_request_model_dropped_payload_fields(
                endpoint_ref=endpoint_ref,
                request_type_ref=deferred_plan.request_type_ref,
                request_model_cls=type(deferred_plan.request_object),
                request_payload=request_payload,
                request_object=deferred_plan.request_object,
            )
        logger.info(
            "Service API dispatch plan used cached deferred endpoint-only envelope "
            f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
            f"api_call_id={deferred_plan.envelope.api_call_id} "
            f"request_class_config_id={deferred_plan.envelope.request_class_config_id}"
        )
        return deferred_plan
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.load_invocation_manifest",
        runtime_package_dir=dependency.runtime_package_dir.as_posix(),
        **trace_fields,
    ):
        invocation_manifest = _load_dependency_api_invocation_manifest(
            runtime_package_dir=dependency.runtime_package_dir
        )
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.build_invocation_ir",
        runtime_package_dir=dependency.runtime_package_dir.as_posix(),
        **trace_fields,
    ):
        ir = _build_api_invocation_ir_from_loaded_manifest(
            index=index,
            invocation_manifest=invocation_manifest,
            runtime_package_dir=dependency.runtime_package_dir,
            endpoint_ref=endpoint_ref,
            discriminant=discriminant,
            request_payload=request_payload,
        )
    if not ir.fulfillment_bindings and compact_deferred_payload:
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.build_deferred_invocation_plan",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=False,
            **trace_fields,
        ):
            deferred_plan = build_api_service_dispatch_plan_from_invocation_ir(
                index=index,
                ir=ir,
                runtime_package_dir=dependency.runtime_package_dir,
                branch_id=uuid4(),
                projection_hash=resolved_api_call_lane.projection_hash,
            )
        if (
            not deferred_plan.fulfillment_bindings
            and deferred_plan.build_execution is None
            and deferred_plan.stream_invoke is None
        ):
            if call_key is not None:
                deferred_plan = _deferred_dispatch_plan_from_template(
                    template=_deferred_dispatch_template_from_plan(plan=deferred_plan),
                    request_payload=request_payload,
                    projection_hash=resolved_api_call_lane.projection_hash,
                    call_key=call_key,
                )
            with service_api_trace_phase(
                "service_host.api_ingress.dispatch_plan.payload_field_guard",
                request_type_ref=deferred_plan.request_type_ref,
                deferred_api_call=True,
                **trace_fields,
            ):
                _raise_if_api_request_model_dropped_payload_fields(
                    endpoint_ref=endpoint_ref,
                    request_type_ref=deferred_plan.request_type_ref,
                    request_model_cls=type(deferred_plan.request_object),
                    request_payload=request_payload,
                    request_object=deferred_plan.request_object,
                )
            with service_api_trace_phase(
                "service_host.api_ingress.dispatch_plan.deferred_template_cache_store",
                **trace_fields,
            ):
                _DEFERRED_DISPATCH_TEMPLATE_CACHE[cache_key] = (
                    _deferred_dispatch_template_from_plan(plan=deferred_plan)
                )
            logger.info(
                "Service API dispatch plan used deferred endpoint-only envelope "
                f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
                f"api_call_id={deferred_plan.envelope.api_call_id} "
                f"request_class_config_id={deferred_plan.envelope.request_class_config_id}"
            )
            return deferred_plan
        with service_api_trace_phase(
            "service_host.api_ingress.dispatch_plan.deferred_invocation_fallback",
            has_fulfillment=bool(deferred_plan.fulfillment_bindings),
            has_execution=deferred_plan.build_execution is not None,
            has_stream=deferred_plan.stream_invoke is not None,
            **trace_fields,
        ):
            pass
    logger.info(
        "Service API dispatch plan subphase started: dispatch_api_invocation "
        f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
        f"request_class_config_id={ir.request_class_config_id} "
        f"fulfillment_bindings={len(ir.fulfillment_bindings)}"
    )
    with collect_api_invocation_trace_timings() as api_invocation_timings:
        dispatched_invocation = await await_with_service_api_trace(
            dispatch_api_invocation(
                runtime=runtime,
                index=index,
                actor_id=actor_id,
                source_lane=resolved_api_source_lane,
                target_lane=resolved_api_call_lane,
                ir=ir,
                call_key=call_key,
                receipt_projection_backend=receipt_projection_backend,
            ),
            phase="service_host.api_ingress.dispatch_plan.dispatch_api_invocation",
            fields=trace_fields,
            api_source_branch_id=str(resolved_api_source_lane.branch_id),
            api_call_branch_id=str(resolved_api_call_lane.branch_id),
            api_call_projection_hash=resolved_api_call_lane.projection_hash,
        )
    _record_api_invocation_trace_timings_for_servicehost(
        timings=api_invocation_timings,
    )
    logger.info(
        "Service API dispatch plan subphase finished: dispatch_api_invocation "
        f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
        f"api_call_id={dispatched_invocation.envelope.api_call_id} "
        f"request_class_config_id={dispatched_invocation.envelope.request_class_config_id}"
    )
    logger.info(
        "Service API dispatch plan subphase started: build_api_service_dispatch_plan_from_materialized_call "
        f"endpoint_ref={endpoint_ref!r} service_name={service_name!r}"
    )
    dispatch_plan = await await_with_service_api_trace(
        build_api_service_dispatch_plan_from_materialized_call(
            index=index,
            envelope=dispatched_invocation.envelope,
            api_call=dispatched_invocation.materialized_call.api_call,
            request_class_config=(
                dispatched_invocation.materialized_call.request_class_config
            ),
            runtime_package_dir=dependency.runtime_package_dir,
            request_payload_override=request_payload,
        ),
        phase=(
            "service_host.api_ingress.dispatch_plan." "build_from_materialized_call"
        ),
        fields=trace_fields,
        runtime_package_dir=dependency.runtime_package_dir.as_posix(),
        api_call_id=str(dispatched_invocation.envelope.api_call_id),
        request_class_config_id=str(
            dispatched_invocation.envelope.request_class_config_id
        ),
    )
    with service_api_trace_phase(
        "service_host.api_ingress.dispatch_plan.payload_field_guard",
        request_type_ref=dispatch_plan.request_type_ref,
        **trace_fields,
    ):
        _raise_if_api_request_model_dropped_payload_fields(
            endpoint_ref=endpoint_ref,
            request_type_ref=dispatch_plan.request_type_ref,
            request_model_cls=type(dispatch_plan.request_object),
            request_payload=request_payload,
            request_object=dispatch_plan.request_object,
        )
    logger.info(
        "Service API dispatch plan subphase finished: build_api_service_dispatch_plan_from_materialized_call "
        f"endpoint_ref={endpoint_ref!r} service_name={service_name!r}"
    )
    return dispatch_plan


async def build_activated_service_api_read_model_dispatch_plan_from_ingress(
    *,
    activated: ActivatedServicePackageBinding,
    index: MetaGraphRuntimeIndex,
    api_call_lane: MaterializationLaneContext,
    service_name: str,
    endpoint_ref: str,
    discriminant: str,
    request_payload: Mapping[str, object],
) -> ApiServiceDispatchPlan:
    trace_fields = {
        "endpoint_ref": endpoint_ref,
        "service_name": service_name,
        "discriminant": discriminant,
    }
    with service_api_trace_phase(
        "service_host.api_ingress.read_model_dispatch_plan.resolve_dependency",
        **trace_fields,
    ):
        dependency = _resolve_service_endpoint_dependency(
            prepared=activated.prepared,
            service_name=service_name,
            endpoint_ref=endpoint_ref,
        )
    cache_key = _read_model_dispatch_template_cache_key(
        activated=activated,
        index=index,
        dependency=dependency,
        service_name=service_name,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )
    with service_api_trace_phase(
        "service_host.api_ingress.read_model_dispatch_plan.template_cache_lookup",
        **trace_fields,
    ):
        template = _READ_MODEL_DISPATCH_TEMPLATE_CACHE.get(cache_key)
    cache_hit = template is not None
    if template is None:
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.load_invocation_manifest",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=False,
            **trace_fields,
        ):
            invocation_manifest = _load_dependency_api_invocation_manifest(
                runtime_package_dir=dependency.runtime_package_dir
            )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.build_invocation_ir",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=False,
            **trace_fields,
        ):
            ir = _build_api_invocation_ir_from_loaded_manifest(
                index=index,
                invocation_manifest=invocation_manifest,
                runtime_package_dir=dependency.runtime_package_dir,
                endpoint_ref=endpoint_ref,
                discriminant=discriminant,
                request_payload=request_payload,
            )
        if ir.fulfillment_bindings:
            raise RuntimeError(
                "Service API read-model dispatch v0 supports endpoint-only service handlers. "
                "Graph fulfillment endpoints must use committed dispatch receipts: "
                f"endpoint_ref={endpoint_ref!r}"
            )
        logger.info(
            "Service API dispatch plan subphase started: build_read_model_dispatch_plan "
            f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
            f"request_class_config_id={ir.request_class_config_id}"
        )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.load_service_protocol_package",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=False,
            **trace_fields,
        ):
            loaded_package = load_api_service_protocol_package(
                runtime_package_dir=dependency.runtime_package_dir
            )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.resolve_endpoint_binding",
            cache_hit=False,
            **trace_fields,
        ):
            endpoint_binding = loaded_package.endpoint_bindings.get(endpoint_ref)
        if endpoint_binding is None:
            raise RuntimeError(
                "Activated Service package could not resolve a compiled API dispatch binding for "
                f"read-model endpoint_ref={endpoint_ref!r}."
            )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.resolve_request_model_class",
            request_type_ref=endpoint_binding.request_type_ref,
            cache_hit=False,
            **trace_fields,
        ):
            request_model_cls = _resolve_generated_request_model_class(
                loaded_package=loaded_package,
                endpoint_binding=endpoint_binding,
            )
        template = _ReadModelDispatchTemplate(
            ir_template=replace(ir, request_payload={}),
            loaded_package=loaded_package,
            endpoint_binding=endpoint_binding,
            request_model_cls=request_model_cls,
        )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.template_cache_store",
            **trace_fields,
        ):
            _READ_MODEL_DISPATCH_TEMPLATE_CACHE[cache_key] = template
    else:
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.load_invocation_manifest",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            pass
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.build_invocation_ir",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            pass
        logger.info(
            "Service API dispatch plan subphase started: build_read_model_dispatch_plan "
            f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
            f"request_class_config_id={template.ir_template.request_class_config_id}"
        )
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.load_service_protocol_package",
            runtime_package_dir=dependency.runtime_package_dir.as_posix(),
            cache_hit=True,
            **trace_fields,
        ):
            pass
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.resolve_endpoint_binding",
            cache_hit=True,
            **trace_fields,
        ):
            pass
        with service_api_trace_phase(
            "service_host.api_ingress.read_model_dispatch_plan.resolve_request_model_class",
            request_type_ref=template.endpoint_binding.request_type_ref,
            cache_hit=True,
            **trace_fields,
        ):
            pass
    ir = _read_model_dispatch_template_ir(
        template=template,
        request_payload=request_payload,
    )
    loaded_package = template.loaded_package
    endpoint_binding = template.endpoint_binding
    request_model_cls = template.request_model_cls
    with service_api_trace_phase(
        "service_host.api_ingress.read_model_dispatch_plan.request_model_validate",
        request_type_ref=endpoint_binding.request_type_ref,
        cache_hit=cache_hit,
        **trace_fields,
    ):
        request_object = request_model_cls.model_validate(dict(request_payload))
    with service_api_trace_phase(
        "service_host.api_ingress.read_model_dispatch_plan.payload_field_guard",
        request_type_ref=endpoint_binding.request_type_ref,
        cache_hit=cache_hit,
        **trace_fields,
    ):
        _raise_if_api_request_model_dropped_payload_fields(
            endpoint_ref=endpoint_ref,
            request_type_ref=endpoint_binding.request_type_ref,
            request_model_cls=request_model_cls,
            request_payload=request_payload,
            request_object=request_object,
        )
    with service_api_trace_phase(
        "service_host.api_ingress.read_model_dispatch_plan.build_envelope",
        cache_hit=cache_hit,
        **trace_fields,
    ):
        envelope = _build_read_model_api_invocation_envelope(
            ir=ir,
            api_call_lane=api_call_lane,
        )
    logger.info(
        "Service API dispatch plan subphase finished: build_read_model_dispatch_plan "
        f"endpoint_ref={endpoint_ref!r} service_name={service_name!r} "
        f"api_call_id={envelope.api_call_id} request_class_config_id={envelope.request_class_config_id}"
    )
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root=loaded_package.public_package_import_root,
        service_protocol_import_root=loaded_package.service_protocol_import_root,
        endpoint_ref=envelope.endpoint_ref,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        request_type_ref=endpoint_binding.request_type_ref,
        response_type_ref=endpoint_binding.response_type_ref,
        stream_event_type_refs=endpoint_binding.stream_event_type_refs,
        execution_protocol_ref=endpoint_binding.execution_protocol_ref,
        build_execution=endpoint_binding.build_execution,
        stream_invoke=endpoint_binding.stream_invoke,
        fulfillment_bindings=(),
        request_object=request_object,
        invoke=endpoint_binding.invoke,
    )


def _record_api_invocation_trace_timings_for_servicehost(
    *,
    timings: Mapping[str, float],
) -> None:
    for key, duration_s in sorted(timings.items()):
        phase = key[:-2] if key.endswith("_s") else key
        record_service_api_trace_timing(
            phase=f"service_host.api_ingress.dispatch_plan.{phase}",
            duration_s=duration_s,
        )


def _read_model_dispatch_template_cache_key(
    *,
    activated: ActivatedServicePackageBinding,
    index: MetaGraphRuntimeIndex,
    dependency: ServicePackageDependencyBinding,
    service_name: str,
    endpoint_ref: str,
    discriminant: str,
) -> _ReadModelDispatchTemplateCacheKey:
    return _ReadModelDispatchTemplateCacheKey(
        prepared_identity=id(activated.prepared),
        runtime_index_identity=id(index),
        runtime_package_dir=dependency.runtime_package_dir.resolve().as_posix(),
        service_protocol_plan_hash_sha256=dependency.service_protocol_plan_hash_sha256,
        service_name=service_name,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )


def _deferred_dispatch_template_cache_key(
    *,
    activated: ActivatedServicePackageBinding,
    index: MetaGraphRuntimeIndex,
    dependency: ServicePackageDependencyBinding,
    service_name: str,
    endpoint_ref: str,
    discriminant: str,
) -> _DeferredDispatchTemplateCacheKey:
    return _DeferredDispatchTemplateCacheKey(
        prepared_identity=id(activated.prepared),
        runtime_index_identity=id(index),
        runtime_package_dir=dependency.runtime_package_dir.resolve().as_posix(),
        service_protocol_plan_hash_sha256=dependency.service_protocol_plan_hash_sha256,
        service_name=service_name,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )


def _deferred_dispatch_template_from_plan(
    *,
    plan: ApiServiceDispatchPlan,
) -> _DeferredDispatchTemplate:
    return _DeferredDispatchTemplate(
        api_capability_endpoint_id=plan.envelope.api_capability_endpoint_id,
        api_name=plan.envelope.api_name,
        capability_name=plan.envelope.capability_name,
        endpoint_name=plan.envelope.endpoint_name,
        endpoint_ref=plan.envelope.endpoint_ref,
        discriminant=plan.envelope.discriminant,
        source_path=plan.envelope.source_path,
        request_class_config_id=plan.envelope.request_class_config_id,
        request_class_ref=plan.envelope.request_class_ref,
        request_source_path=plan.envelope.request_source_path,
        request_type_ref=plan.request_type_ref,
        response_class_ref=plan.envelope.response_class_ref,
        response_source_path=plan.envelope.response_source_path,
        response_type_ref=plan.response_type_ref,
        stream_event_type_refs=plan.stream_event_type_refs,
        execution_protocol_ref=plan.execution_protocol_ref,
        description=plan.envelope.description,
        public_package_import_root=plan.public_package_import_root,
        service_protocol_import_root=plan.service_protocol_import_root,
        build_execution=plan.build_execution,
        stream_invoke=plan.stream_invoke,
        request_model_cls=type(plan.request_object),
        invoke=plan.invoke,
    )


def _deferred_dispatch_plan_from_template(
    *,
    template: _DeferredDispatchTemplate,
    request_payload: Mapping[str, object],
    projection_hash: str,
    call_key: UUID | None = None,
) -> ApiServiceDispatchPlan:
    request_payload_dict = dict(request_payload)
    request_object = template.request_model_cls.model_validate(request_payload_dict)
    envelope = _deferred_dispatch_envelope_from_template(
        template=template,
        request_payload=request_payload_dict,
        projection_hash=projection_hash,
        call_key=call_key,
    )
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root=template.public_package_import_root,
        service_protocol_import_root=template.service_protocol_import_root,
        endpoint_ref=template.endpoint_ref,
        api_name=template.api_name,
        capability_name=template.capability_name,
        endpoint_name=template.endpoint_name,
        request_type_ref=template.request_type_ref,
        response_type_ref=template.response_type_ref,
        stream_event_type_refs=template.stream_event_type_refs,
        execution_protocol_ref=template.execution_protocol_ref,
        build_execution=template.build_execution,
        stream_invoke=template.stream_invoke,
        fulfillment_bindings=(),
        request_object=request_object,
        invoke=template.invoke,
    )


def _deferred_dispatch_envelope_from_template(
    *,
    template: _DeferredDispatchTemplate,
    request_payload: Mapping[str, object],
    projection_hash: str,
    call_key: UUID | None = None,
) -> ResolvedApiInvocationEnvelope:
    resolved_call_key = call_key or uuid4()
    api_call_id = stable_api_call_id(
        api_capability_endpoint_id=template.api_capability_endpoint_id,
        call_key=resolved_call_key,
    )
    request_model_id = stable_inline_value_instance_id(
        class_config_id=template.request_class_config_id,
        owner_key=resolved_call_key,
    )
    synthetic_commit_id = uuid5(
        NAMESPACE_URL,
        f"aware:api_deferred_dispatch_commit:{api_call_id}",
    )
    return ResolvedApiInvocationEnvelope(
        api_call_id=api_call_id,
        api_capability_endpoint_id=template.api_capability_endpoint_id,
        call_key=resolved_call_key,
        request_hash=compute_api_request_hash_from_mapping(payload=request_payload),
        commit_id=synthetic_commit_id,
        head_commit_id=synthetic_commit_id,
        branch_id=uuid4(),
        projection_hash=projection_hash,
        api_name=template.api_name,
        capability_name=template.capability_name,
        endpoint_name=template.endpoint_name,
        endpoint_ref=template.endpoint_ref,
        discriminant=template.discriminant,
        source_path=template.source_path,
        request_model_id=request_model_id,
        request_class_config_id=template.request_class_config_id,
        request_class_ref=template.request_class_ref,
        request_source_path=template.request_source_path,
        response_class_ref=template.response_class_ref,
        response_source_path=template.response_source_path,
        stream=None,
        fulfillment_bindings=(),
        description=template.description,
        deferred_api_call=True,
    )


def _read_model_dispatch_template_ir(
    *,
    template: _ReadModelDispatchTemplate,
    request_payload: Mapping[str, object],
) -> ApiInvocationIR:
    return replace(template.ir_template, request_payload=dict(request_payload))


def _clear_service_api_read_model_dispatch_plan_cache() -> None:
    _READ_MODEL_DISPATCH_TEMPLATE_CACHE.clear()


def _clear_service_api_deferred_dispatch_plan_cache() -> None:
    _DEFERRED_DISPATCH_TEMPLATE_CACHE.clear()


def resolve_activated_service_api_source_lane(
    *,
    activated: ActivatedServicePackageBinding,
    default_lane: MaterializationLaneContext,
    endpoint_ref: str,
) -> MaterializationLaneContext:
    return _resolve_api_source_lane_for_endpoint_ref(
        default_lane=default_lane,
        endpoint_ref=endpoint_ref,
        api_reference_branch_ids_by_api_name=(
            getattr(activated, "api_reference_branch_ids_by_api_name", None)
        ),
    )


async def execute_activated_service_api_dispatch_request(
    *,
    activated: ActivatedServicePackageBinding,
    runtime,
    index: MetaGraphRuntimeIndex,
    session,
    actor_id: UUID | None,
    target_lane: MaterializationLaneContext,
    service_package_id: UUID | None = None,
    service_package_name: str | None = None,
    service_name: str,
    dispatch_request: ServiceApiDispatchRequest,
    execution_backend: ServiceApiExecutionBackend | None = None,
    execution_backend_mode: ServiceApiExecutionBackendMode | None = None,
    graph_gateway: ServiceGraphGateway | None = None,
    meta_temporal_graph_route: MetaTemporalGraphRoute | None = None,
    workspace_root: Path | None = None,
    stream_requested: bool = False,
    stream_event_sink: ServiceApiStreamEventSink | None = None,
    economy_settlement_adapter: ServiceOperationEconomySettlementAdapter | None = None,
    invocation_context: Mapping[str, object] | None = None,
    ontology_authority_package_names: tuple[str, ...] = (),
    ontology_authority_source_kind: str | None = None,
    ontology_authority_root: Path | None = None,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...] = (),
    service_view_provider_routes: tuple[ServiceViewProviderRouteDescriptor, ...] = (),
    environment_commit_receipt_source: (
        ServiceEnvironmentCommitReceiptSource | None
    ) = None,
    ontology_replica_query: ServiceOntologyReplicaQueryProtocol | None = None,
    ontology_replica_orm_session: (
        ServiceOntologyReplicaOrmSessionProtocol | None
    ) = None,
) -> ExecutedServiceApiDispatch:
    dispatch_plan = _rebuild_activated_service_api_dispatch_plan(
        activated=activated,
        index=index,
        service_name=service_name,
        dispatch_request=dispatch_request,
    )
    return await execute_activated_service_api_dispatch(
        activated=activated,
        runtime=runtime,
        index=index,
        session=session,
        actor_id=actor_id,
        target_lane=target_lane,
        service_package_id=service_package_id,
        service_package_name=service_package_name,
        service_name=service_name,
        operation_key=dispatch_request.operation_key,
        dispatch_plan=dispatch_plan,
        execution_backend=execution_backend,
        execution_backend_mode=execution_backend_mode,
        graph_gateway=graph_gateway,
        meta_temporal_graph_route=meta_temporal_graph_route,
        workspace_root=workspace_root,
        stream_requested=stream_requested,
        stream_event_sink=stream_event_sink,
        economy_settlement_adapter=economy_settlement_adapter,
        invocation_context=invocation_context,
        ontology_authority_package_names=ontology_authority_package_names,
        ontology_authority_source_kind=ontology_authority_source_kind,
        ontology_authority_root=ontology_authority_root,
        service_api_dependency_routes=service_api_dependency_routes,
        service_view_provider_routes=service_view_provider_routes,
        environment_commit_receipt_source=environment_commit_receipt_source,
        ontology_replica_query=ontology_replica_query,
        ontology_replica_orm_session=ontology_replica_orm_session,
    )


def _load_dependency_api_invocation_manifest(
    *,
    runtime_package_dir: Path,
) -> LoadedApiInvocationManifest:
    invocation_manifest_path = (
        runtime_package_dir / "api.invocation_manifest.json"
    ).resolve()
    if not invocation_manifest_path.exists():
        raise RuntimeError(
            "Activated Service package dependency is missing the pinned API invocation manifest: "
            f"{invocation_manifest_path}"
        )
    return load_api_invocation_manifest_file(invocation_manifest_path)


def _build_api_invocation_ir_from_loaded_manifest(
    *,
    index: MetaGraphRuntimeIndex,
    invocation_manifest: LoadedApiInvocationManifest,
    runtime_package_dir: Path,
    endpoint_ref: str,
    discriminant: str,
    request_payload: Mapping[str, object],
) -> ApiInvocationIR:
    binding = _resolve_invocation_manifest_endpoint_binding(
        invocation_manifest=invocation_manifest,
        endpoint_ref=endpoint_ref,
        discriminant=discriminant,
    )
    endpoint = binding.endpoint
    stream = endpoint.stream
    runtime_request_class_config_id = _resolve_runtime_request_class_config_id(
        index=index,
        class_ref=endpoint.request.class_ref,
    )
    compiled_request_class_config_id = _resolve_compiled_api_request_class_config_id(
        runtime_package_dir=runtime_package_dir,
        endpoint_ref=endpoint.endpoint_ref,
        class_ref=endpoint.request.class_ref,
    )
    if (
        runtime_request_class_config_id is not None
        and compiled_request_class_config_id is not None
        and runtime_request_class_config_id != compiled_request_class_config_id
    ):
        raise RuntimeError(
            "Service API ingress request class ref resolved to conflicting ClassConfig ids "
            "between runtime index and pinned API compile plan: "
            f"endpoint_ref={endpoint.endpoint_ref!r} "
            f"class_ref={endpoint.request.class_ref!r} "
            f"runtime_class_config_id={runtime_request_class_config_id} "
            f"compiled_class_config_id={compiled_request_class_config_id}"
        )
    return ApiInvocationIR(
        api_name=binding.api.name,
        capability_name=binding.capability.name,
        endpoint_name=endpoint.name,
        endpoint_ref=endpoint.endpoint_ref,
        discriminant=endpoint.discriminant,
        source_path=endpoint.source_path,
        request_payload=dict(request_payload),
        request_class_ref=endpoint.request.class_ref,
        request_class_config_id=(
            runtime_request_class_config_id or compiled_request_class_config_id
        ),
        request_source_path=endpoint.request.source_path,
        response_class_ref=(
            endpoint.response.class_ref if endpoint.response is not None else None
        ),
        response_source_path=(
            endpoint.response.source_path if endpoint.response is not None else None
        ),
        stream=(
            ResolvedApiInvocationStream(
                stream_mode=stream.stream_mode,
                source_path=stream.source_path,
                events=tuple(
                    ResolvedApiInvocationStreamEvent(
                        kind=event.kind,
                        class_ref=event.class_ref,
                        source_path=event.source_path,
                        description=event.description,
                    )
                    for event in stream.events
                ),
                description=stream.description,
            )
            if stream is not None
            else None
        ),
        fulfillment_bindings=tuple(
            ResolvedApiInvocationFulfillmentBinding(
                name=binding_item.name,
                graph_target=binding_item.graph_target,
                graph_capability_function_name=binding_item.graph_capability_function_name,
                source_path=binding_item.source_path,
            )
            for binding_item in endpoint.fulfillment_bindings
        ),
        description=endpoint.description,
    )


def _resolve_invocation_manifest_endpoint_binding(
    *,
    invocation_manifest: LoadedApiInvocationManifest,
    endpoint_ref: str,
    discriminant: str,
) -> ApiInvocationEndpointBinding:
    if endpoint_ref.strip():
        return invocation_manifest.index.require_endpoint_by_ref(endpoint_ref)
    if discriminant.strip():
        return invocation_manifest.index.require_endpoint_by_discriminant(discriminant)
    raise RuntimeError(
        "Service API ingress requires endpoint_ref or discriminant to resolve the "
        "pinned API invocation manifest endpoint."
    )


def _resolve_runtime_request_class_config_id(
    *,
    index: MetaGraphRuntimeIndex,
    class_ref: str,
) -> UUID | None:
    normalized = class_ref.strip()
    if not normalized:
        return None

    exact_matches = sorted(
        {
            class_config.id
            for class_config in index.class_configs_by_id.values()
            if class_config.id is not None
            and (class_config.class_fqn or "").strip() == normalized
        },
        key=str,
    )
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise RuntimeError(
            "API ingress request class ref resolved to multiple exact runtime ClassConfig ids: "
            f"class_ref={normalized!r} matches={[str(item) for item in exact_matches]}"
        )

    tail = ".".join(normalized.split(".")[-2:])
    if not tail:
        return None
    suffix = f".{tail}"
    suffix_matches = sorted(
        {
            class_config.id
            for class_config in index.class_configs_by_id.values()
            if class_config.id is not None
            and (class_config.class_fqn or "").strip().endswith(suffix)
        },
        key=str,
    )
    if len(suffix_matches) == 1:
        return suffix_matches[0]
    if len(suffix_matches) > 1:
        raise RuntimeError(
            "API ingress request class ref resolved ambiguously by runtime ClassConfig suffix: "
            f"class_ref={normalized!r} suffix={suffix!r} matches={[str(item) for item in suffix_matches]}"
        )
    return None


def _resolve_compiled_api_request_class_config_id(
    *,
    runtime_package_dir: Path,
    endpoint_ref: str,
    class_ref: str,
) -> UUID | None:
    """Resolve generated DTO request ids from the pinned API compile plan.

    Read-model dispatch does not materialize an ApiCall receipt, so generated
    API DTO classes might not exist in the hosted runtime index. The API
    runtime package already pins the dependency ClassConfig ids in its compile
    plan; ServiceHost can use that package-local truth without reaching into
    API provider internals.
    """

    normalized_endpoint_ref = endpoint_ref.strip()
    normalized_class_ref = class_ref.strip()
    if not normalized_endpoint_ref or not normalized_class_ref:
        return None
    compile_plan_path = runtime_package_dir / "api.compile_plan.json"
    if not compile_plan_path.is_file():
        return None

    plan = decode_api_compile_plan_payload(
        payload=_load_json_mapping(compile_plan_path)
    )
    matches: list[UUID] = []
    endpoint_seen = False
    for api in plan.api_ownership:
        api_name = api.name.strip()
        for capability in api.capabilities:
            capability_name = capability.name.strip()
            for endpoint in capability.endpoints:
                candidate_endpoint_ref = ".".join(
                    (
                        api_name,
                        capability_name,
                        endpoint.name.strip(),
                    )
                )
                if candidate_endpoint_ref != normalized_endpoint_ref:
                    continue
                endpoint_seen = True
                request_config = endpoint.request_config
                compiled_class_ref = request_config.class_ref.strip()
                if compiled_class_ref != normalized_class_ref:
                    raise RuntimeError(
                        "Pinned API compile plan request class ref mismatches invocation manifest: "
                        f"endpoint_ref={normalized_endpoint_ref!r} "
                        f"manifest_class_ref={normalized_class_ref!r} "
                        f"compile_plan_class_ref={compiled_class_ref!r}"
                    )
                if request_config.class_config_id is not None:
                    matches.append(request_config.class_config_id)

    unique_matches = tuple(dict.fromkeys(matches))
    if len(unique_matches) == 1:
        return unique_matches[0]
    if len(unique_matches) > 1:
        raise RuntimeError(
            "Pinned API compile plan contains multiple request ClassConfig ids "
            f"for endpoint_ref={normalized_endpoint_ref!r}: "
            f"{[str(item) for item in unique_matches]}"
        )
    if endpoint_seen:
        return None
    return None


async def load_committed_service_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    error_context: str,
    commit_store_root: Path | None = None,
) -> object:
    return await _hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context=error_context,
        commit_store_root=commit_store_root,
    )


def _resolve_api_service_protocol_dependencies(
    *,
    repo_root: Path,
    compile_result: ServiceCompileResult,
    dependency_payloads: Sequence[Mapping[str, object]] | None = None,
    dependency_workspace_roots: Sequence[str | Path] = (),
) -> tuple[ServicePackageDependencyBinding, ...]:
    activation_plan = compile_result.activation_plan
    if activation_plan is None:
        return ()

    resolved_dependency_payloads = (
        tuple(dependency_payloads)
        if dependency_payloads is not None
        else load_committed_service_activation_dependency_payloads(
            toml_paths=(compile_result.snapshot.spec_path,),
        )
    )
    protocol_pins = tuple(
        (
            str(payload.get("package_name") or "").strip(),
            str(payload.get("service_protocol_plan_hash_sha256") or "").strip() or None,
        )
        for payload in resolved_dependency_payloads
        if str(payload.get("kind") or "").strip() == "api_service_protocol"
    )
    dependencies: list[ServicePackageDependencyBinding] = []
    for package_name, expected_hash_sha256 in protocol_pins:
        if not package_name:
            raise RuntimeError(
                "Service activation protocol dependency requires package_name."
            )
        runtime_package_dir = _resolve_api_service_protocol_runtime_package_dir(
            repo_root=repo_root,
            package_name=package_name,
            dependency_workspace_roots=dependency_workspace_roots,
        )
        service_protocol_plan_path = (
            runtime_package_dir / "api.service_protocol_plan.json"
        ).resolve()
        if not service_protocol_plan_path.exists():
            raise RuntimeError(
                "Service activation requires a compiled API dispatch service protocol artifact at "
                f"{service_protocol_plan_path}."
            )
        actual_hash_sha256 = _hash_json_artifact(service_protocol_plan_path)
        if expected_hash_sha256 is None:
            raise RuntimeError(
                "Service activation requires a committed protocol digest for "
                f"api_service_protocol dependency {package_name!r}."
            )
        if actual_hash_sha256 != expected_hash_sha256:
            raise RuntimeError(
                "Service activation API dispatch pin mismatch: "
                + f"package_name={package_name!r} "
                + f"expected={expected_hash_sha256} actual={actual_hash_sha256}"
            )
        dependencies.append(
            ServicePackageDependencyBinding(
                package_name=package_name,
                runtime_package_dir=runtime_package_dir,
                service_protocol_plan_path=service_protocol_plan_path,
                service_protocol_plan_hash_sha256=actual_hash_sha256,
                endpoint_refs=_load_service_protocol_plan_endpoint_refs(
                    service_protocol_plan_path
                ),
            )
        )
    return tuple(sorted(dependencies, key=lambda item: item.package_name.casefold()))


def _resolve_api_service_protocol_runtime_package_dir(
    *,
    repo_root: Path,
    package_name: str,
    dependency_workspace_roots: Sequence[str | Path] = (),
) -> Path:
    roots = tuple(
        dict.fromkeys(
            (
                *api_service_protocol_dependency_roots(repo_root),
                *(
                    Path(raw_root).expanduser().resolve()
                    for raw_root in dependency_workspace_roots
                ),
            )
        )
    )
    for root in roots:
        runtime_package_dir = (
            root / ".aware" / "api" / "runtime" / package_name
        ).resolve()
        if runtime_package_dir.exists():
            return runtime_package_dir
    return (repo_root / ".aware" / "api" / "runtime" / package_name).resolve()


def _dependency_import_roots(
    *,
    dependencies: tuple[ServicePackageDependencyBinding, ...],
    runtime_python_roots: tuple[Path, ...] = (),
) -> tuple[Path, ...]:
    roots: list[Path] = list(runtime_python_roots)
    for dependency in dependencies:
        resolved_roots = resolve_api_service_protocol_package_roots(
            runtime_package_dir=dependency.runtime_package_dir,
        )
        roots.append(resolved_roots.public_package_root)
        roots.append(resolved_roots.service_protocol_package_root)
    deduped: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = root.as_posix()
        if key in seen:
            continue
        deduped.append(root)
        seen.add(key)
    return tuple(deduped)


def _resolve_service_binding_implementation_package(
    *,
    compile_result: ServiceCompileResult,
) -> AwareServiceTomlImplementationPackageSpec:
    implementation_packages = [
        package
        for package in compile_result.snapshot.spec.implementation.packages
        if package.language == AwareServiceImplementationLanguage.python
        and package.role == AwareServiceImplementationRole.service_bindings
    ]
    if len(implementation_packages) != 1:
        raise RuntimeError(
            "Service activation requires exactly one python service_bindings "
            "implementation package declaration: "
            f"package_name={compile_result.snapshot.spec.service.package_name!r} "
            f"count={len(implementation_packages)}"
        )
    implementation_package = implementation_packages[0]
    package_root = (
        compile_result.snapshot.package_root / implementation_package.package_root
    ).resolve()
    if not package_root.is_dir():
        raise NotADirectoryError(
            "Service implementation package_root does not exist: "
            f"package_name={implementation_package.package_name!r} package_root={package_root}"
        )
    manifest_path = (package_root / implementation_package.manifest_path).resolve()
    if not manifest_path.is_file():
        raise FileNotFoundError(
            "Service implementation package manifest_path does not exist: "
            f"package_name={implementation_package.package_name!r} manifest_path={manifest_path}"
        )
    return implementation_package


def _load_service_bindings(
    *,
    package_root: Path,
    import_root: str,
    entrypoint: str | None,
    dependency_import_roots: tuple[Path, ...],
) -> Mapping[str, object]:
    with _scoped_sys_path((package_root, *dependency_import_roots)):
        if entrypoint is not None and entrypoint.strip():
            module_name, function_name = _parse_entrypoint(entrypoint)
        else:
            module_name = f"{import_root}.service_bindings"
            function_name = "build_service_bindings"
        module = cast(
            _BindingModuleProtocol,
            cast(object, import_module(module_name)),
        )
        build_service_bindings = getattr(module, function_name, None)
        if not callable(build_service_bindings):
            raise RuntimeError(
                "Service implementation package must expose a callable service binding entrypoint: "
                + f"{module_name}:{function_name}"
            )
        bindings_obj = cast(object, build_service_bindings())
    if not isinstance(bindings_obj, Mapping):
        raise RuntimeError(
            "Service implementation package build_service_bindings() must return Mapping[str, object]."
        )
    return {
        str(key): value
        for key, value in cast(Mapping[object, object], bindings_obj).items()
    }


def _parse_entrypoint(entrypoint: str) -> tuple[str, str]:
    module_name, separator, function_name = entrypoint.strip().partition(":")
    if not separator or not module_name.strip() or not function_name.strip():
        raise RuntimeError(
            "Service implementation entrypoint must use 'module:function' format: "
            f"{entrypoint!r}"
        )
    return module_name.strip(), function_name.strip()


def _build_service_endpoint_ref_map(
    *,
    compile_result: ServiceCompileResult,
) -> Mapping[str, tuple[str, ...]]:
    compile_plan = compile_result.compile_plan
    if compile_plan is None:
        raise RuntimeError("Service compile result is missing compile_plan.")
    out: dict[str, tuple[str, ...]] = {}
    for service_config in compile_plan.service_configs:
        endpoint_refs = tuple(
            endpoint.endpoint_ref
            for operation in service_config.service_operation_configs
            for endpoint in operation.api_endpoints
        )
        out[service_config.name] = tuple(sorted(set(endpoint_refs)))
    return out


def _validate_service_bindings(
    *,
    service_bindings: Mapping[str, object],
    expected_service_names: tuple[str, ...],
) -> None:
    expected = set(expected_service_names)
    actual = {str(name).strip() for name in service_bindings}
    missing = sorted(expected.difference(actual))
    extra = sorted(actual.difference(expected))
    if missing or extra:
        raise RuntimeError(
            "Service implementation package binding keys do not match compiled Service names: "
            + f"missing={missing} extra={extra}"
        )


def _build_endpoint_dependency_map(
    *,
    dependencies: tuple[ServicePackageDependencyBinding, ...],
) -> Mapping[str, ServicePackageDependencyBinding]:
    out: dict[str, ServicePackageDependencyBinding] = {}
    for dependency in dependencies:
        for endpoint_ref in dependency.endpoint_refs:
            existing = out.get(endpoint_ref)
            if existing is not None and existing != dependency:
                raise RuntimeError(
                    "Multiple API dispatch dependencies expose conflicting endpoint bindings for "
                    + f"{endpoint_ref!r}."
                )
            out[endpoint_ref] = dependency
    return out


def _validate_bound_service_endpoint_refs(
    *,
    service_endpoint_refs: Mapping[str, tuple[str, ...]],
    endpoint_dependencies: Mapping[str, ServicePackageDependencyBinding],
) -> None:
    missing: list[str] = []
    for endpoint_refs in service_endpoint_refs.values():
        for endpoint_ref in endpoint_refs:
            if endpoint_ref not in endpoint_dependencies:
                missing.append(endpoint_ref)
    if missing:
        raise RuntimeError(
            "Service implementation package references endpoint bindings that are not available from pinned "
            f"API dispatch dependencies: {sorted(set(missing))}"
        )


def _build_service_stream_endpoint_ref_map(
    *,
    service_endpoint_refs: Mapping[str, tuple[str, ...]],
    endpoint_dependencies: Mapping[str, ServicePackageDependencyBinding],
) -> Mapping[str, tuple[str, ...]]:
    loaded_packages: dict[Path, LoadedApiServiceProtocolPackage] = {}
    out: dict[str, tuple[str, ...]] = {}
    for service_name, endpoint_refs in service_endpoint_refs.items():
        stream_endpoint_refs: list[str] = []
        for endpoint_ref in endpoint_refs:
            dependency = endpoint_dependencies.get(endpoint_ref)
            if dependency is None:
                continue
            loaded_package = loaded_packages.get(dependency.runtime_package_dir)
            if loaded_package is None:
                loaded_package = load_api_service_protocol_package(
                    runtime_package_dir=dependency.runtime_package_dir
                )
                loaded_packages[dependency.runtime_package_dir] = loaded_package
            endpoint_binding = loaded_package.endpoint_bindings.get(endpoint_ref)
            if endpoint_binding is None:
                continue
            if endpoint_binding.stream_event_type_refs:
                stream_endpoint_refs.append(endpoint_ref)
        out[service_name] = tuple(sorted(set(stream_endpoint_refs)))
    return out


def _resolve_service_endpoint_dependency(
    *,
    prepared: PreparedServicePackageBinding,
    service_name: str,
    endpoint_ref: str,
) -> ServicePackageDependencyBinding:
    service_handler = prepared.service_bindings.get(service_name)
    if service_handler is None:
        raise RuntimeError(
            f"Prepared Service package is missing bound handler for {service_name!r}."
        )
    endpoint_refs = prepared.service_endpoint_refs.get(service_name)
    if endpoint_refs is None or endpoint_ref not in endpoint_refs:
        raise RuntimeError(
            f"Service {service_name!r} is not bound to endpoint_ref {endpoint_ref!r}."
        )
    dependency = prepared.endpoint_dependencies.get(endpoint_ref)
    if dependency is None:
        raise RuntimeError(
            f"Prepared Service package is missing API dispatch endpoint binding for {endpoint_ref!r}."
        )
    return dependency


def _rebuild_activated_service_api_dispatch_plan(
    *,
    activated: ActivatedServicePackageBinding,
    index: MetaGraphRuntimeIndex,
    service_name: str,
    dispatch_request: ServiceApiDispatchRequest,
) -> ApiServiceDispatchPlan:
    prepared = activated.prepared
    dependency = _resolve_service_endpoint_dependency(
        prepared=prepared,
        service_name=service_name,
        endpoint_ref=dispatch_request.envelope.endpoint_ref,
    )
    loaded_package = load_api_service_protocol_package(
        runtime_package_dir=dependency.runtime_package_dir
    )
    endpoint_binding = loaded_package.endpoint_bindings.get(
        dispatch_request.envelope.endpoint_ref
    )
    if endpoint_binding is None:
        raise RuntimeError(
            "Activated Service package could not resolve a compiled API dispatch binding for "
            f"endpoint_ref={dispatch_request.envelope.endpoint_ref!r}."
        )
    request_model_cls = _resolve_generated_request_model_class(
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
    )
    request_payload = dict(dispatch_request.request_payload)
    request_object = request_model_cls.model_validate(request_payload)
    _raise_if_api_request_model_dropped_payload_fields(
        endpoint_ref=dispatch_request.envelope.endpoint_ref,
        request_type_ref=endpoint_binding.request_type_ref,
        request_model_cls=request_model_cls,
        request_payload=request_payload,
        request_object=request_object,
    )
    envelope = _build_resolved_api_invocation_envelope(
        dispatch_request=dispatch_request,
    )
    fulfillment_bindings = _rebuild_dispatch_fulfillment_bindings(
        endpoint_ref=dispatch_request.envelope.endpoint_ref,
        loaded_package=loaded_package,
        endpoint_binding=endpoint_binding,
        dispatch_request=dispatch_request,
    )
    fulfillment_bindings = resolve_api_service_dispatch_instance_target_plans(
        index=index,
        runtime_package_dir=dependency.runtime_package_dir,
        endpoint_ref=dispatch_request.envelope.endpoint_ref,
        request_class_ref=dispatch_request.envelope.request_class_ref,
        request_class_config_id=dispatch_request.envelope.request_class_config_id,
        request_object=request_object,
        fulfillment_bindings=fulfillment_bindings,
    )
    return ApiServiceDispatchPlan(
        envelope=envelope,
        public_package_import_root=loaded_package.public_package_import_root,
        service_protocol_import_root=loaded_package.service_protocol_import_root,
        endpoint_ref=dispatch_request.envelope.endpoint_ref,
        api_name=dispatch_request.envelope.api_name,
        capability_name=dispatch_request.envelope.capability_name,
        endpoint_name=dispatch_request.envelope.endpoint_name,
        request_type_ref=endpoint_binding.request_type_ref,
        response_type_ref=endpoint_binding.response_type_ref,
        stream_event_type_refs=endpoint_binding.stream_event_type_refs,
        execution_protocol_ref=endpoint_binding.execution_protocol_ref,
        build_execution=endpoint_binding.build_execution,
        stream_invoke=endpoint_binding.stream_invoke,
        fulfillment_bindings=fulfillment_bindings,
        request_object=request_object,
        invoke=endpoint_binding.invoke,
    )


def _build_resolved_api_invocation_envelope(
    *,
    dispatch_request: ServiceApiDispatchRequest,
) -> ResolvedApiInvocationEnvelope:
    envelope = dispatch_request.envelope
    return ResolvedApiInvocationEnvelope(
        api_call_id=envelope.api_call_id,
        api_capability_endpoint_id=envelope.api_capability_endpoint_id,
        call_key=envelope.call_key,
        request_hash=envelope.request_hash,
        commit_id=envelope.commit_id,
        head_commit_id=envelope.head_commit_id,
        branch_id=envelope.branch_id,
        projection_hash=envelope.projection_hash,
        api_name=envelope.api_name,
        capability_name=envelope.capability_name,
        endpoint_name=envelope.endpoint_name,
        endpoint_ref=envelope.endpoint_ref,
        discriminant=envelope.discriminant,
        source_path=envelope.source_path,
        request_model_id=envelope.request_model_id,
        request_class_config_id=envelope.request_class_config_id,
        request_class_ref=envelope.request_class_ref,
        request_source_path=envelope.request_source_path,
        response_class_ref=envelope.response_class_ref,
        response_source_path=envelope.response_source_path,
        stream=None,
        fulfillment_bindings=tuple(
            ResolvedApiInvocationFulfillmentBinding(
                name=binding.name,
                graph_target=binding.graph_target,
                graph_capability_function_name=binding.graph_capability_function_name,
                source_path=binding.source_path,
                api_capability_endpoint_function_id=binding.api_capability_endpoint_function_id,
            )
            for binding in dispatch_request.fulfillment_bindings
        ),
        description=None,
    )


def _raise_if_api_request_model_dropped_payload_fields(
    *,
    endpoint_ref: str,
    request_type_ref: str,
    request_model_cls: type[BaseModel],
    request_payload: Mapping[str, object],
    request_object: BaseModel,
) -> None:
    model_payload = request_object.model_dump(mode="json", exclude_none=False)
    if not isinstance(model_payload, Mapping):
        raise RuntimeError(
            "Service API dispatch request model did not produce a JSON-object "
            "payload after validation: "
            f"endpoint_ref={endpoint_ref!r} "
            f"request_type_ref={request_type_ref!r} "
            f"request_model={request_model_cls.__module__}."
            f"{request_model_cls.__name__}"
        )

    dropped_fields = tuple(
        sorted(str(key) for key in request_payload.keys() if key not in model_payload)
    )
    changed_fields = tuple(
        sorted(
            str(key)
            for key, value in request_payload.items()
            if key in model_payload
            and _canonical_api_payload_value(model_payload[key])
            != _canonical_api_payload_value(value)
        )
    )
    if not dropped_fields and not changed_fields:
        return

    changed_field_values = {
        key: {
            "caller": _canonical_api_payload_value(request_payload[key]),
            "model": _canonical_api_payload_value(model_payload[key]),
        }
        for key in changed_fields
    }
    raise RuntimeError(
        "Service API dispatch request model changed caller payload fields. "
        "The pinned API runtime package is stale or incompatible with the "
        "current API DTO contract; materialize the API package through "
        "Workspace before serving this endpoint. "
        f"endpoint_ref={endpoint_ref!r} "
        f"request_type_ref={request_type_ref!r} "
        f"request_model={request_model_cls.__module__}."
        f"{request_model_cls.__name__} "
        f"dropped_fields={dropped_fields!r} "
        f"changed_fields={changed_fields!r} "
        f"changed_field_values={changed_field_values!r}"
    )


def _canonical_api_payload_value(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )


def _build_read_model_api_invocation_envelope(
    *,
    ir: ApiInvocationIR,
    api_call_lane: MaterializationLaneContext,
) -> ResolvedApiInvocationEnvelope:
    request_class_config_id = ir.request_class_config_id
    if request_class_config_id is None:
        raise RuntimeError(
            "Service API read-model dispatch requires request_class_config_id "
            f"for endpoint_ref={ir.endpoint_ref!r}."
        )
    api_id = stable_api_id(name=ir.api_name)
    capability_id = stable_api_capability_id(
        api_id=api_id,
        name=ir.capability_name,
    )
    api_capability_endpoint_id = (
        ir.api_capability_endpoint_id
        or stable_api_capability_endpoint_id(
            api_capability_id=capability_id,
            name=ir.endpoint_name,
        )
    )
    request_hash = _hash_api_read_model_request_payload(ir.request_payload)
    call_key = uuid4()
    api_call_id = stable_api_call_id(
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=call_key,
    )
    synthetic_commit_id = uuid5(
        NAMESPACE_URL,
        f"aware:api_read_model_dispatch_commit:{api_call_id}",
    )
    request_model_id = uuid5(
        NAMESPACE_URL,
        f"aware:api_read_model_request_model:{request_hash}",
    )
    return ResolvedApiInvocationEnvelope(
        api_call_id=api_call_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        call_key=call_key,
        request_hash=request_hash,
        commit_id=synthetic_commit_id,
        head_commit_id=synthetic_commit_id,
        branch_id=api_call_lane.branch_id,
        projection_hash=api_call_lane.projection_hash,
        api_name=ir.api_name,
        capability_name=ir.capability_name,
        endpoint_name=ir.endpoint_name,
        endpoint_ref=ir.endpoint_ref,
        discriminant=ir.discriminant,
        source_path=ir.source_path,
        request_model_id=request_model_id,
        request_class_config_id=request_class_config_id,
        request_class_ref=ir.request_class_ref,
        request_source_path=ir.request_source_path,
        response_class_ref=ir.response_class_ref,
        response_source_path=ir.response_source_path,
        stream=ir.stream,
        fulfillment_bindings=ir.fulfillment_bindings,
        description=ir.description,
    )


def _hash_api_read_model_request_payload(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return "sha256:" + sha256(canonical).hexdigest()


def _rebuild_dispatch_fulfillment_bindings(
    *,
    endpoint_ref: str,
    loaded_package: LoadedApiServiceProtocolPackage,
    endpoint_binding: ApiServiceProtocolEndpointBinding,
    dispatch_request: ServiceApiDispatchRequest,
) -> tuple[ApiServiceDispatchFulfillmentBinding, ...]:
    package_bindings_by_key = {
        (
            binding.name.strip(),
            binding.graph_target.strip(),
            binding.graph_capability_function_name.strip(),
        ): binding
        for binding in endpoint_binding.fulfillment_bindings
    }
    rebuilt: list[ApiServiceDispatchFulfillmentBinding] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for binding in dispatch_request.fulfillment_bindings:
        key = (
            binding.name.strip(),
            binding.graph_target.strip(),
            binding.graph_capability_function_name.strip(),
        )
        if key in seen_keys:
            raise RuntimeError(
                "Service API dispatch request contains duplicate fulfillment bindings for "
                f"endpoint_ref={endpoint_ref!r}: {key!r}"
            )
        seen_keys.add(key)
        package_binding = package_bindings_by_key.get(key)
        if package_binding is None:
            raise RuntimeError(
                "Service API dispatch request could not be reconciled with the pinned API endpoint "
                f"binding: endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        planned_key = (
            endpoint_ref.strip(),
            binding.name.strip(),
            binding.graph_target.strip(),
            binding.graph_capability_function_name.strip(),
        )
        planned_binding = loaded_package.runtime_fulfillment_bindings.get(planned_key)
        if planned_binding is None:
            raise RuntimeError(
                "Service API dispatch request is missing compiled runtime callable metadata for "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        if (
            binding.graph_function_python_ref
            != package_binding.graph_function_python_ref
        ):
            raise RuntimeError(
                "Service API dispatch request graph_function_python_ref mismatches the pinned API package: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        if (
            binding.graph_function_runtime_target
            != planned_binding.graph_function_runtime_target
        ):
            raise RuntimeError(
                "Service API dispatch request graph_function_runtime_target mismatches the pinned API plan: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        if binding.method_name != package_binding.method_name:
            raise RuntimeError(
                "Service API dispatch request method_name mismatches the pinned API package: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        if binding.request_type_ref != package_binding.request_type_ref:
            raise RuntimeError(
                "Service API dispatch request request_type_ref mismatches the pinned API package: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        if binding.response_type_ref != package_binding.response_type_ref:
            raise RuntimeError(
                "Service API dispatch request response_type_ref mismatches the pinned API package: "
                f"endpoint_ref={endpoint_ref!r} fulfillment_name={binding.name!r}"
            )
        rebuilt.append(
            ApiServiceDispatchFulfillmentBinding(
                name=binding.name,
                graph_target=binding.graph_target,
                graph_capability_function_name=binding.graph_capability_function_name,
                graph_function_python_ref=binding.graph_function_python_ref,
                graph_function_runtime_target=binding.graph_function_runtime_target,
                call_target_kind=planned_binding.call_target_kind,
                exact_output_field_name=planned_binding.exact_output_field_name,
                method_name=binding.method_name,
                request_type_ref=binding.request_type_ref,
                response_type_ref=binding.response_type_ref,
                source_path=binding.source_path,
                api_capability_endpoint_function_id=binding.api_capability_endpoint_function_id,
            )
        )
    return tuple(rebuilt)


def _resolve_generated_request_model_class(
    *,
    loaded_package: LoadedApiServiceProtocolPackage,
    endpoint_binding: ApiServiceProtocolEndpointBinding,
) -> type[BaseModel]:
    class_name = _class_name_from_ref(endpoint_binding.request_type_ref)
    with _scoped_sys_path(
        (
            loaded_package.public_package_root,
            loaded_package.service_protocol_package_root,
        )
    ):
        for module_name in _request_model_module_candidates(
            loaded_package=loaded_package,
            request_type_ref=endpoint_binding.request_type_ref,
            class_name=class_name,
        ):
            try:
                module = import_module(module_name)
            except ModuleNotFoundError:
                continue
            model_cls = getattr(module, class_name, None)
            if isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
                return model_cls
    module_name = to_snake_case(class_name)
    raise RuntimeError(
        "Service API dispatch could not resolve the generated request model class from the pinned "
        "API package or service protocol DTO refs: "
        f"request_type_ref={endpoint_binding.request_type_ref!r} "
        f"legacy_module={loaded_package.public_package_import_root}.models.{module_name} "
        f"class_name={class_name}"
    )


def _request_model_module_candidates(
    *,
    loaded_package: LoadedApiServiceProtocolPackage,
    request_type_ref: str,
    class_name: str,
) -> tuple[str, ...]:
    normalized_ref = str(request_type_ref or "").strip()
    candidates: list[str] = []
    if "." in normalized_ref:
        candidates.append(normalized_ref.rsplit(".", 1)[0])
    candidates.append(f"{loaded_package.service_protocol_import_root}.protocols")
    candidates.append(
        f"{loaded_package.public_package_import_root}.models.{to_snake_case(class_name)}"
    )
    return tuple(dict.fromkeys(candidate for candidate in candidates if candidate))


def _class_name_from_ref(type_ref: str) -> str:
    class_name = str(type_ref).strip().rsplit(".", 1)[-1].strip()
    if not class_name:
        raise RuntimeError(
            f"Service API dispatch requires a dotted request type ref, got {type_ref!r}."
        )
    return class_name


async def _materialize_service_instances(
    *,
    runtime,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_lane: MaterializationLaneContext,
    service_names: tuple[str, ...],
) -> Mapping[str, UUID]:
    service_ids_by_name: dict[str, UUID] = {}
    for service_name in service_names:
        service_config_id = stable_service_config_id(name=service_name)
        _ = runtime
        result = await commit_service_instance_snapshot(
            index=index,
            actor_id=actor_id,
            branch_id=service_lane.branch_id,
            projection_hash=service_lane.projection_hash,
            service_config_id=service_config_id,
            name=service_name,
            description=None,
        )
        service_id = result.service.id
        if service_id is None:
            raise RuntimeError(
                "Service activation instance snapshot produced Service without id."
            )
        service_ids_by_name[service_name] = service_id
    return service_ids_by_name


async def _materialize_service_subscriptions(
    *,
    prepared: PreparedServicePackageBinding,
    runtime,
    index: MetaGraphRuntimeIndex,
    actor_id: UUID | None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    service_ids_by_name: Mapping[str, UUID],
    service_config_lanes_by_name: Mapping[str, MaterializationLaneContext] | None,
    service_lanes_by_name: Mapping[str, MaterializationLaneContext] | None,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
    allow_materialization: bool = True,
    commit_store_root: Path | None = None,
) -> Mapping[str, tuple[ServiceLaneSubscriptionBinding, ...]]:
    compile_plan = prepared.compile_result.compile_plan
    if compile_plan is None:
        raise RuntimeError("Service compile result is missing compile_plan.")

    api_projection_hash = find_meta_graph_projection_hash_by_name(
        index=index,
        projection_name="Api",
    )
    api_reference_context = await _hydrate_committed_api_reference_contexts(
        index=index,
        lanes=_resolve_api_reference_lanes_for_service_compile_plan(
            service_config_lane=service_config_lane,
            api_projection_hash=api_projection_hash,
            compile_plan=compile_plan,
            api_reference_branch_ids_by_api_name=api_reference_branch_ids_by_api_name,
        ),
        commit_store=_explicit_commit_store(commit_store_root=commit_store_root),
    )
    subscriptions_by_name: dict[str, tuple[ServiceLaneSubscriptionBinding, ...]] = {}
    for service_config in compile_plan.service_configs:
        current_service_lane = (
            service_lanes_by_name.get(service_config.name)
            if service_lanes_by_name is not None
            else None
        ) or service_lane
        object_instance_graph_branch_id = stable_object_instance_graph_branch_id(
            branch_id=current_service_lane.branch_id,
        )
        service_id = service_ids_by_name.get(service_config.name)
        if service_id is None:
            raise RuntimeError(
                "Service subscription activation requires a committed Service instance for "
                f"{service_config.name!r}."
            )
        service_config_id = stable_service_config_id(name=service_config.name)
        committed_service_lane_head_commit_id = await _committed_lane_head_commit_id(
            lane=current_service_lane,
            commit_store_root=commit_store_root,
        )
        subscriptions: list[ServiceLaneSubscriptionBinding] = []
        for api_plan in service_config.apis:
            api_id = _resolve_committed_api_id_for_subscription(
                api_ref=api_plan.api_ref,
                api_reference_context=api_reference_context,
            )
            service_config_api_id = stable_service_config_api_id(
                service_config_id=service_config_id,
                api_id=api_id,
            )
            for projection_plan in api_plan.api_projections:
                api_graph_projection_id = _resolve_committed_api_graph_projection_id(
                    api_context=api_reference_context,
                    api_ref=api_plan.api_ref,
                    projection_ref=projection_plan.projection_ref,
                )
                api_graph_projection = _require_committed_api_graph_projection(
                    api_reference_context=api_reference_context,
                    api_graph_projection_id=api_graph_projection_id,
                    api_ref=api_plan.api_ref,
                    projection_ref=projection_plan.projection_ref,
                )
                projection = index.opg_by_id.get(
                    api_graph_projection.object_projection_graph_id
                )
                if projection is None:
                    raise RuntimeError(
                        "Service subscription activation could not resolve the runtime projection "
                        f"for api_ref={api_plan.api_ref!r} projection_ref={projection_plan.projection_ref!r}."
                    )
                service_config_api_projection_id = (
                    stable_service_config_api_projection_id(
                        service_config_api_id=service_config_api_id,
                        api_graph_projection_id=api_graph_projection_id,
                    )
                )
                if committed_service_lane_head_commit_id is not None:
                    service_branch_id = stable_service_branch_id(
                        service_id=service_id,
                        service_config_api_projection_id=service_config_api_projection_id,
                        object_instance_graph_branch_id=object_instance_graph_branch_id,
                    )
                    logger.info(
                        "Service activation reused committed Service lane subscription binding "
                        "without lane hydration service_name=%s api_ref=%s projection_ref=%s "
                        "branch_id=%s projection_hash=%s head_commit_id=%s",
                        service_config.name,
                        api_plan.api_ref,
                        projection_plan.projection_ref,
                        current_service_lane.branch_id,
                        current_service_lane.projection_hash,
                        committed_service_lane_head_commit_id,
                    )
                    subscriptions.append(
                        ServiceLaneSubscriptionBinding(
                            service_branch_id=service_branch_id,
                            service_config_api_projection_id=service_config_api_projection_id,
                            api_graph_projection_id=api_graph_projection_id,
                            object_instance_graph_branch_id=object_instance_graph_branch_id,
                            branch_id=current_service_lane.branch_id,
                            projection_hash=projection.projection_hash,
                        )
                    )
                    continue
                if not allow_materialization:
                    raise ServiceActivationRequiresMaterialization(
                        "Service activation requires ServiceBranch subscription "
                        "materialization before it can use read-only committed "
                        f"package-ref activation: service={service_config.name!r} "
                        f"api_ref={api_plan.api_ref!r} "
                        f"projection_ref={projection_plan.projection_ref!r} "
                        f"branch_id={current_service_lane.branch_id} "
                        f"projection_hash={current_service_lane.projection_hash}."
                    )
                materialized_branch = await materialize_service_branch(
                    runtime=runtime,
                    index=index,
                    actor_id=actor_id,
                    target_lane=current_service_lane,
                    service_id=service_id,
                    service_config_api_projection_id=service_config_api_projection_id,
                    object_instance_graph_branch_id=object_instance_graph_branch_id,
                    description=None,
                )
                subscriptions.append(
                    ServiceLaneSubscriptionBinding(
                        service_branch_id=materialized_branch.binding.service_branch_id,
                        service_config_api_projection_id=service_config_api_projection_id,
                        api_graph_projection_id=api_graph_projection_id,
                        object_instance_graph_branch_id=object_instance_graph_branch_id,
                        branch_id=current_service_lane.branch_id,
                        projection_hash=projection.projection_hash,
                    )
                )
        subscriptions_by_name[service_config.name] = tuple(subscriptions)

    return subscriptions_by_name


def _resolve_api_reference_lanes_for_service_compile_plan(
    *,
    service_config_lane: MaterializationLaneContext,
    api_projection_hash: str,
    compile_plan,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
) -> tuple[MaterializationLaneContext, ...]:
    api_refs = tuple(
        sorted(
            {
                api_plan.api_ref.strip()
                for service_config in compile_plan.service_configs
                for api_plan in service_config.apis
                if api_plan.api_ref.strip()
            }
        )
    )
    if not api_refs:
        return (
            MaterializationLaneContext(
                branch_id=service_config_lane.branch_id,
                projection_hash=api_projection_hash,
            ),
        )

    normalized_branch_ids = (
        {
            **{
                name.strip(): branch_id
                for name, branch_id in api_reference_branch_ids_by_api_name.items()
                if name.strip()
            },
            **{
                name.casefold().strip(): branch_id
                for name, branch_id in api_reference_branch_ids_by_api_name.items()
                if name.strip()
            },
        }
        if api_reference_branch_ids_by_api_name is not None
        else {}
    )
    return tuple(
        MaterializationLaneContext(
            branch_id=(
                normalized_branch_ids.get(api_ref)
                or normalized_branch_ids.get(api_ref.casefold())
                or service_config_lane.branch_id
            ),
            projection_hash=api_projection_hash,
        )
        for api_ref in api_refs
    )


def _normalize_api_reference_branch_ids_by_api_name(
    values: Mapping[str, UUID] | None,
) -> Mapping[str, UUID]:
    if values is None:
        return {}
    normalized: dict[str, UUID] = {}
    for name, branch_id in values.items():
        token = name.strip()
        if not token:
            continue
        normalized[token] = branch_id
        normalized[token.casefold()] = branch_id
    return normalized


def _resolve_api_source_lane_for_endpoint_ref(
    *,
    default_lane: MaterializationLaneContext,
    endpoint_ref: str,
    api_reference_branch_ids_by_api_name: Mapping[str, UUID] | None,
) -> MaterializationLaneContext:
    api_name = _api_ref_from_endpoint_ref(endpoint_ref=endpoint_ref)
    branch_ids = _normalize_api_reference_branch_ids_by_api_name(
        api_reference_branch_ids_by_api_name
    )
    branch_id = branch_ids.get(api_name) or branch_ids.get(api_name.casefold())
    if branch_id is None or branch_id == default_lane.branch_id:
        return default_lane
    return MaterializationLaneContext(
        branch_id=branch_id,
        projection_hash=default_lane.projection_hash,
    )


def _api_ref_from_endpoint_ref(*, endpoint_ref: str) -> str:
    token = endpoint_ref.strip()
    if not token:
        raise RuntimeError("Service API dispatch requires non-empty endpoint_ref.")
    api_name, separator, _ = token.partition(".")
    if not separator or not api_name.strip():
        raise RuntimeError(
            "Service API dispatch endpoint_ref must begin with an API name: "
            f"{endpoint_ref!r}."
        )
    return api_name.strip()


def _resolve_committed_api_id_for_subscription(
    *,
    api_ref: str,
    api_reference_context: _CommittedAPIReferenceContext,
) -> UUID:
    key = (api_ref or "").casefold().strip()
    api = api_reference_context.apis_by_name.get(key)
    if api is None or api.id is None:
        raise RuntimeError(
            "Service subscription activation could not resolve a committed Api for "
            f"api_ref={api_ref!r}."
        )
    return api.id


def _require_committed_api_graph_projection(
    *,
    api_reference_context: _CommittedAPIReferenceContext,
    api_graph_projection_id: UUID,
    api_ref: str,
    projection_ref: str,
) -> ApiGraphProjection:
    for projection in api_reference_context.graph_projections_by_key.values():
        if projection.id == api_graph_projection_id:
            return projection
    raise RuntimeError(
        "Service subscription activation could not hydrate the committed ApiGraphProjection "
        f"for api_ref={api_ref!r} projection_ref={projection_ref!r}."
    )


async def _load_committed_service_ids(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    service_names: tuple[str, ...],
    commit_store_root: Path | None = None,
) -> Mapping[str, UUID]:
    from aware_service_ontology.service.service import Service

    session = await _hydrate_committed_lane_session(
        index=index,
        lane=lane,
        error_context="Service activation",
        commit_store_root=commit_store_root,
    )
    service_ids_by_name: dict[str, UUID] = {}
    expected_names = {name.casefold(): name for name in service_names}
    for obj in session.imap_all_objects():
        if not isinstance(obj, Service) or obj.id is None:
            continue
        key = (obj.name or "").casefold().strip()
        canonical = expected_names.get(key)
        if canonical is None:
            continue
        service_ids_by_name[canonical] = obj.id
    missing = sorted(set(service_names).difference(service_ids_by_name))
    if missing:
        raise RuntimeError(
            "Service activation expected committed Service instances for "
            f"{missing}, but they were not found on the service lane."
        )
    return service_ids_by_name


async def _hydrate_committed_lane_session(
    *,
    index: MetaGraphRuntimeIndex,
    lane: MaterializationLaneContext,
    error_context: str,
    commit_store_root: Path | None = None,
):
    from aware_meta.graph.instance.commit.materialization_cache import (
        CachedLaneMaterializer,
    )
    from uuid import UUID as _UUID

    commit_store = _commit_store(commit_store_root=commit_store_root)
    target_head = await commit_store.head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )
    if target_head is None or not target_head.get("commit_id"):
        raise RuntimeError(f"{error_context} requires a committed lane head.")

    opg = index.opg_by_hash.get(lane.projection_hash)
    if opg is None:
        raise RuntimeError(
            f"{error_context} could not resolve projection hash {lane.projection_hash!r}."
        )

    target_oig, _ = await CachedLaneMaterializer(commits=commit_store).get(
        branch_id=lane.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=_UUID(str(target_head["commit_id"])),
        oig_id=(
            _UUID(str(target_head["object_instance_graph_id"]))
            if target_head.get("object_instance_graph_id")
            else None
        ),
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )

    return reify_oig_session(
        index=index,
        opg=opg,
        oig=target_oig,
        branch_id=lane.branch_id,
    )


@contextmanager
def _scoped_sys_path(paths: tuple[Path, ...]):
    inserted: list[str] = []
    try:
        for path in paths:
            token = path.resolve().as_posix()
            if token in sys.path:
                continue
            sys.path.insert(0, token)
            inserted.append(token)
        yield
    finally:
        for token in inserted:
            try:
                sys.path.remove(token)
            except ValueError:
                pass


def _load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object at {path}")
    return {
        str(key): value for key, value in cast(dict[object, object], payload).items()
    }


def _hash_json_artifact(path: Path) -> str:
    payload = _load_json_mapping(path)
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


def _load_service_protocol_plan_endpoint_refs(path: Path) -> tuple[str, ...]:
    payload = _load_json_mapping(path)
    apis = payload.get("apis")
    if not isinstance(apis, list):
        raise RuntimeError(
            f"Invalid API service protocol plan at {path}: missing apis[]"
        )
    endpoint_refs: list[str] = []
    for api in apis:
        if not isinstance(api, dict):
            continue
        capabilities = api.get("capabilities")
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            if not isinstance(capability, dict):
                continue
            endpoints = capability.get("endpoints")
            if not isinstance(endpoints, list):
                continue
            for endpoint in endpoints:
                if not isinstance(endpoint, dict):
                    continue
                endpoint_ref = endpoint.get("endpoint_ref")
                if isinstance(endpoint_ref, str) and endpoint_ref.strip():
                    endpoint_refs.append(endpoint_ref.strip())
    return tuple(sorted(set(endpoint_refs)))


__all__ = [
    "ActivatedServicePackageBinding",
    "PreparedServicePackageBinding",
    "ProjectionSessionResolver",
    "ServiceActivationRequiresMaterialization",
    "ServicePackageDependencyBinding",
    "activate_committed_service_package_binding",
    "activate_service_package_binding",
    "build_activated_service_api_dispatch_plan_from_ingress",
    "build_activated_service_api_read_model_dispatch_plan_from_ingress",
    "build_prepared_service_config_session_for_api_dispatch",
    "build_service_api_dispatch_request",
    "build_service_operation_request_for_api_dispatch",
    "execute_activated_service_api_dispatch_request",
    "load_committed_service_lane_session",
    "execute_activated_service_api_dispatch",
    "invoke_prepared_service_endpoint_binding",
    "prepare_committed_service_package_binding",
    "prepare_service_package_binding",
    "resolve_activated_service_api_source_lane",
    "resolve_prepared_service_api_receipt_policy",
]
