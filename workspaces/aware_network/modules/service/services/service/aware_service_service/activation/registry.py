from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import UUID

from aware_service_runtime import UnsupportedServiceError
from aware_service_runtime.contracts import ServiceLaneSubscriptionBinding
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_ontology.stable_ids import stable_service_package_id


@dataclass(frozen=True, slots=True)
class ActivatedServiceImplementationPackage:
    source_path: Path | None
    service_package_id: UUID
    binding: Any


@dataclass(frozen=True, slots=True)
class ActivatedImplementationEndpointBinding:
    activated: ActivatedServiceImplementationPackage
    service_name: str


@dataclass(frozen=True, slots=True)
class ActivatedImplementationViewProtocolBinding:
    service_name: str
    operation_name: str
    view_ref: str
    endpoint_refs: tuple[str, ...]
    source_path: str


def service_package_id_for_activated_binding(
    binding: Any,
) -> UUID:
    package_name = service_package_name_for_activated_binding(binding)
    if not package_name:
        raise RuntimeError(
            "ServiceHost activated implementation package is missing "
            "ServicePackage package_name."
        )
    return stable_service_package_id(name=package_name)


def service_package_name_for_activated_binding(
    binding: Any,
) -> str | None:
    package_name = (
        binding.prepared.compile_result.snapshot.spec.service.package_name or ""
    ).strip()
    return package_name or None


def ontology_package_requirements_for_activated_binding(
    binding: Any,
) -> tuple[object, ...]:
    prepared = getattr(binding, "prepared", None)
    compile_result = getattr(prepared, "compile_result", None)
    snapshot = getattr(compile_result, "snapshot", None)
    spec = getattr(snapshot, "spec", None)
    if spec is None:
        return ()
    return tuple(getattr(spec, "ontology_packages", ()) or ())


def ontology_package_requirements_for_activated_package(
    activated: ActivatedServiceImplementationPackage,
) -> tuple[object, ...]:
    requirements = ontology_package_requirements_for_activated_binding(
        activated.binding
    )
    source_path = getattr(activated, "source_path", None)
    if source_path is None:
        return requirements
    spec = load_aware_service_toml_spec(toml_path=source_path.expanduser().resolve())
    source_requirements = tuple(getattr(spec, "ontology_packages", ()) or ())
    return dedupe_ontology_package_requirements((*requirements, *source_requirements))


def dedupe_ontology_package_requirements(
    requirements: tuple[object, ...],
) -> tuple[object, ...]:
    deduped: list[object] = []
    seen: set[tuple[str, str, str, str]] = set()
    for requirement in requirements:
        key = (
            str(getattr(requirement, "package_name", "") or "").strip(),
            str(getattr(requirement, "fqn_prefix", "") or "").strip(),
            enum_or_token_value(getattr(requirement, "role", None)),
            enum_or_token_value(getattr(requirement, "requirement_mode", None)),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(requirement)
    return tuple(deduped)


def service_package_id_for_committed_package_ref(
    *,
    package_ref: Any,
    binding: Any,
) -> UUID:
    if package_ref.service_package_id is not None:
        return package_ref.service_package_id
    raw_package_id = (package_ref.semantic_package_id or "").strip()
    if raw_package_id:
        return UUID(raw_package_id)
    return service_package_id_for_activated_binding(binding)


def activated_implementation_service_names(
    *,
    service_ids_by_name: dict[str, UUID],
) -> tuple[str, ...]:
    return tuple(sorted(service_ids_by_name))


def activated_implementation_endpoint_refs_by_service(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
) -> dict[str, tuple[str, ...]]:
    return endpoint_refs_by_service(
        packages=packages,
        prepared_attr="service_endpoint_refs",
    )


def activated_implementation_stream_endpoint_refs_by_service(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
) -> dict[str, tuple[str, ...]]:
    return endpoint_refs_by_service(
        packages=packages,
        prepared_attr="service_stream_endpoint_refs",
    )


def activated_implementation_view_protocol_bindings(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
) -> tuple[ActivatedImplementationViewProtocolBinding, ...]:
    bindings: list[ActivatedImplementationViewProtocolBinding] = []
    for activated in packages:
        prepared = getattr(activated.binding, "prepared", None)
        compile_result = getattr(prepared, "compile_result", None)
        compile_plan = getattr(compile_result, "compile_plan", None)
        if compile_plan is None:
            continue
        for service_config in getattr(compile_plan, "service_configs", ()) or ():
            service_name = str(getattr(service_config, "name", "") or "").strip()
            if not service_name:
                continue
            for operation in (
                getattr(service_config, "service_operation_configs", ()) or ()
            ):
                operation_name = str(getattr(operation, "name", "") or "").strip()
                if not operation_name:
                    continue
                endpoint_refs = tuple(
                    ref
                    for ref in (
                        str(getattr(endpoint, "endpoint_ref", "") or "").strip()
                        for endpoint in getattr(operation, "api_endpoints", ()) or ()
                    )
                    if ref
                )
                for view in getattr(operation, "api_views", ()) or ():
                    view_ref = str(getattr(view, "view_ref", "") or "").strip()
                    if not view_ref:
                        continue
                    bindings.append(
                        ActivatedImplementationViewProtocolBinding(
                            service_name=service_name,
                            operation_name=operation_name,
                            view_ref=view_ref,
                            endpoint_refs=endpoint_refs,
                            source_path=str(
                                getattr(view, "source_path", "") or ""
                            ).strip(),
                        )
                    )
    return tuple(
        sorted(
            bindings,
            key=lambda item: (
                item.service_name.casefold(),
                item.operation_name.casefold(),
                item.view_ref.casefold(),
            ),
        )
    )


def endpoint_refs_by_service(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    prepared_attr: str,
) -> dict[str, tuple[str, ...]]:
    endpoint_refs: dict[str, set[str]] = {}
    for activated in packages:
        refs_by_service = getattr(activated.binding.prepared, prepared_attr)
        for service_name, refs in refs_by_service.items():
            bucket = endpoint_refs.setdefault(service_name, set())
            bucket.update(
                item.strip() for item in refs if isinstance(item, str) and item.strip()
            )
    return {
        service_name: tuple(sorted(refs))
        for service_name, refs in sorted(
            endpoint_refs.items(),
            key=lambda item: item[0].casefold(),
        )
    }


def activated_implementation_service_package_ids_by_name(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
) -> dict[str, UUID]:
    package_ids_by_name: dict[str, UUID] = {}
    for activated in packages:
        for service_name in activated.binding.service_ids_by_name:
            existing = package_ids_by_name.get(service_name)
            if existing is not None and existing != activated.service_package_id:
                raise RuntimeError(
                    "Multiple Service implementation packages advertise "
                    "different ServicePackage ids for service "
                    f"{service_name!r}."
                )
            package_ids_by_name[service_name] = activated.service_package_id
    return {
        service_name: package_id
        for service_name, package_id in sorted(
            package_ids_by_name.items(),
            key=lambda item: item[0].casefold(),
        )
    }


def activated_implementation_lane_subscriptions(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
) -> tuple[ServiceLaneSubscriptionBinding, ...]:
    subscriptions_by_key: dict[
        tuple[UUID, str, UUID], ServiceLaneSubscriptionBinding
    ] = {}
    for activated in packages:
        for subscriptions in activated.binding.service_subscriptions_by_name.values():
            for subscription in subscriptions:
                key = (
                    subscription.branch_id,
                    (subscription.projection_hash or "").strip(),
                    subscription.service_branch_id,
                )
                subscriptions_by_key[key] = subscription
    return tuple(
        subscriptions_by_key[key]
        for key in sorted(
            subscriptions_by_key,
            key=lambda item: (
                str(item[0]),
                item[1],
                str(item[2]),
            ),
        )
    )


def resolve_activated_implementation_package(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    service_name: str,
) -> ActivatedServiceImplementationPackage:
    for activated_package in packages:
        if service_name in activated_package.binding.service_ids_by_name:
            return activated_package
    raise UnsupportedServiceError(
        "Service host API dispatch could not resolve an activated implementation package for "
        f"service={service_name!r}."
    )


def resolve_activated_implementation_package_by_service_id(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    service_id: UUID,
) -> tuple[ActivatedServiceImplementationPackage, str]:
    match: tuple[ActivatedServiceImplementationPackage, str] | None = None
    for activated_package in packages:
        for (
            service_name,
            candidate_service_id,
        ) in activated_package.binding.service_ids_by_name.items():
            if candidate_service_id != service_id:
                continue
            candidate = (activated_package, service_name)
            if match is not None and match != candidate:
                raise UnsupportedServiceError(
                    "Service host contract access context bootstrap found "
                    "multiple activated implementation-package services for "
                    f"service_id={service_id}."
                )
            match = candidate
    if match is None:
        raise UnsupportedServiceError(
            "Service host contract access context bootstrap could not resolve "
            "an activated implementation-package service for "
            f"service_id={service_id}."
        )
    return match


def resolve_activated_implementation_endpoint(
    *,
    packages: tuple[ActivatedServiceImplementationPackage, ...],
    endpoint_ref: str,
) -> ActivatedImplementationEndpointBinding:
    normalized = endpoint_ref.strip()
    if not normalized:
        raise UnsupportedServiceError("Service host API ingress requires endpoint_ref.")

    match: ActivatedImplementationEndpointBinding | None = None
    for activated_package in packages:
        for (
            service_name,
            endpoint_refs,
        ) in activated_package.binding.prepared.service_endpoint_refs.items():
            if normalized not in endpoint_refs:
                continue
            candidate = ActivatedImplementationEndpointBinding(
                activated=activated_package,
                service_name=service_name,
            )
            if match is not None and match != candidate:
                raise UnsupportedServiceError(
                    "Service host API ingress found multiple activated implementation-package "
                    f"services for endpoint_ref={normalized!r}."
                )
            match = candidate

    if match is None:
        raise UnsupportedServiceError(
            "Service host API ingress could not resolve an activated implementation-package "
            f"service for endpoint_ref={normalized!r}."
        )
    return match


def raise_if_generic_request_targets_implementation_service(
    *,
    service: str,
    service_ids_by_name: dict[str, UUID],
) -> None:
    if service not in service_ids_by_name:
        return
    raise UnsupportedServiceError(
        "Activated Service implementation-package services are not served through the generic "
        f"ServiceOperationRequest host rail: service={service!r}. Route through the API-owned "
        "dispatch rail instead."
    )


def enum_or_token_value(value: object) -> str:
    raw_value = getattr(value, "value", value)
    token = str(raw_value or "").strip().casefold()
    if "." in token:
        token = token.rsplit(".", 1)[-1]
    return token


__all__ = [
    "ActivatedImplementationEndpointBinding",
    "ActivatedServiceImplementationPackage",
    "ActivatedImplementationViewProtocolBinding",
    "activated_implementation_endpoint_refs_by_service",
    "activated_implementation_lane_subscriptions",
    "activated_implementation_service_names",
    "activated_implementation_service_package_ids_by_name",
    "activated_implementation_stream_endpoint_refs_by_service",
    "activated_implementation_view_protocol_bindings",
    "dedupe_ontology_package_requirements",
    "endpoint_refs_by_service",
    "enum_or_token_value",
    "ontology_package_requirements_for_activated_binding",
    "ontology_package_requirements_for_activated_package",
    "raise_if_generic_request_targets_implementation_service",
    "resolve_activated_implementation_endpoint",
    "resolve_activated_implementation_package",
    "resolve_activated_implementation_package_by_service_id",
    "service_package_id_for_activated_binding",
    "service_package_id_for_committed_package_ref",
    "service_package_name_for_activated_binding",
]
