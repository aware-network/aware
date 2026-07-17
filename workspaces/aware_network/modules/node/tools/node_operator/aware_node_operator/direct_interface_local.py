from __future__ import annotations

import asyncio
import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import sys
import tomllib
from typing import Iterator, Mapping
from uuid import UUID, uuid4

from aware_node_service.host.run_manifest import (
    NODE_RUN_MANIFEST_VERSION,
    apply_node_run_manifest_env,
)
from aware_node_operator.service_host_refs import (
    ServiceHostImplementationPackageRefInput,
)


DEFAULT_DIRECT_INTERFACE_LOCAL_HANDLE = "dev-localhost"
DEFAULT_DIRECT_INTERFACE_LOCAL_NAMESPACE = "flutter-aware-control"
DEFAULT_DIRECT_INTERFACE_LOCAL_INTERFACE_PACKAGE = "aware-control-interface"
DEFAULT_DIRECT_INTERFACE_LOCAL_HOST = "127.0.0.1"
DEFAULT_DIRECT_INTERFACE_LOCAL_PORT = 8911
DEFAULT_DIRECT_INTERFACE_LOCAL_NODE_PACKAGE = "direct-interface-local"
DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_REQUEST_TIMEOUT_S = 30.0
DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_TOMLS = (
    "workspaces/aware_network/modules/attention/services/attention/aware.service.toml",
    "workspaces/aware_network/modules/environment/services/environment/aware.service.toml",
    "workspaces/aware_network/modules/experience/services/experience/aware.service.toml",
    "workspaces/aware_network/modules/meta/services/meta/aware.service.toml",
    "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml",
    "workspaces/aware_network/modules/hub/services/hub/aware.service.toml",
    "workspaces/aware_network/modules/identity/services/identity/aware.service.toml",
    "workspaces/aware_network/modules/reactivity/services/reactivity/aware.service.toml",
)
DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOB = (
    "experiences/*/aware.experience.toml"
)
DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOBS = (
    DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOB,
    "modules/*/experiences/**/aware.experience.toml",
)
_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV = "AWARE_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_PATH"
_IDENTITY_OPG_INDEX_RELATIVE_PATH = (
    Path("modules")
    / "identity"
    / "structure"
    / "ontology"
    / ".aware"
    / "environment"
    / "runtime"
    / "opg.index.json"
)
_ROOT_ENVIRONMENT_MANIFEST_RELATIVE_PATH = (
    Path(".aware") / "environment" / "runtime" / "environment.manifest.json"
)


@dataclass(frozen=True, slots=True)
class _TokenAuthorityInputResult:
    token_authority_manifest_path: Path | None = None
    token_seed_receipt_path: Path | None = None
    auth_token_projection_hash: str | None = None


@dataclass(frozen=True, slots=True)
class _IssuedRuntimeAuthToken:
    token: str
    token_id: UUID
    actor_id: UUID
    public_key: str
    commit_store_root_path: Path
    environment_config_id: UUID
    environment_id: UUID
    process_id: UUID
    thread_id: UUID


@dataclass(frozen=True, slots=True)
class DirectInterfaceLocalBootstrapRequest:
    repo_root: Path
    run_dir: Path
    node_package: str = DEFAULT_DIRECT_INTERFACE_LOCAL_NODE_PACKAGE
    namespace: str = DEFAULT_DIRECT_INTERFACE_LOCAL_NAMESPACE
    interface_package_name: str = DEFAULT_DIRECT_INTERFACE_LOCAL_INTERFACE_PACKAGE
    host: str = DEFAULT_DIRECT_INTERFACE_LOCAL_HOST
    port: int = DEFAULT_DIRECT_INTERFACE_LOCAL_PORT
    service_toml_paths: tuple[Path, ...] = ()
    experience_toml_paths: tuple[Path, ...] = ()
    auth_token: str | None = None
    issue_runtime_auth_token: bool = False
    require_live_runtime: bool = True
    allow_degraded_local_shell: bool = False
    environment_port_ready_timeout_s: float = 420.0
    hosted_service_request_timeout_s: float = (
        DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_REQUEST_TIMEOUT_S
    )
    environment_config_manifest_globs: str | None = (
        ".aware/environment/runtime/environment.manifest.json"
    )


@dataclass(frozen=True, slots=True)
class DirectInterfaceLocalBootstrapPlan:
    repo_root: Path
    run_dir: Path
    node_package: str
    node_run_manifest_path: Path
    service_host_config_path: Path
    interface_host_config_path: Path
    node_env_path: Path
    node_command_path: Path
    node_log_path: Path
    node_operator_pid_path: Path
    node_operator_status_path: Path
    receipt_path: Path
    service_socket_path: Path
    interface_control_socket_path: Path
    node_root: Path
    node_endpoint: str
    runtime_manifest_path: Path
    node_host: str
    node_port: int
    namespace: str
    interface_package_name: str
    service_toml_paths: tuple[Path, ...]
    experience_toml_paths: tuple[Path, ...]
    require_live_runtime: bool
    allow_degraded_local_shell: bool
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
            "version": "aware.node.direct_interface_local_bootstrap.v1",
            "repo_root": self.repo_root.as_posix(),
            "run_dir": self.run_dir.as_posix(),
            "node_package": self.node_package,
            "node_run_manifest_path": self.node_run_manifest_path.as_posix(),
            "service_host_config_path": self.service_host_config_path.as_posix(),
            "interface_host_config_path": self.interface_host_config_path.as_posix(),
            "node_env_path": self.node_env_path.as_posix(),
            "node_command_path": self.node_command_path.as_posix(),
            "node_log_path": self.node_log_path.as_posix(),
            "node_operator_pid_path": self.node_operator_pid_path.as_posix(),
            "node_operator_status_path": self.node_operator_status_path.as_posix(),
            "receipt_path": self.receipt_path.as_posix(),
            "service_socket_path": self.service_socket_path.as_posix(),
            "interface_control_socket_path": (
                self.interface_control_socket_path.as_posix()
            ),
            "node_root": self.node_root.as_posix(),
            "node_endpoint": self.node_endpoint,
            "runtime_manifest_path": self.runtime_manifest_path.as_posix(),
            "node_host": self.node_host,
            "node_port": self.node_port,
            "namespace": self.namespace,
            "interface_package_name": self.interface_package_name,
            "service_toml_paths": [path.as_posix() for path in self.service_toml_paths],
            "experience_toml_paths": [
                path.as_posix() for path in self.experience_toml_paths
            ],
            "require_live_runtime": self.require_live_runtime,
            "allow_degraded_local_shell": self.allow_degraded_local_shell,
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
            "node_env": _redacted_env(self.node_env),
            "node_command": list(self.node_command),
            "workspace_revision_deployment_payload_env_present": (
                _NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV in self.node_env
            ),
        }


def prepare_direct_interface_local_bootstrap(
    request: DirectInterfaceLocalBootstrapRequest,
) -> DirectInterfaceLocalBootstrapPlan:
    repo_root = request.repo_root.expanduser().resolve()
    run_dir = request.run_dir.expanduser().resolve()
    namespace = _required_text(request.namespace, "namespace")
    node_package = _required_text(request.node_package, "node_package")
    interface_package_name = _required_text(
        request.interface_package_name,
        "interface_package_name",
    )
    host = _required_text(request.host, "host")
    port = int(request.port)
    if port <= 0:
        raise ValueError("port must be greater than 0.")
    hosted_service_request_timeout_s = float(request.hosted_service_request_timeout_s)
    if hosted_service_request_timeout_s <= 0:
        raise ValueError("hosted_service_request_timeout_s must be greater than 0.")

    service_toml_paths = _resolve_service_toml_paths(
        repo_root=repo_root,
        service_toml_paths=request.service_toml_paths,
    )
    source_runtime_manifest_path = _root_environment_manifest_path(repo_root=repo_root)
    experience_toml_paths = _resolve_experience_toml_paths(
        repo_root=repo_root,
        service_toml_paths=service_toml_paths,
        interface_package_name=interface_package_name,
        experience_toml_paths=request.experience_toml_paths,
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
    runtime_manifest_path = _snapshot_direct_local_runtime_manifest(
        repo_root=repo_root,
        run_dir=run_dir,
        source_runtime_manifest_path=source_runtime_manifest_path,
    )

    service_socket_path = (service_dir / "aware-service-host.sock").resolve()
    service_host_config_path = (service_dir / "aware.service-host.toml").resolve()
    (
        ontology_replica_state_db_path,
        ontology_replica_projection_db_path,
    ) = _service_host_ontology_replica_db_paths(
        service_dir=service_dir,
        service_toml_paths=service_toml_paths,
    )
    interface_state_home = (interface_dir / "state").resolve()
    interface_host_config_path = (interface_dir / "aware.interface-host.toml").resolve()
    interface_control_socket_path = (
        interface_state_home / "interface-control.sock"
    ).resolve()
    node_root = (run_dir / "node-root").resolve()
    node_root.mkdir(parents=True, exist_ok=True)
    network_node_info = _ensure_direct_local_network_node_info(
        node_root=node_root,
        host=host,
        port=port,
    )
    resolved_auth_token = (
        str(request.auth_token).strip() if request.auth_token is not None else ""
    ) or None
    runtime_auth_token: _IssuedRuntimeAuthToken | None = None
    if (
        resolved_auth_token is None
        and request.require_live_runtime
        and request.issue_runtime_auth_token
    ):
        runtime_auth_commit_store_root = (auth_dir / "runtime-auth-store").resolve()
        runtime_auth_token = _issue_direct_local_runtime_auth_token(
            repo_root=repo_root,
            runtime_manifest_path=runtime_manifest_path,
            node_id=network_node_info.id,
            commit_store_root_path=runtime_auth_commit_store_root,
        )
        resolved_auth_token = runtime_auth_token.token
    token_authority_inputs = _write_token_authority_inputs_for_direct_local_node(
        repo_root=repo_root,
        auth_dir=auth_dir,
        runtime_manifest_path=runtime_manifest_path,
        auth_token=resolved_auth_token,
        commit_store_root_path=(
            runtime_auth_token.commit_store_root_path
            if runtime_auth_token is not None
            else None
        ),
    )
    node_endpoint = f"ws://{host}:{port}"
    node_env_path = (env_dir / "node.env").resolve()
    node_command_path = (commands_dir / "node.sh").resolve()
    node_log_path = (logs_dir / "node.log").resolve()
    node_run_manifest_path = (run_dir / "node-run-manifest.json").resolve()
    node_operator_pid_path = (
        run_dir / "node-deploy" / "pids" / f"{_receipt_name(node_package)}.pid"
    ).resolve()
    node_operator_status_path = (
        run_dir / "node-deploy" / "status" / f"{_receipt_name(node_package)}.json"
    ).resolve()

    service_host_config_path.write_text(
        _service_host_toml(
            socket_path=service_socket_path,
            runtime_manifest_path=runtime_manifest_path,
            artifact_root=repo_root,
            service_toml_paths=service_toml_paths,
            experience_toml_paths=experience_toml_paths,
            environment_api_endpoint=f"http://{host}:{port}",
            environment_api_request_timeout_s=hosted_service_request_timeout_s,
            ontology_replica_state_db_path=ontology_replica_state_db_path,
            ontology_replica_projection_db_path=ontology_replica_projection_db_path,
        ),
        encoding="utf-8",
    )
    interface_host_config_path.write_text(
        _interface_host_toml(
            repo_root=repo_root,
            state_home=interface_state_home,
            namespace=namespace,
            endpoint=node_endpoint,
            interface_package_name=interface_package_name,
            require_live_runtime=request.require_live_runtime,
            allow_degraded_local_shell=request.allow_degraded_local_shell,
            service_host_config_path=service_host_config_path,
        ),
        encoding="utf-8",
    )
    service_api_dependency_refs_json = (
        _service_api_dependency_package_refs_json_from_tomls(
            service_toml_paths=service_toml_paths,
        )
    )
    node_run_manifest_path.write_text(
        json.dumps(
            _node_run_manifest_payload(
                repo_root=repo_root,
                run_dir=run_dir,
                node_package=node_package,
                node_root=node_root,
                host=host,
                port=port,
                node_env_path=node_env_path,
                node_command_path=node_command_path,
                node_log_path=node_log_path,
                service_host_config_path=service_host_config_path,
                interface_host_config_path=interface_host_config_path,
                runtime_manifest_path=runtime_manifest_path,
                token_authority_manifest_path=(
                    token_authority_inputs.token_authority_manifest_path
                ),
                token_seed_receipt_path=(
                    token_authority_inputs.token_seed_receipt_path
                ),
                service_api_dependency_refs_json=service_api_dependency_refs_json,
                environment_port_ready_timeout_s=(
                    request.environment_port_ready_timeout_s
                ),
                hosted_service_request_timeout_s=hosted_service_request_timeout_s,
            ),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    node_env = _node_env(
        repo_root=repo_root,
        node_run_manifest_path=node_run_manifest_path,
        auth_token=resolved_auth_token,
        runtime_auth_actor_id=(
            runtime_auth_token.actor_id if runtime_auth_token is not None else None
        ),
        interface_control_socket_path=interface_control_socket_path,
        node_endpoint=node_endpoint,
        interface_package_name=interface_package_name,
        require_live_runtime=request.require_live_runtime,
        allow_degraded_local_shell=request.allow_degraded_local_shell,
    )
    node_env_path.write_text(_env_text(node_env), encoding="utf-8")
    node_command = (sys.executable, "-m", "aware_node_service.app")
    node_command_path.write_text(
        _node_command_text(
            env_path=node_env_path,
            node_command=node_command,
            repo_root=repo_root,
            log_path=node_log_path,
        ),
        encoding="utf-8",
    )
    node_command_path.chmod(0o755)

    plan = DirectInterfaceLocalBootstrapPlan(
        repo_root=repo_root,
        run_dir=run_dir,
        node_package=node_package,
        node_run_manifest_path=node_run_manifest_path,
        service_host_config_path=service_host_config_path,
        interface_host_config_path=interface_host_config_path,
        node_env_path=node_env_path,
        node_command_path=node_command_path,
        node_log_path=node_log_path,
        node_operator_pid_path=node_operator_pid_path,
        node_operator_status_path=node_operator_status_path,
        receipt_path=(receipts_dir / "direct-interface-local.json").resolve(),
        service_socket_path=service_socket_path,
        interface_control_socket_path=interface_control_socket_path,
        node_root=node_root,
        node_endpoint=node_endpoint,
        runtime_manifest_path=runtime_manifest_path,
        node_host=host,
        node_port=port,
        namespace=namespace,
        interface_package_name=interface_package_name,
        service_toml_paths=service_toml_paths,
        experience_toml_paths=experience_toml_paths,
        require_live_runtime=request.require_live_runtime,
        allow_degraded_local_shell=request.allow_degraded_local_shell,
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


def _resolve_service_toml_paths(
    *,
    repo_root: Path,
    service_toml_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    raw_paths = service_toml_paths or tuple(
        Path(value) for value in DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_TOMLS
    )
    resolved: list[Path] = []
    for raw_path in raw_paths:
        path = raw_path.expanduser()
        if not path.is_absolute():
            path = repo_root / path
        resolved_path = path.resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError(f"Service TOML does not exist: {resolved_path}")
        if resolved_path not in resolved:
            resolved.append(resolved_path)
    return tuple(resolved)


def _root_environment_manifest_path(*, repo_root: Path) -> Path:
    manifest_path = repo_root / _ROOT_ENVIRONMENT_MANIFEST_RELATIVE_PATH
    if not manifest_path.is_file():
        raise RuntimeError(
            "Direct local Interface node requires the root environment runtime "
            "manifest so hosted Meta can resolve domain projections. Compile the "
            "environment before booting direct local Interface: "
            f"missing={manifest_path}"
        )
    return manifest_path.resolve()


def _snapshot_direct_local_runtime_manifest(
    *,
    repo_root: Path,
    run_dir: Path,
    source_runtime_manifest_path: Path,
) -> Path:
    content = source_runtime_manifest_path.read_bytes()
    content_hash = hashlib.sha256(content).hexdigest()[:16]
    run_hash = hashlib.sha256(run_dir.as_posix().encode("utf-8")).hexdigest()[:16]
    snapshot_path = (
        repo_root
        / ".aware"
        / "node"
        / "direct-interface-local"
        / f"{run_hash}-{content_hash}"
        / "environment"
        / "runtime"
        / "environment.manifest.json"
    ).resolve()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(content)
    return snapshot_path


def _resolve_experience_toml_paths(
    *,
    repo_root: Path,
    service_toml_paths: tuple[Path, ...],
    interface_package_name: str | None = None,
    experience_toml_paths: tuple[Path, ...],
) -> tuple[Path, ...]:
    raw_paths = experience_toml_paths
    if not raw_paths:
        required_experience_refs = tuple(
            sorted(
                {
                    *_service_required_experience_refs(
                        repo_root=repo_root,
                        service_toml_paths=service_toml_paths,
                    ),
                    *(
                        _interface_required_experience_refs(
                            repo_root=repo_root,
                            interface_package_name=interface_package_name,
                        )
                        if (interface_package_name or "").strip()
                        else ()
                    ),
                },
                key=str.casefold,
            )
        )
        if not required_experience_refs:
            return ()
        raw_paths = _experience_toml_paths_for_refs(
            repo_root=repo_root,
            experience_refs=required_experience_refs,
        )
    resolved: list[Path] = []
    for raw_path in raw_paths:
        path = raw_path.expanduser()
        if not path.is_absolute():
            path = repo_root / path
        resolved_path = path.resolve()
        if not resolved_path.is_file():
            raise FileNotFoundError(f"Experience TOML does not exist: {resolved_path}")
        if resolved_path not in resolved:
            resolved.append(resolved_path)
    return tuple(resolved)


def _service_required_experience_refs(
    *,
    repo_root: Path,
    service_toml_paths: tuple[Path, ...],
) -> tuple[str, ...]:
    from aware_service_runtime.compile import compile_service_workspace

    refs: set[str] = set()
    for service_toml_path in service_toml_paths:
        compile_result = compile_service_workspace(
            toml_path=service_toml_path,
            repo_root=repo_root,
            emit_compile_plan=False,
        )
        compile_plan = compile_result.compile_plan
        if compile_plan is None:
            continue
        for service_config in compile_plan.service_configs:
            refs.update(
                experience.experience_ref.strip()
                for experience in service_config.experiences
                if experience.experience_ref.strip()
            )
            refs.update(
                contract_config.projection_experience_ref.strip()
                for contract_config in service_config.contract_configs
                if contract_config.projection_experience_ref is not None
                and contract_config.projection_experience_ref.strip()
            )
    return tuple(sorted(refs, key=str.casefold))


def _interface_required_experience_refs(
    *,
    repo_root: Path,
    interface_package_name: str,
) -> tuple[str, ...]:
    from aware_interface.manifest.interface_spec import AwareInterfaceDependencyKind
    from aware_interface.manifest.loader import load_aware_interface_toml_spec

    interface_toml_path = _interface_toml_path_for_package(
        repo_root=repo_root,
        interface_package_name=interface_package_name,
    )
    spec = load_aware_interface_toml_spec(toml_path=interface_toml_path)
    return tuple(
        sorted(
            {
                dependency.package_name.strip()
                for dependency in spec.dependencies
                if dependency.kind is AwareInterfaceDependencyKind.experience_package
                and dependency.package_name.strip()
            },
            key=str.casefold,
        )
    )


def _interface_toml_path_for_package(
    *,
    repo_root: Path,
    interface_package_name: str,
) -> Path:
    from aware_interface.manifest.loader import load_aware_interface_toml_spec

    package_key = (interface_package_name or "").strip().casefold()
    if not package_key:
        raise ValueError("interface_package_name is required")
    matches: list[Path] = []
    for toml_path in sorted((repo_root / "interfaces").glob("*/aware.interface.toml")):
        spec = load_aware_interface_toml_spec(toml_path=toml_path)
        if spec.interface.package_name.strip().casefold() == package_key:
            matches.append(toml_path.resolve())
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise RuntimeError(
            "Direct local Interface found multiple Interface TOMLs for package "
            f"{interface_package_name!r}: "
            + ", ".join(path.as_posix() for path in matches)
        )
    raise FileNotFoundError(
        "Direct local Interface could not resolve Interface TOML for package "
        f"{interface_package_name!r} under {repo_root / 'interfaces'}"
    )


def _experience_toml_paths_for_refs(
    *,
    repo_root: Path,
    experience_refs: tuple[str, ...],
) -> tuple[Path, ...]:
    refs_by_key = {ref.casefold(): ref for ref in experience_refs if ref.strip()}
    toml_paths_by_ref_key: dict[str, Path] = {}
    candidate_toml_paths = _candidate_experience_toml_paths(repo_root=repo_root)
    for toml_path in candidate_toml_paths:
        _record_experience_toml_ref_match(
            refs_by_key=refs_by_key,
            toml_paths_by_ref_key=toml_paths_by_ref_key,
            experience_name=_experience_package_name_for_toml(
                experience_toml_path=toml_path,
            ),
            toml_path=toml_path,
        )
    unresolved_ref_keys = refs_by_key.keys() - toml_paths_by_ref_key.keys()
    if unresolved_ref_keys:
        for toml_path in candidate_toml_paths:
            for experience_name in _projection_experience_names_for_toml(
                repo_root=repo_root,
                experience_toml_path=toml_path,
            ):
                _record_experience_toml_ref_match(
                    refs_by_key=refs_by_key,
                    toml_paths_by_ref_key=toml_paths_by_ref_key,
                    experience_name=experience_name,
                    toml_path=toml_path,
                )
            unresolved_ref_keys = refs_by_key.keys() - toml_paths_by_ref_key.keys()
            if not unresolved_ref_keys:
                break
    missing = tuple(
        ref
        for key, ref in sorted(refs_by_key.items())
        if key not in toml_paths_by_ref_key
    )
    if missing:
        raise RuntimeError(
            "Direct local Interface could not resolve local Experience TOMLs for "
            "service/interface experience refs: "
            + ", ".join(repr(ref) for ref in missing)
        )
    selected_paths = set(toml_paths_by_ref_key.values())
    pending_paths = list(selected_paths)
    while pending_paths:
        source_path = pending_paths.pop()
        for dependency_name in _experience_package_dependencies_for_toml(
            experience_toml_path=source_path,
        ):
            matches = tuple(
                path
                for path in candidate_toml_paths
                if (
                    _experience_package_name_for_toml(
                        experience_toml_path=path,
                    )
                    or ""
                ).casefold()
                == dependency_name.casefold()
            )
            if len(matches) != 1:
                reason = "was not found" if not matches else "resolved ambiguously"
                raise RuntimeError(
                    "Direct local Interface Experience dependency "
                    f"{reason}: package_name={dependency_name!r} "
                    f"source={source_path} matches="
                    f"{tuple(path.as_posix() for path in matches)}"
                )
            dependency_path = matches[0]
            if dependency_path in selected_paths:
                continue
            selected_paths.add(dependency_path)
            pending_paths.append(dependency_path)
    return tuple(
        sorted(
            selected_paths,
            key=lambda path: path.as_posix(),
        )
    )


def _record_experience_toml_ref_match(
    *,
    refs_by_key: Mapping[str, str],
    toml_paths_by_ref_key: dict[str, Path],
    experience_name: str | None,
    toml_path: Path,
) -> None:
    if experience_name is None:
        return
    normalized_experience_name = experience_name.strip()
    if not normalized_experience_name:
        return
    key = normalized_experience_name.casefold()
    if key not in refs_by_key:
        return
    existing = toml_paths_by_ref_key.get(key)
    resolved_toml_path = toml_path.resolve()
    if existing is not None and existing != resolved_toml_path:
        raise RuntimeError(
            "Direct local Interface found multiple Experience packages "
            f"for experience ref {refs_by_key[key]!r}: "
            f"{existing} and {resolved_toml_path}"
        )
    toml_paths_by_ref_key[key] = resolved_toml_path


def _candidate_experience_toml_paths(*, repo_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for pattern in DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            resolved = path.resolve()
            if resolved not in paths:
                paths.append(resolved)
    for path in _workspace_module_experience_toml_paths(repo_root=repo_root):
        resolved = path.resolve()
        if resolved not in paths:
            paths.append(resolved)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def _workspace_module_experience_toml_paths(*, repo_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    module_toml_paths = tuple(
        dict.fromkeys(
            (
                *sorted((repo_root / "modules").glob("*/aware.module.toml")),
                *sorted(
                    (repo_root / "workspaces").glob("*/modules/*/aware.module.toml")
                ),
            )
        )
    )
    for module_toml_path in module_toml_paths:
        try:
            payload = tomllib.loads(module_toml_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        packages = payload.get("packages")
        if not isinstance(packages, list):
            continue
        module_root = module_toml_path.parent
        for package in packages:
            if not isinstance(package, dict):
                continue
            if package.get("kind") != "experience":
                continue
            manifest = package.get("manifest")
            if not isinstance(manifest, str) or not manifest.strip():
                continue
            candidate = (module_root / manifest).resolve()
            if candidate.is_file() and candidate not in paths:
                paths.append(candidate)
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def _experience_package_name_for_toml(*, experience_toml_path: Path) -> str | None:
    payload = tomllib.loads(experience_toml_path.read_text(encoding="utf-8"))
    experience_payload = payload.get("experience")
    if not isinstance(experience_payload, dict):
        return None
    package_name = experience_payload.get("package_name")
    return package_name if isinstance(package_name, str) else None


def _experience_package_dependencies_for_toml(
    *, experience_toml_path: Path
) -> tuple[str, ...]:
    payload = tomllib.loads(experience_toml_path.read_text(encoding="utf-8"))
    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, list):
        return ()
    package_names: list[str] = []
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            continue
        if dependency.get("kind") != "experience_package":
            continue
        package_name = dependency.get("package_name")
        if not isinstance(package_name, str) or not package_name.strip():
            raise RuntimeError(
                "Direct local Interface Experience dependency requires "
                f"package_name: source={experience_toml_path}"
            )
        normalized = package_name.strip()
        if normalized not in package_names:
            package_names.append(normalized)
    return tuple(package_names)


def _projection_experience_names_for_toml(
    *,
    repo_root: Path,
    experience_toml_path: Path,
) -> tuple[str, ...]:
    from aware_experience.compiler import compile_experience_workspace
    from aware_experience.projection.compiler import (
        load_projection_experience_ownership_from_sources,
    )

    compile_result = compile_experience_workspace(
        toml_path=experience_toml_path,
        repo_root=repo_root,
    )
    ownership = load_projection_experience_ownership_from_sources(
        package_root=compile_result.snapshot.package_root,
        source_files=compile_result.snapshot.source_files,
    )
    return tuple(sorted({item.name for item in ownership}, key=str.casefold))


def _ensure_direct_local_network_node_info(
    *,
    node_root: Path,
    host: str,
    port: int,
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
                "Direct local Interface could not read persisted node identity: "
                + info_path.as_posix()
            ) from exc
        info = info.model_copy(
            update={
                "http_base_url": http_base_url,
                "label": info.label or "direct-interface-local",
                "requires_auth_interface_to_node": True,
            }
        )
    else:
        info = LocalNetworkNodeInfo(
            label="direct-interface-local",
            http_base_url=http_base_url,
            requires_auth_interface_to_node=True,
        )
    info = normalize_local_network_node_info_identity(info)
    info_path.write_text(info.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return info


def _root_environment_config_id(*, runtime_manifest_path: Path) -> UUID:
    try:
        payload = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            "Direct local Interface runtime auth could not read environment "
            f"manifest: {runtime_manifest_path}"
        ) from exc
    if not isinstance(payload, dict):
        raise RuntimeError(
            "Direct local Interface runtime auth requires a JSON object "
            f"environment manifest: {runtime_manifest_path}"
        )
    environment_payload = payload.get("environment")
    raw_id = (
        environment_payload.get("id")
        if isinstance(environment_payload, dict)
        else payload.get("environment_config_id")
    )
    raw_text = str(raw_id or "").strip()
    if not raw_text:
        raise RuntimeError(
            "Direct local Interface runtime auth could not resolve the root "
            "environment config id from " + runtime_manifest_path.as_posix()
        )
    return UUID(raw_text)


def _issue_direct_local_runtime_auth_token(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
    node_id: UUID,
    commit_store_root_path: Path,
) -> _IssuedRuntimeAuthToken:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass
    else:
        raise RuntimeError(
            "Direct local Interface runtime auth token issuance cannot run from "
            "an active event loop."
        )

    from aware_identity.auth.public_key.generator import (
        canonicalize_ed25519_public_key,
    )
    from aware_identity_ontology.identity.identity_enums import IdentityType
    from aware_identity_ontology.stable_ids import (
        stable_actor_id,
        stable_auth_token_registry_id,
        stable_identity_id,
    )
    from aware_environment.environment.identity import environment_id_for_config
    from aware_environment.stable_ids import (
        stable_boot_process_id,
        stable_boot_thread_id,
    )
    from aware_identity.handlers._generated import (
        meta_handlers as identity_meta_handlers,
    )
    from aware_identity_ontology.auth.auth_token_registry import (
        AuthTokenRegistry,
    )
    from aware_meta_service.local_sdk import (
        build_local_meta_sdk_session_for_aware_package_manifests,
    )

    environment_config_id = _root_environment_config_id(
        runtime_manifest_path=runtime_manifest_path,
    )
    environment_id = environment_id_for_config(
        node_id=node_id,
        environment_config_id=environment_config_id,
    )
    process_id = stable_boot_process_id(environment_id=environment_id)
    thread_id = stable_boot_thread_id(environment_id=environment_id)

    key_hex = "77" * 32
    public_key, _ = canonicalize_ed25519_public_key(f"ed25519:{key_hex}")
    identity_id = stable_identity_id(
        public_key=public_key,
        type=IdentityType.agent.value,
    )
    actor_id = stable_actor_id(identity_id=identity_id)
    registry_id = stable_auth_token_registry_id()
    token_id = uuid4()
    secret_b64url = (
        base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    )
    package_manifest_paths = _runtime_source_manifest_paths(
        repo_root=repo_root,
        runtime_manifest_path=runtime_manifest_path,
    )

    async def _issue(*, include_constructor: bool) -> object:
        meta_session = build_local_meta_sdk_session_for_aware_package_manifests(
            package_manifest_paths=package_manifest_paths,
            workspace_root=repo_root,
            aware_root=commit_store_root_path,
            composite_name="Aware Node Direct Local Auth Token",
            projection_name="AuthToken",
            actor_id=actor_id,
            branch_id=registry_id,
            generated_language_handler_module=identity_meta_handlers,
        )
        lane = meta_session.bind(
            projection="AuthToken",
            actor_id=actor_id,
            branch_id=registry_id,
        )
        with lane.activate(commit=True, publish=False):
            registry = (
                await AuthTokenRegistry.ensure_registry()
                if include_constructor
                else AuthTokenRegistry(id=registry_id)
            )
            return await registry.issue_apt_token(
                actor_id=actor_id,
                public_key=public_key,
                context_environment_id=environment_id,
                context_process_id=process_id,
                context_thread_id=thread_id,
                label="direct-interface-local",
                scopes=["interface:session", "agent:turn.execute"],
                token_id=token_id,
                secret_b64url=secret_b64url,
            )

    with _local_aware_root_env(commit_store_root_path, persistence_backend="fs"):
        try:
            payload = asyncio.run(_issue(include_constructor=True))
        except Exception as exc:
            if not _should_retry_runtime_auth_issue_without_constructor(exc):
                raise
            payload = asyncio.run(_issue(include_constructor=False))
    if not isinstance(payload, dict):
        raise RuntimeError("Direct local Interface runtime auth returned no token.")
    token = str(payload.get("token") or "").strip()
    if not token.startswith("aware_apt_"):
        raise RuntimeError(
            "Direct local Interface runtime auth returned invalid token."
        )
    return _IssuedRuntimeAuthToken(
        token=token,
        token_id=token_id,
        actor_id=actor_id,
        public_key=public_key,
        commit_store_root_path=commit_store_root_path,
        environment_config_id=environment_config_id,
        environment_id=environment_id,
        process_id=process_id,
        thread_id=thread_id,
    )


def _should_retry_runtime_auth_issue_without_constructor(exc: Exception) -> bool:
    message = str(exc)
    if "Lane already initialized" in message:
        return True
    if (
        "Expected exactly one FunctionConfig for local Meta SDK ORM lane" in message
        and "class='AuthTokenRegistry'" in message
        and "function='ensure_registry'" in message
        and "is_constructor=True" in message
        and "matches=0" in message
    ):
        return True
    return (
        "Cannot assemble append-ready changes for rejected mutations" in message
        and "Class instance mutation requires an invoked target object" in message
    )


def _runtime_source_manifest_paths(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
) -> tuple[Path, ...]:
    try:
        payload = json.loads(runtime_manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(
            "Unable to read direct local runtime manifest package list: "
            f"{runtime_manifest_path}"
        ) from exc
    packages = payload.get("packages") if isinstance(payload, Mapping) else None
    if not isinstance(packages, list):
        single_package_manifests = _single_package_source_manifest_paths(
            repo_root=repo_root,
            runtime_manifest_path=runtime_manifest_path,
        )
        if single_package_manifests:
            return single_package_manifests
        raise ValueError(
            "Direct local runtime manifest is missing packages list and is not "
            "inside a package .aware runtime directory: "
            f"{runtime_manifest_path}"
        )
    paths: list[Path] = []
    seen: set[Path] = set()
    for item in packages:
        if not isinstance(item, Mapping):
            continue
        raw_path = str(item.get("source_manifest_path") or "").strip()
        if not raw_path:
            continue
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = repo_root / path
        resolved = path.resolve()
        if resolved in seen:
            continue
        if not resolved.is_file():
            raise ValueError(
                "Direct local Interface runtime manifest references a missing "
                f"source manifest: {resolved}"
            )
        seen.add(resolved)
        paths.append(resolved)
    if not paths:
        raise ValueError(
            "Direct local Interface runtime manifest did not provide any source "
            f"package manifests: {runtime_manifest_path}"
        )
    return tuple(paths)


def _single_package_source_manifest_paths(
    *,
    repo_root: Path,
    runtime_manifest_path: Path,
) -> tuple[Path, ...]:
    for parent in runtime_manifest_path.resolve().parents:
        if parent.name != ".aware":
            continue
        source_manifest_path = (parent.parent / "aware.toml").resolve()
        if source_manifest_path == (repo_root.resolve() / "aware.toml"):
            return ()
        if not source_manifest_path.is_file():
            return ()
        from aware_meta.manifest.loader import load_aware_toml_spec
        from aware_meta.runtime.graph_context import (
            resolve_meta_runtime_package_manifest_closure_for_package_names,
        )

        spec = load_aware_toml_spec(toml_path=source_manifest_path)
        package_name = str(spec.package.package_name).strip()
        if not package_name:
            raise ValueError(
                "Direct local runtime manifest source package is missing "
                f"package_name: {source_manifest_path}"
            )
        return resolve_meta_runtime_package_manifest_closure_for_package_names(
            repo_root=repo_root,
            package_names=tuple(dict.fromkeys((package_name, "identity-ontology"))),
        )
    return ()


@contextmanager
def _local_aware_root_env(
    root: Path,
    *,
    persistence_backend: str,
) -> Iterator[Path]:
    resolved_root = root.expanduser().resolve()
    resolved_root.mkdir(parents=True, exist_ok=True)
    (resolved_root / ".aware").mkdir(parents=True, exist_ok=True)
    previous = {
        "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
        "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }
    os.environ["AWARE_ROOT"] = resolved_root.as_posix()
    os.environ["AWARE_PERSISTENCE_BACKEND"] = persistence_backend
    os.environ.pop("DATABASE_URL", None)
    try:
        yield resolved_root
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _write_token_authority_inputs_for_direct_local_node(
    *,
    repo_root: Path,
    auth_dir: Path,
    runtime_manifest_path: Path,
    auth_token: str | None,
    commit_store_root_path: Path | None = None,
) -> _TokenAuthorityInputResult:
    token = str(auth_token or "").strip()
    if not token:
        return _TokenAuthorityInputResult()

    try:
        from aware_identity_ontology.stable_ids import stable_auth_token_registry_id
    except (
        Exception
    ) as exc:  # pragma: no cover - import failure is environment-specific
        raise RuntimeError(
            "Direct local Interface auth authority input requires identity ontology "
            "stable ids to be importable."
        ) from exc

    projection_hash = (
        _resolve_auth_token_projection_hash(repo_root=repo_root)
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
        "source_kind": "local_manifest",
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
        "source_kind": "local_manifest",
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
    return _TokenAuthorityInputResult(
        token_authority_manifest_path=authority_manifest_path,
        token_seed_receipt_path=seed_receipt_path,
        auth_token_projection_hash=projection_hash,
    )


def _resolve_auth_token_projection_hash(*, repo_root: Path) -> str:
    opg_index_path = (repo_root / _IDENTITY_OPG_INDEX_RELATIVE_PATH).resolve()
    if not opg_index_path.is_file():
        raise RuntimeError(
            "Direct local Interface auth authority input could not find the "
            "Identity OPG index: " + opg_index_path.as_posix()
        )
    try:
        payload = json.loads(opg_index_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RuntimeError(
            "Direct local Interface auth authority input could not read the "
            "Identity OPG index: " + opg_index_path.as_posix()
        ) from exc
    entries = payload.get("entries")
    if not isinstance(entries, list):
        raise RuntimeError(
            "Direct local Interface auth authority input found an invalid "
            "Identity OPG index: " + opg_index_path.as_posix()
        )
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("model") or "").strip() != "AuthToken":
            continue
        projection_hash = str(entry.get("projection_hash") or "").strip()
        if projection_hash:
            return projection_hash
    raise RuntimeError(
        "Direct local Interface auth authority input could not resolve the "
        "AuthToken projection hash from " + opg_index_path.as_posix()
    )


def _node_env(
    *,
    repo_root: Path,
    node_run_manifest_path: Path,
    auth_token: str | None,
    interface_control_socket_path: Path,
    node_endpoint: str,
    interface_package_name: str,
    require_live_runtime: bool,
    allow_degraded_local_shell: bool,
    runtime_auth_actor_id: UUID | None = None,
) -> dict[str, str]:
    env: dict[str, str] = {}
    apply_node_run_manifest_env(node_run_manifest_path, environ=env)
    env["AWARE_REPO_ROOT"] = repo_root.as_posix()
    env["AWARE_NODE_BOOT_KERNEL"] = "1"
    env["AWARE_ENVIRONMENT_OIG_SYNC_MODE"] = "off"
    env["AWARE_INTERFACE_CONTROL_SOCKET"] = interface_control_socket_path.as_posix()
    env["AWARE_INTERFACE_SERVICE_ENDPOINT"] = node_endpoint
    env["AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME"] = interface_package_name
    env["AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME"] = (
        "1" if require_live_runtime else "0"
    )
    env["AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL"] = (
        "1" if allow_degraded_local_shell else "0"
    )
    if auth_token is not None:
        env["AWARE_AUTH_TOKEN"] = auth_token
    if runtime_auth_actor_id is not None:
        env["AWARE_INTERFACE_AUTH_ACTOR_ID"] = str(runtime_auth_actor_id)
        env["AWARE_NODE_RUNTIME_AUTH_ACTOR_ID"] = str(runtime_auth_actor_id)
    env.pop(_NODE_WORKSPACE_DEPLOYMENT_PAYLOAD_ENV, None)
    return dict(sorted(env.items()))


def _node_run_manifest_payload(
    *,
    repo_root: Path,
    run_dir: Path,
    node_package: str,
    node_root: Path,
    host: str,
    port: int,
    node_env_path: Path,
    node_command_path: Path,
    node_log_path: Path,
    service_host_config_path: Path,
    interface_host_config_path: Path,
    runtime_manifest_path: Path,
    token_authority_manifest_path: Path | None,
    token_seed_receipt_path: Path | None,
    service_api_dependency_refs_json: str,
    environment_port_ready_timeout_s: float,
    hosted_service_request_timeout_s: float,
) -> dict[str, object]:
    timeout_s = float(environment_port_ready_timeout_s)
    payload: dict[str, object] = {
        "version": NODE_RUN_MANIFEST_VERSION,
        "node_package": node_package,
        "host": host,
        "port": port,
        "node_base_url": f"http://{host}:{port}",
        "node_websocket_path": "/interface/network_node",
        "run_dir": run_dir.as_posix(),
        "aware_root": node_root.as_posix(),
        "node_host_root": repo_root.as_posix(),
        "env_file_path": node_env_path.as_posix(),
        "command_file_path": node_command_path.as_posix(),
        "log_path": node_log_path.as_posix(),
        "python_project_path": repo_root.as_posix(),
        "environment_provision_mode": "subprocess",
        "environment_manifest_path": runtime_manifest_path.as_posix(),
        "environment_service_port": port,
        "environment_api_endpoint": f"http://{host}:{port}",
        "hosted_services": [
            {
                "name": "local-service-host",
                "bootstrap_config_path": service_host_config_path.as_posix(),
                "launch_command": [
                    sys.executable,
                    "-m",
                    "aware_service_service",
                ],
            }
        ],
        "hosted_interfaces": [
            {
                "name": "local-interface-host",
                "bootstrap_config_path": interface_host_config_path.as_posix(),
                "launch_command": [
                    sys.executable,
                    "-m",
                    "aware_interface_service",
                ],
            }
        ],
        "route_inputs": {
            "service_api_dependency_package_refs_json": (
                service_api_dependency_refs_json
            ),
        },
        "readiness": {
            "node_http_ready_timeout_s": timeout_s,
            "environment_service_ready_timeout_s": timeout_s,
            "environment_ready_timeout_s": timeout_s,
            "hosted_service_ready_timeout_s": timeout_s,
            "hosted_interface_ready_timeout_s": timeout_s,
            "hosted_service_request_timeout_s": float(hosted_service_request_timeout_s),
        },
        "provenance": {
            "source_kind": "local_manifest",
            "workspace_root": repo_root.as_posix(),
        },
    }
    if token_authority_manifest_path is not None:
        payload["auth_inputs"] = {
            "token_authority_manifest_path": (token_authority_manifest_path.as_posix()),
            "token_seed_receipt_path": (
                token_seed_receipt_path.as_posix()
                if token_seed_receipt_path is not None
                else None
            ),
        }
    return payload


def _service_api_dependency_package_refs_json_from_tomls(
    *,
    service_toml_paths: tuple[Path, ...],
) -> str:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec
    from aware_service_runtime.manifest.spec import AwareServiceDependencyKind
    from aware_api_ontology.stable_ids import stable_api_package_id
    from aware_service_ontology.stable_ids import stable_service_package_id

    refs: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for service_toml_path in service_toml_paths:
        resolved_path = service_toml_path.expanduser().resolve()
        spec = load_aware_service_toml_spec(toml_path=resolved_path)
        package_name = spec.service.package_name.strip()
        key = (package_name.casefold(), resolved_path.as_posix())
        if key in seen:
            continue
        seen.add(key)
        dependencies = tuple(
            _service_toml_dependency_payload(dependency)
            for dependency in spec.dependencies
        )
        refs.append(
            {
                "family_key": "service",
                "package_kind": "service",
                "package_name": package_name,
                "service_package_id": str(stable_service_package_id(name=package_name)),
                "dependencies": list(dependencies),
                "provided_api_packages": [
                    {
                        "api_package_id": str(
                            stable_api_package_id(name=str(dependency["package_name"]))
                        ),
                        "api_package_name": dependency["package_name"],
                    }
                    for dependency in dependencies
                    if dependency["kind"]
                    == AwareServiceDependencyKind.api_service_protocol.value
                ],
                "required_api_packages": [
                    {
                        "api_package_id": str(
                            stable_api_package_id(name=str(dependency["package_name"]))
                        ),
                        "api_package_name": dependency["package_name"],
                    }
                    for dependency in dependencies
                    if dependency["kind"]
                    == AwareServiceDependencyKind.api_invocation.value
                ],
            }
        )
    refs.sort(key=lambda item: str(item["package_name"]).casefold())
    return json.dumps(refs, sort_keys=True)


def _service_host_ontology_replica_db_paths(
    *,
    service_dir: Path,
    service_toml_paths: tuple[Path, ...],
) -> tuple[Path | None, Path | None]:
    if not _service_tomls_require_ontology_replica(
        service_toml_paths=service_toml_paths
    ):
        return None, None
    replica_dir = (service_dir / "ontology-replica").resolve()
    return (
        (replica_dir / "state.sqlite").resolve(),
        (replica_dir / "projection.sqlite").resolve(),
    )


def _service_tomls_require_ontology_replica(
    *,
    service_toml_paths: tuple[Path, ...],
) -> bool:
    from aware_service_runtime.manifest.loader import load_aware_service_toml_spec

    for service_toml_path in dict.fromkeys(service_toml_paths):
        spec = load_aware_service_toml_spec(
            toml_path=service_toml_path.expanduser().resolve()
        )
        for ontology_package in spec.ontology_packages:
            if (
                str(ontology_package.role or "").strip() == "replica"
                and str(ontology_package.requirement_mode or "required").strip()
                == "required"
            ):
                return True
    return False


def _service_toml_dependency_payload(dependency: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "package_name": str(getattr(dependency, "package_name")).strip(),
        "kind": str(getattr(getattr(dependency, "kind"), "value", dependency.kind)),
    }
    version_number = getattr(dependency, "version_number", None)
    if version_number is not None:
        payload["version_number"] = version_number
    expected_hash_sha256 = getattr(dependency, "expected_hash_sha256", None)
    if expected_hash_sha256 is not None:
        payload["expected_hash_sha256"] = expected_hash_sha256
    route_authority_selector = getattr(dependency, "route_authority_selector", None)
    if route_authority_selector is not None:
        selector_payload = route_authority_selector.to_payload()
        if selector_payload:
            payload["route_authority_selector"] = selector_payload
    return payload


def _service_host_toml(
    *,
    socket_path: Path,
    runtime_manifest_path: Path | None,
    service_toml_paths: tuple[Path, ...],
    experience_toml_paths: tuple[Path, ...],
    environment_api_endpoint: str | None,
    environment_api_request_timeout_s: float | None = None,
    kernel_repo_root: Path | None = None,
    artifact_root: Path | None = None,
    ontology_authority_package_names: tuple[str, ...] = (),
    ontology_authority_source_kind: str | None = None,
    ontology_authority_root: Path | None = None,
    ontology_replica_state_db_path: Path | None = None,
    ontology_replica_projection_db_path: Path | None = None,
    service_package_refs: tuple[ServiceHostImplementationPackageRefInput, ...] = (),
) -> str:
    if service_toml_paths and service_package_refs:
        raise ValueError(
            "ServiceHost bootstrap cannot combine implementation TOML paths "
            "with committed implementation package refs."
        )
    toml_paths = ", ".join(_toml_string(path.as_posix()) for path in service_toml_paths)
    experience_paths = ", ".join(
        _toml_string(path.as_posix()) for path in experience_toml_paths
    )
    implementation_lines = ["[implementation_packages]"]
    if service_toml_paths:
        implementation_lines.append(f"toml_paths = [{toml_paths}]")
    elif not service_package_refs:
        implementation_lines.append("toml_paths = []")
    if implementation_lines:
        implementation_lines.append("")
    package_ref_lines = _service_package_ref_toml_lines(service_package_refs)
    reference_package_lines = (
        [
            "[reference_packages]",
            f"experience_toml_paths = [{experience_paths}]",
            "",
        ]
        if experience_toml_paths
        else []
    )
    authority_package_names = tuple(
        dict.fromkeys(
            name.strip() for name in ontology_authority_package_names if name.strip()
        )
    )
    ontology_authority_lines: list[str] = []
    authority_source_kind = str(ontology_authority_source_kind or "").strip()
    if authority_package_names:
        ontology_authority_lines.append("[ontology_authority]")
        if authority_source_kind:
            ontology_authority_lines.append(
                f"source_kind = {_toml_string(authority_source_kind)}"
            )
        if ontology_authority_root is not None:
            ontology_authority_lines.append(
                f"root = {_toml_string(ontology_authority_root.as_posix())}"
            )
        ontology_authority_lines.append(
            "package_names = ["
            + ", ".join(_toml_string(name) for name in authority_package_names)
            + "]"
        )
        ontology_authority_lines.append("")
    app_lines = ["[app]"]
    if runtime_manifest_path is not None:
        app_lines.append(
            "runtime_manifest_path = "
            f"{_toml_string(runtime_manifest_path.as_posix())}"
        )
    if kernel_repo_root is not None:
        app_lines.append(
            f"kernel_repo_root = {_toml_string(kernel_repo_root.as_posix())}"
        )
    app_lines.append("")
    artifact_lines = (
        [
            "[artifact]",
            f"root = {_toml_string(artifact_root.as_posix())}",
            "",
        ]
        if artifact_root is not None
        else []
    )
    environment_lines: list[str] = []
    if environment_api_endpoint is not None:
        environment_lines = [
            "[environment]",
            f"api_endpoint = {_toml_string(environment_api_endpoint)}",
        ]
        if environment_api_request_timeout_s is not None:
            timeout_s = float(environment_api_request_timeout_s)
            if timeout_s <= 0:
                raise ValueError(
                    "environment_api_request_timeout_s must be greater than 0."
                )
            environment_lines.append(f"request_timeout_s = {timeout_s:.6g}")
        environment_lines.append("")
    ontology_replica_lines: list[str] = []
    if (
        ontology_replica_state_db_path is not None
        or ontology_replica_projection_db_path is not None
    ):
        ontology_replica_lines.append("[ontology_replica]")
        if ontology_replica_state_db_path is not None:
            ontology_replica_lines.append(
                "state_db_path = "
                f"{_toml_string(ontology_replica_state_db_path.as_posix())}"
            )
        if ontology_replica_projection_db_path is not None:
            ontology_replica_lines.append(
                "projection_db_path = "
                f"{_toml_string(ontology_replica_projection_db_path.as_posix())}"
            )
        ontology_replica_lines.append("")
    return "\n".join(
        [
            *app_lines,
            *artifact_lines,
            "[ipc]",
            f"socket_path = {_toml_string(socket_path.as_posix())}",
            "",
            *implementation_lines,
            *package_ref_lines,
            *reference_package_lines,
            *ontology_authority_lines,
            *ontology_replica_lines,
            *environment_lines,
        ]
    )


def _service_package_ref_toml_lines(
    refs: tuple[ServiceHostImplementationPackageRefInput, ...],
) -> list[str]:
    if not refs:
        return []
    lines: list[str] = []
    for ref in refs:
        payload = ref.to_payload()
        lines.append("[[implementation_packages.package_refs]]")
        for key in sorted(payload):
            lines.append(f"{key} = {_toml_string(payload[key])}")
        lines.append("")
    return lines


def _interface_host_toml(
    *,
    repo_root: Path,
    state_home: Path,
    namespace: str,
    endpoint: str,
    interface_package_name: str,
    require_live_runtime: bool,
    allow_degraded_local_shell: bool,
    service_host_config_path: Path,
) -> str:
    lines = [
        "[app]",
        f"repository_root = {_toml_string(repo_root.as_posix())}",
        f"state_home = {_toml_string(state_home.as_posix())}",
        f"namespace = {_toml_string(namespace)}",
        'host_label = "direct-node-interface"',
        f"endpoint = {_toml_string(endpoint)}",
        f"allow_degraded_local_shell = {_toml_bool(allow_degraded_local_shell)}",
        f"require_live_runtime = {_toml_bool(require_live_runtime)}",
        "",
        "[interface_package]",
        f"package_name = {_toml_string(interface_package_name)}",
    ]
    lines.extend(
        [
            "",
            "[local_service_host]",
            "bootstrap_config_path = "
            f"{_toml_string(service_host_config_path.as_posix())}",
            "",
        ]
    )
    return "\n".join(lines)


def _env_text(env: Mapping[str, str]) -> str:
    return (
        "\n".join(f"{key}={shlex.quote(value)}" for key, value in sorted(env.items()))
        + "\n"
    )


def _node_command_text(
    *,
    env_path: Path,
    node_command: tuple[str, ...],
    repo_root: Path,
    log_path: Path,
) -> str:
    command = " ".join(shlex.quote(part) for part in node_command)
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            f"set -a; source {shlex.quote(env_path.as_posix())}; set +a",
            f"cd {shlex.quote(repo_root.as_posix())}",
            f"exec {command} >> {shlex.quote(log_path.as_posix())} 2>&1",
            "",
        ]
    )


def _redacted_env(env: Mapping[str, str]) -> dict[str, str]:
    redacted = dict(env)
    for key in ("AWARE_AUTH_TOKEN", "AWARE_APT_TOKEN"):
        if key in redacted:
            redacted[key] = "<redacted>"
    return redacted


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"


def _required_text(value: str, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required.")
    return text


def _receipt_name(value: str) -> str:
    return "".join(char if char.isalnum() or char in "-_." else "_" for char in value)


__all__ = [
    "DEFAULT_DIRECT_INTERFACE_LOCAL_HANDLE",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_HOST",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_INTERFACE_PACKAGE",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_NAMESPACE",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_NODE_PACKAGE",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_PORT",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOB",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_EXPERIENCE_TOML_GLOBS",
    "DEFAULT_DIRECT_INTERFACE_LOCAL_SERVICE_TOMLS",
    "DirectInterfaceLocalBootstrapPlan",
    "DirectInterfaceLocalBootstrapRequest",
    "prepare_direct_interface_local_bootstrap",
]
