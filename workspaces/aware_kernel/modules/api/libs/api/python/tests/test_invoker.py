from __future__ import annotations

from collections.abc import AsyncIterator
import sys
import types
from typing import Any, cast

import pytest
from pydantic import BaseModel

from aware_api.invocation import load_api_invocation_manifest_payload
from aware_api.invoker import (
    ApiEndpointInvocation,
    ApiEndpointResponse,
    ApiEndpointStream,
    AwareApiEndpointInvoker,
    resolve_api_endpoint_model_class,
)


def _manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "package_name": "home-story-api",
        "fqn_prefix": "aware_home_api",
        "apis": [
            {
                "name": "home_devices",
                "source_path": "apis/bindings/home.apis.aware",
                "capabilities": [
                    {
                        "name": "door",
                        "source_path": "apis/bindings/home.apis.aware",
                        "endpoints": [
                            {
                                "name": "lock",
                                "source_path": "apis/bindings/home.apis.aware",
                                "endpoint_ref": "home_devices.door.lock",
                                "discriminant": "home_devices.door.lock",
                                "invocation_kind": "shared_client_endpoint",
                                "client_backend": "aware_api.invoker.AwareApiEndpointInvoker",
                                "client_operation": "invoke_api_endpoint",
                                "addressing_strategy": "session_bound",
                                "request": {
                                    "class_ref": "aware_home_api.door.LockDoorRequest",
                                    "source_path": "apis/types/home/aware/door/endpoints.aware",
                                },
                                "response": {
                                    "class_ref": "aware_home_api.door.LockDoorResult",
                                    "source_path": "apis/types/home/aware/door/endpoints.aware",
                                },
                                "stream": {
                                    "stream_mode": "server",
                                    "source_path": "apis/bindings/home.apis.aware",
                                    "events": [
                                        {
                                            "kind": "snapshot",
                                            "class_ref": "aware_home_api.door.DoorSnapshot",
                                            "source_path": "apis/types/home/aware/door/endpoints.aware",
                                        },
                                        {
                                            "kind": "delta",
                                            "class_ref": "aware_home_api.door.DoorDelta",
                                            "source_path": "apis/types/home/aware/door/endpoints.aware",
                                        },
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }


class LockDoorRequest(BaseModel):
    label: str
    force: bool = False


class LockDoorResult(BaseModel):
    accepted: bool


class DoorSnapshot(BaseModel):
    locked: bool


class DoorDelta(BaseModel):
    changed: bool


class ActorContext(BaseModel):
    kind: str
    provider_session_id: str | None = None


class WorkspaceStatusProbeRequest(BaseModel):
    workspace_root: str
    actor_context: ActorContext | None = None
    session_key: str | None = None


class _RecordingTransport:
    def __init__(self, response: ApiEndpointResponse | None = None) -> None:
        self.response = response or ApiEndpointResponse(response_payload={"accepted": True})
        self.calls: list[tuple[ApiEndpointInvocation, float | None]] = []

    async def invoke(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointResponse:
        self.calls.append((invocation, timeout_s))
        return self.response


class _StreamTransport(_RecordingTransport):
    def __init__(self) -> None:
        super().__init__()
        self.closed = False

    async def open_stream(
        self,
        invocation: ApiEndpointInvocation,
        *,
        timeout_s: float | None = None,
    ) -> ApiEndpointStream:
        self.calls.append((invocation, timeout_s))

        async def _events() -> AsyncIterator[ApiEndpointResponse]:
            yield ApiEndpointResponse(response_payload={"locked": True})
            yield ApiEndpointResponse(response_payload={"changed": True})

        async def _close() -> None:
            self.closed = True

        return ApiEndpointStream(events=_events(), close=_close)


@pytest.fixture(autouse=True)
def _install_home_api_module(monkeypatch: pytest.MonkeyPatch) -> None:
    package_module = types.ModuleType("aware_home_api")
    door_module = types.ModuleType("aware_home_api.door")
    setattr(door_module, "LockDoorResult", LockDoorResult)
    setattr(door_module, "DoorSnapshot", DoorSnapshot)
    setattr(door_module, "DoorDelta", DoorDelta)
    monkeypatch.setitem(sys.modules, "aware_home_api", package_module)
    monkeypatch.setitem(sys.modules, "aware_home_api.door", door_module)


def _install_generated_model_module(
    monkeypatch: pytest.MonkeyPatch,
    module_name: str,
    **models: type[BaseModel],
) -> None:
    parts = module_name.split(".")
    for index in range(1, len(parts)):
        package_name = ".".join(parts[:index])
        if package_name not in sys.modules:
            monkeypatch.setitem(sys.modules, package_name, types.ModuleType(package_name))
    module = types.ModuleType(module_name)
    for name, model in models.items():
        setattr(module, name, model)
    monkeypatch.setitem(sys.modules, module_name, module)


@pytest.mark.asyncio
async def test_invoker_delegates_endpoint_invocation_to_supplied_transport() -> None:
    loaded = load_api_invocation_manifest_payload(_manifest_payload())
    transport = _RecordingTransport()
    invoker = AwareApiEndpointInvoker(transport)

    response = await invoker.invoke_api_endpoint(
        manifest=loaded,
        endpoint_ref="home_devices.door.lock",
        request_payload=LockDoorRequest(label="Front Door"),
        timeout_s=3.0,
    )

    assert response == LockDoorResult(accepted=True)
    invocation, timeout_s = transport.calls[0]
    assert timeout_s == 3.0
    assert invocation.endpoint_ref == "home_devices.door.lock"
    assert invocation.discriminant == "home_devices.door.lock"
    assert invocation.request_payload == {"label": "Front Door", "force": False}


@pytest.mark.asyncio
async def test_invoker_preserves_none_values_in_nested_base_model_payloads() -> None:
    loaded = load_api_invocation_manifest_payload(_manifest_payload())
    transport = _RecordingTransport()
    invoker = AwareApiEndpointInvoker(transport)

    await invoker.invoke_api_endpoint(
        manifest=loaded,
        endpoint_ref="home_devices.door.lock",
        request_payload=WorkspaceStatusProbeRequest(
            workspace_root="/tmp/workspace",
            actor_context=ActorContext(kind="agent"),
        ),
    )

    invocation, _ = transport.calls[0]
    assert invocation.request_payload == {
        "workspace_root": "/tmp/workspace",
        "actor_context": {
            "kind": "agent",
            "provider_session_id": None,
        },
        "session_key": None,
    }


@pytest.mark.asyncio
async def test_invoker_prefers_python_model_ref_for_response_decode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _manifest_payload()
    endpoint = payload["apis"][0]["capabilities"][0]["endpoints"][0]  # type: ignore[index]
    response = endpoint["response"]  # type: ignore[index]
    response["class_ref"] = "aware_home_api.semantic_only.LockDoorResult"  # type: ignore[index]
    response["python_model_ref"] = "generated_home_api.models.lock_door_result.LockDoorResult"  # type: ignore[index]
    _install_generated_model_module(
        monkeypatch,
        "generated_home_api.models.lock_door_result",
        LockDoorResult=LockDoorResult,
    )

    loaded = load_api_invocation_manifest_payload(payload)
    invoker = AwareApiEndpointInvoker(_RecordingTransport())

    decoded = await invoker.invoke_api_endpoint(
        manifest=loaded,
        endpoint_ref="home_devices.door.lock",
        request_payload=LockDoorRequest(label="Front Door"),
    )

    assert decoded == LockDoorResult(accepted=True)


@pytest.mark.asyncio
async def test_invoker_rejects_legacy_aware_api_client_backend() -> None:
    payload = cast(dict[str, Any], _manifest_payload())
    payload["apis"][0]["capabilities"][0]["endpoints"][0][  # type: ignore[index]
        "client_backend"
    ] = "aware_api.client.AwareApiClient"
    loaded = load_api_invocation_manifest_payload(payload)
    invoker = AwareApiEndpointInvoker(_RecordingTransport())

    with pytest.raises(ValueError, match="Unsupported client backend"):
        await invoker.invoke_api_endpoint(
            manifest=loaded,
            endpoint_ref="home_devices.door.lock",
            request_payload={"label": "Front Door"},
        )


@pytest.mark.asyncio
async def test_invoker_rejects_non_api_client_backend() -> None:
    payload = cast(dict[str, Any], _manifest_payload())
    payload["apis"][0]["capabilities"][0]["endpoints"][0][  # type: ignore[index]
        "client_backend"
    ] = "aware_service.internal.Client"
    loaded = load_api_invocation_manifest_payload(payload)
    invoker = AwareApiEndpointInvoker(_RecordingTransport())

    with pytest.raises(ValueError, match="Unsupported client backend"):
        await invoker.invoke_api_endpoint(
            manifest=loaded,
            endpoint_ref="home_devices.door.lock",
            request_payload={"label": "Front Door"},
        )


@pytest.mark.asyncio
async def test_invoker_streams_and_decodes_typed_events() -> None:
    loaded = load_api_invocation_manifest_payload(_manifest_payload())
    transport = _StreamTransport()
    invoker = AwareApiEndpointInvoker(transport)

    events = [
        event
        async for event in invoker.stream_api_endpoint(
            manifest=loaded,
            endpoint_ref="home_devices.door.lock",
            request_payload={"label": "Front Door"},
        )
    ]

    assert events == [DoorSnapshot(locked=True), DoorDelta(changed=True)]
    assert transport.closed is True


@pytest.mark.asyncio
async def test_invoker_prefers_python_model_refs_for_stream_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _manifest_payload()
    endpoint = payload["apis"][0]["capabilities"][0]["endpoints"][0]  # type: ignore[index]
    events = endpoint["stream"]["events"]  # type: ignore[index]
    events[0]["class_ref"] = "aware_home_api.semantic_only.DoorSnapshot"  # type: ignore[index]
    events[0]["python_model_ref"] = "generated_home_api.models.door_snapshot.DoorSnapshot"  # type: ignore[index]
    events[1]["class_ref"] = "aware_home_api.semantic_only.DoorDelta"  # type: ignore[index]
    events[1]["python_model_ref"] = "generated_home_api.models.door_delta.DoorDelta"  # type: ignore[index]
    _install_generated_model_module(
        monkeypatch,
        "generated_home_api.models.door_snapshot",
        DoorSnapshot=DoorSnapshot,
    )
    _install_generated_model_module(
        monkeypatch,
        "generated_home_api.models.door_delta",
        DoorDelta=DoorDelta,
    )

    loaded = load_api_invocation_manifest_payload(payload)
    transport = _StreamTransport()
    invoker = AwareApiEndpointInvoker(transport)

    decoded = [
        event
        async for event in invoker.stream_api_endpoint(
            manifest=loaded,
            endpoint_ref="home_devices.door.lock",
            request_payload={"label": "Front Door"},
        )
    ]

    assert decoded == [DoorSnapshot(locked=True), DoorDelta(changed=True)]


def test_default_package_dependencies_stay_off_node_and_service_routing() -> None:
    import tomllib
    from pathlib import Path

    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = {
        dependency.split("[", 1)[0].split("<", 1)[0].split(">", 1)[0].split("=", 1)[0].strip()
        for dependency in data["project"]["dependencies"]
    }

    assert dependencies == {"pydantic", "aware-types"}
    assert "optional-dependencies" not in data["project"]


def test_public_package_surface_is_invoker_only() -> None:
    import aware_api

    assert "AwareApiEndpointInvoker" in aware_api.__all__
    assert "AwareApiClient" not in aware_api.__all__
    assert "AwareApiConfig" not in aware_api.__all__
    assert "AwareApiContext" not in aware_api.__all__


def test_invoker_resolves_authored_package_level_class_ref_from_package_bootstrap() -> None:
    from aware_code_service_dto.code.features.package_distribution import (
        PublishCodePackageResponse,
    )

    resolved = resolve_api_endpoint_model_class(
        "aware_code_service_dto.code.PublishCodePackageResponse"
    )

    assert resolved is PublishCodePackageResponse
