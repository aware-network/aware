from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

import pytest
from aware_interface_sdk import InterfaceSdkClient
from aware_interface_sdk.operation_catalog import (
    INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF,
    INTERFACE_SDK_PING_OPERATION_REF,
    dispatch_interface_sdk_operation,
    get_sdk_operation_catalog,
)
from aware_interface_service_dto.comms.models.hosted_interface_namespace import HostedInterfaceNamespace
from aware_interface_service_dto.comms.models.control_plane import NamespaceListResponse
from aware_interface_service_dto.comms.models.control_plane import PingResponse


def test_interface_sdk_operation_catalog_declares_read_only_canaries() -> None:
    catalog = get_sdk_operation_catalog()

    assert catalog["catalog_contract"] == "aware.sdk_operation_catalog.v0"
    assert catalog["sdk_name"] == "interface_sdk"
    operations = cast(list[dict[str, object]], catalog["operations"])
    operation_by_ref = {
        str(operation["operation_ref"]): operation for operation in operations
    }
    assert {
        INTERFACE_SDK_PING_OPERATION_REF,
        INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF,
    } <= set(operation_by_ref)
    assert operation_by_ref[INTERFACE_SDK_PING_OPERATION_REF]["effect"] == "read"
    assert operation_by_ref[INTERFACE_SDK_PING_OPERATION_REF]["handler_ref"] == (
        "aware_interface_sdk.operation_catalog:dispatch_interface_sdk_operation"
    )


@pytest.mark.asyncio
async def test_interface_sdk_operation_dispatcher_uses_explicit_operation_refs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: dict[str, object] = {}

    def _from_local_service_host(
        cls: type[InterfaceSdkClient],
        *,
        socket_path: Path | None = None,
        state_home: Path | None = None,
        request_timeout_s: float = 30.0,
    ) -> InterfaceSdkClient:
        _ = cls, request_timeout_s
        observed["socket_path"] = socket_path
        observed["state_home"] = state_home
        return InterfaceSdkClient(control_client=_FakeInterfaceControlClient())

    monkeypatch.setattr(
        InterfaceSdkClient,
        "from_local_service_host",
        classmethod(_from_local_service_host),
    )

    result = await dispatch_interface_sdk_operation(
        operation_ref=INTERFACE_SDK_LIST_NAMESPACES_OPERATION_REF,
        request_payload={},
        context={
            "socket_path": str(tmp_path / "interface.sock"),
            "state_home": str(tmp_path / "state"),
        },
    )

    assert observed == {
        "socket_path": tmp_path / "interface.sock",
        "state_home": tmp_path / "state",
    }
    assert isinstance(result, NamespaceListResponse)
    assert result.namespaces[0].namespace == "codex"


class _FakeInterfaceControlClient:
    async def ping(self) -> PingResponse:
        return PingResponse(request_id=uuid4(), service="aware_interface_service")

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
