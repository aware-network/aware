from __future__ import annotations

from collections.abc import MutableMapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shlex
from typing import Any

from aware_node_service_dto.node.host import NodeRunManifest
from aware_node_service_dto.node.host import NodeRunManifestAuthInputs
from aware_node_service_dto.node.host import NodeRunManifestHostedInterfaceSpec
from aware_node_service_dto.node.host import NodeRunManifestHostedServiceSpec
from aware_node_service_dto.node.host import NodeRunManifestProvenance
from aware_node_service_dto.node.host import NodeRunManifestReadinessPolicy
from aware_node_service_dto.node.host import NodeRunManifestRouteInputs


NODE_RUN_MANIFEST_VERSION = "aware.node.run_manifest.v1"
NODE_RUN_MANIFEST_PATH_ENV = "AWARE_NODE_RUN_MANIFEST_PATH"
NODE_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED_ENV = (
    "AWARE_NODE_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED"
)

_DEFAULT_NODE_WEBSOCKET_PATH = "/interface/network_node"


@dataclass(frozen=True, slots=True)
class NodeHostRuntimePlan:
    manifest_path: Path
    manifest: NodeRunManifest
    env: dict[str, str]
    run_dir: Path
    aware_root: Path | None = None
    node_host_root: Path | None = None
    environment_manifest_path: Path | None = None
    hosted_service_bootstrap_config_paths: tuple[Path, ...] = ()
    interface_host_bootstrap_config_paths: tuple[Path, ...] = ()
    materialized_workspace_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None


def load_node_run_manifest(path: str | Path) -> NodeRunManifest:
    manifest_path = Path(path).expanduser().resolve()
    payload = _load_json_object(path=manifest_path)
    manifest = NodeRunManifest.model_validate(payload)
    if manifest.version != NODE_RUN_MANIFEST_VERSION:
        raise ValueError(
            "Unsupported NodeRunManifest version "
            f"{manifest.version!r}; expected {NODE_RUN_MANIFEST_VERSION!r}."
        )
    return manifest


def build_node_host_runtime_plan(path: str | Path) -> NodeHostRuntimePlan:
    manifest_path = Path(path).expanduser().resolve()
    manifest = load_node_run_manifest(manifest_path)
    base_dir = manifest_path.parent
    run_dir = _resolve_required_path(
        manifest.run_dir,
        base_dir=base_dir,
        field_name="run_dir",
    )
    aware_root = _resolve_optional_path(
        manifest.aware_root,
        base_dir=base_dir,
        field_name="aware_root",
    )
    node_host_root = _resolve_optional_path(
        manifest.node_host_root,
        base_dir=base_dir,
        field_name="node_host_root",
    )
    environment_manifest_path = _resolve_optional_path(
        manifest.environment_manifest_path,
        base_dir=base_dir,
        field_name="environment_manifest_path",
    )
    hosted_service_bootstrap_config_paths = tuple(
        _resolve_required_path(
            service.bootstrap_config_path,
            base_dir=base_dir,
            field_name="hosted_services.bootstrap_config_path",
        )
        for service in manifest.hosted_services
    )
    interface_host_bootstrap_config_paths = tuple(
        _resolve_required_path(
            interface.bootstrap_config_path,
            base_dir=base_dir,
            field_name="hosted_interfaces.bootstrap_config_path",
        )
        for interface in manifest.hosted_interfaces
    )
    materialized_workspace_root = _resolve_optional_path(
        (
            manifest.provenance.materialized_workspace_root
            if manifest.provenance
            else None
        ),
        base_dir=base_dir,
        field_name="provenance.materialized_workspace_root",
    )
    workspace_revision_manifest_path = _resolve_optional_path(
        (
            manifest.provenance.workspace_revision_manifest_path
            if manifest.provenance
            else None
        ),
        base_dir=base_dir,
        field_name="provenance.workspace_revision_manifest_path",
    )
    service_bootstrap_paths = hosted_service_bootstrap_config_paths
    interface_bootstrap_paths = interface_host_bootstrap_config_paths
    env = _render_env(
        manifest=manifest,
        manifest_path=manifest_path,
        base_dir=base_dir,
        run_dir=run_dir,
        aware_root=aware_root,
        node_host_root=node_host_root,
        environment_manifest_path=environment_manifest_path,
        hosted_service_bootstrap_config_paths=service_bootstrap_paths,
        interface_host_bootstrap_config_paths=interface_bootstrap_paths,
        materialized_workspace_root=materialized_workspace_root,
        workspace_revision_manifest_path=workspace_revision_manifest_path,
    )
    return NodeHostRuntimePlan(
        manifest_path=manifest_path,
        manifest=manifest,
        env=env,
        run_dir=run_dir,
        aware_root=aware_root,
        node_host_root=node_host_root,
        environment_manifest_path=environment_manifest_path,
        hosted_service_bootstrap_config_paths=service_bootstrap_paths,
        interface_host_bootstrap_config_paths=interface_bootstrap_paths,
        materialized_workspace_root=materialized_workspace_root,
        workspace_revision_manifest_path=workspace_revision_manifest_path,
    )


def apply_node_run_manifest_env(
    path: str | Path,
    *,
    environ: MutableMapping[str, str] | None = None,
) -> NodeHostRuntimePlan:
    plan = build_node_host_runtime_plan(path)
    target_env = environ if environ is not None else os.environ
    target_env.update(plan.env)
    return plan


def _render_env(
    *,
    manifest: NodeRunManifest,
    manifest_path: Path,
    base_dir: Path,
    run_dir: Path,
    aware_root: Path | None,
    node_host_root: Path | None,
    environment_manifest_path: Path | None,
    hosted_service_bootstrap_config_paths: tuple[Path, ...],
    interface_host_bootstrap_config_paths: tuple[Path, ...],
    materialized_workspace_root: Path | None,
    workspace_revision_manifest_path: Path | None,
) -> dict[str, str]:
    env: dict[str, str] = {
        NODE_RUN_MANIFEST_PATH_ENV: manifest_path.as_posix(),
        "AWARE_NODE_HOST": manifest.host,
        "AWARE_NODE_PORT": str(manifest.port),
        "AWARE_NODE_BASE_URL": manifest.node_base_url
        or f"http://{manifest.host}:{manifest.port}",
        "AWARE_NODE_WS_PATH": (
            manifest.node_websocket_path or _DEFAULT_NODE_WEBSOCKET_PATH
        ),
    }
    _set_path(env, "AWARE_NODE_RUN_DIR", run_dir)
    _set_path(env, "AWARE_ROOT", aware_root)
    _set_path(env, "AWARE_REPO_ROOT", node_host_root)
    _set_path(env, "AWARE_NODE_HOST_ROOT", node_host_root)
    _set_manifest_path(
        env,
        "AWARE_NODE_ENV_FILE",
        manifest.env_file_path,
        base_dir=base_dir,
        field_name="env_file_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_COMMAND_FILE",
        manifest.command_file_path,
        base_dir=base_dir,
        field_name="command_file_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_LOG_FILE",
        manifest.log_path,
        base_dir=base_dir,
        field_name="log_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_PID_FILE",
        manifest.pid_file_path,
        base_dir=base_dir,
        field_name="pid_file_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_STATUS_FILE",
        manifest.status_file_path,
        base_dir=base_dir,
        field_name="status_file_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_PYTHON_PROJECT_PATH",
        manifest.python_project_path,
        base_dir=base_dir,
        field_name="python_project_path",
    )
    _set_path(
        env,
        "AWARE_NODE_PYTHON_EXECUTION_CLOSURE_MANIFEST_PATH",
        _resolve_optional_path(
            manifest.python_execution_closure_manifest_path,
            base_dir=base_dir,
            field_name="python_execution_closure_manifest_path",
        ),
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_DEPLOYMENT_PAYLOAD_PATH",
        manifest.deployment_payload_path,
        base_dir=base_dir,
        field_name="deployment_payload_path",
    )
    _set_text(env, "AWARE_PERSISTENCE_BACKEND", manifest.persistence_backend)
    _set_text(env, "DATABASE_URL", manifest.database_url)
    _set_manifest_path(
        env,
        "AWARE_NODE_REGISTRY_PATH",
        manifest.registry_path,
        base_dir=base_dir,
        field_name="registry_path",
    )
    _set_manifest_path(
        env,
        "AWARE_SECRETS_DIR",
        manifest.secrets_dir,
        base_dir=base_dir,
        field_name="secrets_dir",
    )
    _set_text(
        env,
        "AWARE_NODE_PROVISION_MODE",
        manifest.environment_provision_mode,
    )
    local_environment_config_input_enabled = environment_manifest_path is not None
    env[NODE_LOCAL_ENVIRONMENT_CONFIG_INPUT_ENABLED_ENV] = (
        "1" if local_environment_config_input_enabled else "0"
    )
    env["AWARE_NODE_BOOT_KERNEL"] = (
        "1" if local_environment_config_input_enabled else "0"
    )
    if environment_manifest_path is not None:
        _set_path(
            env,
            "AWARE_NODE_ENVIRONMENT_CONFIG_MANIFESTS",
            environment_manifest_path,
        )
        _set_path(
            env,
            "AWARE_NODE_ENVIRONMENT_CONFIG_ROOT",
            environment_manifest_path.parent,
        )
    _set_manifest_path(
        env,
        "AWARE_RUNTIME_BASE_ENVIRONMENT_MANIFEST",
        manifest.runtime_base_environment_manifest_path,
        base_dir=base_dir,
        field_name="runtime_base_environment_manifest_path",
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_SERVICE_PORT",
        manifest.environment_service_port,
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_API_ENDPOINT",
        manifest.environment_api_endpoint,
    )
    if hosted_service_bootstrap_config_paths:
        env["AWARE_NODE_HOSTED_SERVICE_BOOTSTRAP_CONFIGS"] = os.pathsep.join(
            path.as_posix() for path in hosted_service_bootstrap_config_paths
        )
    if interface_host_bootstrap_config_paths:
        env["AWARE_NODE_HOSTED_INTERFACE_BOOTSTRAP_CONFIGS"] = os.pathsep.join(
            path.as_posix() for path in interface_host_bootstrap_config_paths
        )
        if len(interface_host_bootstrap_config_paths) == 1:
            _set_path(
                env,
                "AWARE_INTERFACE_SERVICE_CONFIG_PATH",
                interface_host_bootstrap_config_paths[0],
            )
    _set_command(
        env,
        "AWARE_NODE_HOSTED_SERVICE_LAUNCH_CMD",
        tuple(service.launch_command for service in manifest.hosted_services),
    )
    _set_command(
        env,
        "AWARE_NODE_HOSTED_INTERFACE_LAUNCH_CMD",
        tuple(interface.launch_command for interface in manifest.hosted_interfaces),
    )
    readiness = manifest.readiness or NodeRunManifestReadinessPolicy()
    _set_readiness_env(env, readiness=readiness)
    _set_service_socket_root(env, manifest=manifest, base_dir=base_dir)
    _set_route_inputs(
        env,
        route_inputs=manifest.route_inputs,
        base_dir=base_dir,
    )
    _set_auth_inputs(env, auth_inputs=manifest.auth_inputs, base_dir=base_dir)
    if materialized_workspace_root is not None:
        _set_path(
            env,
            "AWARE_NODE_WORKSPACE_REVISION_MATERIALIZED_ROOT",
            materialized_workspace_root,
        )
        _set_path(
            env,
            "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_MATERIALIZED_ROOT",
            materialized_workspace_root,
        )
    if workspace_revision_manifest_path is not None:
        _set_path(
            env,
            "AWARE_NODE_WORKSPACE_REVISION_MANIFEST_PATH",
            workspace_revision_manifest_path,
        )
        _set_path(
            env,
            "AWARE_ENVIRONMENT_HOST_WORKSPACE_REVISION_MANIFEST_PATH",
            workspace_revision_manifest_path,
        )
    _set_provenance(env, provenance=manifest.provenance, base_dir=base_dir)
    return dict(sorted(env.items()))


def _set_service_socket_root(
    env: dict[str, str],
    *,
    manifest: NodeRunManifest,
    base_dir: Path,
) -> None:
    socket_roots = tuple(
        _resolve_required_path(
            service.socket_root,
            base_dir=base_dir,
            field_name="hosted_services.socket_root",
        )
        for service in manifest.hosted_services
        if _clean(service.socket_root)
    )
    if not socket_roots:
        return
    if len(set(socket_roots)) != 1:
        raise ValueError(
            "NodeRunManifest hosted_services declare multiple socket_root "
            "values; the current Node host env accepts one "
            "AWARE_NODE_HOSTED_SERVICE_SOCKET_ROOT."
        )
    _set_path(env, "AWARE_NODE_HOSTED_SERVICE_SOCKET_ROOT", socket_roots[0])


def _set_readiness_env(
    env: dict[str, str],
    *,
    readiness: NodeRunManifestReadinessPolicy,
) -> None:
    _set_text(
        env,
        "AWARE_NODE_HOSTED_SERVICE_READY_TIMEOUT_S",
        readiness.hosted_service_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_HOSTED_INTERFACE_READY_TIMEOUT_S",
        readiness.hosted_interface_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_HOSTED_SERVICE_REQUEST_TIMEOUT_S",
        readiness.hosted_service_request_timeout_s,
    )
    _set_text(
        env,
        "AWARE_INTERFACE_SERVICE_REQUEST_TIMEOUT_S",
        readiness.environment_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_PORT_READY_TIMEOUT_S",
        readiness.environment_service_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_READY_TIMEOUT_S",
        readiness.environment_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_ROUTE_CONFIG_TIMEOUT_S",
        readiness.environment_ready_timeout_s,
    )
    _set_text(
        env,
        "AWARE_NODE_REMOTE_SERVICE_API_ROUTE_REFRESH_TIMEOUT_S",
        readiness.environment_ready_timeout_s,
    )


def _set_route_inputs(
    env: dict[str, str],
    *,
    route_inputs: NodeRunManifestRouteInputs | None,
    base_dir: Path,
) -> None:
    if route_inputs is None:
        return
    _set_text_or_file(
        env,
        "AWARE_NODE_SERVICE_API_DEPENDENCY_PACKAGE_REFS_JSON",
        inline_value=route_inputs.service_api_dependency_package_refs_json,
        path_value=route_inputs.service_api_dependency_package_refs_path,
        base_dir=base_dir,
        field_name="route_inputs.service_api_dependency_package_refs_path",
    )
    _set_text_or_file(
        env,
        "AWARE_NODE_REMOTE_SERVICE_API_PROVIDER_REFS_JSON",
        inline_value=route_inputs.remote_service_api_provider_refs_json,
        path_value=route_inputs.remote_service_api_provider_refs_path,
        base_dir=base_dir,
        field_name="route_inputs.remote_service_api_provider_refs_path",
    )


def _set_auth_inputs(
    env: dict[str, str],
    *,
    auth_inputs: NodeRunManifestAuthInputs | None,
    base_dir: Path,
) -> None:
    if auth_inputs is None:
        return
    _set_manifest_path(
        env,
        "AWARE_NODE_TOKEN_AUTHORITY_MANIFEST_PATH",
        auth_inputs.token_authority_manifest_path,
        base_dir=base_dir,
        field_name="auth_inputs.token_authority_manifest_path",
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_TOKEN_SEED_RECEIPT_PATH",
        auth_inputs.token_seed_receipt_path,
        base_dir=base_dir,
        field_name="auth_inputs.token_seed_receipt_path",
    )


def _set_provenance(
    env: dict[str, str],
    *,
    provenance: NodeRunManifestProvenance | None,
    base_dir: Path,
) -> None:
    if provenance is None:
        return
    _set_text(
        env,
        "AWARE_NODE_RUN_MANIFEST_SOURCE_KIND",
        provenance.source_kind,
    )
    _set_manifest_path(
        env,
        "AWARE_WORKSPACE_ROOT",
        provenance.workspace_root,
        base_dir=base_dir,
        field_name="provenance.workspace_root",
    )
    _set_text(
        env,
        "AWARE_NODE_WORKSPACE_REVISION_ID",
        provenance.workspace_revision_id,
    )
    _set_text(
        env,
        "AWARE_NODE_WORKSPACE_SOURCE_REVISION_ID",
        provenance.workspace_source_revision_id,
    )
    _set_text(
        env,
        "AWARE_NODE_WORKSPACE_SOURCE_REVISION_KIND",
        provenance.workspace_source_revision_kind,
    )
    _set_text(
        env,
        "AWARE_NODE_WORKSPACE_DEPLOYMENT_REVISION_ID",
        provenance.workspace_deployment_revision_id,
    )
    _set_text(
        env,
        "AWARE_NODE_ENVIRONMENT_RUNTIME_REVISION_ID",
        provenance.environment_runtime_revision_id,
    )
    _set_manifest_path(
        env,
        "AWARE_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH",
        provenance.deployment_payload_path,
        base_dir=base_dir,
        field_name="provenance.deployment_payload_path",
    )
    _set_text(
        env,
        "AWARE_NODE_RUN_MANIFEST_ARTIFACT_REFS_JSON",
        provenance.artifact_refs_json,
    )
    _set_text(
        env,
        "AWARE_ENVIRONMENT_HOST_RUNTIME_ARTIFACT_REFS_JSON",
        provenance.artifact_refs_json,
    )


def _set_command(
    env: dict[str, str],
    env_name: str,
    commands: tuple[list[str], ...],
) -> None:
    normalized = tuple(
        tuple(_clean(part) for part in command if _clean(part)) for command in commands
    )
    non_empty = tuple(command for command in normalized if command)
    if not non_empty:
        return
    if len(set(non_empty)) != 1:
        raise ValueError(
            f"NodeRunManifest cannot render {env_name}: multiple launch "
            "commands declared."
        )
    env[env_name] = shlex.join(non_empty[0])


def _set_text(env: dict[str, str], name: str, value: object | None) -> None:
    cleaned = _clean(value)
    if cleaned:
        env[name] = cleaned


def _set_manifest_path(
    env: dict[str, str],
    name: str,
    value: str | None,
    *,
    base_dir: Path,
    field_name: str,
) -> None:
    _set_path(
        env,
        name,
        _resolve_optional_path(
            value,
            base_dir=base_dir,
            field_name=field_name,
        ),
    )


def _set_path(env: dict[str, str], name: str, path: Path | None) -> None:
    if path is not None:
        env[name] = path.as_posix()


def _set_text_or_file(
    env: dict[str, str],
    name: str,
    *,
    inline_value: str | None,
    path_value: str | None,
    base_dir: Path,
    field_name: str,
) -> None:
    inline = _clean(inline_value)
    path_text = _clean(path_value)
    if inline and path_text:
        raise ValueError(
            f"NodeRunManifest {field_name} cannot be combined with inline " f"{name}."
        )
    if inline:
        env[name] = inline
        return
    if path_text:
        path = _resolve_required_path(
            path_text,
            base_dir=base_dir,
            field_name=field_name,
        )
        env[name] = path.read_text(encoding="utf-8").strip()


def _resolve_required_path(
    value: str | None,
    *,
    base_dir: Path,
    field_name: str,
) -> Path:
    path = _resolve_optional_path(
        value,
        base_dir=base_dir,
        field_name=field_name,
    )
    if path is None:
        raise ValueError(f"NodeRunManifest field {field_name!r} is required.")
    return path


def _resolve_optional_path(
    value: str | None,
    *,
    base_dir: Path,
    field_name: str,
) -> Path | None:
    cleaned = _clean(value)
    if not cleaned:
        return None
    path = Path(cleaned).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    try:
        return path.resolve()
    except RuntimeError as exc:
        raise ValueError(
            f"NodeRunManifest field {field_name!r} could not be resolved: "
            f"{cleaned!r}"
        ) from exc


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"NodeRunManifest does not exist: {path}") from exc
    if not isinstance(payload, dict):
        raise ValueError("NodeRunManifest payload must be a JSON object.")
    return payload


def _clean(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "NODE_RUN_MANIFEST_PATH_ENV",
    "NODE_RUN_MANIFEST_VERSION",
    "NodeHostRuntimePlan",
    "NodeRunManifest",
    "NodeRunManifestAuthInputs",
    "NodeRunManifestHostedInterfaceSpec",
    "NodeRunManifestHostedServiceSpec",
    "NodeRunManifestProvenance",
    "NodeRunManifestReadinessPolicy",
    "NodeRunManifestRouteInputs",
    "apply_node_run_manifest_env",
    "build_node_host_runtime_plan",
    "load_node_run_manifest",
]
