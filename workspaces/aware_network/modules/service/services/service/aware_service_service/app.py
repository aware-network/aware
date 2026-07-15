from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version as package_version
import json
import os
from pathlib import Path
import sys
from time import perf_counter
from typing import Any, cast
from uuid import UUID

from aware_comms import DuplexIpcEndpoint
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_environment_sdk import EnvironmentGeneratedApiClient
from aware_meta_service.local_sdk import (
    LaneHeadReceiptRelay,
    MaterializationLaneContext,
    MetaSdkLaneStore,
    build_local_meta_sdk_lane_store,
    build_local_meta_sdk_service_graph_gateway,
)
from aware_orm.session.session import Session
from aware_service_runtime import ServiceRuntimeHost, UnsupportedServiceError
from aware_service_runtime import runtime_resolution as service_runtime_resolution
from aware_service_runtime.api_ingress.execution import (
    ExecutedServiceApiDispatch,
    ServiceApiStreamEventSink,
)
from aware_service_runtime.api_ingress.execution_context import (
    ServiceApiExecutionBackend,
    ServiceApiExecutionBackendMode,
)
from aware_service_runtime.contracts import (
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    BootstrapServiceContractAccessContextHostControlRequest,
    BootstrapServiceContractAccessContextHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    EnsureServiceContractAccessContextHostControlRequest,
    EnsureServiceContractAccessContextHostControlResponse,
    RequestStatus,
    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_PACKAGE_IDS_BY_NAME_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
    SERVICE_HOST_CAPABILITY_API_DISPATCH,
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceApiDispatchRequest,
    ServiceGraphGateway,
    ServiceHostApiIngressRequest,
    ServiceHostBootstrapStatus,
    ServiceHostCapabilityAdvertisement,
    ServiceHostCapabilityState,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
    ServiceHostReadiness,
    ServiceHostTransport,
    MetaTemporalGraphRoute,
    ServiceLaneSubscriptionBinding,
    ServiceOperationRequest,
    ServiceOperationResponse,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_from_payload,
)
from aware_service_runtime.view_provider_routes import (
    ServiceViewProviderRouteDescriptor,
    build_service_view_provider_routes,
)
from aware_service_runtime.duplex import ServiceDuplexStreamEvent
from aware_service_runtime.implementation_package import (
    ProjectionSessionResolver,
    ServiceActivationRequiresMaterialization,
    load_committed_service_lane_session,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.runtime_resolution import (
    ServiceProtocolRuntimeResolution,
    resolve_service_protocol_runtime_manifest,
)
from aware_service_runtime.package_ref_resolution import (
    ResolvedServiceRuntimePackageRef,
)
from aware_types import JsonObject
from aware_utils.logging import logger

from aware_service_service.activation.runtime_context import (
    ActivatedImplementationRuntimeContext as _ActivatedImplementationRuntimeContext,
    HostedImplementationLanes as _HostedImplementationLanes,
    MetaSdkServiceHostRuntime as _MetaSdkServiceHostRuntime,
    MissingServiceHostRuntimeArtifactResolver,
    ServiceProtocolRuntimeArtifactResolver,
    WorkspaceRevisionRuntimeContextResolver,
    build_implementation_package_lanes as _build_activation_implementation_package_lanes,
    resolve_hosted_runtime_manifest_context,
)
from aware_service_service.activation.registry import (
    ActivatedImplementationEndpointBinding as _ActivatedImplementationEndpointBinding,
    ActivatedServiceImplementationPackage,
    activated_implementation_endpoint_refs_by_service as _activated_implementation_endpoint_refs_by_service,
    activated_implementation_lane_subscriptions as _activated_implementation_lane_subscriptions,
    activated_implementation_service_names as _activated_implementation_service_names,
    activated_implementation_service_package_ids_by_name as _activated_implementation_service_package_ids_by_name,
    activated_implementation_stream_endpoint_refs_by_service as _activated_implementation_stream_endpoint_refs_by_service,
    activated_implementation_view_protocol_bindings as _activated_implementation_view_protocol_bindings,
    ontology_package_requirements_for_activated_package as _ontology_package_requirements_for_activated_package,
    raise_if_generic_request_targets_implementation_service as _raise_if_generic_request_targets_implementation_service,
    resolve_activated_implementation_endpoint as _resolve_activated_implementation_endpoint,
    resolve_activated_implementation_package as _resolve_activated_implementation_package,
    resolve_activated_implementation_package_by_service_id as _resolve_activated_implementation_package_by_service_id,
    service_package_name_for_activated_binding as _service_package_name_for_activated_binding,
)
from aware_service_service.activation.package_refs import (
    has_committed_package_ref_coordinates as _has_committed_package_ref_coordinates,
    implementation_package_toml_paths as _implementation_package_toml_paths,
    requires_remote_environment_sdk as _requires_remote_environment_sdk,
    resolve_implementation_package_refs as _resolve_implementation_package_refs,
    service_runtime_package_ref_from_config_ref as _service_runtime_package_ref_from_config_ref,
)
from aware_service_service.activation.projection_read_model import (
    SERVICE_HOST_REQUIRED_PROJECTION_NAMES as _SERVICE_HOST_REQUIRED_PROJECTION_NAMES,
    explicit_service_host_root as _explicit_service_host_root,
    read_service_host_source_activation_meta_api_activation_read_model as _read_service_host_source_activation_meta_api_activation_read_model,
    read_service_host_source_activation_meta_read_model as _read_service_host_source_activation_meta_read_model,
    service_host_api_workspace_root as _service_host_api_workspace_root,
    service_host_bootstrap_actor_id as _service_host_bootstrap_actor_id,
    service_host_ontology_authority_root as _service_host_ontology_authority_root,
    service_host_projection_runtime_requirements as _service_host_projection_runtime_requirements,
    service_host_required_projection_names as _service_host_required_projection_names,
)
from aware_service_service.activation.host_activation import (
    activate_service_host_implementation_packages as _activate_service_host_implementation_packages,
)
from aware_service_service.activation.lifecycle import (
    start_activated_service_lifecycle_handlers as _start_activated_service_lifecycle_handlers,
    stop_started_service_lifecycle_handlers as _stop_started_service_lifecycle_handlers,
)
from aware_service_service.economy.settlement import (
    build_economy_api_client_settlement_adapter,
)
from aware_service_service.economy.contract_control import (
    build_service_contract_lane as _build_service_contract_lane,
    build_service_subscription_lane as _build_service_subscription_lane,
    load_contract_access_context_bootstrap_session as _load_contract_access_context_bootstrap_session_impl,
    merge_service_sessions as _merge_service_sessions,
    require_service_session as _require_service_session,
    resolve_activated_service_lane as _resolve_activated_service_lane,
)
from aware_service_service.economy.host_control import (
    handle_contract_access_context_bootstrap_request as _handle_contract_access_context_bootstrap_request,
    handle_contract_access_context_ensure_request as _handle_contract_access_context_ensure_request,
)
from aware_service_service.config import (
    ServiceHostAppConfig,
)
from aware_service_service.api.reference_materialization import (
    load_service_protocol_api_reference_materialization_inputs as _load_service_protocol_api_reference_materialization_inputs,
    materialize_service_protocol_api_reference_lanes as _materialize_service_protocol_api_reference_lanes,
)
from aware_service_service.api.dispatch import (
    execute_service_api_dispatch as _execute_service_api_dispatch,
)
from aware_service_service.api.ingress import (
    handle_service_host_api_ingress_request as _handle_service_host_api_ingress_request,
    handle_service_operation_api_dispatch_request as _handle_service_operation_api_dispatch_request,
)
from aware_service_service.api.duplex_streams import (
    StreamEventEmitter as _StreamEventEmitter,
    active_duplex_stream_session_id as _active_duplex_stream_session_id,
    close_duplex_service_stream as _close_duplex_service_stream,
    emit_duplex_stream_event as _emit_duplex_stream_event,
    run_duplex_api_ingress_request as _run_duplex_api_ingress_request,
    run_duplex_service_notification as _run_duplex_service_notification,
    run_duplex_service_request as _run_duplex_service_request,
    send_duplex_service_response as _send_duplex_service_response,
)
from aware_service_service.experience.references import (
    ExperienceReferenceBranchResolution as _ExperienceReferenceBranchResolution,
    has_committed_experience_package_ref_coordinates as _has_committed_experience_package_ref_coordinates,
    resolve_experience_reference_branch_resolution as _resolve_experience_reference_branch_resolution,
)
from aware_service_service.environment.commit_receipts import (
    ServiceHostEnvironmentCommitReceiptClient,
    build_service_host_environment_commit_receipt_source,
    dispatch_service_host_lane_commit_receipt,
)
from aware_service_service.environment.gateway import EnvironmentSdkGraphGateway
from aware_service_service.ontology.runtime_installation import (
    ensure_service_host_db_schema_installed as _ensure_service_host_db_schema_installed,
    install_service_host_ontology_runtime_artifacts as _install_service_host_ontology_runtime_artifacts,
)

load_service_protocol_api_compile_plan_payloads = (
    service_runtime_resolution.load_service_protocol_api_compile_plan_payloads
)
from aware_service_service.ontology.replica.projector import (
    EnvironmentApiServiceOntologyCommitSource,
    LocalFsServiceOntologyCommitSource,
    ServiceOntologyCommitSource,
)
from aware_service_service.ontology.replica.query import (
    ServiceOntologyReplicaQuery,
)
from aware_service_service.ontology.replica.orm import (
    build_service_ontology_replica_orm_session,
)
from aware_service_service.ontology.replica.orm_activation import (
    activate_required_service_ontology_replica_orm_packages,
)
from aware_service_service.ontology.replica.gateway import (
    graph_gateway_for_activated_package as _graph_gateway_for_activated_package,
)
from aware_service_service.ontology.replica.lifecycle import (
    start_service_ontology_replica_worker_if_needed as _start_service_ontology_replica_worker_if_needed,
    stop_service_ontology_replica_worker as _stop_service_ontology_replica_worker,
)
from aware_service_service.ontology.replica.worker import (
    ServiceOntologyReplicaWorker,
)


_SERVICE_HOST_ID = "aware_service_service"
_REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH = (
    Path(".aware") / "workspace" / "revision-filesystem.manifest.json"
)


class RuntimeHarness:
    """Retired runtime harness bridge kept only as a fail-closed sentinel."""

    def __new__(cls, *args: object, **kwargs: object) -> object:
        _ = (cls, args, kwargs)
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost RuntimeHarness bridge is retired; activate through "
            "the Meta SDK ServiceHost runtime/read-model rail."
        )


def activate_runtime_imports(*, plan: object) -> None:
    raw_roots = getattr(plan, "roots", ())
    existing = set(sys.path)
    ordered_locations: list[str] = []
    for root in raw_roots:
        resolved = Path(root).expanduser().resolve()
        if not resolved.exists():
            continue
        ordered_locations.append(resolved.as_posix())
    for location in reversed(ordered_locations):
        if location in existing:
            continue
        sys.path.insert(0, location)
        existing.add(location)


def bind_runtime_lane(*args: object, **kwargs: object) -> object:
    _ = (args, kwargs)
    raise ServiceActivationRequiresMaterialization(
        "ServiceHost runtime lane binding bridge is retired; bind lanes through "
        "the supplied Meta-native runtime.bind(...)."
    )


async def ensure_materialization_runtime_context(**kwargs: object) -> object:
    _ = kwargs
    raise ServiceActivationRequiresMaterialization(
        "ServiceHost materialization runtime context bridge is retired; consume "
        "the WorkspaceRevision Meta read model or explicit Meta SDK runtime "
        "context."
    )


@dataclass(frozen=True, slots=True)
class _RevisionSemanticRuntimeCatalog:
    catalog: Mapping[str, object]
    manifest_path: Path
    workspace_revision_id: UUID
    artifact_path: Path
    sha256: str
    byte_length: int


@contextmanager
def _service_host_materialization_runtime_persistence_context() -> Iterator[None]:
    previous_backend = os.environ.get("AWARE_PERSISTENCE_BACKEND")
    os.environ["AWARE_PERSISTENCE_BACKEND"] = "fs"
    try:
        yield
    finally:
        if previous_backend is None:
            os.environ.pop("AWARE_PERSISTENCE_BACKEND", None)
        else:
            os.environ["AWARE_PERSISTENCE_BACKEND"] = previous_backend


def _service_activation_projection_session_resolver() -> (
    ProjectionSessionResolver | None
):
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return None

    def _resolve(lane: MaterializationLaneContext) -> Session:
        return Session(branch_id=lane.branch_id, backend_name="db")

    return _resolve


class _MissingMetaTemporalGraphRoute(MetaTemporalGraphRoute):
    def __init__(self, *, error: str) -> None:
        self._error = error

    async def invoke_temporal_function(self, **kwargs: object) -> object:
        _ = kwargs
        raise RuntimeError(self._error)


class ServiceHostApp(ServiceHostTransport):
    """Thin standalone Service host over the shared runtime core."""

    def __init__(
        self,
        *,
        resolver: Any | None = None,
        config: ServiceHostAppConfig | None = None,
        environment_api_client: EnvironmentGeneratedApiClient | None = None,
        ontology_replica_state_db_path: Path | None = None,
        ontology_replica_projection_db_path: Path | None = None,
        ontology_replica_commit_source: ServiceOntologyCommitSource | None = None,
    ) -> None:
        self._config = config or ServiceHostAppConfig.from_env()
        self._ontology_replica_state_db_path_override = ontology_replica_state_db_path
        self._ontology_replica_projection_db_path_override = (
            ontology_replica_projection_db_path
        )
        self._ontology_replica_commit_source_override = ontology_replica_commit_source
        self._environment_api_client = environment_api_client
        if self._config.runtime_manifest_path is not None:
            raise RuntimeError(
                "ServiceHost explicit runtime_manifest_path is retired. Use "
                "Service protocol ontology runtime artifact sources or a "
                "generated Environment API route instead."
            )
        self._resolved_implementation_package_refs = (
            _resolve_implementation_package_refs(
                config=self._config,
            )
        )
        self._implementation_package_toml_paths = _implementation_package_toml_paths(
            config=self._config,
            resolved_package_refs=self._resolved_implementation_package_refs,
        )
        self._uses_committed_package_refs = any(
            _has_committed_package_ref_coordinates(
                _service_runtime_package_ref_from_config_ref(package_ref)
            )
            for package_ref in self._config.implementation_packages.package_refs
        )
        uses_remote_environment_gateway = (
            resolver is None
            and environment_api_client is not None
            and _requires_remote_environment_sdk(self._config)
        )
        self._uses_remote_environment_gateway = uses_remote_environment_gateway
        revision_runtime_catalog: _RevisionSemanticRuntimeCatalog | None = None
        if self._uses_committed_package_refs and not self._config.environment.enabled:
            try:
                revision_runtime_catalog = (
                    _load_verified_revision_semantic_runtime_catalog(
                        config=self._config
                    )
                )
            except ServiceActivationRequiresMaterialization:
                revision_runtime_catalog = None
        supports_local_committed_revision_activation = (
            revision_runtime_catalog is not None
        )
        if (
            resolver is None
            and not uses_remote_environment_gateway
            and _requires_remote_environment_sdk(self._config)
            and not supports_local_committed_revision_activation
        ):
            if not self._config.environment.enabled:
                raise RuntimeError(
                    "ServiceHost artifact deployment requires a remote "
                    "Environment SDK endpoint. Local Environment runtime "
                    "manifest fallback is retired for committed service "
                    "package refs."
                )
            raise RuntimeError(
                "ServiceHost artifact deployment resolved a remote "
                "Environment SDK endpoint, but the ServiceGraphGateway adapter over "
                "aware_environment_sdk requires a generated Environment API client "
                "or endpoint transport. Local Environment runtime manifest "
                "fallback is retired."
            )
        self._service_protocol_runtime_resolution: (
            ServiceProtocolRuntimeResolution | None
        ) = None
        if resolver is not None:
            self._resolver = resolver
        elif self._implementation_package_toml_paths:
            self._service_protocol_runtime_resolution = (
                resolve_service_protocol_runtime_manifest(
                    toml_paths=self._implementation_package_toml_paths,
                    kernel_repo_root=self._config.kernel_repo_root,
                )
            )
            if self._service_protocol_runtime_resolution is not None:
                activate_runtime_imports(
                    plan=self._service_protocol_runtime_resolution.runtime_resolution.import_activation
                )
                self._resolver = ServiceProtocolRuntimeArtifactResolver(
                    self._service_protocol_runtime_resolution
                )
            else:
                self._resolver = MissingServiceHostRuntimeArtifactResolver()
        elif revision_runtime_catalog is not None:
            self._resolver = WorkspaceRevisionRuntimeContextResolver(
                manifest_path=revision_runtime_catalog.manifest_path,
                workspace_revision_id=revision_runtime_catalog.workspace_revision_id,
            )
        else:
            self._resolver = MissingServiceHostRuntimeArtifactResolver()
        if uses_remote_environment_gateway:
            if environment_api_client is None:
                raise RuntimeError(
                    "ServiceHost Environment SDK graph gateway requires a "
                    "generated Environment API client."
                )
            self._graph_gateway = EnvironmentSdkGraphGateway(
                api_client=environment_api_client
            )
            self._meta_temporal_graph_route = _MissingMetaTemporalGraphRoute(
                error=(
                    "ServiceHost remote Environment SDK mode requires an explicit "
                    "Meta temporal graph route; Environment invoke_function cannot "
                    "execute temporal overlays."
                )
            )
        else:
            self._graph_gateway = build_local_meta_sdk_service_graph_gateway()
            self._meta_temporal_graph_route = cast(
                MetaTemporalGraphRoute, self._graph_gateway
            )
        self._meta_lane_store = build_local_meta_sdk_lane_store()
        self._activated_implementation_packages: tuple[
            ActivatedServiceImplementationPackage, ...
        ] = ()
        self._activated_implementation_service_ids_by_name: dict[str, UUID] = {}
        self._activated_implementation_runtime_context: (
            _ActivatedImplementationRuntimeContext | None
        ) = None
        self._service_api_dependency_routes: tuple[
            ServiceApiDependencyRouteDescriptor, ...
        ] = ()
        self._lane_head_receipt_relay: LaneHeadReceiptRelay | None = None
        self._ontology_replica_worker: ServiceOntologyReplicaWorker | None = None
        self._started_service_lifecycle_handlers: tuple[object, ...] = ()
        self._is_prepared = False
        self._dependency_route_plan_installed = False
        self._service_lifecycles_active = False
        self._is_configured = False
        self._startup_phase_timings_s: dict[str, object] = {}
        self._implementation_activation_evidence: dict[str, object] = {}
        self._host = ServiceRuntimeHost(
            transport=self,
            providers_env_var="AWARE_SERVICE_SERVICE_PLUGIN_PROVIDERS",
            enabled_services_env_var="AWARE_SERVICE_SERVICE_ENABLED_SERVICES",
        )

    async def configure(self) -> tuple[str, ...]:
        plugin_services = await self.prepare()
        self.configure_service_api_dependency_routes(
            self._service_api_dependency_routes
        )
        await self.activate_service_lifecycles()
        return plugin_services

    async def prepare(self) -> tuple[str, ...]:
        started = perf_counter()
        timings: dict[str, object] = {}
        self._is_prepared = False
        self._dependency_route_plan_installed = False
        self._service_lifecycles_active = False
        self._is_configured = False
        stop_lifecycle_started = perf_counter()
        await self._stop_started_service_lifecycles()
        timings["stop_service_lifecycle_duration_s"] = _duration_since(
            stop_lifecycle_started
        )
        stop_replica_worker_started = perf_counter()
        await self._stop_ontology_replica_worker()
        timings["stop_ontology_replica_worker_duration_s"] = _duration_since(
            stop_replica_worker_started
        )
        stop_relay_started = perf_counter()
        self._stop_lane_head_receipt_relay()
        timings["stop_lane_head_receipt_relay_duration_s"] = _duration_since(
            stop_relay_started
        )
        refresh_local_meta_started = perf_counter()
        self._refresh_local_meta_facades()
        timings["refresh_local_meta_facades_duration_s"] = _duration_since(
            refresh_local_meta_started
        )
        provider_resolution_started = perf_counter()
        if (
            self._uses_remote_environment_gateway
            or self._uses_committed_package_refs
            or self._implementation_package_toml_paths
        ):
            provider_modules = ()
            service_surface_paths = ()
        else:
            provider_modules = await self._resolver.get_service_provider_modules(
                surface="service"
            )
            service_surface_paths = await self._resolver.get_service_surface_paths(
                surface="service"
            )
        timings["provider_surface_resolution_duration_s"] = _duration_since(
            provider_resolution_started
        )
        host_configure_started = perf_counter()
        self._host.configure(
            provider_modules=provider_modules,
            service_surface_paths=service_surface_paths,
        )
        timings["plugin_host_configure_duration_s"] = _duration_since(
            host_configure_started
        )
        activation_started = perf_counter()
        activated_implementation_services = (
            await self._activate_implementation_packages()
        )
        timings["activate_implementation_packages_duration_s"] = _duration_since(
            activation_started
        )
        overlap_started = perf_counter()
        plugin_services = self.plugin_services
        overlap = sorted(
            set(plugin_services).intersection(activated_implementation_services)
        )
        if overlap:
            raise RuntimeError(
                "Service host activation found conflicting plugin and implementation-package service names: "
                f"{overlap}"
            )
        timings["overlap_validation_duration_s"] = _duration_since(overlap_started)
        logger.info(
            "ServiceHostApp configured service surface providers=%s services=%s implementation_services=%s "
            "implementation_package_tomls=%s implementation_package_refs=%s runtime_manifest_path=%s "
            "service_protocol_runtime_manifest_path=%s roots=%s",
            sorted(provider_modules),
            list(plugin_services),
            list(activated_implementation_services),
            [path.as_posix() for path in self._implementation_package_toml_paths],
            [
                ref.semantic_package_id or ref.semantic_root_id or ref.package_name
                for ref in self._resolved_implementation_package_refs
            ],
            (
                self._config.runtime_manifest_path.as_posix()
                if self._config.runtime_manifest_path is not None
                else None
            ),
            (
                self._service_protocol_runtime_resolution.manifest_path.as_posix()
                if self._service_protocol_runtime_resolution is not None
                else None
            ),
            [path.as_posix() for path in service_surface_paths],
        )
        lane_relay_started = perf_counter()
        await self._start_lane_head_receipt_relay_if_needed()
        timings["start_lane_head_receipt_relay_duration_s"] = _duration_since(
            lane_relay_started
        )
        replica_worker_started = perf_counter()
        await self._start_ontology_replica_worker_if_needed()
        timings["start_ontology_replica_worker_duration_s"] = _duration_since(
            replica_worker_started
        )
        self._is_prepared = True
        timings["total_duration_s"] = _duration_since(started)
        self._startup_phase_timings_s = timings
        return plugin_services

    async def activate_service_lifecycles(self) -> tuple[int, bool]:
        if not self._is_prepared:
            raise RuntimeError(
                "ServiceHost lifecycle activation requires completed preparation."
            )
        if not self._dependency_route_plan_installed:
            raise RuntimeError(
                "ServiceHost lifecycle activation requires an explicit dependency "
                "route plan, including an empty plan."
            )
        if self._service_lifecycles_active:
            return len(self._started_service_lifecycle_handlers), True

        service_lifecycle_started = perf_counter()
        await self._start_activated_service_lifecycles()
        self._startup_phase_timings_s["start_service_lifecycle_duration_s"] = (
            _duration_since(service_lifecycle_started)
        )
        self._service_lifecycles_active = True
        self._is_configured = True
        return len(self._started_service_lifecycle_handlers), False

    async def start(self) -> tuple[str, ...]:
        return await self.configure()

    async def close(self) -> None:
        await self._stop_started_service_lifecycles()
        await self._stop_ontology_replica_worker()
        self._stop_lane_head_receipt_relay()
        self._is_prepared = False
        self._dependency_route_plan_installed = False
        self._service_lifecycles_active = False
        self._is_configured = False

    @property
    def plugin_services(self) -> tuple[str, ...]:
        return self._host.plugin_services

    @property
    def activated_implementation_service_names(self) -> tuple[str, ...]:
        return _activated_implementation_service_names(
            service_ids_by_name=self._activated_implementation_service_ids_by_name,
        )

    @property
    def service_protocol_runtime_resolution_evidence(self) -> dict[str, object] | None:
        resolution = self._service_protocol_runtime_resolution
        if resolution is None:
            return None
        api_dependencies = tuple(getattr(resolution, "api_dependencies", ()) or ())
        cache_metadata_path = getattr(resolution, "cache_metadata_path", None)
        return {
            "manifest_path": resolution.manifest_path.as_posix(),
            "environment_config_id": (
                str(resolution.runtime_resolution.environment_config_id)
                if resolution.runtime_resolution.environment_config_id is not None
                else None
            ),
            "runtime_ontology_artifact_manifest_paths": [
                path.as_posix()
                for path in resolution.runtime_resolution.runtime_bundle_manifest_paths
            ],
            "cache_status": getattr(resolution, "cache_status", None),
            "cache_metadata_path": (
                cache_metadata_path.as_posix()
                if cache_metadata_path is not None
                else None
            ),
            "cache_reason": getattr(resolution, "cache_reason", None),
            "api_dependencies": [
                {
                    "package_name": dependency.package_name,
                    "service_protocol_plan_hash_sha256": (
                        dependency.service_protocol_plan_hash_sha256
                    ),
                }
                for dependency in api_dependencies
            ],
        }

    @property
    def startup_phase_timings_s(self) -> dict[str, object]:
        return dict(self._startup_phase_timings_s)

    @property
    def implementation_activation_evidence(self) -> dict[str, object]:
        return dict(self._implementation_activation_evidence)

    @property
    def ontology_replica_query(self) -> ServiceOntologyReplicaQuery | None:
        worker = self._ontology_replica_worker
        if worker is None or worker.projection_store is None:
            return None
        return ServiceOntologyReplicaQuery(projection_store=worker.projection_store)

    @property
    def ontology_replica_orm_session(self) -> Session | None:
        return self._build_ontology_replica_orm_session()

    def _build_ontology_replica_orm_session(
        self,
        *,
        branch_id: UUID | None = None,
    ) -> Session | None:
        worker = self._ontology_replica_worker
        if worker is None or worker.projection_store is None:
            return None
        return build_service_ontology_replica_orm_session(
            projection_store=worker.projection_store,
            branch_id=branch_id,
        )

    @contextmanager
    def _activated_service_ontology_orm_package_path_context(
        self,
        *,
        activated_package: ActivatedServiceImplementationPackage,
    ) -> Iterator[tuple[object, ...]]:
        requirements = _ontology_package_requirements_for_activated_package(
            activated_package
        )
        if not requirements:
            yield ()
            return
        with activate_required_service_ontology_replica_orm_packages(
            repo_root=self._ontology_orm_repo_root_for_activated_package(
                activated_package=activated_package
            ),
            ontology_packages=requirements,
        ) as activation:
            yield tuple(activation.resolved_paths)

    def _ontology_orm_repo_root_for_activated_package(
        self,
        *,
        activated_package: ActivatedServiceImplementationPackage,
    ) -> Path:
        _ = activated_package
        return _explicit_service_host_root(
            config=self._config,
            purpose="ontology replica ORM package activation",
        )

    @contextmanager
    def _service_ontology_orm_package_path_context_for_toml_path(
        self,
        *,
        toml_path: Path,
    ) -> Iterator[tuple[object, ...]]:
        resolved_toml_path = toml_path.expanduser().resolve()
        spec = load_aware_service_toml_spec(toml_path=resolved_toml_path)
        requirements = tuple(spec.ontology_packages or ())
        if not requirements:
            yield ()
            return
        repo_root = _explicit_service_host_root(
            config=self._config,
            purpose="service TOML ontology package activation",
        )
        with activate_required_service_ontology_replica_orm_packages(
            repo_root=repo_root,
            ontology_packages=requirements,
        ) as activation:
            yield tuple(activation.resolved_paths)

    @property
    def service_api_dependency_routes(
        self,
    ) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
        return self._service_api_dependency_routes

    def configure_service_api_dependency_routes(
        self,
        routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    ) -> None:
        self._service_api_dependency_routes = tuple(routes)
        self._dependency_route_plan_installed = True

    @property
    def activated_implementation_endpoint_refs_by_service(
        self,
    ) -> dict[str, tuple[str, ...]]:
        return _activated_implementation_endpoint_refs_by_service(
            packages=self._activated_implementation_packages,
        )

    @property
    def activated_implementation_service_package_ids_by_name(
        self,
    ) -> dict[str, UUID]:
        return _activated_implementation_service_package_ids_by_name(
            packages=self._activated_implementation_packages,
        )

    @property
    def activated_implementation_stream_endpoint_refs_by_service(
        self,
    ) -> dict[str, tuple[str, ...]]:
        return _activated_implementation_stream_endpoint_refs_by_service(
            packages=self._activated_implementation_packages,
        )

    @property
    def activated_implementation_lane_subscriptions(
        self,
    ) -> tuple[ServiceLaneSubscriptionBinding, ...]:
        return _activated_implementation_lane_subscriptions(
            packages=self._activated_implementation_packages,
        )

    @property
    def activated_implementation_view_provider_routes(
        self,
    ) -> tuple[ServiceViewProviderRouteDescriptor, ...]:
        return build_service_view_provider_routes(
            bindings=_activated_implementation_view_protocol_bindings(
                packages=self._activated_implementation_packages,
            ),
            api_dependency_routes=self._service_api_dependency_routes,
            require_all=False,
        )

    def _build_economy_settlement_adapter(
        self,
        *,
        actor_id: UUID | None,
    ):
        economy_config = self._config.economy
        if not economy_config.enabled or economy_config.endpoint is None:
            return None
        return build_economy_api_client_settlement_adapter(
            endpoint=economy_config.endpoint,
            request_timeout_s=economy_config.request_timeout_s,
        )

    def _graph_gateway_for_activated_package(
        self,
        *,
        activated_package: ActivatedServiceImplementationPackage,
        service_name: str,
    ) -> ServiceGraphGateway:
        return _graph_gateway_for_activated_package(
            base_graph_gateway=self._graph_gateway,
            ontology_replica_worker=self._ontology_replica_worker,
            activated_package=activated_package,
            service_name=service_name,
        )

    async def execute_api_dispatch(
        self,
        *,
        service_name: str,
        dispatch_request: ServiceApiDispatchRequest,
        actor_id: UUID | None = None,
        execution_backend: ServiceApiExecutionBackend | None = None,
        execution_backend_mode: ServiceApiExecutionBackendMode | None = None,
        stream_requested: bool = False,
        stream_event_sink: ServiceApiStreamEventSink | None = None,
        invocation_context: JsonObject | dict[str, object] | None = None,
    ) -> ExecutedServiceApiDispatch:
        return await _execute_service_api_dispatch(
            service_name=service_name,
            dispatch_request=dispatch_request,
            actor_id=actor_id,
            execution_backend=execution_backend,
            execution_backend_mode=execution_backend_mode,
            stream_requested=stream_requested,
            stream_event_sink=stream_event_sink,
            invocation_context=invocation_context,
            environment_api_client=self._environment_api_client,
            resolve_activated_implementation_package=(
                self._resolve_activated_implementation_package
            ),
            resolve_dispatch_runtime_context=(
                self._resolve_implementation_dispatch_runtime_context
            ),
            build_economy_settlement_adapter=self._build_economy_settlement_adapter,
            ontology_orm_package_path_context=(
                self._activated_service_ontology_orm_package_path_context
            ),
            graph_gateway_for_activated_package=(
                self._graph_gateway_for_activated_package
            ),
            workspace_root=_service_host_api_workspace_root(config=self._config),
            ontology_authority_package_names=(
                self._config.ontology_authority.package_names
            ),
            ontology_authority_source_kind=(
                self._config.ontology_authority.source_kind
            ),
            ontology_authority_root=_service_host_ontology_authority_root(
                config=self._config
            ),
            service_api_dependency_routes=self._service_api_dependency_routes,
            service_view_provider_routes=(
                self.activated_implementation_view_provider_routes
            ),
            meta_temporal_graph_route=self._meta_temporal_graph_route,
            build_environment_commit_receipt_source=(
                build_service_host_environment_commit_receipt_source
            ),
            ontology_replica_query=self.ontology_replica_query,
            build_ontology_replica_orm_session=self._build_ontology_replica_orm_session,
            resolve_activated_service_lane=_resolve_activated_service_lane,
            service_package_name_for_activated_binding=(
                _service_package_name_for_activated_binding
            ),
        )

    async def handle_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
    ) -> ServiceOperationResponse:
        return await _handle_service_host_api_ingress_request(
            request=request,
            active_stream_session_id=_active_duplex_stream_session_id(),
            resolve_activated_implementation_endpoint=(
                self._resolve_activated_implementation_endpoint
            ),
            resolve_dispatch_runtime_context=(
                self._resolve_implementation_dispatch_runtime_context
            ),
            materialization_runtime_persistence_context=(
                _service_host_materialization_runtime_persistence_context
            ),
            build_service_contract_lane=self._build_service_contract_lane,
            build_service_subscription_lane=self._build_service_subscription_lane,
            build_economy_settlement_adapter=self._build_economy_settlement_adapter,
            ontology_orm_package_path_context=(
                self._activated_service_ontology_orm_package_path_context
            ),
            graph_gateway_for_activated_package=(
                self._graph_gateway_for_activated_package
            ),
            send_service_response=self.send_service_response,
            close_service_stream=self.close_service_stream,
            default_execution_backend_mode=self._default_api_execution_backend_mode,
            workspace_root=_service_host_api_workspace_root(config=self._config),
            ontology_authority_package_names=(
                self._config.ontology_authority.package_names
            ),
            ontology_authority_source_kind=(
                self._config.ontology_authority.source_kind
            ),
            ontology_authority_root=_service_host_ontology_authority_root(
                config=self._config
            ),
            service_api_dependency_routes=self._service_api_dependency_routes,
            service_view_provider_routes=(
                self.activated_implementation_view_provider_routes
            ),
            meta_temporal_graph_route=self._meta_temporal_graph_route,
            build_environment_commit_receipt_source=(
                build_service_host_environment_commit_receipt_source
            ),
            ontology_replica_query=self.ontology_replica_query,
            build_ontology_replica_orm_session=self._build_ontology_replica_orm_session,
            resolve_activated_service_lane=_resolve_activated_service_lane,
            service_package_name_for_activated_binding=(
                _service_package_name_for_activated_binding
            ),
            load_contract_access_context_bootstrap_session=(
                _load_contract_access_context_bootstrap_session
            ),
            merge_service_sessions=_merge_service_sessions,
            require_service_session=_require_service_session,
        )

    async def handle_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        if request.api_dispatch is not None:
            return await self._handle_api_dispatch_request(request=request)
        self._raise_if_generic_request_targets_implementation_service(
            service=request.service
        )
        return await self._host.handle_request(request=request)

    async def handle_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
    ) -> ServiceHostControlResponse:
        if isinstance(request, EnsureServiceContractAccessContextHostControlRequest):
            return await self._handle_contract_access_context_ensure_request(
                request=request
            )
        if isinstance(request, BootstrapServiceContractAccessContextHostControlRequest):
            return await self._handle_contract_access_context_bootstrap_request(
                request=request
            )
        if isinstance(request, ConfigureServiceApiDependencyRoutesHostControlRequest):
            routes = service_api_dependency_routes_from_payload(
                request.routes,
                base_dir=Path.cwd(),
            )
            self.configure_service_api_dependency_routes(routes)
            return ConfigureServiceApiDependencyRoutesHostControlResponse(
                status=RequestStatus.succeeded,
                error=None,
                route_count=len(routes),
            )
        if isinstance(request, ActivateServiceHostLifecyclesHostControlRequest):
            try:
                handler_count, already_active = await self.activate_service_lifecycles()
            except RuntimeError as exc:
                return ActivateServiceHostLifecyclesHostControlResponse(
                    status=RequestStatus.failed,
                    error=str(exc),
                )
            return ActivateServiceHostLifecyclesHostControlResponse(
                status=RequestStatus.succeeded,
                error=None,
                lifecycle_handler_count=handler_count,
                already_active=already_active,
            )
        return ServiceHostControlResponse(
            operation=request.operation,
            status=RequestStatus.failed,
            error=f"Unsupported ServiceHost control operation: {request.operation!r}",
        )

    async def _handle_contract_access_context_bootstrap_request(
        self,
        *,
        request: BootstrapServiceContractAccessContextHostControlRequest,
    ) -> BootstrapServiceContractAccessContextHostControlResponse:
        return await _handle_contract_access_context_bootstrap_request(
            request=request,
            resolve_activated_implementation_package_by_service_id=(
                self._resolve_activated_implementation_package_by_service_id
            ),
            resolve_dispatch_runtime_context=(
                self._resolve_implementation_dispatch_runtime_context
            ),
            build_implementation_package_lanes=(
                self._build_implementation_package_lanes_for_runtime_context
            ),
            build_service_subscription_lane=self._build_service_subscription_lane,
            build_service_contract_lane=self._build_service_contract_lane,
            load_committed_service_lane_session=load_committed_service_lane_session,
        )

    async def _handle_contract_access_context_ensure_request(
        self,
        *,
        request: EnsureServiceContractAccessContextHostControlRequest,
    ) -> EnsureServiceContractAccessContextHostControlResponse:
        return await _handle_contract_access_context_ensure_request(
            request=request,
            resolve_activated_implementation_package_by_service_id=(
                self._resolve_activated_implementation_package_by_service_id
            ),
            resolve_dispatch_runtime_context=(
                self._resolve_implementation_dispatch_runtime_context
            ),
            build_implementation_package_lanes=(
                self._build_implementation_package_lanes_for_runtime_context
            ),
            build_service_subscription_lane=self._build_service_subscription_lane,
            build_service_contract_lane=self._build_service_contract_lane,
            load_committed_service_lane_session=load_committed_service_lane_session,
        )

    def _build_service_subscription_lane(
        self,
        *,
        runtime_context: _ActivatedImplementationRuntimeContext,
        branch_id: UUID,
    ) -> MaterializationLaneContext:
        return _build_service_subscription_lane(
            runtime_context=runtime_context,
            branch_id=branch_id,
        )

    def _build_service_contract_lane(
        self,
        *,
        runtime_context: _ActivatedImplementationRuntimeContext,
        branch_id: UUID,
    ) -> MaterializationLaneContext:
        return _build_service_contract_lane(
            runtime_context=runtime_context,
            branch_id=branch_id,
        )

    def _build_implementation_package_lanes_for_runtime_context(
        self,
        *,
        runtime_context: _ActivatedImplementationRuntimeContext,
        runtime: Any | None,
        index,
    ) -> _HostedImplementationLanes:
        return self._build_implementation_package_lanes(
            runtime=runtime,
            index=index,
            environment_id=runtime_context.environment_config_id,
        )

    async def handle_notification(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        if request.api_dispatch is not None:
            raise UnsupportedServiceError(
                "Service host does not support notification-only API dispatch requests. "
                "Use the request/response ServiceOperation rail."
            )
        self._raise_if_generic_request_targets_implementation_service(
            service=request.service
        )
        await self._host.handle_notification(request=request)

    async def handle_lane_commit_receipt_notification(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> None:
        dispatch_service_host_lane_commit_receipt(receipt)

    async def handle_duplex_request(
        self,
        *,
        request: ServiceOperationRequest,
        emit_event: _StreamEventEmitter,
    ) -> ServiceOperationResponse:
        return await _run_duplex_service_request(
            request=request,
            emit_event=emit_event,
            handle_request=self.handle_request,
        )

    async def handle_duplex_notification(
        self,
        *,
        request: ServiceOperationRequest,
        emit_event: _StreamEventEmitter,
    ) -> None:
        await _run_duplex_service_notification(
            request=request,
            emit_event=emit_event,
            handle_notification=self.handle_notification,
        )

    async def handle_duplex_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        emit_event: _StreamEventEmitter,
    ) -> ServiceOperationResponse:
        return await _run_duplex_api_ingress_request(
            request=request,
            emit_event=emit_event,
            handle_api_ingress_request=self.handle_api_ingress_request,
        )

    async def handle_handshake(
        self,
        *,
        request: ServiceHostHandshakeRequest,
        endpoint: DuplexIpcEndpoint,
    ) -> ServiceHostHandshakeResponse:
        return ServiceHostHandshakeResponse(
            endpoint=endpoint,
            protocol_version=SERVICE_HOST_PROTOCOL_VERSION,
            host_id=_SERVICE_HOST_ID,
            host_version=_resolve_service_host_version(),
            readiness=self._build_handshake_readiness(request=request),
            capabilities=self._build_handshake_capabilities(),
        )

    async def send_service_response(
        self,
        *,
        request: ServiceOperationRequest,
        response: ServiceOperationResponse,
    ) -> None:
        await _send_duplex_service_response(
            request=request,
            response=response,
        )

    async def close_service_stream(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> None:
        _ = request
        await _close_duplex_service_stream()

    async def get_graph_gateway(self) -> ServiceGraphGateway:
        return self._graph_gateway

    async def get_meta_temporal_graph_route(self) -> MetaTemporalGraphRoute:
        return self._meta_temporal_graph_route

    async def _emit_duplex_stream_event(
        self,
        event: ServiceDuplexStreamEvent,
    ) -> None:
        await _emit_duplex_stream_event(event)

    async def _activate_implementation_packages(self) -> tuple[str, ...]:
        self._activated_implementation_packages = ()
        self._activated_implementation_service_ids_by_name = {}
        self._activated_implementation_runtime_context = None
        activation_result = await _activate_service_host_implementation_packages(
            config=self._config,
            resolver=self._resolver,
            graph_gateway=self._graph_gateway,
            implementation_package_toml_paths_value=(
                self._implementation_package_toml_paths
            ),
            resolved_implementation_package_refs=(
                self._resolved_implementation_package_refs
            ),
            uses_committed_package_refs=self._uses_committed_package_refs,
            service_api_dependency_routes=self._service_api_dependency_routes,
            resolve_hosted_runtime_manifest_context=(
                resolve_hosted_runtime_manifest_context
            ),
            install_service_host_ontology_runtime_artifacts=(
                _install_service_host_ontology_runtime_artifacts
            ),
            ensure_service_host_db_schema_installed=(
                _ensure_service_host_db_schema_installed
            ),
            service_host_projection_runtime_requirements=(
                _service_host_projection_runtime_requirements
            ),
            service_host_required_projection_names=(
                _service_host_required_projection_names
            ),
            read_source_activation_meta_runtime_read_model=(
                _read_service_host_source_activation_meta_read_model
            ),
            read_source_activation_meta_api_activation_read_model=(
                _read_service_host_source_activation_meta_api_activation_read_model
            ),
            load_verified_revision_semantic_runtime_catalog=(
                _load_verified_revision_semantic_runtime_catalog
            ),
            materialize_service_protocol_api_reference_lanes=(
                self._materialize_service_protocol_api_reference_lanes
            ),
            resolve_experience_reference_branch_resolution=(
                self._resolve_experience_reference_branch_resolution
            ),
            service_ontology_orm_package_path_context_for_toml_path=(
                lambda toml_path: (
                    self._service_ontology_orm_package_path_context_for_toml_path(
                        toml_path=toml_path
                    )
                )
            ),
            service_activation_projection_session_resolver=(
                _service_activation_projection_session_resolver
            ),
            service_host_materialization_runtime_persistence_context=(
                _service_host_materialization_runtime_persistence_context
            ),
            baseline_required_projection_names=_SERVICE_HOST_REQUIRED_PROJECTION_NAMES,
        )
        service_ids_by_name = activation_result.service_ids_by_name
        self._resolved_implementation_package_refs = (
            activation_result.resolved_implementation_package_refs
        )
        self._implementation_package_toml_paths = (
            activation_result.implementation_package_toml_paths
        )
        self._activated_implementation_packages = activation_result.activated_packages
        self._activated_implementation_service_ids_by_name = service_ids_by_name
        self._activated_implementation_runtime_context = (
            activation_result.runtime_context
        )
        self._implementation_activation_evidence = activation_result.timings
        return tuple(sorted(service_ids_by_name))

    def _refresh_local_meta_facades(self) -> None:
        self._meta_lane_store = build_local_meta_sdk_lane_store()
        if self._uses_remote_environment_gateway:
            return
        self._graph_gateway = build_local_meta_sdk_service_graph_gateway()
        self._meta_temporal_graph_route = cast(
            MetaTemporalGraphRoute,
            self._graph_gateway,
        )

    async def _resolve_experience_reference_branch_ids(
        self,
        *,
        index: Any,
        runtime: RuntimeHarness | None = None,
        environment_id: UUID | None = None,
    ) -> Mapping[str, UUID]:
        resolution = await self._resolve_experience_reference_branch_resolution(
            index=index,
            runtime=runtime,
            environment_id=environment_id,
        )
        return resolution.branch_ids_by_name

    async def _resolve_experience_reference_branch_resolution(
        self,
        *,
        index: Any,
        runtime: RuntimeHarness | None = None,
        environment_id: UUID | None = None,
    ) -> _ExperienceReferenceBranchResolution:
        local_workspace_root: Path | None = None
        if self._config.reference_packages.experience_toml_paths or any(
            package_ref.manifest_path is not None
            and not _has_committed_experience_package_ref_coordinates(package_ref)
            for package_ref in self._config.experience_package_refs
        ):
            local_workspace_root = _explicit_service_host_root(
                config=self._config,
                purpose="local Experience TOML refs",
            )
        return await _resolve_experience_reference_branch_resolution(
            config=self._config,
            index=index,
            runtime=runtime,
            environment_id=environment_id,
            actor_id=_service_host_bootstrap_actor_id(),
            environment_api_client=self._environment_api_client,
            local_workspace_root=local_workspace_root,
        )

    async def _materialize_service_protocol_api_reference_lanes(
        self,
        *,
        runtime: Any | None,
        index,
        lane: MaterializationLaneContext,
        toml_paths: tuple[Path, ...],
        committed_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...] = (),
        allow_materialization: bool = True,
    ) -> Mapping[str, UUID]:
        return await _materialize_service_protocol_api_reference_lanes(
            runtime=runtime,
            index=index,
            lane=lane,
            toml_paths=toml_paths,
            committed_package_refs=committed_package_refs,
            kernel_repo_root=self._config.kernel_repo_root,
            artifact_root=self._config.artifact_root,
            meta_lane_store=self._meta_lane_store,
            allow_materialization=allow_materialization,
        )

    def _load_service_protocol_api_reference_lane_inputs(
        self,
        *,
        toml_paths: tuple[Path, ...],
        committed_package_refs: tuple[ResolvedServiceRuntimePackageRef, ...],
        package_names: frozenset[str] | None = None,
    ):
        return _load_service_protocol_api_reference_materialization_inputs(
            toml_paths=toml_paths,
            committed_package_refs=committed_package_refs,
            kernel_repo_root=self._config.kernel_repo_root,
            artifact_root=self._config.artifact_root,
            package_names=package_names,
        )

    async def _start_lane_head_receipt_relay_if_needed(self) -> None:
        if self._lane_head_receipt_relay is not None:
            return
        if not any(
            subscriptions
            for activated in self._activated_implementation_packages
            for subscriptions in activated.binding.service_subscriptions_by_name.values()
        ):
            return
        relay = LaneHeadReceiptRelay()
        relay.start()
        self._lane_head_receipt_relay = relay

    def _stop_lane_head_receipt_relay(self) -> None:
        relay = self._lane_head_receipt_relay
        if relay is None:
            return
        relay.stop()
        self._lane_head_receipt_relay = None

    async def _start_ontology_replica_worker_if_needed(self) -> None:
        worker = await _start_service_ontology_replica_worker_if_needed(
            current_worker=self._ontology_replica_worker,
            packages=self._activated_implementation_packages,
            state_db_path=self._ontology_replica_state_db_path(),
            projection_db_path=self._ontology_replica_projection_db_path(),
            resolve_runtime_context=(
                lambda: resolve_hosted_runtime_manifest_context(self._resolver)
            ),
            commit_source_factory=(
                lambda environment_id: self._ontology_replica_commit_source(
                    environment_id=environment_id
                )
            ),
            environment_api_client=ServiceHostEnvironmentCommitReceiptClient(),
        )
        if worker is not None:
            self._ontology_replica_worker = worker

    async def _stop_ontology_replica_worker(self) -> None:
        worker = self._ontology_replica_worker
        self._ontology_replica_worker = None
        await _stop_service_ontology_replica_worker(worker=worker)

    def _ontology_replica_state_db_path(self) -> Path | None:
        return (
            self._ontology_replica_state_db_path_override
            or self._config.ontology_replica.state_db_path
        )

    def _ontology_replica_projection_db_path(self) -> Path | None:
        return (
            self._ontology_replica_projection_db_path_override
            or self._config.ontology_replica.projection_db_path
        )

    def _ontology_replica_commit_source(
        self,
        *,
        environment_id: UUID,
    ) -> ServiceOntologyCommitSource:
        if self._ontology_replica_commit_source_override is not None:
            return self._ontology_replica_commit_source_override
        if self._uses_remote_environment_gateway:
            if self._environment_api_client is None:
                raise RuntimeError(
                    "ServiceHost ontology replica projection requires a generated "
                    "Environment API client when remote Environment gateway is active."
                )
            return EnvironmentApiServiceOntologyCommitSource(
                api_client=self._environment_api_client,
                environment_id=environment_id,
            )
        return LocalFsServiceOntologyCommitSource()

    async def _start_activated_service_lifecycles(self) -> None:
        await self._stop_started_service_lifecycles()
        self._started_service_lifecycle_handlers = (
            await _start_activated_service_lifecycle_handlers(
                packages=self._activated_implementation_packages,
                environment_api_client=ServiceHostEnvironmentCommitReceiptClient(),
                package_context=lambda activated: (
                    self._activated_service_ontology_orm_package_path_context(
                        activated_package=activated
                    )
                ),
            )
        )

    async def _stop_started_service_lifecycles(self) -> None:
        handlers = self._started_service_lifecycle_handlers
        self._started_service_lifecycle_handlers = ()
        await _stop_started_service_lifecycle_handlers(handlers=handlers)

    def _build_implementation_package_lanes(
        self,
        *,
        runtime: Any | None,
        index,
        environment_id: UUID,
    ) -> _HostedImplementationLanes:
        return _build_activation_implementation_package_lanes(
            runtime=runtime,
            index=index,
            environment_id=environment_id,
        )

    async def _resolve_implementation_dispatch_runtime_context(
        self,
    ) -> _ActivatedImplementationRuntimeContext:
        runtime_context = self._activated_implementation_runtime_context
        if runtime_context is not None:
            return runtime_context
        if self._uses_committed_package_refs:
            raise RuntimeError(
                "ServiceHost committed package dispatch requires an activated "
                "WorkspaceRevision runtime context. Call configure/start before "
                "dispatching Service API requests."
            )

        runtime = await resolve_hosted_runtime_manifest_context(self._resolver)
        read_model = _read_service_host_source_activation_meta_read_model(
            config=self._config,
            runtime=runtime,
            implementation_toml_paths=self._implementation_package_toml_paths,
        )
        index = read_model.index
        harness = _MetaSdkServiceHostRuntime(
            manifest_path=runtime.manifest_path,
            graph_gateway=self._graph_gateway,
            index=index,
            environment_id=runtime.environment_config_id,
        )
        lanes = self._build_implementation_package_lanes(
            runtime=None,
            index=index,
            environment_id=runtime.environment_config_id,
        )
        return _ActivatedImplementationRuntimeContext(
            runtime=harness,
            environment_config_id=runtime.environment_config_id,
            index=index,
            lanes=lanes,
            runtime_index_source="servicehost_source_meta_runtime_read_model",
        )

    def _resolve_activated_implementation_package(
        self,
        *,
        service_name: str,
    ) -> ActivatedServiceImplementationPackage:
        return _resolve_activated_implementation_package(
            packages=self._activated_implementation_packages,
            service_name=service_name,
        )

    def _resolve_activated_implementation_package_by_service_id(
        self,
        *,
        service_id: UUID,
    ) -> tuple[ActivatedServiceImplementationPackage, str]:
        return _resolve_activated_implementation_package_by_service_id(
            packages=self._activated_implementation_packages,
            service_id=service_id,
        )

    def _resolve_activated_implementation_endpoint(
        self,
        *,
        endpoint_ref: str,
    ) -> _ActivatedImplementationEndpointBinding:
        return _resolve_activated_implementation_endpoint(
            packages=self._activated_implementation_packages,
            endpoint_ref=endpoint_ref,
        )

    def _raise_if_generic_request_targets_implementation_service(
        self, *, service: str
    ) -> None:
        _raise_if_generic_request_targets_implementation_service(
            service=service,
            service_ids_by_name=self._activated_implementation_service_ids_by_name,
        )

    async def _handle_api_dispatch_request(
        self,
        *,
        request: ServiceOperationRequest,
    ) -> ServiceOperationResponse:
        return await _handle_service_operation_api_dispatch_request(
            request=request,
            execute_api_dispatch=self.execute_api_dispatch,
            send_service_response=self.send_service_response,
            close_service_stream=self.close_service_stream,
            default_execution_backend_mode=self._default_api_execution_backend_mode(),
        )

    @staticmethod
    def _default_api_execution_backend_mode() -> ServiceApiExecutionBackendMode:
        return ServiceApiExecutionBackendMode.graph_gateway

    def _build_handshake_readiness(
        self,
        *,
        request: ServiceHostHandshakeRequest,
    ) -> ServiceHostReadiness:
        supported_protocol_versions = tuple(
            item.strip() for item in request.supported_protocol_versions if item.strip()
        )
        if (
            supported_protocol_versions
            and SERVICE_HOST_PROTOCOL_VERSION not in supported_protocol_versions
        ):
            return ServiceHostReadiness(
                is_ready=False,
                status=ServiceHostBootstrapStatus.failed,
                reason=(
                    "Unsupported service host protocol version "
                    f"(host={SERVICE_HOST_PROTOCOL_VERSION} client={supported_protocol_versions})"
                ),
                detail_payload={
                    "host_protocol_version": SERVICE_HOST_PROTOCOL_VERSION,
                    "supported_protocol_versions": list(supported_protocol_versions),
                },
            )
        if not self._is_prepared:
            return ServiceHostReadiness(
                is_ready=False,
                status=ServiceHostBootstrapStatus.starting,
                reason="Service host has not completed preparation.",
            )
        if not self._dependency_route_plan_installed:
            return ServiceHostReadiness(
                is_ready=False,
                status=ServiceHostBootstrapStatus.awaiting_dependency_routes,
                reason="Service host is awaiting its dependency route plan.",
            )
        if not self._service_lifecycles_active or not self._is_configured:
            return ServiceHostReadiness(
                is_ready=False,
                status=ServiceHostBootstrapStatus.starting,
                reason="Service host is awaiting lifecycle activation.",
            )
        return ServiceHostReadiness(
            is_ready=True,
            status=ServiceHostBootstrapStatus.ready,
        )

    def _build_handshake_capabilities(
        self,
    ) -> tuple[ServiceHostCapabilityAdvertisement, ...]:
        implementation_service_names = list(self.activated_implementation_service_names)
        implementation_endpoint_refs_by_service = {
            service_name: list(endpoint_refs)
            for service_name, endpoint_refs in self.activated_implementation_endpoint_refs_by_service.items()
        }
        implementation_stream_endpoint_refs_by_service = {
            service_name: list(endpoint_refs)
            for service_name, endpoint_refs in self.activated_implementation_stream_endpoint_refs_by_service.items()
        }
        implementation_service_ids_by_name = {
            service_name: str(service_id)
            for service_name, service_id in sorted(
                self._activated_implementation_service_ids_by_name.items(),
                key=lambda item: item[0].casefold(),
            )
        }
        implementation_service_package_ids_by_name = {
            service_name: str(service_package_id)
            for service_name, service_package_id in (
                self.activated_implementation_service_package_ids_by_name.items()
            )
        }
        view_provider_bindings = [
            {
                "service_name": binding.service_name,
                "operation_name": binding.operation_name,
                "view_ref": binding.view_ref,
                "endpoint_refs": list(binding.endpoint_refs),
                "source_path": binding.source_path,
            }
            for binding in _activated_implementation_view_protocol_bindings(
                packages=self._activated_implementation_packages,
            )
        ]
        lane_subscriptions = [
            {
                "service_branch_id": str(subscription.service_branch_id),
                "service_config_api_projection_id": str(
                    subscription.service_config_api_projection_id
                ),
                "api_graph_projection_id": str(subscription.api_graph_projection_id),
                "object_instance_graph_branch_id": str(
                    subscription.object_instance_graph_branch_id
                ),
                "branch_id": str(subscription.branch_id),
                "projection_hash": subscription.projection_hash,
            }
            for subscription in self.activated_implementation_lane_subscriptions
        ]
        implementation_dispatch_state = (
            ServiceHostCapabilityState.available
            if implementation_service_names
            else ServiceHostCapabilityState.unavailable
        )
        lane_commit_receipt_state = (
            ServiceHostCapabilityState.available
            if lane_subscriptions
            else ServiceHostCapabilityState.unavailable
        )
        view_provider_protocol_state = (
            ServiceHostCapabilityState.available
            if view_provider_bindings
            else ServiceHostCapabilityState.unavailable
        )
        return (
            ServiceHostCapabilityAdvertisement(
                capability_id="generic_service_operation_request",
                detail_payload={"plugin_services": list(self.plugin_services)},
            ),
            ServiceHostCapabilityAdvertisement(
                capability_id="duplex_stream_events",
            ),
            ServiceHostCapabilityAdvertisement(
                capability_id="graph_gateway_execution",
                detail_payload={
                    "backend": (
                        "environment_sdk"
                        if self._uses_remote_environment_gateway
                        else "meta_sdk_local"
                    )
                },
            ),
            ServiceHostCapabilityAdvertisement(
                capability_id="lane_commit_receipts",
                state=lane_commit_receipt_state,
                detail_payload={"subscriptions": lane_subscriptions},
            ),
            ServiceHostCapabilityAdvertisement(
                capability_id=SERVICE_HOST_CAPABILITY_API_DISPATCH,
                state=implementation_dispatch_state,
                detail_payload={
                    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY: implementation_service_names,
                    SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY: implementation_service_ids_by_name,
                    SERVICE_HOST_API_DISPATCH_SERVICE_PACKAGE_IDS_BY_NAME_KEY: (
                        implementation_service_package_ids_by_name
                    ),
                    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY: (
                        implementation_endpoint_refs_by_service
                    ),
                    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY: (
                        implementation_stream_endpoint_refs_by_service
                    ),
                },
            ),
            ServiceHostCapabilityAdvertisement(
                capability_id="service_view_provider_protocol",
                state=view_provider_protocol_state,
                detail_payload={"bindings": view_provider_bindings},
            ),
        )


def _load_verified_revision_semantic_runtime_catalog(
    *,
    config: ServiceHostAppConfig,
) -> _RevisionSemanticRuntimeCatalog:
    artifact_root = config.artifact_root
    if artifact_root is None:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires artifact.root "
            "or workspace_revision.materialized_workspace_root so it can verify "
            "the WorkspaceRevision semantic runtime package catalog."
        )
    resolved_artifact_root = artifact_root.expanduser().resolve()
    manifest_path = (
        (
            config.workspace_revision.manifest_path
            or (resolved_artifact_root / _REVISION_FILESYSTEM_MANIFEST_RELATIVE_PATH)
        )
        .expanduser()
        .resolve()
    )
    if not _is_relative_to(path=manifest_path, parent=resolved_artifact_root):
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires the "
            "WorkspaceRevision filesystem manifest to resolve under artifact.root: "
            f"manifest_path={manifest_path} artifact_root={resolved_artifact_root}"
        )
    if not manifest_path.is_file():
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires a "
            "WorkspaceRevision filesystem manifest with semantic runtime package catalog "
            f"evidence: {manifest_path}"
        )
    manifest_payload = _load_json_mapping(manifest_path)
    try:
        workspace_revision_id = UUID(
            str(manifest_payload.get("workspace_revision_id") or "")
        )
    except ValueError as exc:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires a valid "
            "workspace_revision_id in the WorkspaceRevision filesystem manifest."
        ) from exc
    raw_ref = manifest_payload.get("semantic_runtime_package_catalog")
    if not isinstance(raw_ref, Mapping):
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires "
            "semantic_runtime_package_catalog evidence in the WorkspaceRevision "
            "filesystem manifest."
        )
    if raw_ref.get("available") is not True:
        reason = str(raw_ref.get("reason") or "unavailable").strip()
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires an available "
            "WorkspaceRevision semantic runtime package catalog: "
            f"reason={reason!r}."
        )
    raw_relative_path = raw_ref.get("relative_path")
    if not isinstance(raw_relative_path, str) or not raw_relative_path.strip():
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost committed package-ref activation requires a relative "
            "semantic runtime package catalog artifact path."
        )
    catalog_path = (resolved_artifact_root / raw_relative_path).resolve()
    if not _is_relative_to(path=catalog_path, parent=resolved_artifact_root):
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost rejected semantic runtime package catalog outside "
            f"artifact.root: {catalog_path}"
        )
    if not catalog_path.is_file():
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost semantic runtime package catalog artifact was not found: "
            f"{catalog_path}"
        )
    content = catalog_path.read_bytes()
    expected_sha256 = str(raw_ref.get("sha256") or "").strip()
    actual_sha256 = sha256(content).hexdigest()
    if not expected_sha256 or actual_sha256 != expected_sha256:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost semantic runtime package catalog digest mismatch: "
            f"expected={expected_sha256!r} actual={actual_sha256!r}"
        )
    catalog_payload = json.loads(content.decode("utf-8"))
    if not isinstance(catalog_payload, Mapping):
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost semantic runtime package catalog artifact must decode "
            "to a JSON object."
        )
    return _RevisionSemanticRuntimeCatalog(
        catalog=catalog_payload,
        manifest_path=manifest_path,
        workspace_revision_id=workspace_revision_id,
        artifact_path=catalog_path,
        sha256=actual_sha256,
        byte_length=len(content),
    )


def _has_available_revision_semantic_runtime_catalog(
    *,
    config: ServiceHostAppConfig,
) -> bool:
    try:
        _load_verified_revision_semantic_runtime_catalog(config=config)
    except ServiceActivationRequiresMaterialization:
        return False
    return True


def _load_json_mapping(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected JSON object at {path}")
    return cast(dict[str, object], payload)


def _is_relative_to(*, path: Path, parent: Path) -> bool:
    try:
        path.expanduser().resolve().relative_to(parent.expanduser().resolve())
    except ValueError:
        return False
    return True


def _canonical_json_sha256(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        dict(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256(canonical).hexdigest()


async def _materialization_lane_head(
    lane: MaterializationLaneContext,
    *,
    meta_lane_store: MetaSdkLaneStore,
) -> Mapping[str, object] | None:
    return await meta_lane_store.head(
        branch_id=lane.branch_id,
        projection_hash=lane.projection_hash,
    )


async def _load_contract_access_context_bootstrap_session(
    *,
    index,
    service_config_session: Session | None = None,
    service_config_lane: MaterializationLaneContext,
    service_lane: MaterializationLaneContext,
    service_contract_lane: MaterializationLaneContext,
    service_subscription_lane: MaterializationLaneContext,
) -> Session:
    return await _load_contract_access_context_bootstrap_session_impl(
        index=index,
        service_config_session=service_config_session,
        service_config_lane=service_config_lane,
        service_lane=service_lane,
        service_contract_lane=service_contract_lane,
        service_subscription_lane=service_subscription_lane,
        load_session=load_committed_service_lane_session,
    )


def _dedupe_paths(paths: tuple[Path, ...]) -> tuple[Path, ...]:
    deduped: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        resolved = path.expanduser().resolve()
        token = resolved.as_posix()
        if token in seen:
            continue
        seen.add(token)
        deduped.append(resolved)
    return tuple(deduped)


def _duration_since(started: float) -> float:
    return perf_counter() - started


def _resolve_service_host_version() -> str | None:
    try:
        return package_version("aware-service-service")
    except PackageNotFoundError:
        return None
