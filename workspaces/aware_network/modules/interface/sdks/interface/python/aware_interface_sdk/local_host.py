from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import os
from pathlib import Path
import tempfile
import time
from typing import Any
from urllib.parse import urlparse
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel


DEFAULT_INTERFACE_LOCAL_HOST_HANDLE = "dev-localhost"
DEFAULT_INTERFACE_LOCAL_NAMESPACE = "default"
DEFAULT_INTERFACE_LOCAL_HOST_LABEL = "interface-sdk-local"
INTERFACE_SDK_REPO_ROOT_ENV_VARS = (
    "AWARE_INTERFACE_SDK_REPO_ROOT",
    "AWARE_INTERFACE_REPO_ROOT",
    "AWARE_INTERFACE_SERVICE_REPO_ROOT",
    "AWARE_INTERFACE_SERVICE_REPOSITORY_ROOT",
    "AWARE_REPO_ROOT",
    "AWARE_REPOSITORY_ROOT",
)

_SERVICE_HOST_SOCKET_FILENAME = "interface-service.sock"
_READY_FILENAME = "interface-service.ready.json"
_SOCKET_SAFE_BYTES = 100
_TRUTHY = frozenset({"1", "true", "yes", "y", "on"})
_FALSY = frozenset({"0", "false", "no", "n", "off"})
_LIVE_RUNTIME_BLOCKING_WARNINGS = frozenset(
    {
        "host_runtime_unbound",
        "live_host_unavailable",
        "runtime_unbound",
        "transport_unbound",
    }
)


@dataclass(frozen=True, slots=True)
class InterfaceLocalHostContext:
    repo_root: Path
    host_handle: str
    namespace: str
    authority_root: Path
    state_home: Path
    service_host_socket_path: Path
    ready_file_path: Path
    endpoint: str | None = None
    interface_package_name: str | None = None
    auth_token: str | None = None
    auth_actor_id: UUID | None = None
    auth_actor_source: str | None = None
    allow_degraded_local_shell: bool = False
    require_live_runtime: bool = True
    state_home_source: str = "default"
    socket_source: str = "default"

    @property
    def control_socket_path(self) -> Path:
        """Compatibility alias for callers that still pass a socket path around."""

        return self.service_host_socket_path

    def to_evidence(self) -> dict[str, object]:
        return {
            "repo_root": self.repo_root.as_posix(),
            "host_handle": self.host_handle,
            "namespace": self.namespace,
            "authority_root": self.authority_root.as_posix(),
            "state_home": self.state_home.as_posix(),
            "service_host_socket_path": self.service_host_socket_path.as_posix(),
            "ready_file_path": self.ready_file_path.as_posix(),
            "endpoint": self.endpoint,
            "interface_package_name": self.interface_package_name,
            "auth_token_present": self.auth_token is not None,
            "auth_actor_id": str(self.auth_actor_id) if self.auth_actor_id else None,
            "auth_actor_source": self.auth_actor_source,
            "allow_degraded_local_shell": self.allow_degraded_local_shell,
            "require_live_runtime": self.require_live_runtime,
            "state_home_source": self.state_home_source,
            "socket_source": self.socket_source,
        }


async def ensure_local_interface_host(
    *,
    context: InterfaceLocalHostContext,
    start_timeout_s: float = 60.0,
    probe_timeout_s: float = 2.0,
    ensure_namespace: bool = True,
    restart_if_stale: bool = True,
) -> dict[str, object]:
    """Ensure the local Interface service host is reachable for one SDK context."""

    started = time.perf_counter()
    timings: dict[str, float] = {}
    with _interface_host_env(context):
        service_host_config = _resolve_interface_service_host_config(context)
        service_host_started = time.perf_counter()
        service_host = await _ensure_interface_service_host(
            config=service_host_config,
            start_timeout_s=start_timeout_s,
            probe_timeout_s=probe_timeout_s,
            cleanup_stale=restart_if_stale,
        )
        timings["service_host_ensure_duration_s"] = _duration_since(
            service_host_started
        )
        action = str(service_host.get("action") or "unknown")

    namespace_payload: object | None = None
    warnings: tuple[str, ...] = ()
    blocking_warnings: tuple[str, ...] = ()
    service_host_healthy = service_host.get("healthy") is True
    if ensure_namespace and service_host_healthy:
        namespace_started = time.perf_counter()
        client = _build_interface_sdk_client(
            socket_path=context.service_host_socket_path,
            state_home=context.state_home,
            request_timeout_s=(
                start_timeout_s if context.require_live_runtime else probe_timeout_s
            ),
            actor_id=context.auth_actor_id,
            invocation_context=_service_actor_invocation_context(context),
        )
        namespace_timeout_s = (
            start_timeout_s if context.require_live_runtime else probe_timeout_s
        )
        namespace_payload = await _await_with_timeout(
            client.ensure_namespace(
                namespace=context.namespace,
                auth_token=context.auth_token,
                endpoint=context.endpoint,
                host_label=DEFAULT_INTERFACE_LOCAL_HOST_LABEL,
                environment_config_id=None,
            ),
            timeout_s=namespace_timeout_s,
        )
        timings["namespace_ensure_duration_s"] = _duration_since(namespace_started)
        warnings = _collect_host_state_warnings(namespace_payload)
        blocking_warnings = tuple(
            warning
            for warning in warnings
            if warning in _LIVE_RUNTIME_BLOCKING_WARNINGS
        )

    healthy = service_host_healthy and not (
        context.require_live_runtime and blocking_warnings
    )
    if not service_host_healthy:
        status = str(service_host.get("status") or "service_host_unavailable")
    else:
        status = "ready" if healthy else "live_runtime_unavailable"
    timings["total_duration_s"] = _duration_since(started)
    return {
        "operation": "interface_local_host_ensure",
        "action": action,
        "status": status,
        "healthy": healthy,
        "context": context.to_evidence(),
        "service_host": _jsonable(service_host),
        "namespace": _jsonable(namespace_payload),
        "warnings": list(warnings),
        "blocking_warnings": list(blocking_warnings),
        "timings": timings,
        "duration_s": timings["total_duration_s"],
    }


def resolve_interface_local_host_context(
    *,
    namespace: str | None = None,
    socket_path: str | Path | None = None,
    state_home: str | Path | None = None,
    authority_root: str | Path | None = None,
    repo_root: str | Path | None = None,
    endpoint: str | None = None,
    interface_package_name: str | None = None,
    auth_token: str | None = None,
    auth_actor_id: str | UUID | None = None,
    allow_degraded_local_shell: bool | None = None,
    require_live_runtime: bool | None = None,
    host_handle: str | None = None,
) -> InterfaceLocalHostContext:
    resolved_repo_root = _resolve_repo_root(repo_root)
    resolved_host_handle = _first_text(
        host_handle,
        os.environ.get("AWARE_INTERFACE_LOCAL_HOST_HANDLE"),
        default=DEFAULT_INTERFACE_LOCAL_HOST_HANDLE,
    )
    resolved_namespace = _first_text(
        namespace,
        os.environ.get("AWARE_INTERFACE_NAMESPACE"),
        default=DEFAULT_INTERFACE_LOCAL_NAMESPACE,
    )
    resolved_authority_root = _resolve_authority_root(
        repo_root=resolved_repo_root,
        host_handle=resolved_host_handle,
        value=authority_root,
    )
    resolved_state_home, state_home_source = _resolve_state_home(
        authority_root=resolved_authority_root,
        value=state_home,
    )
    resolved_socket_path, socket_source = _resolve_service_host_socket_path(
        authority_root=resolved_authority_root,
        state_home=resolved_state_home,
        state_home_source=state_home_source,
        value=socket_path,
    )
    resolved_auth_actor_id, resolved_auth_actor_source = (
        resolve_local_service_host_actor_context_identity(
            explicit_actor_id=auth_actor_id,
            socket_path=resolved_socket_path,
            state_home=resolved_state_home,
            repo_root=resolved_repo_root,
        )
    )
    return InterfaceLocalHostContext(
        repo_root=resolved_repo_root,
        host_handle=resolved_host_handle,
        namespace=resolved_namespace,
        authority_root=resolved_authority_root,
        state_home=resolved_state_home,
        service_host_socket_path=resolved_socket_path,
        ready_file_path=(resolved_socket_path.parent / _READY_FILENAME).resolve(),
        endpoint=_resolve_endpoint(endpoint),
        interface_package_name=_resolve_interface_package_name(interface_package_name),
        auth_token=_resolve_auth_token(auth_token),
        auth_actor_id=resolved_auth_actor_id,
        auth_actor_source=resolved_auth_actor_source,
        allow_degraded_local_shell=_resolve_bool(
            value=allow_degraded_local_shell,
            env_name="AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL",
            default=False,
        ),
        require_live_runtime=_resolve_bool(
            value=require_live_runtime,
            env_name="AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME",
            default=True,
        ),
        state_home_source=state_home_source,
        socket_source=socket_source,
    )


@contextmanager
def _interface_host_env(context: InterfaceLocalHostContext) -> Iterator[None]:
    updates: dict[str, str | None] = {
        "AWARE_REPO_ROOT": str(context.repo_root),
        "AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH": str(
            context.service_host_socket_path
        ),
        "AWARE_INTERFACE_SERVICE_SOCKET_PATH": str(context.service_host_socket_path),
        "AWARE_INTERFACE_SERVICE_STATE_HOME": str(context.state_home),
        "AWARE_STATE_HOME": str(context.state_home),
        "AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL": _bool_env(
            context.allow_degraded_local_shell
        ),
        "AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME": _bool_env(
            context.require_live_runtime
        ),
    }
    if context.endpoint is not None:
        updates["AWARE_INTERFACE_SERVICE_ENDPOINT"] = context.endpoint
    if context.interface_package_name is not None:
        updates["AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME"] = (
            context.interface_package_name
        )
    if context.auth_token is not None:
        updates["AWARE_AUTH_TOKEN"] = context.auth_token

    previous = {key: os.environ.get(key) for key in updates}
    try:
        for key, value in updates.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _resolve_interface_service_host_config(
    context: InterfaceLocalHostContext,
) -> Any:
    from aware_interface_service.local_host import (
        resolve_local_interface_service_host_config,
    )

    return resolve_local_interface_service_host_config(
        repo_root=context.repo_root,
        socket_path=context.service_host_socket_path,
        ready_file_path=context.ready_file_path,
        state_root_path=context.state_home / "servicehost-state",
    )


async def _ensure_interface_service_host(**kwargs: Any) -> dict[str, object]:
    from aware_interface_service.local_host import ensure_local_interface_service_host

    return await ensure_local_interface_service_host(**kwargs)


def _build_interface_sdk_client(
    *,
    socket_path: Path,
    state_home: Path,
    request_timeout_s: float,
    actor_id: UUID | None = None,
    invocation_context: Mapping[str, object] | None = None,
) -> Any:
    from aware_interface_sdk.client import InterfaceSdkClient

    return InterfaceSdkClient.from_local_service_host(
        socket_path=socket_path,
        state_home=state_home,
        request_timeout_s=request_timeout_s,
        actor_id=actor_id,
        invocation_context=invocation_context,
    )


async def _await_with_timeout(awaitable: Any, *, timeout_s: float) -> Any:
    import asyncio

    return await asyncio.wait_for(awaitable, timeout=max(timeout_s, 0.1))


def _resolve_repo_root(value: str | Path | None) -> Path:
    if value is not None and str(value).strip():
        return Path(value).expanduser().resolve()
    for env_name in INTERFACE_SDK_REPO_ROOT_ENV_VARS:
        env_repo = _clean_text(os.environ.get(env_name))
        if env_repo is not None:
            return Path(env_repo).expanduser().resolve()
    raise RuntimeError(
        "Interface SDK local host repo root is required. Pass repo_root or set "
        f"one of {', '.join(INTERFACE_SDK_REPO_ROOT_ENV_VARS)}."
    )


def _resolve_authority_root(
    *,
    repo_root: Path,
    host_handle: str,
    value: str | Path | None,
) -> Path:
    raw = (
        Path(str(value).strip())
        if value is not None and str(value).strip()
        else Path("targets/interface-authorities") / host_handle
    )
    if raw.is_absolute():
        return raw.expanduser().resolve()
    return (repo_root / raw).expanduser().resolve()


def _resolve_state_home(
    *,
    authority_root: Path,
    value: str | Path | None,
) -> tuple[Path, str]:
    if value is not None and str(value).strip():
        return Path(value).expanduser().resolve(), "argument"
    for env_name in ("AWARE_INTERFACE_SERVICE_STATE_HOME", "AWARE_STATE_HOME"):
        env_value = _clean_text(os.environ.get(env_name))
        if env_value is not None:
            return Path(env_value).expanduser().resolve(), env_name
    return (authority_root / "state").resolve(), "default"


def _resolve_service_host_socket_path(
    *,
    authority_root: Path,
    state_home: Path,
    state_home_source: str,
    value: str | Path | None,
) -> tuple[Path, str]:
    if value is not None and str(value).strip():
        return Path(value).expanduser().resolve(), "argument"
    for env_name in (
        "AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH",
        "AWARE_INTERFACE_SERVICE_SOCKET_PATH",
    ):
        env_socket = _clean_text(os.environ.get(env_name))
        if env_socket is not None:
            return Path(env_socket).expanduser().resolve(), env_name
    legacy_env_socket = _clean_text(os.environ.get("AWARE_INTERFACE_CONTROL_SOCKET"))
    if legacy_env_socket is not None:
        return (
            Path(legacy_env_socket).expanduser().resolve(),
            "AWARE_INTERFACE_CONTROL_SOCKET_compat",
        )
    if state_home_source != "default":
        state_socket = (state_home / _SERVICE_HOST_SOCKET_FILENAME).resolve()
        if _socket_path_is_length_safe(state_socket):
            return state_socket, state_home_source
        return (
            _default_short_socket_path(identity_root=state_home),
            f"{state_home_source}:short_socket",
        )
    authority_socket = (
        authority_root / "services" / "interface" / _SERVICE_HOST_SOCKET_FILENAME
    ).resolve()
    if _socket_path_is_length_safe(authority_socket):
        return authority_socket, "authority_root"
    return _default_short_socket_path(identity_root=authority_root), "short_socket"


def _default_short_socket_path(*, identity_root: Path) -> Path:
    identity_hash = hashlib.sha256(
        identity_root.expanduser().resolve().as_posix().encode("utf-8")
    ).hexdigest()[:16]
    return (
        Path(tempfile.gettempdir())
        / "aware-interface"
        / "interface-service"
        / identity_hash
        / _SERVICE_HOST_SOCKET_FILENAME
    ).resolve()


def _socket_path_is_length_safe(path: Path) -> bool:
    path_bytes = path.expanduser().resolve().as_posix().encode("utf-8")
    return len(path_bytes) < _SOCKET_SAFE_BYTES


def _service_actor_invocation_context(
    context: InterfaceLocalHostContext,
) -> dict[str, object] | None:
    if context.auth_actor_id is None:
        return None
    return {
        "actor_context": {
            "status": "ready",
            "kind": "agent_operator",
            "source": (
                context.auth_actor_source or "interface_sdk.local_host.runtime_auth"
            ),
            "actor_id": str(context.auth_actor_id),
        }
    }


def _resolve_endpoint(value: str | None) -> str | None:
    explicit = _clean_text(value)
    if explicit is not None:
        return explicit
    configured = _clean_text(os.environ.get("AWARE_INTERFACE_SERVICE_ENDPOINT"))
    if configured is not None:
        return configured
    node_base_url = _clean_text(os.environ.get("AWARE_NODE_BASE_URL"))
    if node_base_url is None:
        return None
    parsed = urlparse(node_base_url)
    if parsed.scheme == "https":
        return f"wss://{node_base_url.removeprefix('https://')}"
    if parsed.scheme == "http":
        return f"ws://{node_base_url.removeprefix('http://')}"
    return node_base_url


def _resolve_interface_package_name(value: str | None) -> str | None:
    explicit = _clean_text(value)
    if explicit is not None:
        return explicit
    configured = _clean_text(
        os.environ.get("AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME")
    )
    if configured is not None:
        return configured
    declared = _clean_text(os.environ.get("AWARE_FLUTTER_APP_INTERFACE_PACKAGES"))
    if declared is None:
        return None
    first = _clean_text(declared.split(",", 1)[0])
    return first


def _resolve_auth_token(value: str | None) -> str | None:
    explicit = _clean_text(value)
    if explicit is not None:
        return explicit
    return _clean_text(os.environ.get("AWARE_AUTH_TOKEN")) or _clean_text(
        os.environ.get("AWARE_APT_TOKEN")
    )


def resolve_local_service_host_actor_context_identity(
    *,
    explicit_actor_id: str | UUID | None = None,
    socket_path: Path | None = None,
    state_home: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[UUID | None, str | None]:
    explicit = _coerce_actor_uuid(explicit_actor_id)
    if explicit is not None:
        return explicit, "interface_sdk.local_host.runtime_auth"
    for env_name in (
        "AWARE_INTERFACE_AUTH_ACTOR_ID",
        "AWARE_NODE_RUNTIME_AUTH_ACTOR_ID",
        "AWARE_RUNTIME_AUTH_ACTOR_ID",
    ):
        env_actor_id = _coerce_actor_uuid(os.environ.get(env_name))
        if env_actor_id is not None:
            return env_actor_id, "interface_sdk.local_host.runtime_auth"
    identity_root = state_home or (
        socket_path.parent if socket_path is not None else None
    )
    if identity_root is None:
        identity_root = repo_root or Path.cwd()
    seed = (
        "aware:interface-sdk-local-host:local-operator:"
        f"{identity_root.expanduser().resolve().as_posix()}"
    )
    return uuid5(NAMESPACE_URL, seed), "interface_sdk.local_host.local_operator"


def _coerce_actor_uuid(value: str | UUID | None) -> UUID | None:
    if isinstance(value, UUID):
        return value
    explicit = _clean_text(value)
    if explicit is not None:
        return UUID(explicit)
    return None


def _resolve_bool(
    *,
    value: bool | None,
    env_name: str,
    default: bool,
) -> bool:
    if value is not None:
        return value
    env_value = _clean_text(os.environ.get(env_name))
    if env_value is None:
        return default
    normalized = env_value.lower()
    if normalized in _TRUTHY:
        return True
    if normalized in _FALSY:
        return False
    raise ValueError(f"Unsupported boolean value for {env_name}: {env_value!r}")


def _first_text(*values: str | None, default: str) -> str:
    for value in values:
        text = _clean_text(value)
        if text is not None:
            return text
    return default


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_env(value: bool) -> str:
    return "1" if value else "0"


def _collect_host_state_warnings(value: object | None) -> tuple[str, ...]:
    host_state = getattr(value, "host_state", None)
    warnings: list[str] = []
    warnings.extend(_string_sequence(getattr(host_state, "warnings", ())))
    runtime = getattr(host_state, "runtime", None)
    warnings.extend(_string_sequence(getattr(runtime, "warnings", ())))
    return tuple(dict.fromkeys(warnings))


def _string_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if str(item).strip())


def _duration_since(started: float) -> float:
    return time.perf_counter() - started


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=True)
    if is_dataclass(value) and not isinstance(value, type):
        return _jsonable(asdict(value))
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if hasattr(value, "__dict__"):
        return {
            str(key): _jsonable(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return value


__all__ = [
    "DEFAULT_INTERFACE_LOCAL_HOST_HANDLE",
    "DEFAULT_INTERFACE_LOCAL_HOST_LABEL",
    "DEFAULT_INTERFACE_LOCAL_NAMESPACE",
    "InterfaceLocalHostContext",
    "INTERFACE_SDK_REPO_ROOT_ENV_VARS",
    "ensure_local_interface_host",
    "resolve_local_service_host_actor_context_identity",
    "resolve_interface_local_host_context",
]
