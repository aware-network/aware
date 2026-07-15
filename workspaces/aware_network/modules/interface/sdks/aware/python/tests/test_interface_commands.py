from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncIterator, Mapping
from contextlib import suppress
from pathlib import Path
from threading import Event, Thread
from typing import Any
from uuid import UUID
from uuid import uuid4
import json

import pytest
from aware_interface_service_dto.comms.models.control_plane import (
    InterfaceActionResponse,
    InterfaceActionRequest,
    InterfaceControlPlaneOperation,
    InterfaceControlPlaneRequest,
    InterfaceControlPlaneResponse,
    InterfaceInvokeApiRequest,
    InterfaceInvokeApiResponse,
    InterfaceSelectProfileResponse,
    InterfaceStopResponse,
    InterfaceStatusRequest,
    InterfaceStatusResponse,
    NamespaceEnsureRequest,
    NamespaceEnsureResponse,
    NamespaceListResponse,
    PingResponse,
)
from aware_interface_service_dto.comms.models.hosted_interface_namespace import (
    HostedInterfaceNamespace,
)
from aware_interface_service_dto.comms.models.interface_host_state import (
    InterfaceAllowedAction,
    InterfaceBackendState,
    InterfaceCurrentScreen,
    InterfaceHostState,
    InterfaceLocalNodeRuntimeState,
    InterfaceLocalServiceHostState,
    InterfaceResolvedPaneDescriptor,
    InterfaceResolvedView,
    InterfaceRuntimeState,
    InterfaceTransportState,
)
from aware_interface_sdk import InterfaceSdkClient
from aware_interface_sdk.local_host import InterfaceLocalHostContext
from aware_sdk import cli
from aware_sdk.commands import interface as interface_command

_PANE_ENDPOINT_ID = UUID("11111111-1111-4111-8111-111111111111")


def test_root_status_dispatches_to_interface_control_client(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(["status", "--namespace", "luis"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {"namespace": "luis"}
    payload = json.loads(captured.out)
    assert payload["namespace"] == "luis"
    assert payload["connected"] is True
    assert payload["actor"]["authenticated"] is True
    assert payload["current_screen"]["screen_key"] == "deployment"
    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0


def test_root_surface_commands_forward_auth_context_to_namespace_admission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setenv("AWARE_AUTH_TOKEN", "apt:env")
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "panes",
            "--namespace",
            "luis",
            "--endpoint",
            "ws://node.example.test",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["namespace"] == "luis"
    assert observed["ensure_namespace"] == {
        "namespace": "luis",
        "auth_token": "apt:env",
        "endpoint": "ws://node.example.test",
        "host_label": None,
        "environment_config_id": None,
        "interface_package_id": None,
        "interface_package_name": None,
    }


def test_root_surface_commands_forward_interface_package_to_namespace_admission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setenv(
        "AWARE_INTERFACE_SERVICE_INTERFACE_PACKAGE_NAME",
        "aware-control-interface",
    )
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "status",
            "--namespace",
            "luis",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["namespace"] == "luis"
    assert observed["ensure_namespace"]["interface_package_name"] == (
        "aware-control-interface"
    )


def test_root_status_reports_structured_interface_host_unavailable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    socket_path = Path("/tmp/missing-interface-control.sock")

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_UnavailableInterfaceControlClient(),
            socket_path=socket_path,
        ),
    )

    exit_code = cli.main(["status", "--namespace", "codex", "--no-ensure-local-host"])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["command"] == "status"
    assert payload["ready"] is False
    assert payload["status"] == "interface_host_unavailable"
    assert payload["product_boundary"] == "interface-renderer"
    assert (
        payload["canonical_rail"]
        == "SDK -> CLI renderer -> Interface -> API -> Services"
    )
    assert payload["operation"] == "interface_status"
    assert payload["reason"] == "socket_not_found"
    assert payload["next_action"] == "start_or_provision_interface_host"
    assert payload["socket_path"] == str(socket_path)


def test_root_status_reports_missing_local_adapter(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _missing_local_service_host(
        *args: object, **kwargs: object
    ) -> InterfaceSdkClient:
        _ = args, kwargs
        raise ModuleNotFoundError(
            "No module named 'aware_interface_service'",
            name="aware_interface_service",
        )

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(_missing_local_service_host),
    )

    exit_code = cli.main(["status", "--namespace", "codex", "--no-ensure-local-host"])

    captured = capsys.readouterr()
    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["command"] == "status"
    assert payload["ready"] is False
    assert payload["operation"] == "interface_client_bootstrap"
    assert payload["reason"] == "local_adapter_not_installed"


def test_root_status_no_ensure_observes_existing_surface_without_admission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(["status", "--namespace", "luis", "--no-ensure-local-host"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["namespace"] == "luis"
    assert observed == {"namespace": "luis"}


def test_root_act_no_ensure_observes_existing_surface_without_admission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "luis",
            "--no-ensure-local-host",
            "deployment",
            "deployment.resolve",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["namespace"] == "luis"
    assert payload["action_key"] == "deployment.resolve"
    assert "ensure_namespace" not in observed
    assert observed["pane_ref"] == "home/main/deployment"
    assert observed["action_key"] == "deployment.resolve"


def test_root_invoke_no_ensure_observes_existing_surface_without_admission(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "invoke",
            "--namespace",
            "luis",
            "--no-ensure-local-host",
            "deployment",
            str(_PANE_ENDPOINT_ID),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "is not exposed by pane" in captured.err
    assert "ensure_namespace" not in observed
    assert "endpoint_ref" not in observed


def test_root_profile_select_dispatches_through_interface_sdk(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "profile",
            "select",
            "--namespace",
            "luis",
            "operator.local_bootstrap",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["namespace"] == "luis"
    assert payload["profile_id"] == "operator.local_bootstrap"
    assert observed["select_profile"] == {
        "namespace": "luis",
        "profile_id": "operator.local_bootstrap",
    }


def test_build_client_ensures_local_host_and_uses_resolved_socket(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    context = InterfaceLocalHostContext(
        repo_root=tmp_path,
        host_handle="dev-localhost",
        namespace="codex",
        authority_root=tmp_path / "authority",
        state_home=tmp_path / "authority" / "state",
        service_host_socket_path=tmp_path / "authority" / "services" / "interface.sock",
        ready_file_path=tmp_path / "authority" / "services" / "interface.ready.json",
        endpoint="ws://localhost:8000",
        interface_package_name="aware-control-interface",
        auth_token="apt:test",
    )

    def _fake_resolve_interface_local_host_context(
        **kwargs: Any,
    ) -> InterfaceLocalHostContext:
        observed["resolve_kwargs"] = kwargs
        return context

    async def _fake_ensure_local_interface_host(**kwargs: Any) -> dict[str, object]:
        observed["ensure_kwargs"] = kwargs
        return {
            "operation": "interface_local_host_ensure",
            "healthy": True,
            "status": "ready",
            "context": context.to_evidence(),
        }

    def _fake_from_local_service_host(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
        request_timeout_s: float = 30.0,
    ) -> InterfaceSdkClient:
        _ = cls, request_timeout_s
        observed["client_kwargs"] = {
            "socket_path": socket_path,
            "state_home": state_home,
        }
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        "aware_interface_sdk.local_host.resolve_interface_local_host_context",
        _fake_resolve_interface_local_host_context,
    )
    monkeypatch.setattr(
        "aware_interface_sdk.local_host.ensure_local_interface_host",
        _fake_ensure_local_interface_host,
    )
    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(_fake_from_local_service_host),
    )

    args = argparse.Namespace(
        namespace="codex",
        socket_path=None,
        state_home=None,
        ensure_local_host=True,
        authority_root=tmp_path / "authority",
        host_handle="dev-localhost",
        endpoint="ws://localhost:8000",
        auth_token="apt:test",
        interface_package_name="aware-control-interface",
        allow_degraded_local_shell=False,
        require_live_runtime=True,
        local_host_start_timeout_s=10.0,
        local_host_probe_timeout_s=1.5,
    )

    client = interface_command._build_client(args)

    assert isinstance(client, InterfaceSdkClient)
    assert observed["resolve_kwargs"] == {
        "namespace": "codex",
        "socket_path": None,
        "state_home": None,
        "authority_root": tmp_path / "authority",
        "endpoint": "ws://localhost:8000",
        "interface_package_name": "aware-control-interface",
        "auth_token": "apt:test",
        "allow_degraded_local_shell": False,
        "require_live_runtime": True,
        "host_handle": "dev-localhost",
    }
    assert observed["ensure_kwargs"]["context"] == context
    assert observed["ensure_kwargs"]["start_timeout_s"] == 10.0
    assert observed["ensure_kwargs"]["probe_timeout_s"] == 1.5
    assert observed["client_kwargs"] == {
        "socket_path": context.control_socket_path,
        "state_home": context.state_home,
    }
    assert args.socket_path == context.control_socket_path
    assert args.state_home == context.state_home
    assert args._interface_local_host_ensure["status"] == "ready"


def test_build_client_uses_interface_control_socket_env_without_local_ensure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    control_socket_path = tmp_path / "interface-control.sock"
    monkeypatch.setenv("AWARE_INTERFACE_CONTROL_SOCKET", str(control_socket_path))

    def _fake_from_local_control(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> InterfaceSdkClient:
        _ = cls
        observed["client_kwargs"] = {
            "socket_path": socket_path,
            "state_home": state_home,
        }
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_control",
        classmethod(_fake_from_local_control),
    )

    args = argparse.Namespace(
        namespace="codex",
        socket_path=None,
        control_socket_path=None,
        state_home=None,
        ensure_local_host=False,
    )

    client = interface_command._build_client(args)

    assert isinstance(client, InterfaceSdkClient)
    assert observed["client_kwargs"] == {
        "socket_path": control_socket_path.resolve(),
        "state_home": None,
    }


def test_build_client_uses_explicit_control_socket_path_without_local_ensure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, Any] = {}
    control_socket_path = tmp_path / "node-hosted" / "interface-control.sock"

    def _fake_from_local_control(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> InterfaceSdkClient:
        _ = cls
        observed["client_kwargs"] = {
            "socket_path": socket_path,
            "state_home": state_home,
        }
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_control",
        classmethod(_fake_from_local_control),
    )

    args = argparse.Namespace(
        namespace="aware_control",
        socket_path=None,
        control_socket_path=control_socket_path,
        state_home=None,
        ensure_local_host=None,
    )

    client = interface_command._build_client(args)

    assert isinstance(client, InterfaceSdkClient)
    assert observed["client_kwargs"] == {
        "socket_path": control_socket_path.resolve(),
        "state_home": None,
    }


def test_root_status_uses_explicit_control_socket_observer_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    control_socket_path = tmp_path / "interface-control.sock"

    def _fake_from_local_control(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> InterfaceSdkClient:
        _ = cls
        observed["client_kwargs"] = {
            "socket_path": socket_path,
            "state_home": state_home,
        }
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_control",
        classmethod(_fake_from_local_control),
    )

    exit_code = cli.main(
        [
            "status",
            "--control-socket-path",
            str(control_socket_path),
            "--namespace",
            "aware_control",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["namespace"] == "aware_control"
    assert payload["current_screen"]["screen_key"] == "deployment"
    assert observed["client_kwargs"] == {
        "socket_path": control_socket_path.resolve(),
        "state_home": None,
    }


def test_root_render_projects_current_surface(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(control_client=_FakeInterfaceControlClient()),
    )

    exit_code = cli.main(["render", "--namespace", "luis"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["current_screen"]["screen_key"] == "deployment"
    assert payload["panes"][0]["pane_ref"] == "home/main/deployment"
    assert payload["panes"][0]["api_capability_endpoint_ids"] == []


def test_root_panes_lists_pane_capability_endpoints(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(control_client=_FakeInterfaceControlClient()),
    )

    exit_code = cli.main(["panes", "--namespace", "luis"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert payload["panes"][0]["aliases"] == [
        "deployment",
        "workspace_deployment",
        "aware-deployment-pane",
    ]
    assert payload["panes"][0]["api_capability_endpoint_ids"] == []


def test_root_panes_dogfoods_bootstrap_host_pane(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_BootstrapInterfaceControlClient()
        ),
    )

    exit_code = cli.main(["panes", "--namespace", "codex"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert payload["panes"][0]["pane_ref"] == (
        "bootstrap/bootstrap.panes/identity_auth_gate"
    )
    assert payload["panes"][0]["pane_kind"] == "identity_auth_gate"
    assert payload["panes"][0]["state_source_kind"] == "host_pane_contribution"
    assert payload["panes"][0]["surface_affordance_keys"] == ["signup_via_profile"]
    assert payload["panes"][0]["api_capability_endpoint_ids"] == []


def test_root_act_dispatches_bootstrap_pane_action_through_interface(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_BootstrapInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "codex",
            "identity_auth_gate",
            "signup_via_profile",
            "--payload-json",
            '{"public_key": "ed25519:test"}',
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "namespace": "codex",
        "pane_ref": "bootstrap/bootstrap.panes/identity_auth_gate",
        "action_key": "signup_via_profile",
        "payload": {"public_key": "ed25519:test"},
    }
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_ref"] == "bootstrap/bootstrap.panes/identity_auth_gate"
    assert payload["action_key"] == "signup_via_profile"


def test_root_act_forwards_auth_context_before_resolving_pane_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AuthObservingInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "luis",
            "--auth-token",
            "apt:arg",
            "--endpoint",
            "ws://node.example.test",
            "deployment",
            "deployment.resolve",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert json.loads(captured.out)["action_key"] == "deployment.resolve"
    assert observed["ensure_namespace"] == {
        "namespace": "luis",
        "auth_token": "apt:arg",
        "endpoint": "ws://node.example.test",
        "host_label": None,
        "environment_config_id": None,
        "interface_package_id": None,
        "interface_package_name": None,
    }
    assert observed["action_key"] == "deployment.resolve"


def test_root_panes_dogfoods_local_service_host_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_LocalRuntimeGateInterfaceControlClient(
                gate="local_service_host_gate"
            )
        ),
    )

    exit_code = cli.main(["panes", "--namespace", "codex"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_count"] == 1
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert payload["panes"][0]["pane_ref"] == (
        "bootstrap/bootstrap.panes/local_service_host_gate"
    )
    assert payload["panes"][0]["aliases"] == ["local_service_host_gate"]
    assert payload["panes"][0]["pane_kind"] == "local_service_host_gate"
    assert payload["panes"][0]["state_source_kind"] == "host_pane_contribution"
    assert payload["panes"][0]["surface_affordance_keys"] == [
        "ensure_local_service_host",
        "restart_local_service_host",
    ]


def test_root_act_dogfoods_local_service_host_gate_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_LocalRuntimeGateInterfaceControlClient(
                gate="local_service_host_gate",
                observed=observed,
            )
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "codex",
            "local_service_host_gate",
            "ensure_local_service_host",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "namespace": "codex",
        "pane_ref": "bootstrap/bootstrap.panes/local_service_host_gate",
        "action_key": "ensure_local_service_host",
        "payload": {},
    }
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_ref"] == "bootstrap/bootstrap.panes/local_service_host_gate"
    assert payload["action_key"] == "ensure_local_service_host"
    assert payload["host_state"]["current_screen"]["screen_key"] == (
        "local_node_runtime_gate"
    )


def test_root_act_dogfoods_local_node_runtime_gate_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_LocalRuntimeGateInterfaceControlClient(
                gate="local_node_runtime_gate",
                observed=observed,
            )
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "codex",
            "local_node_runtime_gate",
            "ensure_local_node_runtime_started",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "namespace": "codex",
        "pane_ref": "bootstrap/bootstrap.panes/local_node_runtime_gate",
        "action_key": "ensure_local_node_runtime_started",
        "payload": {},
    }
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_ref"] == "bootstrap/bootstrap.panes/local_node_runtime_gate"
    assert payload["action_key"] == "ensure_local_node_runtime_started"
    assert payload["host_state"]["local_node_runtime"]["ready"] is True


def test_root_act_dogfoods_aware_control_hub_selector_mounted_api_action(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_AwareControlInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "codex",
            "hub_package_selector",
            "api:hub.code_package.search",
            "--payload-json",
            '{"query": "aware-control", "limit": 5}',
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "namespace": "codex",
        "pane_ref": "main/coordination_center/primary",
        "action_key": "api:hub.code_package.search",
        "payload": {"query": "aware-control", "limit": 5},
    }
    payload = json.loads(captured.out)
    assert payload["namespace"] == "codex"
    assert payload["pane_ref"] == "main/coordination_center/primary"
    assert payload["action_key"] == "api:hub.code_package.search"


def test_root_act_rejects_action_not_exposed_by_pane(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed = {"invoked": False}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_BootstrapInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "act",
            "--namespace",
            "codex",
            "identity_auth_gate",
            "submit_token",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert observed["invoked"] is False
    assert "is not exposed by pane" in captured.err


def test_root_invoke_rejects_retired_direct_pane_capability(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "invoke",
            "--namespace",
            "luis",
            "deployment",
            str(_PANE_ENDPOINT_ID),
            "--payload-json",
            '{"artifact_key": "workspace/home"}',
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "is not exposed by pane" in captured.err
    assert "endpoint_ref" not in observed


def test_root_invoke_rejects_capability_not_exposed_by_pane(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed = {"invoked": False}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "invoke",
            "--namespace",
            "luis",
            "deployment",
            "22222222-2222-4222-8222-222222222222",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert observed["invoked"] is False
    assert "is not exposed by pane" in captured.err


def test_transitional_run_invokes_surface_affordance_with_payload(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, Any] = {}

    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(
            control_client=_FakeInterfaceControlClient(observed=observed)
        ),
    )

    exit_code = cli.main(
        [
            "run",
            "--namespace",
            "luis",
            "deployment.resolve",
            "--payload-json",
            '{"artifact_key": "workspace/home"}',
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "namespace": "luis",
        "pane_ref": None,
        "action_key": "deployment.resolve",
        "payload": {"artifact_key": "workspace/home"},
    }
    payload = json.loads(captured.out)
    assert payload["action_key"] == "deployment.resolve"


def test_root_capabilities_renders_interface_snapshot(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        interface_command,
        "_build_client",
        lambda args: InterfaceSdkClient(control_client=_FakeInterfaceControlClient()),
    )

    exit_code = cli.main(["capabilities", "--namespace", "luis"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["namespace"] == "luis"
    assert payload["transport"]["capabilities"] == [
        "interface.actions",
        "workspace.open",
    ]
    assert payload["local_service_host"]["status"] == "ready"
    assert payload["pane_api_capability_endpoint_count"] == 0
    assert payload["panes"][0]["api_capability_endpoint_ids"] == []
    assert payload["surface_affordances"][0]["action_key"] == "deployment.resolve"


def test_public_help_mounts_interface_renderer_commands_not_public_hub(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert "status" in captured.out
    assert "render" in captured.out
    assert "panes" in captured.out
    assert "invoke" in captured.out
    assert "act" in captured.out
    assert "follow" in captured.out
    assert "capabilities" in captured.out
    assert "hub" not in captured.out
    assert "\n    actions" not in captured.out
    assert "\n    run" not in captured.out
    assert "Call Hub APIs" not in captured.out
    assert "workspace-deployment" not in captured.out


def test_renderer_commands_use_interface_service_client_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    socket_path = tmp_path / "interface-service.sock"
    client_kwargs: list[dict[str, object]] = []

    def _from_local_service_host(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
        request_timeout_s: float = 30.0,
    ) -> InterfaceSdkClient:
        _ = cls, request_timeout_s
        client_kwargs.append({"socket_path": socket_path, "state_home": state_home})
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(_from_local_service_host),
    )

    status_exit_code = cli.main(
        ["status", "--socket-path", str(socket_path), "--namespace", "luis"]
    )
    status_output = json.loads(capsys.readouterr().out)

    render_exit_code = cli.main(
        ["render", "--socket-path", str(socket_path), "--namespace", "luis"]
    )
    render_output = json.loads(capsys.readouterr().out)

    panes_exit_code = cli.main(
        ["panes", "--socket-path", str(socket_path), "--namespace", "luis"]
    )
    panes_output = json.loads(capsys.readouterr().out)

    invoke_exit_code = cli.main(
        [
            "invoke",
            "--socket-path",
            str(socket_path),
            "--namespace",
            "luis",
            "deployment",
            "1",
            "--payload-json",
            '{"artifact_key": "workspace/home"}',
        ]
    )
    invoke_captured = capsys.readouterr()

    act_exit_code = cli.main(
        [
            "act",
            "--socket-path",
            str(socket_path),
            "--namespace",
            "luis",
            "deployment",
            "deployment.resolve",
            "--payload-json",
            '{"artifact_key": "workspace/home"}',
        ]
    )
    act_output = json.loads(capsys.readouterr().out)

    assert status_exit_code == 0
    assert render_exit_code == 0
    assert panes_exit_code == 0
    assert invoke_exit_code == 1
    assert act_exit_code == 0
    assert status_output["connected"] is True
    assert status_output["current_screen"]["screen_key"] == "deployment"
    assert render_output["panes"][0]["pane_ref"] == "home/main/deployment"
    assert panes_output["panes"][0]["api_capability_endpoint_ids"] == []
    assert invoke_captured.out == ""
    assert "is not exposed by pane" in invoke_captured.err
    assert act_output["action_key"] == "deployment.resolve"
    assert act_output["pane_ref"] == "home/main/deployment"
    assert client_kwargs == [
        {"socket_path": socket_path, "state_home": None},
        {"socket_path": socket_path, "state_home": None},
        {"socket_path": socket_path, "state_home": None},
        {"socket_path": socket_path, "state_home": None},
        {"socket_path": socket_path, "state_home": None},
    ]


def _host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="https://interface.example",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="workspace",
            screen_key="deployment",
            source_kind="pane",
            title="Deployment",
            pane_key="deployment",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=uuid4(),
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            session_label=f"interface-{namespace}",
            capabilities=["interface.actions", "workspace.open"],
        ),
        local_service_host=InterfaceLocalServiceHostState(
            managed=True,
            supported=True,
            available=True,
            ready=True,
            status="ready",
            capabilities=["local.fs"],
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=True,
                database_exists=True,
                opg_count=1,
                projection_bundle_available=True,
                projection_plan_count=1,
                table_count=2,
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="home",
                    layout_key="main",
                    section_key="deployment",
                    pane_kind="workspace_deployment",
                    pane_package_name="aware-deployment-pane",
                    title="Deployment",
                    summary="Resolve deployment packages",
                    state_source_kind="api",
                    action_keys=["deployment.resolve"],
                )
            ],
        ),
        allowed_actions=[
            InterfaceAllowedAction(
                action_key="deployment.resolve",
                label="Resolve Deployment",
            )
        ],
    )


class _FakeInterfaceControlClient:
    def __init__(self, *, observed: dict[str, Any] | None = None) -> None:
        self._observed = observed

    async def ping(self) -> PingResponse:
        return PingResponse(request_id=uuid4(), service="aware_interface_service")

    async def list_namespaces(self) -> NamespaceListResponse:
        return NamespaceListResponse(
            request_id=uuid4(),
            namespaces=[
                HostedInterfaceNamespace(
                    namespace="luis",
                    host_label="interface-luis",
                    started=True,
                )
            ],
        )

    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        _ = (
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace),
        )

    async def select_step(self, *, namespace: str, step_id: str | None) -> object:
        return {"namespace": namespace, "step_id": step_id}

    async def select_profile(
        self,
        *,
        namespace: str,
        profile_id: str,
    ) -> InterfaceSelectProfileResponse:
        if self._observed is not None:
            self._observed["select_profile"] = {
                "namespace": namespace,
                "profile_id": profile_id,
            }
        return InterfaceSelectProfileResponse(
            request_id=uuid4(),
            namespace=namespace,
            profile_id=profile_id,
            host_state=_host_state(namespace),
        )

    async def request_window_layout(
        self,
        *,
        namespace: str,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
        window_key: str | None = None,
        layout_config_id: UUID | None = None,
        layout_key: str | None = None,
        section_key: str | None = None,
        observable_id: UUID | None = None,
        representation_id: UUID | None = None,
        requested_by_service: str | None = None,
        requested_by_operation: str | None = None,
        reason: str | None = None,
        idempotency_key: str | None = None,
    ) -> object:
        return {
            "namespace": namespace,
            "interface_package_id": interface_package_id,
            "interface_package_name": interface_package_name,
            "window_key": window_key,
            "layout_config_id": layout_config_id,
            "layout_key": layout_key,
            "section_key": section_key,
            "observable_id": observable_id,
            "representation_id": representation_id,
            "requested_by_service": requested_by_service,
            "requested_by_operation": requested_by_operation,
            "reason": reason,
            "idempotency_key": idempotency_key,
        }

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_host_state(namespace),
        )

    async def stop(self, *, namespace: str) -> InterfaceStopResponse:
        return InterfaceStopResponse(
            request_id=uuid4(),
            namespace=namespace,
            hosted_namespace=HostedInterfaceNamespace(
                namespace=namespace,
                host_label=f"interface-{namespace}",
                started=False,
            ),
        )

    async def invoke_api(self, **kwargs: Any) -> InterfaceInvokeApiResponse:
        if self._observed is not None:
            if "invoked" in self._observed:
                self._observed["invoked"] = True
            self._observed.update(kwargs)
        return InterfaceInvokeApiResponse(
            request_id=uuid4(),
            namespace=str(kwargs["namespace"]),
            endpoint_ref=str(kwargs["endpoint_ref"]),
            discriminant=str(kwargs["discriminant"]),
            service_status="ok",
            response_payload={"resolved": True},
        )

    async def action(self, **kwargs: Any) -> InterfaceActionResponse:
        if self._observed is not None:
            if "invoked" in self._observed:
                self._observed["invoked"] = True
            self._observed.update(kwargs)
            self._observed["payload"] = dict(kwargs.get("payload") or {})
        namespace = str(kwargs["namespace"])
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=kwargs.get("pane_ref"),
            action_key=str(kwargs["action_key"]),
            host_state=_host_state(namespace),
        )

    async def follow(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[InterfaceHostState]:
        _ = poll_interval_ms
        yield _host_state(namespace)


class _UnavailableInterfaceControlClient(_FakeInterfaceControlClient):
    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        _ = (
            namespace,
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        raise FileNotFoundError("No such file or directory")

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        _ = namespace
        raise FileNotFoundError("No such file or directory")


class _AuthObservingInterfaceControlClient(_FakeInterfaceControlClient):
    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        if self._observed is not None:
            self._observed["ensure_namespace"] = {
                "namespace": namespace,
                "auth_token": auth_token,
                "endpoint": endpoint,
                "host_label": host_label,
                "environment_config_id": environment_config_id,
                "interface_package_id": interface_package_id,
                "interface_package_name": interface_package_name,
            }
        return await super().ensure_namespace(
            namespace=namespace,
            auth_token=auth_token,
            endpoint=endpoint,
            host_label=host_label,
            environment_config_id=environment_config_id,
            interface_package_id=interface_package_id,
            interface_package_name=interface_package_name,
        )


class _BootstrapInterfaceControlClient(_FakeInterfaceControlClient):
    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        _ = (
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_bootstrap_host_state(namespace),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_bootstrap_host_state(namespace),
        )


class _LocalRuntimeGateInterfaceControlClient(_FakeInterfaceControlClient):
    def __init__(
        self,
        *,
        gate: str,
        observed: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(observed=observed)
        self._gate = gate

    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        _ = (
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_local_runtime_gate_host_state(namespace, gate=self._gate),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_local_runtime_gate_host_state(namespace, gate=self._gate),
        )

    async def action(self, **kwargs: Any) -> InterfaceActionResponse:
        if self._observed is not None:
            if "invoked" in self._observed:
                self._observed["invoked"] = True
            self._observed.update(kwargs)
            self._observed["payload"] = dict(kwargs.get("payload") or {})
        namespace = str(kwargs["namespace"])
        action_key = str(kwargs["action_key"])
        if action_key == "ensure_local_service_host":
            host_state = _local_runtime_gate_host_state(
                namespace,
                gate="local_node_runtime_gate",
            )
        elif action_key == "ensure_local_node_runtime_started":
            host_state = _local_runtime_gate_host_state(
                namespace,
                gate="local_node_runtime_gate",
                node_ready=True,
            )
        else:
            host_state = _local_runtime_gate_host_state(namespace, gate=self._gate)
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=kwargs.get("pane_ref"),
            action_key=action_key,
            host_state=host_state,
        )


class _AwareControlInterfaceControlClient(_FakeInterfaceControlClient):
    async def ensure_namespace(
        self,
        *,
        namespace: str,
        auth_token: str | None = None,
        endpoint: str | None = None,
        host_label: str | None = None,
        environment_config_id: UUID | None = None,
        interface_package_id: UUID | None = None,
        interface_package_name: str | None = None,
    ) -> NamespaceEnsureResponse:
        _ = (
            auth_token,
            endpoint,
            host_label,
            environment_config_id,
            interface_package_id,
            interface_package_name,
        )
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return NamespaceEnsureResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_aware_control_host_state(namespace),
        )

    async def status(self, *, namespace: str) -> InterfaceStatusResponse:
        if self._observed is not None:
            self._observed["namespace"] = namespace
        return InterfaceStatusResponse(
            request_id=uuid4(),
            namespace=namespace,
            host_state=_aware_control_host_state(namespace),
        )

    async def action(self, **kwargs: Any) -> InterfaceActionResponse:
        if self._observed is not None:
            if "invoked" in self._observed:
                self._observed["invoked"] = True
            self._observed.update(kwargs)
        namespace = str(kwargs["namespace"])
        return InterfaceActionResponse(
            request_id=uuid4(),
            namespace=namespace,
            pane_ref=kwargs.get("pane_ref"),
            action_key=str(kwargs["action_key"]),
            host_state=_aware_control_host_state(namespace),
        )


class _InterfaceControlPlaneSocketFixture:
    def __init__(self, socket_path: Path) -> None:
        self.socket_path = socket_path
        self.requests: list[dict[str, object]] = []
        self._ready = Event()
        self._thread: Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event: asyncio.Event | None = None
        self._error: BaseException | None = None

    def __enter__(self) -> "_InterfaceControlPlaneSocketFixture":
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=5):
            raise AssertionError("Interface control socket fixture did not start.")
        if self._error is not None:
            raise AssertionError(
                "Interface control socket fixture failed."
            ) from self._error
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        loop = self._loop
        stop_event = self._stop_event
        if loop is not None and stop_event is not None:
            loop.call_soon_threadsafe(stop_event.set)
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive() and exc_type is None:
                raise AssertionError("Interface control socket fixture did not stop.")
        with suppress(FileNotFoundError):
            self.socket_path.unlink()
        if self._error is not None and exc_type is None:
            raise AssertionError(
                "Interface control socket fixture failed."
            ) from self._error

    def _run(self) -> None:
        try:
            asyncio.run(self._serve())
        except BaseException as exc:
            self._error = exc
            self._ready.set()

    async def _serve(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        with suppress(FileNotFoundError):
            self.socket_path.unlink()
        self._loop = asyncio.get_running_loop()
        self._stop_event = asyncio.Event()
        server = await asyncio.start_unix_server(
            self._handle_client,
            path=str(self.socket_path),
        )
        self._ready.set()
        async with server:
            await self._stop_event.wait()
            server.close()
            await server.wait_closed()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            line = await reader.readline()
            if not line:
                return
            operation = InterfaceControlPlaneOperation.model_validate(
                json.loads(line.decode("utf-8"))
            )
            request = operation.request
            if request is None:
                raise RuntimeError("Interface control fixture received a non-request.")
            self.requests.append(_request_record(request))
            response = _fixture_response(request)
            writer.write(
                InterfaceControlPlaneOperation(response=response)
                .model_dump_json(exclude_none=True)
                .encode("utf-8")
                + b"\n"
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()


def _fixture_response(
    request: InterfaceControlPlaneRequest,
) -> InterfaceControlPlaneResponse:
    if isinstance(request, NamespaceEnsureRequest):
        return NamespaceEnsureResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            host_state=_host_state(request.namespace),
        )
    if isinstance(request, InterfaceStatusRequest):
        return InterfaceStatusResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            host_state=_host_state(request.namespace),
        )
    if isinstance(request, InterfaceInvokeApiRequest):
        return InterfaceInvokeApiResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            endpoint_ref=request.endpoint_ref,
            discriminant=request.discriminant,
            service_status="ok",
            response_payload={
                "resolved": True,
                "request_payload": _json_object(request.request_payload),
            },
        )
    if isinstance(request, InterfaceActionRequest):
        return InterfaceActionResponse(
            request_id=request.request_id,
            namespace=request.namespace,
            pane_ref=request.pane_ref,
            action_key=request.action_key,
            host_state=_host_state(request.namespace),
        )
    raise RuntimeError(f"Unsupported fixture request operation: {request.operation}")


def _request_record(request: InterfaceControlPlaneRequest) -> dict[str, object]:
    record: dict[str, object] = {"operation": request.operation}
    namespace = getattr(request, "namespace", None)
    if namespace is not None:
        record["namespace"] = str(namespace)
    if isinstance(request, InterfaceInvokeApiRequest):
        record.update(
            {
                "endpoint_ref": request.endpoint_ref,
                "discriminant": request.discriminant,
                "request_payload": _json_object(request.request_payload),
            }
        )
    if isinstance(request, InterfaceActionRequest):
        record.update(
            {
                "pane_ref": request.pane_ref,
                "action_key": request.action_key,
                "payload": _json_object(request.payload),
            }
        )
    return record


def _json_object(value: object) -> dict[str, object]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _aware_control_host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="control",
            screen_key="aware_control",
            source_kind="pane",
            title="Aware Control",
            pane_key="hub_package_selector",
        ),
        transport=InterfaceTransportState(
            available=True,
            registered=True,
            authenticated=True,
            actor_id=uuid4(),
            interface_id=uuid4(),
            interface_session_id=uuid4(),
            session_label=f"interface-{namespace}",
            capabilities=["interface.actions"],
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=True,
                database_exists=True,
                opg_count=1,
                projection_bundle_available=True,
                projection_plan_count=1,
                table_count=2,
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware_control",
                projection_view_id="hub_package.selector",
                interface_package_name="aware-control-interface",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="main",
                    layout_key="coordination_center",
                    section_key="primary",
                    pane_kind="hub_package_selector",
                    pane_package_name="aware-hub-package-selector-pane",
                    title="Hub Package Selector",
                    summary="Resolve CodePackage artifacts",
                    state_source_kind="api",
                    action_keys=["api:hub.code_package.search"],
                )
            ],
        ),
    )


def _bootstrap_host_state(namespace: str) -> InterfaceHostState:
    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="gate",
            screen_key="identity_auth_gate",
            source_kind="gate",
            title="Identity/Auth Required",
            message=(
                "Identity admission requires an Interface transport session bound "
                "to a node endpoint."
            ),
            pane_key="identity_auth_gate",
        ),
        transport=InterfaceTransportState(
            available=False,
            registered=False,
            authenticated=False,
            capabilities=[],
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=False,
                database_exists=False,
                opg_count=0,
                projection_bundle_available=False,
                projection_plan_count=0,
                table_count=0,
                reason="interface_host_bootstrap_panes",
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware.interface.bootstrap",
                projection_view_id="entry.control-plane",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="bootstrap",
                    layout_key="bootstrap.panes",
                    section_key="identity_auth_gate",
                    pane_kind="identity_auth_gate",
                    title="Identity/Auth Required",
                    summary=(
                        "Identity admission requires an Interface transport "
                        "session bound to a node endpoint."
                    ),
                    narrative_key="bootstrap.panes.identity_auth_gate",
                    state_source_kind="host_pane_contribution",
                    state_projection_hash="section:bootstrap.panes:identity_auth_gate",
                    action_keys=["signup_via_profile"],
                )
            ],
            warnings=["interface_host_bootstrap_panes"],
        ),
        warnings=["identity_auth_required"],
    )


def _local_runtime_gate_host_state(
    namespace: str,
    *,
    gate: str,
    node_ready: bool = False,
) -> InterfaceHostState:
    if gate == "local_service_host_gate":
        action_keys = ["ensure_local_service_host", "restart_local_service_host"]
        title = "Local Service Host Required"
        summary = "Service host bootstrap is required."
        message = "Service host bootstrap is required."
        service_host_ready = False
    elif gate == "local_node_runtime_gate":
        action_keys = [
            "ensure_local_node_runtime_started",
            "restart_local_service_host",
            "tail_local_node_runtime_logs",
        ]
        title = "Local Node Runtime Required"
        summary = "Postgres: database bootstrap pending"
        message = "Postgres: database bootstrap pending"
        service_host_ready = True
    else:
        raise AssertionError(f"Unsupported local runtime gate fixture: {gate}")

    return InterfaceHostState(
        host_label=f"interface-{namespace}",
        namespace=namespace,
        endpoint="http://127.0.0.1:9000",
        started=True,
        current_screen=InterfaceCurrentScreen(
            screen_kind="gate",
            screen_key=gate,
            source_kind="gate",
            title=title,
            message=message,
            pane_key=gate,
        ),
        transport=InterfaceTransportState(
            available=False,
            registered=False,
            authenticated=False,
            capabilities=[],
        ),
        local_service_host=InterfaceLocalServiceHostState(
            managed=True,
            supported=True,
            available=service_host_ready,
            ready=service_host_ready,
            status="ready" if service_host_ready else "absent",
            socket_path="/tmp/aware-service-host.sock",
            capabilities=["service.host"],
        ),
        local_node_runtime=(
            InterfaceLocalNodeRuntimeState(
                managed=True,
                available=service_host_ready,
                ready=node_ready,
                phase="ready" if node_ready else "start_db",
                active_target_id="postgres",
                target_key="postgres",
                display_name="Postgres",
                backend_kind="postgres",
                is_active=service_host_ready and not node_ready,
                is_healthy=node_ready,
                summary="Node runtime ready." if node_ready else summary,
            )
            if gate == "local_node_runtime_gate"
            else None
        ),
        runtime=InterfaceRuntimeState(
            backend=InterfaceBackendState(
                available=False,
                database_exists=False,
                opg_count=0,
                projection_bundle_available=False,
                projection_plan_count=0,
                table_count=0,
                reason="interface_host_bootstrap_panes",
            ),
            resolved_view=InterfaceResolvedView(
                experience_key="aware.interface.bootstrap",
                projection_view_id="entry.control-plane",
            ),
            resolved_panes=[
                InterfaceResolvedPaneDescriptor(
                    window_key="bootstrap",
                    layout_key="bootstrap.panes",
                    section_key=gate,
                    pane_kind=gate,
                    title=title,
                    summary=summary,
                    narrative_key=f"bootstrap.panes.{gate}",
                    state_source_kind="host_pane_contribution",
                    state_projection_hash=f"section:bootstrap.panes:{gate}",
                    action_keys=action_keys,
                )
            ],
            warnings=["interface_host_bootstrap_panes"],
        ),
        allowed_actions=[
            InterfaceAllowedAction(action_key=action_key, label=action_key)
            for action_key in action_keys
        ],
        warnings=[
            (
                "local_node_runtime_required"
                if gate == "local_node_runtime_gate"
                else "local_service_host_required"
            )
        ],
    )
