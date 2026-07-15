from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from aware_api_ontology.stable_ids import stable_api_package_id
from aware_service_runtime.contracts import ServiceHostBootstrapStatus
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
    ServiceApiDependencyRouteKind,
    ServiceApiRouteAuthority,
    ServiceApiRouteAuthoritySelector,
)


class ServiceApiDependencyResolutionError(RuntimeError):
    """Base error for service API dependency route resolution failures."""


class ServiceApiDependencyMissingProviderError(ServiceApiDependencyResolutionError):
    """Raised when a required API package has no provider in the selected services."""


class ServiceApiDependencyDuplicateProviderError(ServiceApiDependencyResolutionError):
    """Raised when a required API package has multiple selected providers."""


class ServiceApiDependencyAuthoritySelectorError(ServiceApiDependencyResolutionError):
    """Raised when an authority selector cannot resolve one provider."""


class ServiceApiDependencyProviderRuntimeError(ServiceApiDependencyResolutionError):
    """Raised when a provider package has no usable live ServiceHost runtime."""


class ServiceApiPackageBridgeLike(Protocol):
    @property
    def api_package_id(self) -> UUID: ...

    @property
    def api_package(self) -> object | None: ...

    @property
    def description(self) -> str | None: ...


class ServicePackageLike(Protocol):
    @property
    def id(self) -> UUID: ...

    @property
    def name(self) -> str: ...

    @property
    def provided_api_packages(self) -> Sequence[ServiceApiPackageBridgeLike]: ...

    @property
    def required_api_packages(self) -> Sequence[ServiceApiPackageBridgeLike]: ...


class _RuntimeProcessLike(Protocol):
    @property
    def returncode(self) -> int | None: ...


class _RuntimeReadinessLike(Protocol):
    @property
    def is_ready(self) -> bool: ...

    @property
    def reason(self) -> str | None: ...

    @property
    def status(self) -> ServiceHostBootstrapStatus: ...


class _RuntimeHandshakeLike(Protocol):
    @property
    def host_id(self) -> str: ...

    @property
    def host_version(self) -> str | None: ...

    @property
    def protocol_version(self) -> str: ...

    @property
    def readiness(self) -> _RuntimeReadinessLike: ...


class HostedServiceRuntimeLike(Protocol):
    @property
    def socket_path(self) -> Path: ...

    @property
    def process(self) -> _RuntimeProcessLike: ...

    @property
    def request_timeout_s(self) -> float: ...

    @property
    def handshake(self) -> _RuntimeHandshakeLike: ...

    @property
    def routable_service_names(self) -> Sequence[str]: ...

    def advertised_endpoint_refs_by_service(self) -> Mapping[str, Sequence[str]]: ...

    def advertised_stream_endpoint_refs_by_service(
        self,
    ) -> Mapping[str, Sequence[str]]: ...


class RemoteHostedServiceRuntimeLike(Protocol):
    @property
    def consumer_node_id(self) -> UUID: ...

    @property
    def provider_node_id(self) -> UUID: ...

    @property
    def provider_node_base_url(self) -> str: ...

    @property
    def route_connection_id(self) -> UUID | None: ...

    @property
    def request_timeout_s(self) -> float: ...

    @property
    def host_id(self) -> str: ...

    @property
    def host_version(self) -> str | None: ...

    @property
    def protocol_version(self) -> str: ...

    @property
    def routable_service_names(self) -> Sequence[str]: ...

    def advertised_endpoint_refs_by_service(self) -> Mapping[str, Sequence[str]]: ...

    def advertised_stream_endpoint_refs_by_service(
        self,
    ) -> Mapping[str, Sequence[str]]: ...

    @property
    def authority(self) -> ServiceApiRouteAuthority | None: ...


@dataclass(frozen=True, slots=True)
class ServiceApiProviderRuntime:
    service_package: ServicePackageLike
    runtime: HostedServiceRuntimeLike | None


@dataclass(frozen=True, slots=True)
class RemoteServiceApiProviderRuntime:
    service_package: ServicePackageLike
    runtime: RemoteHostedServiceRuntimeLike


@dataclass(frozen=True, slots=True)
class _ProviderCandidate:
    service_package: ServicePackageLike
    bridge: ServiceApiPackageBridgeLike
    runtime: HostedServiceRuntimeLike | None = None
    remote_runtime: RemoteHostedServiceRuntimeLike | None = None


def resolve_service_api_dependency_routes(
    *,
    consumer_service_packages: Sequence[ServicePackageLike],
    provider_runtimes: Sequence[ServiceApiProviderRuntime] = (),
    remote_provider_runtimes: Sequence[RemoteServiceApiProviderRuntime] = (),
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
) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
    """Resolve committed ServicePackage API requirements to provider routes.

    The resolver is package-truth driven: callers supply committed
    ServicePackage provided/required ApiPackage bridges plus already-started
    local or discovered remote ServiceHost runtimes. Lifecycle, deployment, and
    network discovery remain owned by the caller.
    """

    providers_by_api_package_id = _index_provider_candidates_by_api_package_id(
        provider_runtimes=provider_runtimes,
        remote_provider_runtimes=remote_provider_runtimes,
    )
    routes: list[ServiceApiDependencyRouteDescriptor] = []
    for consumer in sorted(
        consumer_service_packages,
        key=lambda package: _service_package_name(package).casefold(),
    ):
        for requirement in sorted(
            consumer.required_api_packages,
            key=lambda bridge: str(bridge.api_package_id),
        ):
            api_package_id = requirement.api_package_id
            api_package_label = _api_package_label(requirement)
            candidates = providers_by_api_package_id.get(api_package_id, ())
            if not candidates:
                raise ServiceApiDependencyMissingProviderError(
                    "No selected ServicePackage provides required ApiPackage "
                    f"{api_package_label} for consumer "
                    f"{_service_package_name(consumer)!r}."
                )
            authority_selector = _authority_selector_for_requirement(
                consumer_service_package_id=consumer.id,
                api_package_id=api_package_id,
                authority_selectors_by_service_api_requirement=(
                    authority_selectors_by_service_api_requirement
                ),
                authority_selectors_by_api_package_id=(
                    authority_selectors_by_api_package_id
                ),
            )
            if authority_selector is not None:
                candidates = _filter_provider_candidates_by_authority(
                    candidates=candidates,
                    selector=authority_selector,
                )
                if not candidates:
                    candidate_evidence = _provider_candidate_authority_evidence(
                        candidates=providers_by_api_package_id.get(api_package_id, ())
                    )
                    raise ServiceApiDependencyAuthoritySelectorError(
                        "No selected ServicePackage provider matched authority "
                        f"selector ({authority_selector.describe()}) for required "
                        f"ApiPackage {api_package_label} and consumer "
                        f"{_service_package_name(consumer)!r}. Candidate "
                        f"authorities: {candidate_evidence}."
                    )
            selected_candidates = _prefer_local_provider_candidates(candidates)
            if len(selected_candidates) > 1:
                provider_names = ", ".join(
                    repr(_service_package_name(candidate.service_package))
                    for candidate in selected_candidates
                )
                selector_detail = (
                    f" after authority selector ({authority_selector.describe()})"
                    if authority_selector is not None
                    else ""
                )
                raise ServiceApiDependencyDuplicateProviderError(
                    "Multiple selected ServicePackages provide required "
                    f"ApiPackage {api_package_label}{selector_detail} for consumer "
                    f"{_service_package_name(consumer)!r}: {provider_names}."
                )
            routes.append(
                _build_route_descriptor(
                    consumer=consumer,
                    requirement=requirement,
                    candidate=next(iter(selected_candidates)),
                    allow_prepared_local_provider=allow_prepared_local_providers,
                )
            )
    return tuple(routes)


def resolve_local_service_api_dependency_routes(
    *,
    consumer_service_packages: Sequence[ServicePackageLike],
    provider_runtimes: Sequence[ServiceApiProviderRuntime],
    allow_prepared_local_providers: bool = False,
) -> tuple[ServiceApiDependencyRouteDescriptor, ...]:
    """Resolve required API packages to local ServiceHost IPC provider routes."""

    return resolve_service_api_dependency_routes(
        consumer_service_packages=consumer_service_packages,
        provider_runtimes=provider_runtimes,
        allow_prepared_local_providers=allow_prepared_local_providers,
    )


def _index_provider_candidates_by_api_package_id(
    *,
    provider_runtimes: Sequence[ServiceApiProviderRuntime],
    remote_provider_runtimes: Sequence[RemoteServiceApiProviderRuntime] = (),
) -> Mapping[UUID, tuple[_ProviderCandidate, ...]]:
    buckets: dict[UUID, list[_ProviderCandidate]] = {}
    for provider_runtime in provider_runtimes:
        provider = provider_runtime.service_package
        for provided in sorted(
            provider.provided_api_packages,
            key=lambda bridge: str(bridge.api_package_id),
        ):
            buckets.setdefault(provided.api_package_id, []).append(
                _ProviderCandidate(
                    service_package=provider,
                    runtime=provider_runtime.runtime,
                    bridge=provided,
                )
            )
    for provider_runtime in remote_provider_runtimes:
        provider = provider_runtime.service_package
        for provided in sorted(
            provider.provided_api_packages,
            key=lambda bridge: str(bridge.api_package_id),
        ):
            buckets.setdefault(provided.api_package_id, []).append(
                _ProviderCandidate(
                    service_package=provider,
                    remote_runtime=provider_runtime.runtime,
                    bridge=provided,
                )
            )
    return {
        api_package_id: tuple(candidates)
        for api_package_id, candidates in sorted(
            buckets.items(),
            key=lambda item: str(item[0]),
        )
    }


def _prefer_local_provider_candidates(
    candidates: tuple[_ProviderCandidate, ...],
) -> tuple[_ProviderCandidate, ...]:
    local_candidates = tuple(
        candidate for candidate in candidates if candidate.remote_runtime is None
    )
    return local_candidates or candidates


def _authority_selector_for_api_package(
    *,
    api_package_id: UUID,
    authority_selectors_by_api_package_id: (
        Mapping[
            UUID,
            ServiceApiRouteAuthoritySelector,
        ]
        | None
    ),
) -> ServiceApiRouteAuthoritySelector | None:
    if authority_selectors_by_api_package_id is None:
        return None
    selector = authority_selectors_by_api_package_id.get(api_package_id)
    if selector is None or selector.is_empty:
        return None
    return selector


def _authority_selector_for_requirement(
    *,
    consumer_service_package_id: UUID,
    api_package_id: UUID,
    authority_selectors_by_service_api_requirement: (
        Mapping[
            tuple[UUID, UUID],
            ServiceApiRouteAuthoritySelector,
        ]
        | None
    ),
    authority_selectors_by_api_package_id: (
        Mapping[
            UUID,
            ServiceApiRouteAuthoritySelector,
        ]
        | None
    ),
) -> ServiceApiRouteAuthoritySelector | None:
    specific_selector: ServiceApiRouteAuthoritySelector | None = None
    if authority_selectors_by_service_api_requirement is not None:
        selector = authority_selectors_by_service_api_requirement.get(
            (consumer_service_package_id, api_package_id)
        )
        if selector is not None and not selector.is_empty:
            specific_selector = selector
    fallback_selector = _authority_selector_for_api_package(
        api_package_id=api_package_id,
        authority_selectors_by_api_package_id=authority_selectors_by_api_package_id,
    )
    if specific_selector is not None and fallback_selector is not None:
        if specific_selector != fallback_selector:
            raise ServiceApiDependencyAuthoritySelectorError(
                "Conflicting Service API authority selectors for consumer "
                f"ServicePackage {consumer_service_package_id} and ApiPackage "
                f"{api_package_id}: source={specific_selector.describe()} "
                f"fallback={fallback_selector.describe()}."
            )
    return specific_selector or fallback_selector


def _filter_provider_candidates_by_authority(
    *,
    candidates: tuple[_ProviderCandidate, ...],
    selector: ServiceApiRouteAuthoritySelector,
) -> tuple[_ProviderCandidate, ...]:
    return tuple(
        candidate
        for candidate in candidates
        if selector.matches(_provider_candidate_authority(candidate))
    )


def _provider_candidate_authority(
    candidate: _ProviderCandidate,
) -> ServiceApiRouteAuthority | None:
    if candidate.remote_runtime is None:
        return None
    return candidate.remote_runtime.authority


def _provider_candidate_authority_evidence(
    *,
    candidates: tuple[_ProviderCandidate, ...],
) -> str:
    if not candidates:
        return "none"
    return "; ".join(
        (
            f"{_service_package_name(candidate.service_package)!r} "
            f"authority={_authority_label(_provider_candidate_authority(candidate))}"
        )
        for candidate in candidates
    )


def _authority_label(authority: ServiceApiRouteAuthority | None) -> str:
    if authority is None or authority.is_empty:
        return "none"
    payload = authority.to_payload()
    return ",".join(
        f"{key}={value!r}"
        for key, value in sorted(payload.items(), key=lambda item: item[0])
        if key != "metadata"
    )


def _build_route_descriptor(
    *,
    consumer: ServicePackageLike,
    requirement: ServiceApiPackageBridgeLike,
    candidate: _ProviderCandidate,
    allow_prepared_local_provider: bool,
) -> ServiceApiDependencyRouteDescriptor:
    if candidate.remote_runtime is not None:
        return _build_remote_route_descriptor(
            consumer=consumer,
            requirement=requirement,
            candidate=candidate,
        )
    return _build_local_route_descriptor(
        consumer=consumer,
        requirement=requirement,
        candidate=candidate,
        allow_prepared_local_provider=allow_prepared_local_provider,
    )


def _build_local_route_descriptor(
    *,
    consumer: ServicePackageLike,
    requirement: ServiceApiPackageBridgeLike,
    candidate: _ProviderCandidate,
    allow_prepared_local_provider: bool,
) -> ServiceApiDependencyRouteDescriptor:
    runtime = _require_live_provider_runtime(
        candidate=candidate,
        allow_prepared=allow_prepared_local_provider,
    )
    service_names = _runtime_service_names(runtime=runtime)
    endpoint_refs_by_service = _normalize_route_map(
        runtime.advertised_endpoint_refs_by_service()
    )
    stream_endpoint_refs_by_service = _normalize_route_map(
        runtime.advertised_stream_endpoint_refs_by_service()
    )
    if not endpoint_refs_by_service and not stream_endpoint_refs_by_service:
        raise ServiceApiDependencyProviderRuntimeError(
            "Selected ServicePackage provider "
            f"{_service_package_name(candidate.service_package)!r} has no "
            "advertised API dispatch endpoint refs."
        )

    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=consumer.id,
        consumer_service_package_name=_service_package_name(consumer),
        provider_service_package_id=candidate.service_package.id,
        provider_service_package_name=_service_package_name(candidate.service_package),
        api_package_id=requirement.api_package_id,
        api_package_name=_api_package_name_for_route(
            service_package=consumer,
            bridge=requirement,
        )
        or _api_package_name_for_route(
            service_package=candidate.service_package,
            bridge=candidate.bridge,
        ),
        route_kind=ServiceApiDependencyRouteKind.LOCAL_SERVICE_HOST_IPC,
        host_id=runtime.handshake.host_id,
        host_version=runtime.handshake.host_version,
        protocol_version=runtime.handshake.protocol_version,
        socket_path=runtime.socket_path,
        request_timeout_s=runtime.request_timeout_s,
        service_names=service_names,
        endpoint_refs_by_service=endpoint_refs_by_service,
        stream_endpoint_refs_by_service=stream_endpoint_refs_by_service,
    )


def _build_remote_route_descriptor(
    *,
    consumer: ServicePackageLike,
    requirement: ServiceApiPackageBridgeLike,
    candidate: _ProviderCandidate,
) -> ServiceApiDependencyRouteDescriptor:
    runtime = candidate.remote_runtime
    if runtime is None:
        raise ServiceApiDependencyProviderRuntimeError(
            "Remote ServicePackage provider candidate is missing remote runtime."
        )
    service_names = _runtime_service_names(runtime=runtime)
    endpoint_refs_by_service = _normalize_route_map(
        runtime.advertised_endpoint_refs_by_service()
    )
    stream_endpoint_refs_by_service = _normalize_route_map(
        runtime.advertised_stream_endpoint_refs_by_service()
    )
    if not endpoint_refs_by_service and not stream_endpoint_refs_by_service:
        raise ServiceApiDependencyProviderRuntimeError(
            "Selected remote ServicePackage provider "
            f"{_service_package_name(candidate.service_package)!r} has no "
            "advertised API dispatch endpoint refs."
        )

    return ServiceApiDependencyRouteDescriptor(
        consumer_service_package_id=consumer.id,
        consumer_service_package_name=_service_package_name(consumer),
        provider_service_package_id=candidate.service_package.id,
        provider_service_package_name=_service_package_name(candidate.service_package),
        api_package_id=requirement.api_package_id,
        api_package_name=_api_package_name_for_route(
            service_package=consumer,
            bridge=requirement,
        )
        or _api_package_name_for_route(
            service_package=candidate.service_package,
            bridge=candidate.bridge,
        ),
        route_kind=ServiceApiDependencyRouteKind.REMOTE_NODE_API_ENDPOINT,
        host_id=runtime.host_id,
        host_version=runtime.host_version,
        protocol_version=runtime.protocol_version,
        socket_path=None,
        request_timeout_s=runtime.request_timeout_s,
        service_names=service_names,
        consumer_node_id=runtime.consumer_node_id,
        provider_node_id=runtime.provider_node_id,
        provider_node_base_url=runtime.provider_node_base_url,
        route_connection_id=runtime.route_connection_id,
        endpoint_refs_by_service=endpoint_refs_by_service,
        stream_endpoint_refs_by_service=stream_endpoint_refs_by_service,
        authority=runtime.authority,
    )


def _require_live_provider_runtime(
    *,
    candidate: _ProviderCandidate,
    allow_prepared: bool = False,
) -> HostedServiceRuntimeLike:
    runtime = candidate.runtime
    provider_name = _service_package_name(candidate.service_package)
    if runtime is None:
        raise ServiceApiDependencyProviderRuntimeError(
            f"Selected ServicePackage provider {provider_name!r} has no live "
            "ServiceHost runtime."
        )
    if runtime.process.returncode is not None:
        raise ServiceApiDependencyProviderRuntimeError(
            f"Selected ServicePackage provider {provider_name!r} is not live "
            f"(returncode={runtime.process.returncode})."
        )
    readiness = runtime.handshake.readiness
    prepared = (
        allow_prepared
        and readiness.status is ServiceHostBootstrapStatus.awaiting_dependency_routes
    )
    if not readiness.is_ready and not prepared:
        reason = readiness.reason
        detail = f" reason={reason!r}" if reason else ""
        raise ServiceApiDependencyProviderRuntimeError(
            f"Selected ServicePackage provider {provider_name!r} is not ready.{detail}"
        )
    return runtime


def _runtime_service_names(
    *,
    runtime: HostedServiceRuntimeLike | RemoteHostedServiceRuntimeLike,
) -> tuple[str, ...]:
    service_names = {
        service_name.strip()
        for service_name in runtime.routable_service_names
        if service_name.strip()
    }
    service_names.update(
        _normalize_route_map(runtime.advertised_endpoint_refs_by_service())
    )
    service_names.update(
        _normalize_route_map(runtime.advertised_stream_endpoint_refs_by_service())
    )
    if not service_names:
        raise ServiceApiDependencyProviderRuntimeError(
            "Selected ServicePackage provider runtime did not advertise routable "
            "service names."
        )
    return tuple(sorted(service_names, key=str.casefold))


def _normalize_route_map(
    value: Mapping[str, Sequence[str]],
) -> Mapping[str, tuple[str, ...]]:
    normalized: dict[str, tuple[str, ...]] = {}
    for raw_service_name, raw_endpoint_refs in value.items():
        service_name = raw_service_name.strip()
        if not service_name:
            continue
        endpoint_refs = tuple(
            sorted(
                {
                    endpoint_ref.strip()
                    for endpoint_ref in raw_endpoint_refs
                    if endpoint_ref.strip()
                },
                key=str.casefold,
            )
        )
        if endpoint_refs:
            normalized[service_name] = endpoint_refs
    return normalized


def _service_package_name(
    service_package: ServicePackageLike,
) -> str:
    name = service_package.name.strip()
    if not name:
        raise ServiceApiDependencyResolutionError(
            "ServicePackage dependency resolution requires package name."
        )
    return name


def _api_package_name(bridge: ServiceApiPackageBridgeLike) -> str | None:
    api_package = bridge.api_package
    if api_package is None:
        return None
    raw_name = getattr(api_package, "name", None)
    if not isinstance(raw_name, str):
        return None
    name = raw_name.strip()
    return name or None


def _api_package_name_for_route(
    *,
    service_package: ServicePackageLike,
    bridge: ServiceApiPackageBridgeLike,
) -> str | None:
    return _api_package_name(bridge) or _api_package_name_from_dependencies(
        service_package=service_package,
        api_package_id=bridge.api_package_id,
    )


def _api_package_name_from_dependencies(
    *,
    service_package: ServicePackageLike,
    api_package_id: UUID,
) -> str | None:
    for dependency in getattr(service_package, "dependencies", ()) or ():
        package_name = _dependency_package_name(dependency)
        if package_name is None:
            continue
        if stable_api_package_id(name=package_name) == api_package_id:
            return package_name
    return None


def _dependency_package_name(dependency: object) -> str | None:
    if isinstance(dependency, Mapping):
        raw_name = dependency.get("package_name")
    else:
        raw_name = getattr(dependency, "package_name", None)
    if not isinstance(raw_name, str):
        return None
    package_name = raw_name.strip()
    return package_name or None


def _api_package_label(bridge: ServiceApiPackageBridgeLike) -> str:
    api_package_name = _api_package_name(bridge)
    if api_package_name is not None:
        return f"{api_package_name!r} ({bridge.api_package_id})"
    return str(bridge.api_package_id)


__all__ = [
    "HostedServiceRuntimeLike",
    "RemoteHostedServiceRuntimeLike",
    "RemoteServiceApiProviderRuntime",
    "ServiceApiDependencyAuthoritySelectorError",
    "ServiceApiDependencyDuplicateProviderError",
    "ServiceApiDependencyMissingProviderError",
    "ServiceApiDependencyProviderRuntimeError",
    "ServiceApiDependencyResolutionError",
    "ServiceApiPackageBridgeLike",
    "ServiceApiProviderRuntime",
    "ServicePackageLike",
    "resolve_local_service_api_dependency_routes",
    "resolve_service_api_dependency_routes",
]
