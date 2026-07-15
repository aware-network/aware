from __future__ import annotations

import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from aware_interface_service_dto.comms.models.hosted_interface_namespace import (
    HostedInterfaceNamespace,
)
from aware_interface_service_dto.comms.models.control_plane import NamespaceListResponse
from aware_interface_service_dto.comms.models.control_plane import PingResponse
from aware_interface_sdk import InterfaceSdkClient
from aware_sdk import cli


def test_sdk_operations_lists_interface_sdk_catalog(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli.main(["sdk", "operations"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["catalog_contract"] == "aware.sdk_operation_catalog.v0"
    operation_refs = {operation["operation_ref"] for operation in payload["operations"]}
    assert "interface_sdk.ping_interface_host" in operation_refs
    assert "interface_sdk.list_interface_namespaces" in operation_refs


def test_sdk_describe_renders_declared_operation_detail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = cli.main(["sdk", "describe", "interface_sdk.ping_interface_host"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    operation = payload["operation"]
    assert operation["operation_ref"] == "interface_sdk.ping_interface_host"
    assert operation["effect"] == "read"
    assert operation["requires_confirmation"] is False
    assert operation["endpoint_refs"] == [
        "interface.ping_interface_host.ping_interface_host"
    ]
    assert operation["handler_ref"] == (
        "aware_interface_sdk.operation_catalog:dispatch_interface_sdk_operation"
    )
    assert operation["input_schema"] == {
        "type": "object",
        "additionalProperties": False,
    }


def test_sdk_invoke_dispatches_read_only_interface_operation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    observed: dict[str, object] = {}

    def _from_local_service_host(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
    ) -> InterfaceSdkClient:
        _ = cls
        observed["socket_path"] = socket_path
        observed["state_home"] = state_home
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(_from_local_service_host),
    )

    socket_path = tmp_path / "interface.sock"
    state_home = tmp_path / "state"
    exit_code = cli.main(
        [
            "sdk",
            "invoke",
            "interface_sdk.ping_interface_host",
            "--socket-path",
            str(socket_path),
            "--state-home",
            str(state_home),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert observed == {
        "socket_path": socket_path.resolve(),
        "state_home": state_home.resolve(),
    }
    payload = json.loads(captured.out)
    assert payload["catalog_contract"] == "aware.sdk_operation_catalog.v0"
    assert payload["operation_ref"] == "interface_sdk.ping_interface_host"
    assert payload["effect"] == "read"
    assert payload["result"]["operation"] == "ping"
    assert payload["result"]["service"] == "aware_interface_service"


def test_sdk_invoke_supports_list_namespace_canary(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(
            lambda cls, **kwargs: InterfaceSdkClient(
                control_client=_FakeInterfaceControlClient()
            )
        ),
    )

    exit_code = cli.main(["sdk", "invoke", "interface_sdk.list_interface_namespaces"])

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["operation_ref"] == "interface_sdk.list_interface_namespaces"
    assert payload["result"]["operation"] == "namespace_list"
    assert payload["result"]["namespaces"][0]["namespace"] == "codex"


def test_sdk_invoke_consumes_workspace_sdk_status_catalog_provider(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from aware_workspace_sdk.state.contracts import LocalWorkspaceStatusBaseline
    from aware_workspace_sdk.state.repository import AwareWorkspaceLocalStateStore

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    database_path = tmp_path / "aware-workspace.sqlite"
    store = AwareWorkspaceLocalStateStore(database_path=database_path)
    _ = store.write_status_baseline(
        LocalWorkspaceStatusBaseline(
            workspace_handle="workspace",
            workspace_root=str(workspace_root),
            workspace_revision_id="workspace-revision:test",
            workspace_revision_commit_id="commit:test",
            materialization_receipt_path=".aware/reports/workspace/materialize.json",
            selected_at_utc=datetime(2026, 5, 20, 1, 0, tzinfo=UTC),
        )
    )

    exit_code = cli.main(
        [
            "sdk",
            "invoke",
            "workspace_sdk.load_status",
            "--payload-json",
            json.dumps(
                {
                    "workspace_root": str(workspace_root),
                    "workspace_handle": "workspace",
                    "database_path": str(database_path),
                }
            ),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["operation_ref"] == "workspace_sdk.load_status"
    assert payload["effect"] == "read"
    assert payload["result"]["status"] == "ok"
    assert payload["result"]["state"] == "missing"
    assert payload["result"]["baseline"]["workspace_revision_id"] == (
        "workspace-revision:test"
    )


class _FakeInterfaceControlClient:
    async def ping(self) -> PingResponse:
        return PingResponse(
            request_id=uuid4(),
            service="aware_interface_service",
            status="ok",
        )

    async def list_namespaces(self) -> NamespaceListResponse:
        return NamespaceListResponse(
            request_id=uuid4(),
            namespaces=[
                HostedInterfaceNamespace(
                    namespace="codex",
                    host_label="interface-codex",
                    started=True,
                )
            ],
        )

    async def ensure_namespace(self, **kwargs: Any) -> object:
        raise AssertionError(
            "ensure_namespace should not be used by SDK catalog canaries"
        )

    async def select_step(self, **kwargs: Any) -> object:
        raise AssertionError("select_step should not be used by SDK catalog canaries")

    async def request_window_layout(self, **kwargs: Any) -> object:
        raise AssertionError(
            "request_window_layout should not be used by SDK catalog canaries"
        )

    async def status(self, **kwargs: Any) -> object:
        raise AssertionError("status should not be used by SDK catalog canaries")

    async def stop(self, **kwargs: Any) -> object:
        raise AssertionError("stop should not be used by SDK catalog canaries")

    async def invoke_api(self, **kwargs: Any) -> object:
        raise AssertionError("invoke_api should not be used by SDK catalog canaries")

    async def action(self, **kwargs: Any) -> object:
        raise AssertionError("action should not be used by SDK catalog canaries")

    def follow(
        self,
        *,
        namespace: str,
        poll_interval_ms: int = 1000,
    ) -> AsyncIterator[object]:
        _ = namespace, poll_interval_ms
        raise AssertionError("follow should not be used by SDK catalog canaries")
