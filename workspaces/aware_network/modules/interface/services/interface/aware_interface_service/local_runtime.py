from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import sys
import time
import tomllib
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from aware_comms import DuplexIpcEndpoint
from aware_network.node_deploy.dto import (
    DescribeNodeRuntimeRequest,
    EnsureNodeRuntimeStartedRequest,
    NodeDeployRuntimePhase,
    NodeDeployRuntimeStatus,
    RestartNodeRuntimeRequest,
    StopNodeRuntimeRequest,
    TailNodeRuntimeLogsRequest,
    TailNodeRuntimeLogsResponse,
    parse_node_deploy_operation_event,
    parse_node_deploy_operation_response,
)
from aware_service_service_dto.comms.models.service import (
    RequestStatus,
    ServiceOperationContext,
    ServiceOperationRequest,
    ServiceOperationResponse,
)
from aware_service_runtime.contracts import (
    SERVICE_HOST_PROTOCOL_VERSION,
    ServiceHostBootstrapStatus,
    ServiceHostHandshakeRequest,
    ServiceHostHandshakeResponse,
)
from aware_service_runtime.duplex import ServiceDuplexStreamEventKind
from aware_service_runtime.duplex_client import ServiceHostDuplexClient
from aware_service_runtime.local_dev_service_host import (
    evaluate_local_servicehost_boot_policy,
)

from aware_interface_service.local_service_host_api_client import (
    LocalServiceHostAwareApiClient,
)
from aware_interface_service.models import (
    InterfaceHostServiceLocalNodeRuntimeState,
    InterfaceHostServiceLocalServiceHostState,
    InterfaceHostServiceOperationTargetState,
)

_SUPPORTED_LOCAL_PLATFORMS = ("linux", "darwin", "win32")
_DEFAULT_LOCAL_SERVICE_DIRNAME = "local_service"
_DEFAULT_LOCAL_SERVICE_SOCKET_FILENAME = "aware-service-host.sock"
_DEFAULT_LOCAL_SERVICE_CONFIG_FILENAME = "aware-service-host.bootstrap.toml"
_DEFAULT_LOCAL_SERVICE_LOG_FILENAME = "aware-service-host.log"
_SERVICE_PLUGIN_PROVIDERS_ENV = "AWARE_SERVICE_SERVICE_PLUGIN_PROVIDERS"
_SERVICE_ENABLED_SERVICES_ENV = "AWARE_SERVICE_SERVICE_ENABLED_SERVICES"
_NETWORK_NODE_DEPLOY_PROVIDER_MODULE = "aware_network_service_service.providers"
_NODE_DEPLOY_SERVICE = "node_deploy"
_UNIX_SOCKET_PATH_SOFT_LIMIT = 100
_DEFAULT_HANDSHAKE_TIMEOUT_S = 2.0
_DEFAULT_START_TIMEOUT_S = 20.0
_DEFAULT_NODE_REQUEST_TIMEOUT_S = 30.0


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _elapsed_ms(started_at_s: float) -> int:
    return max(0, int((time.monotonic() - started_at_s) * 1000))


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _resolve_service_host_pid_linux(*, socket_path: Path) -> int | None:
    target_socket = str(socket_path)
    proc_root = Path("/proc")
    for proc_dir in proc_root.iterdir():
        if not proc_dir.name.isdigit():
            continue
        pid = int(proc_dir.name)
        cmdline_path = proc_dir / "cmdline"
        environ_path = proc_dir / "environ"
        try:
            cmdline = cmdline_path.read_bytes().decode("utf-8", errors="ignore")
        except OSError:
            continue
        if "aware_service_service" not in cmdline:
            continue
        try:
            environ = environ_path.read_bytes().decode("utf-8", errors="ignore")
        except OSError:
            continue
        env_pairs = {
            key: value
            for key, _, value in (
                entry.partition("=") for entry in environ.split("\x00") if entry
            )
        }
        if env_pairs.get("AWARE_SERVICE_HOST_SOCKET_PATH") == target_socket:
            return pid
    return None


def _is_supported_local_platform() -> bool:
    return sys.platform.startswith(_SUPPORTED_LOCAL_PLATFORMS)


def _normalize_env_token(name: str) -> str | None:
    raw = str(os.environ.get(name) or "").strip()
    return raw or None


def _ensure_csv_env_token(
    env: dict[str, str],
    *,
    name: str,
    token: str,
) -> None:
    normalized_token = token.strip()
    if not normalized_token:
        return
    raw = str(env.get(name) or "").strip()
    tokens = [item.strip() for item in raw.split(",") if item.strip()]
    if normalized_token not in tokens:
        tokens.append(normalized_token)
    env[name] = ",".join(tokens)


def _apply_local_node_deploy_service_env(env: dict[str, str]) -> None:
    """Mount the Network-owned node_deploy service without changing UI rails."""

    _ensure_csv_env_token(
        env,
        name=_SERVICE_PLUGIN_PROVIDERS_ENV,
        token=_NETWORK_NODE_DEPLOY_PROVIDER_MODULE,
    )
    if str(env.get(_SERVICE_ENABLED_SERVICES_ENV) or "").strip():
        _ensure_csv_env_token(
            env,
            name=_SERVICE_ENABLED_SERVICES_ENV,
            token=_NODE_DEPLOY_SERVICE,
        )


def _default_local_service_socket_path(
    *,
    namespace: str,
    state_home: Path,
) -> Path:
    preferred = (
        state_home
        / _DEFAULT_LOCAL_SERVICE_DIRNAME
        / _DEFAULT_LOCAL_SERVICE_SOCKET_FILENAME
    ).resolve()
    if not sys.platform.startswith(("linux", "darwin")):
        return preferred
    if len(str(preferred)) <= _UNIX_SOCKET_PATH_SOFT_LIMIT:
        return preferred
    digest = uuid5(
        NAMESPACE_URL,
        f"aware-interface-local-service:{namespace}:{state_home.resolve()}",
    )
    candidate_roots: list[Path] = []
    tmpdir = _normalize_env_token("TMPDIR")
    if tmpdir is not None:
        candidate_roots.append(Path(tmpdir).expanduser().resolve())
    candidate_roots.append(Path("/tmp"))
    fallback = (
        Path("/tmp")
        / f"aware-iface-{digest.hex[:16]}"
        / (_DEFAULT_LOCAL_SERVICE_SOCKET_FILENAME)
    )
    for root in candidate_roots:
        candidate = (
            root
            / f"aware-iface-{digest.hex[:16]}"
            / _DEFAULT_LOCAL_SERVICE_SOCKET_FILENAME
        )
        fallback = candidate
        if len(str(candidate)) <= _UNIX_SOCKET_PATH_SOFT_LIMIT:
            return candidate
    return fallback


def _read_service_host_socket_path_from_bootstrap_config(*, config_path: Path) -> Path:
    if not config_path.is_file():
        raise FileNotFoundError(
            "Interface local ServiceHost bootstrap config was not found: "
            f"{config_path}"
        )
    with config_path.open("rb") as handle:
        payload = tomllib.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(
            "Interface local ServiceHost bootstrap config must decode to a TOML table."
        )
    ipc_payload = payload.get("ipc")
    if not isinstance(ipc_payload, dict):
        raise RuntimeError(
            "Interface local ServiceHost bootstrap config requires an [ipc] table."
        )
    raw_socket_path = ipc_payload.get("socket_path")
    if not isinstance(raw_socket_path, str) or not raw_socket_path.strip():
        raise RuntimeError(
            "Interface local ServiceHost bootstrap config requires ipc.socket_path."
        )
    socket_path = Path(raw_socket_path).expanduser()
    if not socket_path.is_absolute():
        socket_path = config_path.parent / socket_path
    return socket_path.resolve()


def _is_local_endpoint(endpoint: str | None) -> bool:
    if endpoint is None:
        return True
    parsed = urlparse(endpoint)
    host = (parsed.hostname or parsed.path or endpoint).strip().lower()
    return host in {"localhost", "127.0.0.1", "::1"}


def _stable_context_uuid(namespace: str, suffix: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"aware://interface/{namespace}/local-runtime/{suffix}")


def _resolve_recent_log_lines(
    *,
    runtime_status: NodeDeployRuntimeStatus | None,
    explicit_log_lines: tuple[str, ...] = (),
) -> tuple[str, ...]:
    normalized = tuple(line.strip() for line in explicit_log_lines if line.strip())
    if normalized:
        return normalized
    if runtime_status is None:
        return ()
    runtime_lines = tuple(
        line.strip() for line in runtime_status.recent_log_lines if line.strip()
    )
    if runtime_lines:
        return runtime_lines
    derived: list[str] = []
    if runtime_status.summary:
        derived.append(runtime_status.summary)
    if runtime_status.error:
        derived.append(runtime_status.error)
    prioritized_targets = list(runtime_status.target_statuses)
    if runtime_status.active_target_id is not None:
        prioritized_targets.sort(
            key=lambda item: item.target_id != runtime_status.active_target_id
        )
    for item in prioritized_targets:
        detail = item.error or item.summary
        if not detail:
            continue
        derived.append(f"{item.display_name}: {detail}")
    deduped: list[str] = []
    seen: set[str] = set()
    for item in derived:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return tuple(deduped[:10])


def _detail_lines_for_target(
    *,
    target_id: str,
    display_name: str,
    summary: str | None,
    error: str | None,
    recent_log_lines: tuple[str, ...],
) -> tuple[str, ...]:
    normalized_target_id = target_id.strip().lower()
    normalized_display_name = display_name.strip().lower()
    candidates: list[str] = []
    for line in recent_log_lines:
        normalized_line = line.strip()
        if not normalized_line:
            continue
        lowered = normalized_line.lower()
        if lowered.startswith(f"[{normalized_target_id}]"):
            candidates.append(normalized_line)
            continue
        if lowered.startswith(f"{normalized_target_id}:"):
            candidates.append(normalized_line)
            continue
        if normalized_display_name and lowered.startswith(
            f"{normalized_display_name}:"
        ):
            candidates.append(normalized_line)
            continue
    if error:
        prefixed_error = (
            error
            if error.lower().startswith(f"{normalized_display_name}:")
            else f"{display_name}: {error}"
        )
        candidates.append(prefixed_error)
    elif summary:
        prefixed_summary = (
            summary
            if summary.lower().startswith(f"{normalized_display_name}:")
            else f"{display_name}: {summary}"
        )
        candidates.append(prefixed_summary)
    deduped: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return tuple(deduped[:6])


@dataclass(frozen=True, slots=True)
class InterfaceLocalRuntimeSnapshot:
    service_host: InterfaceHostServiceLocalServiceHostState
    node_runtime: InterfaceHostServiceLocalNodeRuntimeState


@dataclass(slots=True)
class InterfaceLocalRuntimeController:
    repository_root: Path
    state_home: Path
    namespace: str
    endpoint: str | None = None
    service_host_bootstrap_config_path: Path | None = None
    service_host_implementation_toml_paths: tuple[Path, ...] = ()
    _service_host_start_lock: asyncio.Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.repository_root = self.repository_root.resolve()
        self.state_home = self.state_home.resolve()
        if self.service_host_bootstrap_config_path is not None:
            self.service_host_bootstrap_config_path = (
                self.service_host_bootstrap_config_path.expanduser().resolve()
            )
        self.service_host_implementation_toml_paths = tuple(
            path.expanduser().resolve()
            for path in self.service_host_implementation_toml_paths
        )
        self._service_host_start_lock = asyncio.Lock()

    @property
    def is_managed(self) -> bool:
        return _is_local_endpoint(self.endpoint)

    def resolve_service_host_socket_path(self) -> Path:
        for env_name in (
            "AWARE_SERVICE_HOST_SOCKET_PATH",
            "AWARE_NODE_DEPLOY_SERVICE_SOCKET_PATH",
            "AWARE_NODE_DEPLOY_SOCKET_PATH",
        ):
            raw = _normalize_env_token(env_name)
            if raw is not None:
                return Path(raw).expanduser().resolve()
        if self.service_host_bootstrap_config_path is not None:
            return _read_service_host_socket_path_from_bootstrap_config(
                config_path=self.service_host_bootstrap_config_path,
            )
        return _default_local_service_socket_path(
            namespace=self.namespace,
            state_home=self.state_home,
        )

    def resolve_service_host_bootstrap_config_path(self) -> Path:
        return (
            self.state_home
            / _DEFAULT_LOCAL_SERVICE_DIRNAME
            / _DEFAULT_LOCAL_SERVICE_CONFIG_FILENAME
        ).resolve()

    def resolve_service_host_log_path(self) -> Path:
        return (
            self.state_home
            / _DEFAULT_LOCAL_SERVICE_DIRNAME
            / _DEFAULT_LOCAL_SERVICE_LOG_FILENAME
        ).resolve()

    def build_local_service_host_api_client(
        self,
        *,
        actor_id: UUID,
        request_timeout_s: float = 10.0,
    ) -> LocalServiceHostAwareApiClient:
        return LocalServiceHostAwareApiClient(
            actor_id=actor_id,
            endpoint=f"aware-service-host://{self.namespace}",
            request_timeout_s=request_timeout_s,
            client_factory=self._service_host_client,
        )

    async def snapshot(self) -> InterfaceLocalRuntimeSnapshot:
        service_host = await self._probe_service_host()
        node_runtime = await self._describe_node_runtime(service_host=service_host)
        return InterfaceLocalRuntimeSnapshot(
            service_host=service_host,
            node_runtime=node_runtime,
        )

    async def probe_service_host_handshake(
        self,
        *,
        timeout_s: float = _DEFAULT_HANDSHAKE_TIMEOUT_S,
    ) -> ServiceHostHandshakeResponse:
        client = self._service_host_client()
        return await client.send_handshake(
            request=ServiceHostHandshakeRequest(
                supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,),
            ),
            timeout_s=timeout_s,
        )

    async def ensure_service_host_ready(
        self,
        *,
        timeout_s: float = _DEFAULT_START_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        async with self._service_host_start_lock:
            return await self._ensure_service_host_ready_locked(timeout_s=timeout_s)

    async def _ensure_service_host_ready_locked(
        self,
        *,
        timeout_s: float,
    ) -> InterfaceLocalRuntimeSnapshot:
        service_host = await self._probe_service_host()
        if not service_host.managed or not service_host.supported or service_host.ready:
            return InterfaceLocalRuntimeSnapshot(
                service_host=service_host,
                node_runtime=await self._describe_node_runtime(
                    service_host=service_host
                ),
            )
        if service_host.status == ServiceHostBootstrapStatus.failed.value and (
            service_host.socket_path is None
        ):
            return InterfaceLocalRuntimeSnapshot(
                service_host=service_host,
                node_runtime=await self._describe_node_runtime(
                    service_host=service_host
                ),
            )

        socket_path = self.resolve_service_host_socket_path()
        socket_path.parent.mkdir(parents=True, exist_ok=True)
        existing_pid = self._resolve_running_service_host_pid(socket_path=socket_path)
        process: asyncio.subprocess.Process | None = None
        if existing_pid is None:
            boot_decision = evaluate_local_servicehost_boot_policy(
                service_name=f"interface:{self.namespace}",
                bootstrap_config_path=self.service_host_bootstrap_config_path,
                implementation_toml_paths=self.service_host_implementation_toml_paths,
                allow_dev_implementation_boot=bool(
                    self.service_host_implementation_toml_paths
                ),
            )
            if not boot_decision.allowed:
                missing = replace(
                    service_host,
                    status=ServiceHostBootstrapStatus.failed.value,
                    ready=False,
                    error=str(boot_decision.error or boot_decision.reason),
                    recent_log_lines=self._tail_service_host_log_lines(),
                    last_checked_at=_utc_now_iso(),
                )
                return InterfaceLocalRuntimeSnapshot(
                    service_host=missing,
                    node_runtime=await self._describe_node_runtime(
                        service_host=missing,
                    ),
                )
            config_path = self._write_service_host_bootstrap_config(
                socket_path=socket_path
            )
            log_path = self.resolve_service_host_log_path()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env["AWARE_SERVICE_HOST_CONFIG_PATH"] = str(config_path)
            env["AWARE_SERVICE_HOST_SOCKET_PATH"] = str(socket_path)
            env["AWARE_LOG_FILE"] = str(log_path)
            env.setdefault("AWARE_LOG_PROFILE", "rotating")
            env.setdefault("AWARE_LOG_FILE_LEVEL", "INFO")
            _apply_local_node_deploy_service_env(env)
            with log_path.open("ab") as log_handle:
                log_handle.write(
                    f"\n--- aware_service_service start {_utc_now_iso()} ---\n".encode(
                        "utf-8"
                    )
                )
                process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "-m",
                    "aware_service_service",
                    cwd=str(self.repository_root),
                    env=env,
                    stdout=log_handle,
                    stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True,
                )
        deadline = asyncio.get_running_loop().time() + timeout_s
        last_state = service_host
        while asyncio.get_running_loop().time() < deadline:
            state = await self._probe_service_host()
            if state.ready:
                return InterfaceLocalRuntimeSnapshot(
                    service_host=state,
                    node_runtime=await self._describe_node_runtime(service_host=state),
                )
            last_state = state
            if process is not None:
                returncode = process.returncode
                if returncode is not None and returncode != 0:
                    break
            elif existing_pid is not None and not _is_pid_running(existing_pid):
                break
            await asyncio.sleep(0.25)
            if process is not None:
                returncode = process.returncode
                if returncode is not None and returncode != 0:
                    break
            elif existing_pid is not None and not _is_pid_running(existing_pid):
                break
        still_starting = (
            process.returncode is None
            if process is not None
            else existing_pid is not None and _is_pid_running(existing_pid)
        )
        failure = InterfaceHostServiceLocalServiceHostState(
            managed=last_state.managed,
            supported=last_state.supported,
            socket_path=last_state.socket_path,
            available=last_state.available,
            ready=False,
            status=(
                ServiceHostBootstrapStatus.starting.value
                if still_starting
                else ServiceHostBootstrapStatus.failed.value
            ),
            host_id=last_state.host_id,
            host_version=last_state.host_version,
            protocol_version=last_state.protocol_version,
            capabilities=last_state.capabilities,
            error=(
                None
                if still_starting
                else (
                    last_state.error
                    or "Interface timed out while waiting for the local Service host to become ready."
                )
            ),
            recent_log_lines=self._tail_service_host_log_lines(),
            probe_duration_ms=last_state.probe_duration_ms,
            last_checked_at=_utc_now_iso(),
        )
        return InterfaceLocalRuntimeSnapshot(
            service_host=failure,
            node_runtime=await self._describe_node_runtime(service_host=failure),
        )

    async def restart_service_host(
        self,
        *,
        timeout_s: float = _DEFAULT_START_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        await self._stop_service_host(timeout_s=timeout_s)
        return await self.ensure_service_host_ready(timeout_s=timeout_s)

    async def ensure_node_runtime_started(
        self,
        *,
        timeout_s: float = _DEFAULT_NODE_REQUEST_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        latest_snapshot: InterfaceLocalRuntimeSnapshot | None = None
        async for snapshot in self.stream_node_runtime_start(timeout_s=timeout_s):
            latest_snapshot = snapshot
        if latest_snapshot is None:
            return await self.ensure_service_host_ready(timeout_s=timeout_s)
        return latest_snapshot

    async def stream_node_runtime_start(
        self,
        *,
        timeout_s: float = _DEFAULT_NODE_REQUEST_TIMEOUT_S,
    ) -> AsyncIterator[InterfaceLocalRuntimeSnapshot]:
        snapshot = await self.ensure_service_host_ready(timeout_s=timeout_s)
        service_host = snapshot.service_host
        if not service_host.ready:
            yield snapshot
            return

        client = self._service_host_client()
        handle = client.open_request_stream(
            request=self._node_request(
                operation=EnsureNodeRuntimeStartedRequest(wait_for_ready=True),
            ),
            timeout_s=timeout_s,
        )
        recent_log_lines: list[str] = []
        last_runtime_status: NodeDeployRuntimeStatus | None = None
        response: ServiceOperationResponse | None = None
        last_emitted_node_runtime: InterfaceHostServiceLocalNodeRuntimeState | None = (
            None
        )
        try:
            async for event in handle.events:
                if (
                    event.kind is not ServiceDuplexStreamEventKind.RESPONSE
                    or event.response is None
                ):
                    continue
                payload = event.response.response_payload
                if payload is None:
                    continue
                parsed_event = parse_node_deploy_operation_event(payload)
                if parsed_event.runtime_status is not None:
                    last_runtime_status = parsed_event.runtime_status
                log_line = getattr(parsed_event, "log_line", None)
                if isinstance(log_line, str) and log_line.strip():
                    recent_log_lines.append(log_line)
                message_line = getattr(parsed_event, "message", None)
                if isinstance(message_line, str) and message_line.strip():
                    recent_log_lines.append(message_line)
                runtime_status = parsed_event.runtime_status or last_runtime_status
                if runtime_status is None:
                    continue
                node_runtime = self._node_state_from_runtime_status(
                    runtime_status=runtime_status,
                    available=True,
                    error=None,
                    recent_log_lines=tuple(recent_log_lines),
                )
                if node_runtime != last_emitted_node_runtime:
                    last_emitted_node_runtime = node_runtime
                    yield InterfaceLocalRuntimeSnapshot(
                        service_host=service_host,
                        node_runtime=node_runtime,
                    )
            response = await handle.response
        except TimeoutError:
            latest_service_host = await self._probe_service_host()
            latest_node_runtime = await self._describe_node_runtime(
                service_host=latest_service_host,
            )
            if last_runtime_status is not None and (
                latest_node_runtime.available is False
                or latest_node_runtime.phase == "idle"
            ):
                latest_node_runtime = self._node_state_from_runtime_status(
                    runtime_status=last_runtime_status,
                    available=True,
                    error=None,
                    recent_log_lines=tuple(recent_log_lines),
                )
            elif recent_log_lines and not latest_node_runtime.recent_log_lines:
                latest_node_runtime = replace(
                    latest_node_runtime,
                    recent_log_lines=tuple(recent_log_lines),
                )
            yield InterfaceLocalRuntimeSnapshot(
                service_host=latest_service_host,
                node_runtime=latest_node_runtime,
            )
            return
        finally:
            await handle.close()
        if response is None:
            raise RuntimeError(
                "Local Node runtime start stream completed without a terminal response."
            )
        node_response = parse_node_deploy_operation_response(response.response_payload)
        runtime_status = node_response.runtime_status or last_runtime_status
        node_runtime = self._node_state_from_runtime_status(
            runtime_status=runtime_status,
            available=response.status is RequestStatus.succeeded,
            error=node_response.error or response.error,
            recent_log_lines=tuple(recent_log_lines),
        )
        yield InterfaceLocalRuntimeSnapshot(
            service_host=await self._probe_service_host(),
            node_runtime=node_runtime,
        )
        return

    async def tail_node_runtime_logs(
        self,
        *,
        line_count: int = 200,
        timeout_s: float = _DEFAULT_NODE_REQUEST_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        snapshot = await self.ensure_service_host_ready(timeout_s=timeout_s)
        service_host = snapshot.service_host
        if not service_host.ready:
            return snapshot
        client = self._service_host_client()
        try:
            response = await client.send_request(
                request=self._node_request(
                    operation=TailNodeRuntimeLogsRequest(
                        line_count=max(1, line_count),
                    )
                ),
                timeout_s=timeout_s,
            )
        except Exception as exc:
            latest_service_host = await self._probe_service_host()
            latest_node_runtime = await self._describe_node_runtime(
                service_host=latest_service_host,
            )
            if latest_node_runtime.error is None:
                latest_node_runtime = replace(
                    latest_node_runtime,
                    error=str(exc),
                )
            return InterfaceLocalRuntimeSnapshot(
                service_host=latest_service_host,
                node_runtime=latest_node_runtime,
            )
        node_response = TailNodeRuntimeLogsResponse.model_validate(
            response.response_payload
        )
        recent_log_lines = _resolve_recent_log_lines(
            runtime_status=node_response.runtime_status,
            explicit_log_lines=tuple(node_response.log_lines),
        )
        node_runtime = self._node_state_from_runtime_status(
            runtime_status=node_response.runtime_status,
            available=response.status is RequestStatus.succeeded,
            error=node_response.error or response.error,
            recent_log_lines=recent_log_lines,
        )
        return InterfaceLocalRuntimeSnapshot(
            service_host=await self._probe_service_host(),
            node_runtime=node_runtime,
        )

    async def restart_node_runtime(
        self,
        *,
        timeout_s: float = _DEFAULT_NODE_REQUEST_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        snapshot = await self.snapshot()
        service_host = snapshot.service_host
        if not service_host.ready:
            return snapshot
        client = self._service_host_client()
        try:
            response = await client.send_request(
                request=self._node_request(
                    operation=RestartNodeRuntimeRequest(wait_for_ready=True),
                ),
                timeout_s=timeout_s,
            )
        except Exception as exc:
            latest_service_host = await self._probe_service_host()
            latest_node_runtime = await self._describe_node_runtime(
                service_host=latest_service_host,
            )
            if latest_node_runtime.error is None:
                latest_node_runtime = replace(
                    latest_node_runtime,
                    error=str(exc),
                )
            return InterfaceLocalRuntimeSnapshot(
                service_host=latest_service_host,
                node_runtime=latest_node_runtime,
            )
        node_response = parse_node_deploy_operation_response(response.response_payload)
        node_runtime = self._node_state_from_runtime_status(
            runtime_status=node_response.runtime_status,
            available=response.status is RequestStatus.succeeded,
            error=node_response.error or response.error,
        )
        return InterfaceLocalRuntimeSnapshot(
            service_host=await self._probe_service_host(),
            node_runtime=node_runtime,
        )

    async def stop_node_runtime(
        self,
        *,
        force: bool = False,
        timeout_s: float = _DEFAULT_NODE_REQUEST_TIMEOUT_S,
    ) -> InterfaceLocalRuntimeSnapshot:
        snapshot = await self.snapshot()
        service_host = snapshot.service_host
        if not service_host.ready:
            return snapshot
        client = self._service_host_client()
        try:
            response = await client.send_request(
                request=self._node_request(
                    operation=StopNodeRuntimeRequest(force=force),
                ),
                timeout_s=timeout_s,
            )
        except Exception as exc:
            latest_service_host = await self._probe_service_host()
            latest_node_runtime = await self._describe_node_runtime(
                service_host=latest_service_host,
            )
            if latest_node_runtime.error is None:
                latest_node_runtime = replace(
                    latest_node_runtime,
                    error=str(exc),
                )
            return InterfaceLocalRuntimeSnapshot(
                service_host=latest_service_host,
                node_runtime=latest_node_runtime,
            )
        node_response = parse_node_deploy_operation_response(response.response_payload)
        node_runtime = self._node_state_from_runtime_status(
            runtime_status=node_response.runtime_status,
            available=response.status is RequestStatus.succeeded,
            error=node_response.error or response.error,
        )
        return InterfaceLocalRuntimeSnapshot(
            service_host=await self._probe_service_host(),
            node_runtime=node_runtime,
        )

    async def _probe_service_host(self) -> InterfaceHostServiceLocalServiceHostState:
        started_at_s = time.monotonic()
        try:
            socket_path = self.resolve_service_host_socket_path()
        except Exception as exc:
            return InterfaceHostServiceLocalServiceHostState(
                managed=self.is_managed,
                supported=_is_supported_local_platform(),
                socket_path=None,
                status="failed",
                error=str(exc),
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        if not self.is_managed:
            return InterfaceHostServiceLocalServiceHostState(
                managed=False,
                supported=_is_supported_local_platform(),
                socket_path=str(socket_path),
                status="remote",
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        if not _is_supported_local_platform():
            return InterfaceHostServiceLocalServiceHostState(
                managed=True,
                supported=False,
                socket_path=str(socket_path),
                status="unsupported",
                error="Local Service host bootstrap is not supported on this platform.",
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        try:
            response = await self.probe_service_host_handshake(
                timeout_s=_DEFAULT_HANDSHAKE_TIMEOUT_S,
            )
        except FileNotFoundError:
            if (
                self._resolve_running_service_host_pid(socket_path=socket_path)
                is not None
            ):
                return InterfaceHostServiceLocalServiceHostState(
                    managed=True,
                    supported=True,
                    socket_path=str(socket_path),
                    status="starting",
                    recent_log_lines=self._tail_service_host_log_lines(),
                    probe_duration_ms=_elapsed_ms(started_at_s),
                    last_checked_at=_utc_now_iso(),
                )
            return InterfaceHostServiceLocalServiceHostState(
                managed=True,
                supported=True,
                socket_path=str(socket_path),
                status="absent",
                error="Local Service host socket was not found.",
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        except ConnectionRefusedError:
            return InterfaceHostServiceLocalServiceHostState(
                managed=True,
                supported=True,
                socket_path=str(socket_path),
                status="starting",
                error="Local Service host is not accepting connections yet.",
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        except TimeoutError:
            if (
                self._resolve_running_service_host_pid(socket_path=socket_path)
                is not None
            ):
                return InterfaceHostServiceLocalServiceHostState(
                    managed=True,
                    supported=True,
                    socket_path=str(socket_path),
                    status="starting",
                    error="Local Service host is running but did not answer the readiness handshake yet.",
                    recent_log_lines=self._tail_service_host_log_lines(),
                    probe_duration_ms=_elapsed_ms(started_at_s),
                    last_checked_at=_utc_now_iso(),
                )
            return InterfaceHostServiceLocalServiceHostState(
                managed=True,
                supported=True,
                socket_path=str(socket_path),
                status="failed",
                error="Local Service host did not answer the readiness handshake.",
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        except Exception as exc:
            return InterfaceHostServiceLocalServiceHostState(
                managed=True,
                supported=True,
                socket_path=str(socket_path),
                status="failed",
                error=str(exc),
                recent_log_lines=self._tail_service_host_log_lines(),
                probe_duration_ms=_elapsed_ms(started_at_s),
                last_checked_at=_utc_now_iso(),
            )
        return InterfaceHostServiceLocalServiceHostState(
            managed=True,
            supported=True,
            socket_path=str(socket_path),
            available=True,
            ready=response.readiness.is_ready,
            status=response.readiness.status.value,
            host_id=response.host_id,
            host_version=response.host_version,
            protocol_version=response.protocol_version,
            capabilities=tuple(
                capability.capability_id for capability in response.capabilities
            ),
            error=response.readiness.reason,
            recent_log_lines=self._tail_service_host_log_lines(),
            probe_duration_ms=_elapsed_ms(started_at_s),
            last_checked_at=_utc_now_iso(),
        )

    async def _describe_node_runtime(
        self,
        *,
        service_host: InterfaceHostServiceLocalServiceHostState,
    ) -> InterfaceHostServiceLocalNodeRuntimeState:
        if not service_host.managed:
            return InterfaceHostServiceLocalNodeRuntimeState(managed=False)
        if not service_host.ready:
            return InterfaceHostServiceLocalNodeRuntimeState(
                managed=True,
                available=False,
                error=service_host.error,
            )
        client = self._service_host_client()
        try:
            response = await client.send_request(
                request=self._node_request(operation=DescribeNodeRuntimeRequest()),
                timeout_s=_DEFAULT_HANDSHAKE_TIMEOUT_S,
            )
        except Exception as exc:
            return InterfaceHostServiceLocalNodeRuntimeState(
                managed=True,
                available=False,
                error=str(exc),
            )
        if not isinstance(response.response_payload, Mapping):
            return InterfaceHostServiceLocalNodeRuntimeState(
                managed=True,
                available=False,
                error=(
                    response.error
                    or "node_deploy.describe_node_runtime returned no response payload"
                ),
            )
        node_response = parse_node_deploy_operation_response(response.response_payload)
        return self._node_state_from_runtime_status(
            runtime_status=node_response.runtime_status,
            available=response.status is RequestStatus.succeeded,
            error=node_response.error or response.error,
        )

    def _node_request(
        self,
        *,
        operation: (
            DescribeNodeRuntimeRequest
            | EnsureNodeRuntimeStartedRequest
            | RestartNodeRuntimeRequest
            | StopNodeRuntimeRequest
            | TailNodeRuntimeLogsRequest
        ),
    ) -> ServiceOperationRequest:
        context = ServiceOperationContext(
            actor_id=None,
            environment_id=_stable_context_uuid(self.namespace, "environment"),
            process_id=_stable_context_uuid(self.namespace, "process"),
            thread_id=_stable_context_uuid(self.namespace, "thread"),
            branch_id=_stable_context_uuid(self.namespace, "branch"),
            projection_hash="interface.local_runtime",
        )
        return ServiceOperationRequest(
            context=context,
            service="node_deploy",
            operation=operation.model_dump(mode="json", exclude_none=True),
        )

    def _service_host_client(self) -> ServiceHostDuplexClient:
        return ServiceHostDuplexClient(
            endpoint=DuplexIpcEndpoint.unix_socket(
                socket_path=str(self.resolve_service_host_socket_path())
            )
        )

    def _resolve_running_service_host_pid(self, *, socket_path: Path) -> int | None:
        if not sys.platform.startswith("linux"):
            return None
        pid = _resolve_service_host_pid_linux(socket_path=socket_path)
        if pid is None or not _is_pid_running(pid):
            return None
        return pid

    def _write_service_host_bootstrap_config(self, *, socket_path: Path) -> Path:
        if self.service_host_bootstrap_config_path is not None:
            if not self.service_host_bootstrap_config_path.is_file():
                raise FileNotFoundError(
                    "Interface local ServiceHost bootstrap config was not found: "
                    f"{self.service_host_bootstrap_config_path}"
                )
            return self.service_host_bootstrap_config_path
        config_path = self.resolve_service_host_bootstrap_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "[ipc]",
            f"socket_path = {json.dumps(str(socket_path))}",
        ]
        if self.service_host_implementation_toml_paths:
            lines.extend(
                [
                    "",
                    "[implementation_packages]",
                    "toml_paths = [",
                ]
            )
            lines.extend(
                f"  {json.dumps(str(path))},"
                for path in self.service_host_implementation_toml_paths
            )
            lines.append("]")
        config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return config_path

    def _tail_service_host_log_lines(self, *, line_count: int = 12) -> tuple[str, ...]:
        log_path = self.resolve_service_host_log_path()
        try:
            text = log_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return ()
        except OSError as exc:
            return (f"Could not read local Service host log {log_path}: {exc}",)
        lines = tuple(line.strip() for line in text.splitlines() if line.strip())
        return lines[-max(1, line_count) :]

    async def _stop_service_host(self, *, timeout_s: float) -> None:
        socket_path = self.resolve_service_host_socket_path()
        pid = None
        if sys.platform.startswith("linux"):
            pid = _resolve_service_host_pid_linux(socket_path=socket_path)
        if pid is None:
            await self._cleanup_stale_service_host_socket(socket_path=socket_path)
            return

        os.kill(pid, signal.SIGTERM)
        deadline = asyncio.get_running_loop().time() + max(timeout_s, 0.1)
        while asyncio.get_running_loop().time() < deadline:
            if not _is_pid_running(pid):
                await self._cleanup_stale_service_host_socket(socket_path=socket_path)
                return
            await asyncio.sleep(0.2)

        with suppress(ProcessLookupError):
            os.kill(pid, signal.SIGKILL)

        force_deadline = asyncio.get_running_loop().time() + 2.0
        while asyncio.get_running_loop().time() < force_deadline:
            if not _is_pid_running(pid):
                await self._cleanup_stale_service_host_socket(socket_path=socket_path)
                return
            await asyncio.sleep(0.1)

        raise RuntimeError(
            "Local Service host did not stop "
            f"within {timeout_s + 2.0:.1f}s (socket={socket_path}, pid={pid})."
        )

    async def _cleanup_stale_service_host_socket(self, *, socket_path: Path) -> None:
        if not socket_path.exists():
            return
        client = self._service_host_client()
        try:
            await client.send_handshake(
                request=ServiceHostHandshakeRequest(
                    supported_protocol_versions=(SERVICE_HOST_PROTOCOL_VERSION,),
                ),
                timeout_s=_DEFAULT_HANDSHAKE_TIMEOUT_S,
            )
        except Exception:
            with suppress(FileNotFoundError):
                socket_path.unlink()

    @staticmethod
    def _node_state_from_runtime_status(
        *,
        runtime_status: NodeDeployRuntimeStatus | None,
        available: bool,
        error: str | None,
        recent_log_lines: tuple[str, ...] = (),
    ) -> InterfaceHostServiceLocalNodeRuntimeState:
        if runtime_status is None:
            return InterfaceHostServiceLocalNodeRuntimeState(
                managed=True,
                available=available,
                error=error,
                recent_log_lines=recent_log_lines,
            )
        return InterfaceHostServiceLocalNodeRuntimeState(
            managed=True,
            available=available,
            ready=runtime_status.phase is NodeDeployRuntimePhase.ready,
            phase=runtime_status.phase.value,
            active_target_id=runtime_status.active_target_id,
            target_key=(
                runtime_status.target.target_key
                if runtime_status.target is not None
                else None
            ),
            display_name=(
                runtime_status.target.display_name
                if runtime_status.target is not None
                else None
            ),
            backend_kind=runtime_status.backend_kind,
            is_active=runtime_status.is_active,
            is_healthy=runtime_status.is_healthy,
            node_base_url=runtime_status.node_base_url,
            node_websocket_path=runtime_status.node_websocket_path,
            summary=runtime_status.summary,
            error=error or runtime_status.error,
            updated_at=runtime_status.updated_at,
            recent_log_lines=recent_log_lines or tuple(runtime_status.recent_log_lines),
            target_statuses=tuple(
                InterfaceHostServiceOperationTargetState(
                    target_id=item.target_id,
                    display_name=item.display_name,
                    kind=item.kind,
                    endpoint=item.endpoint,
                    phase=item.phase,
                    is_active=item.is_active,
                    is_healthy=item.is_healthy,
                    summary=item.summary,
                    error=item.error,
                    detail_lines=tuple(item.detail_lines)
                    or _detail_lines_for_target(
                        target_id=item.target_id,
                        display_name=item.display_name,
                        summary=item.summary,
                        error=item.error,
                        recent_log_lines=recent_log_lines
                        or tuple(runtime_status.recent_log_lines),
                    ),
                )
                for item in runtime_status.target_statuses
            ),
        )


__all__ = [
    "InterfaceLocalRuntimeController",
    "InterfaceLocalRuntimeSnapshot",
]
