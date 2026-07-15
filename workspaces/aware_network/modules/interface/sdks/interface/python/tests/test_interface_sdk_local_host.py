from __future__ import annotations

import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest

from aware_interface_sdk import local_host
from aware_interface_sdk.local_host import (
    INTERFACE_SDK_REPO_ROOT_ENV_VARS,
    ensure_local_interface_host,
    resolve_interface_local_host_context,
)


def test_resolve_interface_local_host_context_defaults_to_shared_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_STATE_HOME", raising=False)
    monkeypatch.delenv("AWARE_STATE_HOME", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_SOCKET_PATH", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_CONTROL_SOCKET", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_ENDPOINT", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME", raising=False)
    monkeypatch.setenv("AWARE_NODE_BASE_URL", "http://localhost:8000")
    monkeypatch.setenv("AWARE_FLUTTER_APP_INTERFACE_PACKAGES", "aware-control-interface")

    context = resolve_interface_local_host_context(
        repo_root=repo_root,
        namespace="codex",
    )

    assert context.repo_root == repo_root.resolve()
    assert context.namespace == "codex"
    assert context.host_handle == "dev-localhost"
    assert context.authority_root == (
        repo_root / "targets" / "interface-authorities" / "dev-localhost"
    ).resolve()
    assert context.state_home == (context.authority_root / "state").resolve()
    if context.socket_source == "authority_root":
        assert context.control_socket_path == (
            context.authority_root / "services" / "interface" / "interface-service.sock"
        ).resolve()
    else:
        assert context.socket_source == "short_socket"
        assert context.control_socket_path.parent.parent == (
            Path(tempfile.gettempdir()) / "aware-interface" / "interface-service"
        )
    assert context.service_host_socket_path == context.control_socket_path
    assert context.endpoint == "ws://localhost:8000"
    assert context.interface_package_name == "aware-control-interface"
    assert context.allow_degraded_local_shell is False
    assert context.require_live_runtime is True


def test_resolve_interface_local_host_context_uses_explicit_env_repo_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name in INTERFACE_SDK_REPO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setenv(INTERFACE_SDK_REPO_ROOT_ENV_VARS[0], str(tmp_path))

    context = resolve_interface_local_host_context(namespace="codex")

    assert context.repo_root == tmp_path.resolve()


def test_resolve_interface_local_host_context_requires_explicit_repo_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for env_name in INTERFACE_SDK_REPO_ROOT_ENV_VARS:
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(RuntimeError, match="repo root is required"):
        resolve_interface_local_host_context(namespace="codex")


def test_resolve_interface_local_host_context_honors_state_home_socket_env(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    state_home = tmp_path / "state"
    monkeypatch.setenv("AWARE_INTERFACE_SERVICE_STATE_HOME", str(state_home))

    context = resolve_interface_local_host_context(
        repo_root=tmp_path,
        endpoint="wss://node.example",
    )

    assert context.state_home == state_home.resolve()
    assert context.state_home_source == "AWARE_INTERFACE_SERVICE_STATE_HOME"
    state_socket = (state_home / "interface-service.sock").resolve()
    if local_host._socket_path_is_length_safe(state_socket):
        assert context.control_socket_path == state_socket
        assert context.socket_source == "AWARE_INTERFACE_SERVICE_STATE_HOME"
    else:
        assert context.control_socket_path.parent.parent == (
            Path(tempfile.gettempdir()) / "aware-interface" / "interface-service"
        )
        assert context.socket_source == "AWARE_INTERFACE_SERVICE_STATE_HOME:short_socket"
    assert context.endpoint == "wss://node.example"


def test_resolve_interface_local_host_context_shortens_long_state_home_socket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_SERVICE_SOCKET_PATH", raising=False)
    monkeypatch.delenv("AWARE_INTERFACE_CONTROL_SOCKET", raising=False)
    state_home = (
        tmp_path
        / "aware-interface-node-identity-attention-live-e2e"
        / "interface-sdk"
        / "state"
        / "very-long-state-root"
    )
    state_socket = (state_home / "interface-service.sock").resolve()
    assert not local_host._socket_path_is_length_safe(state_socket)

    context = resolve_interface_local_host_context(
        repo_root=tmp_path,
        state_home=state_home,
    )

    assert context.state_home == state_home.resolve()
    assert context.state_home_source == "argument"
    assert context.socket_source == "argument:short_socket"
    assert context.control_socket_path.parent.parent == (
        Path(tempfile.gettempdir()) / "aware-interface" / "interface-service"
    )
    assert local_host._socket_path_is_length_safe(context.control_socket_path)


@pytest.mark.asyncio
async def test_ensure_local_interface_host_sets_servicehost_env_and_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setenv("AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL", "1")

    async def _fake_ensure_interface_service_host(**kwargs: Any) -> dict[str, object]:
        observed["service_host_kwargs"] = kwargs
        observed["service_host_env"] = {
            key: os.environ.get(key)
            for key in (
                "AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH",
                "AWARE_INTERFACE_SERVICE_SOCKET_PATH",
                "AWARE_INTERFACE_SERVICE_STATE_HOME",
                "AWARE_INTERFACE_SERVICE_ENDPOINT",
                "AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME",
                "AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL",
                "AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME",
                "AWARE_AUTH_TOKEN",
            )
        }
        return {
            "operation": "interface_service_host_ensure",
            "action": "started",
            "status": "ready",
            "healthy": True,
        }

    def _fake_sdk_client(
        *,
        socket_path: Path,
        state_home: Path,
        request_timeout_s: float,
        actor_id: object | None = None,
        invocation_context: dict[str, object] | None = None,
    ) -> _FakeInterfaceSdkClient:
        observed["client_socket_path"] = socket_path
        observed["client_state_home"] = state_home
        observed["client_request_timeout_s"] = request_timeout_s
        observed["client_actor_id"] = actor_id
        observed["client_invocation_context"] = invocation_context
        return _FakeInterfaceSdkClient(observed=observed)

    monkeypatch.setattr(
        local_host,
        "_ensure_interface_service_host",
        _fake_ensure_interface_service_host,
    )
    monkeypatch.setattr(
        local_host,
        "_build_interface_sdk_client",
        _fake_sdk_client,
    )

    auth_actor_id = uuid4()
    context = resolve_interface_local_host_context(
        repo_root=tmp_path,
        namespace="codex",
        endpoint="ws://localhost:8000",
        interface_package_name="aware-control-interface",
        auth_token="apt:test",
        auth_actor_id=auth_actor_id,
        allow_degraded_local_shell=False,
        require_live_runtime=True,
    )

    report = await ensure_local_interface_host(context=context)

    service_config = observed["service_host_kwargs"]["config"]
    assert report["healthy"] is True
    assert report["status"] == "ready"
    assert service_config.socket_path == context.control_socket_path
    assert service_config.repo_root == context.repo_root
    assert service_config.ready_file_path == context.ready_file_path
    assert observed["client_socket_path"] == context.control_socket_path
    assert observed["client_state_home"] == context.state_home
    assert observed["client_request_timeout_s"] == 60.0
    assert observed["client_actor_id"] == auth_actor_id
    assert observed["client_invocation_context"] == {
        "actor_context": {
            "status": "ready",
            "kind": "agent_operator",
            "source": "interface_sdk.local_host.runtime_auth",
            "actor_id": str(auth_actor_id),
        }
    }
    assert observed["namespace_kwargs"] == {
        "namespace": "codex",
        "auth_token": "apt:test",
        "endpoint": "ws://localhost:8000",
        "host_label": "interface-sdk-local",
        "environment_config_id": None,
    }
    assert observed["service_host_env"] == {
        "AWARE_INTERFACE_SERVICE_HOST_SOCKET_PATH": str(context.control_socket_path),
        "AWARE_INTERFACE_SERVICE_SOCKET_PATH": str(context.control_socket_path),
        "AWARE_INTERFACE_SERVICE_STATE_HOME": str(context.state_home),
        "AWARE_INTERFACE_SERVICE_ENDPOINT": "ws://localhost:8000",
        "AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME": "aware-control-interface",
        "AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL": "0",
        "AWARE_INTERFACE_SERVICE_REQUIRE_LIVE_RUNTIME": "1",
        "AWARE_AUTH_TOKEN": "apt:test",
    }
    assert os.environ.get("AWARE_INTERFACE_SERVICE_ALLOW_DEGRADED_LOCAL_SHELL") == "1"


@pytest.mark.asyncio
async def test_ensure_local_interface_host_reports_live_runtime_blockers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_ensure_interface_service_host(**kwargs: Any) -> dict[str, object]:
        _ = kwargs
        return {
            "operation": "interface_service_host_ensure",
            "action": "reused",
            "status": "ready",
            "healthy": True,
        }

    def _fake_sdk_client(**kwargs: Any) -> _FakeInterfaceSdkClient:
        _ = kwargs
        return _FakeInterfaceSdkClient(warnings=("runtime_unbound",))

    monkeypatch.setattr(
        local_host,
        "_ensure_interface_service_host",
        _fake_ensure_interface_service_host,
    )
    monkeypatch.setattr(
        local_host,
        "_build_interface_sdk_client",
        _fake_sdk_client,
    )

    context = resolve_interface_local_host_context(
        repo_root=tmp_path,
        namespace="codex",
        require_live_runtime=True,
    )

    report = await ensure_local_interface_host(context=context)

    assert report["healthy"] is False
    assert report["status"] == "live_runtime_unavailable"
    assert report["blocking_warnings"] == ["runtime_unbound"]


@pytest.mark.asyncio
async def test_ensure_local_interface_host_uses_start_timeout_for_live_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}

    async def _fake_ensure_interface_service_host(**kwargs: Any) -> dict[str, object]:
        _ = kwargs
        return {
            "operation": "interface_service_host_ensure",
            "action": "reused",
            "status": "ready",
            "healthy": True,
        }

    def _fake_sdk_client(**kwargs: Any) -> _FakeInterfaceSdkClient:
        _ = kwargs
        return _FakeInterfaceSdkClient()

    async def _fake_await_with_timeout(awaitable: Any, *, timeout_s: float) -> Any:
        observed["timeout_s"] = timeout_s
        return await awaitable

    monkeypatch.setattr(
        local_host,
        "_ensure_interface_service_host",
        _fake_ensure_interface_service_host,
    )
    monkeypatch.setattr(
        local_host,
        "_build_interface_sdk_client",
        _fake_sdk_client,
    )
    monkeypatch.setattr(
        local_host,
        "_await_with_timeout",
        _fake_await_with_timeout,
    )

    context = resolve_interface_local_host_context(
        repo_root=tmp_path,
        namespace="codex",
        require_live_runtime=True,
    )

    await ensure_local_interface_host(
        context=context,
        start_timeout_s=42.0,
        probe_timeout_s=2.0,
    )

    assert observed["timeout_s"] == 42.0


class _FakeInterfaceSdkClient:
    def __init__(
        self,
        *,
        observed: dict[str, Any] | None = None,
        warnings: tuple[str, ...] = (),
    ) -> None:
        self._observed = observed
        self._warnings = warnings

    async def ensure_namespace(self, **kwargs: Any) -> object:
        if self._observed is not None:
            self._observed["namespace_kwargs"] = kwargs
        return SimpleNamespace(
            namespace=kwargs["namespace"],
            host_state=SimpleNamespace(
                warnings=list(self._warnings),
                runtime=SimpleNamespace(warnings=[]),
            ),
        )
