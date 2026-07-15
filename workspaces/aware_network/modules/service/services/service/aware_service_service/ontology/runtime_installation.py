from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from aware_api_runtime.semantic_contract import AWARE_API_SEMANTIC_CONTRACT
from aware_code.semantic_contract import AWARE_CODE_SEMANTIC_CONTRACT
from aware_orm.db.boot import DBBootConnection, ensure_db_schema_installed_multi
from aware_service_runtime.host_contract import (
    ServiceHostContractBackendInput,
    ServiceHostContractTargetInput,
)
from aware_service_runtime.implementation_package import (
    ServiceActivationRequiresMaterialization,
)
from aware_service_runtime.semantic_contract import AWARE_SERVICE_SEMANTIC_CONTRACT

from aware_service_service.activation.runtime_context import (
    HostedRuntimeManifestContext,
)
from aware_service_service.config import (
    ServiceHostAppConfig,
    ServiceHostOntologyAuthorityConfig,
)
from aware_service_service.ontology.artifacts import (
    install_ontology_runtime_artifact_manifest,
)
from aware_service_service.ontology.db_requirements import (
    resolve_service_host_ontology_runtime_artifact_manifests,
)

_SERVICE_HOST_ACTIVATION_PROJECTION_SEMANTIC_CONTRACTS = (
    AWARE_CODE_SEMANTIC_CONTRACT,
    AWARE_API_SEMANTIC_CONTRACT,
    AWARE_SERVICE_SEMANTIC_CONTRACT,
)


@dataclass(frozen=True, slots=True)
class ServiceHostOntologyRuntimeArtifactInstallEvidence:
    status: str
    source_manifest_path: str | None = None
    manifest_kind: str | None = None
    ontology_runtime_manifest_count: int = 0
    projection_plan_count: int = 0
    authority_package_names: tuple[str, ...] = ()
    reason: str | None = None

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "ontology_runtime_manifest_count": self.ontology_runtime_manifest_count,
            "projection_plan_count": self.projection_plan_count,
        }
        if self.source_manifest_path is not None:
            payload["source_manifest_path"] = self.source_manifest_path
        if self.manifest_kind is not None:
            payload["manifest_kind"] = self.manifest_kind
        if self.authority_package_names:
            payload["authority_package_names"] = list(self.authority_package_names)
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


@dataclass(frozen=True, slots=True)
class ServiceHostDBSchemaInstallEvidence:
    status: str
    source_manifest_path: str | None = None
    manifest_kind: str | None = None
    db_marker_scope_id: str | None = None
    sql_root_count: int = 0
    schema_count: int = 0
    step_count: int = 0
    db_schema_hash: str | None = None
    authority_package_names: tuple[str, ...] = ()
    reason: str | None = None

    def as_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "sql_root_count": self.sql_root_count,
            "schema_count": self.schema_count,
            "step_count": self.step_count,
        }
        if self.source_manifest_path is not None:
            payload["source_manifest_path"] = self.source_manifest_path
        if self.manifest_kind is not None:
            payload["manifest_kind"] = self.manifest_kind
        if self.db_marker_scope_id is not None:
            payload["db_marker_scope_id"] = self.db_marker_scope_id
        if self.db_schema_hash is not None:
            payload["db_schema_hash"] = self.db_schema_hash
        if self.authority_package_names:
            payload["authority_package_names"] = list(self.authority_package_names)
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


class _ClosableDBBootConnection(DBBootConnection, Protocol):
    async def close(self) -> object: ...


def install_service_host_ontology_runtime_artifacts(
    *,
    runtime: HostedRuntimeManifestContext,
    config: ServiceHostAppConfig | None = None,
    implementation_toml_paths: tuple[Path, ...] = (),
) -> dict[str, object]:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return ServiceHostOntologyRuntimeArtifactInstallEvidence(
            status="skipped",
            reason=f"backend:{backend or 'default'}",
        ).as_payload()
    effective_toml_paths = implementation_toml_paths
    if not effective_toml_paths and config is not None:
        effective_toml_paths = config.implementation_packages.toml_paths
    manifest_path = runtime.manifest_path.expanduser().resolve()
    manifest_set = resolve_service_host_ontology_runtime_artifact_manifests(
        runtime_manifest_path=manifest_path,
        artifact_root=config.artifact_root if config is not None else None,
        implementation_toml_paths=effective_toml_paths,
        contract_target=_service_host_contract_target_input(
            runtime_manifest_path=manifest_path,
            config=config,
            implementation_toml_paths=effective_toml_paths,
        ),
        contract_backend=_service_host_contract_backend_input(),
        activation_projection_package_names=(
            _service_host_activation_projection_package_names()
        ),
    )
    if not manifest_set.ontology_runtime_manifest_paths:
        return ServiceHostOntologyRuntimeArtifactInstallEvidence(
            status="skipped",
            source_manifest_path=manifest_set.source_manifest_path.as_posix(),
            manifest_kind=manifest_set.kind,
            reason="no_ontology_runtime_artifact_requirements",
        ).as_payload()
    projection_plan_count = 0
    for ontology_runtime_manifest_path in manifest_set.ontology_runtime_manifest_paths:
        projection_plan_count += install_ontology_runtime_artifact_manifest(
            manifest_path=ontology_runtime_manifest_path,
        )
    return ServiceHostOntologyRuntimeArtifactInstallEvidence(
        status="installed",
        source_manifest_path=manifest_set.source_manifest_path.as_posix(),
        manifest_kind=manifest_set.kind,
        ontology_runtime_manifest_count=len(
            manifest_set.ontology_runtime_manifest_paths
        ),
        projection_plan_count=projection_plan_count,
        authority_package_names=manifest_set.authority_package_names,
    ).as_payload()


async def ensure_service_host_db_schema_installed(
    *,
    runtime: HostedRuntimeManifestContext,
    config: ServiceHostAppConfig | None = None,
    implementation_toml_paths: tuple[Path, ...] = (),
) -> dict[str, object]:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip().lower()
    if backend != "db":
        return ServiceHostDBSchemaInstallEvidence(
            status="skipped",
            reason=f"backend:{backend or 'default'}",
        ).as_payload()
    database_url = (os.environ.get("DATABASE_URL") or "").strip()
    if not database_url:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost DB schema readiness requires DATABASE_URL when "
            "AWARE_PERSISTENCE_BACKEND=db."
        )
    effective_toml_paths = implementation_toml_paths
    if not effective_toml_paths and config is not None:
        effective_toml_paths = config.implementation_packages.toml_paths
    manifest_path = runtime.manifest_path.expanduser().resolve()
    manifest_set = resolve_service_host_ontology_runtime_artifact_manifests(
        runtime_manifest_path=manifest_path,
        artifact_root=config.artifact_root if config is not None else None,
        implementation_toml_paths=effective_toml_paths,
        contract_target=_service_host_contract_target_input(
            runtime_manifest_path=manifest_path,
            config=config,
            implementation_toml_paths=effective_toml_paths,
        ),
        contract_backend=_service_host_contract_backend_input(),
        activation_projection_package_names=(
            _service_host_activation_projection_package_names()
        ),
    )
    if not manifest_set.sql_roots:
        return ServiceHostDBSchemaInstallEvidence(
            status="skipped",
            source_manifest_path=manifest_set.source_manifest_path.as_posix(),
            manifest_kind=manifest_set.kind,
            reason="no_db_requirements",
        ).as_payload()
    if manifest_set.db_marker_scope_id is None:
        raise ServiceActivationRequiresMaterialization(
            "ServiceHost DB schema readiness requires a ServiceHost-owned DB "
            "marker scope id when DB requirements declare SQL roots."
        )
    connection = await _connect_service_host_db_boot_database(
        database_url=database_url,
    )
    try:
        result = await ensure_db_schema_installed_multi(
            connection=connection,
            sql_roots=manifest_set.sql_roots,
            environment_id=manifest_set.db_marker_scope_id,
            ocg_hash=manifest_set.db_schema_hash,
            ocg_head_commit_id=None,
            adapter="postgres",
        )
    finally:
        await connection.close()
    return ServiceHostDBSchemaInstallEvidence(
        status="installed",
        source_manifest_path=manifest_set.source_manifest_path.as_posix(),
        manifest_kind=manifest_set.kind,
        db_marker_scope_id=str(manifest_set.db_marker_scope_id),
        sql_root_count=len(manifest_set.sql_roots),
        schema_count=int(getattr(result, "schema_count", 0)),
        step_count=int(getattr(result, "step_count", 0)),
        db_schema_hash=manifest_set.db_schema_hash,
        authority_package_names=manifest_set.authority_package_names,
    ).as_payload()


async def _connect_service_host_db_boot_database(
    *,
    database_url: str,
) -> _ClosableDBBootConnection:
    try:
        import asyncpg  # pyright: ignore[reportMissingTypeStubs]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "asyncpg is required for ServiceHost DB schema readiness against Postgres."
        ) from exc
    connect = cast(
        Callable[[str], Awaitable[_ClosableDBBootConnection]],
        asyncpg.connect,
    )
    return await connect(database_url)


def _service_host_contract_target_input(
    *,
    runtime_manifest_path: Path,
    config: ServiceHostAppConfig | None,
    implementation_toml_paths: tuple[Path, ...],
) -> ServiceHostContractTargetInput:
    authority_root = (
        _service_host_ontology_authority_root(config=config)
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


def _service_host_contract_backend_input() -> ServiceHostContractBackendInput:
    backend = (os.environ.get("AWARE_PERSISTENCE_BACKEND") or "").strip() or None
    return ServiceHostContractBackendInput(
        persistence_backend=backend,
        adapter="postgres" if backend == "db" else None,
        database_url_present=bool(str(os.environ.get("DATABASE_URL") or "").strip()),
    )


def _service_host_ontology_authority_root(
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


def _service_host_activation_projection_package_names() -> tuple[str, ...]:
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
    "ServiceHostDBSchemaInstallEvidence",
    "ServiceHostOntologyRuntimeArtifactInstallEvidence",
    "ensure_service_host_db_schema_installed",
    "install_service_host_ontology_runtime_artifacts",
]
