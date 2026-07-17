from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass, field, replace
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any, Callable, Mapping, Protocol, Sequence, TYPE_CHECKING, cast
from uuid import UUID

from aware_code.types import JsonArray, JsonObject
from aware_comms import DuplexIpcEndpoint, DuplexIpcTransportKind
from aware_environment_service_dto.environment.environment import (
    LaneCommitReceiptNotification,
)
from aware_environment_service_dto.environment.environment import (
    DescribeEnvironmentConfigRequest,
    FetchCapabilitiesRequest,
    GetLaneHeadRequest,
    GetObjectInstanceGraphCommitRequest,
    InvokeFunctionRequest,
)
from aware_network_service_dto.comms.models.network_node import (
    HostedServiceAdvertisement,
    HostedServiceRuntimeStatus,
)
from aware_node_service_dto.node.host import (
    HostedRuntimeLifecycleStatus,
    HostedRuntimeRecoveryCapability,
)
from aware_network.network.node.manager import network_node_manager
from aware_network_ontology.stable_ids import stable_network_node_peer_id
from aware_api_ontology.stable_ids import stable_api_package_id
from aware_service_ontology.stable_ids import stable_service_package_id
from aware_network.node_hosted_services import (
    HostedServiceRuntimeServiceStatusSnapshot,
    HostedServiceRuntimeStatusSnapshot,
    utc_now_iso,
)
from aware_meta_service.local_sdk import (
    ProjectionReadinessModes,
    ProjectionReadinessRequirement,
    ProjectionReadinessResult,
    build_local_meta_commit_store,
    ensure_projection_readiness,
    materialize_local_meta_lane_oig,
    read_local_meta_runtime_read_model,
    start_local_meta_lane_head_receipt_relay,
)
from aware_node_service.duplex.lane_commit_receipt_bus import LaneCommitReceiptBus
from aware_service_runtime.contracts import (
    ActivateServiceHostLifecyclesHostControlRequest,
    ActivateServiceHostLifecyclesHostControlResponse,
    ConfigureServiceApiDependencyRoutesHostControlRequest,
    ConfigureServiceApiDependencyRoutesHostControlResponse,
    RequestStatus,
    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_PACKAGE_IDS_BY_NAME_KEY,
    SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
    SERVICE_HOST_CAPABILITY_API_DISPATCH,
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceHostBootstrapStatus,
    ServiceHostCapabilityState,
    ServiceHostApiIngressRequest,
    ServiceHostControlRequest,
    ServiceHostControlResponse,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
    ServiceLaneSubscriptionBinding,
    ServiceOperationRequest,
    ServiceOperationResponse,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiRouteAuthority,
    ServiceApiRouteAuthoritySelector,
    service_api_dependency_routes_to_payload,
)
from aware_service_runtime.duplex_client import (
    ServiceHostDuplexClient,
    ServiceHostDuplexRequestHandle,
)

from aware_utils.logging import logger

from aware_node_service.control_plane.actor_authority import (
    resolve_node_system_actor_id,
)
from aware_node_service.control_plane.environment_registry import environment_registry
from aware_node_service.control_plane.environment_api_network import (
    build_environment_service_api_client,
    invoke_environment_service_api_request,
)
from aware_node_service.control_plane.environment_host_support import (
    EnvironmentRouteHandler,
)
from aware_node_service.control_plane.peer_directory import (
    NetworkNodePeerEndpoint,
    build_remote_environment_route_to_peer,
    discover_remote_hosted_service_advertisements_from_peer,
    read_remote_boot_environment_descriptor_from_peer,
)
from aware_node_service.host.config import (
    NodeHostedInterfaceSupervisorConfig,
    NodeHostedServiceSupervisorConfig,
)
from aware_node_service.host.network_sdk import (
    NETWORK_SERVICE_API_PACKAGE_NAME,
    NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME,
    configure_network_sdk_client_from_service_api_routes,
)
from aware_node_service.host.network_publication import (
    reconcile_node_runtime_publication,
)
from aware_node_service.host.network_peer_bootstrap import (
    bootstrap_network_peers_from_provider_inputs,
)

_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON_ENV = (
    "AWARE_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON"
)
_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV = (
    "AWARE_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT"
)
_NODE_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV = (
    "AWARE_NODE_SERVICE_API_DEPENDENCY_ROUTES_JSON"
)
_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV = (
    "AWARE_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON"
)
_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON_ENV = (
    "AWARE_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON"
)
_NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON_ENV = (
    "AWARE_NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON"
)
_RUNTIME_BASE_ENVIRONMENT_MANIFEST_ENV = "AWARE_RUNTIME_BASE_ENVIRONMENT_MANIFEST"
_RUNTIME_BASE_ENVIRONMENT_MANIFESTS_ENV = "AWARE_RUNTIME_BASE_ENVIRONMENT_MANIFESTS"
_META_EVENT_STORE_ROOT_ENV = "AWARE_META_SERVICE_EVENT_STORE_ROOT"
_META_EVENT_STORE_ROOT_RELATIVE_PATH = Path(".aware/meta/commit-events")
_NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_INTERVAL_S_ENV = (
    "AWARE_NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_INTERVAL_S"
)
_NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_TIMEOUT_S_ENV = (
    "AWARE_NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_TIMEOUT_S"
)
_NODE_HOSTED_SERVICE_BINDING_TIMEOUT_S_ENV = (
    "AWARE_NODE_HOSTED_SERVICE_BINDING_TIMEOUT_S"
)
_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S_ENV = (
    "AWARE_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S"
)
_SERVICE_HOST_NODE_MANAGED_STARTUP_ENV = "AWARE_SERVICE_HOST_NODE_MANAGED_STARTUP"
_NODE_NETWORK_NODE_DISCOVERY_REQUEST_TIMEOUT_S_ENV = (
    "AWARE_NODE_NETWORK_NODE_DISCOVERY_REQUEST_TIMEOUT_S"
)
_ENVIRONMENT_SERVICE_PACKAGE_NAME = "aware-environment-service"
_HOSTED_SERVICE_SUBPROCESS_NODE_ONLY_ENV_NAMES = frozenset(
    (
        _NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON_ENV,
        _NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON_ENV,
        _NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_INTERVAL_S_ENV,
        _NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_TIMEOUT_S_ENV,
    )
)

if TYPE_CHECKING:
    from aware_service_runtime.package_ref_resolution import (
        ResolvedServiceRuntimePackageRef,
        ServiceRuntimePackageRef,
    )
    from aware_node_service.host.service_api_dependency_resolution import (
        NodeRemoteServiceApiProviderRuntime,
        NodeServiceApiDependencyRouteDescriptor,
        ServiceApiPackageBridgeLike,
        ServicePackageLike,
    )


class _HostedServiceProcess(Protocol):
    @property
    def pid(self) -> int: ...

    @property
    def returncode(self) -> int | None: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...

    async def wait(self) -> int: ...


class _HostedServiceDuplexClient(Protocol):
    async def send_handshake(
        self,
        *,
        request: ServiceHostHandshakeRequest | None = None,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostHandshakeResponse: ...

    async def send_request(
        self,
        *,
        request: ServiceOperationRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceOperationResponse: ...

    async def send_api_ingress_request(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceOperationResponse: ...

    async def send_host_control_request(
        self,
        *,
        request: ServiceHostControlRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostControlResponse: ...

    async def send_lane_commit_receipt_notification(
        self,
        *,
        receipt: LaneCommitReceiptNotification,
    ) -> None: ...

    def open_request_stream(
        self,
        *,
        request: ServiceOperationRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostDuplexRequestHandle: ...

    def open_api_ingress_stream(
        self,
        *,
        request: ServiceHostApiIngressRequest,
        timeout_s: float | None = 5.0,
    ) -> ServiceHostDuplexRequestHandle: ...


class _HostedServiceIpcConfig(Protocol):
    @property
    def socket_path(self) -> Path: ...


class _LoadedServiceHostBootstrapConfig(Protocol):
    @property
    def ipc(self) -> _HostedServiceIpcConfig: ...


class _HostedEnvironmentRouteConfigurer(Protocol):
    async def configure_service_api_dependency_routes(
        self,
        *,
        environment_id: UUID,
        node_id: UUID,
        routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
        timeout_s: float,
    ) -> object: ...


class CommittedHostedServiceLookupMiss(RuntimeError):
    """Committed hosted-service truth has no local advertisement for the request."""


@dataclass(frozen=True)
class _CommittedHostedServiceAdvertisementIndex:
    advertisements: tuple[HostedServiceAdvertisement, ...] = ()
    advertisement_by_service_name: Mapping[str, HostedServiceAdvertisement] = field(
        default_factory=dict
    )
    advertisement_by_endpoint_ref: Mapping[str, HostedServiceAdvertisement] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class NodeHostedServiceRuntime:
    bootstrap_config_path: Path
    socket_path: Path
    process: _HostedServiceProcess
    request_timeout_s: float
    handshake: ServiceHostHandshakeResponse
    ready_timeout_s: float = 30.0
    implementation_service_package_id: UUID | None = None
    implementation_package_names: tuple[str, ...] = ()
    routable_service_names: tuple[str, ...] = ()
    routable_endpoint_refs_by_service: Mapping[str, tuple[str, ...]] = field(
        default_factory=dict
    )
    lane_subscriptions: tuple[ServiceLaneSubscriptionBinding, ...] = ()

    def advertised_endpoint_refs_by_service(self) -> Mapping[str, tuple[str, ...]]:
        if self.routable_endpoint_refs_by_service:
            return self.routable_endpoint_refs_by_service
        return _extract_routable_endpoint_refs_by_service_from_handshake(
            handshake=self.handshake
        )

    def advertised_stream_endpoint_refs_by_service(
        self,
    ) -> Mapping[str, tuple[str, ...]]:
        return _extract_routable_stream_endpoint_refs_by_service_from_handshake(
            handshake=self.handshake
        )

    def runtime_status_snapshot(self) -> HostedServiceRuntimeStatusSnapshot:
        endpoint_refs_by_service = self.advertised_endpoint_refs_by_service()
        stream_endpoint_refs_by_service = (
            self.advertised_stream_endpoint_refs_by_service()
        )
        service_names = {
            *self.routable_service_names,
            *endpoint_refs_by_service.keys(),
            *stream_endpoint_refs_by_service.keys(),
        }
        services = tuple(
            HostedServiceRuntimeServiceStatusSnapshot(
                service_name=service_name,
                endpoint_refs=endpoint_refs_by_service.get(service_name, ()),
                stream_endpoint_refs=stream_endpoint_refs_by_service.get(
                    service_name, ()
                ),
            )
            for service_name in sorted(service_names, key=str.casefold)
        )

        process_alive = self.process.returncode is None
        readiness = self.handshake.readiness
        readiness_status = readiness.status.value
        error: str | None = None
        summary: str | None = None
        if not process_alive:
            readiness_status = "stopped"
            error = (
                "Hosted Service process exited "
                f"(returncode={self.process.returncode})"
            )
            summary = error
        elif (
            readiness.is_ready and readiness.status is ServiceHostBootstrapStatus.ready
        ):
            summary = "Hosted Service ready."
        elif readiness.reason:
            summary = readiness.reason
            if readiness.status is ServiceHostBootstrapStatus.failed:
                error = readiness.reason
        else:
            summary = f"Hosted Service {readiness_status}."

        return HostedServiceRuntimeStatusSnapshot(
            host_id=self.handshake.host_id,
            host_version=self.handshake.host_version,
            protocol_version=self.handshake.protocol_version,
            readiness_status=readiness_status,
            is_ready=(
                process_alive
                and readiness.is_ready
                and readiness.status is ServiceHostBootstrapStatus.ready
            ),
            is_alive=process_alive,
            supports_stream_events=_handshake_capability_is_available(
                handshake=self.handshake,
                capability_id="duplex_stream_events",
            ),
            summary=summary,
            error=error,
            updated_at=utc_now_iso(),
            services=services,
        )

    def lifecycle_status_snapshot(self) -> HostedRuntimeLifecycleStatus:
        status = self.runtime_status_snapshot()
        process_alive = self.process.returncode is None
        service_payloads = [
            {
                "service_name": service.service_name,
                "endpoint_refs": list(service.endpoint_refs),
                "stream_endpoint_refs": list(service.stream_endpoint_refs),
            }
            for service in status.services
        ]
        return HostedRuntimeLifecycleStatus(
            runtime_key=_hosted_runtime_key(
                runtime_kind="service",
                manifest_ref=self.bootstrap_config_path,
            ),
            runtime_kind="service",
            status=status.readiness_status,
            is_ready=status.is_ready,
            is_alive=status.is_alive,
            summary=status.summary,
            error=status.error,
            updated_at=status.updated_at,
            pid=self.process.pid,
            returncode=self.process.returncode,
            socket_path=self.socket_path.as_posix(),
            manifest_ref=self.bootstrap_config_path.as_posix(),
            provider_ref=status.host_id,
            provider_package=(
                str(self.implementation_service_package_id)
                if self.implementation_service_package_id is not None
                else None
            ),
            provider_api_ref="service-host-ipc.v1",
            provider_metadata=JsonObject(
                {
                    "host_id": status.host_id,
                    "host_version": status.host_version,
                    "protocol_version": status.protocol_version,
                    "supports_stream_events": status.supports_stream_events,
                    "process_alive": process_alive,
                    "services": service_payloads,
                }
            ),
            recovery_capabilities=_hosted_runtime_recovery_capabilities(
                restart_reason=(
                    "Hosted Service child restart is not enabled by the generic "
                    "Node lifecycle facade in v0."
                )
            ),
        )


@dataclass(frozen=True)
class NodeHostedInterfaceRuntime:
    bootstrap_config_path: Path
    socket_path: Path
    process: _HostedServiceProcess
    ping: object
    launch_command: tuple[str, ...]
    ready_timeout_s: float

    def lifecycle_status_snapshot(self) -> HostedRuntimeLifecycleStatus:
        process_alive = self.process.returncode is None
        ping_success = bool(getattr(self.ping, "success", process_alive))
        ping_status = _optional_text(getattr(self.ping, "status", None))
        ping_error = _optional_text(getattr(self.ping, "error", None))
        restart_recommended = bool(getattr(self.ping, "restart_recommended", False))
        restart_reason = _optional_text(getattr(self.ping, "restart_reason", None))
        if not process_alive:
            status = "stopped"
            is_ready = False
            error = (
                "Hosted Interface process exited "
                f"(returncode={self.process.returncode})"
            )
            summary = error
        else:
            status = ping_status or ("ready" if ping_success else "unknown")
            is_ready = ping_success and status != "failed"
            error = ping_error
            if restart_recommended:
                summary = restart_reason or "Hosted Interface restart recommended."
            elif is_ready:
                summary = "Hosted Interface ready."
            else:
                summary = error or f"Hosted Interface {status}."

        provider_metadata = JsonObject(
            {
                "service": _optional_text(getattr(self.ping, "service", None)),
                "daemon_instance_id": _optional_text(
                    getattr(self.ping, "daemon_instance_id", None)
                ),
                "daemon_started_at": _optional_text(
                    getattr(self.ping, "daemon_started_at", None)
                ),
                "daemon_source_fingerprint": _optional_text(
                    getattr(self.ping, "daemon_source_fingerprint", None)
                ),
                "expected_source_fingerprint": _optional_text(
                    getattr(self.ping, "expected_source_fingerprint", None)
                ),
                "restart_recommended": restart_recommended,
                "restart_reason": restart_reason,
                "repository_root": _optional_text(
                    getattr(self.ping, "repository_root", None)
                ),
                "state_home": _optional_text(getattr(self.ping, "state_home", None)),
            }
        )
        return HostedRuntimeLifecycleStatus(
            runtime_key=_hosted_runtime_key(
                runtime_kind="interface",
                manifest_ref=self.bootstrap_config_path,
            ),
            runtime_kind="interface",
            status=status,
            is_ready=is_ready,
            is_alive=process_alive,
            summary=summary,
            error=error,
            updated_at=utc_now_iso(),
            pid=self.process.pid,
            returncode=self.process.returncode,
            endpoint=_optional_text(getattr(self.ping, "default_endpoint", None)),
            socket_path=self.socket_path.as_posix(),
            manifest_ref=self.bootstrap_config_path.as_posix(),
            provider_ref=_optional_text(getattr(self.ping, "daemon_instance_id", None)),
            provider_package="interface-host",
            provider_api_ref="interface-control-plane.v1",
            provider_metadata=provider_metadata,
            recovery_capabilities=_hosted_runtime_recovery_capabilities(
                restart_enabled=True,
            ),
        )


def _hosted_runtime_key(*, runtime_kind: str, manifest_ref: Path) -> str:
    return f"{runtime_kind}:{manifest_ref.expanduser().resolve().as_posix()}"


def _hosted_runtime_recovery_capabilities(
    *,
    restart_enabled: bool = False,
    restart_reason: str | None = None,
) -> list[HostedRuntimeRecoveryCapability]:
    restart_capability_reason = (
        restart_reason
        if restart_reason is not None
        else "Hosted runtime restart is not enabled by this Node lifecycle facade."
    )
    return [
        HostedRuntimeRecoveryCapability(
            key="refresh",
            enabled=True,
            action_key="node.host.describe_hosted_runtimes",
        ),
        HostedRuntimeRecoveryCapability(
            key="restart",
            enabled=restart_enabled,
            reason=None if restart_enabled else restart_capability_reason,
            action_key="node.host.restart_hosted_runtime",
        ),
        HostedRuntimeRecoveryCapability(
            key="upgrade",
            enabled=False,
            reason=(
                "Runtime upgrade requires WorkspaceRevision/deployment revision "
                "truth and is outside the Node lifecycle v0 facade."
            ),
        ),
    ]


def _hosted_runtime_restart_failure_payload(
    *,
    runtime_key: str,
    error: str,
    reason: str | None,
    evidence: JsonObject | None,
    match_count: int,
    runtime_kind: str | None = None,
    hosted_runtime: HostedRuntimeLifecycleStatus | None = None,
    extra_receipt: Mapping[str, object] | None = None,
) -> dict[str, object]:
    receipt: dict[str, object] = {
        "operation": "restart_hosted_runtime",
        "status": "failed",
        "runtime_key": runtime_key,
        "runtime_kind": runtime_kind,
        "reason": reason,
        "evidence": dict(evidence or {}),
        "match_count": match_count,
        "error": error,
        "recorded_at": utc_now_iso(),
    }
    if extra_receipt:
        receipt.update(dict(extra_receipt))
    return {
        "status": "failed",
        "error": error,
        "runtime_kind": runtime_kind,
        "hosted_runtime": (
            hosted_runtime.model_dump(mode="json", exclude_none=True)
            if hosted_runtime is not None
            else None
        ),
        "operation_receipt": JsonObject(receipt),
    }


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


@dataclass(frozen=True)
class _NetworkNodeLaneHead:
    commit_id: UUID
    graph_hash_post: str | None
    object_instance_graph_id: UUID | None
    root_object_id: UUID


@dataclass(frozen=True)
class _NetworkNodeReplicaWatermark:
    branch_id: UUID
    projection_hash: str
    authority_head_commit_id: UUID
    local_head_commit_id: UUID
    previous_local_head_commit_id: UUID | None
    commits_applied: int


@dataclass(frozen=True)
class _BootNetworkNodeHostedServiceTargets:
    actor_id: UUID
    branch_id: UUID
    node_root_object_id: UUID
    head_commit_id: UUID
    object_instance_graph_id: UUID | None
    graph_hash_post: str | None
    environment_id: UUID
    process_id: UUID
    thread_id: UUID
    projection_graph_id: UUID
    projection_hash: str
    attach_service_function_id: UUID
    runtime_manifest_path: Path | None = None
    route_to_environment_service: EnvironmentRouteHandler | None = None


@dataclass(frozen=True)
class _BootEnvironmentDescriptorResolution:
    descriptor: object
    route_to_environment_service: EnvironmentRouteHandler


@dataclass(frozen=True)
class _RemoteServiceApiProviderInput:
    service_package_ref_payload: Mapping[str, object]
    provider_node_id: UUID
    provider_node_base_url: str
    route_connection_id: UUID | None
    request_timeout_s: float
    hosted_service_advertisement: HostedServiceAdvertisement | None
    authority: ServiceApiRouteAuthority | None = None


@dataclass(frozen=True)
class _NodeServiceApiDependencyRouteResolution:
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...] = ()
    pending_remote_provider_package_names: tuple[str, ...] = ()


@dataclass(frozen=True)
class _ServicePackageRequiredApiFilter:
    service_package: "ServicePackageLike"
    filtered_required_api_packages: tuple["ServiceApiPackageBridgeLike", ...]

    @property
    def id(self) -> UUID:
        return self.service_package.id

    @property
    def name(self) -> str:
        return self.service_package.name

    @property
    def provided_api_packages(self) -> Sequence["ServiceApiPackageBridgeLike"]:
        return self.service_package.provided_api_packages

    @property
    def required_api_packages(self) -> Sequence["ServiceApiPackageBridgeLike"]:
        return self.filtered_required_api_packages

    @property
    def dependencies(self) -> object:
        return getattr(self.service_package, "dependencies", ())


@dataclass(frozen=True)
class _NodeControlPlaneServiceApiConsumerPackage:
    required_api_package: "ServiceApiPackageBridgeLike"

    @property
    def id(self) -> UUID:
        return stable_service_package_id(name=NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME)

    @property
    def name(self) -> str:
        return NODE_CONTROL_PLANE_SERVICE_PACKAGE_NAME

    @property
    def provided_api_packages(self) -> Sequence["ServiceApiPackageBridgeLike"]:
        return ()

    @property
    def required_api_packages(self) -> Sequence["ServiceApiPackageBridgeLike"]:
        return (self.required_api_package,)


@dataclass(frozen=True)
class _PreparedServiceApiPackageBridge:
    api_package_id: UUID
    description: str | None = None
    api_package: object | None = None


@dataclass(frozen=True)
class _PreparedServicePackage:
    id: UUID
    name: str
    provided_api_packages: tuple[_PreparedServiceApiPackageBridge, ...]
    required_api_packages: tuple[_PreparedServiceApiPackageBridge, ...]
    dependencies: tuple[Mapping[str, object], ...] = ()


@dataclass(frozen=True)
class _RemoteServiceApiProviderRuntime:
    consumer_node_id: UUID
    provider_node_id: UUID
    provider_node_base_url: str
    route_connection_id: UUID | None
    request_timeout_s: float
    advertisement: HostedServiceAdvertisement
    authority: ServiceApiRouteAuthority | None = None

    @property
    def host_id(self) -> str:
        return self.advertisement.host_id

    @property
    def host_version(self) -> str | None:
        return self.advertisement.host_version

    @property
    def protocol_version(self) -> str:
        return self.advertisement.protocol_version

    @property
    def routable_service_names(self) -> tuple[str, ...]:
        service_name = self.advertisement.service_name.strip()
        return (service_name,) if service_name else ()

    def advertised_endpoint_refs_by_service(self) -> Mapping[str, tuple[str, ...]]:
        service_name = self.advertisement.service_name.strip()
        if not service_name:
            return {}
        return {
            service_name: tuple(
                ref.strip()
                for ref in self.advertisement.endpoint_refs
                if isinstance(ref, str) and ref.strip()
            )
        }

    def advertised_stream_endpoint_refs_by_service(
        self,
    ) -> Mapping[str, tuple[str, ...]]:
        return {}


@dataclass
class NodeHostServicesAssembly:
    fanout_service: object | None
    fanout_pull_service: object | None = None
    lane_head_receipt_relay: object | None = None
    hosted_service_lane_receipt_relay: object | None = None
    committed_hosted_service_advertisement_index_refresh_relay: object | None = None
    hosted_service_runtimes: tuple[NodeHostedServiceRuntime, ...] = ()
    hosted_interface_runtimes: tuple[NodeHostedInterfaceRuntime, ...] = ()
    service_api_dependency_routes: tuple[
        "NodeServiceApiDependencyRouteDescriptor", ...
    ] = ()
    service_api_dependency_route_refresh_task: asyncio.Task[None] | None = None
    committed_hosted_service_advertisement_index: (
        _CommittedHostedServiceAdvertisementIndex | None
    ) = None

    def discover_hosted_service_advertisements(
        self,
    ) -> tuple[HostedServiceAdvertisement, ...]:
        advertisements: list[HostedServiceAdvertisement] = []
        seen_service_names: set[str] = set()

        for runtime in self.hosted_service_runtimes:
            if not runtime.routable_service_names:
                continue

            supports_stream_events = _handshake_capability_is_available(
                handshake=runtime.handshake,
                capability_id="duplex_stream_events",
            )
            endpoint_refs_by_service = runtime.advertised_endpoint_refs_by_service()
            service_ids_by_name = _extract_committed_service_ids_by_name_from_handshake(
                handshake=runtime.handshake
            )
            service_package_ids_by_name = (
                _extract_service_package_ids_by_name_from_handshake(
                    handshake=runtime.handshake
                )
            )
            for service_name in runtime.routable_service_names:
                if service_name in seen_service_names:
                    raise RuntimeError(
                        "Multiple Node hosted Service runtimes advertise the same service "
                        f"{service_name!r}"
                    )
                seen_service_names.add(service_name)
                service_name_key = service_name.casefold()
                advertisements.append(
                    HostedServiceAdvertisement(
                        service_package_id=(
                            service_package_ids_by_name.get(service_name_key)
                            or runtime.implementation_service_package_id
                        ),
                        service_id=service_ids_by_name.get(service_name_key),
                        service_name=service_name,
                        endpoint_refs=list(
                            endpoint_refs_by_service.get(service_name, ())
                        ),
                        host_id=runtime.handshake.host_id,
                        host_version=runtime.handshake.host_version,
                        protocol_version=runtime.handshake.protocol_version,
                        supports_stream_events=supports_stream_events,
                    )
                )

        return tuple(advertisements)

    def discover_committed_hosted_service_advertisements(
        self,
    ) -> tuple[HostedServiceAdvertisement, ...] | None:
        if self.committed_hosted_service_advertisement_index is None:
            return None
        return self.committed_hosted_service_advertisement_index.advertisements

    def resolve_committed_hosted_service_advertisement_for_service_name(
        self,
        *,
        service_name: str,
    ) -> HostedServiceAdvertisement:
        normalized = service_name.strip()
        if not normalized:
            raise RuntimeError("ServiceOperationRequest.service is required")
        index = self.committed_hosted_service_advertisement_index
        if index is None:
            raise RuntimeError(
                "Node committed hosted-service advertisement index is unavailable"
            )
        advertisement = index.advertisement_by_service_name.get(normalized.casefold())
        if advertisement is None:
            raise CommittedHostedServiceLookupMiss(
                "Node hosted Service runtime is not registered for service "
                f"{normalized!r} via committed NetworkNodeService truth"
            )
        return advertisement

    def resolve_committed_hosted_service_advertisement_for_endpoint_ref(
        self,
        *,
        endpoint_ref: str,
    ) -> HostedServiceAdvertisement:
        normalized = endpoint_ref.strip()
        if not normalized:
            raise RuntimeError("InvokeApiEndpointRequest.endpoint_ref is required")
        index = self.committed_hosted_service_advertisement_index
        if index is None:
            raise RuntimeError(
                "Node committed hosted-service advertisement index is unavailable"
            )
        advertisement = index.advertisement_by_endpoint_ref.get(normalized.casefold())
        if advertisement is None:
            raise CommittedHostedServiceLookupMiss(
                "Node hosted Service runtime is not registered for endpoint_ref "
                f"{normalized!r} via committed NetworkNodeService truth"
            )
        return advertisement

    def describe_hosted_service_runtime_statuses(
        self,
    ) -> tuple[HostedServiceRuntimeStatus, ...]:
        return tuple(
            runtime.runtime_status_snapshot().to_api_model()
            for runtime in self.hosted_service_runtimes
        )

    def describe_hosted_runtime_lifecycle_statuses(
        self,
        *,
        runtime_kind: str | None = None,
        runtime_key: str | None = None,
    ) -> tuple[HostedRuntimeLifecycleStatus, ...]:
        requested_kind = runtime_kind.strip().casefold() if runtime_kind else None
        requested_key = runtime_key.strip() if runtime_key else None
        statuses = [
            *(
                runtime.lifecycle_status_snapshot()
                for runtime in self.hosted_service_runtimes
            ),
            *(
                runtime.lifecycle_status_snapshot()
                for runtime in self.hosted_interface_runtimes
            ),
        ]
        return tuple(
            status
            for status in statuses
            if (
                requested_kind is None
                or status.runtime_kind.casefold() == requested_kind
            )
            and (requested_key is None or status.runtime_key == requested_key)
        )

    def describe_hosted_runtime_lifecycle_status(
        self,
        *,
        runtime_key: str,
    ) -> HostedRuntimeLifecycleStatus | None:
        matches = self.describe_hosted_runtime_lifecycle_statuses(
            runtime_key=runtime_key
        )
        if not matches:
            return None
        if len(matches) > 1:
            raise RuntimeError(
                "Multiple hosted runtimes matched runtime_key "
                f"{runtime_key!r}; runtime_key must be unique."
            )
        return matches[0]

    async def restart_hosted_runtime(
        self,
        *,
        runtime_key: str,
        reason: str | None = None,
        evidence: JsonObject | None = None,
    ) -> dict[str, object]:
        normalized_key = runtime_key.strip()
        if not normalized_key:
            return _hosted_runtime_restart_failure_payload(
                runtime_key=runtime_key,
                error="Hosted runtime restart requires runtime_key.",
                reason=reason,
                evidence=evidence,
                match_count=0,
            )

        service_matches = [
            runtime.lifecycle_status_snapshot()
            for runtime in self.hosted_service_runtimes
            if runtime.lifecycle_status_snapshot().runtime_key == normalized_key
        ]
        interface_matches: list[
            tuple[int, NodeHostedInterfaceRuntime, HostedRuntimeLifecycleStatus]
        ] = []
        for index, runtime in enumerate(self.hosted_interface_runtimes):
            status = runtime.lifecycle_status_snapshot()
            if status.runtime_key == normalized_key:
                interface_matches.append((index, runtime, status))

        match_count = len(service_matches) + len(interface_matches)
        if match_count != 1:
            return _hosted_runtime_restart_failure_payload(
                runtime_key=normalized_key,
                error=(
                    "Hosted runtime restart requires exactly one runtime match; "
                    f"found {match_count}."
                ),
                reason=reason,
                evidence=evidence,
                match_count=match_count,
            )
        if service_matches:
            return _hosted_runtime_restart_failure_payload(
                runtime_key=normalized_key,
                error=(
                    "Hosted Service child restart remains disabled; this operation "
                    "only restarts hosted Interface runtimes."
                ),
                reason=reason,
                evidence=evidence,
                match_count=match_count,
                runtime_kind="service",
                hosted_runtime=service_matches[0],
            )

        index, runtime, before_status = interface_matches[0]
        stopped_pid = runtime.process.pid
        await _stop_hosted_interface_process(runtime)
        with contextlib.suppress(FileNotFoundError):
            if runtime.socket_path.exists() or runtime.socket_path.is_socket():
                runtime.socket_path.unlink()

        try:
            replacement = await _start_hosted_interface_runtime(
                bootstrap_config_path=runtime.bootstrap_config_path,
                launch_command=runtime.launch_command,
                ready_timeout_s=runtime.ready_timeout_s,
            )
        except Exception as exc:
            stopped_status = runtime.lifecycle_status_snapshot()
            return _hosted_runtime_restart_failure_payload(
                runtime_key=normalized_key,
                error=str(exc),
                reason=reason,
                evidence=evidence,
                match_count=match_count,
                runtime_kind="interface",
                hosted_runtime=stopped_status,
                extra_receipt={
                    "previous_pid": stopped_pid,
                    "status_before_restart": before_status.model_dump(
                        mode="json", exclude_none=True
                    ),
                },
            )

        runtimes = list(self.hosted_interface_runtimes)
        runtimes[index] = replacement
        self.hosted_interface_runtimes = tuple(runtimes)
        restarted_status = replacement.lifecycle_status_snapshot()
        return {
            "status": "succeeded",
            "error": None,
            "runtime_kind": "interface",
            "hosted_runtime": restarted_status.model_dump(
                mode="json", exclude_none=True
            ),
            "operation_receipt": JsonObject(
                {
                    "operation": "restart_hosted_runtime",
                    "status": "succeeded",
                    "runtime_key": restarted_status.runtime_key,
                    "runtime_kind": "interface",
                    "reason": reason,
                    "evidence": dict(evidence or {}),
                    "previous_pid": stopped_pid,
                    "new_pid": replacement.process.pid,
                    "bootstrap_config_path": runtime.bootstrap_config_path.as_posix(),
                    "socket_path": replacement.socket_path.as_posix(),
                    "restarted_at": restarted_status.updated_at or utc_now_iso(),
                    "status_before_restart": before_status.model_dump(
                        mode="json", exclude_none=True
                    ),
                }
            ),
        }

    def resolve_hosted_service_runtime(
        self,
        *,
        bootstrap_config_path: str | Path,
    ) -> NodeHostedServiceRuntime:
        resolved = Path(bootstrap_config_path).expanduser().resolve()
        for runtime in self.hosted_service_runtimes:
            if runtime.bootstrap_config_path == resolved:
                return runtime
        raise RuntimeError(
            "Node hosted Service runtime is not registered for bootstrap config "
            f"{resolved}"
        )

    def resolve_hosted_service_runtime_for_host_id(
        self,
        *,
        host_id: str,
    ) -> NodeHostedServiceRuntime:
        normalized = host_id.strip()
        if not normalized:
            raise RuntimeError("Hosted Service host_id is required")

        match: NodeHostedServiceRuntime | None = None
        for runtime in self.hosted_service_runtimes:
            runtime_host_id = (runtime.handshake.host_id or "").strip()
            if runtime_host_id.casefold() != normalized.casefold():
                continue
            if match is not None:
                raise RuntimeError(
                    "Multiple Node hosted Service runtimes are registered for host_id "
                    f"{normalized!r}"
                )
            match = runtime

        if match is None:
            raise RuntimeError(
                "Node hosted Service runtime is not registered for host_id "
                f"{normalized!r}"
            )
        return match

    def resolve_local_service_api_dependency_routes(
        self,
        *,
        consumer_service_packages: Sequence["ServicePackageLike"],
        provider_service_packages: Sequence["ServicePackageLike"],
        allow_prepared_local_providers: bool = False,
    ) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
        return self.resolve_service_api_dependency_routes(
            consumer_service_packages=consumer_service_packages,
            provider_service_packages=provider_service_packages,
            allow_prepared_local_providers=allow_prepared_local_providers,
        )

    def resolve_service_api_dependency_routes(
        self,
        *,
        consumer_service_packages: Sequence["ServicePackageLike"],
        provider_service_packages: Sequence["ServicePackageLike"],
        remote_provider_runtimes: Sequence["NodeRemoteServiceApiProviderRuntime"] = (),
        authority_selectors_by_service_api_requirement: (
            Mapping[
                tuple[UUID, UUID],
                ServiceApiRouteAuthoritySelector,
            ]
            | None
        ) = None,
        authority_selectors_by_api_package_id: (
            Mapping[
                UUID,
                ServiceApiRouteAuthoritySelector,
            ]
            | None
        ) = None,
        allow_prepared_local_providers: bool = False,
    ) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
        from aware_node_service.host.service_api_dependency_resolution import (
            NodeServiceApiProviderRuntime,
            resolve_service_api_dependency_routes,
        )

        runtime_by_package_name: dict[str, NodeHostedServiceRuntime] = {}
        for runtime in self.hosted_service_runtimes:
            for package_name in runtime.implementation_package_names:
                normalized_package_name = package_name.strip().casefold()
                if not normalized_package_name:
                    continue
                existing = runtime_by_package_name.get(normalized_package_name)
                if existing is not None and existing is not runtime:
                    raise RuntimeError(
                        "Multiple Node hosted Service runtimes are registered for "
                        f"ServicePackage {package_name!r}"
                    )
                runtime_by_package_name[normalized_package_name] = runtime

        provider_runtimes = tuple(
            NodeServiceApiProviderRuntime(
                service_package=provider,
                runtime=runtime_by_package_name.get(
                    _hosted_service_package_name(provider).casefold()
                ),
            )
            for provider in provider_service_packages
        )
        return resolve_service_api_dependency_routes(
            consumer_service_packages=consumer_service_packages,
            provider_runtimes=provider_runtimes,
            remote_provider_runtimes=tuple(remote_provider_runtimes),
            authority_selectors_by_service_api_requirement=(
                authority_selectors_by_service_api_requirement
            ),
            authority_selectors_by_api_package_id=(
                authority_selectors_by_api_package_id
            ),
            allow_prepared_local_providers=allow_prepared_local_providers,
        )


@dataclass(frozen=True)
class _CommittedHostedServiceAdvertisementCoverage:
    live_service_count: int
    live_endpoint_count: int
    committed_service_count: int
    committed_endpoint_count: int
    missing_service_names: tuple[str, ...] = ()
    missing_endpoint_refs: tuple[str, ...] = ()
    mismatched_endpoint_refs: tuple[str, ...] = ()

    @property
    def is_satisfied(self) -> bool:
        return not (
            self.missing_service_names
            or self.missing_endpoint_refs
            or self.mismatched_endpoint_refs
        )


class HostedServiceLaneReceiptRelay:
    """Forward node-local lane receipts into hosted Service processes."""

    def __init__(
        self,
        *,
        hosted_service_runtimes: tuple[NodeHostedServiceRuntime, ...],
    ) -> None:
        self._hosted_service_runtimes = hosted_service_runtimes
        self._unsubscribe_by_lane: list[Callable[[], None]] = []

    def start(self) -> None:
        lane_to_runtimes: dict[tuple[UUID, str], list[NodeHostedServiceRuntime]] = {}
        for runtime in self._hosted_service_runtimes:
            for subscription in runtime.lane_subscriptions:
                projection_hash = (subscription.projection_hash or "").strip()
                if not projection_hash:
                    continue
                lane_to_runtimes.setdefault(
                    (subscription.branch_id, projection_hash), []
                ).append(runtime)

        bus = LaneCommitReceiptBus.instance()
        self._unsubscribe_by_lane = []
        for (branch_id, projection_hash), runtimes in lane_to_runtimes.items():
            self._unsubscribe_by_lane.append(
                bus.subscribe_lane(
                    branch_id=branch_id,
                    projection_hash=projection_hash,
                    watcher=self._build_lane_watcher(runtimes=tuple(runtimes)),
                )
            )

    async def stop(self) -> None:
        while self._unsubscribe_by_lane:
            unsubscribe = self._unsubscribe_by_lane.pop()
            unsubscribe()

    def _build_lane_watcher(
        self,
        *,
        runtimes: tuple[NodeHostedServiceRuntime, ...],
    ):
        async def _watcher(receipt: LaneCommitReceiptNotification) -> None:
            for runtime in runtimes:
                try:
                    await _send_lane_commit_receipt_to_hosted_service_runtime(
                        runtime=runtime,
                        receipt=receipt,
                    )
                except Exception as exc:
                    logger.warning(
                        "Node hosted Service lane receipt forward failed "
                        "(bootstrap_config=%s branch_id=%s projection_hash=%s error=%s)",
                        runtime.bootstrap_config_path.as_posix(),
                        receipt.branch_id,
                        receipt.projection_hash,
                        exc,
                    )

        return _watcher


class CommittedHostedServiceAdvertisementIndexRefreshRelay:
    """Refresh the bootstrapped committed hosted-service index from lane receipts."""

    def __init__(
        self,
        *,
        node_app: object,
        runtime_registry: NodeHostServicesAssembly,
        targets: _BootNetworkNodeHostedServiceTargets,
    ) -> None:
        self._node_app = node_app
        self._runtime_registry = runtime_registry
        self._targets = targets
        self._unsubscribe: Callable[[], None] | None = None
        self._refresh_generation = 0
        self._refresh_task: asyncio.Task[None] | None = None

    def start(self) -> None:
        if self._unsubscribe is not None:
            return
        self._unsubscribe = LaneCommitReceiptBus.instance().subscribe_lane(
            branch_id=self._targets.branch_id,
            projection_hash=self._targets.projection_hash,
            watcher=self._on_receipt,
        )
        logger.info(
            "Node committed hosted-service index refresh relay started "
            "(branch_id=%s projection_hash=%s)",
            self._targets.branch_id,
            self._targets.projection_hash,
        )

    async def stop(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        refresh_task = self._refresh_task
        self._refresh_task = None
        if refresh_task is None:
            return
        refresh_task.cancel()
        await asyncio.gather(refresh_task, return_exceptions=True)

    async def _on_receipt(self, receipt: LaneCommitReceiptNotification) -> None:
        del receipt
        self._refresh_generation += 1
        refresh_task = self._refresh_task
        if refresh_task is not None and not refresh_task.done():
            return
        self._refresh_task = asyncio.create_task(self._refresh_until_caught_up())

    async def _refresh_until_caught_up(self) -> None:
        while True:
            generation = self._refresh_generation
            try:
                refreshed_index = (
                    await _refresh_committed_hosted_service_advertisement_index(
                        node_app=self._node_app,
                        targets=self._targets,
                    )
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._runtime_registry.committed_hosted_service_advertisement_index = (
                    None
                )
                logger.warning(
                    "Node committed hosted-service index refresh failed; "
                    "invalidated bootstrap index and will fall back to direct reads "
                    "(branch_id=%s projection_hash=%s error=%s)",
                    self._targets.branch_id,
                    self._targets.projection_hash,
                    exc,
                )
                return

            self._runtime_registry.committed_hosted_service_advertisement_index = (
                refreshed_index
            )
            if self._refresh_generation == generation:
                return


async def start_node_host_services(*, node_app: object) -> NodeHostServicesAssembly:
    fanout_service: object | None = None
    lane_head_receipt_relay: object | None = None
    fanout_pull_service: object | None = None
    hosted_service_lane_receipt_relay: object | None = None
    committed_hosted_service_advertisement_index_refresh_relay: object | None = None
    try:
        from aware_node_service.network.fanout_service import NetworkFanoutService

        fanout_service = NetworkFanoutService.from_env(network_app=cast(Any, node_app))
        if fanout_service is not None:
            fanout_service.start()
    except Exception as exc:
        logger.warning("Network fanout service not started: %s", exc)
        fanout_service = None

    try:
        lane_head_receipt_relay = _start_node_lane_head_receipt_relay(node_app=node_app)
        fanout_pull_service = _start_node_fanout_pull_service(
            node_app=node_app,
            lane_head_receipt_relay=lane_head_receipt_relay,
        )
    except Exception:
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise

    try:
        hosted_service_runtimes = await _start_hosted_service_runtimes(
            config=NodeHostedServiceSupervisorConfig.from_env()
        )
    except Exception:
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise

    try:
        hosted_interface_runtimes = await _start_hosted_interface_runtimes(
            config=NodeHostedInterfaceSupervisorConfig.from_env()
        )
    except Exception:
        await _stop_hosted_service_runtimes(hosted_service_runtimes)
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise

    try:
        hosted_service_lane_receipt_relay = _start_hosted_service_lane_receipt_relay(
            hosted_service_runtimes=hosted_service_runtimes,
        )
    except Exception:
        await _stop_hosted_interface_runtimes(hosted_interface_runtimes)
        await _stop_hosted_service_runtimes(hosted_service_runtimes)
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise

    try:
        (
            committed_hosted_service_targets,
            committed_hosted_service_advertisement_index,
        ) = await _bootstrap_committed_hosted_service_advertisement_index(
            node_app=node_app,
            hosted_service_runtimes=hosted_service_runtimes,
            defer_unavailable_environment=True,
        )
    except Exception:
        await _stop_hosted_service_lane_receipt_relay(hosted_service_lane_receipt_relay)
        await _stop_hosted_interface_runtimes(hosted_interface_runtimes)
        await _stop_hosted_service_runtimes(hosted_service_runtimes)
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise

    assembly = NodeHostServicesAssembly(
        fanout_service=fanout_service,
        fanout_pull_service=fanout_pull_service,
        lane_head_receipt_relay=lane_head_receipt_relay,
        hosted_service_lane_receipt_relay=hosted_service_lane_receipt_relay,
        hosted_service_runtimes=hosted_service_runtimes,
        hosted_interface_runtimes=hosted_interface_runtimes,
        committed_hosted_service_advertisement_index=(
            committed_hosted_service_advertisement_index
        ),
    )
    try:
        committed_hosted_service_advertisement_index_refresh_relay = (
            _start_committed_hosted_service_advertisement_index_refresh_relay(
                node_app=node_app,
                runtime_registry=assembly,
                targets=committed_hosted_service_targets,
            )
        )
    except Exception:
        await _stop_hosted_service_lane_receipt_relay(hosted_service_lane_receipt_relay)
        await _stop_hosted_interface_runtimes(hosted_interface_runtimes)
        await _stop_hosted_service_runtimes(hosted_service_runtimes)
        await _stop_node_fanout_pull_service(fanout_pull_service)
        _stop_node_lane_head_receipt_relay(lane_head_receipt_relay)
        await _stop_fanout_service(fanout_service)
        raise
    assembly.committed_hosted_service_advertisement_index_refresh_relay = (
        committed_hosted_service_advertisement_index_refresh_relay
    )
    return assembly


async def bind_node_service_api_dependency_routes(
    *,
    node_app: object,
    runtime: NodeHostServicesAssembly,
    start_remote_refresh: bool = True,
    configure_hosted_environments: bool = True,
    allow_prepared_local_providers: bool = False,
    include_node_control_plane_consumer: bool = True,
    require_complete: bool = False,
) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
    """Bind selected ServicePackage API requirements to live local ServiceHosts."""

    if configure_hosted_environments:
        await _ensure_committed_hosted_service_advertisement_index(
            node_app=node_app,
            runtime=runtime,
            defer_unavailable_environment=True,
        )
        if _committed_hosted_service_advertisement_bootstrap_pending(
            runtime=runtime,
        ):
            logger.info(
                "Node authority ready with Network publication pending; "
                "committed hosted-service advertisement coverage will be "
                "reconciled after Environment and Network routes are ready"
            )
        else:
            _require_committed_hosted_service_advertisement_index_coverage(
                runtime=runtime,
                context="node service API dependency route binding",
            )

    resolution = await _resolve_node_service_api_dependency_routes_from_env(
        node_app=node_app,
        runtime=runtime,
        allow_prepared_local_providers=allow_prepared_local_providers,
        include_node_control_plane_consumer=include_node_control_plane_consumer,
    )
    if require_complete and resolution.pending_remote_provider_package_names:
        raise RuntimeError(
            "Node initial ServiceHost activation requires complete dependency "
            "routes; remote providers remain pending: "
            f"{resolution.pending_remote_provider_package_names}."
        )
    routes = resolution.routes
    await _apply_node_service_api_dependency_routes(
        node_app=node_app,
        runtime=runtime,
        routes=routes,
        configure_hosted_environments=configure_hosted_environments,
    )
    if start_remote_refresh and (
        resolution.pending_remote_provider_package_names
        or _committed_hosted_service_advertisement_bootstrap_pending(
            runtime=runtime,
        )
    ):
        _start_node_service_api_dependency_route_refresh_task(
            node_app=node_app,
            runtime=runtime,
            pending_remote_provider_package_names=(
                resolution.pending_remote_provider_package_names
            ),
        )
    elif not resolution.pending_remote_provider_package_names:
        await _stop_node_service_api_dependency_route_refresh_task(
            runtime.service_api_dependency_route_refresh_task
        )
        runtime.service_api_dependency_route_refresh_task = None
    return routes


async def activate_node_hosted_service_lifecycles(
    *,
    runtime: NodeHostServicesAssembly,
) -> int:
    """Activate prepared ServiceHosts only after every route plan is installed."""

    activated_runtimes: list[NodeHostedServiceRuntime] = []
    for hosted_runtime in runtime.hosted_service_runtimes:
        client = _build_hosted_service_duplex_client(
            socket_path=hosted_runtime.socket_path
        )
        response = await client.send_host_control_request(
            request=ActivateServiceHostLifecyclesHostControlRequest(),
            timeout_s=hosted_runtime.ready_timeout_s,
        )
        if (
            not isinstance(
                response,
                ActivateServiceHostLifecyclesHostControlResponse,
            )
            or response.status is not RequestStatus.succeeded
        ):
            raise RuntimeError(
                "ServiceHost lifecycle activation failed "
                f"(bootstrap_config={hosted_runtime.bootstrap_config_path} "
                f"error={getattr(response, 'error', None) or 'unknown error'})"
            )
        handshake = await wait_for_hosted_service_handshake_ready(
            socket_path=hosted_runtime.socket_path,
            process=hosted_runtime.process,
            timeout_s=hosted_runtime.ready_timeout_s,
        )
        activated_runtimes.append(
            replace(
                hosted_runtime,
                handshake=handshake,
                routable_service_names=(
                    _extract_routable_service_names_from_handshake(handshake=handshake)
                ),
                routable_endpoint_refs_by_service=(
                    _extract_routable_endpoint_refs_by_service_from_handshake(
                        handshake=handshake
                    )
                ),
                lane_subscriptions=_extract_lane_subscriptions_from_handshake(
                    handshake=handshake
                ),
            )
        )
    runtime.hosted_service_runtimes = tuple(activated_runtimes)
    if activated_runtimes:
        logger.info(
            "Node activated hosted Service lifecycles " "(service_host_count=%s)",
            len(activated_runtimes),
        )
    return len(activated_runtimes)


async def _apply_node_service_api_dependency_routes(
    *,
    node_app: object,
    runtime: NodeHostServicesAssembly,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
    configure_hosted_environments: bool = True,
) -> None:
    runtime.service_api_dependency_routes = routes
    network_sdk_binding = configure_network_sdk_client_from_service_api_routes(
        node_app=node_app,
        routes=routes,
    )
    if network_sdk_binding is not None:
        remote_provider_inputs = _remote_service_api_provider_inputs_from_env()
        if remote_provider_inputs:
            await bootstrap_network_peers_from_provider_inputs(
                network_sdk_client=network_sdk_binding.client,
                provider_inputs=remote_provider_inputs,
            )
    routes_json = json.dumps(
        service_api_dependency_routes_to_payload(routes),
        sort_keys=True,
    )
    environment_routes = _service_api_dependency_routes_for_consumer_package(
        routes=routes,
        consumer_service_package_name=_ENVIRONMENT_SERVICE_PACKAGE_NAME,
    )
    environment_routes_json = json.dumps(
        service_api_dependency_routes_to_payload(environment_routes),
        sort_keys=True,
    )
    os.environ[_NODE_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV] = routes_json
    await _configure_hosted_service_api_dependency_routes(
        runtime=runtime,
        routes=routes,
    )
    if not routes:
        os.environ.pop(_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV, None)
        logger.info(
            "Node installed explicit empty service API dependency route plans "
            "(provider_hosts=%s)",
            len(runtime.hosted_service_runtimes),
        )
        return
    if environment_routes:
        os.environ[_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV] = (
            environment_routes_json
        )
    else:
        os.environ.pop(_ENVIRONMENT_HOST_SERVICE_API_DEPENDENCY_ROUTES_JSON_ENV, None)
    await _configure_in_process_environment_service_api_dependency_routes(
        node_app=node_app,
        routes=environment_routes,
    )
    if configure_hosted_environments:
        await _configure_hosted_environment_service_api_dependency_routes(
            node_app=node_app,
            routes=environment_routes,
        )
    if network_sdk_binding is not None:
        environment_id = _resolve_node_publication_environment_id(node_app=node_app)
        if environment_id is None:
            logger.info(
                "Deferred Network publication until an Environment descriptor is ready"
            )
        else:
            await reconcile_node_runtime_publication(
                network_sdk_client=network_sdk_binding.client,
                runtime=runtime,
                environment_id=environment_id,
            )
    logger.info(
        "Node service API dependency routes bound "
        "(route_count=%s provider_hosts=%s)",
        len(routes),
        len(runtime.hosted_service_runtimes),
    )


def _resolve_node_publication_environment_id(*, node_app: object) -> UUID | None:
    hosted_environment_service = getattr(
        node_app, "_node_hosted_environment_service", None
    )
    if hosted_environment_service is None:
        return None
    if not _has_local_environment_config_runtime_input(hosted_environment_service):
        return None
    resolution = hosted_environment_service.read_boot_environment_descriptor(
        node_id=network_node_manager.hosted_node_id
    )
    descriptor = getattr(resolution, "descriptor", None)
    return getattr(descriptor, "boot_environment_id", None)


async def resolve_node_service_api_dependency_routes_from_env(
    *,
    node_app: object | None = None,
    runtime: NodeHostServicesAssembly,
) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
    return (
        await _resolve_node_service_api_dependency_routes_from_env(
            node_app=node_app,
            runtime=runtime,
        )
    ).routes


async def _resolve_node_service_api_dependency_routes_from_env(
    *,
    node_app: object | None = None,
    runtime: NodeHostServicesAssembly,
    allow_prepared_local_providers: bool = False,
    include_node_control_plane_consumer: bool = True,
) -> _NodeServiceApiDependencyRouteResolution:
    package_refs_payload = _service_api_dependency_package_refs_payload_from_env()
    remote_provider_inputs = _remote_service_api_provider_inputs_from_env()
    authority_selectors_by_api_package_id = (
        _service_api_dependency_authority_selectors_by_api_package_id_from_env()
    )
    if not package_refs_payload and not remote_provider_inputs:
        return _NodeServiceApiDependencyRouteResolution()
    remote_package_refs_payload = tuple(
        item.service_package_ref_payload for item in remote_provider_inputs
    )
    local_service_packages = (
        await _resolve_service_packages_for_api_dependency_routes(
            package_refs_payload=package_refs_payload,
        )
        if package_refs_payload
        else ()
    )
    remote_service_packages = (
        await _resolve_service_packages_for_api_dependency_routes(
            package_refs_payload=remote_package_refs_payload,
            prepared_service_package_catalog=local_service_packages,
        )
        if remote_package_refs_payload
        else ()
    )
    service_packages = local_service_packages + remote_service_packages
    source_authority_selectors_by_requirement = _service_api_dependency_authority_selectors_by_requirement_from_service_packages(
        service_packages=service_packages,
    )
    consumer_packages = list(
        package
        for package in local_service_packages
        if tuple(getattr(package, "required_api_packages", ()))
    )
    network_service_api_consumer = None
    if include_node_control_plane_consumer:
        network_service_api_consumer = (
            _node_control_plane_network_service_api_consumer_package(
                service_packages=service_packages,
            )
        )
    if network_service_api_consumer is not None:
        consumer_packages.append(network_service_api_consumer)
    if not consumer_packages:
        return _NodeServiceApiDependencyRouteResolution()
    provider_packages = tuple(
        package
        for package in local_service_packages
        if tuple(getattr(package, "provided_api_packages", ()))
    )
    remote_provider_inputs = _filter_remote_provider_inputs_for_consumers(
        remote_provider_inputs=remote_provider_inputs,
        consumer_packages=tuple(consumer_packages),
        provider_packages=provider_packages,
        service_packages=service_packages,
    )
    remote_provider_inputs = await _hydrate_remote_service_api_provider_inputs_with_discovered_advertisements(
        node_app=node_app,
        remote_provider_inputs=remote_provider_inputs,
        service_packages=service_packages,
    )
    remote_provider_runtimes = _build_remote_service_api_provider_runtimes(
        remote_provider_inputs=remote_provider_inputs,
        service_packages=service_packages,
    )
    pending_remote_provider_names = _pending_remote_service_api_provider_package_names(
        remote_provider_inputs=remote_provider_inputs,
    )
    pending_remote_provider_names = (
        _pending_remote_provider_package_names_for_consumers(
            pending_remote_provider_package_names=pending_remote_provider_names,
            consumer_packages=tuple(consumer_packages),
            provider_packages=provider_packages,
            remote_provider_runtimes=remote_provider_runtimes,
            service_packages=service_packages,
        )
    )
    filtered_consumer_packages = _filter_consumer_packages_for_pending_remote_providers(
        consumer_packages=tuple(consumer_packages),
        provider_packages=provider_packages,
        remote_provider_runtimes=remote_provider_runtimes,
        pending_remote_provider_package_names=pending_remote_provider_names,
        service_packages=service_packages,
    )
    if not filtered_consumer_packages:
        return _NodeServiceApiDependencyRouteResolution(
            pending_remote_provider_package_names=tuple(
                sorted(pending_remote_provider_names, key=str.casefold)
            )
        )
    routes = runtime.resolve_service_api_dependency_routes(
        consumer_service_packages=filtered_consumer_packages,
        provider_service_packages=provider_packages,
        remote_provider_runtimes=remote_provider_runtimes,
        authority_selectors_by_service_api_requirement=(
            source_authority_selectors_by_requirement
        ),
        authority_selectors_by_api_package_id=authority_selectors_by_api_package_id,
        allow_prepared_local_providers=allow_prepared_local_providers,
    )
    return _NodeServiceApiDependencyRouteResolution(
        routes=routes,
        pending_remote_provider_package_names=tuple(
            sorted(pending_remote_provider_names, key=str.casefold)
        ),
    )


def _node_control_plane_network_service_api_consumer_package(
    *,
    service_packages: tuple["ServicePackageLike", ...],
) -> _NodeControlPlaneServiceApiConsumerPackage | None:
    bridge = _select_network_service_api_provider_bridge(
        service_packages=service_packages,
    )
    if bridge is None:
        return None
    return _NodeControlPlaneServiceApiConsumerPackage(required_api_package=bridge)


def _select_network_service_api_provider_bridge(
    *,
    service_packages: tuple["ServicePackageLike", ...],
) -> "ServiceApiPackageBridgeLike | None":
    matches: list["ServiceApiPackageBridgeLike"] = []
    for package in service_packages:
        for bridge in tuple(getattr(package, "provided_api_packages", ())):
            if _service_api_package_bridge_matches_network_service_api(bridge):
                matches.append(bridge)
    if not matches:
        return None
    unique_by_id = {bridge.api_package_id: bridge for bridge in matches}
    if len(unique_by_id) != 1:
        labels = ", ".join(sorted(str(api_id) for api_id in unique_by_id))
        raise RuntimeError(
            "Selected Network Service providers expose conflicting "
            f"network-service-api package ids: {labels}."
        )
    return next(iter(unique_by_id.values()))


def _service_api_package_bridge_matches_network_service_api(
    bridge: "ServiceApiPackageBridgeLike",
) -> bool:
    api_package_name = _service_api_package_bridge_name(bridge)
    if (
        api_package_name is not None
        and api_package_name.casefold() == NETWORK_SERVICE_API_PACKAGE_NAME
    ):
        return True
    return bridge.api_package_id == stable_api_package_id(
        name=NETWORK_SERVICE_API_PACKAGE_NAME
    )


def _service_api_package_bridge_name(
    bridge: "ServiceApiPackageBridgeLike",
) -> str | None:
    api_package = bridge.api_package
    if api_package is None:
        return None
    raw_name = getattr(api_package, "name", None)
    if not isinstance(raw_name, str):
        return None
    name = raw_name.strip()
    return name or None


def _start_node_service_api_dependency_route_refresh_task(
    *,
    node_app: object,
    runtime: NodeHostServicesAssembly,
    pending_remote_provider_package_names: tuple[str, ...],
) -> None:
    refresh_task = runtime.service_api_dependency_route_refresh_task
    if refresh_task is not None and not refresh_task.done():
        return
    runtime.service_api_dependency_route_refresh_task = asyncio.create_task(
        _node_service_api_dependency_route_refresh_loop(
            node_app=node_app,
            runtime=runtime,
            initial_pending_remote_provider_package_names=(
                pending_remote_provider_package_names
            ),
        )
    )


async def _node_service_api_dependency_route_refresh_loop(
    *,
    node_app: object,
    runtime: NodeHostServicesAssembly,
    initial_pending_remote_provider_package_names: tuple[str, ...],
) -> None:
    interval_s = _float_env(
        _NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_INTERVAL_S_ENV,
        default=2.0,
    )
    timeout_s = _float_env(
        _NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_TIMEOUT_S_ENV,
        default=60.0,
    )
    deadline = monotonic() + max(timeout_s, interval_s)
    pending = initial_pending_remote_provider_package_names
    logger.info(
        "Node service API dependency route refresh started "
        "(pending_remote_provider_packages=%s interval_s=%.2f timeout_s=%.2f)",
        ",".join(pending),
        interval_s,
        timeout_s,
    )
    last_error: Exception | None = None
    try:
        while (
            pending
            or _committed_hosted_service_advertisement_bootstrap_pending(
                runtime=runtime,
            )
        ) and monotonic() < deadline:
            await asyncio.sleep(interval_s)
            try:
                if _committed_hosted_service_advertisement_bootstrap_pending(
                    runtime=runtime,
                ):
                    await _ensure_committed_hosted_service_advertisement_index(
                        node_app=node_app,
                        runtime=runtime,
                        defer_unavailable_environment=True,
                    )
                resolution = await _resolve_node_service_api_dependency_routes_from_env(
                    node_app=node_app,
                    runtime=runtime,
                )
                await _apply_node_service_api_dependency_routes(
                    node_app=node_app,
                    runtime=runtime,
                    routes=resolution.routes,
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Node service API dependency route refresh retryable iteration "
                    "failed (pending_remote_provider_packages=%s "
                    "local_publication_pending=%s error=%s)",
                    ",".join(pending),
                    _committed_hosted_service_advertisement_bootstrap_pending(
                        runtime=runtime,
                    ),
                    exc,
                )
                continue
            pending = resolution.pending_remote_provider_package_names
            local_publication_pending = (
                _committed_hosted_service_advertisement_bootstrap_pending(
                    runtime=runtime,
                )
            )
            if not pending and not local_publication_pending:
                logger.info(
                    "Node service API dependency route refresh completed "
                    "(route_count=%s)",
                    len(resolution.routes),
                )
                return
        if pending or _committed_hosted_service_advertisement_bootstrap_pending(
            runtime=runtime,
        ):
            logger.warning(
                "Node service API dependency route refresh stopped with pending "
                "remote provider packages or local hosted-service publication "
                "(pending_remote_provider_packages=%s local_publication_pending=%s "
                "last_error=%s)",
                ",".join(pending),
                _committed_hosted_service_advertisement_bootstrap_pending(
                    runtime=runtime,
                ),
                last_error,
            )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning(
            "Node service API dependency route refresh failed "
            "(pending_remote_provider_packages=%s error=%s)",
            ",".join(pending),
            exc,
        )


async def _stop_node_service_api_dependency_route_refresh_task(
    task: asyncio.Task[None] | None,
) -> None:
    if task is None:
        return
    if task.done():
        with contextlib.suppress(asyncio.CancelledError, Exception):
            task.result()
        return
    task.cancel()
    await asyncio.gather(task, return_exceptions=True)


async def _hydrate_remote_service_api_provider_inputs_with_discovered_advertisements(
    *,
    node_app: object | None,
    remote_provider_inputs: tuple[_RemoteServiceApiProviderInput, ...],
    service_packages: tuple["ServicePackageLike", ...],
) -> tuple[_RemoteServiceApiProviderInput, ...]:
    if not remote_provider_inputs or node_app is None:
        return remote_provider_inputs

    package_by_name = {
        _hosted_service_package_name(package).casefold(): package
        for package in service_packages
    }
    hydrated: list[_RemoteServiceApiProviderInput] = []
    for provider_input in remote_provider_inputs:
        if provider_input.hosted_service_advertisement is not None:
            hydrated.append(provider_input)
            continue

        package_name = _required_text(
            provider_input.service_package_ref_payload.get("package_name"),
            "service_package_ref.package_name",
        )
        package = package_by_name.get(package_name.casefold())
        if package is None:
            hydrated.append(provider_input)
            continue

        advertisements = (
            await _discover_remote_hosted_service_advertisements_for_provider_input(
                node_app=node_app,
                provider_input=provider_input,
            )
        )
        advertisement = _select_remote_hosted_service_advertisement_for_service_package(
            provider_node_id=provider_input.provider_node_id,
            service_package=package,
            advertisements=advertisements,
        )
        hydrated.append(
            replace(
                provider_input,
                hosted_service_advertisement=advertisement,
            )
            if advertisement is not None
            else provider_input
        )
    return tuple(hydrated)


async def _discover_remote_hosted_service_advertisements_for_provider_input(
    *,
    node_app: object,
    provider_input: _RemoteServiceApiProviderInput,
) -> tuple[HostedServiceAdvertisement, ...]:
    try:
        return await discover_remote_hosted_service_advertisements_from_peer(
            network_app=cast(Any, node_app),
            peer=NetworkNodePeerEndpoint(
                node_id=provider_input.provider_node_id,
                base_url=provider_input.provider_node_base_url,
            ),
            route_connection_id=provider_input.route_connection_id,
            timeout_s=provider_input.request_timeout_s,
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning(
            "Remote hosted-service advertisement discovery failed "
            "(provider_node_id=%s provider_node_base_url=%s error=%s)",
            provider_input.provider_node_id,
            provider_input.provider_node_base_url,
            exc,
        )
        return ()


def _select_remote_hosted_service_advertisement_for_service_package(
    *,
    provider_node_id: UUID,
    service_package: "ServicePackageLike",
    advertisements: tuple[HostedServiceAdvertisement, ...],
) -> HostedServiceAdvertisement | None:
    package_name = _hosted_service_package_name(service_package)
    package_id = service_package.id
    matches = tuple(
        advertisement
        for advertisement in advertisements
        if getattr(advertisement, "service_package_id", None) == package_id
        and _hosted_service_advertisement_has_api_dispatch_route(advertisement)
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise RuntimeError(
            "Remote Node peer "
            f"{provider_node_id} advertised duplicate hosted ServicePackage "
            f"{package_name!r}"
        )
    return matches[0]


def _hosted_service_advertisement_has_api_dispatch_route(
    advertisement: HostedServiceAdvertisement,
) -> bool:
    return any(
        isinstance(endpoint_ref, str) and endpoint_ref.strip()
        for endpoint_ref in advertisement.endpoint_refs
    )


def _pending_remote_service_api_provider_package_names(
    *,
    remote_provider_inputs: tuple[_RemoteServiceApiProviderInput, ...],
) -> set[str]:
    names: set[str] = set()
    for provider_input in remote_provider_inputs:
        if provider_input.hosted_service_advertisement is not None:
            continue
        package_name = _clean_text(
            provider_input.service_package_ref_payload.get("package_name")
        )
        if package_name:
            names.add(package_name.casefold())
    return names


def _filter_remote_provider_inputs_for_consumers(
    *,
    remote_provider_inputs: tuple[_RemoteServiceApiProviderInput, ...],
    consumer_packages: tuple["ServicePackageLike", ...],
    provider_packages: tuple["ServicePackageLike", ...],
    service_packages: tuple["ServicePackageLike", ...],
) -> tuple[_RemoteServiceApiProviderInput, ...]:
    required_api_package_ids = {
        requirement.api_package_id
        for consumer in consumer_packages
        for requirement in tuple(getattr(consumer, "required_api_packages", ()))
    }
    unresolved_api_package_ids = required_api_package_ids - _provided_api_package_ids(
        packages=provider_packages,
    )
    relevant_provider_package_names = {
        _hosted_service_package_name(package).casefold()
        for package in service_packages
        if _provided_api_package_ids(packages=(package,)) & unresolved_api_package_ids
    }
    return tuple(
        provider_input
        for provider_input in remote_provider_inputs
        if _clean_text(
            provider_input.service_package_ref_payload.get("package_name")
        ).casefold()
        in relevant_provider_package_names
    )


def _pending_remote_provider_package_names_for_consumers(
    *,
    pending_remote_provider_package_names: set[str],
    consumer_packages: tuple["ServicePackageLike", ...],
    provider_packages: tuple["ServicePackageLike", ...],
    remote_provider_runtimes: tuple["NodeRemoteServiceApiProviderRuntime", ...],
    service_packages: tuple["ServicePackageLike", ...],
) -> set[str]:
    if not pending_remote_provider_package_names:
        return set()

    required_api_package_ids = {
        requirement.api_package_id
        for consumer in consumer_packages
        for requirement in tuple(getattr(consumer, "required_api_packages", ()))
    }
    available_api_package_ids = _provided_api_package_ids(packages=provider_packages)
    available_api_package_ids.update(
        _provided_api_package_ids(
            packages=tuple(
                provider_runtime.service_package
                for provider_runtime in remote_provider_runtimes
            )
        )
    )
    unresolved_api_package_ids = required_api_package_ids - available_api_package_ids
    if not unresolved_api_package_ids:
        return set()

    return {
        package_name
        for package in service_packages
        for package_name in (_hosted_service_package_name(package).casefold(),)
        if package_name in pending_remote_provider_package_names
        and _provided_api_package_ids(packages=(package,)) & unresolved_api_package_ids
    }


def _filter_consumer_packages_for_pending_remote_providers(
    *,
    consumer_packages: tuple["ServicePackageLike", ...],
    provider_packages: tuple["ServicePackageLike", ...],
    remote_provider_runtimes: tuple["NodeRemoteServiceApiProviderRuntime", ...],
    pending_remote_provider_package_names: set[str],
    service_packages: tuple["ServicePackageLike", ...],
) -> tuple["ServicePackageLike", ...]:
    if not pending_remote_provider_package_names:
        return consumer_packages

    available_api_package_ids = _provided_api_package_ids(packages=provider_packages)
    available_api_package_ids.update(
        _provided_api_package_ids(
            packages=tuple(
                provider_runtime.service_package
                for provider_runtime in remote_provider_runtimes
            )
        )
    )
    pending_api_package_ids = _provided_api_package_ids(
        packages=tuple(
            package
            for package in service_packages
            if _hosted_service_package_name(package).casefold()
            in pending_remote_provider_package_names
        )
    )
    filtered_consumers: list["ServicePackageLike"] = []
    for consumer in consumer_packages:
        requirements = tuple(getattr(consumer, "required_api_packages", ()))
        filtered_requirements = tuple(
            requirement
            for requirement in requirements
            if requirement.api_package_id not in pending_api_package_ids
            or requirement.api_package_id in available_api_package_ids
        )
        if not filtered_requirements:
            continue
        if len(filtered_requirements) == len(requirements):
            filtered_consumers.append(consumer)
            continue
        filtered_consumers.append(
            _ServicePackageRequiredApiFilter(
                service_package=consumer,
                filtered_required_api_packages=filtered_requirements,
            )
        )
    return tuple(filtered_consumers)


def _provided_api_package_ids(
    *,
    packages: tuple["ServicePackageLike", ...],
) -> set[UUID]:
    return {
        bridge.api_package_id
        for package in packages
        for bridge in tuple(getattr(package, "provided_api_packages", ()))
    }


def _service_api_dependency_authority_selectors_by_requirement_from_service_packages(
    *,
    service_packages: tuple["ServicePackageLike", ...],
) -> Mapping[tuple[UUID, UUID], ServiceApiRouteAuthoritySelector]:
    selectors: dict[tuple[UUID, UUID], ServiceApiRouteAuthoritySelector] = {}
    for service_package in service_packages:
        service_package_id = getattr(service_package, "id", None)
        if not isinstance(service_package_id, UUID):
            continue
        for dependency in _json_object_list(
            getattr(service_package, "dependencies", ()),
        ):
            if _clean_text(dependency.get("kind")) != "api_invocation":
                continue
            selector_payload = dependency.get("route_authority_selector")
            if selector_payload is None:
                continue
            if not isinstance(selector_payload, Mapping):
                raise RuntimeError(
                    "ServicePackage dependency route_authority_selector must be "
                    "an object."
                )
            selector = ServiceApiRouteAuthoritySelector.from_payload(selector_payload)
            if selector.is_empty:
                continue
            package_name = _clean_text(dependency.get("package_name"))
            if not package_name:
                raise RuntimeError(
                    "ServicePackage api_invocation dependency authority selector "
                    "requires package_name."
                )
            api_package_id = stable_api_package_id(name=package_name)
            key = (service_package_id, api_package_id)
            existing = selectors.get(key)
            if existing is not None and existing != selector:
                raise RuntimeError(
                    "Conflicting ServicePackage dependency authority selectors "
                    f"for consumer ServicePackage {service_package_id} and "
                    f"ApiPackage {api_package_id}: existing={existing.describe()} "
                    f"new={selector.describe()}."
                )
            selectors[key] = selector
    return selectors


def _json_object_list(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (bytes, str)):
        return ()
    return tuple(
        cast(Mapping[str, object], item) for item in value if isinstance(item, Mapping)
    )


async def stop_node_host_services(*, runtime: NodeHostServicesAssembly) -> None:
    await _stop_node_service_api_dependency_route_refresh_task(
        runtime.service_api_dependency_route_refresh_task
    )
    runtime.service_api_dependency_route_refresh_task = None
    await _stop_committed_hosted_service_advertisement_index_refresh_relay(
        runtime.committed_hosted_service_advertisement_index_refresh_relay
    )
    await _stop_hosted_service_lane_receipt_relay(
        runtime.hosted_service_lane_receipt_relay
    )
    await _stop_node_fanout_pull_service(runtime.fanout_pull_service)
    _stop_node_lane_head_receipt_relay(runtime.lane_head_receipt_relay)
    await _stop_fanout_service(runtime.fanout_service)
    await _stop_hosted_interface_runtimes(runtime.hosted_interface_runtimes)
    await _stop_hosted_service_runtimes(runtime.hosted_service_runtimes)


def _service_api_dependency_package_refs_payload_from_env() -> (
    tuple[Mapping[str, object], ...]
):
    raw_json = (
        os.environ.get(_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON_ENV) or ""
    ).strip()
    if not raw_json:
        return ()
    payload = json.loads(raw_json)
    if not isinstance(payload, list):
        raise RuntimeError(
            f"{_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON_ENV} must be a JSON list."
        )
    refs: list[Mapping[str, object]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError(
                f"{_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON_ENV} entries must be objects."
            )
        refs.append(item)
    return tuple(refs)


def _service_api_dependency_authority_selectors_by_api_package_id_from_env() -> (
    Mapping[UUID, ServiceApiRouteAuthoritySelector]
):
    raw_json = (
        os.environ.get(_NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON_ENV) or ""
    ).strip()
    if not raw_json:
        return {}
    payload = json.loads(raw_json)
    if not isinstance(payload, list):
        raise RuntimeError(
            f"{_NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON_ENV} "
            "must be a JSON list."
        )
    selectors: dict[UUID, ServiceApiRouteAuthoritySelector] = {}
    for item in payload:
        api_package_id, selector = (
            _service_api_dependency_authority_selector_entry_from_payload(item)
        )
        if selector.is_empty:
            continue
        if api_package_id in selectors:
            raise RuntimeError(
                "Duplicate Service API authority selector for ApiPackage "
                f"{api_package_id}."
            )
        selectors[api_package_id] = selector
    return selectors


def _service_api_dependency_authority_selector_entry_from_payload(
    payload: object,
) -> tuple[UUID, ServiceApiRouteAuthoritySelector]:
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            f"{_NODE_SERVICE_API_DEPENDENCY_AUTHORITY_SELECTORS_JSON_ENV} "
            "entries must be objects."
        )
    api_package_id = _authority_selector_api_package_id_from_payload(payload)
    selector_payload = payload.get("selector")
    if selector_payload is None:
        selector_payload = payload
    if not isinstance(selector_payload, Mapping):
        raise RuntimeError(
            "Service API authority selector entry selector must be an object."
        )
    return (
        api_package_id,
        ServiceApiRouteAuthoritySelector.from_payload(selector_payload),
    )


def _authority_selector_api_package_id_from_payload(
    payload: Mapping[str, object],
) -> UUID:
    raw_api_package_id = _clean_text(payload.get("api_package_id"))
    if raw_api_package_id:
        return UUID(raw_api_package_id)
    raw_api_package_name = _clean_text(payload.get("api_package_name"))
    if raw_api_package_name:
        return stable_api_package_id(name=raw_api_package_name)
    raise RuntimeError(
        "Service API authority selector entries require api_package_id or "
        "api_package_name."
    )


def _remote_service_api_provider_inputs_from_env() -> (
    tuple[_RemoteServiceApiProviderInput, ...]
):
    raw_json = (
        os.environ.get(_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON_ENV) or ""
    ).strip()
    if not raw_json:
        return ()
    payload = json.loads(raw_json)
    if not isinstance(payload, list):
        raise RuntimeError(
            f"{_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON_ENV} must be a JSON list."
        )
    return tuple(
        _remote_service_api_provider_input_from_payload(item) for item in payload
    )


def _remote_service_api_provider_input_from_payload(
    payload: object,
) -> _RemoteServiceApiProviderInput:
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            f"{_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON_ENV} entries must be objects."
        )
    service_package_ref = payload.get("service_package_ref")
    if not isinstance(service_package_ref, Mapping):
        raise RuntimeError(
            "Remote Service API provider input requires service_package_ref."
        )
    advertisement_payload = payload.get("hosted_service_advertisement")
    if advertisement_payload is not None and not isinstance(
        advertisement_payload, Mapping
    ):
        raise RuntimeError(
            "Remote Service API provider input hosted_service_advertisement "
            "must be an object when provided."
        )
    authority_payload = payload.get("authority")
    if authority_payload is not None and not isinstance(authority_payload, Mapping):
        raise RuntimeError(
            "Remote Service API provider input authority must be an object when provided."
        )
    return _RemoteServiceApiProviderInput(
        service_package_ref_payload=service_package_ref,
        provider_node_id=UUID(
            _required_text(payload.get("provider_node_id"), "provider_node_id")
        ),
        provider_node_base_url=_required_text(
            payload.get("provider_node_base_url"),
            "provider_node_base_url",
        ),
        route_connection_id=_optional_uuid(payload.get("route_connection_id")),
        request_timeout_s=_optional_float(payload.get("request_timeout_s")) or 5.0,
        hosted_service_advertisement=(
            _hosted_service_advertisement_from_payload(advertisement_payload)
            if advertisement_payload is not None
            else None
        ),
        authority=(
            ServiceApiRouteAuthority.from_payload(authority_payload)
            if isinstance(authority_payload, Mapping)
            else None
        ),
    )


def _hosted_service_advertisement_from_payload(
    payload: Mapping[str, object],
) -> HostedServiceAdvertisement:
    raw_endpoint_refs = payload.get("endpoint_refs")
    endpoint_refs = (
        [
            item.strip()
            for item in raw_endpoint_refs
            if isinstance(item, str) and item.strip()
        ]
        if isinstance(raw_endpoint_refs, list)
        else []
    )
    service_package_id = _optional_uuid(payload.get("service_package_id"))
    service_id = _optional_uuid(payload.get("service_id"))
    return HostedServiceAdvertisement(
        service_package_id=service_package_id,
        service_id=service_id,
        service_name=_required_text(payload.get("service_name"), "service_name"),
        endpoint_refs=endpoint_refs,
        host_id=_required_text(payload.get("host_id"), "host_id"),
        host_version=_clean_text(payload.get("host_version")),
        protocol_version=_required_text(
            payload.get("protocol_version"),
            "protocol_version",
        ),
        supports_stream_events=bool(payload.get("supports_stream_events", False)),
    )


def _build_remote_service_api_provider_runtimes(
    *,
    remote_provider_inputs: tuple[_RemoteServiceApiProviderInput, ...],
    service_packages: tuple["ServicePackageLike", ...],
) -> tuple["NodeRemoteServiceApiProviderRuntime", ...]:
    if not remote_provider_inputs:
        return ()
    from aware_node_service.host.service_api_dependency_resolution import (
        NodeRemoteServiceApiProviderRuntime,
    )

    package_by_name = {
        _hosted_service_package_name(package).casefold(): package
        for package in service_packages
    }
    runtimes: list[NodeRemoteServiceApiProviderRuntime] = []
    consumer_node_id = network_node_manager.hosted_node_id
    for provider_input in remote_provider_inputs:
        if provider_input.hosted_service_advertisement is None:
            continue
        package_name = _required_text(
            provider_input.service_package_ref_payload.get("package_name"),
            "service_package_ref.package_name",
        )
        package = package_by_name.get(package_name.casefold())
        if package is None:
            raise RuntimeError(
                "Remote Service API provider package ref did not resolve to "
                f"ServicePackage truth: {package_name!r}"
            )
        runtimes.append(
            NodeRemoteServiceApiProviderRuntime(
                service_package=package,
                runtime=_RemoteServiceApiProviderRuntime(
                    consumer_node_id=consumer_node_id,
                    provider_node_id=provider_input.provider_node_id,
                    provider_node_base_url=provider_input.provider_node_base_url,
                    route_connection_id=provider_input.route_connection_id
                    or stable_network_node_peer_id(
                        source_peer_node_id=consumer_node_id,
                        target_peer_node_id=provider_input.provider_node_id,
                    ),
                    request_timeout_s=provider_input.request_timeout_s,
                    advertisement=provider_input.hosted_service_advertisement,
                    authority=provider_input.authority,
                ),
            )
        )
    return tuple(runtimes)


async def _resolve_service_packages_for_api_dependency_routes(
    *,
    package_refs_payload: tuple[Mapping[str, object], ...],
    prepared_service_package_catalog: tuple["ServicePackageLike", ...] = (),
) -> tuple["ServicePackageLike", ...]:
    if _service_api_dependency_package_refs_are_prepared_payloads(
        package_refs_payload=package_refs_payload,
    ):
        return _resolve_prepared_service_packages_for_routes(
            package_refs_payload=package_refs_payload,
        )

    package_refs = tuple(
        _service_runtime_package_ref_from_payload(payload)
        for payload in package_refs_payload
    )
    if not package_refs:
        return ()
    if _service_api_dependency_package_refs_are_direct_manifest_refs(
        package_refs=package_refs,
    ):
        raise RuntimeError(
            "Node service API dependency route binding no longer accepts direct "
            "manifest ServicePackage refs. Local-manifest producers must parse "
            "aware.service.toml before runtime handoff and provide prepared "
            "service package route inputs; artifact producers must provide "
            "committed semantic refs."
        )
    if _service_api_dependency_package_refs_are_local_catalog_refs(
        package_refs=package_refs,
    ):
        return _resolve_service_packages_from_prepared_catalog_for_routes(
            package_refs=package_refs,
            prepared_service_package_catalog=prepared_service_package_catalog,
        )
    root = _service_api_dependency_materialized_workspace_root()
    if root is None:
        raise RuntimeError(
            "Node service API dependency route binding requires "
            f"{_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV} for committed "
            "ServicePackage refs."
        )
    resolved_refs = await _resolve_committed_service_runtime_package_refs_for_routes(
        package_refs=package_refs,
        materialized_workspace_root=root,
    )
    service_packages: list["ServicePackageLike"] = []
    for resolved in resolved_refs:
        service_package = getattr(resolved, "service_package", None)
        if service_package is None:
            raise RuntimeError(
                "Node service API dependency route binding resolved a "
                "ServicePackage ref without service_package ontology truth: "
                f"{getattr(resolved, 'package_name', '<unknown>')!r}"
            )
        service_packages.append(cast("ServicePackageLike", service_package))
    return tuple(service_packages)


def _service_api_dependency_package_refs_are_local_catalog_refs(
    *,
    package_refs: tuple["ServiceRuntimePackageRef", ...],
) -> bool:
    catalog_refs = tuple(
        package_ref
        for package_ref in package_refs
        if _clean_text(package_ref.manifest_path) is None
        and not _service_runtime_package_ref_has_committed_coordinates(package_ref)
    )
    if not catalog_refs:
        return False
    if len(catalog_refs) != len(package_refs):
        raise RuntimeError(
            "Node service API dependency route binding cannot mix local "
            "ServicePackage catalog refs with committed or direct manifest refs."
        )
    return True


def _resolve_service_packages_from_prepared_catalog_for_routes(
    *,
    package_refs: tuple["ServiceRuntimePackageRef", ...],
    prepared_service_package_catalog: tuple["ServicePackageLike", ...],
) -> tuple["ServicePackageLike", ...]:
    package_by_name: dict[str, ServicePackageLike] = {}
    for package in prepared_service_package_catalog:
        package_name = _hosted_service_package_name(package)
        package_key = package_name.casefold()
        existing = package_by_name.get(package_key)
        if existing is not None and existing is not package:
            raise RuntimeError(
                "Prepared ServicePackage route catalog contains duplicate "
                f"package name: {package_name!r}"
            )
        package_by_name[package_key] = package
    if not package_by_name:
        raise RuntimeError(
            "Node service API dependency route binding requires prepared "
            "ServicePackage route inputs for local catalog refs."
        )

    service_packages: list["ServicePackageLike"] = []
    for package_ref in package_refs:
        package_name = _required_text(package_ref.package_name, "package_name")
        package = package_by_name.get(package_name.casefold())
        if package is None:
            raise RuntimeError(
                "Node service API dependency route binding could not resolve "
                f"local ServicePackage catalog ref: {package_name!r}"
            )
        service_packages.append(package)
    return tuple(service_packages)


def _service_api_dependency_package_refs_are_prepared_payloads(
    *,
    package_refs_payload: tuple[Mapping[str, object], ...],
) -> bool:
    prepared_payloads = tuple(
        payload
        for payload in package_refs_payload
        if _service_api_dependency_package_ref_is_prepared_payload(payload)
    )
    if not prepared_payloads:
        return False
    if len(prepared_payloads) != len(package_refs_payload):
        raise RuntimeError(
            "Node service API dependency route binding cannot mix prepared "
            "service package route inputs with committed or direct manifest refs."
        )
    direct_manifest_payloads = tuple(
        payload
        for payload in prepared_payloads
        if _clean_text(payload.get("manifest_path")) is not None
    )
    if direct_manifest_payloads:
        raise RuntimeError(
            "Prepared Node service API dependency route inputs must not include "
            "manifest_path; source TOML parsing is producer-only."
        )
    return True


def _service_api_dependency_package_ref_is_prepared_payload(
    payload: Mapping[str, object],
) -> bool:
    return any(
        key in payload
        for key in ("provided_api_packages", "required_api_packages", "dependencies")
    )


def _resolve_prepared_service_packages_for_routes(
    *,
    package_refs_payload: tuple[Mapping[str, object], ...],
) -> tuple["ServicePackageLike", ...]:
    return tuple(
        _prepared_service_package_for_routes(payload=payload)
        for payload in package_refs_payload
    )


def _prepared_service_package_for_routes(
    *,
    payload: Mapping[str, object],
) -> _PreparedServicePackage:
    package_name = _required_text(payload.get("package_name"), "package_name")
    package_id = _prepared_service_package_id(
        payload=payload,
        package_name=package_name,
    )
    dependencies = _prepared_dependencies_from_payload(payload.get("dependencies"))
    return _PreparedServicePackage(
        id=package_id,
        name=package_name,
        provided_api_packages=_prepared_api_package_bridges_from_payload(
            payload.get("provided_api_packages"),
            field_name="provided_api_packages",
        ),
        required_api_packages=_prepared_api_package_bridges_from_payload(
            payload.get("required_api_packages"),
            field_name="required_api_packages",
        ),
        dependencies=dependencies,
    )


def _prepared_service_package_id(
    *,
    payload: Mapping[str, object],
    package_name: str,
) -> UUID:
    for key in ("service_package_id", "semantic_package_id"):
        raw_value = _clean_text(payload.get(key))
        if raw_value:
            return UUID(raw_value)
    return stable_service_package_id(name=package_name)


def _prepared_dependencies_from_payload(
    payload: object,
) -> tuple[Mapping[str, object], ...]:
    if payload is None:
        return ()
    if not isinstance(payload, Sequence) or isinstance(payload, (bytes, str)):
        raise RuntimeError(
            "Prepared service package route input dependencies must be a JSON list."
        )
    dependencies: list[Mapping[str, object]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError(
                "Prepared service package route input dependency entries must "
                "be objects."
            )
        dependencies.append(cast(Mapping[str, object], item))
    return tuple(dependencies)


def _prepared_api_package_bridges_from_payload(
    payload: object,
    *,
    field_name: str,
) -> tuple[_PreparedServiceApiPackageBridge, ...]:
    if payload is None:
        return ()
    if not isinstance(payload, Sequence) or isinstance(payload, (bytes, str)):
        raise RuntimeError(
            f"Prepared service package route input {field_name} must be a JSON list."
        )
    bridges: list[_PreparedServiceApiPackageBridge] = []
    for item in payload:
        if not isinstance(item, Mapping):
            raise RuntimeError(
                f"Prepared service package route input {field_name} entries "
                "must be objects."
            )
        bridges.append(
            _PreparedServiceApiPackageBridge(
                api_package_id=_prepared_api_package_id_from_payload(item),
                description=_clean_text(item.get("description")),
            )
        )
    return tuple(bridges)


def _prepared_api_package_id_from_payload(payload: Mapping[str, object]) -> UUID:
    raw_api_package_id = _clean_text(payload.get("api_package_id"))
    if raw_api_package_id:
        return UUID(raw_api_package_id)
    raw_api_package_name = _clean_text(payload.get("api_package_name"))
    if raw_api_package_name is None:
        raw_api_package_name = _clean_text(payload.get("package_name"))
    if raw_api_package_name:
        return stable_api_package_id(name=raw_api_package_name)
    raise RuntimeError(
        "Prepared service package route input API package entries require "
        "api_package_id or api_package_name."
    )


def _service_api_dependency_package_refs_are_direct_manifest_refs(
    *,
    package_refs: tuple["ServiceRuntimePackageRef", ...],
) -> bool:
    direct_refs = tuple(
        package_ref
        for package_ref in package_refs
        if _clean_text(package_ref.manifest_path) is not None
        and not _service_runtime_package_ref_has_committed_coordinates(package_ref)
    )
    if not direct_refs:
        return False
    if len(direct_refs) != len(package_refs):
        raise RuntimeError(
            "Node service API dependency route binding cannot mix direct "
            "manifest ServicePackage refs with committed semantic refs."
        )
    return True


def _service_runtime_package_ref_has_committed_coordinates(
    package_ref: "ServiceRuntimePackageRef",
) -> bool:
    has_oig_commit = _clean_text(package_ref.semantic_object_instance_graph_commit_id)
    has_branch = _clean_text(package_ref.semantic_branch_id)
    has_legacy_head = _clean_text(package_ref.semantic_head_commit_id)
    return bool(has_oig_commit or (has_branch and has_legacy_head))


async def _resolve_committed_service_runtime_package_refs_for_routes(
    *,
    package_refs: tuple["ServiceRuntimePackageRef", ...],
    materialized_workspace_root: Path,
) -> tuple["ResolvedServiceRuntimePackageRef", ...]:
    from aware_service_runtime.package_ref_resolution import (
        resolve_committed_service_runtime_package_refs,
    )

    return await resolve_committed_service_runtime_package_refs(
        index=_graph_catalog(
            await _resolve_service_graph_context_for_routes(
                materialized_workspace_root=materialized_workspace_root,
            )
        ),
        package_refs=package_refs,
        materialized_workspace_root=materialized_workspace_root,
    )


async def _resolve_service_graph_context_for_routes(
    *,
    materialized_workspace_root: Path,
) -> object:
    return _read_node_meta_runtime_context(
        materialized_workspace_root=materialized_workspace_root,
        required_projection_names=("ServicePackage",),
        composite_name="Aware Node Service Route Graph Context",
    )


def _service_runtime_package_ref_from_payload(
    payload: Mapping[str, object],
) -> "ServiceRuntimePackageRef":
    from aware_service_runtime.package_ref_resolution import ServiceRuntimePackageRef

    package_kind = _clean_text(payload.get("package_kind"))
    if package_kind == "service_package":
        package_kind = "service"
    return ServiceRuntimePackageRef(
        family_key=_clean_text(payload.get("family_key")) or "service",
        package_kind=package_kind or "service",
        package_name=_required_text(payload.get("package_name"), "package_name"),
        manifest_path=_clean_text(payload.get("manifest_path")),
        workspace_package_id=_clean_text(payload.get("workspace_package_id")),
        semantic_package_id=_clean_text(payload.get("semantic_package_id")),
        semantic_object_instance_graph_commit_id=_clean_text(
            payload.get("semantic_object_instance_graph_commit_id")
        ),
        semantic_head_commit_id=_clean_text(payload.get("semantic_head_commit_id")),
        semantic_branch_id=_clean_text(payload.get("semantic_branch_id")),
        semantic_root_kind=_clean_text(payload.get("semantic_root_kind")),
        semantic_root_id=_clean_text(payload.get("semantic_root_id")),
        semantic_root_object_instance_graph_commit_id=_clean_text(
            payload.get("semantic_root_object_instance_graph_commit_id")
        ),
        source_code_package_id=_clean_text(payload.get("source_code_package_id")),
    )


def _service_api_dependency_materialized_workspace_root() -> Path | None:
    raw_value = _clean_text(
        os.environ.get(_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV)
    )
    if raw_value is None:
        return None
    return Path(raw_value).expanduser().resolve()


async def _configure_in_process_environment_service_api_dependency_routes(
    *,
    node_app: object,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
) -> bool:
    del node_app
    try:
        from aware_network_service_dto.comms.models.network import NetworkAppType
        from aware_comms.app.registry import app_registry
    except Exception:
        return False
    try:
        environment_app = app_registry.get_app(NetworkAppType.environment.value)
    except Exception:
        return False

    configure = getattr(
        environment_app,
        "configure_service_api_dependency_routes",
        None,
    )
    if not callable(configure):
        return False
    configure(routes)
    start = getattr(environment_app, "start_meta_topology_subscriber", None)
    if callable(start):
        result = start()
        if asyncio.iscoroutine(result):
            await result
    return True


async def _configure_hosted_service_api_dependency_routes(
    *,
    runtime: NodeHostServicesAssembly,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
) -> int:
    configured_count = 0
    for hosted_runtime in runtime.hosted_service_runtimes:
        consumer_routes = _service_api_dependency_routes_for_hosted_runtime(
            hosted_runtime=hosted_runtime,
            routes=routes,
        )
        response = await _send_service_api_dependency_routes_to_hosted_service_runtime(
            runtime=hosted_runtime,
            routes=consumer_routes,
        )
        if (
            not isinstance(
                response,
                ConfigureServiceApiDependencyRoutesHostControlResponse,
            )
            or response.status is not RequestStatus.succeeded
        ):
            raise RuntimeError(
                "ServiceHost route install failed "
                f"(bootstrap_config={hosted_runtime.bootstrap_config_path} "
                f"error={getattr(response, 'error', None) or 'unknown error'})"
            )
        configured_count += 1
    if runtime.hosted_service_runtimes:
        logger.info(
            "Node installed service API dependency routes into hosted ServiceHosts "
            "(service_host_count=%s route_count=%s)",
            configured_count,
            len(routes),
        )
    return configured_count


def _service_api_dependency_routes_for_hosted_runtime(
    *,
    hosted_runtime: NodeHostedServiceRuntime,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
    package_names = {
        package_name.strip().casefold()
        for package_name in hosted_runtime.implementation_package_names
        if package_name.strip()
    }
    if not package_names:
        return ()
    return tuple(
        route
        for route in routes
        if route.consumer_service_package_name.strip().casefold() in package_names
    )


async def _send_service_api_dependency_routes_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
) -> ServiceHostControlResponse:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    return await client.send_host_control_request(
        request=ConfigureServiceApiDependencyRoutesHostControlRequest(
            routes=cast(JsonArray, service_api_dependency_routes_to_payload(routes)),
        ),
        timeout_s=runtime.request_timeout_s,
    )


async def _configure_hosted_environment_service_api_dependency_routes(
    *,
    node_app: object,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
) -> bool:
    if not any(
        route.consumer_service_package_name.strip().casefold()
        == "aware-environment-service"
        for route in routes
    ):
        return False

    hosted_environment_service = getattr(
        node_app,
        "_node_hosted_environment_service",
        None,
    )
    configure = getattr(
        hosted_environment_service,
        "configure_service_api_dependency_routes",
        None,
    )
    if not callable(configure):
        return False

    route_configurer = cast(
        _HostedEnvironmentRouteConfigurer,
        hosted_environment_service,
    )
    records = environment_registry.list_records()
    if not records:
        raise RuntimeError(
            "Node resolved service API dependency routes for "
            "aware-environment-service but no hosted Environment is registered."
        )

    node_id = network_node_manager.hosted_node_id
    timeout_s = float(
        os.environ.get("AWARE_NODE_ENVIRONMENT_ROUTE_CONFIG_TIMEOUT_S", "15.0")
    )
    configured_count = 0
    for record in records:
        response = await route_configurer.configure_service_api_dependency_routes(
            environment_id=record.environment_id,
            node_id=node_id,
            routes=routes,
            timeout_s=timeout_s,
        )
        status = str(getattr(response, "status", "") or "").strip().casefold()
        if status != "succeeded":
            error = str(getattr(response, "error", "") or "").strip()
            raise RuntimeError(
                "Hosted Environment rejected service API dependency route "
                f"configuration for environment_id={record.environment_id}"
                + (f": {error}" if error else "")
            )
        route_count = getattr(response, "route_count", None)
        if route_count is not None and int(route_count) < len(routes):
            raise RuntimeError(
                "Hosted Environment accepted only a partial service API dependency "
                "route configuration for environment_id="
                f"{record.environment_id}: accepted={route_count} expected={len(routes)}"
            )
        configured_count += 1
    logger.info(
        "Node installed service API dependency routes into hosted Environments "
        "(environment_count=%s route_count=%s)",
        configured_count,
        len(routes),
    )
    return configured_count > 0


def _service_api_dependency_routes_for_consumer_package(
    *,
    routes: tuple["NodeServiceApiDependencyRouteDescriptor", ...],
    consumer_service_package_name: str,
) -> tuple["NodeServiceApiDependencyRouteDescriptor", ...]:
    consumer_name = consumer_service_package_name.strip().casefold()
    if not consumer_name:
        return ()
    return tuple(
        route
        for route in routes
        if route.consumer_service_package_name.strip().casefold() == consumer_name
    )


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _graph_catalog(graph_context: object) -> object:
    catalog = getattr(graph_context, "index", None)
    if catalog is not None:
        return catalog
    return graph_context


def _required_text(value: object, label: str) -> str:
    text = _clean_text(value)
    if text is None:
        raise RuntimeError(
            "Node service API dependency package ref requires " f"{label}."
        )
    return text


def _optional_uuid(value: object) -> UUID | None:
    text = _clean_text(value)
    return UUID(text) if text is not None else None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    if not isinstance(value, int | float):
        raise RuntimeError("Node service API dependency route timeout must be numeric.")
    return float(value)


def _float_env(env_name: str, *, default: float) -> float:
    raw_value = _clean_text(os.environ.get(env_name))
    if raw_value is None:
        return default
    try:
        value = float(raw_value)
    except ValueError:
        return default
    return value if value > 0 else default


async def _start_hosted_interface_runtimes(
    *,
    config: NodeHostedInterfaceSupervisorConfig,
) -> tuple[NodeHostedInterfaceRuntime, ...]:
    if not config.enabled:
        return ()
    runtimes: list[NodeHostedInterfaceRuntime] = []
    try:
        for bootstrap_config_path in config.interface_bootstrap_config_paths:
            runtime = await _start_hosted_interface_runtime(
                bootstrap_config_path=bootstrap_config_path,
                launch_command=config.launch_command,
                ready_timeout_s=config.ready_timeout_s,
            )
            runtimes.append(runtime)
    except Exception:
        await _stop_hosted_interface_runtimes(tuple(runtimes))
        raise
    return tuple(runtimes)


async def _start_hosted_interface_runtime(
    *,
    bootstrap_config_path: Path,
    launch_command: tuple[str, ...],
    ready_timeout_s: float,
) -> NodeHostedInterfaceRuntime:
    bootstrap = _load_interface_host_bootstrap_config(bootstrap_config_path)
    socket_path = _hosted_interface_socket_path(bootstrap=bootstrap)
    env = _build_hosted_interface_subprocess_env(
        bootstrap_config_path=bootstrap_config_path
    )
    process = await asyncio.create_subprocess_exec(
        *launch_command,
        env=env,
    )
    hosted_process = cast(_HostedServiceProcess, process)
    try:
        ping = await wait_for_hosted_interface_control_ready(
            socket_path=socket_path,
            process=hosted_process,
            timeout_s=ready_timeout_s,
        )
    except Exception:
        await _stop_hosted_service_process_handle(hosted_process)
        raise
    runtime = NodeHostedInterfaceRuntime(
        bootstrap_config_path=bootstrap_config_path,
        socket_path=socket_path,
        process=hosted_process,
        ping=ping,
        launch_command=launch_command,
        ready_timeout_s=ready_timeout_s,
    )
    logger.info(
        "Node hosted Interface ready " "(bootstrap_config=%s socket=%s pid=%s)",
        bootstrap_config_path.as_posix(),
        runtime.socket_path.as_posix(),
        process.pid,
    )
    return runtime


async def wait_for_hosted_interface_control_ready(
    *,
    socket_path: Path,
    process: _HostedServiceProcess,
    timeout_s: float,
) -> object:
    deadline = monotonic() + max(timeout_s, 0.5)
    last_error: Exception | None = None
    while monotonic() < deadline:
        if process.returncode is not None:
            raise RuntimeError(
                "Hosted Interface exited before completing control-plane readiness "
                f"(socket={socket_path} returncode={process.returncode})"
            )
        try:
            return await _build_interface_control_client(socket_path=socket_path).ping()
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
    detail = f": {last_error}" if last_error is not None else ""
    raise TimeoutError(
        "Hosted Interface control plane did not become ready "
        f"(socket={socket_path} timeout_s={timeout_s:.1f}){detail}"
    )


async def _start_hosted_service_runtimes(
    *,
    config: NodeHostedServiceSupervisorConfig,
) -> tuple[NodeHostedServiceRuntime, ...]:
    if not config.enabled:
        return ()
    runtimes: list[NodeHostedServiceRuntime] = []
    try:
        for bootstrap_config_path in config.service_bootstrap_config_paths:
            runtime = await _start_hosted_service_runtime(
                bootstrap_config_path=bootstrap_config_path,
                launch_command=config.launch_command,
                ready_timeout_s=config.ready_timeout_s,
                request_timeout_s=config.request_timeout_s,
            )
            runtimes.append(runtime)
    except Exception:
        await _stop_hosted_service_runtimes(tuple(runtimes))
        raise
    return tuple(runtimes)


async def _start_hosted_service_runtime(
    *,
    bootstrap_config_path: Path,
    launch_command: tuple[str, ...],
    ready_timeout_s: float,
    request_timeout_s: float,
) -> NodeHostedServiceRuntime:
    bootstrap = _load_service_host_bootstrap_config(bootstrap_config_path)
    env = _build_hosted_service_subprocess_env(
        bootstrap_config_path=bootstrap_config_path,
        bootstrap=bootstrap,
    )
    process = await asyncio.create_subprocess_exec(
        *launch_command,
        env=env,
    )
    hosted_process = cast(_HostedServiceProcess, process)
    try:
        handshake = await wait_for_hosted_service_handshake_ready(
            socket_path=bootstrap.ipc.socket_path,
            process=hosted_process,
            timeout_s=ready_timeout_s,
            allow_awaiting_dependency_routes=True,
        )
    except Exception:
        await _stop_hosted_service_process_handle(hosted_process)
        raise
    runtime = NodeHostedServiceRuntime(
        bootstrap_config_path=bootstrap_config_path,
        socket_path=bootstrap.ipc.socket_path,
        process=hosted_process,
        request_timeout_s=request_timeout_s,
        handshake=handshake,
        ready_timeout_s=ready_timeout_s,
        implementation_service_package_id=(
            _extract_implementation_service_package_id_from_bootstrap(
                bootstrap=bootstrap
            )
        ),
        implementation_package_names=_extract_implementation_package_names_from_bootstrap(
            bootstrap=bootstrap
        ),
        routable_service_names=_extract_routable_service_names_from_handshake(
            handshake=handshake
        ),
        routable_endpoint_refs_by_service=_extract_routable_endpoint_refs_by_service_from_handshake(
            handshake=handshake
        ),
        lane_subscriptions=_extract_lane_subscriptions_from_handshake(
            handshake=handshake
        ),
    )
    logger.info(
        "Node hosted Service prepared "
        "(bootstrap_config=%s socket=%s pid=%s host_id=%s protocol_version=%s)",
        bootstrap_config_path.as_posix(),
        runtime.socket_path.as_posix(),
        process.pid,
        runtime.handshake.host_id,
        runtime.handshake.protocol_version,
    )
    return runtime


async def wait_for_hosted_service_socket_ready(
    *,
    socket_path: Path,
    process: _HostedServiceProcess,
    timeout_s: float,
) -> None:
    deadline = monotonic() + max(timeout_s, 0.5)
    last_error: Exception | None = None
    while monotonic() < deadline:
        if process.returncode is not None:
            raise RuntimeError(
                "Hosted Service exited before becoming ready "
                f"(socket={socket_path} returncode={process.returncode})"
            )
        try:
            reader, writer = await asyncio.open_unix_connection(path=str(socket_path))
            writer.close()
            await writer.wait_closed()
            _ = reader
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
    detail = f": {last_error}" if last_error is not None else ""
    raise TimeoutError(
        "Hosted Service socket did not become ready "
        f"(socket={socket_path} timeout_s={timeout_s:.1f}){detail}"
    )


async def wait_for_hosted_service_handshake_ready(
    *,
    socket_path: Path,
    process: _HostedServiceProcess,
    timeout_s: float,
    allow_awaiting_dependency_routes: bool = False,
) -> ServiceHostHandshakeResponse:
    deadline = monotonic() + max(timeout_s, 0.5)
    last_error: Exception | None = None
    last_handshake: ServiceHostHandshakeResponse | None = None
    handshake_request = ServiceHostHandshakeRequest(
        supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
    )
    while monotonic() < deadline:
        if process.returncode is not None:
            raise RuntimeError(
                "Hosted Service exited before completing handshake readiness "
                f"(socket={socket_path} returncode={process.returncode})"
            )
        try:
            handshake = await _build_hosted_service_duplex_client(
                socket_path=socket_path
            ).send_handshake(
                request=handshake_request,
                timeout_s=min(1.0, max(deadline - monotonic(), 0.1)),
            )
            _validate_hosted_service_handshake(
                handshake=handshake,
                expected_socket_path=socket_path,
            )
            last_handshake = handshake
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(0.2)
            continue
        if (
            handshake.readiness.is_ready
            and handshake.readiness.status is ServiceHostBootstrapStatus.ready
        ):
            return handshake
        if (
            allow_awaiting_dependency_routes
            and handshake.readiness.status
            is ServiceHostBootstrapStatus.awaiting_dependency_routes
        ):
            return handshake
        if handshake.readiness.status is ServiceHostBootstrapStatus.failed:
            raise RuntimeError(
                "Hosted Service handshake failed before becoming ready "
                f"(socket={socket_path} reason={handshake.readiness.reason!r})"
            )
        await asyncio.sleep(0.2)
    if last_handshake is not None:
        raise TimeoutError(
            "Hosted Service handshake did not become ready "
            f"(socket={socket_path} timeout_s={timeout_s:.1f} "
            f"status={last_handshake.readiness.status.value} "
            f"reason={last_handshake.readiness.reason!r})"
        )
    detail = f": {last_error}" if last_error is not None else ""
    raise TimeoutError(
        "Hosted Service handshake did not complete "
        f"(socket={socket_path} timeout_s={timeout_s:.1f}){detail}"
    )


def _validate_hosted_service_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
    expected_socket_path: Path,
) -> None:
    if handshake.protocol_version != SERVICE_HOST_PROTOCOL_VERSION:
        raise RuntimeError(
            "Hosted Service reported unsupported protocol version "
            f"(expected={SERVICE_HOST_PROTOCOL_VERSION!r} actual={handshake.protocol_version!r})"
        )
    if handshake.endpoint.transport is not DuplexIpcTransportKind.UNIX_SOCKET:
        raise RuntimeError(
            "Hosted Service handshake returned unexpected transport "
            f"(expected=unix_socket actual={handshake.endpoint.transport.value})"
        )
    actual_socket_path = (
        Path(handshake.endpoint.socket_path or "").expanduser().resolve()
    )
    expected_socket_path = expected_socket_path.resolve()
    if actual_socket_path != expected_socket_path:
        raise RuntimeError(
            "Hosted Service handshake returned mismatched socket path "
            f"(expected={expected_socket_path} actual={actual_socket_path})"
        )


async def _stop_fanout_service(fanout_service: object | None) -> None:
    stop = getattr(fanout_service, "stop", None)
    if callable(stop):
        stop()


def _has_local_environment_config_runtime_input(
    hosted_environment_service: object,
) -> bool:
    has_runtime_input = getattr(
        hosted_environment_service,
        "has_local_environment_config_runtime_input",
        None,
    )
    if not callable(has_runtime_input):
        return False
    return bool(has_runtime_input())


def _start_node_lane_head_receipt_relay(*, node_app: object) -> object | None:
    hosted_environment_service = getattr(
        node_app, "_node_hosted_environment_service", None
    )
    if hosted_environment_service is None:
        return None
    if not _has_local_environment_config_runtime_input(hosted_environment_service):
        logger.info(
            "Node lane-head receipt relay not started: no local EnvironmentConfig runtime input"
        )
        return None

    boot = hosted_environment_service.read_boot_environment_descriptor(
        node_id=network_node_manager.hosted_node_id
    )
    descriptor = boot.descriptor
    if descriptor is None:
        logger.warning(
            "Node lane-head receipt relay not started: boot environment descriptor unavailable "
            "(status=%s error=%s)",
            boot.response_status,
            boot.response_error or boot.network_error,
        )
        return None

    relay = start_local_meta_lane_head_receipt_relay()
    logger.info(
        "Node lane-head receipt relay started (environment_id=%s process_id=%s thread_id=%s)",
        descriptor.boot_environment_id,
        descriptor.process_id,
        descriptor.thread_id,
    )
    return relay


def _stop_node_lane_head_receipt_relay(
    lane_head_receipt_relay: object | None,
) -> None:
    if lane_head_receipt_relay is None:
        return
    lane_head_receipt_relay.stop()


def _start_node_fanout_pull_service(
    *,
    node_app: object,
    lane_head_receipt_relay: object | None,
) -> object | None:
    if lane_head_receipt_relay is None:
        return None

    network_router = getattr(node_app, "_network_router", None)
    if network_router is None:
        logger.warning(
            "Node fanout pull service not started: network router unavailable"
        )
        return None

    from aware_node_service.network.fanout_pull_service import NetworkFanoutPullService

    service = NetworkFanoutPullService(network_router=network_router)
    service.start()
    return service


async def _stop_node_fanout_pull_service(fanout_pull_service: object | None) -> None:
    stop = getattr(fanout_pull_service, "stop", None)
    if callable(stop):
        result = stop()
        if asyncio.iscoroutine(result):
            await result


def _start_hosted_service_lane_receipt_relay(
    *,
    hosted_service_runtimes: tuple[NodeHostedServiceRuntime, ...],
) -> object | None:
    if not any(runtime.lane_subscriptions for runtime in hosted_service_runtimes):
        return None
    relay = HostedServiceLaneReceiptRelay(
        hosted_service_runtimes=hosted_service_runtimes,
    )
    relay.start()
    return relay


async def _stop_hosted_service_lane_receipt_relay(
    hosted_service_lane_receipt_relay: object | None,
) -> None:
    stop = getattr(hosted_service_lane_receipt_relay, "stop", None)
    if callable(stop):
        result = stop()
        if asyncio.iscoroutine(result):
            await result


def _start_committed_hosted_service_advertisement_index_refresh_relay(
    *,
    node_app: object,
    runtime_registry: NodeHostServicesAssembly,
    targets: _BootNetworkNodeHostedServiceTargets | None,
) -> object | None:
    if targets is None:
        return None
    relay = CommittedHostedServiceAdvertisementIndexRefreshRelay(
        node_app=node_app,
        runtime_registry=runtime_registry,
        targets=targets,
    )
    relay.start()
    return relay


async def _stop_committed_hosted_service_advertisement_index_refresh_relay(
    relay: object | None,
) -> None:
    stop = getattr(relay, "stop", None)
    if callable(stop):
        result = stop()
        if asyncio.iscoroutine(result):
            await result


async def _stop_hosted_interface_runtimes(
    runtimes: tuple[NodeHostedInterfaceRuntime, ...],
) -> None:
    for runtime in reversed(runtimes):
        await _stop_hosted_interface_process(runtime)


async def _stop_hosted_interface_process(runtime: NodeHostedInterfaceRuntime) -> None:
    await _stop_hosted_service_process_handle(runtime.process)


async def _stop_hosted_service_runtimes(
    runtimes: tuple[NodeHostedServiceRuntime, ...],
) -> None:
    for runtime in reversed(runtimes):
        await _stop_hosted_service_process(runtime)


async def _stop_hosted_service_process(runtime: NodeHostedServiceRuntime) -> None:
    await _stop_hosted_service_process_handle(runtime.process)


async def _stop_hosted_service_process_handle(process: _HostedServiceProcess) -> None:
    if process.returncode is not None:
        return
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5.0)
    except asyncio.TimeoutError:
        process.kill()
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(process.wait(), timeout=5.0)


async def route_request_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    request: ServiceOperationRequest,
    timeout_s: float | None = None,
) -> ServiceOperationResponse:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    return await client.send_request(
        request=request,
        timeout_s=runtime.request_timeout_s if timeout_s is None else timeout_s,
    )


async def route_api_request_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    request: ServiceHostApiIngressRequest,
    timeout_s: float | None = None,
) -> ServiceOperationResponse:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    return await client.send_api_ingress_request(
        request=request,
        timeout_s=runtime.request_timeout_s if timeout_s is None else timeout_s,
    )


def open_api_ingress_stream_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    request: ServiceHostApiIngressRequest,
    timeout_s: float | None = None,
) -> ServiceHostDuplexRequestHandle:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    return client.open_api_ingress_stream(
        request=request,
        timeout_s=timeout_s,
    )


def open_request_stream_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    request: ServiceOperationRequest,
    timeout_s: float | None = None,
) -> ServiceHostDuplexRequestHandle:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    return client.open_request_stream(
        request=request,
        timeout_s=timeout_s,
    )


async def _send_lane_commit_receipt_to_hosted_service_runtime(
    *,
    runtime: NodeHostedServiceRuntime,
    receipt: LaneCommitReceiptNotification,
) -> None:
    client = _build_hosted_service_duplex_client(socket_path=runtime.socket_path)
    await client.send_lane_commit_receipt_notification(receipt=receipt)


async def route_request_to_registered_hosted_service(
    *,
    runtime: NodeHostServicesAssembly,
    bootstrap_config_path: str | Path,
    request: ServiceOperationRequest,
    timeout_s: float | None = None,
) -> ServiceOperationResponse:
    hosted_runtime = runtime.resolve_hosted_service_runtime(
        bootstrap_config_path=bootstrap_config_path
    )
    return await route_request_to_hosted_service_runtime(
        runtime=hosted_runtime,
        request=request,
        timeout_s=timeout_s,
    )


def require_node_host_services_runtime(*, node_app: object) -> NodeHostServicesAssembly:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if runtime is None:
        raise RuntimeError(
            "Node hosted Service runtime assembly is not available on this node app"
        )
    return cast(NodeHostServicesAssembly, runtime)


async def discover_node_hosted_service_advertisements(
    *,
    node_app: object,
) -> tuple[HostedServiceAdvertisement, ...]:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if isinstance(runtime, NodeHostServicesAssembly):
        committed = runtime.discover_committed_hosted_service_advertisements()
        if committed is not None:
            return committed

    targets = await _read_network_node_hosted_service_targets(node_app=node_app)
    if targets is None:
        return ()

    advertisements = await _read_committed_node_hosted_service_advertisements(
        node_app=node_app,
        targets=targets,
    )
    return advertisements


async def _read_committed_node_hosted_service_advertisements(
    *,
    node_app: object,
    targets: _BootNetworkNodeHostedServiceTargets,
) -> tuple[HostedServiceAdvertisement, ...]:
    route_to_environment_service = (
        targets.route_to_environment_service
        or _require_node_environment_route(node_app=node_app)
    )
    await _ensure_local_network_node_lane_commits(
        route_to_environment_service=route_to_environment_service,
        targets=targets,
    )
    await _ensure_network_node_lane_projected_for_db_publication(
        targets=targets,
        mode=_network_node_publication_projection_cache_mode(),
    )
    snapshot = await _materialize_committed_network_node_lane_snapshot(
        targets=targets,
    )
    advertisements = _parse_materialized_network_node_hosted_service_advertisements(
        snapshot=snapshot,
    )
    logger.info(
        "Materialized committed NetworkNode hosted-service advertisements "
        "(branch_id=%s commit_id=%s graph_hash_post=%s instance_count=%s "
        "relationship_count=%s advertisement_count=%s)",
        targets.branch_id,
        targets.head_commit_id,
        targets.graph_hash_post,
        len(snapshot.get("class_instances", ()) or ()),
        len(snapshot.get("class_instance_relationships", ()) or ()),
        len(advertisements),
    )
    return advertisements


async def _ensure_local_network_node_lane_commits(
    *,
    route_to_environment_service,
    targets: _BootNetworkNodeHostedServiceTargets,
) -> _NetworkNodeReplicaWatermark:
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
        ObjectInstanceGraphCommit,
    )

    commit_store = build_local_meta_commit_store()
    local_head = await commit_store.head(
        branch_id=targets.branch_id,
        projection_hash=targets.projection_hash,
    )
    local_head_commit_id = _optional_uuid_from_mapping(local_head, "commit_id")
    if local_head_commit_id == targets.head_commit_id:
        logger.info(
            "NetworkNode committed lane already current locally "
            "(branch_id=%s commit_id=%s projection_hash=%s)",
            targets.branch_id,
            targets.head_commit_id,
            targets.projection_hash,
        )
        return _NetworkNodeReplicaWatermark(
            branch_id=targets.branch_id,
            projection_hash=targets.projection_hash,
            authority_head_commit_id=targets.head_commit_id,
            local_head_commit_id=targets.head_commit_id,
            previous_local_head_commit_id=local_head_commit_id,
            commits_applied=0,
        )

    commits: list[ObjectInstanceGraphCommit] = []
    current_commit_id: UUID | None = targets.head_commit_id
    found_local_head = local_head_commit_id is None
    max_commits = int(os.environ.get("AWARE_NODE_NETWORK_NODE_PULL_MAX_COMMITS", "256"))

    while current_commit_id is not None:
        commit = await _fetch_environment_object_instance_graph_commit(
            route_to_environment_service=route_to_environment_service,
            targets=targets,
            commit_id=current_commit_id,
        )
        commits.append(commit)
        parents = tuple(commit.commit.commit_parents)
        parent_commit_id = parents[0].parent_commit_id if len(parents) == 1 else None
        if (
            local_head_commit_id is not None
            and parent_commit_id == local_head_commit_id
        ):
            found_local_head = True
            break
        if parent_commit_id is None:
            break
        current_commit_id = parent_commit_id
        if len(commits) >= max_commits:
            raise RuntimeError(
                "NetworkNode hosted-service discovery pull exceeded "
                "AWARE_NODE_NETWORK_NODE_PULL_MAX_COMMITS "
                f"(branch_id={targets.branch_id} projection_hash={targets.projection_hash})"
            )

    if local_head_commit_id is not None and not found_local_head:
        raise RuntimeError(
            "NetworkNode hosted-service discovery cannot fast-forward local "
            "commit truth from Environment lane head "
            f"(branch_id={targets.branch_id} projection_hash={targets.projection_hash} "
            f"local_head={local_head_commit_id} remote_head={targets.head_commit_id})"
        )

    for commit in reversed(commits):
        await commit_store.append(
            branch_id=targets.branch_id,
            projection_hash=targets.projection_hash,
            commit=commit,
            root_object_id=commit.root_source_object_id,
        )
    replica_head = await commit_store.head(
        branch_id=targets.branch_id,
        projection_hash=targets.projection_hash,
    )

    logger.info(
        "NetworkNode committed lane synchronized locally "
        "(branch_id=%s authority_commit_id=%s previous_local_commit_id=%s "
        "commits_applied=%s projection_hash=%s)",
        targets.branch_id,
        targets.head_commit_id,
        local_head_commit_id,
        len(commits),
        targets.projection_hash,
    )
    replica_head_commit_id = _optional_uuid_from_mapping(replica_head, "commit_id")
    if replica_head_commit_id != targets.head_commit_id:
        raise RuntimeError(
            "NetworkNode hosted-service discovery replica watermark was not "
            "reached after pulling authority commits "
            f"(branch_id={targets.branch_id} projection_hash={targets.projection_hash} "
            f"local_head={replica_head_commit_id} authority_head={targets.head_commit_id})"
        )
    logger.info(
        "NetworkNode hosted-service discovery replica watermark reached "
        "branch_id=%s projection_hash=%s authority_head=%s commits_applied=%s",
        targets.branch_id,
        targets.projection_hash,
        targets.head_commit_id,
        len(commits),
    )
    return _NetworkNodeReplicaWatermark(
        branch_id=targets.branch_id,
        projection_hash=targets.projection_hash,
        authority_head_commit_id=targets.head_commit_id,
        local_head_commit_id=replica_head_commit_id,
        previous_local_head_commit_id=local_head_commit_id,
        commits_applied=len(commits),
    )


async def _ensure_network_node_lane_projected_for_db_publication(
    *,
    targets: _BootNetworkNodeHostedServiceTargets,
    mode: str = ProjectionReadinessModes.REQUIRED_DB,
) -> ProjectionReadinessResult:
    normalized_mode = _network_node_projection_cache_mode(value=mode)
    backend = (os.getenv("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db" or normalized_mode == ProjectionReadinessModes.OFF:
        return await ensure_projection_readiness(
            index=None,
            requirement=ProjectionReadinessRequirement(
                name="network_node.hosted_service_publication",
                branch_id=targets.branch_id,
                projection_hash=targets.projection_hash,
                head_commit_id=targets.head_commit_id,
                object_instance_graph_id=targets.object_instance_graph_id,
                mode=ProjectionReadinessModes.OFF,
            ),
        )

    index = _graph_catalog(
        await _resolve_network_graph_context_for_hosted_service_discovery(
            targets=targets,
        )
    )
    requirement = ProjectionReadinessRequirement(
        name="network_node.hosted_service_publication",
        branch_id=targets.branch_id,
        projection_hash=targets.projection_hash,
        head_commit_id=targets.head_commit_id,
        object_instance_graph_id=targets.object_instance_graph_id,
        mode=normalized_mode,
    )
    try:
        result = await ensure_projection_readiness(
            index=index,
            requirement=requirement,
        )
    except Exception as exc:
        if normalized_mode != ProjectionReadinessModes.OPTIONAL_DB:
            raise
        logger.info(
            "Optional NetworkNode hosted-service publication DB projection cache "
            "was not prepared branch_id=%s projection_hash=%s reason=%s",
            targets.branch_id,
            targets.projection_hash,
            exc,
        )
        return ProjectionReadinessResult(
            requirement=requirement,
            status="degraded",
            skipped_reason=str(exc),
        )
    if result.skipped_reason:
        logger.debug(
            "Skipped NetworkNode hosted-service publication DB projection catch-up "
            "branch_id=%s projection_hash=%s reason=%s",
            targets.branch_id,
            targets.projection_hash,
            result.skipped_reason,
        )
        return result
    if result.commits_applied:
        logger.info(
            "NetworkNode hosted-service publication DB projection catch-up applied "
            "committed lane branch_id=%s projection_hash=%s commits=%s "
            "head_commit_id=%s",
            targets.branch_id,
            targets.projection_hash,
            result.commits_applied,
            result.head_commit_id,
        )
    return result


def _network_node_publication_projection_cache_mode() -> str:
    return _network_node_projection_cache_mode(
        value=os.environ.get(
            "AWARE_NODE_NETWORK_NODE_PUBLICATION_PROJECTION_CACHE_MODE",
            ProjectionReadinessModes.OFF,
        )
    )


def _network_node_projection_cache_mode(*, value: object) -> str:
    normalized = str(value or "").strip().lower() or ProjectionReadinessModes.OFF
    if normalized in {
        ProjectionReadinessModes.REQUIRED_DB,
        ProjectionReadinessModes.OPTIONAL_DB,
        ProjectionReadinessModes.OFF,
    }:
        return normalized
    raise RuntimeError(
        "AWARE_NODE_NETWORK_NODE_PUBLICATION_PROJECTION_CACHE_MODE must be one "
        "of required_db, optional_db, or off."
    )


async def _fetch_environment_object_instance_graph_commit(
    *,
    route_to_environment_service,
    targets: _BootNetworkNodeHostedServiceTargets,
    commit_id: UUID,
):
    from aware_meta_ontology.graph.instance.object_instance_graph_commit import (
        ObjectInstanceGraphCommit,
    )

    response = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=targets.environment_id,
        timeout_s=_network_node_discovery_request_timeout_s(),
        request=GetObjectInstanceGraphCommitRequest(
            actor_id=targets.actor_id,
            environment_id=targets.environment_id,
            process_id=targets.process_id,
            thread_id=targets.thread_id,
            branch_id=targets.branch_id,
            projection_hash=targets.projection_hash,
            commit_id=commit_id,
        ),
    )
    if getattr(response, "operation", None) != "get_object_instance_graph_commit":
        raise RuntimeError(
            "get_object_instance_graph_commit returned unexpected payload while "
            "pulling NetworkNode hosted-service discovery truth"
        )
    if (getattr(response, "status", "") or "").lower() != "succeeded":
        raise RuntimeError(
            getattr(response, "error", None)
            or "get_object_instance_graph_commit failed while pulling "
            "NetworkNode hosted-service discovery truth"
        )
    payload = getattr(response, "commit", None)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "get_object_instance_graph_commit returned no commit payload while "
            f"pulling NetworkNode hosted-service discovery truth: {commit_id}"
        )
    return ObjectInstanceGraphCommit.model_validate_json(
        json.dumps(payload, separators=(",", ":"), sort_keys=True)
    )


async def _materialize_committed_network_node_lane_snapshot(
    *,
    targets: _BootNetworkNodeHostedServiceTargets,
) -> Mapping[str, object]:
    index = _graph_catalog(
        await _resolve_network_graph_context_for_hosted_service_discovery(
            targets=targets,
        )
    )
    opg = index.opg_by_hash.get(targets.projection_hash)
    if opg is None:
        raise RuntimeError(
            "NetworkNode hosted-service discovery cannot resolve projection hash "
            f"{targets.projection_hash!r} from the deployed graph context"
        )
    oig, _indexes = await materialize_local_meta_lane_oig(
        branch_id=targets.branch_id,
        ocg=index.ocg,
        opg=opg,
        commit_id=targets.head_commit_id,
        oig_id=targets.object_instance_graph_id,
        attribute_configs_by_id=index.attribute_configs_by_id,
        class_configs_by_id=index.class_configs_by_id,
    )
    payload = oig.model_dump(mode="json", exclude_none=True)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "Materialized NetworkNode lane snapshot is not a JSON object"
        )
    return cast(Mapping[str, object], payload)


async def _resolve_network_graph_context_for_hosted_service_discovery(
    *,
    targets: _BootNetworkNodeHostedServiceTargets,
) -> object:
    _ = targets
    return _read_node_meta_runtime_context(
        materialized_workspace_root=_node_workspace_revision_materialized_root_required(
            purpose="NetworkNode hosted-service discovery"
        ),
        required_projection_names=("NetworkNode",),
        composite_name="Aware Node NetworkNode Hosted-Service Discovery Context",
    )


def _read_node_meta_runtime_context(
    *,
    materialized_workspace_root: Path,
    required_projection_names: tuple[str, ...],
    composite_name: str,
) -> object:
    resolved_root = Path(materialized_workspace_root).expanduser().resolve()
    read_model = read_local_meta_runtime_read_model(
        repo_root=resolved_root,
        aware_root=resolved_root,
        required_projection_names=required_projection_names,
        composite_name=composite_name,
    )
    context = getattr(read_model, "context", None)
    if context is None:
        raise RuntimeError(
            "Node Meta runtime read model did not expose graph context "
            f"(projections={required_projection_names!r})"
        )
    return context


def _node_workspace_revision_materialized_root_required(*, purpose: str) -> Path:
    root = _service_api_dependency_materialized_workspace_root()
    if root is None:
        raise RuntimeError(
            f"{purpose} requires {_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV}; "
            "Node deployment must provide a prepared WorkspaceRevision "
            "materialized root instead of source-local graph discovery."
        )
    return root


def _parse_materialized_network_node_hosted_service_advertisements(
    *,
    snapshot: Mapping[str, object],
) -> tuple[HostedServiceAdvertisement, ...]:
    service_class_config_id = _network_node_service_class_config_id()
    field_names = _network_node_service_materialized_field_names()

    advertisements: list[HostedServiceAdvertisement] = []
    seen_service_names: set[str] = set()
    raw_class_instances = snapshot.get("class_instances")
    if not isinstance(raw_class_instances, list):
        return ()
    for raw_instance in raw_class_instances:
        if not isinstance(raw_instance, Mapping):
            continue
        if (
            _optional_uuid_from_mapping(raw_instance, "class_config_id")
            != service_class_config_id
        ):
            continue
        payload = _materialized_class_instance_attribute_payload(
            instance=raw_instance,
            field_names=field_names,
        )
        service_id = _required_uuid_value(
            payload.get("service_id"),
            field_name="service_id",
            context="materialized NetworkNodeService",
        )
        service_package_id = _required_uuid_value(
            payload.get("service_package_id"),
            field_name="service_package_id",
            context="materialized NetworkNodeService",
        )
        service_name = _required_string_value(
            payload.get("service_name"),
            field_name="service_name",
            context="materialized NetworkNodeService",
        )
        normalized_service_name = service_name.casefold()
        if normalized_service_name in seen_service_names:
            raise RuntimeError(
                "Materialized NetworkNodeService lane contains duplicate service_name "
                f"{service_name!r}"
            )
        seen_service_names.add(normalized_service_name)

        advertisements.append(
            HostedServiceAdvertisement(
                service_package_id=service_package_id,
                service_id=service_id,
                service_name=service_name,
                endpoint_refs=_string_tuple_value(payload.get("endpoint_refs")),
                host_id=_required_string_value(
                    payload.get("host_id"),
                    field_name="host_id",
                    context=f"materialized NetworkNodeService {service_name!r}",
                ),
                host_version=_optional_string_value(payload.get("host_version")),
                protocol_version=_required_string_value(
                    payload.get("protocol_version"),
                    field_name="protocol_version",
                    context=f"materialized NetworkNodeService {service_name!r}",
                ),
                supports_stream_events=_bool_value(
                    payload.get("supports_stream_events")
                ),
            )
        )

    return tuple(
        sorted(
            advertisements,
            key=lambda item: (item.service_name.casefold(), str(item.service_id)),
        )
    )


def _network_node_service_class_config_id() -> UUID:
    from aware_network_ontology.stable_ids import (
        CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID,
    )

    for (
        raw_class_config_id,
        binding,
    ) in CONSTRUCTOR_STABLE_ID_BINDINGS_BY_CLASS_CONFIG_ID.items():
        stable_function_name = binding[0] if binding else None
        if stable_function_name == "stable_network_node_service_id":
            return UUID(str(raw_class_config_id))
    raise RuntimeError("NetworkNodeService class_config_id is missing from stable IDs")


def _network_node_service_materialized_field_names() -> tuple[str, ...]:
    from aware_network_ontology.network.network_node_service import NetworkNodeService

    return tuple(
        field_name
        for field_name in NetworkNodeService.model_fields
        if field_name not in {"id", "service", "service_package"}
    )


def _materialized_class_instance_attribute_payload(
    *,
    instance: Mapping[str, object],
    field_names: tuple[str, ...],
) -> dict[str, object | None]:
    raw_edges = instance.get("class_instance_attributes")
    if not isinstance(raw_edges, list):
        raise RuntimeError("Materialized ClassInstance missing attribute edges")
    values = tuple(
        _decode_materialized_attribute_edge_value(edge)
        for edge in raw_edges
        if isinstance(edge, Mapping)
    )
    if len(values) != len(field_names):
        source_object_id = instance.get("source_object_id")
        raise RuntimeError(
            "Materialized NetworkNodeService attribute count does not match "
            "generated field contract "
            f"(source_object_id={source_object_id!r} fields={len(field_names)} "
            f"values={len(values)})"
        )
    return dict(zip(field_names, values, strict=True))


def _decode_materialized_attribute_edge_value(
    edge: Mapping[str, object]
) -> object | None:
    raw_attribute = edge.get("attribute")
    if not isinstance(raw_attribute, Mapping):
        return None
    raw_value_root = raw_attribute.get("value_root")
    if not isinstance(raw_value_root, Mapping):
        return None
    return _decode_materialized_attribute_value(raw_value_root)


def _decode_materialized_attribute_value(value: Mapping[str, object]) -> object | None:
    primitive = value.get("primitive_value")
    if isinstance(primitive, Mapping) and "value" in primitive:
        return primitive.get("value")
    if primitive is not None and not isinstance(primitive, Mapping):
        return primitive

    enum_option = value.get("enum_option")
    if isinstance(enum_option, Mapping) and "value" in enum_option:
        return enum_option.get("value")
    enum_option_id = value.get("enum_option_id")
    if enum_option_id is not None:
        return str(enum_option_id)

    class_instance_id = value.get("class_instance_id")
    if class_instance_id is not None:
        return str(class_instance_id)

    raw_links = value.get("child_links")
    if not isinstance(raw_links, list):
        return None
    decoded_values = [
        _decode_materialized_attribute_value(child)
        for child in _materialized_attribute_value_children(raw_links)
    ]
    descriptor = value.get("type_descriptor")
    descriptor_kind = (
        str(descriptor.get("kind"))
        if isinstance(descriptor, Mapping) and descriptor.get("kind") is not None
        else None
    )
    if descriptor_kind == "union":
        return next((item for item in decoded_values if item is not None), None)
    return decoded_values


def _materialized_attribute_value_children(
    raw_links: list[object],
) -> tuple[Mapping[str, object], ...]:
    links = [link for link in raw_links if isinstance(link, Mapping)]
    links.sort(key=_materialized_attribute_value_link_sort_key)
    children: list[Mapping[str, object]] = []
    for link in links:
        child = link.get("child")
        if isinstance(child, Mapping):
            children.append(child)
    return tuple(children)


def _materialized_attribute_value_link_sort_key(
    link: Mapping[str, object],
) -> tuple[int, str]:
    position = link.get("position")
    position_key = int(position) if isinstance(position, int | str) else 0
    return (position_key, str(link.get("identity_key") or ""))


def _optional_uuid_from_mapping(
    payload: Mapping[str, object] | None,
    key: str,
) -> UUID | None:
    if payload is None:
        return None
    value = payload.get(key)
    if value is None:
        return None
    try:
        return value if isinstance(value, UUID) else UUID(str(value).strip())
    except (AttributeError, TypeError, ValueError):
        return None


def _required_uuid_value(
    value: object,
    *,
    field_name: str,
    context: str,
) -> UUID:
    try:
        return value if isinstance(value, UUID) else UUID(str(value).strip())
    except (AttributeError, TypeError, ValueError) as exc:
        raise RuntimeError(f"{context} missing valid {field_name}") from exc


def _required_string_value(
    value: object,
    *,
    field_name: str,
    context: str,
) -> str:
    text = _optional_string_value(value)
    if text is None:
        raise RuntimeError(f"{context} missing non-empty {field_name}")
    return text


def _optional_string_value(value: object) -> str | None:
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_tuple_value(value: object) -> list[str]:
    if value is None:
        return []
    raw_values = value if isinstance(value, list) else [value]
    return [
        text
        for item in raw_values
        if (text := _optional_string_value(item)) is not None
    ]


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().casefold() in {"1", "true", "yes", "on"}
    return bool(value)


def _build_committed_hosted_service_advertisement_index(
    *,
    advertisements: tuple[HostedServiceAdvertisement, ...],
) -> _CommittedHostedServiceAdvertisementIndex:
    advertisement_by_service_name: dict[str, HostedServiceAdvertisement] = {}
    advertisement_by_endpoint_ref: dict[str, HostedServiceAdvertisement] = {}
    for advertisement in advertisements:
        normalized_service_name = advertisement.service_name.strip().casefold()
        if not normalized_service_name:
            continue
        if normalized_service_name in advertisement_by_service_name:
            raise RuntimeError(
                "Committed hosted-service index contains duplicate service_name "
                f"{advertisement.service_name!r}"
            )
        advertisement_by_service_name[normalized_service_name] = advertisement

        for endpoint_ref in advertisement.endpoint_refs:
            normalized_endpoint_ref = endpoint_ref.strip().casefold()
            if not normalized_endpoint_ref:
                continue
            if normalized_endpoint_ref in advertisement_by_endpoint_ref:
                raise RuntimeError(
                    "Committed hosted-service index contains duplicate endpoint_ref "
                    f"{endpoint_ref!r}"
                )
            advertisement_by_endpoint_ref[normalized_endpoint_ref] = advertisement

    return _CommittedHostedServiceAdvertisementIndex(
        advertisements=advertisements,
        advertisement_by_service_name=advertisement_by_service_name,
        advertisement_by_endpoint_ref=advertisement_by_endpoint_ref,
    )


def _committed_hosted_service_advertisement_coverage(
    *,
    runtime: NodeHostServicesAssembly,
) -> _CommittedHostedServiceAdvertisementCoverage:
    live_advertisements = runtime.discover_hosted_service_advertisements()
    live_service_names = tuple(
        sorted(
            {
                advertisement.service_name.strip()
                for advertisement in live_advertisements
                if advertisement.service_name.strip()
            },
            key=str.casefold,
        )
    )
    live_endpoint_refs = tuple(
        sorted(
            {
                endpoint_ref.strip()
                for advertisement in live_advertisements
                for endpoint_ref in advertisement.endpoint_refs
                if isinstance(endpoint_ref, str) and endpoint_ref.strip()
            },
            key=str.casefold,
        )
    )

    index = runtime.committed_hosted_service_advertisement_index
    if index is None:
        return _CommittedHostedServiceAdvertisementCoverage(
            live_service_count=len(live_service_names),
            live_endpoint_count=len(live_endpoint_refs),
            committed_service_count=0,
            committed_endpoint_count=0,
            missing_service_names=live_service_names,
            missing_endpoint_refs=live_endpoint_refs,
        )

    missing_service_names = tuple(
        service_name
        for service_name in live_service_names
        if service_name.casefold() not in index.advertisement_by_service_name
    )
    missing_endpoint_refs: list[str] = []
    mismatched_endpoint_refs: list[str] = []
    for advertisement in live_advertisements:
        live_service_name = advertisement.service_name.strip()
        for endpoint_ref in advertisement.endpoint_refs:
            normalized_endpoint_ref = (
                endpoint_ref.strip().casefold() if isinstance(endpoint_ref, str) else ""
            )
            if not normalized_endpoint_ref:
                continue
            committed = index.advertisement_by_endpoint_ref.get(normalized_endpoint_ref)
            if committed is None:
                missing_endpoint_refs.append(endpoint_ref.strip())
                continue
            if (
                committed.service_name.strip().casefold()
                != live_service_name.casefold()
            ):
                mismatched_endpoint_refs.append(endpoint_ref.strip())

    return _CommittedHostedServiceAdvertisementCoverage(
        live_service_count=len(live_service_names),
        live_endpoint_count=len(live_endpoint_refs),
        committed_service_count=len(index.advertisement_by_service_name),
        committed_endpoint_count=len(index.advertisement_by_endpoint_ref),
        missing_service_names=tuple(
            sorted(set(missing_service_names), key=str.casefold)
        ),
        missing_endpoint_refs=tuple(
            sorted(set(missing_endpoint_refs), key=str.casefold)
        ),
        mismatched_endpoint_refs=tuple(
            sorted(set(mismatched_endpoint_refs), key=str.casefold)
        ),
    )


def _require_committed_hosted_service_advertisement_index_coverage(
    *,
    runtime: NodeHostServicesAssembly,
    context: str,
) -> None:
    coverage = _committed_hosted_service_advertisement_coverage(runtime=runtime)
    if coverage.is_satisfied:
        if coverage.live_service_count or coverage.live_endpoint_count:
            logger.info(
                "Committed hosted-service advertisement coverage satisfied "
                "(context=%s live_services=%s live_endpoints=%s "
                "committed_services=%s committed_endpoints=%s)",
                context,
                coverage.live_service_count,
                coverage.live_endpoint_count,
                coverage.committed_service_count,
                coverage.committed_endpoint_count,
            )
        return

    logger.error(
        "Committed hosted-service advertisement coverage failed "
        "(context=%s live_services=%s live_endpoints=%s committed_services=%s "
        "committed_endpoints=%s missing_services=%s missing_endpoints=%s "
        "mismatched_endpoints=%s)",
        context,
        coverage.live_service_count,
        coverage.live_endpoint_count,
        coverage.committed_service_count,
        coverage.committed_endpoint_count,
        list(coverage.missing_service_names),
        list(coverage.missing_endpoint_refs),
        list(coverage.mismatched_endpoint_refs),
    )
    details: list[str] = []
    if coverage.missing_service_names:
        details.append(
            "missing_services=[" + ", ".join(coverage.missing_service_names) + "]"
        )
    if coverage.missing_endpoint_refs:
        details.append(
            "missing_endpoint_refs=[" + ", ".join(coverage.missing_endpoint_refs) + "]"
        )
    if coverage.mismatched_endpoint_refs:
        details.append(
            "mismatched_endpoint_refs=["
            + ", ".join(coverage.mismatched_endpoint_refs)
            + "]"
        )
    raise RuntimeError(
        "Committed hosted-service advertisement index does not cover live "
        "hosted ServiceHost advertisements during "
        f"{context}; node readiness/provider refs must not advertise endpoints "
        "that cannot route through committed NetworkNodeService truth"
        + (": " + "; ".join(details) if details else "")
    )


async def _bootstrap_committed_hosted_service_advertisement_index(
    *,
    node_app: object,
    hosted_service_runtimes: tuple[NodeHostedServiceRuntime, ...],
    defer_unavailable_environment: bool = False,
) -> tuple[
    _BootNetworkNodeHostedServiceTargets | None,
    _CommittedHostedServiceAdvertisementIndex | None,
]:
    if not hosted_service_runtimes:
        return None, None
    try:
        targets = await _read_network_node_hosted_service_targets(node_app=node_app)
        if targets is None:
            return None, None
        published_targets = targets
    except Exception as exc:
        if defer_unavailable_environment:
            logger.info(
                "Deferred committed hosted-service advertisement bootstrap until "
                "the boot Environment API is ready (error=%s)",
                exc,
            )
            return None, None
        raise
    return (
        published_targets,
        await _refresh_committed_hosted_service_advertisement_index(
            node_app=node_app,
            targets=published_targets,
        ),
    )


async def _ensure_committed_hosted_service_advertisement_index(
    *,
    node_app: object,
    runtime: NodeHostServicesAssembly,
    defer_unavailable_environment: bool = False,
) -> None:
    if not runtime.hosted_service_runtimes:
        return
    if (
        runtime.committed_hosted_service_advertisement_index is not None
        and runtime.committed_hosted_service_advertisement_index_refresh_relay
        is not None
    ):
        coverage = _committed_hosted_service_advertisement_coverage(runtime=runtime)
        if coverage.is_satisfied:
            return
        logger.info(
            "Refreshing committed hosted-service advertisement index after "
            "live ServiceHost capability change (missing_services=%s "
            "missing_endpoints=%s mismatched_endpoints=%s)",
            list(coverage.missing_service_names),
            list(coverage.missing_endpoint_refs),
            list(coverage.mismatched_endpoint_refs),
        )

    targets, index = await _bootstrap_committed_hosted_service_advertisement_index(
        node_app=node_app,
        hosted_service_runtimes=runtime.hosted_service_runtimes,
        defer_unavailable_environment=defer_unavailable_environment,
    )
    runtime.committed_hosted_service_advertisement_index = index

    if targets is None:
        return

    await _stop_committed_hosted_service_advertisement_index_refresh_relay(
        runtime.committed_hosted_service_advertisement_index_refresh_relay
    )
    runtime.committed_hosted_service_advertisement_index_refresh_relay = (
        _start_committed_hosted_service_advertisement_index_refresh_relay(
            node_app=node_app,
            runtime_registry=runtime,
            targets=targets,
        )
    )


def _committed_hosted_service_advertisement_bootstrap_pending(
    *,
    runtime: NodeHostServicesAssembly,
) -> bool:
    return (
        bool(runtime.hosted_service_runtimes)
        and runtime.committed_hosted_service_advertisement_index is None
    )


def _network_node_discovery_request_timeout_s(*, default: float = 15.0) -> float:
    discovery_timeout = _clean_text(
        os.environ.get(_NODE_NETWORK_NODE_DISCOVERY_REQUEST_TIMEOUT_S_ENV)
    )
    if discovery_timeout is not None:
        return _float_env(
            _NODE_NETWORK_NODE_DISCOVERY_REQUEST_TIMEOUT_S_ENV,
            default=default,
        )
    hosted_request_timeout = _clean_text(
        os.environ.get(_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S_ENV)
    )
    if hosted_request_timeout is not None:
        return _float_env(
            _NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S_ENV,
            default=default,
        )
    return default


async def _refresh_committed_hosted_service_advertisement_index(
    *,
    node_app: object,
    targets: _BootNetworkNodeHostedServiceTargets,
) -> _CommittedHostedServiceAdvertisementIndex:
    advertisements = await _read_committed_node_hosted_service_advertisements(
        node_app=node_app,
        targets=targets,
    )
    return _build_committed_hosted_service_advertisement_index(
        advertisements=advertisements
    )


async def resolve_node_hosted_service_runtime_for_service_name(
    *,
    node_app: object,
    service_name: str,
) -> NodeHostedServiceRuntime:
    normalized_service_name = service_name.strip()
    if not normalized_service_name:
        raise RuntimeError("ServiceOperationRequest.service is required")

    match = await _resolve_committed_hosted_service_advertisement_for_service_name(
        node_app=node_app,
        service_name=normalized_service_name,
    )
    return _resolve_local_hosted_service_runtime_for_committed_advertisement(
        node_app=node_app,
        advertisement=match,
        resolution_label=f"service {normalized_service_name!r}",
    )


async def resolve_node_hosted_service_runtime_for_endpoint_ref(
    *,
    node_app: object,
    endpoint_ref: str,
) -> NodeHostedServiceRuntime:
    normalized_endpoint_ref = endpoint_ref.strip()
    if not normalized_endpoint_ref:
        raise RuntimeError("InvokeApiEndpointRequest.endpoint_ref is required")

    match = await _resolve_committed_hosted_service_advertisement_for_endpoint_ref(
        node_app=node_app,
        endpoint_ref=normalized_endpoint_ref,
    )
    return _resolve_local_hosted_service_runtime_for_committed_advertisement(
        node_app=node_app,
        advertisement=match,
        resolution_label=f"endpoint_ref {normalized_endpoint_ref!r}",
    )


async def resolve_node_hosted_service_runtime_for_service_request(
    *,
    node_app: object,
    request: ServiceOperationRequest,
) -> NodeHostedServiceRuntime:
    api_dispatch = request.api_dispatch
    if api_dispatch is None:
        return await resolve_node_hosted_service_runtime_for_service_name(
            node_app=node_app,
            service_name=request.service,
        )

    normalized_service_name = request.service.strip()
    if not normalized_service_name:
        raise RuntimeError("ServiceOperationRequest.service is required")

    endpoint_ref = api_dispatch.envelope.endpoint_ref.strip()
    if not endpoint_ref:
        raise RuntimeError(
            "ServiceApiDispatchRequest.envelope.endpoint_ref is required"
        )

    advertisement = (
        await _resolve_committed_hosted_service_advertisement_for_endpoint_ref(
            node_app=node_app,
            endpoint_ref=endpoint_ref,
        )
    )
    advertised_service_name = (advertisement.service_name or "").strip()
    if advertised_service_name.casefold() != normalized_service_name.casefold():
        raise RuntimeError(
            "ServiceOperationRequest.service "
            f"{normalized_service_name!r} does not match committed "
            "NetworkNodeService advertisement service_name "
            f"{advertised_service_name!r} for endpoint_ref {endpoint_ref!r}"
        )

    return _resolve_local_hosted_service_runtime_for_committed_advertisement(
        node_app=node_app,
        advertisement=advertisement,
        resolution_label=f"endpoint_ref {endpoint_ref!r}",
    )


def describe_node_hosted_service_runtime_statuses(
    *,
    node_app: object,
) -> tuple[HostedServiceRuntimeStatus, ...]:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if runtime is None:
        return ()
    return cast(
        NodeHostServicesAssembly, runtime
    ).describe_hosted_service_runtime_statuses()


def describe_node_hosted_runtime_lifecycle_statuses(
    *,
    node_app: object,
    runtime_kind: str | None = None,
    runtime_key: str | None = None,
) -> tuple[HostedRuntimeLifecycleStatus, ...]:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if runtime is None:
        return ()
    return cast(
        NodeHostServicesAssembly, runtime
    ).describe_hosted_runtime_lifecycle_statuses(
        runtime_kind=runtime_kind,
        runtime_key=runtime_key,
    )


def _resolve_local_hosted_service_runtime_for_committed_advertisement(
    *,
    node_app: object,
    advertisement: HostedServiceAdvertisement,
    resolution_label: str,
) -> NodeHostedServiceRuntime:
    runtime_registry = require_node_host_services_runtime(node_app=node_app)
    try:
        return runtime_registry.resolve_hosted_service_runtime_for_host_id(
            host_id=advertisement.host_id
        )
    except RuntimeError as exc:
        raise RuntimeError(
            "Committed NetworkNodeService advertisement for "
            f"{resolution_label} targets unknown local host_id "
            f"{advertisement.host_id!r}"
        ) from exc


async def _resolve_committed_hosted_service_advertisement_for_service_name(
    *,
    node_app: object,
    service_name: str,
) -> HostedServiceAdvertisement:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if isinstance(runtime, NodeHostServicesAssembly):
        index = runtime.committed_hosted_service_advertisement_index
        if index is not None:
            return (
                runtime.resolve_committed_hosted_service_advertisement_for_service_name(
                    service_name=service_name
                )
            )

    match: HostedServiceAdvertisement | None = None
    for advertisement in await discover_node_hosted_service_advertisements(
        node_app=node_app
    ):
        advertised_service_name = advertisement.service_name.strip()
        if advertised_service_name.casefold() != service_name.casefold():
            continue
        if match is not None:
            raise RuntimeError(
                "Materialized NetworkNodeService lane contains duplicate service_name "
                f"{service_name!r}"
            )
        match = advertisement

    if match is None:
        raise CommittedHostedServiceLookupMiss(
            "Node hosted Service runtime is not registered for service "
            f"{service_name!r} via committed NetworkNodeService truth"
        )
    return match


async def _resolve_committed_hosted_service_advertisement_for_endpoint_ref(
    *,
    node_app: object,
    endpoint_ref: str,
) -> HostedServiceAdvertisement:
    runtime = getattr(node_app, "_host_services_runtime", None)
    if isinstance(runtime, NodeHostServicesAssembly):
        index = runtime.committed_hosted_service_advertisement_index
        if index is not None:
            return (
                runtime.resolve_committed_hosted_service_advertisement_for_endpoint_ref(
                    endpoint_ref=endpoint_ref
                )
            )

    match: HostedServiceAdvertisement | None = None
    for advertisement in await discover_node_hosted_service_advertisements(
        node_app=node_app
    ):
        advertised_endpoint_refs = {
            ref.strip().casefold()
            for ref in advertisement.endpoint_refs
            if isinstance(ref, str) and ref.strip()
        }
        if endpoint_ref.casefold() not in advertised_endpoint_refs:
            continue
        if match is not None:
            raise RuntimeError(
                "Materialized NetworkNodeService lane contains duplicate endpoint_ref "
                f"{endpoint_ref!r}"
            )
        match = advertisement

    if match is None:
        raise CommittedHostedServiceLookupMiss(
            "Node hosted Service runtime is not registered for endpoint_ref "
            f"{endpoint_ref!r} via committed NetworkNodeService truth"
        )
    return match


def _require_node_environment_route(
    *,
    node_app: object,
):
    network_router = getattr(node_app, "_network_router", None)
    route_to_environment_service = getattr(
        network_router, "route_to_environment_service", None
    )
    if not callable(route_to_environment_service):
        raise RuntimeError(
            "Node environment route is unavailable for hosted-service discovery"
        )
    return route_to_environment_service


async def _send_environment_request(
    *,
    route_to_environment_service,
    environment_id: UUID,
    request: object,
    timeout_s: float,
):
    client = build_environment_service_api_client(
        route_to_environment_service=route_to_environment_service,
        environment_id=environment_id,
        node_id=network_node_manager.hosted_node_id,
        actor_id=getattr(request, "actor_id", None),
        default_timeout_s=timeout_s,
    )
    return await invoke_environment_service_api_request(client, request)


async def _read_network_node_hosted_service_targets(
    *,
    node_app: object,
) -> _BootNetworkNodeHostedServiceTargets | None:
    hosted_environment_service = getattr(
        node_app, "_node_hosted_environment_service", None
    )
    node_id = network_node_manager.hosted_node_id
    descriptor_resolution: _BootEnvironmentDescriptorResolution | None = None
    if hosted_environment_service is not None:
        if _has_local_environment_config_runtime_input(hosted_environment_service):
            boot = hosted_environment_service.read_boot_environment_descriptor(
                node_id=node_id
            )
            if boot.descriptor is not None:
                descriptor_resolution = _BootEnvironmentDescriptorResolution(
                    descriptor=boot.descriptor,
                    route_to_environment_service=_require_node_environment_route(
                        node_app=node_app
                    ),
                )
    if descriptor_resolution is None:
        descriptor_resolution = await _read_remote_provider_boot_environment_descriptor(
            node_app=node_app,
        )
    if descriptor_resolution is None:
        return None
    descriptor = descriptor_resolution.descriptor
    if descriptor.process_id is None or descriptor.thread_id is None:
        raise RuntimeError(
            "Boot environment descriptor is missing process_id/thread_id "
            "for NetworkNode hosted-service discovery"
        )
    actor_id = resolve_node_system_actor_id()

    route_to_environment_service = descriptor_resolution.route_to_environment_service
    describe_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=descriptor.boot_environment_id,
        timeout_s=_network_node_discovery_request_timeout_s(),
        request=DescribeEnvironmentConfigRequest(
            actor_id=actor_id,
            environment_id=descriptor.boot_environment_id,
            process_id=descriptor.process_id,
            thread_id=descriptor.thread_id,
            branch_id=descriptor.branch_id,
            projection_hash=None,
        ),
    )
    if getattr(describe_payload, "operation", None) != "describe_environment_config":
        raise RuntimeError(
            "describe_environment_config returned unexpected payload "
            "while resolving NetworkNode hosted-service discovery"
        )
    describe_payload_typed = cast(Any, describe_payload)
    runtime_manifest_path = _runtime_manifest_path_from_describe_environment_config(
        describe_payload=describe_payload_typed,
    )

    network_node_opg = next(
        (
            opg
            for opg in describe_payload_typed.opgs
            if (opg.name or "").strip() == "NetworkNode"
        ),
        None,
    )
    if network_node_opg is None:
        raise RuntimeError(
            "Boot environment does not expose the network_node projection"
        )
    network_node_lane_head = await _try_read_network_node_lane_head(
        actor_id=actor_id,
        branch_id=node_id,
        environment_id=descriptor.boot_environment_id,
        process_id=descriptor.process_id,
        projection_hash=network_node_opg.projection_hash,
        route_to_environment_service=route_to_environment_service,
        thread_id=descriptor.thread_id,
    )
    if network_node_lane_head is None:
        logger.info(
            "Deferred committed NetworkNode discovery until Network Service "
            "reconciliation publishes the local node lane "
            "(branch_id=%s projection_hash=%s)",
            node_id,
            network_node_opg.projection_hash,
        )
        return None

    capabilities_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=descriptor.boot_environment_id,
        timeout_s=_network_node_discovery_request_timeout_s(),
        request=FetchCapabilitiesRequest(
            actor_id=actor_id,
            environment_id=descriptor.boot_environment_id,
            process_id=descriptor.process_id,
            thread_id=descriptor.thread_id,
            branch_id=None,
            projection_hash=None,
        ),
    )
    if getattr(capabilities_payload, "operation", None) != "fetch_capabilities":
        raise RuntimeError(
            "fetch_capabilities returned unexpected payload while resolving "
            "NetworkNode hosted-service discovery"
        )
    capabilities_payload_typed = cast(Any, capabilities_payload)
    attach_service_fn_id = next(
        (
            fn.id
            for obj in capabilities_payload_typed.objects
            if obj.name == "NetworkNode"
            for fn in obj.functions
            if fn.name == "attach_service"
        ),
        None,
    )
    if attach_service_fn_id is None:
        raise RuntimeError(
            "NetworkNode.attach_service is missing from boot environment capabilities"
        )

    return _BootNetworkNodeHostedServiceTargets(
        actor_id=actor_id,
        branch_id=node_id,
        node_root_object_id=network_node_lane_head.root_object_id,
        head_commit_id=network_node_lane_head.commit_id,
        object_instance_graph_id=network_node_lane_head.object_instance_graph_id,
        graph_hash_post=network_node_lane_head.graph_hash_post,
        environment_id=descriptor.boot_environment_id,
        process_id=descriptor.process_id,
        thread_id=descriptor.thread_id,
        projection_graph_id=network_node_opg.id,
        projection_hash=network_node_opg.projection_hash,
        attach_service_function_id=attach_service_fn_id,
        runtime_manifest_path=runtime_manifest_path,
        route_to_environment_service=route_to_environment_service,
    )


async def _read_remote_provider_boot_environment_descriptor(
    *,
    node_app: object,
) -> _BootEnvironmentDescriptorResolution | None:
    provider_inputs = tuple(
        provider_input
        for provider_input in _remote_service_api_provider_inputs_from_env()
        if _remote_provider_input_is_environment_service(provider_input)
    )
    if not provider_inputs:
        return None

    resolutions: list[_BootEnvironmentDescriptorResolution] = []
    actor_id = resolve_node_system_actor_id()
    for provider_input in provider_inputs:
        peer = NetworkNodePeerEndpoint(
            node_id=provider_input.provider_node_id,
            base_url=provider_input.provider_node_base_url,
        )
        try:
            descriptor = await read_remote_boot_environment_descriptor_from_peer(
                network_app=cast(Any, node_app),
                peer=peer,
                route_connection_id=provider_input.route_connection_id,
                actor_id=actor_id,
                timeout_s=provider_input.request_timeout_s,
            )
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(
                "Remote Environment boot descriptor discovery failed "
                "(provider_node_id=%s provider_node_base_url=%s error=%s)",
                provider_input.provider_node_id,
                provider_input.provider_node_base_url,
                exc,
            )
            continue
        if descriptor is not None:
            logger.info(
                "Remote Environment boot descriptor resolved "
                "(provider_node_id=%s provider_node_base_url=%s environment_id=%s)",
                provider_input.provider_node_id,
                provider_input.provider_node_base_url,
                getattr(descriptor, "boot_environment_id", None),
            )
            resolutions.append(
                _BootEnvironmentDescriptorResolution(
                    descriptor=descriptor,
                    route_to_environment_service=(
                        build_remote_environment_route_to_peer(
                            network_app=cast(Any, node_app),
                            peer=peer,
                            route_connection_id=provider_input.route_connection_id,
                            default_timeout_s=provider_input.request_timeout_s,
                        )
                    ),
                )
            )

    unique_environment_ids = {
        str(getattr(resolution.descriptor, "boot_environment_id", ""))
        for resolution in resolutions
        if getattr(resolution.descriptor, "boot_environment_id", None) is not None
    }
    if len(unique_environment_ids) > 1:
        raise RuntimeError(
            "Remote Environment provider refs resolved multiple boot "
            "Environment descriptors: " + ", ".join(sorted(unique_environment_ids))
        )
    return resolutions[0] if resolutions else None


def _remote_provider_input_is_environment_service(
    provider_input: _RemoteServiceApiProviderInput,
) -> bool:
    package_name = _clean_text(
        provider_input.service_package_ref_payload.get("package_name")
    )
    if package_name == _ENVIRONMENT_SERVICE_PACKAGE_NAME:
        return True
    advertisement = provider_input.hosted_service_advertisement
    if advertisement is None:
        return False
    return advertisement.service_name.strip().casefold() == "aware_environment"


def _runtime_manifest_path_from_describe_environment_config(
    *,
    describe_payload: object,
) -> Path | None:
    raw_path = _clean_text(getattr(describe_payload, "bundle_manifest_path", None))
    if raw_path is None:
        return None
    manifest_path = Path(raw_path).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = manifest_path.resolve()
    if not manifest_path.is_file():
        raise RuntimeError(
            "Boot Environment describe_environment_config advertised "
            "bundle_manifest_path for NetworkNode hosted-service discovery, "
            f"but the manifest does not exist: {manifest_path}"
        )
    return manifest_path


async def _read_network_node_lane_head(
    *,
    actor_id: UUID,
    branch_id: UUID,
    environment_id: UUID,
    process_id: UUID,
    projection_hash: str,
    route_to_environment_service,
    thread_id: UUID,
) -> _NetworkNodeLaneHead:
    lane_head = await _try_read_network_node_lane_head(
        actor_id=actor_id,
        branch_id=branch_id,
        environment_id=environment_id,
        process_id=process_id,
        projection_hash=projection_hash,
        route_to_environment_service=route_to_environment_service,
        thread_id=thread_id,
    )
    if lane_head is None:
        raise RuntimeError(
            "NetworkNode hosted-service discovery requires a committed "
            "NetworkNode lane head with commit_id and root_object_id. "
            f"branch_id={branch_id} projection_hash={projection_hash}"
        )
    return lane_head


async def _try_read_network_node_lane_head(
    *,
    actor_id: UUID,
    branch_id: UUID,
    environment_id: UUID,
    process_id: UUID,
    projection_hash: str,
    route_to_environment_service,
    thread_id: UUID,
) -> _NetworkNodeLaneHead | None:
    head_payload = await _send_environment_request(
        route_to_environment_service=route_to_environment_service,
        environment_id=environment_id,
        timeout_s=_network_node_discovery_request_timeout_s(),
        request=GetLaneHeadRequest(
            actor_id=actor_id,
            environment_id=environment_id,
            process_id=process_id,
            thread_id=thread_id,
            branch_id=branch_id,
            projection_hash=projection_hash,
        ),
    )
    if getattr(head_payload, "operation", None) != "get_lane_head":
        raise RuntimeError(
            "get_lane_head returned unexpected payload while resolving "
            "NetworkNode lane head"
        )
    commit_id = getattr(head_payload, "commit_id", None)
    root_object_id = getattr(head_payload, "root_object_id", None)
    if commit_id is None or root_object_id is None:
        return None
    raw_object_instance_graph_id = getattr(
        head_payload,
        "object_instance_graph_id",
        None,
    )
    object_instance_graph_id = (
        raw_object_instance_graph_id
        if isinstance(raw_object_instance_graph_id, UUID)
        else (
            UUID(str(raw_object_instance_graph_id))
            if raw_object_instance_graph_id is not None
            else None
        )
    )
    resolved_root_object_id = (
        root_object_id
        if isinstance(root_object_id, UUID)
        else UUID(str(root_object_id))
    )
    return _NetworkNodeLaneHead(
        commit_id=commit_id if isinstance(commit_id, UUID) else UUID(str(commit_id)),
        graph_hash_post=getattr(head_payload, "graph_hash_post", None),
        object_instance_graph_id=object_instance_graph_id,
        root_object_id=resolved_root_object_id,
    )


def _extract_routable_service_names_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> tuple[str, ...]:
    service_names: set[str] = set()
    for capability in handshake.capabilities:
        if capability.state is not ServiceHostCapabilityState.available:
            continue
        raw_items: object | None = None
        if capability.capability_id == "generic_service_operation_request":
            detail_payload = capability.detail_payload
            if isinstance(detail_payload, dict):
                raw_items = detail_payload.get("plugin_services")
        elif capability.capability_id == SERVICE_HOST_CAPABILITY_API_DISPATCH:
            detail_payload = capability.detail_payload
            if isinstance(detail_payload, dict):
                raw_items = detail_payload.get(
                    SERVICE_HOST_API_DISPATCH_SERVICE_NAMES_KEY
                )
                raw_endpoint_refs = detail_payload.get(
                    SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY
                )
                if isinstance(raw_endpoint_refs, dict):
                    service_names.update(
                        service_name.strip()
                        for service_name in raw_endpoint_refs
                        if isinstance(service_name, str) and service_name.strip()
                    )
        else:
            continue
        if not isinstance(raw_items, list):
            continue
        service_names.update(
            item.strip() for item in raw_items if isinstance(item, str) and item.strip()
        )
    return tuple(sorted(service_names))


def _extract_implementation_package_names_from_bootstrap(
    *,
    bootstrap: _LoadedServiceHostBootstrapConfig,
) -> tuple[str, ...]:
    app_config = getattr(bootstrap, "app", None)
    implementation_packages = getattr(app_config, "implementation_packages", None)
    package_refs = getattr(implementation_packages, "package_refs", ())
    package_names: set[str] = set()
    if not isinstance(package_refs, tuple):
        package_refs = ()
    package_names.update(
        package_name.strip()
        for package_ref in package_refs
        if isinstance((package_name := getattr(package_ref, "package_name", None)), str)
        and package_name.strip()
    )
    toml_paths = getattr(implementation_packages, "toml_paths", ())
    if isinstance(toml_paths, tuple):
        package_names.update(
            package_name
            for toml_path in toml_paths
            if (package_name := _service_toml_package_name(toml_path)) is not None
        )
    return tuple(sorted(package_names, key=str.casefold))


def _service_toml_package_name(toml_path: object) -> str | None:
    if not isinstance(toml_path, Path):
        return None
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec

    spec = load_aware_service_toml_spec(toml_path=toml_path.expanduser().resolve())
    package_name = spec.service.package_name.strip()
    return package_name or None


def _extract_implementation_service_package_id_from_bootstrap(
    *,
    bootstrap: _LoadedServiceHostBootstrapConfig,
) -> UUID | None:
    app_config = getattr(bootstrap, "app", None)
    implementation_packages = getattr(app_config, "implementation_packages", None)
    package_refs = getattr(implementation_packages, "package_refs", ())
    if not isinstance(package_refs, tuple):
        return None

    package_ids: list[UUID] = []
    for package_ref in package_refs:
        raw_package_id = getattr(package_ref, "semantic_package_id", None)
        if raw_package_id is None:
            continue
        try:
            package_id = (
                raw_package_id
                if isinstance(raw_package_id, UUID)
                else UUID(str(raw_package_id).strip())
            )
        except (AttributeError, TypeError, ValueError) as exc:
            package_name = getattr(package_ref, "package_name", None)
            raise RuntimeError(
                "ServiceHost bootstrap contains invalid ServicePackage "
                f"semantic_package_id for {package_name!r}."
            ) from exc
        if package_id not in package_ids:
            package_ids.append(package_id)

    if len(package_ids) > 1:
        raise RuntimeError(
            "ServiceHost network publication requires one committed ServicePackage "
            f"identity per hosted runtime; got {len(package_ids)}."
        )
    return package_ids[0] if package_ids else None


def _require_runtime_service_package_id(
    *,
    runtime: NodeHostedServiceRuntime,
) -> UUID:
    service_package_id = _runtime_service_package_id_fallback(runtime=runtime)
    if service_package_id is None:
        raise RuntimeError(
            "NetworkNodeService publication requires the hosted Service runtime "
            "bootstrap to carry a committed ServicePackage semantic_package_id."
        )
    return service_package_id


def _runtime_service_package_id_fallback(
    *,
    runtime: NodeHostedServiceRuntime,
) -> UUID | None:
    service_package_id = runtime.implementation_service_package_id
    return service_package_id


def _hosted_service_package_name(
    service_package: object,
) -> str:
    raw_name = getattr(service_package, "name", None)
    if not isinstance(raw_name, str) or not raw_name.strip():
        raise RuntimeError(
            "Node service API dependency route resolution requires ServicePackage.name"
        )
    return raw_name.strip()


def _extract_routable_endpoint_refs_by_service_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> Mapping[str, tuple[str, ...]]:
    endpoint_refs_by_service: dict[str, set[str]] = {}
    for capability in handshake.capabilities:
        if capability.state is not ServiceHostCapabilityState.available:
            continue
        if capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH:
            continue
        detail_payload = capability.detail_payload
        if not isinstance(detail_payload, dict):
            continue
        raw_endpoint_refs = detail_payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY
        )
        if not isinstance(raw_endpoint_refs, dict):
            continue
        for raw_service_name, raw_items in raw_endpoint_refs.items():
            if not isinstance(raw_service_name, str):
                continue
            service_name = raw_service_name.strip()
            if not service_name or not isinstance(raw_items, list):
                continue
            bucket = endpoint_refs_by_service.setdefault(service_name, set())
            bucket.update(
                item.strip()
                for item in raw_items
                if isinstance(item, str) and item.strip()
            )
    return {
        service_name: tuple(sorted(endpoint_refs))
        for service_name, endpoint_refs in sorted(
            endpoint_refs_by_service.items(),
            key=lambda item: item[0].casefold(),
        )
    }


def _extract_committed_service_ids_by_name_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> Mapping[str, UUID]:
    service_ids_by_name: dict[str, UUID] = {}
    for capability in handshake.capabilities:
        if capability.state is not ServiceHostCapabilityState.available:
            continue
        if capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH:
            continue
        detail_payload = capability.detail_payload
        if not isinstance(detail_payload, dict):
            continue
        raw_service_ids = detail_payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_IDS_BY_NAME_KEY
        )
        if not isinstance(raw_service_ids, dict):
            continue
        for raw_service_name, raw_service_id in raw_service_ids.items():
            if not isinstance(raw_service_name, str):
                continue
            service_name = raw_service_name.strip()
            if not service_name:
                continue
            normalized_service_name = service_name.casefold()
            if normalized_service_name in service_ids_by_name:
                raise RuntimeError(
                    "Service host handshake advertised duplicate committed "
                    f"service_id for hosted service {service_name!r}"
                )
            try:
                service_id = (
                    raw_service_id
                    if isinstance(raw_service_id, UUID)
                    else UUID(str(raw_service_id).strip())
                )
            except (AttributeError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Service host handshake advertised invalid committed "
                    f"service_id for hosted service {service_name!r}"
                ) from exc
            service_ids_by_name[normalized_service_name] = service_id
    return service_ids_by_name


def _extract_service_package_ids_by_name_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> Mapping[str, UUID]:
    service_package_ids_by_name: dict[str, UUID] = {}
    for capability in handshake.capabilities:
        if (
            capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH
            or capability.state is not ServiceHostCapabilityState.available
        ):
            continue
        detail_payload = capability.detail_payload
        if not isinstance(detail_payload, dict):
            continue
        raw_package_ids_by_name = detail_payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_PACKAGE_IDS_BY_NAME_KEY
        )
        if not isinstance(raw_package_ids_by_name, Mapping):
            continue
        for raw_service_name, raw_package_id in raw_package_ids_by_name.items():
            if not isinstance(raw_service_name, str):
                continue
            normalized_service_name = raw_service_name.strip().casefold()
            if not normalized_service_name:
                continue
            try:
                service_package_id = UUID(str(raw_package_id).strip())
            except (AttributeError, TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Service host handshake advertised invalid "
                    "service_package_id for hosted service "
                    f"{raw_service_name!r}."
                ) from exc
            if normalized_service_name in service_package_ids_by_name:
                raise RuntimeError(
                    "Service host handshake advertised duplicate "
                    "service_package_id entries for hosted service "
                    f"{raw_service_name!r}."
                )
            service_package_ids_by_name[normalized_service_name] = service_package_id
    return service_package_ids_by_name


def _extract_routable_stream_endpoint_refs_by_service_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> Mapping[str, tuple[str, ...]]:
    endpoint_refs_by_service: dict[str, set[str]] = {}
    for capability in handshake.capabilities:
        if capability.state is not ServiceHostCapabilityState.available:
            continue
        if capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH:
            continue
        detail_payload = capability.detail_payload
        if not isinstance(detail_payload, dict):
            continue
        raw_endpoint_refs = detail_payload.get(
            SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY
        )
        if not isinstance(raw_endpoint_refs, dict):
            continue
        for raw_service_name, raw_items in raw_endpoint_refs.items():
            if not isinstance(raw_service_name, str):
                continue
            service_name = raw_service_name.strip()
            if not service_name or not isinstance(raw_items, list):
                continue
            bucket = endpoint_refs_by_service.setdefault(service_name, set())
            bucket.update(
                item.strip()
                for item in raw_items
                if isinstance(item, str) and item.strip()
            )
    return {
        service_name: tuple(sorted(endpoint_refs))
        for service_name, endpoint_refs in sorted(
            endpoint_refs_by_service.items(),
            key=lambda item: item[0].casefold(),
        )
    }


def _extract_lane_subscriptions_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> tuple[ServiceLaneSubscriptionBinding, ...]:
    subscriptions: list[ServiceLaneSubscriptionBinding] = []
    seen: set[tuple[UUID, str, UUID]] = set()
    for capability in handshake.capabilities:
        if capability.state is not ServiceHostCapabilityState.available:
            continue
        if capability.capability_id != "lane_commit_receipts":
            continue
        detail_payload = capability.detail_payload
        if not isinstance(detail_payload, dict):
            continue
        raw_subscriptions = detail_payload.get("subscriptions")
        if not isinstance(raw_subscriptions, list):
            continue
        for raw_item in raw_subscriptions:
            if not isinstance(raw_item, dict):
                continue
            try:
                subscription = ServiceLaneSubscriptionBinding(
                    service_branch_id=UUID(str(raw_item["service_branch_id"])),
                    service_config_api_projection_id=UUID(
                        str(raw_item["service_config_api_projection_id"])
                    ),
                    api_graph_projection_id=UUID(
                        str(raw_item["api_graph_projection_id"])
                    ),
                    object_instance_graph_branch_id=UUID(
                        str(raw_item["object_instance_graph_branch_id"])
                    ),
                    branch_id=UUID(str(raw_item["branch_id"])),
                    projection_hash=str(raw_item["projection_hash"]).strip(),
                )
            except Exception:
                continue
            if not subscription.projection_hash:
                continue
            key = (
                subscription.branch_id,
                subscription.projection_hash,
                subscription.service_branch_id,
            )
            if key in seen:
                continue
            seen.add(key)
            subscriptions.append(subscription)
    return tuple(
        sorted(
            subscriptions,
            key=lambda item: (
                str(item.branch_id),
                item.projection_hash,
                str(item.service_branch_id),
            ),
        )
    )


def _handshake_capability_is_available(
    *,
    handshake: ServiceHostHandshakeResponse,
    capability_id: str,
) -> bool:
    for capability in handshake.capabilities:
        if capability.capability_id != capability_id:
            continue
        return capability.state is ServiceHostCapabilityState.available
    return False


def _build_hosted_service_subprocess_env(
    *,
    bootstrap_config_path: Path,
    bootstrap: _LoadedServiceHostBootstrapConfig,
) -> dict[str, str]:
    env = dict(os.environ)
    for env_name in _HOSTED_SERVICE_SUBPROCESS_NODE_ONLY_ENV_NAMES:
        env.pop(env_name, None)
    env["AWARE_SERVICE_HOST_CONFIG_PATH"] = str(bootstrap_config_path)
    env[_SERVICE_HOST_NODE_MANAGED_STARTUP_ENV] = "1"
    env[_META_EVENT_STORE_ROOT_ENV] = _hosted_service_meta_event_store_root(
        bootstrap_config_path=bootstrap_config_path
    ).as_posix()
    app_config = getattr(bootstrap, "app", None)
    if getattr(app_config, "runtime_manifest_path", None) is not None:
        env.pop(_RUNTIME_BASE_ENVIRONMENT_MANIFEST_ENV, None)
        env.pop(_RUNTIME_BASE_ENVIRONMENT_MANIFESTS_ENV, None)
    return env


def _hosted_service_meta_event_store_root(*, bootstrap_config_path: Path) -> Path:
    return (
        (bootstrap_config_path.parent / _META_EVENT_STORE_ROOT_RELATIVE_PATH)
        .expanduser()
        .resolve()
    )


def _build_hosted_interface_subprocess_env(
    *,
    bootstrap_config_path: Path,
) -> dict[str, str]:
    env = dict(os.environ)
    env["AWARE_INTERFACE_SERVICE_CONFIG_PATH"] = str(bootstrap_config_path)
    # The InterfaceHost bootstrap file is the state/socket authority for a
    # Node-hosted Interface. Renderer-local overrides must not leak into it.
    for env_name in (
        "AWARE_INTERFACE_CONTROL_SOCKET",
        "AWARE_INTERFACE_CONTROL_PID_PATH",
        "AWARE_INTERFACE_SERVICE_STATE_HOME",
        "AWARE_STATE_HOME",
    ):
        env.pop(env_name, None)
    return env


def _load_service_host_bootstrap_config(
    bootstrap_config_path: Path,
) -> _LoadedServiceHostBootstrapConfig:
    from aware_service_service import ServiceHostBootstrapConfig

    return ServiceHostBootstrapConfig.from_path(bootstrap_config_path)


def _load_interface_host_bootstrap_config(
    bootstrap_config_path: Path,
) -> object:
    from aware_interface_service import InterfaceHostServiceConfig

    return InterfaceHostServiceConfig.from_path(bootstrap_config_path)


def _hosted_interface_socket_path(*, bootstrap: object) -> Path:
    state_home = getattr(bootstrap, "state_home", None)
    if not isinstance(state_home, Path):
        raise RuntimeError("InterfaceHost bootstrap config must expose state_home.")
    return (state_home / "interface-control.sock").resolve()


def _build_hosted_service_duplex_client(
    *,
    socket_path: Path,
) -> _HostedServiceDuplexClient:
    return ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(socket_path))
    )


def _build_interface_control_client(*, socket_path: Path) -> Any:
    from aware_interface_control import InterfaceControlPlaneClient

    return InterfaceControlPlaneClient(socket_path=socket_path)


__all__ = [
    "activate_node_hosted_service_lifecycles",
    "CommittedHostedServiceAdvertisementIndexRefreshRelay",
    "CommittedHostedServiceLookupMiss",
    "describe_node_hosted_runtime_lifecycle_statuses",
    "describe_node_hosted_service_runtime_statuses",
    "discover_node_hosted_service_advertisements",
    "NodeHostedInterfaceRuntime",
    "NodeHostedServiceRuntime",
    "NodeHostServicesAssembly",
    "open_api_ingress_stream_to_hosted_service_runtime",
    "open_request_stream_to_hosted_service_runtime",
    "resolve_node_hosted_service_runtime_for_endpoint_ref",
    "resolve_node_hosted_service_runtime_for_service_request",
    "resolve_node_hosted_service_runtime_for_service_name",
    "route_api_request_to_hosted_service_runtime",
    "require_node_host_services_runtime",
    "route_request_to_hosted_service_runtime",
    "route_request_to_registered_hosted_service",
    "start_node_host_services",
    "stop_node_host_services",
    "wait_for_hosted_service_handshake_ready",
    "wait_for_hosted_service_socket_ready",
]
