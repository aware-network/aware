from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
import importlib
import inspect
import json
import os
from pathlib import Path
from typing import cast
from uuid import uuid4

from aware_orm.db.schema_registry import (
    compute_db_schema_registry_payload_hash,
    load_db_schema_registry,
    resolve_db_schema_registry_sql_roots,
)
from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
from aware_service_runtime.manifest.spec import AwareServiceTomlSpec
from aware_service_service_dto.host import (
    ServiceHostBackendContext,
    ServiceHostCapability,
    ServiceHostContractCapabilityKey,
    ServiceHostContractRequest,
    ServiceHostContractResponse,
    ServiceHostContractStatus,
    ServiceHostDbRequirement,
    ServiceHostDbRequirementKind,
    ServiceHostDbRequirementPlan,
    ServiceHostProjectionRuntimeRequirement,
    ServiceHostProjectionRuntimeRequirementKind,
    ServiceHostProjectionRuntimeRequirementPlan,
    ServiceHostRuntimeRequirementReceipt,
    ServiceHostTargetContext,
)
from aware_code.module_semantic_contract import ModuleSemanticContract


class ServiceHostContractError(RuntimeError):
    """Raised when a hosted service contract cannot be resolved honestly."""


@dataclass(frozen=True, slots=True)
class ServiceHostContractBackendInput:
    persistence_backend: str | None = None
    adapter: str | None = None
    database_url_present: bool | None = None
    backend_key: str = "default"


@dataclass(frozen=True, slots=True)
class ServiceHostContractTargetInput:
    node_kind: str | None = None
    backend: str | None = None
    runtime_manifest_path: Path | None = None
    artifact_root: Path | None = None
    authority_root: Path | None = None
    ontology_authority_source_kind: str | None = None
    ontology_authority_package_names: tuple[str, ...] = ()
    implementation_toml_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class _RuntimeManifestDirectSqlRoot:
    path: Path
    path_token: str


def build_service_host_contract_request(
    *,
    spec: AwareServiceTomlSpec,
    service_toml_path: Path,
    target: ServiceHostContractTargetInput | None = None,
    backend: ServiceHostContractBackendInput | None = None,
) -> ServiceHostContractRequest:
    target_input = target or ServiceHostContractTargetInput()
    backend_input = backend or ServiceHostContractBackendInput()
    database_url_present = backend_input.database_url_present
    if database_url_present is None:
        database_url_present = bool(str(os.environ.get("DATABASE_URL") or "").strip())
    return ServiceHostContractRequest(
        request_id=uuid4(),
        target=ServiceHostTargetContext(
            service_package_name=spec.service.package_name,
            service_fqn_prefix=spec.service.fqn_prefix,
            service_toml_path=service_toml_path.expanduser().resolve().as_posix(),
            service_import_root=_first_service_import_root(spec),
            node_kind=target_input.node_kind,
            backend=target_input.backend,
            runtime_manifest_path=_path_token(target_input.runtime_manifest_path),
            artifact_root=_path_token(target_input.artifact_root),
            authority_root=_path_token(target_input.authority_root),
            ontology_authority_source_kind=(
                target_input.ontology_authority_source_kind
            ),
            ontology_authority_package_names=list(
                target_input.ontology_authority_package_names
            ),
            implementation_toml_paths=[
                path.expanduser().resolve().as_posix()
                for path in target_input.implementation_toml_paths
            ],
        ),
        backend=ServiceHostBackendContext(
            backend_key=backend_input.backend_key,
            persistence_backend=backend_input.persistence_backend,
            adapter=backend_input.adapter,
            database_url_present=database_url_present,
        ),
        capabilities=[
            ServiceHostCapability(
                capability_key=ServiceHostContractCapabilityKey.db_requirements,
                required=True,
                status="requested",
                description="Hosted service DB requirements for Node-owned backend preparation.",
            ),
            ServiceHostCapability(
                capability_key=(
                    ServiceHostContractCapabilityKey.projection_runtime_requirements
                ),
                required=False,
                status="requested",
                description="Hosted service projection runtime requirements for ServiceHost activation.",
            ),
        ],
    )


def resolve_service_host_contract_for_toml(
    *,
    service_toml_path: Path,
    target: ServiceHostContractTargetInput | None = None,
    backend: ServiceHostContractBackendInput | None = None,
) -> ServiceHostContractResponse:
    resolved_toml_path = service_toml_path.expanduser().resolve()
    spec = load_aware_service_toml_spec(toml_path=resolved_toml_path)
    request = build_service_host_contract_request(
        spec=spec,
        service_toml_path=resolved_toml_path,
        target=target,
        backend=backend,
    )
    entrypoint = (spec.host.contract.entrypoint or "").strip()
    if entrypoint:
        return _invoke_contract_entrypoint(entrypoint=entrypoint, request=request)
    return _generic_service_host_contract_response(
        request=request,
        spec=spec,
        service_toml_path=resolved_toml_path,
    )


def resolve_service_host_contracts_for_tomls(
    *,
    service_toml_paths: Sequence[Path],
    target: ServiceHostContractTargetInput | None = None,
    backend: ServiceHostContractBackendInput | None = None,
) -> ServiceHostContractResponse:
    responses = [
        resolve_service_host_contract_for_toml(
            service_toml_path=path,
            target=target,
            backend=backend,
        )
        for path in service_toml_paths
    ]
    requirements: list[ServiceHostDbRequirement] = []
    projection_requirements: list[ServiceHostProjectionRuntimeRequirement] = []
    capabilities: list[ServiceHostCapability] = []
    receipts: list[ServiceHostRuntimeRequirementReceipt] = []
    metadata: dict[str, object] = {"service_toml_count": len(service_toml_paths)}
    errors: list[str] = []
    for response in responses:
        capabilities.extend(response.capabilities)
        receipts.extend(response.receipts)
        if response.db_requirement_plan is not None:
            requirements.extend(response.db_requirement_plan.requirements)
        if response.projection_runtime_requirement_plan is not None:
            projection_requirements.extend(
                response.projection_runtime_requirement_plan.requirements
            )
        if response.status == ServiceHostContractStatus.failed:
            errors.append(response.error or "hosted service contract failed")
    return ServiceHostContractResponse(
        request_id=None,
        status=(
            ServiceHostContractStatus.failed
            if errors
            else ServiceHostContractStatus.succeeded
        ),
        error="; ".join(errors) or None,
        capabilities=capabilities,
        db_requirement_plan=ServiceHostDbRequirementPlan(
            requirements=_dedupe_db_requirements(requirements),
            metadata=metadata,
        ),
        projection_runtime_requirement_plan=(
            ServiceHostProjectionRuntimeRequirementPlan(
                requirements=(
                    _dedupe_projection_runtime_requirements(projection_requirements)
                ),
                metadata=metadata,
            )
        ),
        receipts=receipts,
        metadata=metadata,
    )


def ontology_authority_db_requirement(
    *,
    request: ServiceHostContractRequest,
    package_names: Sequence[str] | None = None,
    authority_root: Path | None = None,
    provider_key: str | None = None,
) -> ServiceHostDbRequirement | None:
    selected_package_names = tuple(
        name.strip()
        for name in (package_names or request.target.ontology_authority_package_names)
        if name.strip()
    )
    if not selected_package_names:
        return None
    root = authority_root
    if root is None and request.target.authority_root:
        root = Path(request.target.authority_root)
    if root is None and request.target.artifact_root:
        root = Path(request.target.artifact_root)
    if root is None:
        raise ServiceHostContractError(
            "Ontology authority DB requirements need authority_root or artifact_root."
        )
    manifest_paths = ontology_authority_runtime_manifest_paths(
        package_names=selected_package_names,
        authority_root=root,
    )
    return ServiceHostDbRequirement(
        kind=ServiceHostDbRequirementKind.ontology_authority,
        provider_key=provider_key or request.target.service_package_name,
        package_names=list(selected_package_names),
        role="authority",
        requirement_mode="required",
        schema_scope="ontology_authority",
        manifest_paths=[path.as_posix() for path in manifest_paths],
        sql_roots=[
            ontology_runtime_artifact_sql_root_from_manifest_path(path).as_posix()
            for path in manifest_paths
        ],
        db_schema_hash=scoped_authority_db_schema_hash(
            package_names=selected_package_names,
            manifest_paths=manifest_paths,
            authority_root=root,
        ),
        authority=True,
        required=True,
        description="Ontology-authority OCG SQL schema owned by the Ontology service.",
    )


def empty_success_contract_response(
    *,
    request: ServiceHostContractRequest,
    provider_key: str | None = None,
    description: str | None = None,
) -> ServiceHostContractResponse:
    requirement_count = 0
    return ServiceHostContractResponse(
        request_id=request.request_id,
        status=ServiceHostContractStatus.succeeded,
        capabilities=[
            ServiceHostCapability(
                capability_key=ServiceHostContractCapabilityKey.db_requirements,
                required=False,
                status="satisfied",
                description=description,
                metadata={
                    "provider_key": provider_key or request.target.service_package_name
                },
            )
        ],
        db_requirement_plan=ServiceHostDbRequirementPlan(requirements=[]),
        projection_runtime_requirement_plan=(
            ServiceHostProjectionRuntimeRequirementPlan(requirements=[])
        ),
        receipts=[
            ServiceHostRuntimeRequirementReceipt(
                capability_key=ServiceHostContractCapabilityKey.db_requirements,
                status=ServiceHostContractStatus.succeeded,
                requirement_count=requirement_count,
                installed_count=0,
                skipped_count=0,
                evidence={
                    "provider_key": provider_key or request.target.service_package_name,
                    "db_requirement_count": requirement_count,
                },
            )
        ],
        metadata={"provider_key": provider_key or request.target.service_package_name},
    )


def projection_runtime_requirements_for_semantic_contracts(
    *,
    provider_key: str,
    contracts: Sequence[ModuleSemanticContract],
    kind: ServiceHostProjectionRuntimeRequirementKind,
    role: str,
    requirement_mode: str = "required",
    required: bool = True,
) -> tuple[ServiceHostProjectionRuntimeRequirement, ...]:
    """Build a ServiceHost projection runtime plan from provider semantic contracts."""

    requirements: list[ServiceHostProjectionRuntimeRequirement] = []
    seen: set[tuple[object, ...]] = set()
    for contract in contracts:
        for descriptor in contract.materialization_runtime_for():
            package_names = _clean_unique(descriptor.runtime_ontology_package_names)
            projection_names = _clean_unique(descriptor.required_projection_names)
            if not projection_names:
                continue
            key = (
                kind.value,
                provider_key,
                descriptor.semantic_owner,
                tuple(package_names),
                tuple(projection_names),
            )
            if key in seen:
                continue
            seen.add(key)
            requirements.append(
                ServiceHostProjectionRuntimeRequirement(
                    kind=kind,
                    provider_key=provider_key,
                    package_names=list(package_names),
                    projection_names=list(projection_names),
                    role=role,
                    requirement_mode=requirement_mode,
                    required=required,
                    description=(
                        "ServiceHost projection runtime requirement declared by "
                        "module semantic materialization runtime descriptors."
                    ),
                    metadata={
                        "semantic_provider_key": contract.provider_key,
                        "semantic_owner": descriptor.semantic_owner,
                        "lane_projection_name": descriptor.lane_projection_name,
                        "environment_handle": descriptor.environment_handle,
                    },
                )
            )
    return tuple(requirements)


def ontology_runtime_artifact_root_from_manifest_path(manifest_path: Path) -> Path:
    aware_dir = next(
        (
            parent
            for parent in manifest_path.expanduser().resolve().parents
            if parent.name in {".aware", "_aware"}
        ),
        None,
    )
    if aware_dir is None:
        return manifest_path.expanduser().resolve().parent
    return aware_dir.parent.resolve()


def ontology_runtime_artifact_sql_root_from_manifest_path(manifest_path: Path) -> Path:
    direct_sql_roots = _runtime_manifest_direct_sql_roots(manifest_path)
    if direct_sql_roots:
        if len(direct_sql_roots) != 1:
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots must resolve exactly "
                f"one postgres SQL root: manifest_path={manifest_path}"
            )
        return direct_sql_roots[0].path
    registry_path = _runtime_manifest_db_schema_registry_path(manifest_path)
    registry = load_db_schema_registry(path=registry_path)
    sql_roots = resolve_db_schema_registry_sql_roots(
        registry_path=registry_path,
        environment_id=registry.environment_id,
        package_kind="ontology",
        backend_target="postgres",
    )
    if len(sql_roots) != 1:
        raise ServiceHostContractError(
            "Ontology runtime db_schema_registry must resolve exactly one "
            f"postgres SQL root: manifest_path={manifest_path}"
        )
    return sql_roots[0].resolve()


def ontology_runtime_manifest_db_schema_hash(manifest_path: Path) -> str:
    direct_sql_roots = _runtime_manifest_direct_sql_roots(manifest_path)
    if direct_sql_roots:
        return _runtime_manifest_direct_sql_roots_schema_hash(direct_sql_roots)
    return compute_db_schema_registry_payload_hash(
        registry=load_db_schema_registry(
            path=_runtime_manifest_db_schema_registry_path(manifest_path)
        )
    )


def _runtime_manifest_direct_sql_roots(
    manifest_path: Path,
) -> tuple[_RuntimeManifestDirectSqlRoot, ...]:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    manifest = _read_json_manifest(resolved_manifest_path)
    db_schema = manifest.get("db_schema")
    if not isinstance(db_schema, Mapping):
        return ()
    raw_sql_roots = db_schema.get("sql_roots")
    if not isinstance(raw_sql_roots, Sequence) or isinstance(
        raw_sql_roots, (bytes, str)
    ):
        return ()
    roots: list[_RuntimeManifestDirectSqlRoot] = []
    for item in raw_sql_roots:
        if isinstance(item, str):
            raw_path = item.strip()
            path_mode = "manifest_relative"
        elif isinstance(item, Mapping):
            raw_path = str(item.get("path") or "").strip()
            path_mode = str(item.get("path_mode") or "manifest_relative").strip()
        else:
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots entries must be "
                f"strings or objects: manifest_path={resolved_manifest_path}"
            )
        if not raw_path:
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots entry is missing "
                f"path: manifest_path={resolved_manifest_path}"
            )
        if path_mode != "manifest_relative":
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots only supports "
                "manifest_relative paths: "
                f"manifest_path={resolved_manifest_path} path_mode={path_mode!r}"
            )
        root_path = Path(raw_path)
        if root_path.is_absolute():
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots must be revision "
                f"relative, not absolute: manifest_path={resolved_manifest_path}"
            )
        resolved_root = (resolved_manifest_path.parent / root_path).resolve()
        if not resolved_root.is_dir():
            raise ServiceHostContractError(
                "Ontology runtime manifest db_schema.sql_roots points to a "
                f"missing SQL root: manifest_path={resolved_manifest_path} "
                f"sql_root={resolved_root}"
            )
        roots.append(
            _RuntimeManifestDirectSqlRoot(
                path=resolved_root,
                path_token=Path(raw_path).as_posix(),
            )
        )
    return tuple(roots)


def _runtime_manifest_direct_sql_roots_schema_hash(
    sql_roots: tuple[_RuntimeManifestDirectSqlRoot, ...],
) -> str:
    roots_payload: list[dict[str, object]] = []
    for sql_root in sql_roots:
        files_payload: list[dict[str, str]] = []
        for child in sorted(
            item for item in sql_root.path.rglob("*") if item.is_file()
        ):
            files_payload.append(
                {
                    "path": child.relative_to(sql_root.path).as_posix(),
                    "sha256": sha256(child.read_bytes()).hexdigest(),
                }
            )
        roots_payload.append(
            {
                "path": sql_root.path_token,
                "files": files_payload,
            }
        )
    return "sha256:" + _canonical_json_sha256(
        {
            "schema": "aware.service.ontology_runtime_direct_sql_roots.v1",
            "sql_roots": roots_payload,
        }
    )


def _runtime_manifest_db_schema_registry_path(manifest_path: Path) -> Path:
    resolved_manifest_path = manifest_path.expanduser().resolve()
    manifest = _read_json_manifest(resolved_manifest_path)
    db_schema_registry = manifest.get("db_schema_registry")
    if not isinstance(db_schema_registry, dict):
        raise ServiceHostContractError(
            "Ontology runtime manifest DB schema resolution requires "
            f"db_schema_registry: {resolved_manifest_path}"
        )
    raw_file = str(db_schema_registry.get("file") or "").strip()
    if not raw_file:
        raise ServiceHostContractError(
            "Ontology runtime manifest db_schema_registry is missing file: "
            + resolved_manifest_path.as_posix()
        )
    registry_path = Path(raw_file).expanduser()
    if not registry_path.is_absolute():
        registry_path = resolved_manifest_path.parent / registry_path
    registry_path = registry_path.resolve()
    if not registry_path.is_file():
        raise ServiceHostContractError(
            "Ontology runtime manifest db_schema_registry file does not exist: "
            + registry_path.as_posix()
        )
    return registry_path


def ontology_authority_runtime_manifest_paths(
    *,
    package_names: Sequence[str],
    authority_root: Path,
) -> tuple[Path, ...]:
    if not package_names:
        return ()
    resolved_root = authority_root.expanduser().resolve()
    revision_catalog = _ontology_revision_runtime_manifest_catalog_by_package_name(
        authority_root=resolved_root,
    )
    catalog = _ontology_manifest_catalog_by_package_name(authority_root=resolved_root)
    selected: list[Path] = []
    missing: list[str] = []
    for package_name in package_names:
        runtime_manifest_path = revision_catalog.get(package_name.casefold())
        if runtime_manifest_path is not None:
            if runtime_manifest_path not in selected:
                selected.append(runtime_manifest_path)
            continue
        ontology_toml_path = catalog.get(package_name.casefold())
        if ontology_toml_path is None:
            missing.append(package_name)
            continue
        runtime_manifest_path = (
            _ontology_runtime_bundle_manifest_path_for_ontology_toml(
                authority_root=resolved_root,
                ontology_toml_path=ontology_toml_path,
            )
        )
        if runtime_manifest_path not in selected:
            selected.append(runtime_manifest_path)
    if missing:
        raise ServiceHostContractError(
            "Ontology authority DB requirement references package names that "
            "do not exist in the local ontology catalog: "
            + ", ".join(repr(name) for name in missing)
        )
    return tuple(selected)


def scoped_authority_db_schema_hash(
    *,
    package_names: Sequence[str],
    manifest_paths: Sequence[Path],
    authority_root: Path | None = None,
) -> str:
    root = authority_root.expanduser().resolve() if authority_root is not None else None

    def _manifest_payload(path: Path) -> dict[str, str]:
        resolved = path.expanduser().resolve()
        path_token = resolved.as_posix()
        if root is not None and _is_relative_to(path=resolved, parent=root):
            path_token = resolved.relative_to(root).as_posix()
        return {
            "path": path_token,
            "sha256": sha256(resolved.read_bytes()).hexdigest(),
        }

    return "sha256:" + _canonical_json_sha256(
        {
            "scope": "ontology_authority",
            "package_names": [name for name in package_names],
            "manifests": [_manifest_payload(path) for path in manifest_paths],
        }
    )


def scoped_local_state_db_schema_hash(
    *,
    manifest_paths: Sequence[Path],
    service_root: Path,
) -> str:
    root = service_root.expanduser().resolve()

    def _manifest_payload(path: Path) -> dict[str, str]:
        resolved = path.expanduser().resolve()
        path_token = resolved.as_posix()
        if _is_relative_to(path=resolved, parent=root):
            path_token = resolved.relative_to(root).as_posix()
        return {
            "path": path_token,
            "sha256": sha256(resolved.read_bytes()).hexdigest(),
        }

    return "sha256:" + _canonical_json_sha256(
        {
            "scope": "local_state",
            "manifests": [_manifest_payload(path) for path in manifest_paths],
        }
    )


def _generic_service_host_contract_response(
    *,
    request: ServiceHostContractRequest,
    spec: AwareServiceTomlSpec,
    service_toml_path: Path,
) -> ServiceHostContractResponse:
    requirements: list[ServiceHostDbRequirement] = []
    for ontology_package in spec.ontology_packages:
        package_name = str(getattr(ontology_package, "package_name", "") or "").strip()
        if not package_name:
            continue
        requirements.append(
            ServiceHostDbRequirement(
                kind=ServiceHostDbRequirementKind.ontology_replica,
                provider_key=spec.service.package_name,
                package_name=package_name,
                package_names=[package_name],
                role=str(getattr(ontology_package, "role", "") or "replica"),
                requirement_mode=str(
                    getattr(ontology_package, "requirement_mode", "") or "required"
                ),
                schema_scope="ontology_replica",
                authority=False,
                required=(
                    str(
                        getattr(ontology_package, "requirement_mode", "") or "required"
                    ).strip()
                    != "optional"
                ),
                description=getattr(ontology_package, "description", None),
                metadata={"service_toml_path": service_toml_path.as_posix()},
            )
        )
    for object_config_graph_package in spec.object_config_graph_packages:
        manifest = str(
            getattr(object_config_graph_package, "manifest", "") or ""
        ).strip()
        if not manifest:
            continue
        resolved_manifest_path = (
            Path(_resolve_manifest_token(service_toml_path, manifest))
            .expanduser()
            .resolve()
        )
        local_state_sql_root = resolved_manifest_path.parent / "sql"
        if not local_state_sql_root.is_dir():
            raise ServiceHostContractError(
                "Hosted service local-state DB requirement requires generated SQL "
                f"beside manifest_path={resolved_manifest_path} "
                f"sql_root={local_state_sql_root}"
            )
        requirements.append(
            ServiceHostDbRequirement(
                kind=ServiceHostDbRequirementKind.local_state,
                provider_key=spec.service.package_name,
                role=str(
                    getattr(object_config_graph_package, "role", "") or "local_state"
                ),
                requirement_mode="required",
                schema_scope="local_state",
                manifest_paths=[resolved_manifest_path.as_posix()],
                sql_roots=[local_state_sql_root.resolve().as_posix()],
                db_schema_hash=scoped_local_state_db_schema_hash(
                    manifest_paths=(resolved_manifest_path,),
                    service_root=service_toml_path.parent,
                ),
                authority=False,
                required=True,
                description=getattr(object_config_graph_package, "description", None),
                metadata={"service_toml_path": service_toml_path.as_posix()},
            )
        )
    return _contract_response_for_requirements(
        request=request,
        provider_key=spec.service.package_name,
        requirements=requirements,
        projection_runtime_requirements=(),
    )


def _direct_activation_projection_requirement(
    *,
    request: ServiceHostContractRequest,
    provider_key: str,
) -> ServiceHostDbRequirement | None:
    runtime_manifest_path = _optional_path(request.target.runtime_manifest_path)
    if runtime_manifest_path is None:
        return None
    if not runtime_manifest_path.is_file():
        return None
    manifest = _read_json_manifest(runtime_manifest_path)
    if "modules" in manifest:
        return None
    if "ocg" not in manifest:
        return None
    return ServiceHostDbRequirement(
        kind=ServiceHostDbRequirementKind.activation_projection,
        provider_key=provider_key,
        role="activation_projection",
        requirement_mode="required",
        schema_scope="activation_projection",
        manifest_paths=[runtime_manifest_path.as_posix()],
        sql_roots=[
            ontology_runtime_artifact_sql_root_from_manifest_path(
                runtime_manifest_path
            ).as_posix()
        ],
        db_schema_hash=ontology_runtime_manifest_db_schema_hash(runtime_manifest_path),
        authority=False,
        required=True,
        description="Single-package activation projection for ServiceHost startup.",
    )


def _contract_response_for_requirements(
    *,
    request: ServiceHostContractRequest,
    provider_key: str,
    requirements: Sequence[ServiceHostDbRequirement],
    projection_runtime_requirements: Sequence[
        ServiceHostProjectionRuntimeRequirement
    ] = (),
) -> ServiceHostContractResponse:
    deduped = _dedupe_db_requirements(requirements)
    projection_deduped = _dedupe_projection_runtime_requirements(
        projection_runtime_requirements
    )
    capabilities = [
        ServiceHostCapability(
            capability_key=ServiceHostContractCapabilityKey.db_requirements,
            required=bool(deduped),
            status="satisfied",
            metadata={"provider_key": provider_key},
        )
    ]
    if projection_deduped:
        capabilities.append(
            ServiceHostCapability(
                capability_key=(
                    ServiceHostContractCapabilityKey.projection_runtime_requirements
                ),
                required=True,
                status="satisfied",
                metadata={"provider_key": provider_key},
            )
        )
    receipts = [
        ServiceHostRuntimeRequirementReceipt(
            capability_key=ServiceHostContractCapabilityKey.db_requirements,
            status=ServiceHostContractStatus.succeeded,
            requirement_count=len(deduped),
            installed_count=0,
            skipped_count=0,
            evidence={
                "provider_key": provider_key,
                "db_requirement_count": len(deduped),
            },
        )
    ]
    if projection_deduped:
        receipts.append(
            ServiceHostRuntimeRequirementReceipt(
                capability_key=(
                    ServiceHostContractCapabilityKey.projection_runtime_requirements
                ),
                status=ServiceHostContractStatus.succeeded,
                requirement_count=len(projection_deduped),
                installed_count=0,
                skipped_count=0,
                evidence={
                    "provider_key": provider_key,
                    "projection_runtime_requirement_count": len(projection_deduped),
                },
            )
        )
    return ServiceHostContractResponse(
        request_id=request.request_id,
        status=ServiceHostContractStatus.succeeded,
        capabilities=capabilities,
        db_requirement_plan=ServiceHostDbRequirementPlan(
            requirements=deduped,
            metadata={"provider_key": provider_key},
        ),
        projection_runtime_requirement_plan=(
            ServiceHostProjectionRuntimeRequirementPlan(
                requirements=projection_deduped,
                metadata={"provider_key": provider_key},
            )
        ),
        receipts=receipts,
        metadata={"provider_key": provider_key},
    )


def _invoke_contract_entrypoint(
    *,
    entrypoint: str,
    request: ServiceHostContractRequest,
) -> ServiceHostContractResponse:
    fn = _load_entrypoint(entrypoint)
    response = fn(request)
    if inspect.isawaitable(response):
        raise ServiceHostContractError(
            "Hosted service contract entrypoints must be synchronous during "
            f"ServiceHost startup: {entrypoint}"
        )
    return _coerce_contract_response(response)


def _load_entrypoint(entrypoint: str) -> Callable[[ServiceHostContractRequest], object]:
    module_name, sep, attr_name = entrypoint.partition(":")
    if not sep or not module_name.strip() or not attr_name.strip():
        raise ServiceHostContractError(
            "Hosted service contract entrypoint must be `module:attribute`: "
            + repr(entrypoint)
        )
    module = importlib.import_module(module_name.strip())
    fn = getattr(module, attr_name.strip())
    if not callable(fn):
        raise ServiceHostContractError(
            f"Hosted service contract entrypoint is not callable: {entrypoint}"
        )
    return cast(Callable[[ServiceHostContractRequest], object], fn)


def _coerce_contract_response(value: object) -> ServiceHostContractResponse:
    if isinstance(value, ServiceHostContractResponse):
        return value
    if isinstance(value, dict):
        return ServiceHostContractResponse.model_validate(value)
    raise ServiceHostContractError(
        "Hosted service contract entrypoint must return ServiceHostContractResponse "
        f"or dict, got {type(value).__name__}."
    )


def _dedupe_db_requirements(
    requirements: Sequence[ServiceHostDbRequirement],
) -> list[ServiceHostDbRequirement]:
    deduped: list[ServiceHostDbRequirement] = []
    seen: set[tuple[object, ...]] = set()
    for requirement in requirements:
        key = (
            requirement.kind.value,
            requirement.provider_key,
            requirement.package_name,
            tuple(requirement.package_names),
            tuple(requirement.manifest_paths),
            tuple(requirement.sql_roots),
            requirement.db_schema_hash,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(requirement)
    return deduped


def _dedupe_projection_runtime_requirements(
    requirements: Sequence[ServiceHostProjectionRuntimeRequirement],
) -> list[ServiceHostProjectionRuntimeRequirement]:
    deduped: list[ServiceHostProjectionRuntimeRequirement] = []
    seen: set[tuple[object, ...]] = set()
    for requirement in requirements:
        key = (
            requirement.kind.value,
            requirement.provider_key,
            requirement.package_name,
            tuple(requirement.package_names),
            requirement.projection_name,
            tuple(requirement.projection_names),
            requirement.role,
            requirement.requirement_mode,
            requirement.required,
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(requirement)
    return deduped


def _clean_unique(values: Sequence[str]) -> tuple[str, ...]:
    cleaned: list[str] = []
    for value in values:
        token = str(value or "").strip()
        if token and token not in cleaned:
            cleaned.append(token)
    return tuple(cleaned)


def _ontology_manifest_catalog_by_package_name(
    *,
    authority_root: Path,
) -> dict[str, Path]:
    from aware_ontology.manifest.loader import load_aware_ontology_toml_spec

    catalog: dict[str, Path] = {}
    for path in _candidate_ontology_manifest_paths(authority_root=authority_root):
        spec = load_aware_ontology_toml_spec(toml_path=path)
        package_name = str(getattr(spec.ontology, "package_name", "") or "").strip()
        if not package_name:
            raise ServiceHostContractError(
                "Ontology authority catalog requires ontology.package_name in "
                + path.as_posix()
            )
        catalog.setdefault(package_name.casefold(), path)
    return catalog


def _ontology_revision_runtime_manifest_catalog_by_package_name(
    *,
    authority_root: Path,
) -> dict[str, Path]:
    runtime_root = (authority_root / ".aware" / "ontology" / "runtime").resolve()
    if not runtime_root.is_dir():
        return {}
    catalog: dict[str, Path] = {}
    for path in sorted(runtime_root.glob("*/ontology.runtime.manifest.json")):
        resolved_path = path.resolve()
        if not _is_relative_to(path=resolved_path, parent=authority_root):
            raise ServiceHostContractError(
                "Ontology authority revision runtime manifest escaped authority "
                f"root: path={resolved_path} root={authority_root}"
            )
        manifest = _read_json_manifest(resolved_path)
        package_name = str(manifest.get("package_name") or "").strip()
        if not package_name:
            raise ServiceHostContractError(
                "Ontology authority revision runtime manifest requires "
                f"package_name: {resolved_path}"
            )
        key = package_name.casefold()
        existing = catalog.get(key)
        if existing is not None and existing != resolved_path:
            raise ServiceHostContractError(
                "Ontology authority revision runtime manifest catalog has "
                f"duplicate package_name={package_name!r}: {existing}, {resolved_path}"
            )
        catalog[key] = resolved_path
    return catalog


def _candidate_ontology_manifest_paths(*, authority_root: Path) -> tuple[Path, ...]:
    patterns = (
        "modules/*/aware.ontology.toml",
        "modules/**/aware.ontology.toml",
        "ontologies/*/aware.ontology.toml",
        "ontologies/**/aware.ontology.toml",
        "workspaces/*/modules/**/aware.ontology.toml",
        "workspaces/*/ontologies/**/aware.ontology.toml",
        "workspaces/*/aware.ontology.toml",
    )
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(authority_root.glob(pattern)):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(resolved)
    return tuple(paths)


def _ontology_runtime_bundle_manifest_path_for_ontology_toml(
    *,
    authority_root: Path,
    ontology_toml_path: Path,
) -> Path:
    from aware_ontology.manifest.loader import load_aware_ontology_toml_spec

    spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
    source_manifest = str(getattr(spec.ontology, "source_manifest", "") or "").strip()
    if not source_manifest:
        raise ServiceHostContractError(
            "Ontology authority catalog requires ontology.source_manifest in "
            + ontology_toml_path.as_posix()
        )
    source_manifest_path = (ontology_toml_path.parent / source_manifest).resolve()
    if not _is_relative_to(path=source_manifest_path, parent=authority_root):
        raise ServiceHostContractError(
            "Ontology authority source_manifest must stay under authority_root: "
            f"path={source_manifest_path} root={authority_root}"
        )
    runtime_manifest_path = (
        source_manifest_path.parent
        / ".aware"
        / "ontology"
        / "runtime"
        / "ontology.runtime.manifest.json"
    ).resolve()
    if not runtime_manifest_path.is_file():
        raise ServiceHostContractError(
            "Ontology authority runtime bundle manifest does not exist: "
            + runtime_manifest_path.as_posix()
        )
    return runtime_manifest_path


def _first_service_import_root(spec: AwareServiceTomlSpec) -> str | None:
    implementation_packages = tuple(spec.implementation.packages or ())
    if not implementation_packages:
        return None
    return str(implementation_packages[0].import_root or "").strip() or None


def _path_token(path: Path | None) -> str | None:
    if path is None:
        return None
    return path.expanduser().resolve().as_posix()


def _optional_path(value: str | None) -> Path | None:
    if not value or not value.strip():
        return None
    return Path(value).expanduser().resolve()


def _resolve_manifest_token(service_toml_path: Path, manifest: str) -> str:
    path = Path(manifest).expanduser()
    if not path.is_absolute():
        path = (service_toml_path.parent / path).resolve()
    else:
        path = path.resolve()
    return path.as_posix()


def _read_json_manifest(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.expanduser().resolve().read_text(encoding="utf-8"))
    except Exception as exc:
        raise ServiceHostContractError(
            "Hosted service contract requires JSON manifest: "
            + path.expanduser().resolve().as_posix()
        ) from exc
    if not isinstance(payload, dict):
        raise ServiceHostContractError(
            "Hosted service contract manifest must contain a JSON object: "
            + path.expanduser().resolve().as_posix()
        )
    return cast(dict[str, object], payload)


def _canonical_json_sha256(payload: object) -> str:
    return sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _is_relative_to(*, path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


__all__ = [
    "ServiceHostContractBackendInput",
    "ServiceHostContractError",
    "ServiceHostContractTargetInput",
    "build_service_host_contract_request",
    "empty_success_contract_response",
    "ontology_runtime_artifact_root_from_manifest_path",
    "ontology_runtime_artifact_sql_root_from_manifest_path",
    "ontology_authority_db_requirement",
    "ontology_authority_runtime_manifest_paths",
    "ontology_runtime_manifest_db_schema_hash",
    "projection_runtime_requirements_for_semantic_contracts",
    "resolve_service_host_contract_for_toml",
    "resolve_service_host_contracts_for_tomls",
    "scoped_authority_db_schema_hash",
]
