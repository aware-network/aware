from __future__ import annotations

import os
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_meta_service.local_sdk import (
    read_local_meta_api_activation_read_model,
    read_local_meta_runtime_read_model,
)
from aware_service_runtime.host_contract import (
    ServiceHostContractBackendInput,
    ServiceHostContractError,
    ServiceHostContractTargetInput,
    projection_runtime_requirements_for_semantic_contracts,
    resolve_service_host_contracts_for_tomls,
)
from aware_service_runtime.implementation_package import (
    ServiceActivationRequiresMaterialization,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.service_api_dependency_routes import (
    ServiceApiDependencyRouteDescriptor,
)
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT
from aware_service_service_dto.host import (
    ServiceHostContractStatus,
    ServiceHostProjectionRuntimeRequirement,
    ServiceHostProjectionRuntimeRequirementKind,
)

from aware_service_service.activation.runtime_context import (
    HostedRuntimeManifestContext,
)
from aware_service_service.config import (
    ServiceHostAppConfig,
    ServiceHostOntologyAuthorityConfig,
)
from aware_service_service.experience.projections import (
    service_host_local_experience_projection_runtime_requirements,
)
from aware_service_service.ontology.projections import (
    dedupe_projection_runtime_requirements,
    service_host_required_projection_names as service_host_required_projection_names_from_baseline,
)

SERVICE_HOST_BOOTSTRAP_ACTOR_ID_ENV = "AWARE_SERVICE_HOST_BOOTSTRAP_ACTOR_ID"
SERVICE_HOST_REQUIRED_PROJECTION_NAMES = (
    "Api",
    "ApiCall",
    "Service",
    "ServiceConfig",
    "ServicePackage",
)
_SERVICE_HOST_ACTIVATION_PROJECTION_SEMANTIC_CONTRACTS = (
    AWARE_CODE_SEMANTIC_CONTRACT,
    AWARE_API_SEMANTIC_CONTRACT,
    AWARE_SERVICE_SEMANTIC_CONTRACT,
)


def service_host_bootstrap_actor_id() -> UUID:
    raw_actor_id = (os.environ.get(SERVICE_HOST_BOOTSTRAP_ACTOR_ID_ENV) or "").strip()
    if raw_actor_id:
        try:
            return UUID(raw_actor_id)
        except ValueError as exc:
            raise RuntimeError(
                f"{SERVICE_HOST_BOOTSTRAP_ACTOR_ID_ENV} must be a UUID"
            ) from exc
    return uuid5(NAMESPACE_URL, "aware:actor:system")


def explicit_service_host_root(
    *,
    config: ServiceHostAppConfig,
    purpose: str,
) -> Path:
    if config.kernel_repo_root is not None:
        return config.kernel_repo_root.expanduser().resolve()
    artifact_root = config.artifact_root
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    raw_root = os.environ.get("AWARE_REPO_ROOT")
    if raw_root is not None and raw_root.strip():
        return Path(raw_root).expanduser().resolve()
    raise ServiceActivationRequiresMaterialization(
        f"ServiceHost {purpose} requires explicit root context: configure "
        "kernel_repo_root, artifact.root, or AWARE_REPO_ROOT. Repository-root "
        "discovery fallback is retired."
    )


def service_host_activation_projection_runtime_requirements() -> (
    tuple[ServiceHostProjectionRuntimeRequirement, ...]
):
    return projection_runtime_requirements_for_semantic_contracts(
        provider_key="aware-service-host",
        contracts=_SERVICE_HOST_ACTIVATION_PROJECTION_SEMANTIC_CONTRACTS,
        kind=ServiceHostProjectionRuntimeRequirementKind.activation_projection,
        role="service_activation_projection",
        required=True,
    )


def service_host_ontology_authority_root(
    *,
    config: ServiceHostAppConfig,
) -> Path | None:
    authority_root = config.ontology_authority.root
    if authority_root is not None:
        return authority_root.expanduser().resolve()
    artifact_root = config.artifact_root
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return None


def service_host_api_workspace_root(
    *,
    config: ServiceHostAppConfig,
) -> Path | None:
    artifact_root = config.artifact_root
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    kernel_repo_root = config.kernel_repo_root
    if kernel_repo_root is not None:
        return kernel_repo_root.expanduser().resolve()
    return None


def service_host_contract_target_input(
    *,
    runtime_manifest_path: Path,
    config: ServiceHostAppConfig | None,
    implementation_toml_paths: tuple[Path, ...],
) -> ServiceHostContractTargetInput:
    authority_root = (
        service_host_ontology_authority_root(config=config)
        if config is not None
        else None
    )
    artifact_root = config.artifact_root if config is not None else None
    authority = (
        config.ontology_authority
        if config is not None
        else ServiceHostOntologyAuthorityConfig()
    )
    return ServiceHostContractTargetInput(
        backend=(os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip() or None,
        runtime_manifest_path=runtime_manifest_path,
        artifact_root=artifact_root,
        authority_root=authority_root,
        ontology_authority_source_kind=authority.source_kind,
        ontology_authority_package_names=authority.package_names,
        implementation_toml_paths=implementation_toml_paths,
    )


def service_host_contract_backend_input() -> ServiceHostContractBackendInput:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip() or None
    return ServiceHostContractBackendInput(
        persistence_backend=backend,
        adapter="postgres" if backend == "db" else None,
        database_url_present=bool(str(os.environ.get("DATABASE_URL") or "").strip()),
    )


def service_host_contract_projection_runtime_requirements(
    *,
    runtime_manifest_path: Path,
    config: ServiceHostAppConfig,
    implementation_toml_paths: tuple[Path, ...],
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    if not implementation_toml_paths:
        return ()
    try:
        response = resolve_service_host_contracts_for_tomls(
            service_toml_paths=implementation_toml_paths,
            target=service_host_contract_target_input(
                runtime_manifest_path=runtime_manifest_path,
                config=config,
                implementation_toml_paths=implementation_toml_paths,
            ),
            backend=service_host_contract_backend_input(),
        )
    except ServiceHostContractError as exc:
        raise ServiceActivationRequiresMaterialization(str(exc)) from exc
    if response.status == ServiceHostContractStatus.failed:
        raise ServiceActivationRequiresMaterialization(
            "Hosted service contract projection runtime requirement resolution failed: "
            + str(response.error or "unknown error")
        )
    if response.projection_runtime_requirement_plan is None:
        return ()
    return tuple(response.projection_runtime_requirement_plan.requirements)


async def service_host_local_experience_projection_runtime_requirements_for_config(
    *,
    config: ServiceHostAppConfig,
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    requirements: list[ServiceHostProjectionRuntimeRequirement] = []
    for toml_path in config.reference_packages.experience_toml_paths:
        resolved_toml_path = toml_path.expanduser().resolve()
        workspace_root = explicit_service_host_root(
            config=config,
            purpose="local Experience projection requirement discovery",
        )
        requirements.extend(
            await service_host_local_experience_projection_runtime_requirements(
                workspace_root=workspace_root,
                experience_toml_path=resolved_toml_path,
                service_api_dependency_routes=service_api_dependency_routes,
                actor_id=service_host_bootstrap_actor_id(),
            )
        )
    for package_ref in config.experience_package_refs:
        if package_ref.manifest_path is None:
            continue
        resolved_toml_path = package_ref.manifest_path.expanduser().resolve()
        workspace_root = explicit_service_host_root(
            config=config,
            purpose="committed Experience package-ref requirement discovery",
        )
        requirements.extend(
            await service_host_local_experience_projection_runtime_requirements(
                workspace_root=workspace_root,
                experience_toml_path=resolved_toml_path,
                service_api_dependency_routes=service_api_dependency_routes,
                actor_id=service_host_bootstrap_actor_id(),
            )
        )
    return dedupe_projection_runtime_requirements(tuple(requirements))


async def service_host_projection_runtime_requirements(
    *,
    runtime_manifest_path: Path,
    config: ServiceHostAppConfig,
    implementation_toml_paths: tuple[Path, ...],
    service_api_dependency_routes: tuple[ServiceApiDependencyRouteDescriptor, ...],
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    local_experience_requirements = (
        await service_host_local_experience_projection_runtime_requirements_for_config(
            config=config,
            service_api_dependency_routes=service_api_dependency_routes,
        )
    )
    return dedupe_projection_runtime_requirements(
        (
            *service_host_activation_projection_runtime_requirements(),
            *service_host_contract_projection_runtime_requirements(
                runtime_manifest_path=runtime_manifest_path,
                config=config,
                implementation_toml_paths=implementation_toml_paths,
            ),
            *local_experience_requirements,
        )
    )


def service_host_required_projection_names(
    *,
    projection_runtime_requirements: tuple[
        ServiceHostProjectionRuntimeRequirement, ...
    ],
) -> tuple[str, ...]:
    return service_host_required_projection_names_from_baseline(
        baseline_projection_names=SERVICE_HOST_REQUIRED_PROJECTION_NAMES,
        projection_runtime_requirements=projection_runtime_requirements,
    )


def read_service_host_source_activation_meta_read_model(
    *,
    config: ServiceHostAppConfig,
    runtime: HostedRuntimeManifestContext,
    implementation_toml_paths: tuple[Path, ...] = (),
    required_projection_names: tuple[str, ...] | None = None,
) -> object:
    repo_root = service_host_activation_repo_root(
        config=config,
        runtime_manifest_path=runtime.manifest_path,
    )
    aware_root = (
        config.artifact_root.expanduser().resolve()
        if config.artifact_root is not None
        else repo_root
    )
    return read_local_meta_runtime_read_model(
        repo_root=repo_root,
        aware_root=aware_root,
        required_projection_names=(
            required_projection_names or SERVICE_HOST_REQUIRED_PROJECTION_NAMES
        ),
        required_package_names=(
            required_meta_runtime_package_names_for_implementation_tomls(
                implementation_toml_paths,
                extra_package_names=service_host_activation_projection_package_names(),
            )
        ),
        composite_name="ServiceHost Source Activation Runtime",
    )


def read_service_host_source_activation_meta_api_activation_read_model(
    *,
    config: ServiceHostAppConfig,
    runtime: HostedRuntimeManifestContext,
    implementation_toml_paths: tuple[Path, ...] = (),
    required_projection_names: tuple[str, ...] | None = None,
) -> object:
    repo_root = service_host_activation_repo_root(
        config=config,
        runtime_manifest_path=runtime.manifest_path,
    )
    aware_root = (
        config.artifact_root.expanduser().resolve()
        if config.artifact_root is not None
        else repo_root
    )
    return read_local_meta_api_activation_read_model(
        repo_root=repo_root,
        aware_root=aware_root,
        required_projection_names=(
            required_projection_names or SERVICE_HOST_REQUIRED_PROJECTION_NAMES
        ),
        required_package_names=(
            required_meta_runtime_package_names_for_implementation_tomls(
                implementation_toml_paths,
                extra_package_names=service_host_activation_projection_package_names(),
            )
        ),
        composite_name="ServiceHost Source Activation Runtime",
    )


def service_host_activation_repo_root(
    *,
    config: ServiceHostAppConfig,
    runtime_manifest_path: Path,
) -> Path:
    _ = runtime_manifest_path
    return explicit_service_host_root(
        config=config,
        purpose="source activation read-model loading",
    )


def required_meta_runtime_package_names_for_implementation_tomls(
    toml_paths: tuple[Path, ...],
    *,
    extra_package_names: tuple[str, ...] = (),
) -> tuple[str, ...]:
    package_names: list[str] = []
    seen: set[str] = set()
    for toml_path in toml_paths:
        spec = load_aware_service_toml_spec(toml_path=toml_path.expanduser().resolve())
        for ontology_package in getattr(spec, "ontology_packages", ()) or ():
            package_name = str(
                getattr(ontology_package, "package_name", "") or ""
            ).strip()
            if not package_name or package_name in seen:
                continue
            seen.add(package_name)
            package_names.append(package_name)
    for package_name in extra_package_names:
        cleaned = str(package_name or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        package_names.append(cleaned)
    return tuple(package_names)


def service_host_activation_projection_package_names() -> tuple[str, ...]:
    package_names: list[str] = []
    for contract in _SERVICE_HOST_ACTIVATION_PROJECTION_SEMANTIC_CONTRACTS:
        for descriptor in contract.materialization_runtime_for():
            for package_name in descriptor.runtime_ontology_package_names:
                normalized = str(package_name or "").strip()
                if normalized and normalized not in package_names:
                    package_names.append(normalized)
    if not package_names:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost activation projection requires Code/API/Service semantic "
            "runtime descriptors with runtime ontology package names."
        )
    return tuple(package_names)


__all__ = [
    "SERVICE_HOST_BOOTSTRAP_ACTOR_ID_ENV",
    "SERVICE_HOST_REQUIRED_PROJECTION_NAMES",
    "explicit_service_host_root",
    "read_service_host_source_activation_meta_api_activation_read_model",
    "read_service_host_source_activation_meta_read_model",
    "required_meta_runtime_package_names_for_implementation_tomls",
    "service_host_activation_projection_package_names",
    "service_host_activation_projection_runtime_requirements",
    "service_host_activation_repo_root",
    "service_host_api_workspace_root",
    "service_host_bootstrap_actor_id",
    "service_host_contract_backend_input",
    "service_host_contract_projection_runtime_requirements",
    "service_host_contract_target_input",
    "service_host_local_experience_projection_runtime_requirements_for_config",
    "service_host_ontology_authority_root",
    "service_host_projection_runtime_requirements",
    "service_host_required_projection_names",
]
