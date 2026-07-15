from __future__ import annotations

import argparse
import asyncio
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

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
    from aware_interface_service_api import AwareInterfaceServiceApiClient
    from aware_service_service.app import ServiceHostApp


DEFAULT_SOCKET_RELATIVE_PATH = Path(".aware/workspaces/aware_network/modules/interface/services/interface/interface-service.sock")
DEFAULT_READY_RELATIVE_PATH = Path(
    ".aware/workspaces/aware_network/modules/interface/services/interface/interface-service.ready.json"
)
DEFAULT_STATE_ROOT_RELATIVE_PATH = Path(".aware/workspaces/aware_network/modules/interface/services/interface/state")
DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH = Path("workspaces/aware_network/modules/interface/services/interface/aware.service.toml")
DEFAULT_API_CLIENT_ENDPOINT = "aware-service-host://aware-interface-service-local"
LOCAL_ENVIRONMENT_API_ENDPOINT = "aware-environment-service://local"
DEFAULT_OPERATOR_START_TIMEOUT_S = 60.0
DEFAULT_OPERATOR_PROBE_TIMEOUT_S = 2.0
DEFAULT_OPERATOR_STOP_TIMEOUT_S = 10.0

INTERFACE_API_SERVICE_NAME = "aware_interface"
LOCAL_INTERFACE_REPO_ROOT_ENV_VARS = (
    "AWARE_INTERFACE_SERVICE_REPO_ROOT",
    "AWARE_INTERFACE_SERVICE_REPOSITORY_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)
_META_EVENT_STORE_ROOT_ENV = "AWARE_META_SERVICE_EVENT_STORE_ROOT"
_META_EVENT_STORE_ROOT_RELATIVE_PATH = Path(".aware/meta/commit-events")


@dataclass(frozen=True, slots=True)
class LocalInterfaceServiceHostConfig:
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


@dataclass(frozen=True, slots=True)
class _LocalInterfaceServiceHostEnsureLock:
    path: Path


@contextmanager
def _isolated_interface_service_state(
    *,
    state_root_path: Path,
    persistence_backend: str = "fs",
) -> Iterator[Path]:
    root = state_root_path.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / ".aware").mkdir(parents=True, exist_ok=True)
    meta_event_store_root = root / _META_EVENT_STORE_ROOT_RELATIVE_PATH
    meta_event_store_root.mkdir(parents=True, exist_ok=True)
    previous = {
        "AWARE_ROOT": os.environ.get("AWARE_ROOT"),
        "AWARE_PERSISTENCE_BACKEND": os.environ.get("AWARE_PERSISTENCE_BACKEND"),
        _META_EVENT_STORE_ROOT_ENV: os.environ.get(_META_EVENT_STORE_ROOT_ENV),
        "DATABASE_URL": os.environ.get("DATABASE_URL"),
    }
    os.environ["AWARE_ROOT"] = str(root)
    os.environ["AWARE_PERSISTENCE_BACKEND"] = persistence_backend
    os.environ[_META_EVENT_STORE_ROOT_ENV] = str(meta_event_store_root)
    os.environ.pop("DATABASE_URL", None)
    try:
        yield root
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def resolve_local_interface_service_host_config(
    *,
    socket_path: str | Path | None = None,
    implementation_toml_paths: Sequence[str | Path] = (),
    runtime_manifest_path: str | Path | None = None,
    environment_api_endpoint: str | None = LOCAL_ENVIRONMENT_API_ENDPOINT,
    ready_file_path: str | Path | None = DEFAULT_READY_RELATIVE_PATH,
    state_root_path: str | Path | None = DEFAULT_STATE_ROOT_RELATIVE_PATH,
    repo_root: str | Path | None = None,
) -> LocalInterfaceServiceHostConfig:
    root = _resolve_repo_root(repo_root)
    resolved_implementation_tomls = tuple(
        _resolve_path(root=root, value=value)
        for value in (
            implementation_toml_paths or (DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH,)
        )
    )
    return LocalInterfaceServiceHostConfig(
        repo_root=root,
        socket_path=_resolve_path(
            root=root,
            value=socket_path or DEFAULT_SOCKET_RELATIVE_PATH,
        ),
        implementation_toml_paths=resolved_implementation_tomls,
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


def build_local_interface_service_host_app(
    *,
    config: LocalInterfaceServiceHostConfig,
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


def build_local_interface_service_host_duplex_client_factory(
    *,
    config: LocalInterfaceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> Callable[[], ServiceHostDuplexClient]:
    resolved_config = config or resolve_local_interface_service_host_config(
        socket_path=socket_path,
        repo_root=repo_root,
    )
    endpoint = resolved_config.endpoint

    def _factory() -> ServiceHostDuplexClient:
        return ServiceHostDuplexClient(endpoint=endpoint)

    return _factory


def build_local_interface_service_host_api_client(
    *,
    config: LocalInterfaceServiceHostConfig | None = None,
    socket_path: str | Path | None = None,
    actor_id: UUID | None = None,
    endpoint: str = DEFAULT_API_CLIENT_ENDPOINT,
    request_timeout_s: float = 30.0,
    invocation_context: Mapping[str, object] | None = None,
    repo_root: str | Path | None = None,
) -> AwareInterfaceServiceApiClient:
    """Build a generated Interface API client backed by ServiceHost IPC."""

    from aware_interface_service_api import AwareInterfaceServiceApiClient

    return AwareInterfaceServiceApiClient(
        client=LocalServiceHostAwareApiClient(
            actor_id=actor_id,
            client_factory=build_local_interface_service_host_duplex_client_factory(
                config=config,
                socket_path=socket_path,
                repo_root=repo_root,
            ),
            endpoint=endpoint,
            request_timeout_s=request_timeout_s,
            invocation_context=cast(Any, invocation_context),
        )
    )


async def serve_local_interface_service_host(
    *,
    config: LocalInterfaceServiceHostConfig,
    app: ServiceHostApp | None = None,
) -> dict[str, object]:
    if config.state_root_path is None:
        return await _serve_local_interface_service_host_in_active_state(
            config=config,
            app=app,
        )

    with _isolated_interface_service_state(state_root_path=config.state_root_path):
        return await _serve_local_interface_service_host_in_active_state(
            config=config,
            app=app,
        )


async def _serve_local_interface_service_host_in_active_state(
    *,
    config: LocalInterfaceServiceHostConfig,
    app: ServiceHostApp | None = None,
) -> dict[str, object]:
    serve_started_at_epoch_s = time.time()
    serve_started = time.perf_counter()
    server_ipc_import_started = time.perf_counter()
    from aware_service_service.ipc import ServiceHostIpcServer

    server_ipc_import_duration_s = _duration_since(server_ipc_import_started)
    app_build_started = time.perf_counter()
    app = app or build_local_interface_service_host_app(config=config)
    app_build_duration_s = _duration_since(app_build_started)
    server_construct_started = time.perf_counter()
    server = ServiceHostIpcServer(app=app, endpoint=config.endpoint)
    server_construct_duration_s = _duration_since(server_construct_started)
    server_start_started = time.perf_counter()
    loaded_services = await server.start()
    server_start_duration_s = _duration_since(server_start_started)
    ready_payload_build_started = time.perf_counter()
    ready_payload = _build_ready_payload(
        config=config,
        app=app,
        loaded_services=loaded_services,
        process_id=os.getpid(),
        serve_started_at_epoch_s=serve_started_at_epoch_s,
        server_ipc_import_duration_s=server_ipc_import_duration_s,
        app_build_duration_s=app_build_duration_s,
        server_construct_duration_s=server_construct_duration_s,
        server_start_duration_s=server_start_duration_s,
        server_start_phase_timings_s=server.startup_phase_timings_s,
        ready_payload_build_duration_s=None,
        ready_duration_s=_duration_since(serve_started),
    )
    ready_payload_build_duration_s = _duration_since(ready_payload_build_started)
    cast(dict[str, object], ready_payload["timings"])[
        "ready_payload_build_duration_s"
    ] = ready_payload_build_duration_s
    _write_ready_file(config=config, payload=ready_payload)
    print(json.dumps(ready_payload, sort_keys=True), flush=True)
    try:
        await _wait_for_shutdown_signal()
    finally:
        await server.close()
    return ready_payload


async def inspect_local_interface_service_host(
    *,
    config: LocalInterfaceServiceHostConfig,
    timeout_s: float = DEFAULT_OPERATOR_PROBE_TIMEOUT_S,
) -> dict[str, object]:
    started = time.perf_counter()
    timings: dict[str, float] = {}
    paths_started = time.perf_counter()
    socket_exists = config.socket_path.exists()
    timings["path_probe_duration_s"] = _duration_since(paths_started)
    ready_read_started = time.perf_counter()
    ready_payload = _read_json_file(config.ready_file_path)
    timings["ready_file_read_duration_s"] = _duration_since(ready_read_started)
    pid_read_started = time.perf_counter()
    pid_payload = _read_json_file(local_interface_service_host_pid_file_path(config))
    timings["pid_file_read_duration_s"] = _duration_since(pid_read_started)
    handshake_payload: dict[str, object] | None = None
    error: str | None = None

    if socket_exists:
        handshake_started = time.perf_counter()
        try:
            response = await _build_service_host_duplex_client(
                endpoint=config.endpoint
            ).send_handshake(
                request=ServiceHostHandshakeRequest(
                    supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,)
                ),
                timeout_s=timeout_s,
            )
            handshake_payload = {
                "host_id": response.host_id,
                "host_version": response.host_version,
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
            timings["handshake_duration_s"] = _duration_since(handshake_started)
        except Exception as exc:  # pragma: no cover - transport-specific detail.
            timings["handshake_duration_s"] = _duration_since(handshake_started)
            error = f"{exc.__class__.__name__}: {exc}"

    healthy = bool(
        handshake_payload
        and isinstance(handshake_payload.get("readiness"), dict)
        and cast(dict[str, object], handshake_payload["readiness"]).get("is_ready")
        is True
    )
    if healthy:
        status = "ready"
    elif handshake_payload is not None:
        status = "unhealthy"
    elif socket_exists or ready_payload is not None or pid_payload is not None:
        status = "stale"
    else:
        status = "missing"

    total_duration_s = _duration_since(started)
    timings["total_duration_s"] = total_duration_s
    return {
        "operation": "interface_service_host_status",
        "status": status,
        "healthy": healthy,
        "socket_exists": socket_exists,
        "ready_file_exists": ready_payload is not None,
        "pid_file_exists": pid_payload is not None,
        "paths": _local_interface_service_host_paths(config),
        "ready_payload": ready_payload,
        "pid_payload": pid_payload,
        "host": _local_interface_service_host_attach_metadata(
            config=config,
            ready_payload=ready_payload,
            pid_payload=pid_payload,
        ),
        "handshake": handshake_payload,
        "error": error,
        "timings": timings,
        "duration_s": total_duration_s,
    }


async def ensure_local_interface_service_host(
    *,
    config: LocalInterfaceServiceHostConfig,
    start_timeout_s: float = DEFAULT_OPERATOR_START_TIMEOUT_S,
    probe_timeout_s: float = DEFAULT_OPERATOR_PROBE_TIMEOUT_S,
    cleanup_stale: bool = True,
) -> dict[str, object]:
    started = time.perf_counter()
    timings: dict[str, float] = {}
    lock_wait_timeout_s = max(start_timeout_s, 0.0) + max(probe_timeout_s, 0.0) + 1.0
    lock_wait_started = time.perf_counter()
    lock = await _acquire_local_interface_service_host_ensure_lock(
        config=config,
        timeout_s=lock_wait_timeout_s,
    )
    timings["ensure_lock_wait_duration_s"] = _duration_since(lock_wait_started)
    if lock is None:
        timings["total_duration_s"] = _duration_since(started)
        return {
            "operation": "interface_service_host_ensure",
            "action": "lock_wait",
            "status": "lock_timeout",
            "healthy": False,
            "paths": _local_interface_service_host_paths(config),
            "lock_path": _local_interface_service_host_ensure_lock_path(
                config
            ).as_posix(),
            "timings": timings,
            "duration_s": timings["total_duration_s"],
        }
    try:
        return await _ensure_local_interface_service_host_locked(
            config=config,
            start_timeout_s=start_timeout_s,
            probe_timeout_s=probe_timeout_s,
            cleanup_stale=cleanup_stale,
            started=started,
            timings=timings,
        )
    finally:
        _release_local_interface_service_host_ensure_lock(lock)


async def _ensure_local_interface_service_host_locked(
    *,
    config: LocalInterfaceServiceHostConfig,
    start_timeout_s: float,
    probe_timeout_s: float,
    cleanup_stale: bool,
    started: float,
    timings: dict[str, float],
) -> dict[str, object]:
    inspect_started = time.perf_counter()
    before = await inspect_local_interface_service_host(
        config=config,
        timeout_s=probe_timeout_s,
    )
    timings["inspect_before_duration_s"] = _duration_since(inspect_started)
    if before.get("healthy") is True:
        timings["total_duration_s"] = _duration_since(started)
        return {
            "operation": "interface_service_host_ensure",
            "action": "reused",
            "status": "ready",
            "healthy": True,
            "paths": _local_interface_service_host_paths(config),
            "before": before,
            "after": before,
            "timings": timings,
            "duration_s": timings["total_duration_s"],
        }

    pending_pid = _live_matching_pid_from_service_host_status(
        status=before,
        config=config,
    )
    if pending_pid is not None:
        pending_wait_started = time.perf_counter()
        deadline = time.perf_counter() + max(start_timeout_s, 0.0)
        after: dict[str, object] = before
        poll_count = 0
        latest_pid: int | None = pending_pid
        while time.perf_counter() <= deadline:
            poll_count += 1
            after = await inspect_local_interface_service_host(
                config=config,
                timeout_s=probe_timeout_s,
            )
            if after.get("healthy") is True:
                timings["pending_host_wait_duration_s"] = _duration_since(
                    pending_wait_started
                )
                timings["total_duration_s"] = _duration_since(started)
                return {
                    "operation": "interface_service_host_ensure",
                    "action": "reused_pending",
                    "status": "ready",
                    "healthy": True,
                    "pid": latest_pid,
                    "paths": _local_interface_service_host_paths(config),
                    "before": before,
                    "after": after,
                    "poll_count": poll_count,
                    "timings": timings,
                    "duration_s": timings["total_duration_s"],
                }
            latest_pid = _live_matching_pid_from_service_host_status(
                status=after,
                config=config,
            )
            if latest_pid is None:
                before = after
                break
            await asyncio.sleep(0.1)
        timings["pending_host_wait_duration_s"] = _duration_since(pending_wait_started)

    if cleanup_stale:
        cleanup_started = time.perf_counter()
        _cleanup_local_interface_service_host_artifacts(config=config)
        timings["cleanup_stale_duration_s"] = _duration_since(cleanup_started)

    process_start_started = time.perf_counter()
    process = _start_local_interface_service_host_process(config=config)
    timings["process_start_duration_s"] = _duration_since(process_start_started)
    command = _build_local_interface_service_host_serve_command(config=config)
    pid_write_started = time.perf_counter()
    _write_local_interface_service_host_pid_file(
        config=config,
        process=process,
        command=command,
    )
    timings["pid_file_write_duration_s"] = _duration_since(pid_write_started)

    deadline = time.perf_counter() + max(start_timeout_s, 0.0)
    after: dict[str, object] = before
    readiness_started = time.perf_counter()
    poll_count = 0
    while time.perf_counter() <= deadline:
        exit_code = process.poll()
        poll_count += 1
        after = await inspect_local_interface_service_host(
            config=config,
            timeout_s=probe_timeout_s,
        )
        if after.get("healthy") is True:
            timings["readiness_wait_duration_s"] = _duration_since(readiness_started)
            timings["total_duration_s"] = _duration_since(started)
            return {
                "operation": "interface_service_host_ensure",
                "action": "started",
                "status": "ready",
                "healthy": True,
                "pid": process.pid,
                "paths": _local_interface_service_host_paths(config),
                "before": before,
                "after": after,
                "poll_count": poll_count,
                "timings": timings,
                "duration_s": timings["total_duration_s"],
            }
        if exit_code is not None:
            timings["readiness_wait_duration_s"] = _duration_since(readiness_started)
            timings["total_duration_s"] = _duration_since(started)
            return {
                "operation": "interface_service_host_ensure",
                "action": "started",
                "status": "failed",
                "healthy": False,
                "pid": process.pid,
                "exit_code": exit_code,
                "paths": _local_interface_service_host_paths(config),
                "before": before,
                "after": after,
                "poll_count": poll_count,
                "timings": timings,
                "duration_s": timings["total_duration_s"],
            }
        await asyncio.sleep(0.1)

    timings["readiness_wait_duration_s"] = _duration_since(readiness_started)
    timings["total_duration_s"] = _duration_since(started)
    return {
        "operation": "interface_service_host_ensure",
        "action": "started",
        "status": "timeout",
        "healthy": False,
        "pid": process.pid,
        "paths": _local_interface_service_host_paths(config),
        "before": before,
        "after": after,
        "poll_count": poll_count,
        "timings": timings,
        "duration_s": timings["total_duration_s"],
    }


async def stop_local_interface_service_host(
    *,
    config: LocalInterfaceServiceHostConfig,
    timeout_s: float = DEFAULT_OPERATOR_STOP_TIMEOUT_S,
) -> dict[str, object]:
    started = time.perf_counter()
    timings: dict[str, float] = {}
    inspect_started = time.perf_counter()
    before = await inspect_local_interface_service_host(
        config=config,
        timeout_s=DEFAULT_OPERATOR_PROBE_TIMEOUT_S,
    )
    timings["inspect_before_duration_s"] = _duration_since(inspect_started)
    pid_path = local_interface_service_host_pid_file_path(config)
    pid_read_started = time.perf_counter()
    pid_payload = _read_json_file(pid_path)
    timings["pid_file_read_duration_s"] = _duration_since(pid_read_started)
    pid = _pid_from_payload(pid_payload)
    if pid is None:
        cleanup_started = time.perf_counter()
        _cleanup_local_interface_service_host_artifacts(config=config)
        timings["cleanup_duration_s"] = _duration_since(cleanup_started)
        timings["total_duration_s"] = _duration_since(started)
        return {
            "operation": "interface_service_host_stop",
            "action": "cleanup",
            "status": "not_running",
            "healthy": False,
            "paths": _local_interface_service_host_paths(config),
            "before": before,
            "termination": {"status": "missing_pid"},
            "timings": timings,
            "duration_s": timings["total_duration_s"],
        }

    if not _pid_payload_matches_config(pid_payload=pid_payload, config=config):
        timings["total_duration_s"] = _duration_since(started)
        return {
            "operation": "interface_service_host_stop",
            "action": "skipped",
            "status": "pid_mismatch",
            "healthy": False,
            "paths": _local_interface_service_host_paths(config),
            "before": before,
            "termination": {"status": "pid_mismatch", "pid": pid},
            "timings": timings,
            "duration_s": timings["total_duration_s"],
        }
    if not _process_id_matches_local_interface_service_host(pid, config=config):
        cleanup_started = time.perf_counter()
        _cleanup_local_interface_service_host_artifacts(config=config)
        timings["cleanup_duration_s"] = _duration_since(cleanup_started)
        timings["total_duration_s"] = _duration_since(started)
        return {
            "operation": "interface_service_host_stop",
            "action": "cleanup",
            "status": "not_running",
            "healthy": False,
            "paths": _local_interface_service_host_paths(config),
            "before": before,
            "termination": {"status": "stale_pid", "pid": pid},
            "timings": timings,
            "duration_s": timings["total_duration_s"],
        }

    terminate_started = time.perf_counter()
    termination = await asyncio.to_thread(_terminate_process_id, pid, timeout_s)
    timings["terminate_duration_s"] = _duration_since(terminate_started)
    cleanup_started = time.perf_counter()
    _cleanup_local_interface_service_host_artifacts(config=config)
    timings["cleanup_duration_s"] = _duration_since(cleanup_started)
    status = str(termination.get("status", "unknown"))
    stopped = status in {"terminated", "not_running"}
    timings["total_duration_s"] = _duration_since(started)
    return {
        "operation": "interface_service_host_stop",
        "action": "stopped" if stopped else "stop_requested",
        "status": "stopped" if stopped else status,
        "healthy": False,
        "paths": _local_interface_service_host_paths(config),
        "before": before,
        "termination": termination,
        "timings": timings,
        "duration_s": timings["total_duration_s"],
    }


def _build_ready_payload(
    *,
    config: LocalInterfaceServiceHostConfig,
    app: ServiceHostApp,
    loaded_services: Sequence[str],
    process_id: int | None = None,
    serve_started_at_epoch_s: float | None = None,
    server_ipc_import_duration_s: float | None = None,
    app_build_duration_s: float | None = None,
    server_construct_duration_s: float | None = None,
    server_start_duration_s: float | None = None,
    server_start_phase_timings_s: Mapping[str, object] | None = None,
    ready_payload_build_duration_s: float | None = None,
    ready_duration_s: float | None = None,
) -> dict[str, object]:
    return {
        "service": "interface",
        "api_service_name": INTERFACE_API_SERVICE_NAME,
        "repo_root": config.repo_root.as_posix(),
        "process_id": process_id,
        "serve_started_at_epoch_s": serve_started_at_epoch_s,
        "ready_at_epoch_s": time.time(),
        "socket_path": config.socket_path.as_posix(),
        "runtime_manifest_path": (
            config.runtime_manifest_path.as_posix()
            if config.runtime_manifest_path is not None
            else None
        ),
        "environment_api_endpoint": config.environment_api_endpoint,
        "state_root_path": (
            config.state_root_path.as_posix()
            if config.state_root_path is not None
            else None
        ),
        "implementation_toml_paths": [
            path.as_posix() for path in config.implementation_toml_paths
        ],
        "plugin_services": sorted(loaded_services),
        "activated_implementation_services": list(
            app.activated_implementation_service_names
        ),
        "activated_endpoint_refs_by_service": {
            key: list(value)
            for key, value in app.activated_implementation_endpoint_refs_by_service.items()
        },
        "service_protocol_runtime_resolution": (
            app.service_protocol_runtime_resolution_evidence
        ),
        "startup_subphase_timings_s": {
            "server_start": dict(server_start_phase_timings_s or {}),
            "app_start": app.startup_phase_timings_s,
            "implementation_activation": app.implementation_activation_evidence,
        },
        "timings": {
            "server_ipc_import_duration_s": server_ipc_import_duration_s,
            "app_build_duration_s": app_build_duration_s,
            "server_construct_duration_s": server_construct_duration_s,
            "server_start_duration_s": server_start_duration_s,
            "ready_payload_build_duration_s": ready_payload_build_duration_s,
            "ready_duration_s": ready_duration_s,
        },
    }


def _write_ready_file(
    *,
    config: LocalInterfaceServiceHostConfig,
    payload: dict[str, object],
) -> None:
    if config.ready_file_path is None:
        return
    config.ready_file_path.parent.mkdir(parents=True, exist_ok=True)
    config.ready_file_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def local_interface_service_host_pid_file_path(
    config: LocalInterfaceServiceHostConfig,
) -> Path:
    return config.socket_path.with_suffix(".pid.json")


def _local_interface_service_host_stdout_log_path(
    config: LocalInterfaceServiceHostConfig,
) -> Path:
    return config.socket_path.with_suffix(".stdout.log")


def _local_interface_service_host_stderr_log_path(
    config: LocalInterfaceServiceHostConfig,
) -> Path:
    return config.socket_path.with_suffix(".stderr.log")


def _local_interface_service_host_paths(
    config: LocalInterfaceServiceHostConfig,
) -> dict[str, str | None]:
    return {
        "repo_root": config.repo_root.as_posix(),
        "socket_path": config.socket_path.as_posix(),
        "ready_file_path": (
            config.ready_file_path.as_posix()
            if config.ready_file_path is not None
            else None
        ),
        "pid_file_path": local_interface_service_host_pid_file_path(config).as_posix(),
        "ensure_lock_path": _local_interface_service_host_ensure_lock_path(
            config
        ).as_posix(),
        "stdout_log_path": _local_interface_service_host_stdout_log_path(
            config
        ).as_posix(),
        "stderr_log_path": _local_interface_service_host_stderr_log_path(
            config
        ).as_posix(),
        "state_root_path": (
            config.state_root_path.as_posix()
            if config.state_root_path is not None
            else None
        ),
    }


def _local_interface_service_host_attach_metadata(
    *,
    config: LocalInterfaceServiceHostConfig,
    ready_payload: dict[str, object] | None,
    pid_payload: dict[str, object] | None,
) -> dict[str, object]:
    pid = _pid_from_payload(pid_payload)
    started_at_epoch_s = _float_payload_value(pid_payload, "started_at_epoch_s")
    ready_at_epoch_s = _float_payload_value(ready_payload, "ready_at_epoch_s")
    serve_started_at_epoch_s = _float_payload_value(
        ready_payload,
        "serve_started_at_epoch_s",
    )
    uptime_s: float | None = None
    if started_at_epoch_s is not None:
        uptime_s = _round_seconds(max(time.time() - started_at_epoch_s, 0.0))
    return {
        "service": "interface",
        "repo_root": config.repo_root.as_posix(),
        "pid": pid,
        "started_at_epoch_s": started_at_epoch_s,
        "uptime_s": uptime_s,
        "process_id_from_ready_file": _int_payload_value(
            ready_payload,
            "process_id",
        ),
        "ready_at_epoch_s": ready_at_epoch_s,
        "serve_started_at_epoch_s": serve_started_at_epoch_s,
        "process_start_to_ready_s": _epoch_delta_seconds(
            started_at_epoch_s,
            ready_at_epoch_s,
        ),
        "command": (
            pid_payload.get("command")
            if isinstance(pid_payload, dict)
            and isinstance(pid_payload.get("command"), list)
            else None
        ),
    }


def _read_json_file(path: Path | None) -> dict[str, object] | None:
    if path is None or not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _duration_since(started: float) -> float:
    return _round_seconds(max(time.perf_counter() - started, 0.0))


def _round_seconds(value: float) -> float:
    return round(value, 6)


def _float_payload_value(
    payload: Mapping[str, object] | None,
    key: str,
) -> float | None:
    if payload is None:
        return None
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _int_payload_value(
    payload: Mapping[str, object] | None,
    key: str,
) -> int | None:
    if payload is None:
        return None
    value = payload.get(key)
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _epoch_delta_seconds(
    start_epoch_s: float | None,
    end_epoch_s: float | None,
) -> float | None:
    if start_epoch_s is None or end_epoch_s is None:
        return None
    return _round_seconds(max(end_epoch_s - start_epoch_s, 0.0))


def _local_interface_service_host_ensure_lock_path(
    config: LocalInterfaceServiceHostConfig,
) -> Path:
    return config.socket_path.with_suffix(".ensure.lock")


async def _acquire_local_interface_service_host_ensure_lock(
    *,
    config: LocalInterfaceServiceHostConfig,
    timeout_s: float,
) -> _LocalInterfaceServiceHostEnsureLock | None:
    lock_path = _local_interface_service_host_ensure_lock_path(config)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.perf_counter() + max(timeout_s, 0.0)
    while True:
        try:
            lock_path.mkdir(mode=0o700)
            _write_local_interface_service_host_ensure_lock_owner(lock_path)
            return _LocalInterfaceServiceHostEnsureLock(path=lock_path)
        except FileExistsError:
            if _local_interface_service_host_ensure_lock_is_stale(lock_path):
                _cleanup_local_interface_service_host_ensure_lock(lock_path)
                continue
            if time.perf_counter() >= deadline:
                return None
            await asyncio.sleep(0.05)


def _write_local_interface_service_host_ensure_lock_owner(lock_path: Path) -> None:
    (lock_path / "owner.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "started_at_epoch_s": time.time(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _release_local_interface_service_host_ensure_lock(
    lock: _LocalInterfaceServiceHostEnsureLock,
) -> None:
    _cleanup_local_interface_service_host_ensure_lock(lock.path)


def _cleanup_local_interface_service_host_ensure_lock(lock_path: Path) -> None:
    try:
        shutil.rmtree(lock_path)
    except FileNotFoundError:
        return
    except NotADirectoryError:
        try:
            lock_path.unlink()
        except FileNotFoundError:
            return


def _local_interface_service_host_ensure_lock_is_stale(lock_path: Path) -> bool:
    owner = _read_json_file(lock_path / "owner.json")
    owner_pid = _pid_from_payload(owner)
    return owner_pid is None or not _process_id_is_running(owner_pid)


def _live_matching_pid_from_service_host_status(
    *,
    status: Mapping[str, object],
    config: LocalInterfaceServiceHostConfig,
) -> int | None:
    payload = status.get("pid_payload")
    if not isinstance(payload, dict):
        return None
    pid_payload = cast(dict[str, object], payload)
    if not _pid_payload_matches_config(pid_payload=pid_payload, config=config):
        return None
    pid = _pid_from_payload(pid_payload)
    if pid is None:
        return None
    if not _process_id_matches_local_interface_service_host(pid, config=config):
        return None
    return pid


def _process_id_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _process_id_matches_local_interface_service_host(
    pid: int,
    *,
    config: LocalInterfaceServiceHostConfig,
) -> bool:
    if not _process_id_is_running(pid):
        return False
    cmdline = _process_cmdline_parts(pid)
    if not cmdline:
        return False
    return (
        "aware_interface_service.local_host" in cmdline
        and "serve" in cmdline
        and config.socket_path.as_posix() in cmdline
    )


def _process_cmdline_parts(pid: int) -> tuple[str, ...] | None:
    try:
        raw = (Path("/proc") / str(pid) / "cmdline").read_bytes()
    except (FileNotFoundError, ProcessLookupError, PermissionError):
        return None
    return tuple(
        item.decode("utf-8", errors="replace")
        for item in raw.split(b"\0")
        if item
    )


def _cleanup_local_interface_service_host_artifacts(
    *,
    config: LocalInterfaceServiceHostConfig,
) -> None:
    for path in (
        config.socket_path,
        config.ready_file_path,
        local_interface_service_host_pid_file_path(config),
    ):
        if path is None:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except IsADirectoryError:
            continue


def _build_local_interface_service_host_serve_command(
    *,
    config: LocalInterfaceServiceHostConfig,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "aware_interface_service.local_host",
        "serve",
        "--repo-root",
        config.repo_root.as_posix(),
        "--socket-path",
        config.socket_path.as_posix(),
    ]
    for implementation_toml_path in config.implementation_toml_paths:
        command.extend(["--implementation-toml", implementation_toml_path.as_posix()])
    if config.runtime_manifest_path is not None:
        command.extend(
            ["--runtime-manifest-path", config.runtime_manifest_path.as_posix()]
        )
    if config.environment_api_endpoint is None:
        command.append("--no-environment-api-endpoint")
    else:
        command.extend(["--environment-api-endpoint", config.environment_api_endpoint])
    if config.ready_file_path is None:
        command.append("--no-ready-file")
    else:
        command.extend(["--ready-file", config.ready_file_path.as_posix()])
    if config.state_root_path is None:
        command.append("--no-isolated-state")
    else:
        command.extend(["--state-root", config.state_root_path.as_posix()])
    return command


def _start_local_interface_service_host_process(
    *,
    config: LocalInterfaceServiceHostConfig,
) -> subprocess.Popen[bytes]:
    config.socket_path.parent.mkdir(parents=True, exist_ok=True)
    if config.ready_file_path is not None:
        config.ready_file_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path = local_interface_service_host_pid_file_path(config)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path = _local_interface_service_host_stdout_log_path(config)
    stderr_path = _local_interface_service_host_stderr_log_path(config)
    command = _build_local_interface_service_host_serve_command(config=config)
    with stdout_path.open("ab") as stdout_file, stderr_path.open("ab") as stderr_file:
        return subprocess.Popen(
            command,
            cwd=str(config.repo_root),
            stdout=stdout_file,
            stderr=stderr_file,
            start_new_session=True,
            close_fds=True,
        )


def _write_local_interface_service_host_pid_file(
    *,
    config: LocalInterfaceServiceHostConfig,
    process: subprocess.Popen[bytes],
    command: Sequence[str],
) -> None:
    pid_path = local_interface_service_host_pid_file_path(config)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(
        json.dumps(
            {
                "service": "interface",
                "repo_root": config.repo_root.as_posix(),
                "pid": process.pid,
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
                "command": list(command),
                "started_at_epoch_s": time.time(),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _pid_from_payload(payload: dict[str, object] | None) -> int | None:
    if payload is None:
        return None
    raw_pid = payload.get("pid")
    if isinstance(raw_pid, bool):
        return None
    if isinstance(raw_pid, int) and raw_pid > 0:
        return raw_pid
    return None


def _pid_payload_matches_config(
    *,
    pid_payload: dict[str, object] | None,
    config: LocalInterfaceServiceHostConfig,
) -> bool:
    if pid_payload is None:
        return False
    return pid_payload.get("socket_path") == config.socket_path.as_posix()


def _terminate_process_id(pid: int, timeout_s: float) -> dict[str, object]:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return {"status": "not_running", "pid": pid}

    os.kill(pid, signal.SIGTERM)
    deadline = time.perf_counter() + max(timeout_s, 0.0)
    while time.perf_counter() <= deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return {"status": "terminated", "pid": pid}
        time.sleep(0.05)
    return {"status": "timeout", "pid": pid}


async def _wait_for_shutdown_signal() -> None:
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()
    for item in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(item, stop_event.set)
        except NotImplementedError:  # pragma: no cover - Windows fallback.
            pass
        except RuntimeError:  # pragma: no cover - non-main-thread fallback.
            pass
    await stop_event.wait()


def _build_service_host_duplex_client(
    *,
    endpoint: DuplexIpcEndpoint,
) -> ServiceHostDuplexClient:
    return ServiceHostDuplexClient(endpoint=endpoint)


def _resolve_path(*, root: Path, value: str | Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _resolve_repo_root(value: str | Path | None) -> Path:
    if value is not None:
        return Path(value).expanduser().resolve()
    for env_name in LOCAL_INTERFACE_REPO_ROOT_ENV_VARS:
        raw = os.environ.get(env_name)
        if raw is not None and raw.strip():
            return Path(raw).expanduser().resolve()
    raise RuntimeError(
        "Local Interface ServiceHost repo root is required. Pass repo_root, "
        "--repo-root, or set one of "
        f"{', '.join(LOCAL_INTERFACE_REPO_ROOT_ENV_VARS)}."
    )


def _clean_optional_text(value: str | None) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None


def _add_local_interface_service_host_config_arguments(
    parser: argparse.ArgumentParser,
    *,
    socket_default: str | None,
) -> None:
    parser.add_argument(
        "--repo-root",
        default=None,
        help=(
            "Explicit source repository root. Defaults to one of "
            f"{', '.join(LOCAL_INTERFACE_REPO_ROOT_ENV_VARS)}."
        ),
    )
    parser.add_argument("--socket-path", default=socket_default)
    parser.add_argument("--implementation-toml", action="append", default=[])
    parser.add_argument("--runtime-manifest-path", default=None)
    parser.add_argument(
        "--environment-api-endpoint",
        default=LOCAL_ENVIRONMENT_API_ENDPOINT,
    )
    parser.add_argument("--no-environment-api-endpoint", action="store_true")
    parser.add_argument("--ready-file", default=str(DEFAULT_READY_RELATIVE_PATH))
    parser.add_argument("--no-ready-file", action="store_true")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT_RELATIVE_PATH))
    parser.add_argument("--no-isolated-state", action="store_true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aware-interface-service-host",
        description="Local warm Interface service host and probe harness.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="Run a warm Interface service host.")
    _add_local_interface_service_host_config_arguments(serve, socket_default=None)

    ensure = subparsers.add_parser(
        "ensure",
        help="Start or reuse the warm Interface service host.",
    )
    _add_local_interface_service_host_config_arguments(
        ensure,
        socket_default=str(DEFAULT_SOCKET_RELATIVE_PATH),
    )
    ensure.add_argument(
        "--start-timeout-s",
        type=float,
        default=DEFAULT_OPERATOR_START_TIMEOUT_S,
    )
    ensure.add_argument(
        "--probe-timeout-s",
        type=float,
        default=DEFAULT_OPERATOR_PROBE_TIMEOUT_S,
    )
    ensure.add_argument("--no-cleanup-stale", action="store_true")

    status = subparsers.add_parser(
        "status",
        help="Inspect warm Interface service host readiness.",
    )
    _add_local_interface_service_host_config_arguments(
        status,
        socket_default=str(DEFAULT_SOCKET_RELATIVE_PATH),
    )
    status.add_argument(
        "--timeout-s",
        type=float,
        default=DEFAULT_OPERATOR_PROBE_TIMEOUT_S,
    )

    stop = subparsers.add_parser(
        "stop",
        help="Stop the warm Interface service host recorded for this socket.",
    )
    _add_local_interface_service_host_config_arguments(
        stop,
        socket_default=str(DEFAULT_SOCKET_RELATIVE_PATH),
    )
    stop.add_argument(
        "--timeout-s",
        type=float,
        default=DEFAULT_OPERATOR_STOP_TIMEOUT_S,
    )
    return parser


def _resolve_serve_config_from_args(
    args: argparse.Namespace,
) -> LocalInterfaceServiceHostConfig:
    return resolve_local_interface_service_host_config(
        socket_path=args.socket_path,
        implementation_toml_paths=tuple(args.implementation_toml),
        runtime_manifest_path=args.runtime_manifest_path,
        environment_api_endpoint=(
            None if args.no_environment_api_endpoint else args.environment_api_endpoint
        ),
        ready_file_path=(None if args.no_ready_file else args.ready_file),
        state_root_path=(None if args.no_isolated_state else args.state_root),
        repo_root=args.repo_root,
    )


def _main_serve(args: argparse.Namespace) -> int:
    config = _resolve_serve_config_from_args(args)
    _ = asyncio.run(serve_local_interface_service_host(config=config))
    return 0


async def _main_ensure_async(args: argparse.Namespace) -> int:
    config = _resolve_serve_config_from_args(args)
    result = await ensure_local_interface_service_host(
        config=config,
        start_timeout_s=args.start_timeout_s,
        probe_timeout_s=args.probe_timeout_s,
        cleanup_stale=not bool(args.no_cleanup_stale),
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("healthy") is True else 2


async def _main_status_async(args: argparse.Namespace) -> int:
    config = _resolve_serve_config_from_args(args)
    result = await inspect_local_interface_service_host(
        config=config,
        timeout_s=args.timeout_s,
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("healthy") is True else 2


async def _main_stop_async(args: argparse.Namespace) -> int:
    config = _resolve_serve_config_from_args(args)
    result = await stop_local_interface_service_host(
        config=config,
        timeout_s=args.timeout_s,
    )
    print(json.dumps(result, sort_keys=True), flush=True)
    return 0 if result.get("status") in {"stopped", "not_running"} else 2


def main(argv: Sequence[str] | None = None) -> int:
    try:
        parser = _build_parser()
        args = parser.parse_args(list(argv) if argv is not None else None)
        if args.command == "serve":
            return _main_serve(args)
        if args.command == "ensure":
            return asyncio.run(_main_ensure_async(args))
        if args.command == "status":
            return asyncio.run(_main_status_async(args))
        if args.command == "stop":
            return asyncio.run(_main_stop_async(args))
    except KeyboardInterrupt:
        return 130
    return 2


__all__ = [
    "DEFAULT_API_CLIENT_ENDPOINT",
    "DEFAULT_IMPLEMENTATION_TOML_RELATIVE_PATH",
    "DEFAULT_READY_RELATIVE_PATH",
    "DEFAULT_SOCKET_RELATIVE_PATH",
    "DEFAULT_STATE_ROOT_RELATIVE_PATH",
    "INTERFACE_API_SERVICE_NAME",
    "LOCAL_ENVIRONMENT_API_ENDPOINT",
    "LocalInterfaceServiceHostConfig",
    "build_local_interface_service_host_api_client",
    "build_local_interface_service_host_app",
    "build_local_interface_service_host_duplex_client_factory",
    "ensure_local_interface_service_host",
    "inspect_local_interface_service_host",
    "resolve_local_interface_service_host_config",
    "serve_local_interface_service_host",
    "stop_local_interface_service_host",
]


if __name__ == "__main__":
    sys.exit(main())
