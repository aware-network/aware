from __future__ import annotations

from collections.abc import Callable, Sequence
from uuid import UUID

from aware_environment_service.ontology_service_route_selector import (
    OntologyServiceApiRouteSelector,
)
from aware_meta_sdk.client import MetaSdkClient
from aware_environment_service.meta_sdk_route import (
    EnvironmentRoutedGeneratedApiClient,
    MetaSdkEnvironmentRoute,
    MetaSdkOntologyProjectionAuthorityRoute,
    build_environment_routed_meta_sdk_client,
)
from aware_ontology_service_api import AwareOntologyServiceApiClient
from aware_ontology_service_api._bindings import (
    ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_route,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)

ONTOLOGY_SERVICE_API_PACKAGE_NAME = "ontology-service-api"


def select_ontology_service_api_route(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    selector: OntologyServiceApiRouteSelector | None = None,
) -> ServiceApiDependencyRouteDescriptor | None:
    matches: list[ServiceApiDependencyRouteDescriptor] = []
    for route in routes:
        if (
            route.api_package_name or ""
        ).strip().casefold() == ONTOLOGY_SERVICE_API_PACKAGE_NAME:
            matches.append(route)
    if not matches:
        return None
    if selector is not None and not selector.is_empty:
        selected = [route for route in matches if selector.matches(route)]
        if not selected:
            route_labels = ", ".join(_route_label(route) for route in matches)
            raise RuntimeError(
                "Environment host config did not resolve an Ontology service API "
                "route for selector "
                f"({selector.describe()}). Candidate routes: {route_labels}."
            )
        matches = selected
    if len(matches) > 1:
        route_labels = ", ".join(_route_label(route) for route in matches)
        selector_text = (
            f" selector=({selector.describe()})"
            if selector is not None and not selector.is_empty
            else ""
        )
        raise RuntimeError(
            "Environment host config resolved multiple Ontology service API "
            f"routes{selector_text}: {route_labels}. Configure "
            "ontology_service_route to identify one authority route."
        )
    return matches[0]


def build_ontology_service_api_client_factory_from_routes(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    selector: OntologyServiceApiRouteSelector | None = None,
    actor_id: UUID | None = None,
) -> Callable[[], AwareOntologyServiceApiClient] | None:
    route = select_ontology_service_api_route(routes, selector=selector)
    if route is None:
        return None

    client: AwareOntologyServiceApiClient | None = None

    def _factory() -> AwareOntologyServiceApiClient:
        nonlocal client
        if client is None:
            client = AwareOntologyServiceApiClient(
                build_service_api_client_for_route(route, actor_id=actor_id)
            )
        return client

    return _factory


def build_meta_sdk_ontology_projection_route_from_routes(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    selector: OntologyServiceApiRouteSelector | None = None,
    actor_id: UUID | None = None,
) -> MetaSdkOntologyProjectionAuthorityRoute | None:
    route = select_ontology_service_api_route(routes, selector=selector)
    if route is None:
        return None
    if not _route_exposes_endpoint_ref(
        route=route,
        endpoint_ref=ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF,
    ):
        raise RuntimeError(
            "Selected Ontology service API route does not expose "
            f"{ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF!r}: "
            f"{_route_label(route)}."
        )
    authority = route.authority
    service_name = route.service_names[0] if route.service_names else None
    return MetaSdkOntologyProjectionAuthorityRoute(
        api_client=AwareOntologyServiceApiClient(
            build_service_api_client_for_route(route, actor_id=actor_id)
        ),
        authority_ref=_route_label(route),
        provider_service_package_name=route.provider_service_package_name,
        provider_node_id=route.provider_node_id,
        host_id=route.host_id,
        route_connection_id=route.route_connection_id,
        service_name=service_name,
        provider_set_id=authority.provider_set_id if authority is not None else None,
        workspace_revision_id=(
            authority.workspace_revision_id if authority is not None else None
        ),
        workspace_deployment_revision_id=(
            authority.workspace_deployment_revision_id
            if authority is not None
            else None
        ),
        workspace_deployment_channel=(
            authority.workspace_deployment_channel if authority is not None else None
        ),
        workspace_deployment_artifact_key=(
            authority.workspace_deployment_artifact_key
            if authority is not None
            else None
        ),
    )


def build_meta_sdk_environment_route_from_routes(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    environment_api_client: EnvironmentRoutedGeneratedApiClient,
    environment_id: UUID,
    selector: OntologyServiceApiRouteSelector | None = None,
    actor_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    branch_id: UUID | None = None,
    projection_hash: str | None = None,
) -> MetaSdkEnvironmentRoute:
    ontology_projection_route = build_meta_sdk_ontology_projection_route_from_routes(
        routes,
        selector=selector,
        actor_id=actor_id,
    )
    if ontology_projection_route is None:
        raise RuntimeError(
            "Environment-routed Meta SDK route construction requires an "
            "Ontology service API dependency route that exposes "
            f"{ONTOLOGY__GRAPH__RESOLVE_PROJECTION_ENDPOINT_REF!r}."
        )
    return MetaSdkEnvironmentRoute(
        api_client=environment_api_client,
        environment_id=environment_id,
        actor_id=actor_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
        ontology_projection_route=ontology_projection_route,
    )


def build_environment_routed_meta_sdk_client_from_routes(
    routes: Sequence[ServiceApiDependencyRouteDescriptor],
    *,
    environment_api_client: EnvironmentRoutedGeneratedApiClient,
    environment_id: UUID,
    selector: OntologyServiceApiRouteSelector | None = None,
    actor_id: UUID | None = None,
    process_id: UUID | None = None,
    thread_id: UUID | None = None,
    branch_id: UUID | None = None,
    projection_hash: str | None = None,
) -> MetaSdkClient:
    route = build_meta_sdk_environment_route_from_routes(
        routes,
        environment_api_client=environment_api_client,
        environment_id=environment_id,
        selector=selector,
        actor_id=actor_id,
        process_id=process_id,
        thread_id=thread_id,
        branch_id=branch_id,
        projection_hash=projection_hash,
    )
    return build_environment_routed_meta_sdk_client(route=route)


def _route_exposes_endpoint_ref(
    *,
    route: ServiceApiDependencyRouteDescriptor,
    endpoint_ref: str,
) -> bool:
    expected = endpoint_ref.strip()
    for endpoint_refs in route.endpoint_refs_by_service.values():
        for candidate in endpoint_refs:
            if candidate.strip() == expected:
                return True
    return False


def _route_label(route: ServiceApiDependencyRouteDescriptor) -> str:
    parts = [
        f"provider={route.provider_service_package_name}",
        f"host={route.host_id}",
    ]
    if route.provider_node_id is not None:
        parts.append(f"provider_node={route.provider_node_id}")
    if route.route_connection_id is not None:
        parts.append(f"route_connection={route.route_connection_id}")
    if route.service_names:
        parts.append("services=" + ",".join(route.service_names))
    return " ".join(parts)


__all__ = [
    "ONTOLOGY_SERVICE_API_PACKAGE_NAME",
    "OntologyServiceApiRouteSelector",
    "build_environment_routed_meta_sdk_client_from_routes",
    "build_meta_sdk_environment_route_from_routes",
    "build_meta_sdk_ontology_projection_route_from_routes",
    "build_ontology_service_api_client_factory_from_routes",
    "select_ontology_service_api_route",
]
