from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

import pytest

from aware_api_ontology.stable_ids import stable_api_package_id
from aware_service_runtime.service_api_dependency_resolution import (
    RemoteServiceApiProviderRuntime,
    ServiceApiDependencyAuthoritySelectorError,
    ServiceApiDependencyDuplicateProviderError,
    ServiceApiDependencyMissingProviderError,
    ServiceApiProviderRuntime,
    resolve_local_service_api_dependency_routes,
    resolve_service_api_dependency_routes,
)
from aware_service_runtime.service_api_dependency_routes import (
    ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY,
    ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
    ServiceApiRouteAuthority,
    ServiceApiRouteAuthoritySelector,
)


@dataclass(frozen=True, slots=True)
class _ApiPackage:
    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class _Bridge:
    api_package_id: UUID
    api_package: _ApiPackage | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class _ServicePackage:
    id: UUID
    name: str
    provided_api_packages: tuple[_Bridge, ...] = ()
    required_api_packages: tuple[_Bridge, ...] = ()
    dependencies: tuple[object, ...] = ()


@dataclass(frozen=True, slots=True)
class _Process:
    returncode: int | None = None


@dataclass(frozen=True, slots=True)
class _Readiness:
    is_ready: bool = True
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class _Handshake:
    host_id: str
    host_version: str | None = "1.0.0"
    protocol_version: str = "1"
    readiness: _Readiness = field(default_factory=_Readiness)


@dataclass(frozen=True, slots=True)
class _Runtime:
    socket_path: Path
    process: _Process
    request_timeout_s: float
    handshake: _Handshake
    routable_service_names: tuple[str, ...]
    endpoint_refs_by_service: dict[str, tuple[str, ...]]
    stream_refs_by_service: dict[str, tuple[str, ...]] = field(default_factory=dict)

    def advertised_endpoint_refs_by_service(self) -> dict[str, tuple[str, ...]]:
        return self.endpoint_refs_by_service

    def advertised_stream_endpoint_refs_by_service(self) -> dict[str, tuple[str, ...]]:
        return self.stream_refs_by_service


@dataclass(frozen=True, slots=True)
class _RemoteRuntime:
    consumer_node_id: UUID
    provider_node_id: UUID
    provider_node_base_url: str
    route_connection_id: UUID | None
    request_timeout_s: float
    host_id: str
    host_version: str | None
    protocol_version: str
    routable_service_names: tuple[str, ...]
    endpoint_refs_by_service: dict[str, tuple[str, ...]]
    stream_refs_by_service: dict[str, tuple[str, ...]]
    authority: ServiceApiRouteAuthority | None

    def advertised_endpoint_refs_by_service(self) -> dict[str, tuple[str, ...]]:
        return self.endpoint_refs_by_service

    def advertised_stream_endpoint_refs_by_service(self) -> dict[str, tuple[str, ...]]:
        return self.stream_refs_by_service


def _api_package(name: str) -> _ApiPackage:
    return _ApiPackage(
        id=stable_api_package_id(name=name),
        name=name,
    )


def _service_package(
    *,
    int_id: int,
    name: str,
    provided_api_packages: tuple[_ApiPackage, ...] = (),
    required_api_packages: tuple[_ApiPackage, ...] = (),
    hydrate_api_package_relationships: bool = True,
    dependencies: tuple[object, ...] = (),
) -> _ServicePackage:
    return _ServicePackage(
        id=UUID(int=int_id),
        name=name,
        provided_api_packages=tuple(
            _Bridge(
                api_package_id=api_package.id,
                api_package=api_package if hydrate_api_package_relationships else None,
            )
            for api_package in provided_api_packages
        ),
        required_api_packages=tuple(
            _Bridge(
                api_package_id=api_package.id,
                api_package=api_package if hydrate_api_package_relationships else None,
            )
            for api_package in required_api_packages
        ),
        dependencies=dependencies,
    )


def _runtime(
    *,
    tmp_path: Path,
    implementation_package_name: str,
    service_name: str,
    endpoint_refs: tuple[str, ...],
    stream_endpoint_refs: tuple[str, ...] = (),
) -> _Runtime:
    return _Runtime(
        socket_path=tmp_path / f"{implementation_package_name}.sock",
        process=_Process(),
        request_timeout_s=5.0,
        handshake=_Handshake(host_id=f"{implementation_package_name}-host"),
        routable_service_names=(service_name,),
        endpoint_refs_by_service={service_name: endpoint_refs},
        stream_refs_by_service=(
            {service_name: stream_endpoint_refs} if stream_endpoint_refs else {}
        ),
    )


def _remote_runtime(
    *,
    provider_node_id: UUID,
    host_id: str,
    authority: ServiceApiRouteAuthority | None,
) -> _RemoteRuntime:
    return _RemoteRuntime(
        consumer_node_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        provider_node_id=provider_node_id,
        provider_node_base_url="ws://kernel-services.example.test/network_node",
        route_connection_id=UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        request_timeout_s=9.0,
        host_id=host_id,
        host_version="1.0.0",
        protocol_version="1",
        routable_service_names=("aware_experience",),
        endpoint_refs_by_service={
            "aware_experience": (
                "experience.activate_experience_section_graph_binding",
            )
        },
        stream_refs_by_service={},
        authority=authority,
    )


def test_resolves_required_api_to_local_service_host_route(tmp_path: Path) -> None:
    meta_api_package = _api_package("meta-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(meta_api_package,),
    )
    meta_package = _service_package(
        int_id=2,
        name="aware-meta-service",
        provided_api_packages=(meta_api_package,),
    )
    runtime = _runtime(
        tmp_path=tmp_path,
        implementation_package_name="aware-meta-service",
        service_name="aware_meta",
        endpoint_refs=("meta.object_instance_graph_identity.history_upsert",),
    )

    routes = resolve_local_service_api_dependency_routes(
        consumer_service_packages=(environment_package,),
        provider_runtimes=(
            ServiceApiProviderRuntime(
                service_package=meta_package,
                runtime=runtime,
            ),
        ),
    )

    assert len(routes) == 1
    route = routes[0]
    assert isinstance(route, ServiceApiDependencyRouteDescriptor)
    assert route.route_kind is ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC
    assert route.consumer_service_package_name == "aware-environment-service"
    assert route.provider_service_package_name == "aware-meta-service"
    assert route.api_package_name == "meta-service-api"
    assert route.socket_path == runtime.socket_path
    assert route.service_names == ("aware_meta",)
    assert route.endpoint_refs_by_service == {
        "aware_meta": ("meta.object_instance_graph_identity.history_upsert",)
    }
    assert ServiceApiDependencyRouteDescriptor.from_payload(route.to_payload()) == route


def test_resolves_api_name_from_dependencies_when_bridge_is_not_hydrated(
    tmp_path: Path,
) -> None:
    meta_api_package = _api_package("meta-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(meta_api_package,),
        hydrate_api_package_relationships=False,
        dependencies=(
            {
                "package_name": "meta-service-api",
                "kind": "api_invocation",
            },
        ),
    )
    meta_package = _service_package(
        int_id=2,
        name="aware-meta-service",
        provided_api_packages=(meta_api_package,),
        hydrate_api_package_relationships=False,
    )
    runtime = _runtime(
        tmp_path=tmp_path,
        implementation_package_name="aware-meta-service",
        service_name="aware_meta",
        endpoint_refs=("meta.graph.invoke_function",),
    )

    routes = resolve_local_service_api_dependency_routes(
        consumer_service_packages=(environment_package,),
        provider_runtimes=(
            ServiceApiProviderRuntime(
                service_package=meta_package,
                runtime=runtime,
            ),
        ),
    )

    assert routes[0].api_package_name == "meta-service-api"
    assert routes[0].to_payload()["api_package_name"] == "meta-service-api"


def test_missing_provider_fails_closed(tmp_path: Path) -> None:
    _ = tmp_path
    meta_api_package = _api_package("meta-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(meta_api_package,),
    )

    with pytest.raises(ServiceApiDependencyMissingProviderError):
        resolve_service_api_dependency_routes(
            consumer_service_packages=(environment_package,),
        )


def test_duplicate_local_providers_fail_without_selector(tmp_path: Path) -> None:
    meta_api_package = _api_package("meta-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(meta_api_package,),
    )
    meta_package = _service_package(
        int_id=2,
        name="aware-meta-service",
        provided_api_packages=(meta_api_package,),
    )
    meta_shadow_package = _service_package(
        int_id=3,
        name="aware-meta-shadow-service",
        provided_api_packages=(meta_api_package,),
    )

    with pytest.raises(ServiceApiDependencyDuplicateProviderError):
        resolve_service_api_dependency_routes(
            consumer_service_packages=(environment_package,),
            provider_runtimes=(
                ServiceApiProviderRuntime(
                    service_package=meta_package,
                    runtime=_runtime(
                        tmp_path=tmp_path,
                        implementation_package_name="aware-meta-service",
                        service_name="aware_meta",
                        endpoint_refs=("meta.graph.invoke_function",),
                    ),
                ),
                ServiceApiProviderRuntime(
                    service_package=meta_shadow_package,
                    runtime=_runtime(
                        tmp_path=tmp_path,
                        implementation_package_name="aware-meta-shadow-service",
                        service_name="aware_meta_shadow",
                        endpoint_refs=("meta.graph.invoke_function",),
                    ),
                ),
            ),
        )


def test_remote_authority_selector_chooses_matching_provider() -> None:
    experience_api_package = _api_package("experience-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(experience_api_package,),
    )
    stable_package = _service_package(
        int_id=2,
        name="aware-experience-stable-service",
        provided_api_packages=(experience_api_package,),
    )
    canary_package = _service_package(
        int_id=3,
        name="aware-experience-canary-service",
        provided_api_packages=(experience_api_package,),
    )
    stable_authority = ServiceApiRouteAuthority(
        provider_set_id="kernel.global_services.v1",
        workspace_deployment_channel="stable",
    )
    canary_authority = ServiceApiRouteAuthority(
        provider_set_id="workspace.experience.canary.v1",
        workspace_deployment_channel="canary",
    )

    routes = resolve_service_api_dependency_routes(
        consumer_service_packages=(environment_package,),
        remote_provider_runtimes=(
            RemoteServiceApiProviderRuntime(
                service_package=stable_package,
                runtime=_remote_runtime(
                    provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                    host_id="aware-experience-stable-host",
                    authority=stable_authority,
                ),
            ),
            RemoteServiceApiProviderRuntime(
                service_package=canary_package,
                runtime=_remote_runtime(
                    provider_node_id=UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                    host_id="aware-experience-canary-host",
                    authority=canary_authority,
                ),
            ),
        ),
        authority_selectors_by_api_package_id={
            experience_api_package.id: ServiceApiRouteAuthoritySelector(
                provider_set_id="workspace.experience.canary.v1",
                workspace_deployment_channel="canary",
            )
        },
    )

    assert len(routes) == 1
    assert (
        routes[0].route_kind is ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT
    )
    assert routes[0].provider_service_package_name == "aware-experience-canary-service"
    assert routes[0].host_id == "aware-experience-canary-host"
    assert routes[0].authority == canary_authority


def test_remote_route_preserves_ontology_authority_catalog_metadata() -> None:
    ontology_api_package = _api_package("ontology-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(ontology_api_package,),
    )
    ontology_package = _service_package(
        int_id=2,
        name="aware-ontology-service",
        provided_api_packages=(ontology_api_package,),
    )
    authority = ServiceApiRouteAuthority(
        provider_set_id="kernel.ontologies.v1",
        workspace_deployment_channel="stable",
        metadata={
            ONTOLOGY_AUTHORITY_CATALOG_METADATA_KEY: {
                "schema": ONTOLOGY_AUTHORITY_CATALOG_SCHEMA,
                "source_kind": "node_ontology_manifest",
                "ontology_package_names": ["content-ontology"],
                "ontology_targets": [{"package_name": "content-ontology"}],
            }
        },
    )

    routes = resolve_service_api_dependency_routes(
        consumer_service_packages=(environment_package,),
        remote_provider_runtimes=(
            RemoteServiceApiProviderRuntime(
                service_package=ontology_package,
                runtime=_remote_runtime(
                    provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                    host_id="aware-content-ontology-host",
                    authority=authority,
                ),
            ),
        ),
    )

    assert len(routes) == 1
    route = routes[0]
    assert route.authority == authority
    assert ServiceApiDependencyRouteDescriptor.from_payload(route.to_payload()) == route


def test_remote_authority_selector_miss_reports_candidate_evidence() -> None:
    experience_api_package = _api_package("experience-service-api")
    environment_package = _service_package(
        int_id=1,
        name="aware-environment-service",
        required_api_packages=(experience_api_package,),
    )
    stable_package = _service_package(
        int_id=2,
        name="aware-experience-service",
        provided_api_packages=(experience_api_package,),
    )

    with pytest.raises(
        ServiceApiDependencyAuthoritySelectorError,
        match="kernel.global_services.v1",
    ):
        resolve_service_api_dependency_routes(
            consumer_service_packages=(environment_package,),
            remote_provider_runtimes=(
                RemoteServiceApiProviderRuntime(
                    service_package=stable_package,
                    runtime=_remote_runtime(
                        provider_node_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                        host_id="aware-experience-stable-host",
                        authority=ServiceApiRouteAuthority(
                            provider_set_id="kernel.global_services.v1",
                            workspace_deployment_channel="stable",
                        ),
                    ),
                ),
            ),
            authority_selectors_by_api_package_id={
                experience_api_package.id: ServiceApiRouteAuthoritySelector(
                    provider_set_id="missing.provider.set",
                )
            },
        )
