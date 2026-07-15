from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import time
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from aware_code.types import JsonObject
from aware_comms import DuplexIpcEndpoint
from aware_service_runtime.contracts import (
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceHostHandshakeRequest,
)
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_runtime.local_service_host_api_client import (
    LocalServiceHostAwareApiClient,
)

if TYPE_CHECKING:
    from aware_ontology_service_api import AwareOntologyServiceApiClient
    from aware_service_service.app import ServiceHostApp


DEFAULT_SOCKET_RELATIVE_PATH = Path(".aware/services/ontology/ontology-service.sock")
DEFAULT_READY_RELATIVE_PATH = Path(
    ".aware/services/ontology/ontology-service.ready.json"
)
DEFAULT_STATE_ROOT_RELATIVE_PATH = Path(".aware/services/ontology/state")
DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH = Path(
    "workspaces/aware_network/modules/ontology/services/ontology/aware.service.toml"
)
DEFAULT_API_CLIENT_ENDPOINT = "aware-service-host://aware-ontology-service-local"
LOCAL_ENVIRONMENT_API_ENDPOINT = "aware-environment-service://local"

ONTOLOGY_API_SERVICE_NAME = "aware_ontology"
ONTOLOGY_API_ENDPOINT_REFS = {
    "get_lane_head": "ontology.graph.get_lane_head",
    "get_object_instance_graph_commit": (
        "ontology.graph.get_object_instance_graph_commit"
    ),
    "invoke_function": "ontology.graph.invoke_function",
    "resolve_projection": "ontology.graph.resolve_projection",
    "ensure_object_config_graph_package": (
        "ontology.package.ensure_object_config_graph_package"
    ),
    "ensure_ready": "ontology.persistence.ensure_ready",
    "subscribe": "ontology.commit.subscribe",
}
_AWARE_REPO_ROOT_ENV = "AWARE_REPO_ROOT"


@dataclass(frozen=True, slots=True)
class LocalOntologyServiceHostConfig:
    repo_root: Path
    socket_path: Path
    implementation_toml_paths: tuple[Path, ...]
    runtime_manifest_path: Path | None
    environment_api_endpoint: str | None
    ready_file_path: Path | None
    state_root_path: Path | None

    @property
    def endpoint(self) -> DuplexIpcEndpoint:
        return DuplexIpcEndpoint.unix_socket(socket_path=str(self.socket_path))


def resolve_local_ontology_service_host_config(
    *,
    socket_path: str | Path | None = None,
    implementation_toml_paths: Sequence[str | Path] = (),
    runtime_manifest_path: str | Path | None = None,
    environment_api_endpoint: str | None = LOCAL_ENVIRONMENT_API_ENDPOINT,
    ready_file_path: str | Path | None = DEFAULT_READY_RELATIVE_PATH,
    state_root_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> LocalOntologyServiceHostConfig:
    root = _resolve_explicit_repo_root(repo_root)
    return LocalOntologyServiceHostConfig(
        repo_root=root,
        socket_path=_resolve_path(
            root=root,
            value=socket_path or DEFAULT_SOCKET_RELATIVE_PATH,
        ),
        implementation_toml_paths=tuple(
            _resolve_path(root=root, value=value)
            for value in (
                implementation_toml_paths
                or (DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH,)
            )
        ),
        runtime_manifest_path=(
            _resolve_path(root=root, value=runtime_manifest_path)
            if runtime_manifest_path is not None
            else None
        ),
        environment_api_endpoint=_clean_optional_text(environment_api_endpoint),
        ready_file_path=(
            _resolve_path(root=root, value=ready_file_path)
            if ready_file_path is not None
            else None
        ),
        state_root_path=(
            _resolve_path(root=root, value=state_root_path)
            if state_root_path is not None
            else None
        ),
    )


def _resolve_explicit_repo_root(repo_root: Path | None) -> Path:
    if repo_root is not None:
        return Path(repo_root).expanduser().resolve()
    raw_repo_root = (os.getenv(_AWARE_REPO_ROOT_ENV) or "").strip()
    if raw_repo_root:
        return Path(raw_repo_root).expanduser().resolve()
    raise RuntimeError(
        "local Ontology service host requires --repo-root, repo_root, or "
        f"{_AWARE_REPO_ROOT_ENV}; public kernel runtime must not discover "
        "repository roots"
    )


def build_local_ontology_service_host_app(
    *,
    config: LocalOntologyServiceHostConfig,
) -> ServiceHostApp:
    from aware_service_service.config import (
        ServiceHostAppConfig,
        ServiceHostEnvironmentConfig,
        ServiceHostImplementationPackageConfig,
    )

    return build_service_host_app(
        config=ServiceHostAppConfig(
            kernel_repo_root=config.repo_root,
            implementation_packages=ServiceHostImplementationPackageConfig(
                toml_paths=config.implementation_toml_paths,
            ),
            runtime_manifest_path=config.runtime_manifest_path,
            environment=ServiceHostEnvironmentConfig(
                api_endpoint=config.environment_api_endpoint,
            ),
        )
    )


def build_service_host_app(*, config: object) -> ServiceHostApp:
    from aware_service_service.environment_api_client import (
        build_service_host_app as _build_service_host_app,
    )

    return _build_service_host_app(config=cast(Any, config))


def build_local_ontology_service_host_duplex_client_factory(
    *,
    config: LocalOntologyServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    repo_root: Path | None = None,
) -> Callable[[], ServiceHostDuplexClient]:
    resolved_config = config or resolve_local_ontology_service_host_config(
        socket_path=socket_path,
        repo_root=repo_root,
    )
    endpoint = resolved_config.endpoint

    def _factory() -> ServiceHostDuplexClient:
        return ServiceHostDuplexClient(endpoint=endpoint)

    return _factory


def build_local_ontology_service_host_api_client(
    *,
    config: LocalOntologyServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    actor_id: UUID | None = None,
    endpoint: str = DEFAULT_API_CLIENT_ENDPOINT,
    request_timeout_s: float = 30.0,
    invocation_context: JsonObject | None = None,
    repo_root: Path | None = None,
) -> AwareOntologyServiceApiClient:
    """Build a generated Ontology API client backed by ServiceHost IPC."""

    from aware_ontology_service_api import AwareOntologyServiceApiClient

    return AwareOntologyServiceApiClient(
        client=LocalServiceHostAwareApiClient(
            actor_id=actor_id,
            client_factory=build_local_ontology_service_host_duplex_client_factory(
                config=config,
                socket_path=socket_path,
                repo_root=repo_root,
            ),
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            invocation_context=invocation_context,
        )
    )


async def serve_local_ontology_service_host(
    *,
    config: LocalOntologyServiceHostConfig,
    app: ServiceHostApp | None = None,
) -> dict[str, object]:
    return await _serve_local_ontology_service_host_in_active_state(
        config=config,
        app=app,
    )


async def _serve_local_ontology_service_host_in_active_state(
    *,
    config: LocalOntologyServiceHostConfig,
    app: ServiceHostApp | None = None,
) -> dict[str, object]:
    from aware_service_service.ipc import ServiceHostIpcServer

    serve_started_at_epoch_s = time.time()
    serve_started = time.perf_counter()
    app = app or build_local_ontology_service_host_app(config=config)
    server = ServiceHostIpcServer(app=app, endpoint=config.endpoint)
    server_start_started = time.perf_counter()
    loaded_services = await server.start()
    server_start_duration_s = _duration_since(server_start_started)
    ready_payload = _build_ready_payload(
        config=config,
        loaded_services=loaded_services,
        process_id=os.getpid(),
        serve_started_at_epoch_s=serve_started_at_epoch_s,
        server_start_duration_s=server_start_duration_s,
        ready_duration_s=_duration_since(serve_started),
    )
    _write_ready_file(config=config, payload=ready_payload)
    print(json.dumps(ready_payload, sort_keys=True), flush=True)
    try:
        await _wait_for_shutdown_signal()
    finally:
        await server.close()
    return ready_payload


async def probe_local_ontology_service_host(
    *,
    socket_path: str | Path,
    timeout_s: float | None = 30.0,
) -> dict[str, object]:
    started = time.perf_counter()
    client = ServiceHostDuplexClient(
        endpoint=DuplexIpcEndpoint.unix_socket(socket_path=str(Path(socket_path)))
    )
    response = await client.send_handshake(
        request=ServiceHostHandshakeRequest(
            supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
        ),
        timeout_s=timeout_s,
    )
    return {
        "status": "succeeded",
        "duration_s": _duration_since(started),
        "host_id": response.host_id,
        "protocol_version": response.protocol_version,
        "readiness": {
            "is_ready": response.readiness.is_ready,
            "status": response.readiness.status.value,
            "reason": response.readiness.reason,
            "detail_payload": response.readiness.detail_payload,
        },
        "capabilities": [
            {
                "capability_id": item.capability_id,
                "state": item.state.value,
                "detail_payload": item.detail_payload,
            }
            for item in response.capabilities
        ],
    }


def _build_ready_payload(
    *,
    config: LocalOntologyServiceHostConfig,
    loaded_services: Sequence[str],
    process_id: int,
    serve_started_at_epoch_s: float,
    server_start_duration_s: float,
    ready_duration_s: float,
) -> dict[str, object]:
    return {
        "status": "ready",
        "service": ONTOLOGY_API_SERVICE_NAME,
        "pid": process_id,
        "socket_path": config.socket_path.as_posix(),
        "ready_file_path": (
            config.ready_file_path.as_posix()
            if config.ready_file_path is not None
            else None
        ),
        "state_root_path": (
            config.state_root_path.as_posix()
            if config.state_root_path is not None
            else None
        ),
        "implementation_toml_paths": [
            path.as_posix() for path in config.implementation_toml_paths
        ],
        "runtime_manifest_path": (
            config.runtime_manifest_path.as_posix()
            if config.runtime_manifest_path is not None
            else None
        ),
        "environment_api_endpoint": config.environment_api_endpoint,
        "loaded_services": list(loaded_services),
        "started_at_epoch_s": serve_started_at_epoch_s,
        "timings": {
            "server_start_duration_s": server_start_duration_s,
            "ready_duration_s": ready_duration_s,
        },
    }


def _write_ready_file(
    *,
    config: LocalOntologyServiceHostConfig,
    payload: dict[str, object],
) -> None:
    if config.ready_file_path is None:
        return
    config.ready_file_path.parent.mkdir(parents=True, exist_ok=True)
    config.ready_file_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _resolve_path(*, root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _clean_optional_text(value: str | None) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned or None


def _duration_since(started: float) -> float:
    return time.perf_counter() - started


async def _wait_for_shutdown_signal() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _stop() -> None:
        stop_event.set()

    registered: list[signal.Signals] = []
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _stop)
            registered.append(sig)
        except (NotImplementedError, RuntimeError):  # pragma: no cover
            pass
    try:
        await stop_event.wait()
    finally:
        for sig in registered:
            loop.remove_signal_handler(sig)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m aware_ontology_service.local_host")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--repo-root", type=Path, default=None)
    serve_parser.add_argument("--socket-path", type=Path, default=None)
    serve_parser.add_argument("--ready-file-path", type=Path, default=None)
    serve_parser.add_argument("--state-root-path", type=Path, default=None)
    serve_parser.add_argument(
        "--disable-environment-api-endpoint",
        action="store_true",
    )

    probe_parser = subparsers.add_parser("probe")
    probe_parser.add_argument("--socket-path", type=Path, default=None)
    probe_parser.add_argument("--repo-root", type=Path, default=None)
    probe_parser.add_argument("--timeout-s", type=float, default=30.0)

    args = parser.parse_args(argv)
    if args.command == "serve":
        config = resolve_local_ontology_service_host_config(
            repo_root=args.repo_root,
            socket_path=args.socket_path,
            ready_file_path=args.ready_file_path or DEFAULT_READY_RELATIVE_PATH,
            state_root_path=args.state_root_path,
            environment_api_endpoint=(
                None
                if args.disable_environment_api_endpoint
                else LOCAL_ENVIRONMENT_API_ENDPOINT
            ),
        )
        asyncio.run(serve_local_ontology_service_host(config=config))
        return 0
    if args.command == "probe":
        config = resolve_local_ontology_service_host_config(
            repo_root=args.repo_root,
            socket_path=args.socket_path,
        )
        payload = asyncio.run(
            probe_local_ontology_service_host(
                socket_path=config.socket_path,
                timeout_s=args.timeout_s,
            )
        )
        print(json.dumps(payload, sort_keys=True))
        return 0
    parser.error(f"Unsupported command: {args.command}")
    return 2


__all__ = [
    "DEFAULT_API_CLIENT_ENDPOINT",
    "DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_READY_RELATIVE_PATH",
    "DEFAULT_SOCKET_RELATIVE_PATH",
    "DEFAULT_STATE_ROOT_RELATIVE_PATH",
    "LOCAL_ENVIRONMENT_API_ENDPOINT",
    "ONTOLOGY_API_ENDPOINT_REFS",
    "ONTOLOGY_API_SERVICE_NAME",
    "LocalOntologyServiceHostConfig",
    "build_local_ontology_service_host_api_client",
    "build_local_ontology_service_host_app",
    "build_local_ontology_service_host_duplex_client_factory",
    "probe_local_ontology_service_host",
    "resolve_local_ontology_service_host_config",
    "serve_local_ontology_service_host",
]


if __name__ == "__main__":
    raise SystemExit(main())
