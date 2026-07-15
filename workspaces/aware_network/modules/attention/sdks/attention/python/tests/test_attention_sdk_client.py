from __future__ import annotations

import pytest

from aware_attention_sdk import build_attention_sdk_client


class _RecordingEndpoint:
    def __init__(self, name: str, calls: list[tuple[str, object]]) -> None:
        self._name = name
        self._calls = calls

    async def __call__(self, request: object) -> object:
        self._calls.append((self._name, request))
        return {"endpoint": self._name, "request": request}


class _Capability:
    def __init__(self, name: str, calls: list[tuple[str, object]]) -> None:
        setattr(self, name, _RecordingEndpoint(name, calls))


class _AttentionApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []
        for name in (
            "start_attention_session",
            "mount_attention_session_layout",
            "mount_attention_session_section",
            "apply_session_layout_topology_transition",
            "apply_session_layout_transition",
            "describe_attention_session",
            "describe_attention_transition",
            "list_attention_transitions",
            "validate_attention_transition",
        ):
            setattr(self, name, _Capability(name, self.calls))


class _ApiClient:
    def __init__(self) -> None:
        self.attention = _AttentionApi()


@pytest.mark.asyncio
async def test_attention_sdk_routes_transition_helpers_to_generated_api() -> None:
    api_client = _ApiClient()
    client = build_attention_sdk_client(api_client=api_client)
    request = object()

    assert await client.describe_attention_session(request) == {
        "endpoint": "describe_attention_session",
        "request": request,
    }
    assert await client.start_attention_session(request) == {
        "endpoint": "start_attention_session",
        "request": request,
    }
    assert await client.mount_attention_session_layout(request) == {
        "endpoint": "mount_attention_session_layout",
        "request": request,
    }
    assert await client.mount_attention_session_section(request) == {
        "endpoint": "mount_attention_session_section",
        "request": request,
    }
    assert await client.apply_session_layout_transition(request) == {
        "endpoint": "apply_session_layout_transition",
        "request": request,
    }
    assert await client.apply_session_layout_topology_transition(request) == {
        "endpoint": "apply_session_layout_topology_transition",
        "request": request,
    }
    assert await client.describe_attention_transition(request) == {
        "endpoint": "describe_attention_transition",
        "request": request,
    }
    assert await client.list_attention_transitions(request) == {
        "endpoint": "list_attention_transitions",
        "request": request,
    }
    assert await client.validate_attention_transition(request) == {
        "endpoint": "validate_attention_transition",
        "request": request,
    }
    assert api_client.attention.calls == [
        ("describe_attention_session", request),
        ("start_attention_session", request),
        ("mount_attention_session_layout", request),
        ("mount_attention_session_section", request),
        ("apply_session_layout_transition", request),
        ("apply_session_layout_topology_transition", request),
        ("describe_attention_transition", request),
        ("list_attention_transitions", request),
        ("validate_attention_transition", request),
    ]
