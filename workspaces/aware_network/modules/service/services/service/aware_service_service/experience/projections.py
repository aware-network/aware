from __future__ import annotations

from pathlib import Path
from uuid import UUID

from aware_experience.package_projection_ownership import (
    resolve_experience_package_projection_ownership_catalog,
)
from aware_experience_service_api import AwareExperienceServiceApiClient
from aware_experience_service_dto.experience.package_materialization.models import (
    ExperiencePackageProjectionConsumerRef,
    ExperiencePackageProjectionOwnershipCatalog,
    ExperiencePackageProjectionOwnershipEntry,
)
from aware_experience_service_dto.experience.package_materialization.service_operation import (
    ResolveExperiencePackageProjectionOwnershipResponse,
)
from aware_service_runtime.implementation_package import (
    ServiceActivationRequiresMaterialization,
)
from aware_service_runtime.local_service_host_api_client import (
    build_service_api_client_for_api_package,
)
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_service.experience.sdk import build_experience_sdk_client
from aware_service_service_dto.host import (
    ServiceHostProjectionRuntimeRequirement,
    ServiceHostProjectionRuntimeRequirementKind,
)

_EXPERIENCE_SERVICE_API_PACKAGE_NAME = "experience-service-api"


async def resolve_service_host_experience_projection_ownership_catalog(
    *,
    workspace_root: Path,
    experience_toml_path: Path,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    actor_id: UUID,
) -> ExperiencePackageProjectionOwnershipCatalog:
    invoker = build_service_api_client_for_api_package(
        service_api_dependency_routes,
        api_package_name=_EXPERIENCE_SERVICE_API_PACKAGE_NAME,
        actor_id=actor_id,
        invocation_context={
            "source": "service_host.projection_runtime_requirements",
            "workspace_root": workspace_root.expanduser().resolve().as_posix(),
            "experience_toml_path": experience_toml_path.expanduser()
            .resolve()
            .as_posix(),
        },
    )
    if invoker is None:
        try:
            return resolve_experience_package_projection_ownership_catalog(
                workspace_root=workspace_root.expanduser().resolve(),
                experience_toml_path=experience_toml_path.expanduser().resolve(),
            )
        except Exception as exc:
            raise ServiceActivationRequiresMaterialization(
                "ServiceHost local Experience projection requirement discovery "
                "could not resolve the Experience-owned projection catalog from "
                f"{experience_toml_path.expanduser().resolve().as_posix()}: {exc}"
            ) from exc
    sdk = build_experience_sdk_client(AwareExperienceServiceApiClient(invoker))
    try:
        raw_response = await sdk.resolve_package_projection_ownership(
            workspace_root=workspace_root.expanduser().resolve().as_posix(),
            experience_toml_path=experience_toml_path.expanduser().resolve().as_posix(),
            request_context={
                "source": "service_host.projection_runtime_requirements",
            },
            validate_only=True,
        )
    except Exception as exc:
        raise ServiceActivationRequiresMaterialization(
            "Experience projection ownership SDK resolution failed for "
            f"{experience_toml_path.expanduser().resolve().as_posix()}: {exc}"
        ) from exc
    response = ResolveExperiencePackageProjectionOwnershipResponse.model_validate(
        raw_response
    )
    if not response.success:
        raise ServiceActivationRequiresMaterialization(
            "Experience projection ownership SDK resolution failed for "
            f"{experience_toml_path.expanduser().resolve().as_posix()}: "
            f"{response.error or response.info or response.status}"
        )
    return response.catalog


def service_host_projection_runtime_requirements_from_experience_catalog(
    *,
    catalog: ExperiencePackageProjectionOwnershipCatalog,
    experience_toml_path: Path,
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    missing_required_refs = tuple(
        ref.strip() for ref in catalog.missing_required_projection_refs if ref.strip()
    )
    if missing_required_refs:
        raise ServiceActivationRequiresMaterialization(
            "Experience projection ownership catalog is missing required "
            "projection refs: " + ", ".join(repr(ref) for ref in missing_required_refs)
        )
    package_name = str(catalog.package_name or "").strip()
    requirements: list[ServiceHostProjectionRuntimeRequirement] = []
    for entry in catalog.entries:
        projection_name = str(entry.target_projection or "").strip()
        if not projection_name:
            continue
        required = _experience_projection_entry_required(entry)
        consumer_kinds = _dedupe_texts(
            [
                str(consumer.kind or "").strip()
                for consumer in entry.consumers
                if str(consumer.kind or "").strip()
            ]
        )
        requirements.append(
            ServiceHostProjectionRuntimeRequirement(
                kind=(
                    ServiceHostProjectionRuntimeRequirementKind.experience_projection
                ),
                provider_key="aware-experience-service",
                package_name=package_name or None,
                package_names=[package_name] if package_name else [],
                projection_name=projection_name,
                projection_names=[projection_name],
                role=_experience_projection_entry_role(entry),
                requirement_mode="required" if required else "optional",
                required=required,
                description=(
                    "Experience-owned projection target OPG resolved through "
                    "the Experience package projection ownership API."
                ),
                metadata={
                    "experience_toml_path": (
                        catalog.experience_toml_path
                        or experience_toml_path.expanduser().resolve().as_posix()
                    ),
                    "experience_name": entry.experience_name,
                    "source_path": entry.source_path,
                    "node_refs": [node.node_ref for node in entry.nodes],
                    "consumer_kinds": list(consumer_kinds),
                    "consumers": _experience_projection_consumer_payloads(
                        entry.consumers
                    ),
                    "catalog_status": catalog.status,
                    "entry_status": entry.status,
                },
            )
        )
    return tuple(requirements)


async def service_host_local_experience_projection_runtime_requirements(
    *,
    workspace_root: Path,
    experience_toml_path: Path,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
    actor_id: UUID,
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    catalog = await resolve_service_host_experience_projection_ownership_catalog(
        workspace_root=workspace_root,
        experience_toml_path=experience_toml_path,
        service_api_dependency_routes=service_api_dependency_routes,
        actor_id=actor_id,
    )
    return service_host_projection_runtime_requirements_from_experience_catalog(
        catalog=catalog,
        experience_toml_path=experience_toml_path,
    )


def _experience_projection_entry_required(
    entry: ExperiencePackageProjectionOwnershipEntry,
) -> bool:
    consumers = tuple(entry.consumers)
    if not consumers:
        return True
    return any(bool(consumer.required) for consumer in consumers)


def _experience_projection_entry_role(
    entry: ExperiencePackageProjectionOwnershipEntry,
) -> str:
    consumer_kinds = {
        str(consumer.kind or "").strip()
        for consumer in entry.consumers
        if str(consumer.kind or "").strip()
    }
    if "program_port" in consumer_kinds:
        return "experience_program_port_projection_target"
    return "experience_projection_target"


def _experience_projection_consumer_payloads(
    consumers: list[ExperiencePackageProjectionConsumerRef],
) -> list[dict[str, object]]:
    return [
        consumer.model_dump(mode="json", exclude_none=True) for consumer in consumers
    ]


def _dedupe_texts(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        token = str(value or "").strip()
        if token and token not in deduped:
            deduped.append(token)
    return tuple(deduped)


__all__ = [
    "resolve_service_host_experience_projection_ownership_catalog",
    "service_host_local_experience_projection_runtime_requirements",
    "service_host_projection_runtime_requirements_from_experience_catalog",
]
