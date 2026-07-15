from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, fields
import json
import os
from pathlib import Path
import tomllib
from uuid import UUID

from aware_interface.runtime_artifact_refs import (
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY,
    ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE,
    InterfaceRuntimeArtifactRef,
    runtime_artifact_refs_from_payload,
)

DEFAULT_HOST_LABEL = "interface-service"
DEFAULT_NAMESPACE = "service"
DEFAULT_HEARTBEAT_INTERVAL_S = 20.0
DEFAULT_REFRESH_INTERVAL_S = 15.0
DEFAULT_CAPABILITIES = ("interface-service", "fanout", "runtime-snapshot")
DEFAULT_LANE_SYNC_WINDOW_KEY = "execution"
DEFAULT_REQUEST_TIMEOUT_S = 60.0

_CONFIG_PATH_ENV = "AWARE_INTERFACE_SERVICE_CONFIG_PATH"
_REPOSITORY_ROOT_ENV = "AWARE_INTERFACE_SERVICE_REPOSITORY_ROOT"
_SHARED_REPOSITORY_ROOT_ENV = "AWARE_REPOSITORY_ROOT"
_SHARED_REPO_ROOT_ENV = "AWARE_REPO_ROOT"
_STATE_HOME_ENV = "AWARE_INTERFACE_SERVICE_STATE_HOME"
_SHARED_STATE_HOME_ENV = "AWARE_STATE_HOME"
_NAMESPACE_ENV = "AWARE_INTERFACE_SERVICE_NAMESPACE"
_HOST_LABEL_ENV = "AWARE_INTERFACE_SERVICE_HOST_LABEL"
_ENDPOINT_ENV = "AWARE_INTERFACE_SERVICE_ENDPOINT"
_AUTH_TOKEN_ENV = "AWARE_INTERFACE_SERVICE_AUTH_TOKEN"
_SHARED_AUTH_TOKEN_ENV = "AWARE_AUTH_TOKEN"
_SHARED_APT_TOKEN_ENV = "AWARE_APT_TOKEN"
_ENVIRONMENT_CONFIG_ID_ENV = "AWARE_INTERFACE_SERVICE_ENVIRONMENT_CONFIG_ID"
_SHARED_ENVIRONMENT_CONFIG_ID_ENV = "AWARE_ENVIRONMENT_CONFIG_ID"
_RUNTIME_MANIFEST_PATH_ENV = "AWARE_INTERFACE_SERVICE_RUNTIME_MANIFEST_PATH"
_RUNTIME_ARTIFACT_REFS_JSON_ENV = "AWARE_INTERFACE_SERVICE_RUNTIME_ARTIFACT_REFS_JSON"
_RUNTIME_ARTIFACT_REFS_PATH_ENV = "AWARE_INTERFACE_SERVICE_RUNTIME_ARTIFACT_REFS_PATH"
_LOCAL_STATE_REGISTRY_PATH_ENV = "AWARE_INTERFACE_SERVICE_LOCAL_STATE_REGISTRY_PATH"
_HEARTBEAT_INTERVAL_ENV = "AWARE_INTERFACE_SERVICE_HEARTBEAT_INTERVAL_S"
_REFRESH_INTERVAL_ENV = "AWARE_INTERFACE_SERVICE_REFRESH_INTERVAL_S"
_REQUEST_TIMEOUT_ENV = "AWARE_INTERFACE_SERVICE_REQUEST_TIMEOUT_S"
_ENSURE_BOOT_GRAPH_ENV = "AWARE_INTERFACE_SERVICE_ENSURE_BOOT_GRAPH"
_ALLOW_DEGRADED_LOCAL_SHELL_ENV = "AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL"
_REQUIRE_LIVE_RUNTIME_ENV = "AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME"
_ONCE_ENV = "AWARE_INTERFACE_SERVICE_ONCE"
_CAPABILITIES_ENV = "AWARE_INTERFACE_SERVICE_CAPABILITIES"
_LANE_SYNC_ENABLED_ENV = "AWARE_INTERFACE_SERVICE_LANE_SYNC_ENABLED"
_LANE_SYNC_WINDOW_KEY_ENV = "AWARE_INTERFACE_SERVICE_LANE_SYNC_WINDOW_KEY"
_LANE_SYNC_INCLUDE_COMMIT_PAYLOAD_ENV = (
    "AWARE_INTERFACE_SERVICE_LANE_SYNC_INCLUDE_COMMIT_PAYLOAD"
)
_LOCAL_SERVICE_IMPLEMENTATION_TOMLS_ENV = (
    "AWARE_INTERFACE_SERVICE_LOCAL_SERVICE_IMPLEMENTATION_TOMLS"
)
_LOCAL_SERVICE_BOOTSTRAP_CONFIG_PATH_ENV = (
    "AWARE_INTERFACE_SERVICE_LOCAL_SERVICE_HOST_BOOTSTRAP_CONFIG_PATH"
)
_DEV_ADAPTERS_ENV = "AWARE_INTERFACE_SERVICE_DEV_ADAPTERS"
_INTERFACE_PACKAGE_NAME_ENV = "AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME"
_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_REVISION_MATERIALIZED_ROOT"
)
_WORKSPACE_REVISION_MANIFEST_PATH_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_REVISION_MANIFEST_PATH"
)
_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL"
)
_WORKSPACE_DEPLOYMENT_INDEX_URL_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_INDEX_URL"
)
_WORKSPACE_DEPLOYMENT_CHANNEL_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_CHANNEL"
)
_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY"
)
_WORKSPACE_DEPLOYMENT_TARGET_ROOT_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_TARGET_ROOT"
)
_WORKSPACE_DEPLOYMENT_RECEIPT_PATH_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_RECEIPT_PATH"
)
_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_REVISION_ID"
)
_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH_ENV = (
    "AWARE_INTERFACE_SERVICE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH"
)
_ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL"
)
_ENVIRONMENT_RUNTIME_INDEX_URL_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_INDEX_URL"
)
_ENVIRONMENT_RUNTIME_CHANNEL_ENV = "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_CHANNEL"
_ENVIRONMENT_RUNTIME_ARTIFACT_KEY_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_ARTIFACT_KEY"
)
_ENVIRONMENT_RUNTIME_TARGET_ROOT_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_TARGET_ROOT"
)
_ENVIRONMENT_RUNTIME_RECEIPT_PATH_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_RECEIPT_PATH"
)
_ENVIRONMENT_RUNTIME_REVISION_ID_ENV = (
    "AWARE_INTERFACE_SERVICE_ENVIRONMENT_RUNTIME_REVISION_ID"
)
_LEGACY_INTERFACE_RUNTIME_ENV_NAMES: tuple[str, ...] = (
    _RUNTIME_MANIFEST_PATH_ENV,
    _ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL_ENV,
    _ENVIRONMENT_RUNTIME_INDEX_URL_ENV,
    _ENVIRONMENT_RUNTIME_CHANNEL_ENV,
    _ENVIRONMENT_RUNTIME_ARTIFACT_KEY_ENV,
    _ENVIRONMENT_RUNTIME_TARGET_ROOT_ENV,
    _ENVIRONMENT_RUNTIME_RECEIPT_PATH_ENV,
    _ENVIRONMENT_RUNTIME_REVISION_ID_ENV,
)


@dataclass(frozen=True, slots=True)
class InterfaceHostDevAdapterSpec:
    service_key: str
    adapter_key: str


@dataclass(frozen=True, slots=True)
class InterfaceHostRuntimeManifestResolution:
    source_kind: str
    runtime_manifest_path: Path | None = None
    runtime_artifact_refs: tuple[InterfaceRuntimeArtifactRef, ...] = ()
    workspace_deployment_revision_id: str | None = None
    environment_runtime_revision_id: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceRuntimeManifestBootstrapInputs:
    """Local/bootstrap inputs used to resolve the Interface runtime manifest."""

    workspace_root: str
    workspace_deployment_authority_base_url: str | None = None
    workspace_deployment_index_url: str | None = None
    workspace_deployment_channel: str | None = None
    workspace_deployment_artifact_key: str | None = None
    workspace_deployment_target_root: str | None = None
    workspace_deployment_receipt_path: str | None = None
    workspace_deployment_revision_id: str | None = None
    workspace_deployment_payload_path: str | None = None
    environment_manifest_path: str | None = None
    environment_runtime_authority_base_url: str | None = None
    environment_runtime_index_url: str | None = None
    environment_runtime_channel: str | None = None
    environment_runtime_artifact_key: str | None = None
    environment_runtime_target_root: str | None = None
    environment_runtime_receipt_path: str | None = None
    environment_runtime_revision_id: str | None = None


@dataclass(frozen=True, slots=True)
class InterfaceHostInterfacePackageRef:
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
class InterfaceHostWorkspaceRevisionConfig:
    materialized_workspace_root: Path | None = None
    manifest_path: Path | None = None
    interface_package_refs: tuple[InterfaceHostInterfacePackageRef, ...] = ()


@dataclass(frozen=True, slots=True)
class InterfaceHostServiceConfig:
    repository_root: Path
    state_home: Path
    namespace: str = DEFAULT_NAMESPACE
    host_label: str = DEFAULT_HOST_LABEL
    endpoint: str | None = None
    auth_token: str | None = None
    environment_config_id: UUID | None = None
    runtime_manifest_path: Path | None = None
    runtime_artifact_refs: tuple[InterfaceRuntimeArtifactRef, ...] = ()
    local_state_registry_path: Path | None = None
    runtime_manifest_source_kind: str | None = None
    workspace_deployment_revision_id: str | None = None
    environment_runtime_revision_id: str | None = None
    heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S
    refresh_interval_s: float = DEFAULT_REFRESH_INTERVAL_S
    request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S
    ensure_boot_graph: bool = True
    allow_degraded_local_shell: bool = True
    require_live_runtime: bool = False
    once: bool = False
    capabilities: tuple[str, ...] = DEFAULT_CAPABILITIES
    lane_sync_enabled: bool = True
    lane_sync_window_key: str = DEFAULT_LANE_SYNC_WINDOW_KEY
    lane_sync_include_commit_payload: bool = True
    local_service_host_bootstrap_config_path: Path | None = None
    local_service_host_implementation_toml_paths: tuple[Path, ...] = ()
    dev_adapter_specs: tuple[InterfaceHostDevAdapterSpec, ...] = ()
    interface_package_name: str | None = None
    workspace_revision: InterfaceHostWorkspaceRevisionConfig = field(
        default_factory=InterfaceHostWorkspaceRevisionConfig
    )
    source_path: Path | None = None

    @classmethod
    def from_env(cls) -> "InterfaceHostServiceConfig":
        return _build_config(
            file_config=_load_bootstrap_file_config_from_env(),
        )

    @classmethod
    def from_path(cls, path: str | Path) -> "InterfaceHostServiceConfig":
        return _build_config(
            file_config=_load_bootstrap_file_config(path),
        )


@dataclass(frozen=True, slots=True)
class _BootstrapFileConfig:
    source_path: Path
    repository_root: Path | None = None
    state_home: Path | None = None
    namespace: str | None = None
    host_label: str | None = None
    endpoint: str | None = None
    auth_token: str | None = None
    environment_config_id: UUID | None = None
    runtime_manifest_path: Path | None = None
    runtime_artifact_refs: tuple[InterfaceRuntimeArtifactRef, ...] = ()
    local_state_registry_path: Path | None = None
    heartbeat_interval_s: float | None = None
    refresh_interval_s: float | None = None
    request_timeout_s: float | None = None
    ensure_boot_graph: bool | None = None
    allow_degraded_local_shell: bool | None = None
    require_live_runtime: bool | None = None
    once: bool | None = None
    capabilities: tuple[str, ...] | None = None
    lane_sync_enabled: bool | None = None
    lane_sync_window_key: str | None = None
    lane_sync_include_commit_payload: bool | None = None
    local_service_host_bootstrap_config_path: Path | None = None
    local_service_host_implementation_toml_paths: tuple[Path, ...] | None = None
    dev_adapter_specs: tuple[InterfaceHostDevAdapterSpec, ...] | None = None
    interface_package_name: str | None = None
    workspace_revision_materialized_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None
    workspace_revision_interface_package_refs: tuple[
        InterfaceHostInterfacePackageRef, ...
    ] = ()


def _build_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> InterfaceHostServiceConfig:
    repository_root = _resolve_repository_root(file_config=file_config)
    workspace_revision = _resolve_workspace_revision_config(file_config=file_config)
    _validate_workspace_revision_config(workspace_revision=workspace_revision)
    runtime_manifest_resolution = _resolve_runtime_manifest_resolution(
        repository_root=repository_root,
        file_config=file_config,
    )
    return InterfaceHostServiceConfig(
        repository_root=repository_root,
        state_home=_resolve_state_home(file_config=file_config),
        namespace=_resolve_optional_token(
            env_names=(_NAMESPACE_ENV,),
            file_value=file_config.namespace if file_config is not None else None,
        )
        or DEFAULT_NAMESPACE,
        host_label=_resolve_optional_token(
            env_names=(_HOST_LABEL_ENV,),
            file_value=file_config.host_label if file_config is not None else None,
        )
        or DEFAULT_HOST_LABEL,
        endpoint=_resolve_optional_token(
            env_names=(_ENDPOINT_ENV,),
            file_value=file_config.endpoint if file_config is not None else None,
        ),
        auth_token=_resolve_optional_token(
            env_names=(
                _AUTH_TOKEN_ENV,
                _SHARED_AUTH_TOKEN_ENV,
                _SHARED_APT_TOKEN_ENV,
            ),
            file_value=file_config.auth_token if file_config is not None else None,
        ),
        environment_config_id=_resolve_optional_uuid(
            env_names=(
                _ENVIRONMENT_CONFIG_ID_ENV,
                _SHARED_ENVIRONMENT_CONFIG_ID_ENV,
            ),
            file_value=(
                file_config.environment_config_id if file_config is not None else None
            ),
        ),
        runtime_manifest_path=(
            runtime_manifest_resolution.runtime_manifest_path
            if runtime_manifest_resolution is not None
            else None
        ),
        runtime_artifact_refs=(
            runtime_manifest_resolution.runtime_artifact_refs
            if runtime_manifest_resolution is not None
            else ()
        ),
        local_state_registry_path=_resolve_optional_path(
            env_names=(_LOCAL_STATE_REGISTRY_PATH_ENV,),
            file_value=(
                file_config.local_state_registry_path
                if file_config is not None
                else None
            ),
        ),
        runtime_manifest_source_kind=(
            runtime_manifest_resolution.source_kind
            if runtime_manifest_resolution is not None
            else None
        ),
        workspace_deployment_revision_id=(
            runtime_manifest_resolution.workspace_deployment_revision_id
            if runtime_manifest_resolution is not None
            else None
        ),
        environment_runtime_revision_id=(
            runtime_manifest_resolution.environment_runtime_revision_id
            if runtime_manifest_resolution is not None
            else None
        ),
        heartbeat_interval_s=_resolve_float(
            env_name=_HEARTBEAT_INTERVAL_ENV,
            file_value=(
                file_config.heartbeat_interval_s if file_config is not None else None
            ),
            default=DEFAULT_HEARTBEAT_INTERVAL_S,
        ),
        refresh_interval_s=_resolve_float(
            env_name=_REFRESH_INTERVAL_ENV,
            file_value=(
                file_config.refresh_interval_s if file_config is not None else None
            ),
            default=DEFAULT_REFRESH_INTERVAL_S,
        ),
        request_timeout_s=_resolve_float(
            env_name=_REQUEST_TIMEOUT_ENV,
            file_value=(
                file_config.request_timeout_s if file_config is not None else None
            ),
            default=DEFAULT_REQUEST_TIMEOUT_S,
        ),
        ensure_boot_graph=_resolve_bool(
            env_name=_ENSURE_BOOT_GRAPH_ENV,
            file_value=(
                file_config.ensure_boot_graph if file_config is not None else None
            ),
            default=True,
        ),
        allow_degraded_local_shell=_resolve_bool(
            env_name=_ALLOW_DEGRADED_LOCAL_SHELL_ENV,
            file_value=(
                file_config.allow_degraded_local_shell
                if file_config is not None
                else None
            ),
            default=True,
        ),
        require_live_runtime=_resolve_bool(
            env_name=_REQUIRE_LIVE_RUNTIME_ENV,
            file_value=(
                file_config.require_live_runtime if file_config is not None else None
            ),
            default=False,
        ),
        once=_resolve_bool(
            env_name=_ONCE_ENV,
            file_value=file_config.once if file_config is not None else None,
            default=False,
        ),
        capabilities=_resolve_capabilities(
            file_value=file_config.capabilities if file_config is not None else None,
        ),
        lane_sync_enabled=_resolve_bool(
            env_name=_LANE_SYNC_ENABLED_ENV,
            file_value=(
                file_config.lane_sync_enabled if file_config is not None else None
            ),
            default=True,
        ),
        lane_sync_window_key=_resolve_optional_token(
            env_names=(_LANE_SYNC_WINDOW_KEY_ENV,),
            file_value=(
                file_config.lane_sync_window_key if file_config is not None else None
            ),
        )
        or DEFAULT_LANE_SYNC_WINDOW_KEY,
        lane_sync_include_commit_payload=_resolve_bool(
            env_name=_LANE_SYNC_INCLUDE_COMMIT_PAYLOAD_ENV,
            file_value=(
                file_config.lane_sync_include_commit_payload
                if file_config is not None
                else None
            ),
            default=True,
        ),
        local_service_host_bootstrap_config_path=_resolve_optional_path(
            env_names=(_LOCAL_SERVICE_BOOTSTRAP_CONFIG_PATH_ENV,),
            file_value=(
                file_config.local_service_host_bootstrap_config_path
                if file_config is not None
                else None
            ),
        ),
        local_service_host_implementation_toml_paths=(
            _resolve_local_service_host_implementation_toml_paths(
                repository_root=repository_root,
                file_value=(
                    file_config.local_service_host_implementation_toml_paths
                    if file_config is not None
                    else None
                ),
            )
        ),
        dev_adapter_specs=_resolve_dev_adapter_specs(
            file_value=(
                file_config.dev_adapter_specs if file_config is not None else None
            ),
        ),
        interface_package_name=_resolve_optional_token(
            env_names=(_INTERFACE_PACKAGE_NAME_ENV,),
            file_value=(
                file_config.interface_package_name if file_config is not None else None
            ),
        ),
        workspace_revision=workspace_revision,
        source_path=file_config.source_path if file_config is not None else None,
    )


def resolve_state_home() -> Path:
    override = _read_env_path(_STATE_HOME_ENV)
    if override is not None:
        return override
    shared = _read_env_path(_SHARED_STATE_HOME_ENV)
    if shared is not None:
        return shared
    raise RuntimeError(
        "Interface service state home is required. Set "
        f"{_STATE_HOME_ENV} or {_SHARED_STATE_HOME_ENV}, or provide "
        "state_home in the Interface host bootstrap config."
    )


def build_bootstrap_snapshot(
    *,
    repository_root: Path,
    host_label: str = DEFAULT_HOST_LABEL,
    state_home: Path | None = None,
) -> dict[str, object]:
    resolved_root = repository_root.resolve()
    resolved_state_home = state_home.resolve() if state_home is not None else None
    config = InterfaceHostServiceConfig(
        repository_root=resolved_root,
        state_home=resolved_state_home
        or _read_env_path(_STATE_HOME_ENV)
        or _read_env_path(_SHARED_STATE_HOME_ENV)
        or (resolved_root / ".aware" / "interface_service").resolve(),
        host_label=host_label,
    )
    return {
        "host_kind": "interface_service",
        "service_package": "workspaces/aware_network/modules/interface/services/interface",
        "runtime_owner": "workspaces/aware_network/modules/interface/ontology/runtime/python",
        "attachment_owner": "workspaces/aware_network/modules/interface/sdks/interface",
        "transport_owner": "workspaces/aware_network/modules/interface/sdks/interface",
        "status": "bootstrap_only_service",
        "host_label": config.host_label,
        "repository_root": str(config.repository_root),
        "state_home": str(config.state_home),
        "consumer_apps": ["apps/interface_textual"],
    }


def _load_bootstrap_file_config_from_env() -> _BootstrapFileConfig | None:
    config_path = _read_env_path(_CONFIG_PATH_ENV)
    if config_path is None:
        return None
    return _load_bootstrap_file_config(config_path)


def _load_bootstrap_file_config(path: str | Path) -> _BootstrapFileConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists() or not config_path.is_file():
        raise RuntimeError(
            f"Interface host bootstrap config file was not found: {config_path}"
        )
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "Interface host bootstrap config must decode to a TOML table."
        )

    base_dir = config_path.parent
    app_payload = _read_table(payload, key="app")
    local_service_host_payload = _read_table(payload, key="local_service_host")
    dev_adapters_payload = _read_table(payload, key="dev_adapters")
    interface_package_payload = _read_table(payload, key="interface_package")
    workspace_revision_payload = _read_table(payload, key="workspace_revision")
    runtime_artifacts_payload = _read_table(payload, key="runtime_artifacts")
    return _BootstrapFileConfig(
        source_path=config_path,
        repository_root=_read_optional_path_from_table(
            app_payload,
            key="repository_root",
            base_dir=base_dir,
        ),
        state_home=_read_optional_path_from_table(
            app_payload,
            key="state_home",
            base_dir=base_dir,
        ),
        namespace=_read_optional_token_from_table(app_payload, key="namespace"),
        host_label=_read_optional_token_from_table(app_payload, key="host_label"),
        endpoint=_read_optional_token_from_table(app_payload, key="endpoint"),
        auth_token=_read_optional_token_from_table(app_payload, key="auth_token"),
        environment_config_id=_read_optional_uuid_from_table(
            app_payload,
            key="environment_config_id",
        ),
        runtime_manifest_path=_read_optional_path_from_table(
            app_payload,
            key="runtime_manifest_path",
            base_dir=base_dir,
        ),
        runtime_artifact_refs=runtime_artifact_refs_from_payload(
            runtime_artifacts_payload.get("artifact_refs")
        ),
        local_state_registry_path=_read_optional_path_from_table(
            app_payload,
            key="local_state_registry_path",
            base_dir=base_dir,
        ),
        heartbeat_interval_s=_read_optional_float_from_table(
            app_payload,
            key="heartbeat_interval_s",
        ),
        refresh_interval_s=_read_optional_float_from_table(
            app_payload,
            key="refresh_interval_s",
        ),
        request_timeout_s=_read_optional_float_from_table(
            app_payload,
            key="request_timeout_s",
        ),
        ensure_boot_graph=_read_optional_bool_from_table(
            app_payload,
            key="ensure_boot_graph",
        ),
        allow_degraded_local_shell=_read_optional_bool_from_table(
            app_payload,
            key="allow_degraded_local_shell",
        ),
        require_live_runtime=_read_optional_bool_from_table(
            app_payload,
            key="require_live_runtime",
        ),
        once=_read_optional_bool_from_table(app_payload, key="once"),
        capabilities=_read_optional_string_list_from_table(
            app_payload,
            key="capabilities",
        ),
        lane_sync_enabled=_read_optional_bool_from_table(
            app_payload,
            key="lane_sync_enabled",
        ),
        lane_sync_window_key=_read_optional_token_from_table(
            app_payload,
            key="lane_sync_window_key",
        ),
        lane_sync_include_commit_payload=_read_optional_bool_from_table(
            app_payload,
            key="lane_sync_include_commit_payload",
        ),
        local_service_host_implementation_toml_paths=_read_optional_path_list_from_table(
            local_service_host_payload,
            key="implementation_toml_paths",
            base_dir=base_dir,
        ),
        local_service_host_bootstrap_config_path=_read_optional_path_from_table(
            local_service_host_payload,
            key="bootstrap_config_path",
            base_dir=base_dir,
        ),
        dev_adapter_specs=_dev_adapter_specs_from_tokens(
            _read_optional_string_list_from_table(
                dev_adapters_payload,
                key="services",
            )
        ),
        interface_package_name=_read_optional_token_from_table(
            interface_package_payload,
            key="package_name",
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
        workspace_revision_interface_package_refs=_read_interface_package_refs_from_table(
            workspace_revision_payload,
            base_dir=base_dir,
        ),
    )


def _resolve_repository_root(*, file_config: _BootstrapFileConfig | None) -> Path:
    override = _resolve_optional_path(
        env_names=(
            _REPOSITORY_ROOT_ENV,
            _SHARED_REPO_ROOT_ENV,
            _SHARED_REPOSITORY_ROOT_ENV,
        ),
        file_value=None,
    )
    if override is not None:
        return override
    if file_config is not None and file_config.repository_root is not None:
        return file_config.repository_root
    raise RuntimeError(
        "Interface service repository root is required. Set "
        f"{_REPOSITORY_ROOT_ENV}, {_SHARED_REPO_ROOT_ENV}, or "
        f"{_SHARED_REPOSITORY_ROOT_ENV}, or provide repository_root in the "
        "Interface host bootstrap config."
    )


def _resolve_state_home(*, file_config: _BootstrapFileConfig | None) -> Path:
    override = _read_env_path(_STATE_HOME_ENV)
    if override is not None:
        return override
    shared = _read_env_path(_SHARED_STATE_HOME_ENV)
    if shared is not None:
        return shared
    if file_config is not None and file_config.state_home is not None:
        return file_config.state_home
    return resolve_state_home()


def _resolve_capabilities(
    *,
    file_value: tuple[str, ...] | None,
) -> tuple[str, ...]:
    override = _resolve_optional_token(env_names=(_CAPABILITIES_ENV,), file_value=None)
    if override is not None:
        return _split_capabilities(override)
    if file_value is not None and len(file_value) > 0:
        return tuple(file_value)
    return DEFAULT_CAPABILITIES


def _resolve_local_service_host_implementation_toml_paths(
    *,
    repository_root: Path,
    file_value: tuple[Path, ...] | None,
) -> tuple[Path, ...]:
    override = _resolve_optional_token(
        env_names=(_LOCAL_SERVICE_IMPLEMENTATION_TOMLS_ENV,),
        file_value=None,
    )
    if override is not None:
        resolved: list[Path] = []
        for token in override.split(os.pathsep):
            value = token.strip()
            if not value:
                continue
            resolved.append(Path(value).expanduser().resolve())
        return tuple(dict.fromkeys(resolved))
    if file_value is not None:
        return tuple(file_value)

    _ = repository_root
    return ()


def _resolve_dev_adapter_specs(
    *,
    file_value: tuple[InterfaceHostDevAdapterSpec, ...] | None,
) -> tuple[InterfaceHostDevAdapterSpec, ...]:
    override = _resolve_optional_token(
        env_names=(_DEV_ADAPTERS_ENV,),
        file_value=None,
    )
    if override is not None:
        return _dev_adapter_specs_from_tokens(_split_dev_adapter_tokens(override))
    if file_value is not None:
        return tuple(file_value)
    return ()


def _split_dev_adapter_tokens(raw: str) -> tuple[str, ...]:
    return tuple(
        token.strip() for token in raw.replace(";", ",").split(",") if token.strip()
    )


def _dev_adapter_specs_from_tokens(
    tokens: tuple[str, ...] | None,
) -> tuple[InterfaceHostDevAdapterSpec, ...]:
    if not tokens:
        return ()
    specs: list[InterfaceHostDevAdapterSpec] = []
    for token in tokens:
        service_key, separator, adapter_key = token.partition("=")
        if not separator:
            raise RuntimeError(
                "Interface host dev adapter entries must use service=adapter "
                f"syntax; got {token!r}."
            )
        normalized_service = service_key.strip().casefold()
        normalized_adapter = adapter_key.strip().casefold()
        if not normalized_service or not normalized_adapter:
            raise RuntimeError(
                "Interface host dev adapter entries require non-empty service "
                f"and adapter keys; got {token!r}."
            )
        specs.append(
            InterfaceHostDevAdapterSpec(
                service_key=normalized_service,
                adapter_key=normalized_adapter,
            )
        )
    return tuple(specs)


def _resolve_workspace_revision_config(
    *,
    file_config: _BootstrapFileConfig | None,
) -> InterfaceHostWorkspaceRevisionConfig:
    materialized_workspace_root = _resolve_optional_path(
        env_names=(_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV,),
        file_value=(
            file_config.workspace_revision_materialized_root
            if file_config is not None
            else None
        ),
    )
    manifest_path = _resolve_optional_path(
        env_names=(_WORKSPACE_REVISION_MANIFEST_PATH_ENV,),
        file_value=(
            file_config.workspace_revision_manifest_path
            if file_config is not None
            else None
        ),
    )
    interface_package_refs = (
        file_config.workspace_revision_interface_package_refs
        if file_config is not None
        else ()
    )
    if (
        materialized_workspace_root is None
        and manifest_path is None
        and not interface_package_refs
    ):
        return InterfaceHostWorkspaceRevisionConfig()
    if materialized_workspace_root is None:
        materialized_workspace_root = _workspace_root_from_revision_manifest_path(
            manifest_path
        )
    if materialized_workspace_root is not None and manifest_path is None:
        manifest_path = _revision_filesystem_manifest_path(materialized_workspace_root)
    return InterfaceHostWorkspaceRevisionConfig(
        materialized_workspace_root=materialized_workspace_root,
        manifest_path=manifest_path,
        interface_package_refs=interface_package_refs,
    )


def _validate_workspace_revision_config(
    *,
    workspace_revision: InterfaceHostWorkspaceRevisionConfig,
) -> None:
    materialized_workspace_root = workspace_revision.materialized_workspace_root
    manifest_path = workspace_revision.manifest_path
    if materialized_workspace_root is None and manifest_path is None:
        if workspace_revision.interface_package_refs:
            raise RuntimeError(
                "Interface host workspace_revision interface_package_refs require "
                "materialized_workspace_root or manifest_path."
            )
        return
    if materialized_workspace_root is None or manifest_path is None:
        raise RuntimeError(
            "Interface host workspace_revision requires both materialized_workspace_root "
            "and manifest_path after normalization."
        )
    expected_manifest_path = _revision_filesystem_manifest_path(
        materialized_workspace_root
    )
    if manifest_path != expected_manifest_path:
        raise RuntimeError(
            "Interface host workspace_revision manifest_path must be the canonical "
            "revision filesystem manifest under materialized_workspace_root: "
            f"expected={expected_manifest_path} actual={manifest_path}"
        )
    if not manifest_path.is_file():
        raise RuntimeError(
            "Interface host workspace_revision manifest_path does not exist: "
            f"{manifest_path}"
        )
    for package_ref in workspace_revision.interface_package_refs:
        package_manifest_path = package_ref.manifest_path
        if package_manifest_path is None:
            continue
        if not _is_relative_to(
            path=package_manifest_path,
            parent=materialized_workspace_root,
        ):
            raise RuntimeError(
                "Interface host workspace_revision requires Interface package "
                "refs to resolve under materialized_workspace_root: "
                f"manifest_path={package_manifest_path} root={materialized_workspace_root}"
            )


def _resolve_runtime_manifest_resolution(
    *,
    repository_root: Path,
    file_config: _BootstrapFileConfig | None,
) -> InterfaceHostRuntimeManifestResolution | None:
    _assert_no_legacy_interface_runtime_inputs(file_config=file_config)

    runtime_artifact_refs = _runtime_artifact_refs_from_env()
    if not runtime_artifact_refs and file_config is not None:
        runtime_artifact_refs = file_config.runtime_artifact_refs
    if runtime_artifact_refs:
        return InterfaceHostRuntimeManifestResolution(
            source_kind="runtime_artifact_refs",
            runtime_artifact_refs=runtime_artifact_refs,
        )

    bootstrap_inputs = _build_runtime_workspace_input_from_env(
        repository_root=repository_root
    )
    if bootstrap_inputs is None:
        return None

    return _resolve_workspace_deployment_runtime_handoff(
        bootstrap_inputs=bootstrap_inputs
    )


def _runtime_artifact_refs_from_env() -> tuple[InterfaceRuntimeArtifactRef, ...]:
    payload = _json_payload_from_env_or_path(
        json_env=_RUNTIME_ARTIFACT_REFS_JSON_ENV,
        path_env=_RUNTIME_ARTIFACT_REFS_PATH_ENV,
        label="Interface host runtime_artifact_refs",
    )
    if payload is None:
        return ()
    return runtime_artifact_refs_from_payload(payload)


def _json_payload_from_env_or_path(
    *,
    json_env: str,
    path_env: str,
    label: str,
) -> object | None:
    raw_json = _clean(os.environ.get(json_env))
    if raw_json:
        return json.loads(raw_json)
    raw_path = _clean(os.environ.get(path_env))
    if not raw_path:
        return None
    path = Path(raw_path).expanduser().resolve()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise RuntimeError(f"{label} file is unreadable: {path}") from exc


def _build_runtime_workspace_input_from_env(
    *,
    repository_root: Path,
) -> InterfaceRuntimeManifestBootstrapInputs | None:
    bootstrap_inputs = InterfaceRuntimeManifestBootstrapInputs(
        workspace_root=repository_root.as_posix(),
        workspace_deployment_authority_base_url=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL_ENV)
        )
        or None,
        workspace_deployment_index_url=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_INDEX_URL_ENV)
        )
        or None,
        workspace_deployment_channel=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_CHANNEL_ENV)
        )
        or None,
        workspace_deployment_artifact_key=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV)
        )
        or None,
        workspace_deployment_target_root=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_TARGET_ROOT_ENV)
        )
        or None,
        workspace_deployment_receipt_path=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_RECEIPT_PATH_ENV)
        )
        or None,
        workspace_deployment_revision_id=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV)
        )
        or None,
        workspace_deployment_payload_path=_clean(
            os.environ.get(_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH_ENV)
        )
        or None,
    )
    if not any(
        _clean(getattr(bootstrap_inputs, field.name))
        for field in fields(bootstrap_inputs)
        if field.name.startswith("workspace_deployment_")
    ):
        return None
    return bootstrap_inputs


def _resolve_workspace_deployment_runtime_handoff(
    *,
    bootstrap_inputs: InterfaceRuntimeManifestBootstrapInputs,
) -> InterfaceHostRuntimeManifestResolution:
    configured_payload_path = _clean(bootstrap_inputs.workspace_deployment_payload_path)
    if not configured_payload_path:
        raise RuntimeError(_workspace_deployment_handoff_error())

    payload_path = _resolve_workspace_path(
        configured_payload_path,
        workspace_root=_resolve_workspace_root(bootstrap_inputs.workspace_root),
    )
    if not payload_path.is_file():
        raise FileNotFoundError(
            "Interface host bootstrap workspace-deployment payload does not exist: "
            f"{payload_path}"
        )

    payload = _load_workspace_deployment_payload(path=payload_path)
    nested_environment_runtime = _select_nested_environment_runtime_input(
        payload=payload
    )
    if nested_environment_runtime is None:
        raise RuntimeError(
            "Interface host bootstrap workspace-deployment payload does not carry "
            "a resolved environment runtime handoff with ontology runtime "
            "artifact-set refs. Provide an upstream payload with one environment "
            "runtime input and ontology-owned runtime artifact refs."
        )
    runtime_artifact_refs = _resolve_nested_ontology_runtime_artifact_refs(
        nested_environment_runtime=nested_environment_runtime,
        payload=payload,
    )
    if not runtime_artifact_refs:
        raise RuntimeError(
            "Interface host bootstrap workspace-deployment payload did not expose "
            "ontology runtime artifact-set refs for the environment runtime "
            "handoff."
        )

    return InterfaceHostRuntimeManifestResolution(
        source_kind="workspace_deployment_payload",
        runtime_artifact_refs=runtime_artifact_refs,
        workspace_deployment_revision_id=(
            _mapping_text(payload, "revision_id")
            or _clean(bootstrap_inputs.workspace_deployment_revision_id)
            or None
        ),
        environment_runtime_revision_id=(
            _mapping_text(nested_environment_runtime, "revision_id")
            or _clean(bootstrap_inputs.environment_runtime_revision_id)
            or None
        ),
    )


def _workspace_deployment_handoff_error() -> str:
    return (
        "Interface host bootstrap no longer materializes or fetches "
        "WorkspaceDeployment runtime inputs. Provide "
        f"{_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH_ENV} pointing at an upstream "
        "materialized deployment payload with ontology runtime artifact-set "
        "refs, or boot through the Interface runtime artifact/provider-route "
        "handoff."
    )


def _load_workspace_deployment_payload(*, path: Path) -> Mapping[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid workspace-deployment payload JSON: {path}"
        ) from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError(
            "Interface host bootstrap workspace-deployment payload must be a JSON object: "
            f"{path}"
        )
    return payload


def _select_nested_environment_runtime_input(
    *,
    payload: Mapping[str, object],
) -> Mapping[str, object] | None:
    runtime_inputs = payload.get("runtime_inputs")
    if runtime_inputs is None:
        return None
    if not _is_sequence_not_text(runtime_inputs):
        raise RuntimeError(
            "Interface host bootstrap workspace-deployment runtime_inputs must be a list."
        )
    matches = [
        item
        for item in runtime_inputs
        if isinstance(item, Mapping)
        and _mapping_text(item, "runtime_kind") == "environment"
        and _has_ontology_runtime_artifact_set_ref(item)
    ]
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(
            "Interface host bootstrap does not support multiple nested "
            "environment runtime artifact-set inputs in one WorkspaceDeployment "
            "payload yet."
        )
    return matches[0]


def _resolve_nested_ontology_runtime_artifact_refs(
    *,
    nested_environment_runtime: Mapping[str, object],
    payload: Mapping[str, object],
) -> tuple[InterfaceRuntimeArtifactRef, ...]:
    _ = payload
    artifact_refs = nested_environment_runtime.get("artifact_refs")
    if artifact_refs is None:
        return ()
    if not _is_sequence_not_text(artifact_refs):
        raise RuntimeError(
            "Interface host bootstrap environment runtime artifact_refs must be a list."
        )
    refs = [
        item
        for item in artifact_refs
        if isinstance(item, Mapping)
        and _mapping_text(item, "artifact_family")
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
        and _mapping_text(item, "artifact_role")
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
    ]
    return runtime_artifact_refs_from_payload(refs)


def _has_ontology_runtime_artifact_set_ref(
    runtime_input: Mapping[str, object],
) -> bool:
    artifact_refs = runtime_input.get("artifact_refs")
    if not _is_sequence_not_text(artifact_refs):
        return False
    return any(
        isinstance(item, Mapping)
        and _mapping_text(item, "artifact_family")
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_FAMILY
        and _mapping_text(item, "artifact_role")
        == ONTOLOGY_RUNTIME_ARTIFACT_SET_ARTIFACT_ROLE
        for item in artifact_refs
    )


def _assert_no_legacy_interface_runtime_inputs(
    *,
    file_config: _BootstrapFileConfig | None,
) -> None:
    configured_env_names = [
        env_name
        for env_name in _LEGACY_INTERFACE_RUNTIME_ENV_NAMES
        if _clean(os.environ.get(env_name))
    ]
    configured_file_fields: list[str] = []
    if file_config is not None and file_config.runtime_manifest_path is not None:
        configured_file_fields.append("bootstrap_file.runtime_manifest_path")

    if not configured_env_names and not configured_file_fields:
        return

    configured = ", ".join((*configured_env_names, *configured_file_fields))
    raise RuntimeError(
        "Interface host bootstrap no longer accepts explicit runtime manifest "
        "or direct legacy runtime startup inputs. Use ontology runtime "
        f"artifact-set refs instead. Configured legacy inputs: {configured}"
    )


def _resolve_workspace_root(workspace_root: str) -> Path:
    cleaned = _clean(workspace_root)
    if not cleaned:
        return Path.cwd().resolve()
    return Path(cleaned).expanduser().resolve()


def _resolve_workspace_path(path: str, *, workspace_root: Path) -> Path:
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = (workspace_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _mapping_text(payload: Mapping[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_sequence_not_text(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _read_interface_package_refs_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> tuple[InterfaceHostInterfacePackageRef, ...]:
    raw = payload.get("interface_package_refs")
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError(
            "Interface host bootstrap config field "
            "'workspace_revision.interface_package_refs' must be an array "
            "of package reference tables."
        )
    refs: list[InterfaceHostInterfacePackageRef] = []
    for item in raw:
        if not isinstance(item, dict):
            raise RuntimeError(
                "Interface host bootstrap config field "
                "'workspace_revision.interface_package_refs' must contain TOML tables."
            )
        refs.append(_read_interface_package_ref_from_table(item, base_dir=base_dir))
    return tuple(refs)


def _read_interface_package_ref_from_table(
    payload: dict[str, object],
    *,
    base_dir: Path,
) -> InterfaceHostInterfacePackageRef:
    return InterfaceHostInterfacePackageRef(
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
            f"Interface host bootstrap config field {key!r} must be a non-empty string."
        )
    return token


def _read_table(payload: dict[str, object], *, key: str) -> dict[str, object]:
    raw = payload.get(key)
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise RuntimeError(
            f"Interface host bootstrap config table {key!r} must be a TOML table."
        )
    return raw


def _read_optional_token_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> str | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be a non-empty string."
        )
    return raw.strip()


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
            f"Interface host bootstrap config field {key!r} must be a non-empty string path."
        )
    return _normalize_path_token(raw, base_dir=base_dir)


def _read_optional_path_list_from_table(
    payload: dict[str, object],
    *,
    key: str,
    base_dir: Path,
) -> tuple[Path, ...] | None:
    if key not in payload:
        return None
    raw = payload[key]
    if not isinstance(raw, list):
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be an array of string paths."
        )
    tokens: list[Path] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(
                f"Interface host bootstrap config field {key!r} must contain non-empty string paths."
            )
        tokens.append(_normalize_path_token(item, base_dir=base_dir))
    return tuple(dict.fromkeys(tokens))


def _read_optional_string_list_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> tuple[str, ...] | None:
    if key not in payload:
        return None
    raw = payload[key]
    if not isinstance(raw, list):
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be an array of strings."
        )
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeError(
                f"Interface host bootstrap config field {key!r} must contain non-empty strings."
            )
        values.append(item.strip())
    return tuple(values)


def _read_optional_uuid_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> UUID | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw.strip():
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be a UUID string."
        )
    try:
        return UUID(raw.strip())
    except ValueError as exc:
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be a valid UUID."
        ) from exc


def _read_optional_float_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> float | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, (int, float)):
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be numeric."
        )
    return float(raw)


def _read_optional_bool_from_table(
    payload: dict[str, object],
    *,
    key: str,
) -> bool | None:
    raw = payload.get(key)
    if raw is None:
        return None
    if not isinstance(raw, bool):
        raise RuntimeError(
            f"Interface host bootstrap config field {key!r} must be boolean."
        )
    return raw


def _resolve_optional_token(
    *,
    env_names: tuple[str, ...],
    file_value: str | None,
) -> str | None:
    for env_name in env_names:
        value = _normalize_token(os.environ.get(env_name))
        if value is not None:
            return value
    return _normalize_token(file_value)


def _resolve_optional_path(
    *,
    env_names: tuple[str, ...],
    file_value: Path | None,
) -> Path | None:
    for env_name in env_names:
        value = _read_env_path(env_name)
        if value is not None:
            return value
    return file_value


def _resolve_optional_uuid(
    *,
    env_names: tuple[str, ...],
    file_value: UUID | None,
) -> UUID | None:
    for env_name in env_names:
        raw = _normalize_token(os.environ.get(env_name))
        if raw is None:
            continue
        try:
            return UUID(raw)
        except ValueError:
            continue
    return file_value


def _resolve_float(
    *,
    env_name: str,
    file_value: float | None,
    default: float,
) -> float:
    raw = _normalize_token(os.environ.get(env_name))
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            return default
    if file_value is not None:
        return file_value
    return default


def _resolve_bool(
    *,
    env_name: str,
    file_value: bool | None,
    default: bool,
) -> bool:
    raw = _normalize_token(os.environ.get(env_name))
    if raw is not None:
        return raw.lower() in {"1", "true", "yes", "on"}
    if file_value is not None:
        return file_value
    return default


def _read_env_path(name: str) -> Path | None:
    raw = _normalize_token(os.environ.get(name))
    if raw is None:
        return None
    return Path(raw).expanduser().resolve()


def _normalize_path_token(raw: str, *, base_dir: Path) -> Path:
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()
    else:
        candidate = candidate.resolve()
    return candidate


def _normalize_token(raw: str | None) -> str | None:
    value = (raw or "").strip()
    return value or None


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
            "Interface host workspace_revision manifest_path must end with "
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


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _split_capabilities(raw: str) -> tuple[str, ...]:
    values = tuple(token.strip() for token in raw.split(",") if token.strip())
    return values or DEFAULT_CAPABILITIES


__all__ = [
    "DEFAULT_CAPABILITIES",
    "DEFAULT_HEARTBEAT_INTERVAL_S",
    "DEFAULT_HOST_LABEL",
    "DEFAULT_LANE_SYNC_WINDOW_KEY",
    "DEFAULT_NAMESPACE",
    "DEFAULT_REFRESH_INTERVAL_S",
    "InterfaceHostInterfacePackageRef",
    "InterfaceHostServiceConfig",
    "InterfaceHostWorkspaceRevisionConfig",
    "build_bootstrap_snapshot",
    "resolve_state_home",
]
