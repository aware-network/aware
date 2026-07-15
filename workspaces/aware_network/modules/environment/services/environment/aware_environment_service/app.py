"""
Aware Environment Service App.

Environment operations enter through generated API/service endpoint calls.
Raw EnvironmentOperation NetworkOperation execution is intentionally rejected at
this host boundary.
"""

import asyncio
from collections.abc import Mapping
from dataclasses import replace
import json
import os
from pathlib import Path
import time
from types import SimpleNamespace
from typing import Any, Callable, cast
from uuid import UUID, uuid4

# Core communications
from aware_comms.duplex.collection import DuplexCollection
from aware_comms.duplex.websocket.models import WsMessageFrameType
from aware_comms.http.server import HttpServer, HttpServerConfig
from aware_comms.app.app import App
from aware_comms.app.registry import app_registry
from aware_network.communications.app_config import (
    get_network_app_config as get_app_config,
)
from aware_network.communications.duplex.duplex import NetworkDuplex
from pydantic import BaseModel

from aware_environment_service.api_service_protocol import (
    _ontology_graph_meta_invoke_client,
    build_aware_environment_service_protocol_handler,
)
from aware_environment_service.config import (
    EnvironmentHostAppConfig,
    EnvironmentHostPackageRef,
    EnvironmentHostServiceApiRouteRegistryConfig,
)
from aware_environment_service.meta_commit_subscriber import (
    EnvironmentOntologyApiClients,
    EnvironmentTopologyAttachFunctionPlanner,
    EnvironmentTopologyAttachPlannerConfig,
    EnvironmentTopologyCommitSubscriber,
)
from aware_environment_service.ontology_service_api_route import (
    build_ontology_service_api_client_factory_from_routes,
)
from aware_environment_service.profile_backend import EnvironmentOntologyProfileBackend
from aware_environment_service.runtime_artifact_registry import (
    EnvironmentRuntimeArtifactRegistry,
)
from aware_environment_service.session_attention_backend import (
    CommittedEnvironmentSessionAttentionBackend,
    EnvironmentSessionAttentionNavigationContextSnapshotProvider,
    EnvironmentSessionAttentionNavigationContextViewProvider,
)
from aware_environment_service.session_service import EnvironmentSessionAttentionBackend

# Environment service
from aware_environment_service.duplex.server import EnvironmentDuplexServer
from aware_environment_service.node_transport import EnvironmentNodeTransport
from aware_environment_service.service_compat import (
    EnvironmentServicePluginTransport,
)

from aware_api_service_dto.comms.models.api import (
    ApiOperation,
    ApiRequestStatus,
    ApiStreamLifecycle,
    InvokeApiEndpointRequest,
    InvokeApiEndpointResponse,
)

# Network protocol models (DTO)
from aware_network_service_dto.comms.models.network import (
    NetworkAppType,
    NetworkOperation,
    NetworkOperationHop,
    NetworkOperationMessageType,
    NetworkOperationType,
    NetworkRequestStatus,
    NetworkResponse,
)

from aware_environment_service_dto.environment.environment import (
    ConfigureServiceApiDependencyRoutesRequest,
    ConfigureServiceApiDependencyRoutesResponse,
    EnsureReadyResponse,
)
from aware_meta_service_dto.graph.instance.function_call import (
    MetaGraphInvokeFunctionRequest,
    MetaGraphInvokeFunctionResponse,
)
from aware_service_runtime.api_ingress.host_context import service_api_host_context
from aware_service_runtime.contracts import (
    ServiceGraphGateway,
    ServiceGraphContextLike,
    ServiceOperationContext,
)
from aware_service_runtime import ServiceRuntimeHost
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    service_api_dependency_routes_from_payload,
)
from aware_environment_service_protocol.protocols import (
    ENDPOINT_BINDINGS as ENVIRONMENT_SERVICE_PROTOCOL_ENDPOINT_BINDINGS,
    ServiceProtocolEndpointBinding,
)

from aware_utils.logging import logger
from aware_utils.aware_root import ensure_aware_oig_dir, require_aware_root
from aware_utils.secrets import use_secrets_dir

OntologyApiClientFactory = Callable[[], object]


class EnvironmentOntologyArtifactHostContext:
    """Protocol-facing Environment host context backed by ontology artifacts."""

    def __init__(
        self,
        *,
        runtime_artifact_refs: tuple[object, ...] = (),
        runtime_artifact_registry: EnvironmentRuntimeArtifactRegistry | None = None,
        workspace_revision_materialized_root: Path | None = None,
    ) -> None:
        self._runtime_artifact_refs = tuple(runtime_artifact_refs)
        self._runtime_artifact_registry = runtime_artifact_registry
        self._workspace_revision_materialized_root = (
            workspace_revision_materialized_root
        )

    async def get_manifest(self) -> tuple[object, object]:
        artifact_set = _environment_ontology_runtime_artifact_set(
            artifact_refs=self._runtime_artifact_refs
        )
        descriptor = _environment_projection_descriptor(artifact_set=artifact_set)
        environment_config_id = _environment_config_id_from_artifact_set(
            artifact_set=artifact_set,
            descriptor=descriptor,
        )
        manifest_ref = _artifact_set_manifest_ref(artifact_set=artifact_set)
        package_name = str(artifact_set.get("package_name") or "").strip()
        title = str(
            _artifact_set_metadata(artifact_set).get("title")
            or package_name
            or "Environment"
        )
        manifest = SimpleNamespace(
            environment=SimpleNamespace(
                id=str(environment_config_id),
                title=title,
                canonical_language=(
                    _artifact_set_metadata(artifact_set).get("canonical_language")
                    or "python"
                ),
            )
        )
        return manifest_ref, manifest

    def get_workspace_revision_materialized_root(self) -> Path | None:
        return self._workspace_revision_materialized_root

    def get_runtime_artifact_refs(self) -> tuple[object, ...]:
        if self._runtime_artifact_registry is not None:
            return self._runtime_artifact_registry.artifact_refs()
        return self._runtime_artifact_refs

    def register_runtime_artifact_set(
        self,
        *,
        artifact_set: object,
        ontology_id: UUID | None = None,
        membership_commit_id: UUID | None = None,
    ) -> object:
        if self._runtime_artifact_registry is None:
            raise RuntimeError(
                "Environment host context does not expose a runtime artifact registry."
            )
        return self._runtime_artifact_registry.register_artifact_set(
            artifact_set=artifact_set,
            ontology_id=ontology_id,
            membership_commit_id=membership_commit_id,
        )

    async def get_environment_service_provider_modules(self) -> tuple[str, ...]:
        return ()

    async def get_environment_service_surface_paths(self) -> tuple[Path, ...]:
        return ()


def _environment_package_ref_payload(
    package_ref: EnvironmentHostPackageRef | None,
) -> dict[str, object] | None:
    if package_ref is None:
        return None
    payload: dict[str, object] = {
        "family_key": package_ref.family_key,
        "package_kind": package_ref.package_kind,
        "package_name": package_ref.package_name,
    }
    optional_fields: dict[str, object | None] = {
        "manifest_path": (
            str(package_ref.manifest_path)
            if package_ref.manifest_path is not None
            else None
        ),
        "workspace_package_id": package_ref.workspace_package_id,
        "semantic_package_id": package_ref.semantic_package_id,
        "semantic_object_instance_graph_commit_id": (
            package_ref.semantic_object_instance_graph_commit_id
        ),
        "semantic_head_commit_id": package_ref.semantic_head_commit_id,
        "semantic_branch_id": package_ref.semantic_branch_id,
        "semantic_root_kind": package_ref.semantic_root_kind,
        "semantic_root_id": package_ref.semantic_root_id,
        "semantic_root_object_instance_graph_commit_id": (
            package_ref.semantic_root_object_instance_graph_commit_id
        ),
        "source_code_package_id": package_ref.source_code_package_id,
    }
    payload.update(
        {key: value for key, value in optional_fields.items() if value is not None}
    )
    return payload


def _runtime_artifact_source_payloads(
    artifact_refs: tuple[object, ...],
) -> tuple[Mapping[str, object], ...]:
    payloads: list[Mapping[str, object]] = []
    for artifact_ref in artifact_refs:
        payload: dict[str, object] = {
            "artifact_family": getattr(artifact_ref, "artifact_family", None),
            "artifact_key": getattr(artifact_ref, "artifact_key", None),
            "artifact_role": getattr(artifact_ref, "artifact_role", None),
            "required_for": list(getattr(artifact_ref, "required_for", ()) or ()),
            "status": getattr(artifact_ref, "status", None),
            "package_name": getattr(artifact_ref, "package_name", None),
            "runtime_contract_version": getattr(
                artifact_ref,
                "runtime_contract_version",
                None,
            ),
            "provider_payload": dict(
                getattr(artifact_ref, "provider_payload", {}) or {}
            ),
            "receipt": dict(getattr(artifact_ref, "receipt", {}) or {}),
        }
        payloads.append(
            {
                key: value
                for key, value in payload.items()
                if value is not None and value != []
            }
        )
    return tuple(payloads)


def _environment_ontology_runtime_artifact_set(
    *,
    artifact_refs: tuple[object, ...],
) -> Mapping[str, object]:
    matches: list[Mapping[str, object]] = []
    saw_runtime_artifact_set = False
    for artifact_ref in artifact_refs:
        artifact_family = _artifact_ref_text(artifact_ref, "artifact_family")
        artifact_role = _artifact_ref_text(artifact_ref, "artifact_role")
        if artifact_family == "ontology_runtime_artifact_set":
            saw_runtime_artifact_set = True
        elif artifact_role != "runtime_artifact_set":
            continue
        artifact_set = _ontology_runtime_artifact_set_payload(artifact_ref)
        if artifact_set is None:
            continue
        if _environment_projection_descriptor(artifact_set=artifact_set) is None:
            continue
        matches.append(artifact_set)
    if not matches:
        if saw_runtime_artifact_set:
            raise RuntimeError(
                "Environment app boot received ontology runtime artifact-set refs "
                "without an Environment runtime projection descriptor."
            )
        raise RuntimeError(
            "Environment app boot requires ontology runtime artifact-set refs; "
            "legacy Environment runtime manifest resolver is retired."
        )
    if len(matches) > 1:
        raise RuntimeError(
            "Environment app boot resolved multiple ontology runtime artifact sets "
            "with an Environment projection descriptor."
        )
    return matches[0]


def _ontology_runtime_artifact_set_payload(
    artifact_ref: object,
) -> Mapping[str, object] | None:
    receipt = _artifact_ref_mapping(artifact_ref, "receipt")
    artifact_set = receipt.get("ontology_runtime_artifact_set")
    if isinstance(artifact_set, Mapping):
        return artifact_set
    provider_payload = _artifact_ref_mapping(artifact_ref, "provider_payload")
    artifact_set = provider_payload.get("ontology_runtime_artifact_set")
    if isinstance(artifact_set, Mapping):
        return artifact_set
    return None


def _environment_projection_descriptor(
    *,
    artifact_set: Mapping[str, object],
) -> Mapping[str, object] | None:
    for descriptor in _mapping_sequence(
        artifact_set.get("runtime_projection_descriptors")
    ):
        if str(descriptor.get("projection_name") or "").strip() == "Environment":
            return descriptor
    return None


def _environment_config_id_from_artifact_set(
    *,
    artifact_set: Mapping[str, object],
    descriptor: Mapping[str, object] | None,
) -> UUID:
    provenance = _artifact_set_provenance(artifact_set)
    for value in (
        descriptor.get("object_config_graph_id") if descriptor is not None else None,
        provenance.get("object_config_graph_id"),
        provenance.get("ontology_package_id"),
    ):
        environment_config_id = _optional_uuid(value)
        if environment_config_id is not None:
            return environment_config_id
    raise RuntimeError(
        "Environment ontology runtime artifact set is missing an Environment "
        "object_config_graph_id."
    )


def _artifact_set_manifest_ref(*, artifact_set: Mapping[str, object]) -> Path:
    provenance = _artifact_set_provenance(artifact_set)
    for key in ("ontology_manifest_path", "source_manifest_path"):
        value = _nonempty_text(provenance.get(key))
        if value is not None:
            return Path(value)
    artifact_set_id = _nonempty_text(artifact_set.get("artifact_set_id"))
    if artifact_set_id is not None:
        return Path(f"ontology-runtime-artifact-set/{artifact_set_id}")
    return Path("ontology-runtime-artifact-set/unknown")


def _artifact_set_metadata(
    artifact_set: Mapping[str, object],
) -> Mapping[str, object]:
    metadata = artifact_set.get("metadata")
    return metadata if isinstance(metadata, Mapping) else {}


def _artifact_set_provenance(
    artifact_set: Mapping[str, object],
) -> Mapping[str, object]:
    provenance = artifact_set.get("provenance")
    return provenance if isinstance(provenance, Mapping) else {}


def _artifact_ref_mapping(
    artifact_ref: object, field_name: str
) -> Mapping[str, object]:
    value = getattr(artifact_ref, field_name, None)
    return value if isinstance(value, Mapping) else {}


def _artifact_ref_text(artifact_ref: object, field_name: str) -> str:
    return str(getattr(artifact_ref, field_name, "") or "").strip()


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _optional_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        return UUID(raw)
    except ValueError:
        return None


def _nonempty_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _reverse_hops(network_op: NetworkOperation) -> list[NetworkOperationHop]:
    hops: list[NetworkOperationHop] = []
    for hop in network_op.network_operation_hop_list:
        hops.append(
            NetworkOperationHop(
                source_app_type=hop.target_app_type,
                source_node_id=hop.target_node_id,
                source_interface_id=hop.target_interface_id,
                source_environment_id=hop.target_environment_id,
                target_app_type=hop.source_app_type,
                target_node_id=hop.source_node_id,
                target_interface_id=hop.source_interface_id,
                target_environment_id=hop.source_environment_id,
            )
        )
    return hops


class _HostedRuntimeGraphGateway(ServiceGraphGateway):
    """Environment-hosted graph backend for module service plugins."""

    def __init__(
        self,
        *,
        ontology_api_client_provider: OntologyApiClientFactory,
    ) -> None:
        self._ontology_api_client_provider = ontology_api_client_provider

    async def invoke_function(
        self,
        *,
        request: MetaGraphInvokeFunctionRequest,
        graph_context: ServiceGraphContextLike | None = None,
    ) -> MetaGraphInvokeFunctionResponse:
        _ = graph_context
        ontology_client = self._ontology_api_client_provider()
        if ontology_client is not None:
            try:
                graph_client = _ontology_graph_meta_invoke_client(ontology_client)
            except RuntimeError as exc:
                return MetaGraphInvokeFunctionResponse(
                    status="failed",
                    actor_id=request.actor_id,
                    domain_branch_id=request.domain_branch_id,
                    domain_projection_hash=request.domain_projection_hash,
                    error=str(exc),
                )
        else:
            return MetaGraphInvokeFunctionResponse(
                status="failed",
                actor_id=request.actor_id,
                domain_branch_id=request.domain_branch_id,
                domain_projection_hash=request.domain_projection_hash,
                error=(
                    "Environment graph gateway function invocation requires a "
                    "configured Ontology graph API route."
                ),
            )
        response = await graph_client.invoke_function(request)
        return MetaGraphInvokeFunctionResponse.model_validate(
            response.model_dump(mode="python")
            if hasattr(response, "model_dump")
            else response
        )


class EnvironmentServiceApp(App):
    """
    Environment Service App - executes environment operations (runtime boundary).

    This service:
    1. Receives FULL NetworkOperations from the node routing layer
    2. Validates environment context and permissions (v0 stub)
    3. Executes operations via kernel runtime (OIG pipeline)
    4. Returns structured responses to the node
    """

    app_type: NetworkAppType = NetworkAppType.environment
    title: str = "Aware Environment Service"
    description: str = (
        "Runtime execution container for AWARE operations with OIG access"
    )

    http_server: HttpServer = HttpServer(
        app_type=NetworkAppType.environment.value,
        config=HttpServerConfig(requires_auth=False, requires_file_operations=False),
        route_metadata=[],
        routers={},
    )

    duplex_collection: DuplexCollection = DuplexCollection()

    def __init__(self, **data):
        super().__init__(**data)
        self._configure_secrets()
        self._config = EnvironmentHostAppConfig.from_env()
        self._runtime_artifact_registry = EnvironmentRuntimeArtifactRegistry(
            seed_artifact_refs=self._config.runtime_artifact_refs,
        )

        # Ontology-owned runtime artifact descriptors; no hosted runtime index.
        self._resolver = EnvironmentOntologyArtifactHostContext(
            workspace_revision_materialized_root=(
                self._config.workspace_revision.materialized_workspace_root
            ),
            runtime_artifact_registry=self._runtime_artifact_registry,
        )
        self._ontology_service_client_factory: OntologyApiClientFactory | None = (
            build_ontology_service_api_client_factory_from_routes(
                self._config.service_api_dependency_routes,
                selector=self._config.ontology_service_route,
            )
        )
        self._ontology_topology_subscriber_client_factory: (
            OntologyApiClientFactory | None
        ) = self._ontology_service_client_factory
        self._environment_session_attention_backend: (
            EnvironmentSessionAttentionBackend | None
        ) = None
        self._environment_session_attention_navigation_context_provider: (
            EnvironmentSessionAttentionNavigationContextViewProvider | None
        ) = None
        self._graph_gateway = _HostedRuntimeGraphGateway(
            ontology_api_client_provider=self._build_ontology_api_client_or_none,
        )
        self._host_environment_id: UUID | None = None
        self._environment_service_protocol_handler = (
            self._build_environment_service_protocol_handler()
        )
        self._environment_service_protocol_endpoint_bindings = dict(
            ENVIRONMENT_SERVICE_PROTOCOL_ENDPOINT_BINDINGS
        )
        self._node_transport = EnvironmentNodeTransport(
            duplex_collection=self.duplex_collection
        )
        self._service_plugin_transport = EnvironmentServicePluginTransport(
            graph_gateway=self._graph_gateway,
            node_transport=self._node_transport,
        )

        # Shared service runtime host (Environment is a transport adapter only).
        self._service_host = ServiceRuntimeHost(
            transport=self._service_plugin_transport,
            providers_env_var="AWARE_ENVIRONMENT_SERVICE_PLUGIN_PROVIDERS",
            enabled_services_env_var="AWARE_ENVIRONMENT_SERVICE_ENABLED_SERVICES",
        )
        self._ontology_topology_subscriber: (
            EnvironmentTopologyCommitSubscriber | None
        ) = None
        self._ontology_topology_subscriber_task: (
            asyncio.Task[tuple[Any, ...]] | None
        ) = None

        # Register duplex servers/clients according to ws_registry
        self._register_duplex_handlers()

        # Register NetworkOperation handlers
        self._register_network_operation_handlers()

        logger.info("EnvironmentServiceApp initialized with NetworkOperation handler")

    @property
    def environment_service_protocol_handler(self) -> object:
        """Generated service protocol handler hosted by this Environment app."""
        return self._environment_service_protocol_handler

    @property
    def environment_service_protocol_endpoint_refs(self) -> tuple[str, ...]:
        return tuple(sorted(self._environment_service_protocol_endpoint_bindings))

    def configure_ontology_topology_subscriber_client_factory(
        self,
        factory: OntologyApiClientFactory | None,
    ) -> None:
        """Install the host-provided Ontology API client factory for topology fanout."""
        self._ontology_topology_subscriber_client_factory = factory

    def configure_ontology_api_client_factory(
        self,
        factory: OntologyApiClientFactory | None,
    ) -> None:
        """Install the host-provided Ontology authority client factory."""
        self._ontology_service_client_factory = factory
        self._ontology_topology_subscriber_client_factory = factory
        self._environment_service_protocol_handler = (
            self._build_environment_service_protocol_handler()
        )

    def configure_environment_session_attention_backend(
        self,
        backend: EnvironmentSessionAttentionBackend | None,
    ) -> None:
        """Install the host-provided Environment session attention resolver."""
        self._environment_session_attention_backend = backend
        self._environment_service_protocol_handler = (
            self._build_environment_service_protocol_handler()
        )

    def configure_environment_session_attention_navigation_context_provider(
        self,
        provider: EnvironmentSessionAttentionNavigationContextViewProvider | None,
    ) -> None:
        """Install an Environment-owned navigation provider for attention resolution."""
        self._environment_session_attention_navigation_context_provider = provider
        if provider is None:
            self.configure_environment_session_attention_backend(None)
            return
        self.configure_environment_session_attention_backend(
            CommittedEnvironmentSessionAttentionBackend(
                snapshot_provider=(
                    EnvironmentSessionAttentionNavigationContextSnapshotProvider(
                        context_provider=provider,
                    )
                ),
            )
        )

    def _build_ontology_api_client_or_none(self) -> object | None:
        factory = self._ontology_service_client_factory
        return factory() if factory is not None else None

    def _current_host_environment_id(self) -> UUID | None:
        return self._host_environment_id

    def _current_host_environment_config_id(self) -> UUID | None:
        artifact_set = _environment_ontology_runtime_artifact_set(
            artifact_refs=self._config.runtime_artifact_refs,
        )
        descriptor = _environment_projection_descriptor(artifact_set=artifact_set)
        return _environment_config_id_from_artifact_set(
            artifact_set=artifact_set,
            descriptor=descriptor,
        )

    def _record_host_environment_id(self, environment_id: UUID) -> None:
        self._host_environment_id = environment_id

    def _build_environment_service_protocol_handler(self) -> object:
        ontology_api_client_provider = (
            self._build_ontology_api_client_or_none
            if self._ontology_service_client_factory is not None
            else None
        )
        return build_aware_environment_service_protocol_handler(
            resolver=self._resolver,
            ontology_api_client_provider=ontology_api_client_provider,
            ontology_service_route_selector=self._config.ontology_service_route,
            environment_session_attention_backend=(
                self._environment_session_attention_backend
            ),
            environment_profile_backend=EnvironmentOntologyProfileBackend(
                ontology_api_client_provider=ontology_api_client_provider,
                runtime_artifact_source_payloads=(
                    _runtime_artifact_source_payloads(
                        self._config.runtime_artifact_refs
                    )
                ),
                host_environment_id_provider=self._current_host_environment_id,
                host_environment_config_id_provider=(
                    self._current_host_environment_config_id
                ),
                host_environment_key=(
                    (os.environ.get("AWARE_ENVIRONMENT_KEY") or "").strip() or None
                ),
            ),
            host_environment_id_observer=self._record_host_environment_id,
        )

    def configure_service_api_dependency_routes(
        self,
        routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    ) -> None:
        """Install host-bound service API dependency routes at runtime."""
        self._config = replace(
            self._config,
            service_api_dependency_routes=tuple(routes),
        )
        self._ontology_service_client_factory = (
            build_ontology_service_api_client_factory_from_routes(
                routes,
                selector=self._config.ontology_service_route,
            )
        )
        self._ontology_topology_subscriber_client_factory = (
            self._ontology_service_client_factory
        )
        self._environment_service_protocol_handler = (
            self._build_environment_service_protocol_handler()
        )

    async def refresh_service_api_dependency_routes_from_node_registry(self) -> bool:
        """Refresh host-bound service routes from the Node route registry."""

        config = self._config.service_api_route_registry
        if not config.enabled:
            return False
        if config.node_id is None or config.environment_id is None:
            raise RuntimeError(
                "Environment service API route registry is enabled but node_id "
                "or environment_id is missing."
            )
        routes = await self._node_transport.discover_service_api_dependency_routes(
            environment_id=config.environment_id,
            node_id=config.node_id,
            timeout_s=config.request_timeout_s,
        )
        self.configure_service_api_dependency_routes(tuple(routes))
        logger.info(
            "Environment refreshed %s service API dependency routes from Node "
            "registry (node_id=%s environment_id=%s).",
            len(routes),
            config.node_id,
            config.environment_id,
        )
        return True

    def configure_service_api_route_registry(
        self,
        config: EnvironmentHostServiceApiRouteRegistryConfig,
    ) -> None:
        """Install host registry config for tests or embedded Node hosting."""
        self._config = replace(self._config, service_api_route_registry=config)

    @property
    def ontology_topology_subscriber_task(
        self,
    ) -> asyncio.Task[tuple[Any, ...]] | None:
        return self._ontology_topology_subscriber_task

    @property
    def ontology_topology_subscriber(
        self,
    ) -> EnvironmentTopologyCommitSubscriber | None:
        return self._ontology_topology_subscriber

    async def start_ontology_topology_subscriber(self) -> bool:
        """Start the Environment-owned Ontology commit subscriber when enabled."""
        config = self._config.meta_topology_subscriber
        if not config.enabled:
            logger.info(
                "Environment Ontology topology subscriber disabled by host config."
            )
            return False
        if (
            self._ontology_topology_subscriber_task is not None
            and not self._ontology_topology_subscriber_task.done()
        ):
            return True
        if self._ontology_topology_subscriber_client_factory is None:
            if self._config.service_api_route_registry.enabled:
                logger.info(
                    "Environment Ontology topology subscriber deferred until service "
                    "API dependency routes are installed."
                )
                return False
            raise RuntimeError(
                "Environment Ontology topology subscriber is enabled but no Ontology "
                "API client factory is configured."
            )

        ontology_api_client = self._ontology_topology_subscriber_client_factory()
        clients = EnvironmentOntologyApiClients.from_ontology_api_client(
            cast(Any, ontology_api_client)
        )
        subscriber = EnvironmentTopologyCommitSubscriber(
            clients=clients,
            planner=EnvironmentTopologyAttachFunctionPlanner(
                EnvironmentTopologyAttachPlannerConfig()
            ),
            subscriber_id=config.subscriber_id,
            topology_projection_name=config.topology_projection_name,
        )
        task = asyncio.create_task(
            subscriber.run(),
            name=f"environment-ontology-topology-subscriber:{config.subscriber_id}",
        )
        task.add_done_callback(self._log_ontology_topology_subscriber_done)
        self._ontology_topology_subscriber = subscriber
        self._ontology_topology_subscriber_task = task
        logger.info(
            "Environment Ontology topology subscriber started "
            "(subscriber_id=%s topology_projection_name=%s)",
            config.subscriber_id,
            config.topology_projection_name,
        )
        return True

    async def stop_ontology_topology_subscriber(self) -> None:
        task = self._ontology_topology_subscriber_task
        if task is None or task.done():
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            return

    @staticmethod
    def _log_ontology_topology_subscriber_done(
        task: asyncio.Task[tuple[Any, ...]],
    ) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is None:
            return
        logger.error(
            "Environment Ontology topology subscriber stopped with error: %s",
            exc,
            exc_info=exc,
        )

    def _resolve_environment_service_protocol_binding(
        self,
        *,
        endpoint_ref: str,
    ) -> ServiceProtocolEndpointBinding:
        normalized = endpoint_ref.strip()
        binding = self._environment_service_protocol_endpoint_bindings.get(normalized)
        if binding is None:
            raise ValueError(
                "Unsupported Environment service-protocol endpoint_ref "
                f"{endpoint_ref!r}."
            )
        return binding

    async def dispatch_environment_service_protocol_endpoint(
        self,
        *,
        endpoint_ref: str,
        request: BaseModel,
        operation_context: ServiceOperationContext | None = None,
    ) -> object | None:
        """Dispatch a generated Environment service protocol endpoint."""
        binding = self._resolve_environment_service_protocol_binding(
            endpoint_ref=endpoint_ref,
        )
        context = operation_context or self._build_service_protocol_operation_context(
            request=request,
        )
        if binding.endpoint_name == "configure_service_api_dependency_routes":
            typed_request = ConfigureServiceApiDependencyRoutesRequest.model_validate(
                request.model_dump(mode="json")
                if isinstance(request, BaseModel)
                else request
            )
            return await self._configure_service_api_dependency_routes_response(
                request=typed_request,
            )
        with service_api_host_context(
            operation_context=context,
            graph_gateway=self._graph_gateway,
            service_name="aware_environment",
            service_api_dependency_routes=self._config.service_api_dependency_routes,
        ):
            request_payload = request.model_dump(mode="json")
            response = await binding.invoke(
                self._environment_service_protocol_handler,
                cast(BaseModel, cast(object, request_payload)),
                None,
            )
            if binding.endpoint_name == "ensure_ready" and isinstance(
                response,
                BaseModel,
            ):
                self._record_host_environment_id_from_readiness(
                    request=request,
                    response=response,
                )
                return self._with_host_readiness_receipt_evidence(response)
            return response

    def _record_host_environment_id_from_readiness(
        self,
        *,
        request: BaseModel,
        response: BaseModel,
    ) -> None:
        status = str(getattr(response, "status", "") or "").strip().casefold()
        if status != "ready":
            return
        environment_id = getattr(response, "environment_id", None) or getattr(
            request,
            "environment_id",
            None,
        )
        if isinstance(environment_id, UUID):
            self._host_environment_id = environment_id

    def _build_service_protocol_operation_context(
        self,
        *,
        request: BaseModel,
    ) -> ServiceOperationContext:
        environment_id = self._request_uuid_or_default(request, "environment_id")
        return ServiceOperationContext(
            actor_id=getattr(request, "actor_id", None),
            environment_id=environment_id,
            process_id=self._request_uuid_or_default(request, "process_id"),
            thread_id=self._request_uuid_or_default(request, "thread_id"),
            branch_id=self._request_uuid_or_default(request, "branch_id"),
            projection_hash=(
                getattr(request, "projection_hash", None)
                or "environment.service_protocol.app"
            ),
        )

    @staticmethod
    def _request_uuid_or_default(request: BaseModel, field_name: str) -> UUID:
        value = getattr(request, field_name, None)
        if isinstance(value, UUID):
            return value
        return UUID(int=0)

    def _configure_secrets(self) -> None:
        secrets_dir = (os.environ.get("AWARE_SECRETS_DIR") or "").strip()
        if not secrets_dir:
            return
        use_secrets_dir(secrets_dir)
        logger.info(
            "Secrets dir enabled for environment service (AWARE_SECRETS_DIR=%s)",
            secrets_dir,
        )

    def _configure_persistence_backend(self) -> None:
        """Ensure the ORM persistence backend is configured before executing runtime operations."""
        backend = os.environ.get("AWARE_PERSISTENCE_BACKEND")
        db_url = os.environ.get("DATABASE_URL")

        if backend:
            logger.info("Using persistence backend from environment: %s", backend)
            return

        if db_url:
            os.environ.setdefault("AWARE_PERSISTENCE_BACKEND", "db")
            logger.info(
                "DATABASE_URL detected; defaulting AWARE_PERSISTENCE_BACKEND to 'db' (set explicitly to override)."
            )
            return

        os.environ["AWARE_PERSISTENCE_BACKEND"] = "fs"
        logger.info(
            "No DATABASE_URL provided; defaulting AWARE_PERSISTENCE_BACKEND to 'fs'."
        )

    def _with_host_readiness_receipt_evidence(
        self,
        response: BaseModel,
    ) -> BaseModel:
        receipt = getattr(response, "readiness_receipt", None)
        if receipt is None:
            return response

        updates: dict[str, object] = {}
        package_ref_payload = _environment_package_ref_payload(
            self._config.environment_package_ref
        )
        if (
            package_ref_payload is not None
            and getattr(receipt, "environment_package_ref", None) is None
        ):
            updates["environment_package_ref"] = package_ref_payload

        if not updates:
            return response
        return response.model_copy(
            update={"readiness_receipt": receipt.model_copy(update=updates)}
        )

    def _register_duplex_handlers(self):
        """Register duplex communication handlers per ws_registry for ENVIRONMENT app"""
        # ENVIRONMENT must accept connections from NETWORK_NODE (server side)
        server = EnvironmentDuplexServer(
            client_type=NetworkAppType.network_node.value,
            server_type=NetworkAppType.environment.value,
        )
        server.set_environment_app_id(uuid4())
        self.duplex_collection.register_duplex(server)

    def _register_network_operation_handlers(self):
        """Register NetworkOperation message handlers on NetworkDuplex"""

        async def _handle_request(
            data: str, message_type: WsMessageFrameType
        ) -> str | None:
            return await self._handle_network_operation_request(data, message_type)

        async def _handle_notification(
            data: str, message_type: WsMessageFrameType
        ) -> None:
            await self._handle_network_operation_notification(data, message_type)
            return None

        # Register on the shared NetworkDuplex handler map
        NetworkDuplex.register_handler(
            message_type=WsMessageFrameType.REQUEST,
            handler=_handle_request,
        )
        NetworkDuplex.register_handler(
            message_type=WsMessageFrameType.NOTIFICATION,
            handler=_handle_notification,
        )

    async def _handle_api_endpoint_network_operation(
        self,
        *,
        network_op: NetworkOperation,
    ) -> str:
        if network_op.api_operation is None or network_op.api_operation.request is None:
            raise RuntimeError(
                "NetworkOperation(type=api) requires api_operation.request"
            )
        if not isinstance(network_op.api_operation.request, InvokeApiEndpointRequest):
            raise RuntimeError(
                "Environment API ingress requires InvokeApiEndpointRequest"
            )

        request = network_op.api_operation.request
        try:
            endpoint_request = self._api_endpoint_request_model(
                endpoint_ref=request.endpoint_ref,
                request_payload=request.request_payload,
            )
            endpoint_response = (
                await self.dispatch_environment_service_protocol_endpoint(
                    endpoint_ref=request.endpoint_ref,
                    request=endpoint_request,
                )
            )
            response_payload = (
                endpoint_response.model_dump(mode="json")
                if isinstance(endpoint_response, BaseModel)
                else endpoint_response
            )
            if request.endpoint_ref == "environment.ready.ensure_ready":
                await self._validate_environment_runtime_package_ref_gate_after_ready(
                    response=EnsureReadyResponse.model_validate(response_payload),
                )
            api_status = ApiRequestStatus.succeeded
            api_error = None
        except Exception as exc:
            response_payload = None
            api_status = ApiRequestStatus.failed
            api_error = str(exc)

        response = NetworkOperation(
            id=network_op.id,
            message_type=NetworkOperationMessageType.response,
            type=NetworkOperationType.api,
            network_response=NetworkResponse(
                network_request_id=(
                    network_op.network_request.id
                    if network_op.network_request is not None
                    else None
                ),
                status=(
                    NetworkRequestStatus.succeeded
                    if api_status is ApiRequestStatus.succeeded
                    else NetworkRequestStatus.failed
                ),
                error=api_error,
            ),
            api_operation=ApiOperation(
                response=InvokeApiEndpointResponse(
                    actor_id=request.actor_id,
                    status=api_status,
                    error=api_error,
                    response_payload=cast(Any, response_payload),
                    stream_lifecycle=ApiStreamLifecycle.auto_close,
                )
            ),
            network_operation_hop_list=_reverse_hops(network_op),
        )
        return response.model_dump_json()

    def _api_endpoint_request_model(
        self,
        *,
        endpoint_ref: str,
        request_payload: object,
    ) -> BaseModel:
        binding = self._resolve_environment_service_protocol_binding(
            endpoint_ref=endpoint_ref,
        )
        from aware_api.invoker import resolve_api_endpoint_model_class

        request_model = resolve_api_endpoint_model_class(binding.request_type_ref)
        return request_model.model_validate(request_payload)

    async def _handle_network_operation_request(
        self, data: str, message_type: WsMessageFrameType
    ) -> str | None:
        """
        Handle incoming NetworkOperation requests.

        Args:
            data: Serialized NetworkOperation JSON
            message_type: The message frame type

        Returns:
            Serialized response JSON
        """
        network_op: NetworkOperation | None = None
        request_json = data
        started_at_s = time.monotonic()
        try:
            network_op = NetworkOperation.model_validate_json(request_json)
            if (
                network_op.network_request is not None
                and network_op.network_request.id is None
            ):
                network_op.network_request.id = uuid4()
                request_json = network_op.model_dump_json()
            self._node_transport.remember_node_binding(network_op)
            if network_op.type == NetworkOperationType.api:
                return await self._handle_api_endpoint_network_operation(
                    network_op=network_op,
                )

            environment_id: UUID | None = None
            node_id: UUID | None = None

            if len(network_op.network_operation_hop_list) == 1:
                hop = network_op.network_operation_hop_list[0]
                node_id = hop.source_node_id
                environment_id = hop.target_environment_id

            logger.info(
                "env.op.request type=%s environment_id=%s node_id=%s network_operation_id=%s network_request_id=%s",
                network_op.type,
                environment_id,
                node_id,
                network_op.id,
                (network_op.network_request.id if network_op.network_request else None),
            )
            if network_op.type == NetworkOperationType.environment:
                raise RuntimeError(
                    "Raw EnvironmentOperation NetworkOperation ingress is removed; "
                    "invoke the generated Environment API endpoint instead."
                )
            raise RuntimeError(
                "EnvironmentServiceApp accepts generated API endpoint requests only."
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - started_at_s) * 1000)
            logger.exception(
                "env.op.exception network_operation_id=%s network_request_id=%s duration_ms=%s error=%s",
                network_op.id if network_op else None,
                (
                    network_op.network_request.id
                    if (network_op and network_op.network_request)
                    else None
                ),
                duration_ms,
                str(e),
            )
            return self._build_failed_network_operation_response(
                data=data,
                network_op=network_op,
                error=e,
            )

    async def _configure_service_api_dependency_routes_response(
        self,
        *,
        request: ConfigureServiceApiDependencyRoutesRequest,
    ) -> ConfigureServiceApiDependencyRoutesResponse:
        try:
            routes = service_api_dependency_routes_from_payload(
                request.routes,
                base_dir=Path.cwd(),
            )
            self.configure_service_api_dependency_routes(routes)
            route_consumers_started = await self.start_ontology_topology_subscriber()
            return ConfigureServiceApiDependencyRoutesResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="succeeded",
                error=None,
                route_count=len(routes),
                route_consumers_started=route_consumers_started,
            )
        except Exception as exc:
            return ConfigureServiceApiDependencyRoutesResponse(
                actor_id=request.actor_id,
                environment_id=request.environment_id,
                process_id=request.process_id,
                thread_id=request.thread_id,
                branch_id=request.branch_id,
                projection_hash=request.projection_hash,
                status="failed",
                error=str(exc),
                route_count=0,
                route_consumers_started=False,
            )

    def _build_failed_network_operation_response(
        self,
        *,
        data: str,
        network_op: NetworkOperation | None,
        error: Exception,
    ) -> str:
        """
        Best-effort fallback: ensure the ENVIRONMENT service always returns a
        NetworkOperation RESPONSE, even if request DTO validation fails.
        """

        raw: dict[str, Any] | None = None
        try:
            raw = json.loads(data)
        except Exception:
            raw = None

        op_id = uuid4()
        if network_op is not None:
            op_id = network_op.id
        elif isinstance(raw, dict) and raw.get("id") is not None:
            try:
                op_id = UUID(str(raw["id"]))
            except Exception:
                op_id = uuid4()

        op_type = NetworkOperationType.api
        if network_op is not None:
            op_type = network_op.type
        elif isinstance(raw, dict) and raw.get("type") is not None:
            try:
                op_type = NetworkOperationType(str(raw["type"]))
            except Exception:
                op_type = NetworkOperationType.api

        request_hop: NetworkOperationHop | None = None
        if network_op is not None and network_op.network_operation_hop_list:
            request_hop = network_op.network_operation_hop_list[0]
        elif isinstance(raw, dict):
            hop_list = raw.get("network_operation_hop_list")
            if isinstance(hop_list, list) and hop_list:
                try:
                    request_hop = NetworkOperationHop.model_validate(hop_list[0])
                except Exception:
                    request_hop = None

        response_hops: list[NetworkOperationHop] = []
        if request_hop is not None:
            response_hops.append(
                NetworkOperationHop(
                    source_app_type=request_hop.target_app_type,
                    source_node_id=request_hop.target_node_id,
                    source_interface_id=request_hop.target_interface_id,
                    source_environment_id=request_hop.target_environment_id,
                    target_app_type=request_hop.source_app_type,
                    target_node_id=request_hop.source_node_id,
                    target_interface_id=request_hop.source_interface_id,
                    target_environment_id=request_hop.source_environment_id,
                )
            )

        network_request_id: UUID | None = None
        if network_op is not None and network_op.network_request is not None:
            network_request_id = network_op.network_request.id
        elif isinstance(raw, dict):
            raw_req = raw.get("network_request")
            if isinstance(raw_req, dict) and raw_req.get("id") is not None:
                try:
                    network_request_id = UUID(str(raw_req["id"]))
                except Exception:
                    network_request_id = None

        response = NetworkOperation(
            id=op_id,
            message_type=NetworkOperationMessageType.response,
            type=op_type,
            network_response=NetworkResponse(
                network_request_id=network_request_id,
                status=NetworkRequestStatus.failed,
                error=str(error),
            ),
            network_operation_hop_list=response_hops,
        )
        return response.model_dump_json()

    async def _handle_network_operation_notification(
        self, data: str, message_type: WsMessageFrameType
    ) -> None:
        """
        Handle incoming NetworkOperation notifications.

        Args:
            data: Serialized NetworkOperation JSON
            message_type: The message frame type
        """
        try:
            logger.debug("env.op.notification_received")

            network_op = NetworkOperation.model_validate_json(data)
            self._node_transport.remember_node_binding(network_op)
            if network_op.type == NetworkOperationType.environment:
                raise RuntimeError(
                    "Raw EnvironmentOperation NetworkOperation notifications are removed; "
                    "publish through canonical API/event contracts instead."
                )
            if network_op.type == NetworkOperationType.api:
                raise RuntimeError("Environment API notifications are not supported.")

        except Exception as e:
            logger.error(
                "env.op.notification_error error=%s",
                str(e),
                exc_info=True,
            )

    async def start(self, host="0.0.0.0"):
        """Start Environment Service"""
        self._configure_storage()
        self._configure_persistence_backend()
        await self._warmup_environment_runtime()
        await self.start_ontology_topology_subscriber()

        # Register self in the global registry
        app_registry.register_app(self)
        app_port = get_app_config(self.app_type).PORT

        logger.info(f"Starting Environment Service on {host}:{app_port}")
        logger.info("Environment service ready to handle NetworkOperations")

        # Start the app
        await self.run_prod(host=host, port=app_port)

    def _configure_storage(self) -> None:
        """Fail-fast checks for commit durability."""
        aware_root = require_aware_root(purpose="ENVIRONMENT storage")
        oig_dir = ensure_aware_oig_dir(aware_root=aware_root, require_writable=True)

        logger.info(
            "OIG commit store ready (AWARE_ROOT=%s oig_dir=%s)", aware_root, oig_dir
        )
        logger.info(
            "OIG commit store source sync skipped; Environment service no longer "
            "resolves composed runtime manifests during boot."
        )

    async def _warmup_environment_runtime(self) -> None:
        """Load ontology artifact metadata and configure explicit service plugins."""
        try:
            manifest_path, manifest = await self._resolver.get_manifest()
            environment_config_id = UUID(manifest.environment.id)
            await self._configure_service_plugins()
            logger.info(
                "Environment ontology artifact context loaded "
                "(environment_config_id=%s title=%s manifest_ref=%s)",
                environment_config_id,
                manifest.environment.title,
                manifest_path,
            )

            if self._config.environment_package_ref is not None:
                logger.info(
                    "Deferring Environment package-ref gate until ensure_ready; "
                    "hosted runtime index warmup is retired."
                )
            logger.info(
                "Environment runtime index warmup skipped "
                "(environment_config_id=%s).",
                environment_config_id,
            )
        except Exception:
            logger.exception(
                "Failed to load Environment ontology artifact context; service cannot start."
            )
            raise

    async def _validate_environment_runtime_package_ref_gate_after_ready(
        self,
        *,
        response: EnsureReadyResponse,
    ) -> None:
        package_ref = self._config.environment_package_ref
        if package_ref is None:
            return
        if response.status.strip().lower() != "ready":
            return

        manifest_environment_config_id = response.environment_id
        self._validate_environment_runtime_ontology_artifact_set_gate(
            package_ref=package_ref,
            manifest_environment_config_id=manifest_environment_config_id,
        )
        return

    async def _configure_service_plugins(self) -> None:
        provider_modules = (
            await self._resolver.get_environment_service_provider_modules()
        )
        service_surface_paths = (
            await self._resolver.get_environment_service_surface_paths()
        )
        self._service_host.configure(
            provider_modules=provider_modules,
            service_surface_paths=service_surface_paths,
        )
        logger.info(
            "Environment service plugins configured (providers=%s loaded=%s surfaces=%s)",
            sorted(provider_modules),
            list(self._service_host.plugin_services),
            [str(path) for path in service_surface_paths],
        )

    async def _validate_environment_runtime_package_ref_gate(
        self,
        *,
        manifest_environment_config_id: UUID,
    ) -> Any:
        package_ref = self._config.environment_package_ref
        if package_ref is None:
            raise RuntimeError(
                "Environment runtime package-ref gate requires a package ref."
            )
        return self._validate_environment_runtime_ontology_artifact_set_gate(
            package_ref=package_ref,
            manifest_environment_config_id=manifest_environment_config_id,
        )

    def _validate_environment_runtime_ontology_artifact_set_gate(
        self,
        *,
        package_ref: EnvironmentHostPackageRef,
        manifest_environment_config_id: UUID,
    ) -> Any:
        artifact_set = _environment_ontology_runtime_artifact_set(
            artifact_refs=self._config.runtime_artifact_refs,
        )
        descriptor = _environment_projection_descriptor(artifact_set=artifact_set)
        artifact_environment_config_id = _environment_config_id_from_artifact_set(
            artifact_set=artifact_set,
            descriptor=descriptor,
        )
        if artifact_environment_config_id != manifest_environment_config_id:
            raise RuntimeError(
                "Environment runtime package-ref gate rejected artifacts: "
                "OntologyRuntimeArtifactSet Environment projection does not "
                "match ready manifest environment id: "
                f"manifest={manifest_environment_config_id} "
                f"artifact_set={artifact_environment_config_id}"
            )
        expected_environment_config_id = _environment_config_id_from_package_ref(
            package_ref
        )
        if (
            expected_environment_config_id is not None
            and expected_environment_config_id != manifest_environment_config_id
        ):
            raise RuntimeError(
                "Environment runtime package-ref gate rejected manifest: "
                "manifest environment id does not match WorkspaceRevision "
                "EnvironmentConfigPackage truth: "
                f"manifest={manifest_environment_config_id} "
                f"package_ref={expected_environment_config_id}"
            )
        package_name = str(artifact_set.get("package_name") or "").strip()
        logger.info(
            "Environment runtime artifact-set gate passed "
            "(package=%s environment_config_id=%s)",
            package_name or "unknown",
            artifact_environment_config_id,
        )
        return artifact_set

    def get_duplex_for_connection(self, connection_id: UUID):
        """Get a duplex instance for a specific connection ID"""
        # Try to get from server
        server = self.duplex_collection.get_ws_connection(connection_id)
        if server is not None:
            return server
        return None


def _environment_config_id_from_package_ref(
    package_ref: EnvironmentHostPackageRef,
) -> UUID | None:
    if (package_ref.semantic_root_kind or "").strip() != "environment_config":
        return None
    raw_environment_config_id = (package_ref.semantic_root_id or "").strip()
    if not raw_environment_config_id:
        return None
    try:
        return UUID(raw_environment_config_id)
    except ValueError as exc:
        raise RuntimeError(
            "Environment runtime package-ref gate requires "
            "environment_config semantic_root_id to be a UUID."
        ) from exc


if __name__ == "__main__":
    app = EnvironmentServiceApp()
    asyncio.run(app.start())
