from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)


class ServiceViewProviderRouteResolutionError(RuntimeError):
    """Raised when a service view-provider route cannot resolve canonically."""


class ServiceViewProtocolBindingLike(Protocol):
    service_name: str
    operation_name: str
    view_ref: str
    endpoint_refs: tuple[str, ...]
    source_path: str


@dataclass(frozen=True, slots=True)
class ServiceViewProviderRouteDescriptor:
    """Runtime route for a service-owned Experience view-state provider."""

    view_ref: str
    service_name: str
    operation_name: str
    api_package_name: str
    source_path: str
    api_route: ServiceApiDependencyRouteDescriptor | None
    endpoint_ref: str | None = None
    stream_endpoint_ref: str | None = None
    provider_ref: str | None = None

    def provider_context(self) -> dict[str, object]:
        context: dict[str, object] = {
            "api_package_name": self.api_package_name,
            "service_name": self.service_name,
            "operation_name": self.operation_name,
            "view_ref": self.view_ref,
            "api_view_ref": self.view_ref,
            "source_path": self.source_path,
        }
        if self.endpoint_ref is not None:
            context["endpoint_ref"] = self.endpoint_ref
        if self.api_route is not None:
            context.update(
                {
                    "route_kind": self.api_route.route_kind.value,
                    "host_id": self.api_route.host_id,
                    "provider_service_package_name": (
                        self.api_route.provider_service_package_name
                    ),
                    "provider_service_package_id": str(
                        self.api_route.provider_service_package_id
                    ),
                }
            )
        if self.provider_ref is not None:
            context["provider_ref"] = self.provider_ref
        if self.stream_endpoint_ref is not None:
            context["stream_endpoint_ref"] = self.stream_endpoint_ref
        if (
            self.api_route is not None
            and self.api_route.authority is not None
            and not self.api_route.authority.is_empty
        ):
            context["authority"] = self.api_route.authority.to_payload()
        return context


def build_service_view_provider_routes(
    *,
    bindings: Sequence[ServiceViewProtocolBindingLike],
    api_dependency_routes: Sequence[ServiceApiDependencyRouteDescriptor],
    require_all: bool = True,
) -> tuple[ServiceViewProviderRouteDescriptor, ...]:
    routes: list[ServiceViewProviderRouteDescriptor] = []
    for binding in bindings:
        endpoint_ref = _optional_single_endpoint_ref(binding=binding)
        route = _resolve_api_route_for_binding(
            binding=binding,
            endpoint_ref=endpoint_ref,
            api_dependency_routes=api_dependency_routes,
            required=require_all,
        )
        if route is None:
            continue
        api_package_name = (route.api_package_name or "").strip()
        if not api_package_name:
            raise ServiceViewProviderRouteResolutionError(
                "Service view-provider route requires api_package_name on the "
                "matched Service API dependency route: "
                + f"view_ref={binding.view_ref!r} service_name={binding.service_name!r}"
            )
        routes.append(
            ServiceViewProviderRouteDescriptor(
                view_ref=binding.view_ref,
                service_name=binding.service_name,
                operation_name=binding.operation_name,
                api_package_name=api_package_name,
                endpoint_ref=endpoint_ref,
                stream_endpoint_ref=_matching_stream_endpoint_ref(
                    route.stream_endpoint_refs_by_service,
                    service_name=binding.service_name,
                    endpoint_refs=binding.endpoint_refs,
                ),
                source_path=binding.source_path,
                api_route=route,
            )
        )
    return tuple(
        sorted(
            routes,
            key=lambda item: (
                item.view_ref.casefold(),
                item.service_name.casefold(),
                item.operation_name.casefold(),
            ),
        )
    )


def require_service_view_provider_route(
    *,
    routes: Sequence[ServiceViewProviderRouteDescriptor],
    view_ref: str,
    service_name: str | None = None,
) -> ServiceViewProviderRouteDescriptor:
    route = resolve_service_view_provider_route(
        routes=routes,
        view_ref=view_ref,
        service_name=service_name,
    )
    if route is None:
        raise ServiceViewProviderRouteResolutionError(
            "Service view-provider route is unavailable: "
            + f"view_ref={view_ref!r} service_name={service_name!r}"
        )
    return route


def resolve_service_view_provider_route(
    *,
    routes: Sequence[ServiceViewProviderRouteDescriptor],
    view_ref: str,
    service_name: str | None = None,
) -> ServiceViewProviderRouteDescriptor | None:
    normalized_view_ref = _normalize_required(view_ref, "view_ref")
    normalized_service_name = _normalize_optional(service_name)
    matches = tuple(
        route
        for route in routes
        if _normalize_required(route.view_ref, "route.view_ref") == normalized_view_ref
        and (
            normalized_service_name is None
            or _normalize_required(route.service_name, "route.service_name")
            == normalized_service_name
        )
    )
    if not matches:
        return None
    if len(matches) != 1:
        service_names = ", ".join(repr(route.service_name) for route in matches)
        raise ServiceViewProviderRouteResolutionError(
            "Service view-provider route requires exactly one match: "
            + f"view_ref={view_ref!r} service_name={service_name!r} "
            + f"matches={service_names}"
        )
    return matches[0]


def _resolve_api_route_for_binding(
    *,
    binding: ServiceViewProtocolBindingLike,
    endpoint_ref: str | None,
    api_dependency_routes: Sequence[ServiceApiDependencyRouteDescriptor],
    required: bool,
) -> ServiceApiDependencyRouteDescriptor | None:
    matches: list[ServiceApiDependencyRouteDescriptor] = []
    for route in api_dependency_routes:
        if binding.service_name not in route.service_names:
            continue
        if endpoint_ref is None:
            matches.append(route)
            continue
        endpoint_refs = route.endpoint_refs_by_service.get(binding.service_name, ())
        if endpoint_ref not in endpoint_refs:
            continue
        matches.append(route)
    if len(matches) != 1:
        if not required and not matches:
            return None
        raise ServiceViewProviderRouteResolutionError(
            "Service view-provider route requires exactly one API dependency "
            "route for binding: "
            + f"view_ref={binding.view_ref!r} "
            + f"service_name={binding.service_name!r} "
            + f"endpoint_ref={endpoint_ref!r} match_count={len(matches)}"
        )
    return matches[0]


def _optional_single_endpoint_ref(
    *, binding: ServiceViewProtocolBindingLike
) -> str | None:
    endpoint_refs = tuple(ref.strip() for ref in binding.endpoint_refs if ref.strip())
    if len(endpoint_refs) != 1:
        if not endpoint_refs:
            return None
        raise ServiceViewProviderRouteResolutionError(
            "Service view-provider route accepts at most one endpoint hint per "
            "service-operation view binding: "
            + f"view_ref={binding.view_ref!r} "
            + f"service_name={binding.service_name!r} "
            + f"endpoint_count={len(endpoint_refs)}"
        )
    return endpoint_refs[0]


def _matching_stream_endpoint_ref(
    stream_refs_by_service: Mapping[str, Sequence[str]],
    *,
    service_name: str,
    endpoint_refs: Sequence[str],
) -> str | None:
    stream_refs = tuple(
        ref.strip()
        for ref in stream_refs_by_service.get(service_name, ())
        if ref.strip()
    )
    if not stream_refs:
        return None
    endpoint_set = {ref.strip() for ref in endpoint_refs if ref.strip()}
    matches = tuple(ref for ref in stream_refs if ref in endpoint_set)
    if not matches:
        return None
    if len(matches) != 1:
        raise ServiceViewProviderRouteResolutionError(
            "Service view-provider route found multiple stream endpoint refs "
            + f"for service_name={service_name!r} matches={matches!r}"
        )
    return matches[0]


def _normalize_required(value: str, label: str) -> str:
    normalized = value.strip().casefold()
    if not normalized:
        raise ServiceViewProviderRouteResolutionError(f"{label} is required.")
    return normalized


def _normalize_optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().casefold()
    return normalized or None


__all__ = [
    "ServiceViewProtocolBindingLike",
    "ServiceViewProviderRouteDescriptor",
    "ServiceViewProviderRouteResolutionError",
    "build_service_view_provider_routes",
    "require_service_view_provider_route",
    "resolve_service_view_provider_route",
]
