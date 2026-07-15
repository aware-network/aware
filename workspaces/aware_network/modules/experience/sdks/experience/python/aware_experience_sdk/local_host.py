from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from aware_experience_service_api._bindings import (
    EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF,
    EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF,
    EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF,
    EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF,
    EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF,
    EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF,
    EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF,
    EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF,
)

from .client import ExperienceSdkClient

if TYPE_CHECKING:
    from aware_comms import DuplexIpcEndpoint
    from aware_service_runtime.contracts import ServiceHostHandshakeResponse
    from aware_service_runtime.duplex_client import ServiceHostDuplexClient
    from aware_service_runtime.service_api_dependency_routes import (
        ServiceApiDependencyRouteDescriptor,
    )
    from aware_service_service.app import ServiceHostApp


DEFAULT_SOCKET_RELATIVE_PATH = Path(
    ".aware/workspaces/aware_network/modules/experience/services/experience/experience-service.sock"
)
DEFAULT_READY_RELATIVE_PATH = Path(
    ".aware/workspaces/aware_network/modules/experience/services/experience/experience-service.ready.json"
)
DEFAULT_STATE_ROOT_RELATIVE_PATH = Path(
    ".aware/workspaces/aware_network/modules/experience/services/experience/state"
)
DEFAULT_ENVIRONMENT_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/environment/services/environment/aware.service.toml"
)
DEFAULT_ATTENTION_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/attention/services/attention/aware.service.toml"
)
DEFAULT_IDENTITY_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/identity/services/identity/aware.service.toml"
)
DEFAULT_REACTIVITY_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/reactivity/services/reactivity/aware.service.toml"
)
DEFAULT_EXPERIENCE_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/experience/services/experience/aware.service.toml"
)
DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS = (
    DEFAULT_ENVIRONMENT_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_ATTENTION_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_IDENTITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_REACTIVITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_EXPERIENCE_IMPLEMENTATION_TOML_RELATIVE_PATH,
)
DEFAULT_DEPENDENCY_PROVIDER_TOML_RELATIVE_PATHS = (
    DEFAULT_ENVIRONMENT_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_ATTENTION_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_IDENTITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
    DEFAULT_REACTIVITY_IMPLEMENTATION_TOML_RELATIVE_PATH,
)
DEFAULT_API_CLIENT_ENDPOINT = "aware-service-host://aware-experience-service-local"
LOCAL_ENVIRONMENT_API_ENDPOINT = "aware-environment-service://local"
EXPERIENCE_API_SERVICE_NAME = "aware_experience"
EXPERIENCE_SDK_REPO_ROOT_ENV_VARS = (
    "AWARE_EXPERIENCE_SDK_REPO_ROOT",
    "AWARE_EXPERIENCE_REPO_ROOT",
    "AWARE_EXPERIENCE_SERVICE_REPO_ROOT",
    "AWARE_EXPERIENCE_SERVICE_REPOSITORY_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)
EXPERIENCE_API_ENDPOINT_REFS = {
    "apply_view_event_transition": (
        EXPERIENCE__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION__APPLY_EXPERIENCE_VIEW_EVENT_TRANSITION_ENDPOINT_REF
    ),
    "ensure_session_handoff": (
        EXPERIENCE__SESSION_HANDOFF__ENSURE_EXPERIENCE_SESSION_HANDOFF_ENDPOINT_REF
    ),
    "resolve_session_context": (
        EXPERIENCE__SESSION_CONTEXT__RESOLVE_EXPERIENCE_SESSION_CONTEXT_ENDPOINT_REF
    ),
    "resolve_session_view_frame": (
        EXPERIENCE__SESSION_VIEW_FRAME__RESOLVE_EXPERIENCE_SESSION_VIEW_FRAME_ENDPOINT_REF
    ),
    "get_section_graph_binding_catalog": (
        EXPERIENCE__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_SECTION_GRAPH_BINDING_CATALOG_ENDPOINT_REF
    ),
    "get_layout_graph_binding_catalog": (
        EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_CATALOG_ENDPOINT_REF
    ),
    "get_layout_graph_binding_state": (
        EXPERIENCE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE__GET_EXPERIENCE_LAYOUT_GRAPH_BINDING_STATE_ENDPOINT_REF
    ),
    "activate_layout_graph_binding": (
        EXPERIENCE__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING__ACTIVATE_EXPERIENCE_LAYOUT_GRAPH_BINDING_ENDPOINT_REF
    ),
    "invoke_view_invocation_action": (
        EXPERIENCE__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION__INVOKE_EXPERIENCE_VIEW_INVOCATION_ACTION_ENDPOINT_REF
    ),
    "get_session_handoff_status": (
        EXPERIENCE__SESSION_HANDOFF__GET_EXPERIENCE_SESSION_HANDOFF_STATUS_ENDPOINT_REF
    ),
}


@dataclass(frozen=True, slots=True)
class LocalExperienceServiceHostConfig:
    repo_root: Path
    socket_path: Path
    implementation_toml_paths: tuple[Path, ...]
    reference_experience_toml_paths: tuple[Path, ...]
    runtime_manifest_path: Path | None
    environment_api_endpoint: str | None
    ready_file_path: Path | None
    state_root_path: Path | None

    @property
    def endpoint(self) -> DuplexIpcEndpoint:
        from aware_comms import DuplexIpcEndpoint

        return DuplexIpcEndpoint.unix_socket(socket_path=str(self.socket_path))


@dataclass(frozen=True, slots=True)
class LocalExperienceServiceApiDependencyRouteInstallResult:
    handshake: ServiceHostHandshakeResponse
    routes: tuple[ServiceApiDependencyRouteDescriptor, ...]
    route_count: int


@dataclass(frozen=True, slots=True)
class _LocalApiPackage:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class _LocalServiceApiPackageBridge:
    api_package_id: UUID
    api_package: _LocalApiPackage
    description: str | None = None


@dataclass(frozen=True, slots=True)
class _LocalServicePackage:
    id: UUID
    name: str
    provided_api_packages: tuple[_LocalServiceApiPackageBridge, ...] = ()
    required_api_packages: tuple[_LocalServiceApiPackageBridge, ...] = ()
    dependencies: tuple[Mapping[str, object], ...] = ()


@dataclass(frozen=True, slots=True)
class _LocalServicePackageRouteSpec:
    service_package: _LocalServicePackage
    service_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _LiveServiceHostProcess:
    returncode: int | None = None


@dataclass(frozen=True, slots=True)
class _LocalServiceHostProviderRuntime:
    socket_path: Path
    request_timeout_s: float
    handshake: ServiceHostHandshakeResponse
    routable_service_names: tuple[str, ...]
    endpoint_refs_by_service: Mapping[str, tuple[str, ...]]
    stream_endpoint_refs_by_service: Mapping[str, tuple[str, ...]]
    process: _LiveServiceHostProcess = field(default_factory=_LiveServiceHostProcess)

    def advertised_endpoint_refs_by_service(self) -> Mapping[str, tuple[str, ...]]:
        return self.endpoint_refs_by_service

    def advertised_stream_endpoint_refs_by_service(
        self,
    ) -> Mapping[str, tuple[str, ...]]:
        return self.stream_endpoint_refs_by_service


def resolve_local_experience_service_host_config(
    *,
    socket_path: str | Path | None = None,
    implementation_toml_paths: Sequence[str | Path] = (),
    reference_experience_toml_paths: Sequence[str | Path] = (),
    runtime_manifest_path: str | Path | None = None,
    environment_api_endpoint: str | None = LOCAL_ENVIRONMENT_API_ENDPOINT,
    ready_file_path: str | Path | None = DEFAULT_READY_RELATIVE_PATH,
    state_root_path: str | Path | None = DEFAULT_STATE_ROOT_RELATIVE_PATH,
    repo_root: str | Path | None = None,
) -> LocalExperienceServiceHostConfig:
    root = _resolve_repo_root(repo_root)
    return LocalExperienceServiceHostConfig(
        repo_root=root,
        socket_path=_resolve_path(
            root=root,
            value=socket_path or DEFAULT_SOCKET_RELATIVE_PATH,
        ),
        implementation_toml_paths=tuple(
            _resolve_path(root=root, value=value)
            for value in (
                implementation_toml_paths or DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS
            )
        ),
        reference_experience_toml_paths=tuple(
            _resolve_path(root=root, value=value)
            for value in reference_experience_toml_paths
        ),
        runtime_manifest_path=(
            _resolve_path(root=root, value=runtime_manifest_path)
            if runtime_manifest_path is not None
            else None
        ),
        environment_api_endpoint=_clean_optional_text(environment_api_endpoint),
        ready_file_path=(
            _resolve_path(root=root, value=ready_file_path)
            if ready_file_path is not None
            else None
        ),
        state_root_path=(
            _resolve_path(root=root, value=state_root_path)
            if state_root_path is not None
            else None
        ),
    )


def build_local_experience_service_host_app(
    *,
    config: LocalExperienceServiceHostConfig,
) -> ServiceHostApp:
    from aware_service_service.config import (
        ServiceHostAppConfig,
        ServiceHostEnvironmentConfig,
        ServiceHostImplementationPackageConfig,
        ServiceHostReferencePackageConfig,
    )

    return build_service_host_app(
        config=ServiceHostAppConfig(
            kernel_repo_root=config.repo_root,
            implementation_packages=ServiceHostImplementationPackageConfig(
                toml_paths=config.implementation_toml_paths,
            ),
            reference_packages=ServiceHostReferencePackageConfig(
                experience_toml_paths=config.reference_experience_toml_paths,
            ),
            runtime_manifest_path=config.runtime_manifest_path,
            environment=ServiceHostEnvironmentConfig(
                api_endpoint=config.environment_api_endpoint,
            ),
        )
    )


def build_service_host_app(*, config: object) -> ServiceHostApp:
    from aware_service_service.environment_api_client import (
        build_service_host_app as _build_service_host_app,
    )

    return _build_service_host_app(config=cast(Any, config))


def resolve_local_experience_service_api_dependency_routes(
    *,
    config: LocalExperienceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    handshake: ServiceHostHandshakeResponse,
    request_timeout_s: float = 30.0,
    consumer_toml_path: (
        str | Path
    ) = DEFAULT_EXPERIENCE_IMPLEMENTATION_TOML_RELATIVE_PATH,
    provider_toml_paths: Sequence[str | Path] = (),
) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
    """Resolve Experience local ServiceHost API dependency routes."""

    from aware_service_runtime.service_api_dependency_resolution import (
        ServiceApiProviderRuntime,
        resolve_local_service_api_dependency_routes,
    )

    resolved_config = config or resolve_local_experience_service_host_config(
        socket_path=socket_path,
        repo_root=repo_root,
    )
    consumer_path = _resolve_path(
        root=resolved_config.repo_root,
        value=consumer_toml_path,
    )
    provider_paths = tuple(
        _resolve_path(root=resolved_config.repo_root, value=value)
        for value in (
            provider_toml_paths
            or _default_dependency_provider_toml_paths(
                config=resolved_config,
                consumer_toml_path=consumer_path,
            )
        )
    )
    consumer = _local_service_package_route_spec_from_toml(
        toml_path=consumer_path,
    ).service_package
    provider_specs = tuple(
        _local_service_package_route_spec_from_toml(toml_path=path)
        for path in provider_paths
    )
    endpoint_refs_by_service, stream_refs_by_service = (
        _api_dispatch_route_maps_from_handshake(handshake=handshake)
    )
    return resolve_local_service_api_dependency_routes(
        consumer_service_packages=(consumer,),
        provider_runtimes=tuple(
            ServiceApiProviderRuntime(
                service_package=provider_spec.service_package,
                runtime=_LocalServiceHostProviderRuntime(
                    socket_path=resolved_config.socket_path,
                    request_timeout_s=request_timeout_s,
                    handshake=handshake,
                    routable_service_names=provider_spec.service_names,
                    endpoint_refs_by_service=_filter_route_map(
                        endpoint_refs_by_service,
                        service_names=provider_spec.service_names,
                    ),
                    stream_endpoint_refs_by_service=_filter_route_map(
                        stream_refs_by_service,
                        service_names=provider_spec.service_names,
                        require_non_empty=False,
                    ),
                ),
            )
            for provider_spec in provider_specs
        ),
    )


async def install_local_experience_service_api_dependency_routes(
    *,
    config: LocalExperienceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    repo_root: str | Path | None = None,
    request_timeout_s: float = 30.0,
    consumer_toml_path: (
        str | Path
    ) = DEFAULT_EXPERIENCE_IMPLEMENTATION_TOML_RELATIVE_PATH,
    provider_toml_paths: Sequence[str | Path] = (),
) -> LocalExperienceServiceApiDependencyRouteInstallResult:
    """Install local Experience dependency routes through ServiceHost control."""

    from aware_service_runtime.service_api_dependency_installation import (
        install_service_api_dependency_routes,
    )

    resolved_config = config or resolve_local_experience_service_host_config(
        socket_path=socket_path,
        repo_root=repo_root,
    )
    client = _build_service_host_duplex_client(endpoint=resolved_config.endpoint)
    handshake = await client.send_handshake(timeout_s=request_timeout_s)
    routes = resolve_local_experience_service_api_dependency_routes(
        config=resolved_config,
        handshake=handshake,
        request_timeout_s=request_timeout_s,
        consumer_toml_path=consumer_toml_path,
        provider_toml_paths=provider_toml_paths,
    )
    response = await install_service_api_dependency_routes(
        client=client,
        routes=routes,
        timeout_s=request_timeout_s,
    )
    return LocalExperienceServiceApiDependencyRouteInstallResult(
        handshake=handshake,
        routes=routes,
        route_count=response.route_count,
    )


def build_local_experience_service_host_duplex_client_factory(
    *,
    config: LocalExperienceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> Callable[[], ServiceHostDuplexClient]:
    resolved_config = config or resolve_local_experience_service_host_config(
        socket_path=socket_path,
        repo_root=repo_root,
    )
    endpoint = resolved_config.endpoint

    def _factory() -> ServiceHostDuplexClient:
        return _build_service_host_duplex_client(endpoint=endpoint)

    return _factory


def build_local_experience_service_host_api_client(
    *,
    config: LocalExperienceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    actor_id: UUID | None = None,
    endpoint: str = DEFAULT_API_CLIENT_ENDPOINT,
    request_timeout_s: float = 30.0,
    invocation_context: dict[str, object] | None = None,
    repo_root: str | Path | None = None,
) -> Any:
    """Build a generated Experience API client backed by ServiceHost IPC."""

    from aware_experience_service_api import AwareExperienceServiceApiClient
    from aware_service_runtime.local_service_host_api_client import (
        LocalServiceHostAwareApiClient,
    )

    return AwareExperienceServiceApiClient(
        client=LocalServiceHostAwareApiClient(
            actor_id=actor_id,
            client_factory=build_local_experience_service_host_duplex_client_factory(
                config=config,
                socket_path=socket_path,
                repo_root=repo_root,
            ),
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            invocation_context=cast(Any, invocation_context),
        )
    )


def build_local_experience_sdk_client(
    *,
    config: LocalExperienceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    actor_id: UUID | None = None,
    endpoint: str = DEFAULT_API_CLIENT_ENDPOINT,
    request_timeout_s: float = 30.0,
    invocation_context: dict[str, object] | None = None,
    repo_root: str | Path | None = None,
) -> ExperienceSdkClient:
    """Build an Experience SDK client backed by local ServiceHost IPC."""

    return ExperienceSdkClient(
        api_client=build_local_experience_service_host_api_client(
            config=config,
            socket_path=socket_path,
            actor_id=actor_id,
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            invocation_context=invocation_context,
            repo_root=repo_root,
        )
    )


def _build_service_host_duplex_client(
    *,
    endpoint: DuplexIpcEndpoint,
) -> ServiceHostDuplexClient:
    from aware_service_runtime.duplex_client import ServiceHostDuplexClient

    return ServiceHostDuplexClient(endpoint=endpoint)


def _default_dependency_provider_toml_paths(
    *,
    config: LocalExperienceServiceHostConfig,
    consumer_toml_path: Path,
) -> tuple[Path, ...]:
    return tuple(
        path
        for path in config.implementation_toml_paths
        if path.resolve() != consumer_toml_path.resolve()
    )


def _local_service_package_route_spec_from_toml(
    *,
    toml_path: Path,
) -> _LocalServicePackageRouteSpec:
    from aware_api_ontology.stable_ids import stable_api_package_id
    from aware_service_ontology.stable_ids import stable_service_package_id
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec

    spec = load_aware_service_toml_spec(toml_path=toml_path)
    provided: list[_LocalServiceApiPackageBridge] = []
    required: list[_LocalServiceApiPackageBridge] = []
    dependencies: list[Mapping[str, object]] = []
    for dependency in spec.dependencies:
        package_name = dependency.package_name.strip()
        kind = str(getattr(dependency.kind, "value", dependency.kind))
        dependencies.append(
            {
                "package_name": package_name,
                "kind": kind,
            }
        )
        if kind not in {"api_service_protocol", "api_invocation"}:
            continue
        api_package = _LocalApiPackage(
            id=stable_api_package_id(name=package_name),
            name=package_name,
        )
        bridge = _LocalServiceApiPackageBridge(
            api_package_id=api_package.id,
            api_package=api_package,
            description=f"{kind} dependency declared by {spec.service.package_name}",
        )
        if kind == "api_service_protocol":
            provided.append(bridge)
            continue
        required.append(bridge)
    return _LocalServicePackageRouteSpec(
        service_package=_LocalServicePackage(
            id=stable_service_package_id(name=spec.service.package_name),
            name=spec.service.package_name,
            provided_api_packages=tuple(provided),
            required_api_packages=tuple(required),
            dependencies=tuple(dependencies),
        ),
        service_names=_service_names_for_toml_spec(spec),
    )


def _service_names_for_toml_spec(spec: object) -> tuple[str, ...]:
    service = getattr(spec, "service")
    raw_fqn_prefix = str(getattr(service, "fqn_prefix")).strip()
    service_name = (
        raw_fqn_prefix[: -len("_service")]
        if raw_fqn_prefix.endswith("_service")
        else raw_fqn_prefix
    )
    if not service_name:
        raise RuntimeError("Experience local route setup requires service fqn_prefix.")
    return (service_name,)


def _api_dispatch_route_maps_from_handshake(
    *,
    handshake: ServiceHostHandshakeResponse,
) -> tuple[Mapping[str, tuple[str, ...]], Mapping[str, tuple[str, ...]]]:
    from aware_service_runtime.contracts import (
        SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY,
        SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY,
        SERVICE_HOST_CAPABILITY_API_DISPATCH,
    )

    for capability in handshake.capabilities:
        if capability.capability_id != SERVICE_HOST_CAPABILITY_API_DISPATCH:
            continue
        payload = capability.detail_payload
        if not isinstance(payload, Mapping):
            break
        return (
            _route_map_from_handshake_payload(
                payload.get(SERVICE_HOST_API_DISPATCH_SERVICE_ENDPOINT_REFS_KEY)
            ),
            _route_map_from_handshake_payload(
                payload.get(SERVICE_HOST_API_DISPATCH_SERVICE_STREAM_ENDPOINT_REFS_KEY)
            ),
        )
    raise RuntimeError(
        "Experience local ServiceHost did not advertise API dispatch capability."
    )


def _route_map_from_handshake_payload(
    payload: object,
) -> Mapping[str, tuple[str, ...]]:
    if payload is None:
        return {}
    if not isinstance(payload, Mapping):
        raise RuntimeError("ServiceHost API dispatch route map must be an object.")
    route_map: dict[str, tuple[str, ...]] = {}
    for raw_service_name, raw_endpoint_refs in payload.items():
        if not isinstance(raw_service_name, str):
            continue
        service_name = raw_service_name.strip()
        if (
            not service_name
            or isinstance(raw_endpoint_refs, str)
            or not isinstance(raw_endpoint_refs, Sequence)
        ):
            continue
        endpoint_refs = tuple(
            sorted(
                {
                    endpoint_ref.strip()
                    for endpoint_ref in raw_endpoint_refs
                    if isinstance(endpoint_ref, str) and endpoint_ref.strip()
                }
            )
        )
        if endpoint_refs:
            route_map[service_name] = endpoint_refs
    return route_map


def _filter_route_map(
    route_map: Mapping[str, tuple[str, ...]],
    *,
    service_names: Sequence[str],
    require_non_empty: bool = True,
) -> Mapping[str, tuple[str, ...]]:
    wanted = {service_name for service_name in service_names if service_name}
    filtered = {
        service_name: endpoint_refs
        for service_name, endpoint_refs in route_map.items()
        if service_name in wanted
    }
    if require_non_empty and not filtered:
        raise RuntimeError(
            "Experience local ServiceHost did not advertise endpoint refs for "
            f"service(s): {sorted(wanted)}"
        )
    return filtered


def _resolve_path(*, root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _resolve_repo_root(value: str | Path | None) -> Path:
    if value is not None and str(value).strip():
        return Path(value).expanduser().resolve()
    for env_name in EXPERIENCE_SDK_REPO_ROOT_ENV_VARS:
        raw = _clean_optional_text(os.environ.get(env_name))
        if raw is not None:
            return Path(raw).expanduser().resolve()
    raise RuntimeError(
        "Experience SDK local host repo root is required. Pass repo_root or set "
        f"one of {', '.join(EXPERIENCE_SDK_REPO_ROOT_ENV_VARS)}."
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


__all__ = [
    "DEFAULT_API_CLIENT_ENDPOINT",
    "DEFAULT_ENVIRONMENT_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_ATTENTION_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_DEPENDENCY_PROVIDER_TOML_RELATIVE_PATHS",
    "DEFAULT_EXPERIENCE_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_IDENTITY_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATHS",
    "DEFAULT_REACTIVITY_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_READY_RELATIVE_PATH",
    "DEFAULT_SOCKET_RELATIVE_PATH",
    "DEFAULT_STATE_ROOT_RELATIVE_PATH",
    "EXPERIENCE_API_ENDPOINT_REFS",
    "EXPERIENCE_API_SERVICE_NAME",
    "EXPERIENCE_SDK_REPO_ROOT_ENV_VARS",
    "LOCAL_ENVIRONMENT_API_ENDPOINT",
    "LocalExperienceServiceApiDependencyRouteInstallResult",
    "LocalExperienceServiceHostConfig",
    "build_local_experience_sdk_client",
    "build_local_experience_service_host_api_client",
    "build_local_experience_service_host_app",
    "build_local_experience_service_host_duplex_client_factory",
    "install_local_experience_service_api_dependency_routes",
    "resolve_local_experience_service_api_dependency_routes",
    "resolve_local_experience_service_host_config",
]
