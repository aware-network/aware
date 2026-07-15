from __future__ import annotations

import pytest

from aware_memory_sdk import build_memory_sdk_client


class _Endpoint:
    def __init__(self, calls: list[tuple[str, object]], name: str) -> None:
        self._calls = calls
        self._name = name

    async def __call__(self, request: object) -> object:
        self._calls.append((self._name, request))
        return {"ok": self._name}


class _Capability:
    def __init__(self, calls: list[tuple[str, object]], name: str) -> None:
        setattr(self, name, _Endpoint(calls, name))
        if name == "watch_actor_memory_context_frame":

            async def _stream(request: object):
                stream_name = f"stream_{name}"
                calls.append((stream_name, request))
                yield {"ok": stream_name}

            setattr(self, f"stream_{name}", _stream)


class _MemoryApi:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        for name in (
            "ensure_memory_working",
            "describe_memory_working",
            "list_memory_working_items",
            "validate_memory_working_item",
            "resolve_memory_context",
            "resolve_actor_memory_context",
            "watch_actor_memory_context",
            "resolve_actor_memory_context_frame",
            "watch_actor_memory_context_frame",
            "remember_attention_transition",
            "remember_content",
            "remember_event",
            "record_resolved_event_meaning",
        ):
            setattr(self, name, _Capability(calls, name))


class _ApiClient:
    def __init__(self, calls: list[tuple[str, object]]) -> None:
        self.memory = _MemoryApi(calls)


@pytest.mark.asyncio
async def test_memory_sdk_client_routes_working_memory_methods() -> None:
    calls: list[tuple[str, object]] = []
    client = build_memory_sdk_client(_ApiClient(calls))
    request = object()

    assert await client.ensure_memory_working(request) == {
        "ok": "ensure_memory_working"
    }
    assert await client.describe_memory_working(request) == {
        "ok": "describe_memory_working"
    }
    assert await client.list_memory_working_items(request) == {
        "ok": "list_memory_working_items"
    }
    assert await client.validate_memory_working_item(request) == {
        "ok": "validate_memory_working_item"
    }
    assert await client.resolve_memory_context(request) == {
        "ok": "resolve_memory_context"
    }
    assert await client.resolve_actor_memory_context(request) == {
        "ok": "resolve_actor_memory_context"
    }
    assert await client.watch_actor_memory_context(request) == {
        "ok": "watch_actor_memory_context"
    }
    assert await client.resolve_actor_memory_context_frame(request) == {
        "ok": "resolve_actor_memory_context_frame"
    }
    assert await client.watch_actor_memory_context_frame(request) == {
        "ok": "watch_actor_memory_context_frame"
    }
    assert [
        event async for event in client.stream_watch_actor_memory_context_frame(request)
    ] == [{"ok": "stream_watch_actor_memory_context_frame"}]
    assert await client.remember_attention_transition(request) == {
        "ok": "remember_attention_transition"
    }
    assert await client.remember_content(request) == {"ok": "remember_content"}
    assert await client.remember_event(request) == {"ok": "remember_event"}
    assert await client.record_resolved_event_meaning(request) == {
        "ok": "record_resolved_event_meaning"
    }

    assert [name for name, _ in calls] == [
        "ensure_memory_working",
        "describe_memory_working",
        "list_memory_working_items",
        "validate_memory_working_item",
        "resolve_memory_context",
        "resolve_actor_memory_context",
        "watch_actor_memory_context",
        "resolve_actor_memory_context_frame",
        "watch_actor_memory_context_frame",
        "stream_watch_actor_memory_context_frame",
        "remember_attention_transition",
        "remember_content",
        "remember_event",
        "record_resolved_event_meaning",
    ]
