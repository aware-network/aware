from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import sys

from aware_utils.aware_root import ensure_aware_state_dir, require_aware_root
from aware_utils.logging import logger
from aware_utils.secrets import use_secrets_dir

from aware_node_service.control_plane.environment_registry import environment_registry
from aware_node_service.host.run_manifest import (
    NODE_RUN_MANIFEST_PATH_ENV,
    apply_node_run_manifest_env,
)

_HOSTED_SERVICE_CONFIGS_ENV = "AWARE_NODE_HOSTED_SERVICE_BOOTSTRAP_CONFIGS"
_HOSTED_INTERFACE_CONFIGS_ENV = "AWARE_NODE_HOSTED_INTERFACE_BOOTSTRAP_CONFIGS"
_HOSTED_SERVICE_LAUNCH_CMD_ENV = "AWARE_NODE_HOSTED_SERVICE_LAUNCH_CMD"
_HOSTED_INTERFACE_LAUNCH_CMD_ENV = "AWARE_NODE_HOSTED_INTERFACE_LAUNCH_CMD"
_HOSTED_SERVICE_READY_TIMEOUT_ENV = "AWARE_NODE_HOSTED_SERVICE_READY_TIMEOUT_S"
_HOSTED_INTERFACE_READY_TIMEOUT_ENV = "AWARE_NODE_HOSTED_INTERFACE_READY_TIMEOUT_S"
_HOSTED_SERVICE_REQUEST_TIMEOUT_ENV = "AWARE_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S"
_DEFAULT_HOSTED_SERVICE_READY_TIMEOUT_S = 180.0
_DEFAULT_HOSTED_INTERFACE_READY_TIMEOUT_S = 180.0
_DEFAULT_HOSTED_SERVICE_REQUEST_TIMEOUT_S = 30.0
_NODE_ENVIRONMENT_CONFIG_MANIFESTS_ENV = "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS"
_ENVIRONMENT_MANIFEST_ENV = "AWARE_ENVIRONMENT_MANIFEST"
_WORKSPACE_ROOT_ENV_NAMES = (
    "AWARE_WORKSPACE_ROOT",
    "AWARE_REPO_ROOT",
)
_NODE_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL"
)
_NODE_WORKSPACE_DEPLOYMENT_INDEX_URL_ENV = "AWARE_NODE_WORKSPACE_DEPLOYMENT_INDEX_URL"
_NODE_WORKSPACE_DEPLOYMENT_CHANNEL_ENV = "AWARE_NODE_WORKSPACE_DEPLOYMENT_CHANNEL"
_NODE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY"
)
_NODE_WORKSPACE_DEPLOYMENT_TARGET_ROOT_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_TARGET_ROOT"
)
_NODE_WORKSPACE_DEPLOYMENT_RECEIPT_PATH_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_RECEIPT_PATH"
)
_NODE_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_REVISION_ID"
)
_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH_ENV = (
    "AWARE_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH"
)
_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV = (
    "AWARE_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT"
)
_NODE_WORKSPACE_REVISION_MANIFEST_PATH_ENV = (
    "AWARE_NODE_WORKSPACE_REVISION_MANIFEST_PATH"
)
_NODE_ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL_ENV = (
    "AWARE_NODE_ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL"
)
_NODE_ENVIRONMENT_RUNTIME_INDEX_URL_ENV = "AWARE_NODE_ENVIRONMENT_RUNTIME_INDEX_URL"
_NODE_ENVIRONMENT_RUNTIME_CHANNEL_ENV = "AWARE_NODE_ENVIRONMENT_RUNTIME_CHANNEL"
_NODE_ENVIRONMENT_RUNTIME_ARTIFACT_KEY_ENV = (
    "AWARE_NODE_ENVIRONMENT_RUNTIME_ARTIFACT_KEY"
)
_NODE_ENVIRONMENT_RUNTIME_TARGET_ROOT_ENV = "AWARE_NODE_ENVIRONMENT_RUNTIME_TARGET_ROOT"
_NODE_ENVIRONMENT_RUNTIME_RECEIPT_PATH_ENV = (
    "AWARE_NODE_ENVIRONMENT_RUNTIME_RECEIPT_PATH"
)
_NODE_ENVIRONMENT_RUNTIME_REVISION_ID_ENV = "AWARE_NODE_ENVIRONMENT_RUNTIME_REVISION_ID"
_LEGACY_NODE_BOOTSTRAP_ENV_NAMES: tuple[str, ...] = (
    _NODE_ENVIRONMENT_CONFIG_MANIFESTS_ENV,
    _ENVIRONMENT_MANIFEST_ENV,
    _NODE_ENVIRONMENT_RUNTIME_AUTHORITY_BASE_URL_ENV,
    _NODE_ENVIRONMENT_RUNTIME_INDEX_URL_ENV,
    _NODE_ENVIRONMENT_RUNTIME_CHANNEL_ENV,
    _NODE_ENVIRONMENT_RUNTIME_ARTIFACT_KEY_ENV,
    _NODE_ENVIRONMENT_RUNTIME_TARGET_ROOT_ENV,
    _NODE_ENVIRONMENT_RUNTIME_RECEIPT_PATH_ENV,
    _NODE_ENVIRONMENT_RUNTIME_REVISION_ID_ENV,
)
_WORKSPACE_DEPLOYMENT_BOOTSTRAP_ENV_NAMES: tuple[str, ...] = (
    _NODE_WORKSPACE_DEPLOYMENT_AUTHORITY_BASE_URL_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_INDEX_URL_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_CHANNEL_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_ARTIFACT_KEY_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_TARGET_ROOT_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_RECEIPT_PATH_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_REVISION_ID_ENV,
    _NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH_ENV,
    _NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT_ENV,
    _NODE_WORKSPACE_REVISION_MANIFEST_PATH_ENV,
)


@dataclass(frozen=True, slots=True)
class NodeHostedServiceSupervisorConfig:
    service_bootstrap_config_paths: tuple[Path, ...] = ()
    launch_command: tuple[str, ...] = (sys.executable, "-m", "aware_service_service")
    ready_timeout_s: float = _DEFAULT_HOSTED_SERVICE_READY_TIMEOUT_S
    request_timeout_s: float = _DEFAULT_HOSTED_SERVICE_REQUEST_TIMEOUT_S

    @property
    def enabled(self) -> bool:
        return bool(self.service_bootstrap_config_paths)

    @classmethod
    def from_env(cls) -> "NodeHostedServiceSupervisorConfig":
        return cls(
            service_bootstrap_config_paths=_resolve_env_path_list(
                _HOSTED_SERVICE_CONFIGS_ENV
            ),
            launch_command=_resolve_service_launch_command_from_env(),
            ready_timeout_s=_resolve_service_ready_timeout_from_env(),
            request_timeout_s=_resolve_service_request_timeout_from_env(),
        )


@dataclass(frozen=True, slots=True)
class NodeHostedInterfaceSupervisorConfig:
    interface_bootstrap_config_paths: tuple[Path, ...] = ()
    launch_command: tuple[str, ...] = (sys.executable, "-m", "aware_interface_service")
    ready_timeout_s: float = _DEFAULT_HOSTED_INTERFACE_READY_TIMEOUT_S

    @property
    def enabled(self) -> bool:
        return bool(self.interface_bootstrap_config_paths)

    @classmethod
    def from_env(cls) -> "NodeHostedInterfaceSupervisorConfig":
        return cls(
            interface_bootstrap_config_paths=_resolve_env_path_list(
                _HOSTED_INTERFACE_CONFIGS_ENV
            ),
            launch_command=_resolve_interface_launch_command_from_env(),
            ready_timeout_s=_resolve_interface_ready_timeout_from_env(),
        )


@dataclass(frozen=True, slots=True)
class NodeBootstrapRuntimeResolution:
    source_kind: str
    workspace_root: Path
    local_environment_config_input_enabled: bool = False
    node_environment_config_manifest_paths: tuple[Path, ...] = ()
    environment_manifest_path: Path | None = None
    hosted_service_bootstrap_config_paths: tuple[Path, ...] = ()
    interface_host_bootstrap_config_paths: tuple[Path, ...] = ()
    workspace_revision_id: str | None = None
    workspace_source_revision_id: str | None = None
    workspace_source_revision_kind: str | None = None
    materialized_workspace_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None
    workspace_deployment_revision_id: str | None = None
    environment_runtime_revision_id: str | None = None


def configure_node_secrets() -> None:
    secrets_dir = (os.environ.get("AWARE_SECRETS_DIR") or "").strip()
    if not secrets_dir:
        return
    use_secrets_dir(secrets_dir)
    logger.info("Secrets dir enabled for node (AWARE_SECRETS_DIR=%s)", secrets_dir)


def configure_node_storage() -> None:
    """Fail-fast checks for node durability and registry persistence."""

    aware_root = require_aware_root(purpose="NETWORK_NODE storage")
    aware_dir = ensure_aware_state_dir(aware_root=aware_root, require_writable=True)

    registry_path_raw = os.environ.get("AWARE_NODE_REGISTRY_PATH")
    if registry_path_raw is not None and registry_path_raw.strip():
        registry_path = Path(registry_path_raw).expanduser().resolve()
    else:
        registry_path = aware_dir / "node" / "environment_registry.json"

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    environment_registry.enable_persistence(path=registry_path, strict=True)
    logger.info("Environment registry persistence enabled (path=%s)", registry_path)


def configure_node_persistence_backend() -> None:
    """Ensure the ORM persistence backend is configured before bootstrap."""

    backend = os.environ.get("AWARE_PERSISTENCE_BACKEND")
    db_url = os.environ.get("DATABASE_URL")

    if backend:
        logger.info("Using persistence backend from environment: %s", backend)
        return

    if db_url:
        os.environ.setdefault("AWARE_PERSISTENCE_BACKEND", "db")
        logger.info(
            "DATABASE_URL detected; defaulting AWARE_PERSISTENCE_BACKEND to 'db' (set explicitly to override)."
        )
        return

    os.environ["AWARE_PERSISTENCE_BACKEND"] = "fs"
    logger.info(
        "No DATABASE_URL provided; defaulting AWARE_PERSISTENCE_BACKEND to 'fs' so node persists state to filesystem."
    )


def configure_node_runtime_inputs(
    *,
    workspace_root: str | Path | None = None,
) -> NodeBootstrapRuntimeResolution | None:
    resolved_workspace_root = _resolve_workspace_root(workspace_root)
    node_run_manifest_path = _clean(os.environ.get(NODE_RUN_MANIFEST_PATH_ENV))
    if node_run_manifest_path:
        plan = apply_node_run_manifest_env(node_run_manifest_path)
        provenance = plan.manifest.provenance
        resolution = NodeBootstrapRuntimeResolution(
            source_kind="node_run_manifest",
            workspace_root=plan.node_host_root or resolved_workspace_root,
            local_environment_config_input_enabled=(
                plan.environment_manifest_path is not None
            ),
            node_environment_config_manifest_paths=(
                (plan.environment_manifest_path,)
                if plan.environment_manifest_path is not None
                else ()
            ),
            environment_manifest_path=plan.environment_manifest_path,
            hosted_service_bootstrap_config_paths=(
                plan.hosted_service_bootstrap_config_paths
            ),
            interface_host_bootstrap_config_paths=(
                plan.interface_host_bootstrap_config_paths
            ),
            workspace_revision_id=(
                _clean(provenance.workspace_revision_id)
                if provenance is not None
                else None
            ),
            workspace_source_revision_id=(
                _clean(provenance.workspace_source_revision_id)
                if provenance is not None
                else None
            ),
            workspace_source_revision_kind=(
                _clean(provenance.workspace_source_revision_kind)
                if provenance is not None
                else None
            ),
            materialized_workspace_root=plan.materialized_workspace_root,
            workspace_revision_manifest_path=plan.workspace_revision_manifest_path,
            workspace_deployment_revision_id=(
                _clean(provenance.workspace_deployment_revision_id)
                if provenance is not None
                else None
            ),
            environment_runtime_revision_id=(
                _clean(provenance.environment_runtime_revision_id)
                if provenance is not None
                else None
            ),
        )
        _log_runtime_input_resolution(resolution=resolution)
        return resolution

    _assert_no_legacy_node_bootstrap_inputs()

    if _has_workspace_deployment_bootstrap_inputs():
        raise RuntimeError(
            "Node host bootstrap no longer consumes workspace-deployment adapter "
            "inputs through retired deploy/release side rails. Distribution must "
            "arrive as a prepared NodeRunManifest or WorkspaceRevision handoff."
        )
    return None


def _resolve_env_path_list(env_name: str) -> tuple[Path, ...]:
    raw = (os.environ.get(env_name) or "").strip()
    if not raw:
        return ()
    paths: list[Path] = []
    for token in raw.split(os.pathsep):
        item = token.strip()
        if not item:
            continue
        path = Path(item).expanduser().resolve()
        if path not in paths:
            paths.append(path)
    return tuple(paths)


def _resolve_launch_command_from_env(
    *,
    env_name: str,
    default: tuple[str, ...],
) -> tuple[str, ...]:
    raw = (os.environ.get(env_name) or "").strip()
    if not raw:
        return default
    command = tuple(part for part in shlex.split(raw) if part.strip())
    if not command:
        raise RuntimeError(f"{env_name} must resolve to a non-empty command.")
    return command


def _resolve_service_launch_command_from_env() -> tuple[str, ...]:
    return _resolve_launch_command_from_env(
        env_name=_HOSTED_SERVICE_LAUNCH_CMD_ENV,
        default=(sys.executable, "-m", "aware_service_service"),
    )


def _resolve_interface_launch_command_from_env() -> tuple[str, ...]:
    return _resolve_launch_command_from_env(
        env_name=_HOSTED_INTERFACE_LAUNCH_CMD_ENV,
        default=(sys.executable, "-m", "aware_interface_service"),
    )


def _resolve_service_ready_timeout_from_env() -> float:
    return _resolve_positive_timeout_from_env(
        env_name=_HOSTED_SERVICE_READY_TIMEOUT_ENV,
        default=_DEFAULT_HOSTED_SERVICE_READY_TIMEOUT_S,
    )


def _resolve_interface_ready_timeout_from_env() -> float:
    return _resolve_positive_timeout_from_env(
        env_name=_HOSTED_INTERFACE_READY_TIMEOUT_ENV,
        default=_DEFAULT_HOSTED_INTERFACE_READY_TIMEOUT_S,
    )


def _resolve_service_request_timeout_from_env() -> float:
    return _resolve_positive_timeout_from_env(
        env_name=_HOSTED_SERVICE_REQUEST_TIMEOUT_ENV,
        default=_DEFAULT_HOSTED_SERVICE_REQUEST_TIMEOUT_S,
    )


def _resolve_positive_timeout_from_env(*, env_name: str, default: float) -> float:
    raw = (os.environ.get(env_name) or "").strip()
    if not raw:
        return default
    timeout_s = float(raw)
    if timeout_s <= 0.0:
        raise RuntimeError(f"{env_name} must be greater than 0.")
    return timeout_s


def _has_workspace_deployment_bootstrap_inputs() -> bool:
    return any(
        _clean(os.environ.get(env_name))
        for env_name in _WORKSPACE_DEPLOYMENT_BOOTSTRAP_ENV_NAMES
    )


def _assert_no_legacy_node_bootstrap_inputs() -> None:
    configured_env_names = [
        env_name
        for env_name in _LEGACY_NODE_BOOTSTRAP_ENV_NAMES
        if _clean(os.environ.get(env_name))
    ]
    if not configured_env_names:
        return
    configured = ", ".join(configured_env_names)
    raise RuntimeError(
        "Node host bootstrap no longer accepts explicit manifest or direct "
        "environment-runtime startup inputs. Use a prepared NodeRunManifest "
        f"or WorkspaceRevision handoff instead. Configured legacy envs: {configured}"
    )


def _resolve_workspace_root(workspace_root: str | Path | None) -> Path:
    if workspace_root is not None and str(workspace_root).strip():
        return Path(workspace_root).expanduser().resolve()
    for env_name in _WORKSPACE_ROOT_ENV_NAMES:
        cleaned = _clean(os.environ.get(env_name))
        if cleaned:
            return Path(cleaned).expanduser().resolve()
    return Path.cwd().resolve()


def _log_runtime_input_resolution(
    *,
    resolution: NodeBootstrapRuntimeResolution,
) -> None:
    logger.info(
        (
            "Node runtime inputs resolved (source=%s manifest=%s services=%s "
            "local_environment_config_input=%s "
            "workspace_revision=%s workspace_source_revision=%s "
            "materialized_workspace_root=%s workspace_revision_manifest=%s "
            "workspace_deployment_revision=%s environment_runtime_revision=%s)"
        ),
        resolution.source_kind,
        (
            resolution.environment_manifest_path.as_posix()
            if resolution.environment_manifest_path is not None
            else None
        ),
        [path.as_posix() for path in resolution.hosted_service_bootstrap_config_paths],
        resolution.local_environment_config_input_enabled,
        resolution.workspace_revision_id,
        resolution.workspace_source_revision_id,
        (
            resolution.materialized_workspace_root.as_posix()
            if resolution.materialized_workspace_root is not None
            else None
        ),
        (
            resolution.workspace_revision_manifest_path.as_posix()
            if resolution.workspace_revision_manifest_path is not None
            else None
        ),
        resolution.workspace_deployment_revision_id,
        resolution.environment_runtime_revision_id,
    )


def _clean(value: str | None) -> str:
    return (value or "").strip()


__all__ = [
    "NodeBootstrapRuntimeResolution",
    "NodeHostedInterfaceSupervisorConfig",
    "NodeHostedServiceSupervisorConfig",
    "configure_node_runtime_inputs",
    "configure_node_persistence_backend",
    "configure_node_secrets",
    "configure_node_storage",
]
