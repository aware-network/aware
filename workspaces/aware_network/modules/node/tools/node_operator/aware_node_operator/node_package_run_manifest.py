from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import importlib
import json
from pathlib import Path
import tempfile
from uuid import UUID

from aware_node_service.host.run_manifest import (
    NODE_RUN_MANIFEST_VERSION,
    apply_node_run_manifest_env,
)
from aware_node_service_dto.node.host import NodeRunManifest
from aware_service_runtime.service_provider_sets import (
    build_ontology_authority_catalog_metadata,
)
from aware_service_runtime.contracts import SERVICE_HOST_PROTOCOL_VERSION
from aware_node_operator import (
    direct_interface_local as direct_local,
)
from aware_node_operator.service_host_refs import (
    ServiceHostImplementationPackageRefInput,
)


DEFAULT_NODE_PACKAGE_LOCAL_HANDLE = "kernel-environment-host"
DEFAULT_NODE_PACKAGE_LOCAL_HOST = "127.0.0.1"
DEFAULT_NODE_PACKAGE_LOCAL_PORT = 8911
DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S = (
    direct_local.DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_REQUEST_TIMEOUT_S
)
DEFAULT_NODE_PACKAGE_SERVICE_TOMLS_BY_TARGET: Mapping[str, str] = {
    "aware_attention": (
        "workspaces/aware_network/modules/attention/services/attention/aware.service.toml"
    ),
    "aware_environment": (
        "workspaces/aware_network/modules/environment/services/environment/aware.service.toml"
    ),
    "aware_experience": (
        "workspaces/aware_network/modules/experience/services/experience/aware.service.toml"
    ),
    "aware_identity": (
        "workspaces/aware_network/modules/identity/services/identity/aware.service.toml"
    ),
    "aware_meta": "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
    "aware_network": (
        "workspaces/aware_network/modules/network/services/network/aware.service.toml"
    ),
    "aware_ontology": (
        "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml"
    ),
    "aware_hub": "workspaces/aware_network/modules/hub/services/hub/aware.service.toml",
    "aware_reactivity": (
        "workspaces/aware_network/modules/reactivity/services/reactivity/aware.service.toml"
    ),
    "aware_workspace": "workspaces/aware_workspace/services/workspace/aware.service.toml",
}
_RUNTIME_PYTHON_COMMAND = "python"
_NODE_SERVICE_ENTRYPOINT = "aware_node_service.app"
_SERVICE_HOST_ENTRYPOINT = "aware_service_service"
_INTERFACE_HOST_ENTRYPOINT = "aware_interface_service"

_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV = "AWARE_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH"
_SOURCE_LOCAL_ONTOLOGY_COMPOSITION_BRIDGE_POLICY = "retired"
_SERVICE_HOST_IPC_TEMP_DIR_NAME = "aware-service-ipc"
_UNIX_SOCKET_SAFE_PATH_LENGTH = 100
_ENVIRONMENT_SERVICE_PACKAGE_NAME = "aware-environment-service"
_ENVIRONMENT_API_PACKAGE_NAME = "environment-service-api"
_ENVIRONMENT_BOOT_COMPANION_ONTOLOGY_PACKAGES = frozenset({"network-ontology"})


@dataclass(frozen=True, slots=True)
class NodePackageEnvironmentProfileMount:
    package_name: str
    profile_key: str
    mount_key: str
    mode: str = "mounted"
    position: int | None = 0


@dataclass(frozen=True, slots=True)
class NodePackageEnvironmentTarget:
    environment_handle: str
    profile_mounts: tuple[NodePackageEnvironmentProfileMount, ...]


@dataclass(frozen=True, slots=True)
class NodePackageServiceTarget:
    service_name: str
    code_packages: tuple["NodePackageServiceCodePackage", ...] = ()


@dataclass(frozen=True, slots=True)
class NodePackageServiceCodePackage:
    slot_key: str
    package_name: str
    language: str = "aware"


@dataclass(frozen=True, slots=True)
class NodePackageOntologyTarget:
    package_name: str


@dataclass(frozen=True, slots=True)
class NodePackageInterfaceTarget:
    interface_name: str


@dataclass(frozen=True, slots=True)
class NodePackageRuntimeSource:
    package_name: str
    config_name: str
    source_kind: str = "node_package"
    node_package_id: UUID | None = None
    node_config_id: UUID | None = None
    source_path: Path | None = None
    environment_targets: tuple[NodePackageEnvironmentTarget, ...] = ()
    ontology_targets: tuple[NodePackageOntologyTarget, ...] = ()
    service_targets: tuple[NodePackageServiceTarget, ...] = ()
    interface_targets: tuple[NodePackageInterfaceTarget, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "package_name": self.package_name,
            "config_name": self.config_name,
            "source_kind": self.source_kind,
            "node_package_id": (
                str(self.node_package_id) if self.node_package_id is not None else None
            ),
            "node_config_id": (
                str(self.node_config_id) if self.node_config_id is not None else None
            ),
            "source_path": (
                self.source_path.as_posix() if self.source_path is not None else None
            ),
            "environment_targets": [
                {
                    "environment_handle": target.environment_handle,
                    "profile_mounts": [
                        {
                            "package_name": mount.package_name,
                            "profile_key": mount.profile_key,
                            "mount_key": mount.mount_key,
                            "mode": mount.mode,
                            "position": mount.position,
                        }
                        for mount in target.profile_mounts
                    ],
                }
                for target in self.environment_targets
            ],
            "service_targets": [
                {
                    "service_name": target.service_name,
                    "code_packages": [
                        {
                            "slot_key": package.slot_key,
                            "package_name": package.package_name,
                            "language": package.language,
                        }
                        for package in target.code_packages
                    ],
                }
                for target in self.service_targets
            ],
            "ontology_targets": [
                {"package_name": target.package_name}
                for target in self.ontology_targets
            ],
            "interface_targets": [
                {"interface_name": target.interface_name}
                for target in self.interface_targets
            ],
        }


@dataclass(frozen=True, slots=True)
class NodePackageRunManifestRequest:
    repo_root: Path
    run_dir: Path
    source: NodePackageRuntimeSource
    workspace_root: Path | None = None
    node_host_root: Path | None = None
    python_project_path: Path | None = None
    python_execution_closure_manifest_path: Path | None = None
    kernel_workspace_revision_root: Path | None = None
    deployment_payload_path: Path | None = None
    materialized_workspace_root: Path | None = None
    workspace_revision_manifest_path: Path | None = None
    runtime_base_environment_manifest_path: Path | None = None
    node_id: UUID | None = None
    workspace_revision_id: str | UUID | None = None
    workspace_source_revision_id: str | None = None
    workspace_source_revision_kind: str | None = None
    workspace_deployment_revision_id: str | None = None
    environment_runtime_revision_id: str | None = None
    host: str = DEFAULT_NODE_PACKAGE_LOCAL_HOST
    port: int = DEFAULT_NODE_PACKAGE_LOCAL_PORT
    service_toml_paths: tuple[Path, ...] = ()
    service_package_refs: tuple[ServiceHostImplementationPackageRefInput, ...] = ()
    allow_default_service_toml_registry: bool = True
    remote_service_api_provider_refs_json: str | None = None
    interface_package_names_by_target: Mapping[str, str] = field(default_factory=dict)
    runtime_manifest_path: Path | None = None
    auth_token: str | None = None
    issue_runtime_auth_token: bool = False
    require_live_runtime: bool = True
    allow_degraded_local_shell: bool = False
    environment_port_ready_timeout_s: float = 420.0
    hosted_service_request_timeout_s: float = (
        DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S
    )


@dataclass(frozen=True, slots=True)
class NodeOntologyLocalBootstrapRequest:
    repo_root: Path
    node_toml_path: Path
    run_dir: Path
    workspace_root: Path | None = None
    host: str = DEFAULT_NODE_PACKAGE_LOCAL_HOST
    port: int = DEFAULT_NODE_PACKAGE_LOCAL_PORT
    service_toml_paths: tuple[Path, ...] = ()
    remote_service_api_provider_refs_json: str | None = None
    interface_package_names_by_target: Mapping[str, str] = field(default_factory=dict)
    runtime_manifest_path: Path | None = None
    auth_token: str | None = None
    issue_runtime_auth_token: bool = False
    require_live_runtime: bool = True
    allow_degraded_local_shell: bool = False
    environment_port_ready_timeout_s: float = 420.0
    hosted_service_request_timeout_s: float = (
        DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S
    )


@dataclass(frozen=True, slots=True)
class NodePackageRunManifestPlan:
    repo_root: Path
    run_dir: Path
    node_package: str
    node_config: str
    source_kind: str
    node_run_manifest_path: Path
    service_host_config_path: Path | None
    interface_host_config_paths: tuple[Path, ...]
    node_env_path: Path
    node_command_path: Path
    node_log_path: Path
    node_operator_pid_path: Path
    node_operator_status_path: Path
    receipt_path: Path
    service_socket_path: Path | None
    interface_control_socket_paths: tuple[Path, ...]
    node_root: Path
    node_endpoint: str
    runtime_manifest_path: Path | None
    node_host: str
    node_port: int
    service_toml_paths: tuple[Path, ...]
    service_package_refs: tuple[ServiceHostImplementationPackageRefInput, ...]
    experience_toml_paths: tuple[Path, ...]
    environment_targets: tuple[NodePackageEnvironmentTarget, ...]
    ontology_targets: tuple[NodePackageOntologyTarget, ...]
    service_targets: tuple[NodePackageServiceTarget, ...]
    interface_targets: tuple[NodePackageInterfaceTarget, ...]
    network_node_id: UUID
    service_api_provider_refs_json: str
    require_live_runtime: bool
    allow_degraded_local_shell: bool
    source_local_ontology_composition_bridge_allowed: bool
    source_local_ontology_composition_bridge_used: bool
    auth_token_present: bool
    auth_token: str | None = field(default=None, repr=False)
    runtime_auth_token_issued: bool = False
    runtime_auth_token_id: UUID | None = None
    runtime_auth_actor_id: UUID | None = None
    runtime_auth_public_key: str | None = None
    runtime_auth_environment_config_id: UUID | None = None
    runtime_auth_environment_id: UUID | None = None
    runtime_auth_process_id: UUID | None = None
    runtime_auth_thread_id: UUID | None = None
    token_authority_manifest_path: Path | None = None
    token_seed_receipt_path: Path | None = None
    auth_token_projection_hash: str | None = None
    node_env: Mapping[str, str] = field(default_factory=dict)
    node_command: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, object]:
        return {
            "version": "aware.node.node_package_run_manifest.v1",
            "repo_root": self.repo_root.as_posix(),
            "run_dir": self.run_dir.as_posix(),
            "node_package": self.node_package,
            "node_config": self.node_config,
            "source_kind": self.source_kind,
            "node_run_manifest_path": self.node_run_manifest_path.as_posix(),
            "service_host_config_path": (
                self.service_host_config_path.as_posix()
                if self.service_host_config_path is not None
                else None
            ),
            "interface_host_config_paths": [
                path.as_posix() for path in self.interface_host_config_paths
            ],
            "node_env_path": self.node_env_path.as_posix(),
            "node_command_path": self.node_command_path.as_posix(),
            "node_log_path": self.node_log_path.as_posix(),
            "node_operator_pid_path": self.node_operator_pid_path.as_posix(),
            "node_operator_status_path": self.node_operator_status_path.as_posix(),
            "receipt_path": self.receipt_path.as_posix(),
            "service_socket_path": (
                self.service_socket_path.as_posix()
                if self.service_socket_path is not None
                else None
            ),
            "interface_control_socket_paths": [
                path.as_posix() for path in self.interface_control_socket_paths
            ],
            "node_root": self.node_root.as_posix(),
            "node_endpoint": self.node_endpoint,
            "runtime_manifest_path": (
                self.runtime_manifest_path.as_posix()
                if self.runtime_manifest_path is not None
                else None
            ),
            "node_host": self.node_host,
            "node_port": self.node_port,
            "service_toml_paths": [path.as_posix() for path in self.service_toml_paths],
            "service_package_refs": [
                ref.to_payload() for ref in self.service_package_refs
            ],
            "experience_toml_paths": [
                path.as_posix() for path in self.experience_toml_paths
            ],
            "environment_targets": [
                target.environment_handle for target in self.environment_targets
            ],
            "service_targets": [target.service_name for target in self.service_targets],
            "service_code_packages": [
                {
                    "service_name": target.service_name,
                    "slot_key": package.slot_key,
                    "package_name": package.package_name,
                    "language": package.language,
                }
                for target in self.service_targets
                for package in target.code_packages
            ],
            "ontology_targets": [
                target.package_name for target in self.ontology_targets
            ],
            "interface_targets": [
                target.interface_name for target in self.interface_targets
            ],
            "network_node_id": str(self.network_node_id),
            "service_api_provider_refs_json": self.service_api_provider_refs_json,
            "require_live_runtime": self.require_live_runtime,
            "allow_degraded_local_shell": self.allow_degraded_local_shell,
            "source_local_ontology_composition_bridge": {
                "allowed": self.source_local_ontology_composition_bridge_allowed,
                "used": self.source_local_ontology_composition_bridge_used,
                "policy": _SOURCE_LOCAL_ONTOLOGY_COMPOSITION_BRIDGE_POLICY,
            },
            "auth_token_present": self.auth_token_present,
            "runtime_auth_token_issued": self.runtime_auth_token_issued,
            "runtime_auth_token_id": (
                str(self.runtime_auth_token_id)
                if self.runtime_auth_token_id is not None
                else None
            ),
            "runtime_auth_actor_id": (
                str(self.runtime_auth_actor_id)
                if self.runtime_auth_actor_id is not None
                else None
            ),
            "runtime_auth_public_key": self.runtime_auth_public_key,
            "runtime_auth_environment_config_id": (
                str(self.runtime_auth_environment_config_id)
                if self.runtime_auth_environment_config_id is not None
                else None
            ),
            "runtime_auth_environment_id": (
                str(self.runtime_auth_environment_id)
                if self.runtime_auth_environment_id is not None
                else None
            ),
            "runtime_auth_process_id": (
                str(self.runtime_auth_process_id)
                if self.runtime_auth_process_id is not None
                else None
            ),
            "runtime_auth_thread_id": (
                str(self.runtime_auth_thread_id)
                if self.runtime_auth_thread_id is not None
                else None
            ),
            "token_authority_manifest_path": (
                self.token_authority_manifest_path.as_posix()
                if self.token_authority_manifest_path is not None
                else None
            ),
            "token_seed_receipt_path": (
                self.token_seed_receipt_path.as_posix()
                if self.token_seed_receipt_path is not None
                else None
            ),
            "auth_token_projection_hash": self.auth_token_projection_hash,
            "node_env": direct_local._redacted_env(self.node_env),
            "node_command": list(self.node_command),
            "workspace_revision_deployment_payload_env_present": (
                _NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV in self.node_env
            ),
        }


def node_package_runtime_source_from_node_package(
    *,
    node_package: object,
    node_config: object | None = None,
    source_kind: str = "node_package",
    source_path: Path | None = None,
) -> NodePackageRuntimeSource:
    resolved_node_config = node_config or getattr(node_package, "node_config", None)
    if resolved_node_config is None:
        raise ValueError("NodePackage run manifest lowering requires NodeConfig truth.")
    return NodePackageRuntimeSource(
        package_name=_required_attr_text(node_package, "name"),
        config_name=_required_attr_text(resolved_node_config, "name"),
        source_kind=source_kind,
        node_package_id=_optional_uuid_attr(node_package, "id"),
        node_config_id=_optional_uuid_attr(resolved_node_config, "id"),
        source_path=source_path,
        environment_targets=_environment_targets_from_node_config(resolved_node_config),
        ontology_targets=_ontology_targets_from_node_config(resolved_node_config),
        service_targets=_service_targets_from_node_config(resolved_node_config),
        interface_targets=_interface_targets_from_node_config(resolved_node_config),
    )


def node_package_runtime_source_from_workspace_deployment_payload(
    payload: object,
    *,
    source_kind: str = "workspace_revision",
) -> NodePackageRuntimeSource:
    """Build Node runtime source from a fetched WorkspaceDeployment payload.

    WorkspaceDeployment payloads are produced from committed NodePackage /
    NodeConfig truth during publication. This adapter intentionally consumes
    only that fetched payload shape and does not read local `aware.node.toml`.
    """

    node_selection = _payload_required_value(payload, "node_selection")
    package_selection = _payload_required_value(node_selection, "package_selection")
    package_name = _payload_required_text(package_selection, "package_name")
    config_name = (
        _payload_optional_text(node_selection, "target_ref")
        or _payload_optional_text(node_selection, "selector_key")
        or package_name
    )
    runtime_inputs = tuple(_payload_sequence(payload, "runtime_inputs"))
    environment_targets: list[NodePackageEnvironmentTarget] = []
    service_targets: list[NodePackageServiceTarget] = []
    ontology_targets: list[NodePackageOntologyTarget] = []
    interface_targets: list[NodePackageInterfaceTarget] = []
    for runtime_input in runtime_inputs:
        runtime_kind = _payload_required_text(runtime_input, "runtime_kind").casefold()
        package_ref = _payload_optional_value(runtime_input, "package_selection")
        target_name = _payload_optional_text(runtime_input, "target_name") or (
            _payload_optional_text(package_ref, "package_name")
            if package_ref is not None
            else None
        )
        if runtime_kind == "environment":
            environment_handle = (
                _payload_optional_text(runtime_input, "environment_handle")
                or target_name
            )
            profile_key = _payload_required_text(runtime_input, "profile_key")
            profile_ref = _payload_required_value(
                runtime_input, "environment_profile_package_selection"
            )
            profile_package_name = _payload_required_text(profile_ref, "package_name")
            environment_targets.append(
                NodePackageEnvironmentTarget(
                    environment_handle=_required_text(
                        environment_handle, "environment_handle"
                    ),
                    profile_mounts=(
                        NodePackageEnvironmentProfileMount(
                            package_name=profile_package_name,
                            profile_key=profile_key,
                            mount_key=f"{profile_package_name}:{profile_key}",
                        ),
                    ),
                )
            )
            continue
        if runtime_kind == "service":
            code_packages = tuple(
                NodePackageServiceCodePackage(
                    slot_key=_payload_required_text(package, "slot_key"),
                    package_name=_payload_required_text(package, "package_name"),
                    language=_payload_optional_text(package, "language") or "aware",
                )
                for package in _payload_sequence(runtime_input, "code_packages")
            )
            service_targets.append(
                NodePackageServiceTarget(
                    service_name=_required_text(target_name, "service target_name"),
                    code_packages=code_packages,
                )
            )
            continue
        if runtime_kind == "ontology":
            ontology_targets.append(
                NodePackageOntologyTarget(
                    package_name=_required_text(target_name, "ontology target_name")
                )
            )
            continue
        if runtime_kind == "interface":
            interface_targets.append(
                NodePackageInterfaceTarget(
                    interface_name=_required_text(target_name, "interface target_name")
                )
            )
            continue
    return NodePackageRuntimeSource(
        package_name=package_name,
        config_name=config_name,
        source_kind=source_kind,
        node_package_id=_optional_uuid_value(
            _payload_optional_value(package_selection, "semantic_package_id")
            or _payload_optional_value(package_selection, "semantic_root_id")
        ),
        node_config_id=_optional_uuid_value(
            _payload_optional_value(node_selection, "node_config_id")
        ),
        environment_targets=tuple(environment_targets),
        ontology_targets=tuple(ontology_targets),
        service_targets=tuple(service_targets),
        interface_targets=tuple(interface_targets),
    )


def node_package_runtime_source_from_materialization_spec(
    spec: object,
    *,
    source_kind: str = "node_ontology_manifest",
) -> NodePackageRuntimeSource:
    return NodePackageRuntimeSource(
        package_name=_required_attr_text(spec, "package_name"),
        config_name=_required_attr_text(spec, "config_name"),
        source_kind=source_kind,
        source_path=getattr(spec, "node_toml_path", None),
        environment_targets=_environment_targets_from_ownership(
            getattr(spec, "environment_targets", ())
        ),
        ontology_targets=tuple(
            NodePackageOntologyTarget(
                package_name=_required_text(str(item), "package_name")
            )
            for item in getattr(spec, "ontology_package_names", ())
        ),
        service_targets=_service_targets_from_materialization_spec(spec),
        interface_targets=(
            tuple(
                NodePackageInterfaceTarget(
                    interface_name=_required_text(
                        getattr(item, "interface_name", ""), "interface_name"
                    )
                )
                for item in getattr(spec, "interface_targets", ())
            )
            if not _sequence_items_are_text(getattr(spec, "interface_names", ()))
            else tuple(
                NodePackageInterfaceTarget(
                    interface_name=_required_text(str(item), "interface_name")
                )
                for item in getattr(spec, "interface_names", ())
            )
        ),
    )


def prepare_node_ontology_local_bootstrap(
    request: NodeOntologyLocalBootstrapRequest,
) -> NodePackageRunManifestPlan:
    from aware_node.materialization import resolve_node_package_materialization_spec

    repo_root = request.repo_root.expanduser().resolve()
    workspace_root = (
        request.workspace_root.expanduser().resolve()
        if request.workspace_root is not None
        else repo_root
    )
    node_toml_path = request.node_toml_path.expanduser()
    if not node_toml_path.is_absolute():
        node_toml_path = workspace_root / node_toml_path
    spec = resolve_node_package_materialization_spec(
        node_toml_path=node_toml_path.resolve(),
        workspace_root=workspace_root,
    )
    source = node_package_runtime_source_from_materialization_spec(spec)
    return prepare_node_package_run_manifest(
        NodePackageRunManifestRequest(
            repo_root=repo_root,
            workspace_root=workspace_root,
            run_dir=request.run_dir,
            source=source,
            host=request.host,
            port=request.port,
            service_toml_paths=request.service_toml_paths,
            remote_service_api_provider_refs_json=(
                request.remote_service_api_provider_refs_json
            ),
            interface_package_names_by_target=(
                request.interface_package_names_by_target
            ),
            runtime_manifest_path=request.runtime_manifest_path,
            auth_token=request.auth_token,
            issue_runtime_auth_token=request.issue_runtime_auth_token,
            require_live_runtime=request.require_live_runtime,
            allow_degraded_local_shell=request.allow_degraded_local_shell,
            environment_port_ready_timeout_s=(request.environment_port_ready_timeout_s),
            hosted_service_request_timeout_s=(request.hosted_service_request_timeout_s),
        )
    )


def prepare_node_package_run_manifest(
    request: NodePackageRunManifestRequest,
) -> NodePackageRunManifestPlan:
    repo_root = request.repo_root.expanduser().resolve()
    workspace_root = (
        request.workspace_root.expanduser().resolve()
        if request.workspace_root is not None
        else repo_root
    )
    node_host_root = (
        request.node_host_root.expanduser().resolve()
        if request.node_host_root is not None
        else repo_root
    )
    python_project_path = (
        request.python_project_path.expanduser().resolve()
        if request.python_project_path is not None
        else repo_root
    )
    python_execution_closure_manifest_path = (
        request.python_execution_closure_manifest_path.expanduser().resolve()
        if request.python_execution_closure_manifest_path is not None
        else None
    )
    kernel_workspace_revision_root = (
        request.kernel_workspace_revision_root.expanduser().resolve()
        if request.kernel_workspace_revision_root is not None
        else None
    )
    deployment_payload_path = (
        request.deployment_payload_path.expanduser().resolve()
        if request.deployment_payload_path is not None
        else None
    )
    materialized_workspace_root = (
        request.materialized_workspace_root.expanduser().resolve()
        if request.materialized_workspace_root is not None
        else None
    )
    workspace_revision_manifest_path = (
        request.workspace_revision_manifest_path.expanduser().resolve()
        if request.workspace_revision_manifest_path is not None
        else None
    )
    runtime_base_environment_manifest_path = (
        request.runtime_base_environment_manifest_path.expanduser().resolve()
        if request.runtime_base_environment_manifest_path is not None
        else None
    )
    run_dir = request.run_dir.expanduser().resolve()
    source = _validate_runtime_source(request.source)
    host = _required_text(request.host, "host")
    port = int(request.port)
    if port <= 0:
        raise ValueError("port must be greater than 0.")
    hosted_service_request_timeout_s = float(request.hosted_service_request_timeout_s)
    if hosted_service_request_timeout_s <= 0:
        raise ValueError("hosted_service_request_timeout_s must be greater than 0.")

    environment_target = _single_environment_target(source)
    source_local_ontology_package_names = (
        _source_local_ontology_package_names_from_remote_provider_refs(
            request.remote_service_api_provider_refs_json
        )
        if environment_target is not None
        else ()
    )
    runtime_manifest_path = (
        _resolve_runtime_manifest_path(
            repo_root=repo_root,
            source=source,
            environment_target=environment_target,
            runtime_manifest_path=request.runtime_manifest_path,
            source_local_ontology_package_names=source_local_ontology_package_names,
        )
        if environment_target is not None or request.runtime_manifest_path is not None
        else None
    )
    source_local_ontology_composition_bridge_used = False
    runtime_artifact_refs_json = (
        _runtime_artifact_refs_json_for_local_environment_runtime(
            repo_root=repo_root,
            runtime_manifest_path=runtime_manifest_path,
            source=source,
            source_local_ontology_package_names=source_local_ontology_package_names,
        )
        if environment_target is not None and runtime_manifest_path is not None
        else None
    )
    if environment_target is not None and runtime_artifact_refs_json is None:
        raise RuntimeError(
            "Environment NodePackage boot requires ontology-owned runtime "
            "artifact refs. The selected runtime manifest did not resolve to "
            f"an ontology runtime artifact set: {runtime_manifest_path}"
        )
    service_toml_paths = _resolve_service_toml_paths_for_targets(
        repo_root=repo_root,
        service_targets=source.service_targets,
        service_toml_paths=request.service_toml_paths,
        allow_default_registry=request.allow_default_service_toml_registry,
        remote_service_api_provider_refs_json=(
            request.remote_service_api_provider_refs_json
        ),
    )
    service_package_refs = tuple(request.service_package_refs)
    experience_package_names = _experience_package_names_from_service_activations(
        source.service_targets
    )
    experience_toml_paths = (
        direct_local._experience_toml_paths_for_refs(
            repo_root=repo_root,
            experience_refs=experience_package_names,
        )
        if experience_package_names
        else ()
    )

    service_dir = run_dir / "service"
    interface_dir = run_dir / "interface"
    auth_dir = run_dir / "auth"
    env_dir = run_dir / "env"
    commands_dir = run_dir / "commands"
    logs_dir = run_dir / "logs"
    receipts_dir = run_dir / "receipts"
    for directory in (
        service_dir,
        interface_dir,
        auth_dir,
        env_dir,
        commands_dir,
        logs_dir,
        receipts_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    node_root = (run_dir / "node-root").resolve()
    node_root.mkdir(parents=True, exist_ok=True)
    network_node_info = _ensure_local_network_node_info(
        node_root=node_root,
        host=host,
        port=port,
        label=source.package_name,
        node_id=request.node_id,
    )
    resolved_auth_token = (
        str(request.auth_token).strip() if request.auth_token is not None else ""
    ) or None
    runtime_auth_token = None
    if (
        resolved_auth_token is None
        and request.require_live_runtime
        and request.issue_runtime_auth_token
    ):
        if runtime_manifest_path is None:
            raise RuntimeError(
                "NodePackage runtime auth token issuance requires an Environment "
                "runtime manifest; service/ontology-only NodePackage runs must "
                "supply auth_token explicitly or disable issue_runtime_auth_token."
            )
        runtime_auth_commit_store_root = (auth_dir / "runtime-auth-store").resolve()
        runtime_auth_token = direct_local._issue_direct_local_runtime_auth_token(
            repo_root=repo_root,
            runtime_manifest_path=runtime_manifest_path,
            node_id=network_node_info.id,
            commit_store_root_path=runtime_auth_commit_store_root,
        )
        resolved_auth_token = runtime_auth_token.token
    token_authority_inputs = _write_token_authority_inputs(
        repo_root=repo_root,
        auth_dir=auth_dir,
        runtime_manifest_path=runtime_manifest_path,
        auth_token=resolved_auth_token,
        source_kind=source.source_kind,
        commit_store_root_path=(
            runtime_auth_token.commit_store_root_path
            if runtime_auth_token is not None
            else None
        ),
    )

    service_socket_path = None
    service_host_config_path = None
    if service_toml_paths or service_package_refs:
        service_socket_path = _local_service_host_socket_path(
            run_dir=run_dir,
            source=source,
        )
        service_host_config_path = (service_dir / "aware.service-host.toml").resolve()
        remote_environment_api_endpoint = None
        remote_environment_api_request_timeout_s = None
        if environment_target is None:
            remote_environment_api_endpoint = (
                _remote_environment_api_endpoint_from_provider_refs(
                    request.remote_service_api_provider_refs_json
                )
            )
            remote_environment_api_request_timeout_s = (
                _remote_environment_api_request_timeout_s_from_provider_refs(
                    request.remote_service_api_provider_refs_json
                )
            )
        environment_api_request_timeout_s = (
            hosted_service_request_timeout_s
            if environment_target is not None
            else (
                remote_environment_api_request_timeout_s
                or hosted_service_request_timeout_s
            )
        )
        (
            ontology_replica_state_db_path,
            ontology_replica_projection_db_path,
        ) = direct_local._service_host_ontology_replica_db_paths(
            service_dir=service_dir,
            service_toml_paths=service_toml_paths,
        )
        service_host_config_path.write_text(
            direct_local._service_host_toml(
                socket_path=service_socket_path,
                runtime_manifest_path=None,
                kernel_repo_root=kernel_workspace_revision_root,
                artifact_root=repo_root,
                service_toml_paths=(() if service_package_refs else service_toml_paths),
                service_package_refs=service_package_refs,
                experience_toml_paths=experience_toml_paths,
                environment_api_endpoint=(
                    f"http://{host}:{port}"
                    if environment_target is not None
                    else remote_environment_api_endpoint
                ),
                environment_api_request_timeout_s=(
                    environment_api_request_timeout_s
                    if (
                        environment_target is not None
                        or remote_environment_api_endpoint is not None
                    )
                    else None
                ),
                ontology_authority_package_names=tuple(
                    target.package_name
                    for target in source.ontology_targets
                    if target.package_name
                ),
                ontology_authority_source_kind=source.source_kind,
                ontology_authority_root=repo_root,
                ontology_replica_state_db_path=ontology_replica_state_db_path,
                ontology_replica_projection_db_path=ontology_replica_projection_db_path,
            ),
            encoding="utf-8",
        )

    node_endpoint = f"ws://{host}:{port}"
    interface_host_config_paths = _write_interface_host_configs(
        repo_root=repo_root,
        interface_dir=interface_dir,
        node_endpoint=node_endpoint,
        source=source,
        service_host_config_path=service_host_config_path,
        remote_service_api_provider_refs_json=(
            request.remote_service_api_provider_refs_json
        ),
        interface_package_names_by_target=(request.interface_package_names_by_target),
        require_live_runtime=request.require_live_runtime,
        allow_degraded_local_shell=request.allow_degraded_local_shell,
    )
    interface_control_socket_paths = tuple(
        path.parent / "interface-control.sock" for path in interface_host_config_paths
    )

    node_env_path = (env_dir / "node.env").resolve()
    node_command_path = (commands_dir / "node.sh").resolve()
    node_log_path = (logs_dir / "node.log").resolve()
    node_run_manifest_path = (run_dir / "node-run-manifest.json").resolve()
    node_operator_pid_path = (
        run_dir / "node-deploy" / "pids" / f"{_receipt_name(source.package_name)}.pid"
    ).resolve()
    node_operator_status_path = (
        run_dir
        / "node-deploy"
        / "status"
        / f"{_receipt_name(source.package_name)}.json"
    ).resolve()

    service_api_dependency_refs_json = (
        direct_local._service_api_dependency_package_refs_json_from_tomls(
            service_toml_paths=service_toml_paths,
        )
        if service_toml_paths
        else "[]"
    )
    service_api_provider_refs_json = _service_api_provider_refs_json_for_local_node(
        network_node_id=network_node_info.id,
        node_endpoint=node_endpoint,
        source=source,
        service_api_dependency_refs_json=service_api_dependency_refs_json,
        request_timeout_s=hosted_service_request_timeout_s,
    )
    manifest_payload = _node_run_manifest_payload(
        repo_root=repo_root,
        workspace_root=workspace_root,
        run_dir=run_dir,
        source=source,
        node_id=request.node_id or network_node_info.id,
        node_root=node_root,
        node_host_root=node_host_root,
        python_project_path=python_project_path,
        python_execution_closure_manifest_path=(python_execution_closure_manifest_path),
        deployment_payload_path=deployment_payload_path,
        materialized_workspace_root=materialized_workspace_root,
        workspace_revision_manifest_path=workspace_revision_manifest_path,
        runtime_base_environment_manifest_path=runtime_base_environment_manifest_path,
        workspace_revision_id=request.workspace_revision_id,
        workspace_source_revision_id=request.workspace_source_revision_id,
        workspace_source_revision_kind=request.workspace_source_revision_kind,
        workspace_deployment_revision_id=request.workspace_deployment_revision_id,
        environment_runtime_revision_id=request.environment_runtime_revision_id,
        host=host,
        port=port,
        node_env_path=node_env_path,
        node_command_path=node_command_path,
        node_log_path=node_log_path,
        service_host_config_path=service_host_config_path,
        interface_host_config_paths=interface_host_config_paths,
        runtime_manifest_path=runtime_manifest_path,
        token_authority_manifest_path=(
            token_authority_inputs.token_authority_manifest_path
        ),
        token_seed_receipt_path=token_authority_inputs.token_seed_receipt_path,
        service_api_dependency_refs_json=service_api_dependency_refs_json,
        remote_service_api_provider_refs_json=(
            request.remote_service_api_provider_refs_json
        ),
        runtime_artifact_refs_json=runtime_artifact_refs_json,
        environment_port_ready_timeout_s=request.environment_port_ready_timeout_s,
        hosted_service_request_timeout_s=hosted_service_request_timeout_s,
    )
    NodeRunManifest.model_validate(manifest_payload)
    node_run_manifest_path.write_text(
        json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    node_env = _node_env(
        repo_root=repo_root,
        node_host_root=node_host_root,
        node_run_manifest_path=node_run_manifest_path,
        auth_token=resolved_auth_token,
        boot_kernel_environment=environment_target is not None,
    )
    node_env_path.write_text(direct_local._env_text(node_env), encoding="utf-8")
    node_command = (
        "uv",
        "run",
        "--project",
        python_project_path.as_posix(),
        _RUNTIME_PYTHON_COMMAND,
        "-m",
        _NODE_SERVICE_ENTRYPOINT,
    )
    node_command_path.write_text(
        direct_local._node_command_text(
            env_path=node_env_path,
            node_command=node_command,
            repo_root=repo_root,
            log_path=node_log_path,
        ),
        encoding="utf-8",
    )
    node_command_path.chmod(0o755)

    plan = NodePackageRunManifestPlan(
        repo_root=repo_root,
        run_dir=run_dir,
        node_package=source.package_name,
        node_config=source.config_name,
        source_kind=source.source_kind,
        node_run_manifest_path=node_run_manifest_path,
        service_host_config_path=service_host_config_path,
        interface_host_config_paths=interface_host_config_paths,
        node_env_path=node_env_path,
        node_command_path=node_command_path,
        node_log_path=node_log_path,
        node_operator_pid_path=node_operator_pid_path,
        node_operator_status_path=node_operator_status_path,
        receipt_path=(receipts_dir / "node-package-run-manifest.json").resolve(),
        service_socket_path=service_socket_path,
        interface_control_socket_paths=tuple(
            path.resolve() for path in interface_control_socket_paths
        ),
        node_root=node_root,
        node_endpoint=node_endpoint,
        runtime_manifest_path=runtime_manifest_path,
        node_host=host,
        node_port=port,
        service_toml_paths=service_toml_paths,
        service_package_refs=service_package_refs,
        experience_toml_paths=experience_toml_paths,
        environment_targets=source.environment_targets,
        ontology_targets=source.ontology_targets,
        service_targets=source.service_targets,
        interface_targets=source.interface_targets,
        network_node_id=network_node_info.id,
        service_api_provider_refs_json=service_api_provider_refs_json,
        require_live_runtime=request.require_live_runtime,
        allow_degraded_local_shell=request.allow_degraded_local_shell,
        source_local_ontology_composition_bridge_allowed=False,
        source_local_ontology_composition_bridge_used=(
            source_local_ontology_composition_bridge_used
        ),
        auth_token_present=resolved_auth_token is not None,
        auth_token=resolved_auth_token,
        runtime_auth_token_issued=runtime_auth_token is not None,
        runtime_auth_token_id=(
            runtime_auth_token.token_id if runtime_auth_token is not None else None
        ),
        runtime_auth_actor_id=(
            runtime_auth_token.actor_id if runtime_auth_token is not None else None
        ),
        runtime_auth_public_key=(
            runtime_auth_token.public_key if runtime_auth_token is not None else None
        ),
        runtime_auth_environment_config_id=(
            runtime_auth_token.environment_config_id
            if runtime_auth_token is not None
            else None
        ),
        runtime_auth_environment_id=(
            runtime_auth_token.environment_id
            if runtime_auth_token is not None
            else None
        ),
        runtime_auth_process_id=(
            runtime_auth_token.process_id if runtime_auth_token is not None else None
        ),
        runtime_auth_thread_id=(
            runtime_auth_token.thread_id if runtime_auth_token is not None else None
        ),
        token_authority_manifest_path=(
            token_authority_inputs.token_authority_manifest_path
        ),
        token_seed_receipt_path=token_authority_inputs.token_seed_receipt_path,
        auth_token_projection_hash=(token_authority_inputs.auth_token_projection_hash),
        node_env=node_env,
        node_command=node_command,
    )
    plan.receipt_path.write_text(
        json.dumps(plan.to_payload(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return plan


def _validate_runtime_source(
    source: NodePackageRuntimeSource,
) -> NodePackageRuntimeSource:
    package_name = _required_text(source.package_name, "source.package_name")
    config_name = _required_text(source.config_name, "source.config_name")
    source_kind = _required_text(source.source_kind, "source.source_kind")
    if not (
        source.environment_targets
        or source.ontology_targets
        or source.service_targets
        or source.interface_targets
    ):
        raise ValueError(
            f"NodePackage {package_name!r} does not declare any runtime targets."
        )
    return NodePackageRuntimeSource(
        package_name=package_name,
        config_name=config_name,
        source_kind=source_kind,
        node_package_id=source.node_package_id,
        node_config_id=source.node_config_id,
        source_path=source.source_path,
        environment_targets=source.environment_targets,
        ontology_targets=source.ontology_targets,
        service_targets=_validated_service_targets(source.service_targets),
        interface_targets=source.interface_targets,
    )


def _single_environment_target(
    source: NodePackageRuntimeSource,
) -> NodePackageEnvironmentTarget | None:
    if not source.environment_targets:
        return None
    if len(source.environment_targets) != 1:
        raise ValueError(
            "NodeRunManifest currently supports exactly one Environment target "
            f"per NodePackage; package={source.package_name!r} "
            f"declared={len(source.environment_targets)}."
        )
    target = source.environment_targets[0]
    _required_text(target.environment_handle, "environment_handle")
    return target


def _resolve_runtime_manifest_path(
    *,
    repo_root: Path,
    source: NodePackageRuntimeSource,
    environment_target: NodePackageEnvironmentTarget | None,
    runtime_manifest_path: Path | None,
    source_local_ontology_package_names: tuple[str, ...],
) -> Path:
    if (
        runtime_manifest_path is None
        and environment_target is not None
        and source_local_ontology_package_names
    ):
        return _source_local_environment_runtime_manifest_path(
            repo_root=repo_root,
            environment_target=environment_target,
            ontology_package_names=source_local_ontology_package_names,
        )
    if runtime_manifest_path is None:
        raise RuntimeError(
            "Environment NodePackage boot requires source-local Ontology "
            "provider refs or an explicit ontology runtime manifest path. "
            "The retired .aware/environment/runtime/environment.manifest.json "
            "fallback is not Environment app boot authority."
        )
    path = runtime_manifest_path
    path = path.expanduser()
    if not path.is_absolute():
        path = repo_root / path
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(
            f"Environment runtime manifest does not exist: {resolved}"
        )
    if (
        environment_target is not None
        and _ontology_package_metadata_for_runtime_manifest(
            repo_root=repo_root,
            runtime_manifest_path=resolved,
        )
        is None
    ):
        raise RuntimeError(
            "Environment NodePackage runtime_manifest_path must point to an "
            "ontology-owned runtime bundle manifest "
            "(.aware/ontology/runtime/ontology.runtime.manifest.json); "
            "Structure Environment runtime manifests are retired as boot "
            f"authority: {resolved}"
        )
    return resolved


def _source_local_environment_runtime_manifest_path(
    *,
    repo_root: Path,
    environment_target: NodePackageEnvironmentTarget,
    ontology_package_names: tuple[str, ...],
) -> Path:
    candidates: list[tuple[str, Path]] = []
    missing: list[str] = []
    for package_name in ontology_package_names:
        metadata = _ontology_package_metadata_for_package_name(
            repo_root=repo_root,
            package_name=package_name,
        )
        if metadata is None:
            missing.append(package_name)
            continue
        runtime_manifest_path = metadata[4]
        if not runtime_manifest_path.is_file():
            missing.append(package_name)
            continue
        descriptors = _runtime_projection_descriptors_from_runtime_manifest(
            runtime_manifest_path=runtime_manifest_path,
        )
        if any(
            str(descriptor.get("projection_name") or "").strip() == "Environment"
            for descriptor in descriptors
        ):
            candidates.append((package_name, runtime_manifest_path))
    if not candidates:
        missing_text = ", ".join(missing) if missing else "none"
        raise RuntimeError(
            "Environment NodePackage source-local Ontology boot could not resolve "
            "an ontology-owned runtime bundle with an Environment projection "
            f"descriptor for environment target {environment_target.environment_handle!r}. "
            "Materialize the owning ontology package and retry. "
            f"provider_packages={list(ontology_package_names)!r} missing={missing_text}"
        )
    if len(candidates) > 1:
        raise RuntimeError(
            "Environment NodePackage source-local Ontology boot resolved multiple "
            "ontology runtime bundles with an Environment projection descriptor: "
            + ", ".join(
                f"{package_name}={path.as_posix()}" for package_name, path in candidates
            )
        )
    return candidates[0][1]


def _source_local_ontology_package_names_from_remote_provider_refs(
    remote_service_api_provider_refs_json: str | None,
) -> tuple[str, ...]:
    refs = _remote_service_api_provider_ref_payloads(
        remote_service_api_provider_refs_json
    )
    names: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        if not _remote_provider_ref_provides_ontology_service_api(ref):
            continue
        raw_source = ref.get("provider_node_runtime_source")
        if raw_source is None:
            raw_source = ref.get("provider_node_run_manifest_source")
        if not isinstance(raw_source, Mapping):
            continue
        source_kind = _clean_text(raw_source.get("source_kind"))
        if source_kind is not None and source_kind != "node_ontology_manifest":
            continue
        raw_environment_targets = raw_source.get("environment_targets")
        if _is_sequence_not_text(raw_environment_targets) and raw_environment_targets:
            continue
        raw_targets = raw_source.get("ontology_targets")
        if not _is_sequence_not_text(raw_targets):
            continue
        for raw_target in raw_targets:
            package_name = None
            if isinstance(raw_target, Mapping):
                package_name = _clean_text(raw_target.get("package_name"))
            elif isinstance(raw_target, str):
                package_name = raw_target.strip() or None
            if package_name is None:
                continue
            key = package_name.casefold()
            if key in seen:
                continue
            seen.add(key)
            names.append(package_name)
    return tuple(names)


def _remote_provider_ref_provides_ontology_service_api(
    ref: Mapping[str, object],
) -> bool:
    service_package_ref = ref.get("service_package_ref")
    if not isinstance(service_package_ref, Mapping):
        return False
    package_name = _clean_text(service_package_ref.get("package_name"))
    if package_name == "aware-ontology-service":
        return True
    raw_provided = service_package_ref.get("provided_api_packages")
    if not _is_sequence_not_text(raw_provided):
        return False
    for raw_api in raw_provided:
        if not isinstance(raw_api, Mapping):
            continue
        api_name = _clean_text(raw_api.get("api_package_name"))
        if api_name == "ontology-service-api":
            return True
    return False


def _candidate_ontology_manifest_paths(*, repo_root: Path) -> tuple[Path, ...]:
    patterns = (
        "modules/*/aware.ontology.toml",
        "ontologies/*/aware.ontology.toml",
        "workspaces/*/modules/**/aware.ontology.toml",
        "workspaces/*/ontologies/**/aware.ontology.toml",
        "workspaces/*/aware.ontology.toml",
    )
    paths: list[Path] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(repo_root.glob(pattern)):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append(resolved)
    return tuple(paths)


def _runtime_artifact_refs_json_for_local_environment_runtime(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
    source: NodePackageRuntimeSource | None = None,
    source_local_ontology_package_names: tuple[str, ...] = (),
) -> str | None:
    artifact_refs: list[dict[str, object]] = []
    seen_manifest_paths: set[Path] = set()

    def _append_runtime_manifest(path: Path) -> None:
        resolved = path.resolve()
        if resolved in seen_manifest_paths:
            return
        artifact_ref = _ontology_runtime_artifact_ref_for_local_runtime_manifest(
            repo_root=repo_root,
            runtime_manifest_path=resolved,
        )
        if artifact_ref is None:
            return
        seen_manifest_paths.add(resolved)
        artifact_refs.append(artifact_ref)

    _append_runtime_manifest(runtime_manifest_path)

    for package_name in source_local_ontology_package_names:
        if package_name not in _ENVIRONMENT_BOOT_COMPANION_ONTOLOGY_PACKAGES:
            continue
        metadata = _ontology_package_metadata_for_package_name(
            repo_root=repo_root,
            package_name=package_name,
        )
        if metadata is None:
            continue
        dependency_runtime_manifest_path = metadata[4]
        if not dependency_runtime_manifest_path.is_file():
            continue
        _append_runtime_manifest(dependency_runtime_manifest_path)

    node_source_artifact_ref = _node_runtime_source_artifact_ref(source=source)
    if node_source_artifact_ref is not None:
        artifact_refs.append(node_source_artifact_ref)

    if not artifact_refs:
        return None
    return json.dumps(artifact_refs, sort_keys=True, separators=(",", ":"))


def _node_runtime_source_artifact_ref(
    *,
    source: NodePackageRuntimeSource | None,
) -> dict[str, object] | None:
    if source is None:
        return None
    if not any(target.profile_mounts for target in source.environment_targets):
        return None
    runtime_source = source.to_payload()
    return {
        "artifact_family": "aware.node.runtime_source",
        "artifact_key": (
            "aware.node.runtime_source:" f"{source.package_name}:{source.config_name}"
        ),
        "artifact_role": "node_runtime_source",
        "required_for": ["environment_profile_mounts"],
        "status": "available",
        "package_name": source.package_name,
        "runtime_contract_version": "aware.node.runtime_source.v1",
        "provider_payload": {
            "node_runtime_source": runtime_source,
        },
        "receipt": {
            "node_runtime_source": runtime_source,
        },
    }


def _ontology_runtime_artifact_ref_for_local_runtime_manifest(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
) -> dict[str, object] | None:
    package_metadata = _ontology_package_metadata_for_runtime_manifest(
        repo_root=repo_root,
        runtime_manifest_path=runtime_manifest_path,
    )
    if package_metadata is None:
        return None
    descriptors = _runtime_projection_descriptors_from_runtime_manifest(
        runtime_manifest_path=runtime_manifest_path,
    )
    if not descriptors:
        return None

    from aware_ontology.semantic_runtime_catalog import (  # noqa: WPS433
        build_ontology_runtime_artifact_set_from_materialization_details,
        build_ontology_runtime_artifact_set_ownership_receipt,
    )

    package_name, fqn_prefix, ontology_toml_path, source_manifest_path = (
        package_metadata
    )
    manifest_relpath = _repo_relative_path(
        repo_root=repo_root,
        path=ontology_toml_path,
    )
    source_manifest_relpath = _repo_relative_path(
        repo_root=repo_root,
        path=source_manifest_path,
    )
    runtime_manifest_relpath = _repo_relative_path(
        repo_root=repo_root,
        path=runtime_manifest_path,
    )
    runtime_manifest_payload = runtime_manifest_path.read_bytes()
    runtime_manifest_size_bytes = len(runtime_manifest_payload)
    runtime_manifest_digest = (
        "sha256:" + hashlib.sha256(runtime_manifest_payload).hexdigest()
    )
    object_config_graph_hash = _runtime_bundle_object_config_graph_hash(
        runtime_manifest_path=runtime_manifest_path,
    )
    db_schema_registry_details = _runtime_bundle_db_schema_registry_details(
        repo_root=repo_root,
        runtime_manifest_path=runtime_manifest_path,
    )
    stable_provenance_ids = _local_ontology_runtime_stable_provenance_ids(
        package_name=package_name,
        fqn_prefix=fqn_prefix,
    )
    ocg_id = next(
        (
            str(descriptor.get("object_config_graph_id"))
            for descriptor in descriptors
            if descriptor.get("object_config_graph_id") is not None
        ),
        None,
    )
    artifact_set = build_ontology_runtime_artifact_set_from_materialization_details(
        details={
            "schema": "aware_node.local_runtime_artifact_refs.v1",
            "provider_key": "aware_node",
            "semantic_owner": "aware_node.local_runtime_artifact_refs",
            "manifest_path": manifest_relpath,
            "source_manifest_path": source_manifest_relpath,
            "package_name": package_name,
            "fqn_prefix": fqn_prefix,
            "object_config_graph_id": ocg_id,
            "object_config_graph_hash": object_config_graph_hash,
            **stable_provenance_ids,
            "runtime_bundle_manifest_path": runtime_manifest_relpath,
            "runtime_bundle_manifest_workspace_relative_path": (
                runtime_manifest_relpath
            ),
            "runtime_bundle_manifest_status": "available",
            "runtime_bundle_manifest_size_bytes": runtime_manifest_size_bytes,
            "runtime_bundle_manifest_digest": runtime_manifest_digest,
            "runtime_projection_descriptors": descriptors,
            **db_schema_registry_details,
        },
        materialization_ref=f"node-local:{runtime_manifest_relpath}",
        include_artifacts=True,
    )
    receipt = build_ontology_runtime_artifact_set_ownership_receipt(
        artifact_set=artifact_set,
    )
    artifact_ref = {
        key: value
        for key, value in receipt.items()
        if key != "ontology_runtime_artifact_set"
    }
    artifact_ref["receipt"] = receipt
    return artifact_ref


def _runtime_bundle_object_config_graph_hash(*, runtime_manifest_path: Path) -> str:
    manifest = _load_json_mapping(runtime_manifest_path)
    object_config_graph_hash = _clean_text(
        _mapping_value(manifest.get("ocg"), "hash")
        or manifest.get("object_config_graph_hash")
    )
    if object_config_graph_hash is None:
        raise RuntimeError(
            "Ontology runtime artifact refs require ocg.hash in "
            f"{runtime_manifest_path}; refusing to emit an incomplete "
            "OntologyRuntimeArtifactSet."
        )
    return object_config_graph_hash


def _local_ontology_runtime_stable_provenance_ids(
    *,
    package_name: str,
    fqn_prefix: str,
) -> dict[str, str]:
    from aware_code.stable_ids import (  # noqa: WPS433
        code_package_source_config_key,
        stable_code_package_config_id,
        stable_code_package_id,
    )
    from aware_meta_ontology_dto.stable_ids import (  # noqa: WPS433
        stable_object_config_graph_package_id,
    )
    from aware_ontology_ontology_dto.stable_ids import (  # noqa: WPS433
        stable_ontology_package_id,
    )

    source_code_package_config_id = stable_code_package_config_id(
        config_key=code_package_source_config_key(
            manifest_kind="aware_toml",
            surface="ontology",
        ),
    )
    return {
        "ontology_package_id": str(
            stable_ontology_package_id(
                fqn_prefix=fqn_prefix,
                name=package_name,
            )
        ),
        "source_code_package_id": str(
            stable_code_package_id(
                code_package_config_id=source_code_package_config_id,
                package_name=package_name,
                language="aware",
            )
        ),
        "object_config_graph_package_id": str(
            stable_object_config_graph_package_id(
                package_name=package_name,
                fqn_prefix=fqn_prefix,
            )
        ),
    }


def _runtime_bundle_db_schema_registry_details(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
) -> dict[str, object]:
    manifest = _load_json_mapping(runtime_manifest_path)
    registry_file = (
        _clean_text(_mapping_value(manifest.get("db_schema_registry"), "file"))
        or "db.schema.registry.json"
    )
    registry_path = (runtime_manifest_path.parent / registry_file).resolve()
    if not registry_path.is_file():
        return {}
    registry_payload = registry_path.read_bytes()
    return {
        "runtime_bundle_db_schema_registry_path": registry_path.as_posix(),
        "runtime_bundle_db_schema_registry_workspace_relative_path": (
            _repo_relative_path(repo_root=repo_root, path=registry_path)
        ),
        "runtime_bundle_db_schema_registry_digest": (
            "sha256:" + hashlib.sha256(registry_payload).hexdigest()
        ),
        "runtime_bundle_db_schema_registry_sql_roots": (
            _db_schema_registry_sql_roots(registry_path)
        ),
    }


def _db_schema_registry_sql_roots(path: Path) -> tuple[str, ...]:
    payload = _load_json_mapping(path)
    return tuple(
        dict.fromkeys(
            sql_root
            for entry in _mapping_sequence(payload.get("entries"))
            for sql_root in (_clean_text(entry.get("sql_root")),)
            if sql_root is not None
        )
    )


def _ontology_package_metadata_for_runtime_manifest(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
) -> tuple[str, str, Path, Path] | None:
    from aware_ontology.manifest.loader import load_aware_ontology_toml_spec

    resolved_runtime_manifest_path = runtime_manifest_path.resolve()
    for ontology_toml_path in _candidate_ontology_manifest_paths(repo_root=repo_root):
        spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
        source_manifest = _required_text(
            getattr(spec.ontology, "source_manifest", ""),
            "ontology.source_manifest",
        )
        source_manifest_path = (ontology_toml_path.parent / source_manifest).resolve()
        candidate_runtime_manifest_path = (
            source_manifest_path.parent
            / ".aware"
            / "ontology"
            / "runtime"
            / "ontology.runtime.manifest.json"
        ).resolve()
        if candidate_runtime_manifest_path != resolved_runtime_manifest_path:
            continue
        package_name = _required_text(
            getattr(spec.ontology, "package_name", ""),
            "ontology.package_name",
        )
        fqn_prefix = _required_text(
            getattr(spec.ontology, "fqn_prefix", ""),
            "ontology.fqn_prefix",
        )
        return (
            package_name,
            fqn_prefix,
            ontology_toml_path.resolve(),
            source_manifest_path,
        )
    return None


def _ontology_package_metadata_for_package_name(
    *,
    repo_root: Path,
    package_name: str,
) -> tuple[str, str, Path, Path, Path] | None:
    from aware_ontology.manifest.loader import load_aware_ontology_toml_spec

    expected_package_name = _required_text(package_name, "package_name")
    for ontology_toml_path in _candidate_ontology_manifest_paths(repo_root=repo_root):
        spec = load_aware_ontology_toml_spec(toml_path=ontology_toml_path)
        candidate_package_name = _required_text(
            getattr(spec.ontology, "package_name", ""),
            "ontology.package_name",
        )
        if candidate_package_name != expected_package_name:
            continue
        source_manifest = _required_text(
            getattr(spec.ontology, "source_manifest", ""),
            "ontology.source_manifest",
        )
        source_manifest_path = (ontology_toml_path.parent / source_manifest).resolve()
        runtime_manifest_path = (
            source_manifest_path.parent
            / ".aware"
            / "ontology"
            / "runtime"
            / "ontology.runtime.manifest.json"
        ).resolve()
        fqn_prefix = _required_text(
            getattr(spec.ontology, "fqn_prefix", ""),
            "ontology.fqn_prefix",
        )
        return (
            candidate_package_name,
            fqn_prefix,
            ontology_toml_path.resolve(),
            source_manifest_path,
            runtime_manifest_path,
        )
    return None


def _runtime_projection_descriptors_from_runtime_manifest(
    *,
    runtime_manifest_path: Path,
) -> tuple[dict[str, object], ...]:
    manifest = _load_json_mapping(runtime_manifest_path)
    runtime_dir = runtime_manifest_path.parent
    opg_entries = _opg_index_entries(manifest.get("opg_index"))
    if not opg_entries:
        return ()
    snapshot = _runtime_manifest_ocg_snapshot(
        runtime_manifest_path=runtime_manifest_path,
        manifest=manifest,
    )
    edge_to_function_id = _constructor_edge_function_ids_from_snapshot(snapshot)
    class_capability_functions = _capability_functions_by_class_config_id_from_snapshot(
        snapshot
    )
    ocg_id = _clean_text(
        _mapping_value(manifest.get("ocg"), "canonical_id")
        or _mapping_value(manifest.get("environment"), "id")
    )
    opg_hashes = tuple(
        sorted(
            {
                projection_hash
                for entry in opg_entries
                for projection_hash in (_clean_text(entry.get("projection_hash")),)
                if projection_hash is not None
            }
        )
    )
    descriptors: list[dict[str, object]] = []
    for entry in opg_entries:
        opg_file = _clean_text(entry.get("file"))
        if opg_file is None:
            continue
        opg_path = (runtime_dir / opg_file).resolve()
        opg = _load_json_mapping(opg_path)
        projection_name = _clean_text(opg.get("name")) or _clean_text(
            entry.get("model")
        )
        if projection_name is None:
            continue
        constructor_function_ids = tuple(
            sorted(
                {
                    function_id
                    for constructor in _mapping_sequence(
                        opg.get("object_projection_graph_constructors")
                    )
                    for edge_id in (
                        _clean_text(constructor.get("function_constructor_id")),
                    )
                    for function_id in (
                        edge_to_function_id.get(edge_id) if edge_id else None,
                    )
                    if function_id is not None
                }
            )
        )
        root_class_config_id = _root_class_config_id_for_opg(opg)
        capability_functions = tuple(
            function
            | {
                "is_constructor": bool(
                    function.get("is_constructor")
                    or function.get("id") in constructor_function_ids
                )
            }
            for function in class_capability_functions.get(root_class_config_id, ())
        )
        metadata: dict[str, object] = {
            "supports_virtual_build": opg.get("supports_virtual_build"),
        }
        if root_class_config_id is not None:
            metadata["root_class_config_id"] = root_class_config_id
        if capability_functions:
            metadata["capability_functions"] = list(capability_functions)
        descriptors.append(
            {
                "projection_name": projection_name,
                "projection_hash": _clean_text(opg.get("projection_hash"))
                or _clean_text(entry.get("projection_hash")),
                "object_projection_graph_id": _clean_text(opg.get("id")),
                "constructor_function_id": (
                    constructor_function_ids[0] if constructor_function_ids else None
                ),
                "object_config_graph_id": _clean_text(opg.get("object_config_graph_id"))
                or ocg_id,
                "opg_hashes": list(opg_hashes),
                "required_for": ["runtime_index", "service_boot"],
                "metadata": metadata,
            }
        )
    return tuple(
        sorted(
            descriptors,
            key=lambda item: (
                str(item.get("projection_name") or ""),
                str(item.get("projection_hash") or ""),
            ),
        )
    )


def _constructor_edge_function_ids_from_runtime_manifest(
    *,
    runtime_manifest_path: Path,
    manifest: Mapping[str, object],
) -> dict[str, str]:
    return _constructor_edge_function_ids_from_snapshot(
        _runtime_manifest_ocg_snapshot(
            runtime_manifest_path=runtime_manifest_path,
            manifest=manifest,
        )
    )


def _runtime_manifest_ocg_snapshot(
    *,
    runtime_manifest_path: Path,
    manifest: Mapping[str, object],
) -> Mapping[str, object]:
    snapshot_name = _clean_text(_mapping_value(manifest.get("ocg"), "snapshot"))
    if snapshot_name is None:
        return {}
    snapshot_path = (runtime_manifest_path.parent / snapshot_name).resolve()
    if not snapshot_path.is_file():
        return {}
    import msgpack  # noqa: WPS433

    snapshot = msgpack.unpackb(snapshot_path.read_bytes(), raw=False)
    if not isinstance(snapshot, Mapping):
        return {}
    return snapshot


def _constructor_edge_function_ids_from_snapshot(
    snapshot: Mapping[str, object],
) -> dict[str, str]:
    edge_to_function_id: dict[str, str] = {}
    for node in _mapping_sequence(snapshot.get("object_config_graph_nodes")):
        class_config = _mapping_payload(node.get("class_config"))
        for link in _mapping_sequence(
            class_config.get("class_config_function_configs")
        ):
            edge_id = _clean_text(link.get("id"))
            function_config = _mapping_payload(link.get("function_config"))
            function_id = _clean_text(function_config.get("id"))
            if edge_id is not None and function_id is not None:
                edge_to_function_id[edge_id] = function_id
    return edge_to_function_id


def _capability_functions_by_class_config_id_from_snapshot(
    snapshot: Mapping[str, object],
) -> dict[str, tuple[dict[str, object], ...]]:
    result: dict[str, tuple[dict[str, object], ...]] = {}
    for node in _mapping_sequence(snapshot.get("object_config_graph_nodes")):
        class_config = _mapping_payload(node.get("class_config"))
        class_config_id = _clean_text(class_config.get("id"))
        if class_config_id is None:
            continue
        functions: list[dict[str, object]] = []
        for link in _mapping_sequence(
            class_config.get("class_config_function_configs")
        ):
            function_config = _mapping_payload(link.get("function_config"))
            function_id = _clean_text(function_config.get("id"))
            function_name = _clean_text(function_config.get("name"))
            if function_id is None or function_name is None:
                continue
            function_kind = _clean_text(function_config.get("kind"))
            functions.append(
                {
                    "id": function_id,
                    "name": function_name,
                    "summary": _clean_text(function_config.get("description")),
                    "is_constructor": function_kind == "constructor",
                    "owner_class_config_id": class_config_id,
                    "owner_class_name": _clean_text(class_config.get("name")),
                    "owner_class_fqn": _clean_text(
                        class_config.get("class_fqn") or class_config.get("fqn")
                    ),
                }
            )
        result[class_config_id] = tuple(
            sorted(functions, key=lambda item: str(item.get("name") or ""))
        )
    return result


def _root_class_config_id_for_opg(opg: Mapping[str, object]) -> str | None:
    root_node_ids = {
        root_node_id
        for constructor in _mapping_sequence(
            opg.get("object_projection_graph_constructors")
        )
        for root_node_id in (_clean_text(constructor.get("root_node_id")),)
        if root_node_id is not None
    }
    fallback: str | None = None
    for node in _mapping_sequence(opg.get("object_projection_graph_nodes")):
        class_config_id = _clean_text(node.get("class_config_id"))
        if class_config_id is None:
            continue
        if fallback is None:
            fallback = class_config_id
        node_id = _clean_text(node.get("id"))
        if node_id is not None and node_id in root_node_ids:
            return class_config_id
        if bool(node.get("is_root")):
            return class_config_id
    return fallback


def _opg_index_entries(value: object) -> tuple[Mapping[str, object], ...]:
    if isinstance(value, Mapping):
        return _mapping_sequence(value.get("entries"))
    return ()


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _mapping_payload(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _mapping_value(value: object, key: str) -> object | None:
    return value.get(key) if isinstance(value, Mapping) else None


def _load_json_mapping(path: Path) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, Mapping) else {}


def _repo_relative_path(*, repo_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _assert_path_within_repo(
    *,
    repo_root: Path,
    path: Path,
    label: str,
) -> None:
    try:
        path.resolve().relative_to(repo_root.resolve())
    except ValueError as exc:
        raise RuntimeError(
            f"NodePackage {label} must stay inside repo root: {path}"
        ) from exc


def _local_service_host_socket_path(
    *,
    run_dir: Path,
    source: NodePackageRuntimeSource,
) -> Path:
    digest_basis = "|".join(
        item
        for item in (
            run_dir.as_posix(),
            source.source_kind,
            source.package_name,
            source.config_name,
        )
        if item
    )
    digest = hashlib.sha256(digest_basis.encode("utf-8")).hexdigest()[:16]
    socket_root = Path(tempfile.gettempdir()) / _SERVICE_HOST_IPC_TEMP_DIR_NAME / digest
    filename_token = _service_socket_filename_token(
        source.config_name or source.package_name or "service-host"
    )
    path = (socket_root / f"{filename_token}.sock").resolve()
    if len(path.as_posix()) >= _UNIX_SOCKET_SAFE_PATH_LENGTH:
        digest = hashlib.sha256(path.as_posix().encode("utf-8")).hexdigest()[:20]
        path = (socket_root / f"{digest}.sock").resolve()
    return path


def _service_socket_filename_token(value: str) -> str:
    token = "".join(
        char if char.isalnum() or char in {"-", "_", "."} else "_"
        for char in value.strip()
    ).strip("._-")
    if not token:
        return "service-host"
    if len(token) <= 48:
        return token
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:12]
    return f"{token[:35]}-{digest}"


def _resolve_service_toml_paths_for_targets(
    *,
    repo_root: Path,
    service_targets: tuple[NodePackageServiceTarget, ...],
    service_toml_paths: tuple[Path, ...],
    allow_default_registry: bool = True,
    remote_service_api_provider_refs_json: str | None = None,
) -> tuple[Path, ...]:
    target_names = tuple(
        _required_text(target.service_name, "service_name")
        for target in service_targets
    )
    if not target_names:
        return ()
    raw_paths = list(service_toml_paths)
    if allow_default_registry:
        for target_name in target_names:
            default_relpath = DEFAULT_NODE_PACKAGE_SERVICE_TOMLS_BY_TARGET.get(
                target_name
            )
            if default_relpath is not None:
                raw_paths.append(Path(default_relpath))
        raw_paths.extend(
            Path(relpath)
            for relpath in DEFAULT_NODE_PACKAGE_SERVICE_TOMLS_BY_TARGET.values()
            if (repo_root / relpath).is_file()
        )
    registry = _service_toml_registry(repo_root=repo_root, raw_paths=tuple(raw_paths))
    resolved: list[Path] = []
    missing: list[str] = []
    for target_name in target_names:
        path = registry.get(target_name.casefold())
        if path is None:
            missing.append(target_name)
            continue
        if path not in resolved:
            resolved.append(path)
    if missing:
        raise RuntimeError(
            "NodePackage run manifest could not resolve Service targets from "
            "explicit local service TOML inputs: "
            + ", ".join(repr(name) for name in missing)
        )
    return _expand_service_toml_paths_for_api_dependency_closure(
        selected_paths=tuple(resolved),
        candidate_paths=tuple(dict.fromkeys(registry.values())),
        externally_satisfied_api_packages=(
            _remote_service_api_provider_package_names(
                remote_service_api_provider_refs_json
            )
        ),
    )


def _service_toml_registry(
    *,
    repo_root: Path,
    raw_paths: tuple[Path, ...],
) -> dict[str, Path]:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec

    registry: dict[str, Path] = {}
    seen_paths: set[Path] = set()
    for raw_path in raw_paths:
        path = raw_path.expanduser()
        if not path.is_absolute():
            path = repo_root / path
        resolved = path.resolve()
        if resolved in seen_paths:
            continue
        seen_paths.add(resolved)
        if not resolved.is_file():
            raise FileNotFoundError(f"Service TOML does not exist: {resolved}")
        spec = load_aware_service_toml_spec(toml_path=resolved)
        for name in _service_target_name_candidates(spec):
            key = name.casefold()
            existing = registry.get(key)
            if existing is not None and existing != resolved:
                raise RuntimeError(
                    "NodePackage run manifest found multiple Service TOMLs "
                    f"for target {name!r}: {existing} and {resolved}"
                )
            registry[key] = resolved
    return registry


def _service_target_name_candidates(spec: object) -> tuple[str, ...]:
    service = getattr(spec, "service")
    package_name = _required_text(getattr(service, "package_name", ""), "package_name")
    fqn_prefix = _required_text(getattr(service, "fqn_prefix", ""), "fqn_prefix")
    candidates = {
        package_name,
        package_name.replace("-", "_"),
        fqn_prefix,
    }
    for suffix in ("_service", "-service"):
        if package_name.endswith(suffix):
            candidates.add(package_name[: -len(suffix)].replace("-", "_"))
        if fqn_prefix.endswith(suffix):
            candidates.add(fqn_prefix[: -len(suffix)])
    return tuple(sorted(candidates, key=str.casefold))


def _expand_service_toml_paths_for_api_dependency_closure(
    *,
    selected_paths: tuple[Path, ...],
    candidate_paths: tuple[Path, ...],
    externally_satisfied_api_packages: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec

    selected = list(selected_paths)
    external_api_package_keys = {
        package_name.casefold()
        for package_name in externally_satisfied_api_packages
        if package_name.strip()
    }
    specs_by_path = {
        path: load_aware_service_toml_spec(toml_path=path)
        for path in dict.fromkeys((*selected_paths, *candidate_paths))
    }
    providers_by_api_package: dict[str, Path] = {}
    for path in candidate_paths:
        spec = specs_by_path[path]
        for api_package_name in _service_spec_api_packages_by_kind(
            spec,
            kind_value="api_service_protocol",
        ):
            providers_by_api_package.setdefault(api_package_name.casefold(), path)

    while True:
        selected_set = set(selected)
        missing_api_packages: list[str] = []
        added = False
        for path in tuple(selected):
            spec = specs_by_path[path]
            for api_package_name in _service_spec_api_packages_by_kind(
                spec,
                kind_value="api_invocation",
            ):
                if api_package_name.casefold() in external_api_package_keys:
                    continue
                provider_path = providers_by_api_package.get(
                    api_package_name.casefold()
                )
                if provider_path is None:
                    missing_api_packages.append(api_package_name)
                    continue
                if provider_path not in selected_set:
                    selected.append(provider_path)
                    selected_set.add(provider_path)
                    added = True
        if missing_api_packages:
            missing = ", ".join(
                repr(name) for name in dict.fromkeys(missing_api_packages)
            )
            raise RuntimeError(
                "NodePackage run manifest could not resolve Service API "
                "dependency providers from explicit local service TOML inputs: "
                f"{missing}"
            )
        if not added:
            return tuple(selected)


def _remote_service_api_provider_package_names(
    remote_service_api_provider_refs_json: str | None,
) -> tuple[str, ...]:
    package_names: list[str] = []
    for item in _remote_service_api_provider_ref_payloads(
        remote_service_api_provider_refs_json
    ):
        service_package_ref = item.get("service_package_ref")
        if not isinstance(service_package_ref, Mapping):
            continue
        for bridge_payload in _remote_service_api_package_bridge_payloads(
            service_package_ref
        ):
            name = bridge_payload.get("api_package_name")
            if not isinstance(name, str):
                name = bridge_payload.get("package_name")
            name = str(name or "").strip()
            if name and name not in package_names:
                package_names.append(name)
    return tuple(package_names)


def _remote_service_api_provider_ref_payloads(
    remote_service_api_provider_refs_json: str | None,
) -> tuple[Mapping[str, object], ...]:
    text = str(remote_service_api_provider_refs_json or "").strip()
    if not text:
        return ()
    try:
        payload = json.loads(text)
    except Exception:
        return ()
    if isinstance(payload, Mapping):
        raw_items = payload.get("remote_service_api_provider_refs")
        if raw_items is None:
            raw_items = payload.get("provider_refs")
        if raw_items is None:
            raw_items = [payload]
    elif isinstance(payload, list):
        raw_items = payload
    else:
        return ()

    if not isinstance(raw_items, list):
        return ()
    return tuple(item for item in raw_items if isinstance(item, Mapping))


def _remote_environment_api_endpoint_from_provider_refs(
    remote_service_api_provider_refs_json: str | None,
) -> str | None:
    endpoints: list[str] = []
    for provider_ref in _remote_service_api_provider_ref_payloads(
        remote_service_api_provider_refs_json
    ):
        if not _remote_provider_ref_provides_environment_api(provider_ref):
            continue
        endpoint = _clean_text(provider_ref.get("provider_node_base_url"))
        if endpoint is None:
            raise RuntimeError(
                "Remote Environment service provider ref is missing "
                "provider_node_base_url."
            )
        if endpoint not in endpoints:
            endpoints.append(endpoint)
    if len(endpoints) > 1:
        raise RuntimeError(
            "Remote Environment API endpoint is ambiguous across provider refs: "
            + ", ".join(sorted(endpoints))
        )
    return endpoints[0] if endpoints else None


def _remote_environment_api_request_timeout_s_from_provider_refs(
    remote_service_api_provider_refs_json: str | None,
) -> float | None:
    timeout_values: list[float] = []
    for provider_ref in _remote_service_api_provider_ref_payloads(
        remote_service_api_provider_refs_json
    ):
        if not _remote_provider_ref_provides_environment_api(provider_ref):
            continue
        raw_timeout = provider_ref.get("request_timeout_s")
        if raw_timeout is None:
            continue
        timeout_s = float(raw_timeout)
        if timeout_s <= 0:
            raise RuntimeError(
                "Remote Environment service provider ref has invalid "
                f"request_timeout_s={raw_timeout!r}."
            )
        if timeout_s not in timeout_values:
            timeout_values.append(timeout_s)
    if len(timeout_values) > 1:
        raise RuntimeError(
            "Remote Environment API request timeout is ambiguous across "
            "provider refs: "
            + ", ".join(f"{value:.6g}" for value in sorted(timeout_values))
        )
    return timeout_values[0] if timeout_values else None


def _remote_provider_ref_provides_environment_api(
    provider_ref: Mapping[str, object],
) -> bool:
    service_package_ref = provider_ref.get("service_package_ref")
    if isinstance(service_package_ref, Mapping):
        package_name = _clean_text(service_package_ref.get("package_name"))
        if package_name == _ENVIRONMENT_SERVICE_PACKAGE_NAME:
            return True
        provided_api_packages = service_package_ref.get("provided_api_packages")
        if isinstance(provided_api_packages, list):
            for item in provided_api_packages:
                if not isinstance(item, Mapping):
                    continue
                for key in ("api_package_name", "package_name"):
                    if _clean_text(item.get(key)) == _ENVIRONMENT_API_PACKAGE_NAME:
                        return True

    advertisement = provider_ref.get("hosted_service_advertisement")
    if isinstance(advertisement, Mapping):
        service_name = _clean_text(advertisement.get("service_name"))
        if service_name == "aware_environment":
            return True
        service_package_names = advertisement.get("service_package_names")
        if isinstance(service_package_names, list) and any(
            _clean_text(item) == _ENVIRONMENT_SERVICE_PACKAGE_NAME
            for item in service_package_names
        ):
            return True
        endpoint_refs = advertisement.get("endpoint_refs")
        if isinstance(endpoint_refs, list) and any(
            str(item).startswith("environment.") for item in endpoint_refs
        ):
            return True
    return False


def _service_api_provider_refs_json_for_local_node(
    *,
    network_node_id: UUID,
    node_endpoint: str,
    source: NodePackageRuntimeSource,
    service_api_dependency_refs_json: str,
    request_timeout_s: float,
) -> str:
    try:
        payload = json.loads(service_api_dependency_refs_json)
    except Exception:
        payload = []
    if not isinstance(payload, list):
        payload = []
    runtime_source = source.to_payload()
    authority_metadata = build_ontology_authority_catalog_metadata(runtime_source)
    provider_refs: list[dict[str, object]] = []
    for item in payload:
        if not isinstance(item, Mapping):
            continue
        provider_ref: dict[str, object] = {
            "provider_node_id": str(network_node_id),
            "provider_node_base_url": node_endpoint,
            "provider_node_package": source.package_name,
            "provider_node_runtime_source": runtime_source,
            "request_timeout_s": float(request_timeout_s),
            "service_package_ref": dict(item),
        }
        advertisement = _hosted_service_advertisement_payload_from_service_package_ref(
            item
        )
        if advertisement is not None:
            provider_ref["hosted_service_advertisement"] = advertisement
        if authority_metadata:
            provider_ref["authority"] = {"metadata": authority_metadata}
        provider_refs.append(provider_ref)
    return json.dumps(provider_refs, sort_keys=True, separators=(",", ":"))


def _hosted_service_advertisement_payload_from_service_package_ref(
    service_package_ref: Mapping[str, object],
) -> dict[str, object] | None:
    package_name = _clean_text(service_package_ref.get("package_name"))
    if package_name is None:
        return None
    endpoint_refs = _service_protocol_endpoint_refs_from_package_ref(
        service_package_ref
    )
    if not endpoint_refs:
        return None
    payload: dict[str, object] = {
        "service_name": _service_name_from_package_name(package_name),
        "service_package_names": [package_name],
        "endpoint_refs": list(endpoint_refs),
        "host_id": "aware_service_service",
        "protocol_version": SERVICE_HOST_PROTOCOL_VERSION,
        "supports_stream_events": False,
    }
    service_package_id = _clean_text(service_package_ref.get("service_package_id"))
    if service_package_id is not None:
        payload["service_package_id"] = service_package_id
    return payload


def _service_protocol_endpoint_refs_from_package_ref(
    service_package_ref: Mapping[str, object],
) -> tuple[str, ...]:
    api_package_names: list[str] = []
    seen_names: set[str] = set()
    for candidate in _service_api_package_names_from_service_package_ref(
        service_package_ref
    ):
        key = candidate.casefold()
        if key in seen_names:
            continue
        seen_names.add(key)
        api_package_names.append(candidate)

    endpoint_refs: set[str] = set()
    for api_package_name in api_package_names:
        module_name = _service_protocol_module_name(api_package_name)
        if module_name is None:
            continue
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        bindings = getattr(module, "ENDPOINT_BINDINGS", None)
        if not isinstance(bindings, Mapping):
            continue
        endpoint_refs.update(
            endpoint_ref.strip()
            for endpoint_ref in bindings
            if isinstance(endpoint_ref, str) and endpoint_ref.strip()
        )
    return tuple(sorted(endpoint_refs, key=str.casefold))


def _service_api_package_names_from_service_package_ref(
    service_package_ref: Mapping[str, object],
) -> tuple[str, ...]:
    names: list[str] = []
    for bridge in _remote_service_api_package_bridge_payloads(service_package_ref):
        for key in ("api_package_name", "package_name"):
            name = _clean_text(bridge.get(key))
            if name is not None:
                names.append(name)
                break
    for dependency in service_package_ref.get("dependencies") or ():
        if not isinstance(dependency, Mapping):
            continue
        kind = _clean_text(dependency.get("kind"))
        if kind is not None and kind != "api_service_protocol":
            continue
        name = _clean_text(dependency.get("package_name"))
        if name is not None:
            names.append(name)
    return tuple(names)


def _service_protocol_module_name(api_package_name: str) -> str | None:
    base = api_package_name.strip().replace("-", "_")
    if not base:
        return None
    if base.endswith("_api"):
        base = base[: -len("_api")] + "_protocol"
    elif not base.endswith("_protocol"):
        base = f"{base}_protocol"
    return f"aware_{base}.protocols"


def _service_name_from_package_name(package_name: str) -> str:
    name = package_name.strip()
    if name.endswith("-service"):
        name = name[: -len("-service")]
    return name.replace("-", "_")


def _is_sequence_not_text(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    )


def _remote_service_api_package_bridge_payloads(
    service_package_ref: Mapping[str, object],
) -> tuple[Mapping[str, object], ...]:
    bridges: list[Mapping[str, object]] = []
    provided_api_packages = service_package_ref.get("provided_api_packages")
    if isinstance(provided_api_packages, list):
        bridges.extend(
            item for item in provided_api_packages if isinstance(item, Mapping)
        )
    dependencies = service_package_ref.get("dependencies")
    if isinstance(dependencies, list):
        for item in dependencies:
            if not isinstance(item, Mapping):
                continue
            kind = str(item.get("kind") or "").strip()
            if kind == "api_service_protocol":
                bridges.append(item)
    return tuple(bridges)


def _service_spec_api_packages_by_kind(
    spec: object,
    *,
    kind_value: str,
) -> tuple[str, ...]:
    packages: list[str] = []
    for dependency in getattr(spec, "dependencies", ()):
        kind = getattr(dependency, "kind", "")
        value = str(getattr(kind, "value", kind))
        if value != kind_value:
            continue
        package_name = str(getattr(dependency, "package_name", "") or "").strip()
        if package_name:
            packages.append(package_name)
    return tuple(dict.fromkeys(packages))


def _write_interface_host_configs(
    *,
    repo_root: Path,
    interface_dir: Path,
    node_endpoint: str,
    source: NodePackageRuntimeSource,
    service_host_config_path: Path | None,
    remote_service_api_provider_refs_json: str | None,
    interface_package_names_by_target: Mapping[str, str],
    require_live_runtime: bool,
    allow_degraded_local_shell: bool,
) -> tuple[Path, ...]:
    if not source.interface_targets:
        return ()
    if (
        service_host_config_path is None
        and not _remote_service_api_provider_ref_payloads(
            remote_service_api_provider_refs_json
        )
    ):
        raise RuntimeError(
            "NodePackage interface targets require a local ServiceHost config or "
            "remote Service API provider refs."
        )
    paths: list[Path] = []
    for target in source.interface_targets:
        interface_name = _required_text(target.interface_name, "interface_name")
        package_name = str(
            interface_package_names_by_target.get(interface_name)
            or interface_package_names_by_target.get(interface_name.casefold())
            or ""
        ).strip()
        if not package_name:
            raise RuntimeError(
                "NodePackage run manifest could not resolve Interface target "
                f"{interface_name!r} from explicit interface package inputs."
            )
        target_dir = (
            interface_dir.parent / "if" / _receipt_name(interface_name)
        ).resolve()
        state_home = target_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        config_path = (target_dir / "aware.interface-host.toml").resolve()
        config_path.write_text(
            _node_package_interface_host_toml(
                repo_root=repo_root,
                state_home=state_home,
                namespace=interface_name,
                endpoint=node_endpoint,
                interface_package_name=package_name,
                require_live_runtime=require_live_runtime,
                allow_degraded_local_shell=allow_degraded_local_shell,
                service_host_config_path=service_host_config_path,
            ),
            encoding="utf-8",
        )
        paths.append(config_path)
    return tuple(paths)


def _node_package_interface_host_toml(
    *,
    repo_root: Path,
    state_home: Path,
    namespace: str,
    endpoint: str,
    interface_package_name: str,
    require_live_runtime: bool,
    allow_degraded_local_shell: bool,
    service_host_config_path: Path | None,
) -> str:
    lines = [
        "[app]",
        f"repository_root = {direct_local._toml_string(repo_root.as_posix())}",
        f"state_home = {direct_local._toml_string(state_home.as_posix())}",
        f"namespace = {direct_local._toml_string(namespace)}",
        'host_label = "node-package-interface"',
        f"endpoint = {direct_local._toml_string(endpoint)}",
        (
            "allow_degraded_local_shell = "
            f"{direct_local._toml_bool(allow_degraded_local_shell)}"
        ),
        f"require_live_runtime = {direct_local._toml_bool(require_live_runtime)}",
        "",
        "[interface_package]",
        f"package_name = {direct_local._toml_string(interface_package_name)}",
    ]
    if service_host_config_path is not None:
        lines.extend(
            [
                "",
                "[local_service_host]",
                "bootstrap_config_path = "
                f"{direct_local._toml_string(service_host_config_path.as_posix())}",
                "",
            ]
        )
    return "\n".join(lines)


def _node_run_manifest_payload(
    *,
    repo_root: Path,
    workspace_root: Path,
    run_dir: Path,
    source: NodePackageRuntimeSource,
    node_id: UUID | None,
    node_root: Path,
    node_host_root: Path,
    python_project_path: Path,
    python_execution_closure_manifest_path: Path | None,
    deployment_payload_path: Path | None,
    materialized_workspace_root: Path | None,
    workspace_revision_manifest_path: Path | None,
    runtime_base_environment_manifest_path: Path | None,
    workspace_revision_id: str | UUID | None,
    workspace_source_revision_id: str | None,
    workspace_source_revision_kind: str | None,
    workspace_deployment_revision_id: str | None,
    environment_runtime_revision_id: str | None,
    host: str,
    port: int,
    node_env_path: Path,
    node_command_path: Path,
    node_log_path: Path,
    service_host_config_path: Path | None,
    interface_host_config_paths: tuple[Path, ...],
    runtime_manifest_path: Path | None,
    token_authority_manifest_path: Path | None,
    token_seed_receipt_path: Path | None,
    service_api_dependency_refs_json: str,
    remote_service_api_provider_refs_json: str | None,
    runtime_artifact_refs_json: str | None,
    environment_port_ready_timeout_s: float,
    hosted_service_request_timeout_s: float,
) -> dict[str, object]:
    timeout_s = float(environment_port_ready_timeout_s)
    hosted_services: list[dict[str, object]] = []
    if service_host_config_path is not None:
        hosted_services.append(
            {
                "name": "local-service-host",
                "bootstrap_config_path": service_host_config_path.as_posix(),
                "launch_command": [
                    _RUNTIME_PYTHON_COMMAND,
                    "-m",
                    _SERVICE_HOST_ENTRYPOINT,
                ],
            }
        )
    route_inputs: dict[str, object] = {
        "service_api_dependency_package_refs_json": (service_api_dependency_refs_json),
    }
    remote_refs_json = str(remote_service_api_provider_refs_json or "").strip()
    if remote_refs_json:
        route_inputs["remote_service_api_provider_refs_json"] = remote_refs_json
    payload: dict[str, object] = {
        "version": NODE_RUN_MANIFEST_VERSION,
        "node_package": source.package_name,
        "node_id": (
            str(node_id)
            if node_id is not None
            else (str(source.node_package_id) if source.node_package_id else None)
        ),
        "display_name": source.config_name,
        "host": host,
        "port": port,
        "node_base_url": f"http://{host}:{port}",
        "node_websocket_path": "/interface/network_node",
        "run_dir": run_dir.as_posix(),
        "aware_root": node_root.as_posix(),
        "node_host_root": node_host_root.as_posix(),
        "env_file_path": node_env_path.as_posix(),
        "command_file_path": node_command_path.as_posix(),
        "log_path": node_log_path.as_posix(),
        "python_project_path": python_project_path.as_posix(),
        "hosted_services": hosted_services,
        "hosted_interfaces": [
            {
                "name": f"local-interface-host:{path.parent.name}",
                "bootstrap_config_path": path.as_posix(),
                "launch_command": [
                    _RUNTIME_PYTHON_COMMAND,
                    "-m",
                    _INTERFACE_HOST_ENTRYPOINT,
                ],
            }
            for path in interface_host_config_paths
        ],
        "route_inputs": route_inputs,
        "readiness": {
            "node_http_ready_timeout_s": timeout_s,
            "environment_service_ready_timeout_s": timeout_s,
            "environment_ready_timeout_s": timeout_s,
            "hosted_service_ready_timeout_s": timeout_s,
            "hosted_interface_ready_timeout_s": timeout_s,
            "hosted_service_request_timeout_s": float(hosted_service_request_timeout_s),
        },
        "provenance": {
            "source_kind": source.source_kind,
            "workspace_root": workspace_root.as_posix(),
            "workspace_revision_id": _optional_text_value(workspace_revision_id),
            "workspace_source_revision_id": workspace_source_revision_id,
            "workspace_source_revision_kind": workspace_source_revision_kind,
            "workspace_deployment_revision_id": workspace_deployment_revision_id,
            "environment_runtime_revision_id": environment_runtime_revision_id,
            "materialized_workspace_root": (
                materialized_workspace_root.as_posix()
                if materialized_workspace_root is not None
                else None
            ),
            "workspace_revision_manifest_path": (
                workspace_revision_manifest_path.as_posix()
                if workspace_revision_manifest_path is not None
                else None
            ),
            "deployment_payload_path": (
                deployment_payload_path.as_posix()
                if deployment_payload_path is not None
                else None
            ),
            "artifact_refs_json": runtime_artifact_refs_json,
        },
    }
    if python_execution_closure_manifest_path is not None:
        payload["python_execution_closure_manifest_path"] = (
            python_execution_closure_manifest_path.as_posix()
        )
    if deployment_payload_path is not None:
        payload["deployment_payload_path"] = deployment_payload_path.as_posix()
    if runtime_base_environment_manifest_path is not None:
        payload["runtime_base_environment_manifest_path"] = (
            runtime_base_environment_manifest_path.as_posix()
        )
    if token_authority_manifest_path is not None:
        payload["auth_inputs"] = {
            "token_authority_manifest_path": (token_authority_manifest_path.as_posix()),
            "token_seed_receipt_path": (
                token_seed_receipt_path.as_posix()
                if token_seed_receipt_path is not None
                else None
            ),
        }
    if runtime_manifest_path is not None:
        payload.update(
            {
                "environment_provision_mode": "subprocess",
                "environment_manifest_path": runtime_manifest_path.as_posix(),
                "environment_service_port": port,
                "environment_api_endpoint": f"http://{host}:{port}",
            }
        )
    return payload


def _node_env(
    *,
    repo_root: Path,
    node_host_root: Path,
    node_run_manifest_path: Path,
    auth_token: str | None,
    boot_kernel_environment: bool = True,
) -> dict[str, str]:
    env: dict[str, str] = {}
    apply_node_run_manifest_env(node_run_manifest_path, environ=env)
    env["AWARE_REPO_ROOT"] = node_host_root.as_posix()
    env["AWARE_NODE_BOOT_KERNEL"] = "1" if boot_kernel_environment else "0"
    env["AWARE_ENVIRONMENT_OIG_SYNC_MODE"] = "off"
    if auth_token is not None:
        env["AWARE_AUTH_TOKEN"] = auth_token
    env.pop(_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV, None)
    return dict(sorted(env.items()))


def _write_token_authority_inputs(
    *,
    repo_root: Path,
    auth_dir: Path,
    runtime_manifest_path: Path | None,
    auth_token: str | None,
    source_kind: str,
    commit_store_root_path: Path | None = None,
):
    token = str(auth_token or "").strip()
    if not token:
        return direct_local._TokenAuthorityInputResult()
    if runtime_manifest_path is None:
        raise RuntimeError(
            "NodePackage token authority inputs require an Environment runtime "
            "manifest; service/ontology-only NodePackage runs must not request "
            "runtime token authority seeding."
        )

    from aware_identity_ontology.stable_ids import stable_auth_token_registry_id

    projection_hash = (
        direct_local._resolve_auth_token_projection_hash(repo_root=repo_root)
        if token.startswith("aware_apt_")
        else None
    )
    registry_id = stable_auth_token_registry_id()
    resolved_commit_store_root = (commit_store_root_path or repo_root).resolve()
    auth_dir.mkdir(parents=True, exist_ok=True)
    authority_manifest_path = (auth_dir / "token-authority.manifest.json").resolve()
    seed_receipt_path = (auth_dir / "token-seed.receipt.json").resolve()
    token_type = "apt" if token.startswith("aware_apt_") else "opaque"

    authority_payload: dict[str, object] = {
        "version": "aware.node.token_authority.v1",
        "source_kind": source_kind,
        "runtime_manifest_path": runtime_manifest_path.as_posix(),
        "commit_store_root_path": resolved_commit_store_root.as_posix(),
        "token_registry_id": str(registry_id),
        "auth_token_projection_hash": projection_hash,
        "raw_oig_lane_copied": False,
    }
    authority_manifest_path.write_text(
        json.dumps(authority_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    seed_receipt_payload: dict[str, object] = {
        "version": "aware.node.token_seed_receipt.v1",
        "source_kind": source_kind,
        "status": "declared",
        "token_authority_manifest_path": authority_manifest_path.as_posix(),
        "runtime_manifest_path": runtime_manifest_path.as_posix(),
        "commit_store_root_path": resolved_commit_store_root.as_posix(),
        "token_registry_id": str(registry_id),
        "auth_token_present": True,
        "auth_token_type": token_type,
        "auth_token_projection_hash": projection_hash,
        "raw_oig_lane_copied": False,
    }
    seed_receipt_path.write_text(
        json.dumps(seed_receipt_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return direct_local._TokenAuthorityInputResult(
        token_authority_manifest_path=authority_manifest_path,
        token_seed_receipt_path=seed_receipt_path,
        auth_token_projection_hash=projection_hash,
    )


def _ensure_local_network_node_info(
    *,
    node_root: Path,
    host: str,
    port: int,
    label: str,
    node_id: UUID | None = None,
):
    from aware_network.network.node.local_info import (
        LocalNetworkNodeInfo,
        normalize_local_network_node_info_identity,
    )

    info_path = node_root / ".aware" / "network_node.json"
    info_path.parent.mkdir(parents=True, exist_ok=True)
    http_base_url = f"http://{host}:{port}"
    if info_path.is_file():
        try:
            info = LocalNetworkNodeInfo.model_validate(
                json.loads(info_path.read_text(encoding="utf-8"))
            )
        except Exception as exc:
            raise RuntimeError(
                "NodePackage run manifest could not read persisted node identity: "
                + info_path.as_posix()
            ) from exc
        info = info.model_copy(
            update={
                "id": node_id or info.id,
                "http_base_url": http_base_url,
                "label": info.label or label,
                "requires_auth_interface_to_node": True,
            }
        )
    else:
        info_kwargs = {
            "label": label,
            "http_base_url": http_base_url,
            "requires_auth_interface_to_node": True,
        }
        if node_id is not None:
            info_kwargs["id"] = node_id
        info = LocalNetworkNodeInfo(**info_kwargs)
    info = normalize_local_network_node_info_identity(info)
    info_path.write_text(info.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return info


def _environment_targets_from_node_config(
    node_config: object,
) -> tuple[NodePackageEnvironmentTarget, ...]:
    return tuple(
        NodePackageEnvironmentTarget(
            environment_handle=_required_attr_text(target, "environment_handle"),
            profile_mounts=_profile_mounts_from_target(target),
        )
        for target in getattr(node_config, "environment_targets", ())
    )


def _service_targets_from_node_config(
    node_config: object,
) -> tuple[NodePackageServiceTarget, ...]:
    return tuple(
        NodePackageServiceTarget(
            service_name=_required_attr_text(target, "service_name"),
            code_packages=_service_code_packages_from_target(target),
        )
        for target in getattr(node_config, "service_targets", ())
    )


def _service_targets_from_materialization_spec(
    spec: object,
) -> tuple[NodePackageServiceTarget, ...]:
    service_targets = tuple(getattr(spec, "service_targets", ()) or ())
    if service_targets:
        return tuple(
            NodePackageServiceTarget(
                service_name=_required_attr_text(target, "service_name"),
                code_packages=_service_code_packages_from_target(target),
            )
            for target in service_targets
        )
    return tuple(
        NodePackageServiceTarget(service_name=_required_text(str(item), "service_name"))
        for item in getattr(spec, "service_names", ())
    )


def _service_code_packages_from_target(
    target: object,
) -> tuple[NodePackageServiceCodePackage, ...]:
    return tuple(
        NodePackageServiceCodePackage(
            slot_key=_required_attr_text(package, "slot_key").casefold(),
            package_name=_required_attr_text(package, "package_name"),
            language=_required_text(
                getattr(
                    getattr(package, "language", "aware"),
                    "value",
                    getattr(package, "language", "aware"),
                ),
                "language",
            ).casefold(),
        )
        for package in getattr(target, "code_packages", ()) or ()
    )


def _validated_service_targets(
    service_targets: tuple[NodePackageServiceTarget, ...],
) -> tuple[NodePackageServiceTarget, ...]:
    normalized_targets: list[NodePackageServiceTarget] = []
    for target in service_targets:
        normalized_targets.append(
            NodePackageServiceTarget(
                service_name=_required_text(target.service_name, "service_name"),
                code_packages=tuple(
                    NodePackageServiceCodePackage(
                        slot_key=_required_text(
                            package.slot_key, "service code package slot_key"
                        ).casefold(),
                        package_name=_required_text(
                            package.package_name, "service code package package_name"
                        ),
                        language=_required_text(
                            package.language or "aware",
                            "service code package language",
                        ).casefold(),
                    )
                    for package in target.code_packages
                ),
            )
        )
    return tuple(normalized_targets)


def _experience_package_names_from_service_activations(
    service_targets: tuple[NodePackageServiceTarget, ...],
) -> tuple[str, ...]:
    package_names: list[str] = []
    seen: set[str] = set()
    for target in service_targets:
        for package in target.code_packages:
            if package.slot_key.casefold() != "experience":
                continue
            key = package.package_name.casefold()
            if key in seen:
                continue
            seen.add(key)
            package_names.append(package.package_name)
    return tuple(package_names)


def _ontology_targets_from_node_config(
    node_config: object,
) -> tuple[NodePackageOntologyTarget, ...]:
    return tuple(
        NodePackageOntologyTarget(
            package_name=_required_attr_text(target, "package_name")
        )
        for target in getattr(node_config, "ontology_targets", ())
    )


def _interface_targets_from_node_config(
    node_config: object,
) -> tuple[NodePackageInterfaceTarget, ...]:
    return tuple(
        NodePackageInterfaceTarget(
            interface_name=_required_attr_text(target, "interface_name")
        )
        for target in getattr(node_config, "interface_targets", ())
    )


def _environment_targets_from_ownership(
    environment_targets: Sequence[object],
) -> tuple[NodePackageEnvironmentTarget, ...]:
    return tuple(
        NodePackageEnvironmentTarget(
            environment_handle=_required_attr_text(target, "environment_handle"),
            profile_mounts=_profile_mounts_from_target(target),
        )
        for target in environment_targets
    )


def _profile_mounts_from_target(
    target: object,
) -> tuple[NodePackageEnvironmentProfileMount, ...]:
    mounts = tuple(getattr(target, "profile_mounts", ()) or ())
    return tuple(
        NodePackageEnvironmentProfileMount(
            package_name=_required_attr_text(mount, "package_name"),
            profile_key=_required_attr_text(mount, "profile_key"),
            mount_key=_required_text(
                getattr(mount, "mount_key", None)
                or f"{getattr(mount, 'package_name', '')}:"
                f"{getattr(mount, 'profile_key', '')}",
                "mount_key",
            ),
            mode=_required_text(getattr(mount, "mode", "mounted"), "mode"),
            position=getattr(mount, "position", 0),
        )
        for mount in mounts
    )


def _required_attr_text(obj: object, attr: str) -> str:
    return _required_text(getattr(obj, attr, ""), attr)


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _optional_text_value(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _payload_optional_value(payload: object, key: str) -> object | None:
    if payload is None:
        return None
    if isinstance(payload, Mapping):
        return payload.get(key)
    return getattr(payload, key, None)


def _payload_required_value(payload: object, key: str) -> object:
    value = _payload_optional_value(payload, key)
    if value is None:
        raise ValueError(f"WorkspaceDeployment payload is missing {key}.")
    return value


def _payload_optional_text(payload: object, key: str) -> str | None:
    return _optional_text_value(_payload_optional_value(payload, key))


def _payload_required_text(payload: object, key: str) -> str:
    return _required_text(_payload_optional_value(payload, key), key)


def _payload_sequence(payload: object, key: str) -> tuple[object, ...]:
    value = _payload_optional_value(payload, key)
    if value is None:
        return ()
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"WorkspaceDeployment payload field {key} must be a sequence.")
    return tuple(value)


def _optional_uuid_value(value: object) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    text = str(value).strip()
    return UUID(text) if text else None


def _optional_uuid_attr(obj: object, attr: str) -> UUID | None:
    value = getattr(obj, attr, None)
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _sequence_items_are_text(value: object) -> bool:
    return isinstance(value, tuple) and all(isinstance(item, str) for item in value)


def _receipt_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in value)


__all__ = [
    "DEFAULT_NODE_PACKAGE_LOCAL_HANDLE",
    "DEFAULT_NODE_PACKAGE_LOCAL_HOST",
    "DEFAULT_NODE_PACKAGE_LOCAL_PORT",
    "DEFAULT_NODE_PACKAGE_SERVICE_TOMLS_BY_TARGET",
    "NodeOntologyLocalBootstrapRequest",
    "NodePackageEnvironmentProfileMount",
    "NodePackageEnvironmentTarget",
    "NodePackageInterfaceTarget",
    "NodePackageRunManifestPlan",
    "NodePackageRunManifestRequest",
    "NodePackageRuntimeSource",
    "NodePackageServiceCodePackage",
    "NodePackageServiceTarget",
    "node_package_runtime_source_from_materialization_spec",
    "node_package_runtime_source_from_node_package",
    "node_package_runtime_source_from_workspace_deployment_payload",
    "prepare_node_ontology_local_bootstrap",
    "prepare_node_package_run_manifest",
]
