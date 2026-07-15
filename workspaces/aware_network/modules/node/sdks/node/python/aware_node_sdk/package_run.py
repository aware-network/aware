from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


DEFAULT_NODE_PACKAGE_LOCAL_HANDLE = "kernel-environment-host"
DEFAULT_NODE_PACKAGE_LOCAL_HOST = "127.0.0.1"
DEFAULT_NODE_PACKAGE_LOCAL_PORT = 8911
DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S = 30.0


class NodePackageRunBackend(Protocol):
    def prepare_local_node_package_run(
        self,
        request: NodePackageRunPrepareLocalRequest,
    ) -> object: ...


@dataclass(frozen=True, slots=True)
class NodePackageRunPrepareLocalRequest:
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
class NodePackageRunPreparation:
    payload: Mapping[str, object]
    run_dir: Path
    node_run_manifest_path: Path
    node_operator_pid_path: Path
    node_log_path: Path
    node_host: str
    node_port: int

    @classmethod
    def from_backend_plan(cls, plan: object) -> NodePackageRunPreparation:
        payload = _payload_from_plan(plan)
        return cls(
            payload=payload,
            run_dir=_path_attr(plan, payload, "run_dir"),
            node_run_manifest_path=_path_attr(
                plan,
                payload,
                "node_run_manifest_path",
            ),
            node_operator_pid_path=_path_attr(
                plan,
                payload,
                "node_operator_pid_path",
            ),
            node_log_path=_path_attr(plan, payload, "node_log_path"),
            node_host=_text_attr(plan, payload, "node_host"),
            node_port=int(_value_attr(plan, payload, "node_port")),
        )

    def to_payload(self) -> dict[str, object]:
        return dict(self.payload)


@dataclass(frozen=True, slots=True)
class NodePackageRunClient:
    backend: NodePackageRunBackend | None = None

    def prepare_local_node_package_run(
        self,
        request: NodePackageRunPrepareLocalRequest,
    ) -> NodePackageRunPreparation:
        backend = self.backend or _ServiceNodePackageRunBackend()
        plan = backend.prepare_local_node_package_run(request)
        return NodePackageRunPreparation.from_backend_plan(plan)


class _ServiceNodePackageRunBackend:
    def prepare_local_node_package_run(
        self,
        request: NodePackageRunPrepareLocalRequest,
    ) -> object:
        try:
            from aware_node_operator.node_package_run_manifest import (
                NodeOntologyLocalBootstrapRequest,
                prepare_node_ontology_local_bootstrap,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Local Node package-run preparation requires the "
                "`aware-node-operator` package. Install `aware-node-sdk[local]` "
                "or run inside the Aware workspace."
            ) from exc

        return prepare_node_ontology_local_bootstrap(
            NodeOntologyLocalBootstrapRequest(
                repo_root=request.repo_root,
                node_toml_path=request.node_toml_path,
                run_dir=request.run_dir,
                workspace_root=request.workspace_root,
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
                environment_port_ready_timeout_s=(
                    request.environment_port_ready_timeout_s
                ),
                hosted_service_request_timeout_s=(
                    request.hosted_service_request_timeout_s
                ),
            )
        )


def _payload_from_plan(plan: object) -> Mapping[str, object]:
    to_payload = getattr(plan, "to_payload", None)
    if callable(to_payload):
        payload = to_payload()
        if isinstance(payload, Mapping):
            return payload
    raise TypeError(
        "Node package-run backend returned a plan without a mapping to_payload()."
    )


def _path_attr(plan: object, payload: Mapping[str, object], name: str) -> Path:
    value = _value_attr(plan, payload, name)
    if isinstance(value, Path):
        return value
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"Node package-run preparation missing {name}.")
    return Path(text)


def _text_attr(plan: object, payload: Mapping[str, object], name: str) -> str:
    text = str(_value_attr(plan, payload, name) or "").strip()
    if not text:
        raise ValueError(f"Node package-run preparation missing {name}.")
    return text


def _value_attr(plan: object, payload: Mapping[str, object], name: str) -> object:
    value = getattr(plan, name, None)
    if value is not None:
        return value
    return payload.get(name)


__all__ = [
    "DEFAULT_NODE_PACKAGE_LOCAL_HANDLE",
    "DEFAULT_NODE_PACKAGE_LOCAL_HOST",
    "DEFAULT_NODE_PACKAGE_LOCAL_PORT",
    "DEFAULT_NODE_PACKAGE_HOSTED_SERVICE_REQUEST_TIMEOUT_S",
    "NodePackageRunBackend",
    "NodePackageRunClient",
    "NodePackageRunPreparation",
    "NodePackageRunPrepareLocalRequest",
]
