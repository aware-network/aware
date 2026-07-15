from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MemorySdkClient:
    api_client: Any

    async def ensure_memory_working(self, request: object) -> object:
        return await self._invoke(
            "ensure_memory_working",
            "ensure_memory_working",
            request,
        )

    async def describe_memory_working(self, request: object) -> object:
        return await self._invoke(
            "describe_memory_working",
            "describe_memory_working",
            request,
        )

    async def list_memory_working_items(self, request: object) -> object:
        return await self._invoke(
            "list_memory_working_items",
            "list_memory_working_items",
            request,
        )

    async def validate_memory_working_item(self, request: object) -> object:
        return await self._invoke(
            "validate_memory_working_item",
            "validate_memory_working_item",
            request,
        )

    async def resolve_memory_context(self, request: object) -> object:
        return await self._invoke(
            "resolve_memory_context",
            "resolve_memory_context",
            request,
        )

    async def resolve_actor_memory_context(self, request: object) -> object:
        return await self._invoke(
            "resolve_actor_memory_context",
            "resolve_actor_memory_context",
            request,
        )

    async def watch_actor_memory_context(self, request: object) -> object:
        return await self._invoke(
            "watch_actor_memory_context",
            "watch_actor_memory_context",
            request,
        )

    async def resolve_actor_memory_context_frame(self, request: object) -> object:
        return await self._invoke(
            "resolve_actor_memory_context_frame",
            "resolve_actor_memory_context_frame",
            request,
        )

    async def watch_actor_memory_context_frame(self, request: object) -> object:
        return await self._invoke(
            "watch_actor_memory_context_frame",
            "watch_actor_memory_context_frame",
            request,
        )

    async def stream_watch_actor_memory_context_frame(
        self,
        request: object,
    ) -> AsyncIterator[object]:
        capability = self.api_client.memory.watch_actor_memory_context_frame
        stream = capability.stream_watch_actor_memory_context_frame
        async for event in stream(request):
            yield event

    async def remember_attention_transition(self, request: object) -> object:
        return await self._invoke(
            "remember_attention_transition",
            "remember_attention_transition",
            request,
        )

    async def remember_content(self, request: object) -> object:
        return await self._invoke(
            "remember_content",
            "remember_content",
            request,
        )

    async def remember_event(self, request: object) -> object:
        return await self._invoke(
            "remember_event",
            "remember_event",
            request,
        )

    async def record_resolved_event_meaning(self, request: object) -> object:
        return await self._invoke(
            "record_resolved_event_meaning",
            "record_resolved_event_meaning",
            request,
        )

    async def _invoke(
        self,
        capability_name: str,
        endpoint_name: str,
        request: object,
    ) -> object:
        capability = getattr(self.api_client.memory, capability_name)
        endpoint = getattr(capability, endpoint_name)
        return await endpoint(request)


def build_memory_sdk_client(api_client: Any) -> MemorySdkClient:
    return MemorySdkClient(api_client=api_client)
