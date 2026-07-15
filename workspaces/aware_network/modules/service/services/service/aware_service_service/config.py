from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import tomllib

from aware_comms import DuplexIpcEndpoint

_CONFIG_PATH_ENV = "AWARE_SERVICE_HOST_CONFIG_PATH"
_SOCKET_PATH_ENV = "AWARE_SERVICE_HOST_SOCKET_PATH"
_IMPLEMENTATION_TOMLS_ENV = "AWARE_SERVICE_HOST_IMPLEMENTATION_TOMLS"
_RUNTIME_MANIFEST_PATH_ENV = "AWARE_SERVICE_HOST_RUNTIME_MANIFEST_PATH"
_KERNEL_REPO_ROOT_ENV = "AWARE_SERVICE_HOST_KERNEL_REPO_ROOT"
_ARTIFACT_ROOT_ENV = "AWARE_SERVICE_HOST_ARTIFACT_ROOT"
_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV = (
    "AWARE_SERVICE_HOST_WORKSPACE_REVISION_MATERIALIZED_ROOT"
)
_WORKSPACE_REVISION_MANIFEST_PATH_ENV = (
    "AWARE_SERVICE_HOST_WORKSPACE_REVISION_MANIFEST_PATH"
)
_ECONOMY_ENDPOINT_ENV = "AWARE_SERVICE_HOST_ECONOMY_ENDPOINT"
_ECONOMY_REQUEST_TIMEOUT_ENV = "AWARE_SERVICE_HOST_ECONOMY_REQUEST_TIMEOUT_S"
_ENVIRONMENT_API_ENDPOINT_ENV = "AWARE_SERVICE_HOST_ENVIRONMENT_API_ENDPOINT"
_ENVIRONMENT_API_REQUEST_TIMEOUT_ENV = (
    "AWARE_SERVICE_HOST_ENVIRONMENT_API_REQUEST_TIMEOUT_S"
)
_ONTOLOGY_REPLICA_STATE_DB_PATH_ENV = (
    "AWARE_SERVICE_HOST_ONTOLOGY_REPLICA_STATE_DB_PATH"
)
_ONTOLOGY_REPLICA_PROJECTION_DB_PATH_ENV = (
    "AWARE_SERVICE_HOST_ONTOLOGY_REPLICA_PROJECTION_DB_PATH"
)

_DEFAULT_ECONOMY_REQUEST_TIMEOUT_S = 10.0
_DEFAULT_ENVIRONMENT_API_REQUEST_TIMEOUT_S = 30.0


@dataclass(frozen=True, slots=True)
class ServiceHostImplementationPackageConfig:
    toml_paths: tuple[Path, ...] = ()
    package_refs: tuple["ServiceHostImplementationPackageRef", ...] = ()

    @classmethod
    def from_env(cls) -> "ServiceHostImplementationPackageConfig":
        return ServiceHostAppConfig.from_env().implementation_packages


@dataclass(frozen=True, slots=True)
class ServiceHostImplementationPackageRef:
    family_key: str
    package_kind: str
    package_name: str
    manifest_path: Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None

    @property
    def has_semantic_identity(self) -> bool:
        return bool(self.semantic_package_id or self.semantic_root_id)


@dataclass(frozen=True, slots=True)
class ServiceHostExperiencePackageRef:
    family_key: str
    package_kind: str
    package_name: str
    manifest_path: Path | None = None
    workspace_package_id: str | None = None
    semantic_package_id: str | None = None
    semantic_object_instance_graph_commit_id: str | None = None
    semantic_head_commit_id: str | None = None
    semantic_branch_id: str | None = None
    semantic_root_kind: str | None = None
    semantic_root_id: str | None = None
    semantic_root_object_instance_graph_commit_id: str | None = None
    source_code_package_id: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostArtifactConfig:
    root: Path | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostReferencePackageConfig:
    experience_package_refs: tuple[ServiceHostExperiencePackageRef, ...] = ()
    experience_toml_paths: tuple[Path, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceHostWorkspaceRevisionConfig:
    materialized_workspace_root: Path | None = None
    manifest_path: Path | None = None
    experience_package_refs: tuple[ServiceHostExperiencePackageRef, ...] = ()


@dataclass(frozen=True, slots=True)
class ServiceHostEnvironmentConfig:
    api_endpoint: str | None = None
    request_timeout_s: float = _DEFAULT_ENVIRONMENT_API_REQUEST_TIMEOUT_S

    @property
    def enabled(self) -> bool:
        return bool(str(self.api_endpoint or "").strip())


@dataclass(frozen=True, slots=True)
class ServiceHostOntologyReplicaConfig:
    state_db_path: Path | None = None
    projection_db_path: Path | None = None

    @property
    def enabled(self) -> bool:
        return self.state_db_path is not None


@dataclass(frozen=True, slots=True)
class ServiceHostOntologyAuthorityConfig:
    package_names: tuple[str, ...] = ()
    source_kind: str | None = None
    root: Path | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostAppConfig:
    kernel_repo_root: Path | None = None
    implementation_packages: ServiceHostImplementationPackageConfig = field(
        default_factory=ServiceHostImplementationPackageConfig
    )
    runtime_manifest_path: Path | None = None
    artifact: ServiceHostArtifactConfig = field(
        default_factory=ServiceHostArtifactConfig
    )
    reference_packages: ServiceHostReferencePackageConfig = field(
        default_factory=ServiceHostReferencePackageConfig
    )
    workspace_revision: ServiceHostWorkspaceRevisionConfig = field(
        default_factory=ServiceHostWorkspaceRevisionConfig
    )
    environment: ServiceHostEnvironmentConfig = field(
        default_factory=ServiceHostEnvironmentConfig
    )
    ontology_replica: ServiceHostOntologyReplicaConfig = field(
        default_factory=ServiceHostOntologyReplicaConfig
    )
    ontology_authority: ServiceHostOntologyAuthorityConfig = field(
        default_factory=ServiceHostOntologyAuthorityConfig
    )
    economy: "ServiceHostEconomyConfig" = field(
        default_factory=lambda: ServiceHostEconomyConfig()
    )

    @classmethod
    def from_env(cls) -> "ServiceHostAppConfig":
        return _build_app_config(
            file_config=_load_bootstrap_file_config_from_env(),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "ServiceHostAppConfig":
        return _build_app_config(
            file_config=_load_bootstrap_file_config(Path(path)),
        )

    @property
    def artifact_root(self) -> Path | None:
        return self.artifact.root or self.workspace_revision.materialized_workspace_root

    @property
    def experience_package_refs(self) -> tuple[ServiceHostExperiencePackageRef, ...]:
        if self.reference_packages.experience_package_refs:
            return self.reference_packages.experience_package_refs
        return self.workspace_revision.experience_package_refs


@dataclass(frozen=True, slots=True)
class ServiceHostIpcConfig:
    socket_path: Path

    @property
    def endpoint(self) -> DuplexIpcEndpoint:
        return DuplexIpcEndpoint.unix_socket(socket_path=str(self.socket_path))

    @classmethod
    def from_env(cls) -> "ServiceHostIpcConfig":
        return ServiceHostBootstrapConfig.from_env().ipc


@dataclass(frozen=True, slots=True)
class ServiceHostBootstrapConfig:
    ipc: ServiceHostIpcConfig
    app: ServiceHostAppConfig = field(default_factory=ServiceHostAppConfig)
    source_path: Path | None = None

    @classmethod
    def from_env(cls) -> "ServiceHostBootstrapConfig":
        return _build_bootstrap_config(
            file_config=_load_bootstrap_file_config_from_env(),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "ServiceHostBootstrapConfig":
        return _build_bootstrap_config(
            file_config=_load_bootstrap_file_config(Path(path)),
        )


@dataclass(frozen=True, slots=True)
class _BootstrapFileConfig:
    source_path: Path
    kernel_repo_root: Path | None = None
    socket_path: Path | None = None
    runtime_manifest_path: Path | None = None
    artifact_root: Path | None = None
    workspace_revision_materialized_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None
    implementation_package_toml_paths: tuple[Path, ...] = ()
    implementation_package_refs: tuple[ServiceHostImplementationPackageRef, ...] = ()
    reference_package_experience_refs: tuple[ServiceHostExperiencePackageRef, ...] = ()
    reference_package_experience_toml_paths: tuple[Path, ...] = ()
    workspace_revision_experience_package_refs: tuple[
        ServiceHostExperiencePackageRef, ...
    ] = ()
    ontology_authority_package_names: tuple[str, ...] = ()
    ontology_authority_source_kind: str | None = None
    ontology_authority_root: Path | None = None
    environment_api_endpoint: str | None = None
    environment_api_request_timeout_s: float | None = None
    ontology_replica_state_db_path: Path | None = None
    ontology_replica_projection_db_path: Path | None = None
    economy_endpoint: str | None = None
    economy_request_timeout_s: float | None = None


@dataclass(frozen=True, slots=True)
class ServiceHostEconomyConfig:
    endpoint: str | None = None
    request_timeout_s: float = _DEFAULT_ECONOMY_REQUEST_TIMEOUT_S

    @property
    def enabled(self) -> bool:
        return bool(str(self.endpoint or "").strip())


def _build_bootstrap_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> ServiceHostBootstrapConfig:
    return ServiceHostBootstrapConfig(
        ipc=ServiceHostIpcConfig(
            socket_path=_resolve_required_path(
                env_name=_SOCKET_PATH_ENV,
                file_value=file_config.socket_path if file_config is not None else None,
                error_message=(
                    "Service host socket path is required via "
                    f"{_SOCKET_PATH_ENV} or bootstrap config file."
                ),
            )
        ),
        app=_build_app_config(file_config=file_config),
        source_path=file_config.source_path if file_config is not None else None,
    )


def _build_app_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> ServiceHostAppConfig:
    implementation_package_toml_paths = _resolve_path_list_from_env_or_file(
        env_name=_IMPLEMENTATION_TOMLS_ENV,
        file_values=(
            file_config.implementation_package_toml_paths
            if file_config is not None
            else ()
        ),
    )
    workspace_revision = _resolve_workspace_revision_config(file_config=file_config)
    artifact = _resolve_artifact_config(
        file_config=file_config,
    )
    reference_packages = _resolve_reference_package_config(
        file_config=file_config,
    )
    effective_experience_package_refs = (
        reference_packages.experience_package_refs
        or workspace_revision.experience_package_refs
    )
    _validate_workspace_revision_config(
        workspace_revision=workspace_revision,
        implementation_package_toml_paths=implementation_package_toml_paths,
        implementation_package_refs=(
            file_config.implementation_package_refs if file_config is not None else ()
        ),
    )
    _validate_artifact_config(
        artifact=artifact,
        implementation_package_toml_paths=implementation_package_toml_paths,
        implementation_package_refs=(
            file_config.implementation_package_refs if file_config is not None else ()
        ),
        experience_package_refs=effective_experience_package_refs,
        experience_toml_paths=reference_packages.experience_toml_paths,
    )
    return ServiceHostAppConfig(
        kernel_repo_root=_resolve_optional_path(
            env_name=_KERNEL_REPO_ROOT_ENV,
            file_value=(
                file_config.kernel_repo_root if file_config is not None else None
            ),
        ),
        implementation_packages=ServiceHostImplementationPackageConfig(
            toml_paths=implementation_package_toml_paths,
            package_refs=(
                file_config.implementation_package_refs
                if file_config is not None
                else ()
            ),
        ),
        runtime_manifest_path=_resolve_optional_path(
            env_name=_RUNTIME_MANIFEST_PATH_ENV,
            file_value=(
                file_config.runtime_manifest_path if file_config is not None else None
            ),
        ),
        artifact=artifact,
        reference_packages=reference_packages,
        workspace_revision=workspace_revision,
        environment=ServiceHostEnvironmentConfig(
            api_endpoint=_resolve_optional_token(
                env_name=_ENVIRONMENT_API_ENDPOINT_ENV,
                file_value=(
                    file_config.environment_api_endpoint
                    if file_config is not None
                    else None
                ),
            ),
            request_timeout_s=_resolve_float(
                env_name=_ENVIRONMENT_API_REQUEST_TIMEOUT_ENV,
                file_value=(
                    file_config.environment_api_request_timeout_s
                    if file_config is not None
                    else None
                ),
                default=_DEFAULT_ENVIRONMENT_API_REQUEST_TIMEOUT_S,
            ),
        ),
        ontology_replica=ServiceHostOntologyReplicaConfig(
            state_db_path=_resolve_optional_path(
                env_name=_ONTOLOGY_REPLICA_STATE_DB_PATH_ENV,
                file_value=(
                    file_config.ontology_replica_state_db_path
                    if file_config is not None
                    else None
                ),
            ),
            projection_db_path=_resolve_optional_path(
                env_name=_ONTOLOGY_REPLICA_PROJECTION_DB_PATH_ENV,
                file_value=(
                    file_config.ontology_replica_projection_db_path
                    if file_config is not None
                    else None
                ),
            ),
        ),
        ontology_authority=ServiceHostOntologyAuthorityConfig(
            package_names=(
                file_config.ontology_authority_package_names
                if file_config is not None
                else ()
            ),
            source_kind=(
                file_config.ontology_authority_source_kind
                if file_config is not None
                else None
            ),
            root=(
                file_config.ontology_authority_root if file_config is not None else None
            ),
        ),
        economy=ServiceHostEconomyConfig(
            endpoint=_resolve_optional_token(
                env_name=_ECONOMY_ENDPOINT_ENV,
                file_value=(
                    file_config.economy_endpoint if file_config is not None else None
                ),
            ),
            request_timeout_s=_resolve_float(
                env_name=_ECONOMY_REQUEST_TIMEOUT_ENV,
                file_value=(
                    file_config.economy_request_timeout_s
                    if file_config is not None
                    else None
                ),
                default=_DEFAULT_ECONOMY_REQUEST_TIMEOUT_S,
            ),
        ),
    )


def _resolve_artifact_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> ServiceHostArtifactConfig:
    root = _resolve_optional_path(
        env_name=_ARTIFACT_ROOT_ENV,
        file_value=file_config.artifact_root if file_config is not None else None,
    )
    return ServiceHostArtifactConfig(root=root)


def _resolve_reference_package_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> ServiceHostReferencePackageConfig:
    experience_refs = (
        file_config.reference_package_experience_refs if file_config is not None else ()
    )
    experience_toml_paths = (
        file_config.reference_package_experience_toml_paths
        if file_config is not None
        else ()
    )
    return ServiceHostReferencePackageConfig(
        experience_package_refs=experience_refs,
        experience_toml_paths=experience_toml_paths,
    )


def _resolve_workspace_revision_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> ServiceHostWorkspaceRevisionConfig:
    materialized_workspace_root = _resolve_optional_path(
        env_name=_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV,
        file_value=(
            file_config.workspace_revision_materialized_root
            if file_config is not None
            else None
        ),
    )
    manifest_path = _resolve_optional_path(
        env_name=_WORKSPACE_REVISION_MANIFEST_PATH_ENV,
        file_value=(
            file_config.workspace_revision_manifest_path
            if file_config is not None
            else None
        ),
    )
    if materialized_workspace_root is None and manifest_path is None:
        return ServiceHostWorkspaceRevisionConfig()

    if materialized_workspace_root is None:
        materialized_workspace_root = _workspace_root_from_revision_manifest_path(
            manifest_path
        )
    if materialized_workspace_root is not None and manifest_path is None:
        manifest_path = _revision_filesystem_manifest_path(materialized_workspace_root)
    return ServiceHostWorkspaceRevisionConfig(
        materialized_workspace_root=materialized_workspace_root,
        manifest_path=manifest_path,
        experience_package_refs=(
            file_config.workspace_revision_experience_package_refs
            if file_config is not None
            else ()
        ),
    )


def _validate_workspace_revision_config(
    *,
    workspace_revision: ServiceHostWorkspaceRevisionConfig,
    implementation_package_toml_paths: tuple[Path, ...],
    implementation_package_refs: tuple[ServiceHostImplementationPackageRef, ...],
) -> None:
    materialized_workspace_root = workspace_revision.materialized_workspace_root
    manifest_path = workspace_revision.manifest_path
    if materialized_workspace_root is None and manifest_path is None:
        return
    if materialized_workspace_root is None or manifest_path is None:
        raise RuntimeError(
            "Service host workspace_revision requires both materialized_workspace_root "
            "and manifest_path after normalization."
        )
    expected_manifest_path = _revision_filesystem_manifest_path(
        materialized_workspace_root
    )
    if manifest_path != expected_manifest_path:
        raise RuntimeError(
            "Service host workspace_revision manifest_path must be the canonical "
            "revision filesystem manifest under materialized_workspace_root: "
            f"expected={expected_manifest_path} actual={manifest_path}"
        )
    if not manifest_path.is_file():
        raise RuntimeError(
            "Service host workspace_revision manifest_path does not exist: "
            f"{manifest_path}"
        )
    for toml_path in implementation_package_toml_paths:
        if not _is_relative_to(path=toml_path, parent=materialized_workspace_root):
            raise RuntimeError(
                "Service host workspace_revision requires implementation package "
                "TOMLs to resolve under materialized_workspace_root: "
                f"toml_path={toml_path} root={materialized_workspace_root}"
            )
    for package_ref in implementation_package_refs:
        manifest_path = package_ref.manifest_path
        if manifest_path is None:
            continue
        if not _is_relative_to(path=manifest_path, parent=materialized_workspace_root):
            raise RuntimeError(
                "Service host workspace_revision requires implementation package "
                "refs to resolve under materialized_workspace_root: "
                f"manifest_path={manifest_path} root={materialized_workspace_root}"
            )
    for package_ref in workspace_revision.experience_package_refs:
        manifest_path = package_ref.manifest_path
        if manifest_path is None:
            continue
        if not _is_relative_to(path=manifest_path, parent=materialized_workspace_root):
            raise RuntimeError(
                "Service host workspace_revision requires Experience package "
                "refs to resolve under materialized_workspace_root: "
                f"manifest_path={manifest_path} root={materialized_workspace_root}"
            )


def _validate_artifact_config(
    *,
    artifact: ServiceHostArtifactConfig,
    implementation_package_toml_paths: tuple[Path, ...],
    implementation_package_refs: tuple[ServiceHostImplementationPackageRef, ...],
    experience_package_refs: tuple[ServiceHostExperiencePackageRef, ...],
    experience_toml_paths: tuple[Path, ...],
) -> None:
    artifact_root = artifact.root
    if artifact_root is None:
        return
    for toml_path in implementation_package_toml_paths:
        if not _is_relative_to(path=toml_path, parent=artifact_root):
            raise RuntimeError(
                "Service host artifact.root requires implementation package "
                "TOMLs to resolve under the artifact root: "
                f"toml_path={toml_path} root={artifact_root}"
            )
    for package_ref in implementation_package_refs:
        manifest_path = package_ref.manifest_path
        if manifest_path is None:
            continue
        if not _is_relative_to(path=manifest_path, parent=artifact_root):
            raise RuntimeError(
                "Service host artifact.root requires implementation package "
                "refs to resolve under the artifact root: "
                f"manifest_path={manifest_path} root={artifact_root}"
            )
    for package_ref in experience_package_refs:
        manifest_path = package_ref.manifest_path
        if manifest_path is None:
            continue
        if not _is_relative_to(path=manifest_path, parent=artifact_root):
            raise RuntimeError(
                "Service host artifact.root requires Experience package "
                "refs to resolve under the artifact root: "
                f"manifest_path={manifest_path} root={artifact_root}"
            )
    for toml_path in experience_toml_paths:
        if not _is_relative_to(path=toml_path, parent=artifact_root):
            raise RuntimeError(
                "Service host artifact.root requires Experience package TOMLs "
                "to resolve under the artifact root: "
                f"toml_path={toml_path} root={artifact_root}"
            )


def _load_bootstrap_file_config_from_env() -> _BootstrapFileConfig | None:
    config_path = _read_env_path(_CONFIG_PATH_ENV)
    if config_path is None:
        return None
    return _load_bootstrap_file_config(config_path)


def _load_bootstrap_file_config(path: str | Path) -> _BootstrapFileConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists() or not config_path.is_file():
        raise RuntimeError(
            f"Service host bootstrap config file was not found: {config_path}"
        )
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError("Service host bootstrap config must decode to a TOML table.")

    base_dir = config_path.parent
    ipc_payload = _read_table(payload, key="ipc")
    app_payload = _read_table(payload, key="app")
    economy_payload = _read_table(payload, key="economy")
    environment_payload = _read_table(payload, key="environment")
    ontology_authority_payload = _read_table(payload, key="ontology_authority")
    ontology_replica_payload = _read_table(payload, key="ontology_replica")
    implementation_payload = _read_table(payload, key="implementation_packages")
    artifact_payload = _read_table(payload, key="artifact")
    reference_packages_payload = _read_table(payload, key="reference_packages")
    workspace_revision_payload = _read_table(payload, key="workspace_revision")
    return _BootstrapFileConfig(
        source_path=config_path,
        socket_path=_read_optional_path_from_table(
            ipc_payload,
            key="socket_path",
            base_dir=base_dir,
        ),
        runtime_manifest_path=_read_optional_path_from_table(
            app_payload,
            key="runtime_manifest_path",
            base_dir=base_dir,
        ),
        kernel_repo_root=_read_optional_path_from_table(
            app_payload,
            key="kernel_repo_root",
            base_dir=base_dir,
        ),
        artifact_root=_read_optional_path_from_table(
            artifact_payload,
            key="root",
            base_dir=base_dir,
        ),
        workspace_revision_materialized_root=_read_optional_path_from_table(
            workspace_revision_payload,
            key="materialized_workspace_root",
            base_dir=base_dir,
        ),
        workspace_revision_manifest_path=_read_optional_path_from_table(
            workspace_revision_payload,
            key="manifest_path",
            base_dir=base_dir,
        ),
        implementation_package_toml_paths=_read_path_list_from_table(
            implementation_payload,
            key="toml_paths",
            base_dir=base_dir,
        ),
        implementation_package_refs=_read_package_refs_from_table(
            implementation_payload,
            base_dir=base_dir,
        ),
        reference_package_experience_refs=_read_experience_package_refs_from_table(
            reference_packages_payload,
            base_dir=base_dir,
            table_label="reference_packages.experience_package_refs",
        ),
        reference_package_experience_toml_paths=_read_path_list_from_table(
            reference_packages_payload,
            key="experience_toml_paths",
            base_dir=base_dir,
        ),
        workspace_revision_experience_package_refs=(
            _read_experience_package_refs_from_table(
                workspace_revision_payload,
                base_dir=base_dir,
                table_label="workspace_revision.experience_package_refs",
            )
        ),
        ontology_authority_package_names=_read_token_list_from_table(
            ontology_authority_payload,
            key="package_names",
        ),
        ontology_authority_source_kind=_read_optional_token_from_table(
            ontology_authority_payload,
            key="source_kind",
        ),
        ontology_authority_root=_read_optional_path_from_table(
            ontology_authority_payload,
            key="root",
            base_dir=base_dir,
        ),
        environment_api_endpoint=_read_optional_token_from_table(
            environment_payload,
            key="api_endpoint",
        ),
        environment_api_request_timeout_s=_read_optional_float_from_table(
            environment_payload,
            key="request_timeout_s",
        ),
        ontology_replica_state_db_path=_read_optional_path_from_table(
            ontology_replica_payload,
            key="state_db_path",
            base_dir=base_dir,
        ),
        ontology_replica_projection_db_path=_read_optional_path_from_table(
            ontology_replica_payload,
            key="projection_db_path",
            base_dir=base_dir,
        ),
        economy_endpoint=_read_optional_token_from_table(
            economy_payload,
            key="endpoint",
        ),
        economy_request_timeout_s=_read_optional_float_from_table(
            economy_payload,
            key="request_timeout_s",
        ),
    )


def _read_table(payload: dict[str, object], *, key: str) -> dict[str, object]:
    raw = payload.get(key)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RuntimeError(
            f"Service host bootstrap config table {key!r} must be a TOML table."
        )
    return raw


def _read_optional_path_from_table(
    payload: dict[str, object],
    *,
    key: str,
    base_dir: Path,
) -> Path | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(
            f"Service host bootstrap config field {key!r} must be a non-empty string path."
        )
    return _normalize_path_token(raw, base_dir=base_dir)


def _read_optional_token_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> str | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise RuntimeError(
            f"Service host bootstrap config field {key!r} must be a string."
        )
    token = raw.strip()
    return token or None


def _read_optional_float_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> float | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    raise RuntimeError(f"Service host bootstrap config field {key!r} must be a number.")


def _read_path_list_from_table(
    payload: dict[str, object],
    *,
    key: str,
    base_dir: Path,
) -> tuple[Path, ...]:
    raw = payload.get(key)
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError(
            f"Service host bootstrap config field {key!r} must be an array of string paths."
        )
    tokens: list[Path] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(
                f"Service host bootstrap config field {key!r} must contain non-empty string paths."
            )
        tokens.append(_normalize_path_token(item, base_dir=base_dir))
    return _dedupe_paths(tokens)


def _read_token_list_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> tuple[str, ...]:
    raw = payload.get(key)
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError(
            f"Service host bootstrap config field {key!r} must be an array of strings."
        )
    tokens: list[str] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(
                f"Service host bootstrap config field {key!r} must contain "
                "non-empty strings."
            )
        token = item.strip()
        if token in seen:
            continue
        seen.add(token)
        tokens.append(token)
    return tuple(tokens)


def _read_package_refs_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> tuple[ServiceHostImplementationPackageRef, ...]:
    raw = payload.get("package_refs")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError(
            "Service host bootstrap config field 'package_refs' must be an array "
            "of package reference tables."
        )
    refs: list[ServiceHostImplementationPackageRef] = []
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Service host bootstrap config field 'package_refs' must contain "
                "TOML tables."
            )
        refs.append(_read_package_ref_from_table(item, base_dir=base_dir))
    return tuple(refs)


def _read_package_ref_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> ServiceHostImplementationPackageRef:
    return ServiceHostImplementationPackageRef(
        family_key=_read_required_token_from_table(payload, key="family_key"),
        package_kind=_read_required_token_from_table(payload, key="package_kind"),
        package_name=_read_required_token_from_table(payload, key="package_name"),
        manifest_path=_read_optional_path_from_table(
            payload,
            key="manifest_path",
            base_dir=base_dir,
        ),
        workspace_package_id=_read_optional_token_from_table(
            payload,
            key="workspace_package_id",
        ),
        semantic_package_id=_read_optional_token_from_table(
            payload,
            key="semantic_package_id",
        ),
        semantic_object_instance_graph_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_object_instance_graph_commit_id",
        ),
        semantic_head_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_head_commit_id",
        ),
        semantic_branch_id=_read_optional_token_from_table(
            payload,
            key="semantic_branch_id",
        ),
        semantic_root_kind=_read_optional_token_from_table(
            payload,
            key="semantic_root_kind",
        ),
        semantic_root_id=_read_optional_token_from_table(
            payload,
            key="semantic_root_id",
        ),
        semantic_root_object_instance_graph_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_root_object_instance_graph_commit_id",
        ),
        source_code_package_id=_read_optional_token_from_table(
            payload,
            key="source_code_package_id",
        ),
    )


def _read_experience_package_refs_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
    table_label: str,
) -> tuple[ServiceHostExperiencePackageRef, ...]:
    raw = payload.get("experience_package_refs")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError(
            "Service host bootstrap config field "
            f"{table_label!r} must be an array of package reference tables."
        )
    refs: list[ServiceHostExperiencePackageRef] = []
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Service host bootstrap config field "
                f"{table_label!r} must contain TOML tables."
            )
        refs.append(_read_experience_package_ref_from_table(item, base_dir=base_dir))
    return tuple(refs)


def _read_experience_package_ref_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> ServiceHostExperiencePackageRef:
    return ServiceHostExperiencePackageRef(
        family_key=_read_required_token_from_table(payload, key="family_key"),
        package_kind=_read_required_token_from_table(payload, key="package_kind"),
        package_name=_read_required_token_from_table(payload, key="package_name"),
        manifest_path=_read_optional_path_from_table(
            payload,
            key="manifest_path",
            base_dir=base_dir,
        ),
        workspace_package_id=_read_optional_token_from_table(
            payload,
            key="workspace_package_id",
        ),
        semantic_package_id=_read_optional_token_from_table(
            payload,
            key="semantic_package_id",
        ),
        semantic_object_instance_graph_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_object_instance_graph_commit_id",
        ),
        semantic_head_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_head_commit_id",
        ),
        semantic_branch_id=_read_optional_token_from_table(
            payload,
            key="semantic_branch_id",
        ),
        semantic_root_kind=_read_optional_token_from_table(
            payload,
            key="semantic_root_kind",
        ),
        semantic_root_id=_read_optional_token_from_table(
            payload,
            key="semantic_root_id",
        ),
        semantic_root_object_instance_graph_commit_id=_read_optional_token_from_table(
            payload,
            key="semantic_root_object_instance_graph_commit_id",
        ),
        source_code_package_id=_read_optional_token_from_table(
            payload,
            key="source_code_package_id",
        ),
    )


def _read_required_token_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> str:
    token = _read_optional_token_from_table(payload, key=key)
    if token is None:
        raise RuntimeError(
            f"Service host bootstrap config field {key!r} must be a non-empty string."
        )
    return token


def _resolve_required_path(
    *,
    env_name: str,
    file_value: Path | None,
    error_message: str,
) -> Path:
    resolved = _resolve_optional_path(env_name=env_name, file_value=file_value)
    if resolved is None:
        raise RuntimeError(error_message)
    return resolved


def _resolve_optional_path(
    *,
    env_name: str,
    file_value: Path | None,
) -> Path | None:
    env_path = _read_env_path(env_name)
    if env_path is not None:
        return env_path
    return file_value


def _resolve_path_list_from_env_or_file(
    *,
    env_name: str,
    file_values: tuple[Path, ...],
) -> tuple[Path, ...]:
    raw = str(os.environ.get(env_name, "") or "").strip()
    if not raw:
        return file_values
    tokens = tuple(item.strip() for item in raw.split(os.pathsep))
    return _normalize_path_tokens(tokens)


def _resolve_optional_token(
    *,
    env_name: str,
    file_value: str | None,
) -> str | None:
    raw = str(os.environ.get(env_name, "") or "").strip()
    if raw:
        return raw
    token = str(file_value or "").strip()
    return token or None


def _resolve_float(
    *,
    env_name: str,
    file_value: float | None,
    default: float,
) -> float:
    raw = str(os.environ.get(env_name, "") or "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError as exc:
            raise RuntimeError(
                f"Environment variable {env_name} must be a valid float."
            ) from exc
    return float(file_value) if file_value is not None else default


def _read_env_path(env_name: str) -> Path | None:
    raw = str(os.environ.get(env_name, "") or "").strip()
    if not raw:
        return None
    return _normalize_path_token(raw)


def _normalize_path_tokens(tokens: tuple[str, ...]) -> tuple[Path, ...]:
    normalized = [_normalize_path_token(token) for token in tokens if token.strip()]
    return _dedupe_paths(normalized)


def _normalize_path_token(raw: str, *, base_dir: Path | None = None) -> Path:
    path = Path(raw).expanduser()
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path.resolve()


def _revision_filesystem_manifest_path(workspace_root: Path) -> Path:
    return (
        workspace_root / ".aware" / "workspace" / "revision-filesystem.manifest.json"
    ).resolve()


def _workspace_root_from_revision_manifest_path(
    manifest_path: Path | None,
) -> Path | None:
    if manifest_path is None:
        return None
    if manifest_path.parts[-3:] != (
        ".aware",
        "workspace",
        "revision-filesystem.manifest.json",
    ):
        raise RuntimeError(
            "Service host workspace_revision manifest_path must end with "
            ".aware/workspace/revision-filesystem.manifest.json: "
            f"{manifest_path}"
        )
    return manifest_path.parents[2].resolve()


def _is_relative_to(*, path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _dedupe_paths(paths: list[Path]) -> tuple[Path, ...]:
    normalized: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = path.as_posix()
        if key in seen:
            continue
        normalized.append(path)
        seen.add(key)
    return tuple(normalized)


__all__ = [
    "ServiceHostArtifactConfig",
    "ServiceHostAppConfig",
    "ServiceHostBootstrapConfig",
    "ServiceHostEconomyConfig",
    "ServiceHostExperiencePackageRef",
    "ServiceHostImplementationPackageRef",
    "ServiceHostImplementationPackageConfig",
    "ServiceHostIpcConfig",
    "ServiceHostReferencePackageConfig",
    "ServiceHostWorkspaceRevisionConfig",
]
