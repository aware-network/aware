from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_service_runtime.host_contract import (
    ServiceHostContractBackendInput,
    ServiceHostContractError,
    ServiceHostContractTargetInput,
    ontology_authority_runtime_manifest_paths,
    ontology_runtime_manifest_db_schema_hash,
    resolve_service_host_contracts_for_tomls,
)
from aware_service_service.ontology.errors import (
    service_activation_requires_materialization as _service_activation_requires_materialization,
)
from aware_service_service.ontology.artifacts import (
    ontology_runtime_artifact_root_from_manifest_path,
    ontology_runtime_artifact_sql_root_from_manifest_path,
)
from aware_service_service_dto.host import (
    ServiceHostContractStatus,
    ServiceHostDbRequirement,
    ServiceHostDbRequirementKind,
)


@dataclass(frozen=True, slots=True)
class ServiceHostOntologyRuntimeArtifactManifestSet:
    kind: str
    source_manifest_path: Path
    artifact_root: Path
    ontology_runtime_manifest_paths: tuple[Path, ...]
    sql_roots: tuple[Path, ...]
    db_schema_hash: str
    db_marker_scope_id: UUID | None = None
    authority_package_names: tuple[str, ...] = ()


def resolve_service_host_ontology_runtime_artifact_manifests(
    *,
    runtime_manifest_path: Path,
    artifact_root: Path | None,
    implementation_toml_paths: tuple[Path, ...],
    contract_target: ServiceHostContractTargetInput,
    contract_backend: ServiceHostContractBackendInput,
    activation_projection_package_names: tuple[str, ...],
) -> ServiceHostOntologyRuntimeArtifactManifestSet:
    manifest_path = runtime_manifest_path.expanduser().resolve()
    if not manifest_path.is_file():
        raise _service_activation_requires_materialization(
            "ServiceHost ontology runtime artifact install requires a hosted "
            f"runtime manifest file: {manifest_path}"
        )
    if not implementation_toml_paths:
        raise _service_activation_requires_materialization(
            "ServiceHost DB runtime/schema preparation requires hosted service "
            "contract TOMLs; a runtime manifest alone is not a DB authority grant."
        )
    try:
        response = resolve_service_host_contracts_for_tomls(
            service_toml_paths=implementation_toml_paths,
            target=contract_target,
            backend=contract_backend,
        )
    except ServiceHostContractError as exc:
        raise _service_activation_requires_materialization(str(exc)) from exc
    if response.status == ServiceHostContractStatus.failed:
        raise _service_activation_requires_materialization(
            "Hosted service contract DB requirement resolution failed: "
            + str(response.error or "unknown error")
        )
    requirements = tuple(
        requirement
        for requirement in (
            response.db_requirement_plan.requirements
            if response.db_requirement_plan is not None
            else ()
        )
        if requirement.manifest_paths or requirement.sql_roots
    )
    resolved_artifact_root = (
        artifact_root.expanduser().resolve()
        if artifact_root is not None
        else ontology_runtime_artifact_root_from_manifest_path(manifest_path)
    )
    activation_projection_requirements = (
        _service_host_activation_projection_db_requirements(
            runtime_manifest_path=manifest_path,
            artifact_root=resolved_artifact_root,
            package_names=activation_projection_package_names,
        )
    )
    return _ontology_runtime_artifact_manifest_set_from_db_requirements(
        source_manifest_path=manifest_path,
        artifact_root=resolved_artifact_root,
        requirements=(*activation_projection_requirements, *requirements),
    )


def _ontology_runtime_artifact_manifest_set_from_db_requirements(
    *,
    source_manifest_path: Path,
    artifact_root: Path,
    requirements: tuple[ServiceHostDbRequirement, ...],
) -> ServiceHostOntologyRuntimeArtifactManifestSet:
    if not requirements:
        return ServiceHostOntologyRuntimeArtifactManifestSet(
            kind="host_contract",
            source_manifest_path=source_manifest_path,
            artifact_root=artifact_root,
            ontology_runtime_manifest_paths=(),
            sql_roots=(),
            db_schema_hash="",
        )
    ontology_runtime_manifest_paths: list[Path] = []
    sql_roots: list[Path] = []
    authority_package_names: list[str] = []
    kind_values: list[str] = []
    schema_hashes: list[str] = []
    for requirement in requirements:
        kind_value = requirement.kind.value
        if kind_value not in kind_values:
            kind_values.append(kind_value)
        if requirement.kind == ServiceHostDbRequirementKind.ontology_authority:
            for package_name in requirement.package_names:
                if package_name not in authority_package_names:
                    authority_package_names.append(package_name)
        requirement_manifest_paths = tuple(
            Path(raw_path).expanduser().resolve()
            for raw_path in requirement.manifest_paths
            if raw_path.strip()
        )
        if not requirement_manifest_paths:
            raise _service_activation_requires_materialization(
                "Hosted service DB requirement declared SQL roots without "
                f"manifest paths: kind={kind_value} provider={requirement.provider_key}"
            )
        requirement_sql_roots = tuple(
            Path(raw_path).expanduser().resolve()
            for raw_path in requirement.sql_roots
            if raw_path.strip()
        )
        if not requirement_sql_roots:
            requirement_sql_roots = tuple(
                ontology_runtime_artifact_sql_root_from_manifest_path(path)
                for path in requirement_manifest_paths
            )
        if len(requirement_sql_roots) != len(requirement_manifest_paths):
            raise _service_activation_requires_materialization(
                "Hosted service DB requirement must declare one SQL root per "
                f"manifest path: kind={kind_value} provider={requirement.provider_key}"
            )
        db_schema_hash = str(requirement.db_schema_hash or "").strip()
        if not db_schema_hash:
            raise _service_activation_requires_materialization(
                "Hosted service DB requirement with manifest paths must declare "
                f"db_schema_hash: kind={kind_value} provider={requirement.provider_key}"
            )
        schema_hashes.append(db_schema_hash)
        if _db_requirement_installs_ontology_runtime_artifact(requirement):
            for path in requirement_manifest_paths:
                if path not in ontology_runtime_manifest_paths:
                    ontology_runtime_manifest_paths.append(path)
        for path in requirement_sql_roots:
            if path not in sql_roots:
                sql_roots.append(path)
    return ServiceHostOntologyRuntimeArtifactManifestSet(
        kind=kind_values[0] if len(kind_values) == 1 else "host_contract",
        source_manifest_path=source_manifest_path,
        artifact_root=artifact_root,
        ontology_runtime_manifest_paths=tuple(ontology_runtime_manifest_paths),
        sql_roots=tuple(sql_roots),
        db_schema_hash=_service_host_contract_db_schema_hash(
            requirements=requirements,
            schema_hashes=tuple(schema_hashes),
        ),
        db_marker_scope_id=_service_host_contract_db_marker_scope_id(
            source_manifest_path=source_manifest_path,
            requirements=requirements,
            schema_hashes=tuple(schema_hashes),
        ),
        authority_package_names=tuple(authority_package_names),
    )


def _service_host_activation_projection_db_requirements(
    *,
    runtime_manifest_path: Path,
    artifact_root: Path,
    package_names: tuple[str, ...],
) -> tuple[ServiceHostDbRequirement, ...]:
    requested = tuple(name.strip() for name in package_names if name.strip())
    if not requested:
        return ()
    try:
        manifest_paths = ontology_authority_runtime_manifest_paths(
            package_names=requested,
            authority_root=artifact_root,
        )
    except ServiceHostContractError as exc:
        raise _service_activation_requires_materialization(str(exc)) from exc

    requirements: list[ServiceHostDbRequirement] = []
    for package_name, manifest_path in zip(requested, manifest_paths, strict=True):
        requirements.append(
            ServiceHostDbRequirement(
                kind=ServiceHostDbRequirementKind.activation_projection,
                provider_key="aware-service-host",
                package_name=package_name,
                package_names=[package_name],
                role="service_activation_projection",
                requirement_mode="required",
                schema_scope="activation_projection",
                manifest_paths=[manifest_path.as_posix()],
                sql_roots=[
                    ontology_runtime_artifact_sql_root_from_manifest_path(
                        manifest_path
                    ).as_posix()
                ],
                db_schema_hash=ontology_runtime_manifest_db_schema_hash(manifest_path),
                authority=False,
                required=True,
                description=(
                    "ServiceHost-owned Service activation projection read model "
                    "for committed ServicePackage/ServiceConfig lanes."
                ),
                metadata={
                    "source": "service_host.activation_projection.semantic_contract",
                    "runtime_manifest_path": runtime_manifest_path.as_posix(),
                },
            )
        )
    return tuple(requirements)


def _db_requirement_installs_ontology_runtime_artifact(
    requirement: ServiceHostDbRequirement,
) -> bool:
    return requirement.kind == ServiceHostDbRequirementKind.activation_projection


def _service_host_contract_db_schema_hash(
    *,
    requirements: tuple[ServiceHostDbRequirement, ...],
    schema_hashes: tuple[str, ...],
) -> str:
    unique_hashes = tuple(dict.fromkeys(schema_hashes))
    if len(unique_hashes) == 1:
        return unique_hashes[0]
    return "sha256:" + _canonical_json_sha256(
        {
            "scope": "service_host_contract_db_requirements",
            "requirements": [
                {
                    "kind": requirement.kind.value,
                    "provider_key": requirement.provider_key,
                    "package_name": requirement.package_name,
                    "package_names": list(requirement.package_names),
                    "manifest_paths": list(requirement.manifest_paths),
                    "sql_roots": list(requirement.sql_roots),
                    "db_schema_hash": requirement.db_schema_hash,
                }
                for requirement in requirements
            ],
        }
    )


def _service_host_contract_db_marker_scope_id(
    *,
    source_manifest_path: Path,
    requirements: tuple[ServiceHostDbRequirement, ...],
    schema_hashes: tuple[str, ...],
) -> UUID:
    payload_hash = _canonical_json_sha256(
        {
            "scope": "service_host_contract_db_marker",
            "source_manifest_path": source_manifest_path.expanduser()
            .resolve()
            .as_posix(),
            "schema_hashes": list(dict.fromkeys(schema_hashes)),
            "requirements": [
                {
                    "kind": requirement.kind.value,
                    "provider_key": requirement.provider_key,
                    "package_name": requirement.package_name,
                    "package_names": list(requirement.package_names),
                    "manifest_paths": list(requirement.manifest_paths),
                    "sql_roots": list(requirement.sql_roots),
                    "db_schema_hash": requirement.db_schema_hash,
                }
                for requirement in requirements
            ],
        }
    )
    return uuid5(NAMESPACE_URL, f"aware-service-host:db-marker:{payload_hash}")


def _canonical_json_sha256(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = [
    "ServiceHostOntologyRuntimeArtifactManifestSet",
    "resolve_service_host_ontology_runtime_artifact_manifests",
]
