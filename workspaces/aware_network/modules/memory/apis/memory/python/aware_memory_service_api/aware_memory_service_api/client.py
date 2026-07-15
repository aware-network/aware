# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF,
    MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF,
    MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF,
    MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF,
    MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF,
    MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF,
    MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF,
    MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
    MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF,
    MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF,
    MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
    MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
)
from aware_memory_service_dto.memory.working.models import MemoryActorContextEvent, MemoryActorContextFrameEvent
from aware_memory_service_dto.memory.working.service_operation import (
    DescribeMemoryWorkingRequest,
    DescribeMemoryWorkingResponse,
    EnsureMemoryWorkingRequest,
    EnsureMemoryWorkingResponse,
    ListMemoryWorkingItemsRequest,
    ListMemoryWorkingItemsResponse,
    RecordResolvedEventMeaningRequest,
    RecordResolvedEventMeaningResponse,
    RememberAttentionTransitionRequest,
    RememberAttentionTransitionResponse,
    RememberContentRequest,
    RememberContentResponse,
    RememberEventRequest,
    RememberEventResponse,
    ResolveActorMemoryContextFrameRequest,
    ResolveActorMemoryContextFrameResponse,
    ResolveActorMemoryContextRequest,
    ResolveActorMemoryContextResponse,
    ResolveMemoryContextRequest,
    ResolveMemoryContextResponse,
    ValidateMemoryWorkingItemRequest,
    ValidateMemoryWorkingItemResponse,
    WatchActorMemoryContextFrameRequest,
    WatchActorMemoryContextFrameResponse,
    WatchActorMemoryContextRequest,
    WatchActorMemoryContextResponse,
)

MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent = MemoryActorContextEvent
MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent = MemoryActorContextFrameEvent


class MemoryDescribeMemoryWorkingCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def describe_memory_working(self, request: DescribeMemoryWorkingRequest) -> DescribeMemoryWorkingResponse:
        """Read one MemoryWorking lane by id or actor/key coordinates."""
        return cast(
            DescribeMemoryWorkingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__DESCRIBE_MEMORY_WORKING__DESCRIBE_MEMORY_WORKING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryEnsureMemoryWorkingCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_memory_working(self, request: EnsureMemoryWorkingRequest) -> EnsureMemoryWorkingResponse:
        """Resolve or create one actor-scoped MemoryWorking lane."""
        return cast(
            EnsureMemoryWorkingResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__ENSURE_MEMORY_WORKING__ENSURE_MEMORY_WORKING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryListMemoryWorkingItemsCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def list_memory_working_items(self, request: ListMemoryWorkingItemsRequest) -> ListMemoryWorkingItemsResponse:
        """List ordered MemoryWorkingItem pins for one working-memory lane."""
        return cast(
            ListMemoryWorkingItemsResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__LIST_MEMORY_WORKING_ITEMS__LIST_MEMORY_WORKING_ITEMS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryRecordResolvedEventMeaningCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def record_resolved_event_meaning(
        self, request: RecordResolvedEventMeaningRequest
    ) -> RecordResolvedEventMeaningResponse:
        """Persist one provider-neutral resolved meaning under a verified
        remembered event with resolver terminal provenance."""
        return cast(
            RecordResolvedEventMeaningResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__RECORD_RESOLVED_EVENT_MEANING__RECORD_RESOLVED_EVENT_MEANING_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryRememberAttentionTransitionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def remember_attention_transition(
        self, request: RememberAttentionTransitionRequest
    ) -> RememberAttentionTransitionResponse:
        """Validate and retain one AttentionFocusTransition pointer in working memory."""
        return cast(
            RememberAttentionTransitionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__REMEMBER_ATTENTION_TRANSITION__REMEMBER_ATTENTION_TRANSITION_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryRememberContentCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def remember_content(self, request: RememberContentRequest) -> RememberContentResponse:
        """Retain one Content pointer in working memory."""
        return cast(
            RememberContentResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__REMEMBER_CONTENT__REMEMBER_CONTENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryRememberEventCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def remember_event(self, request: RememberEventRequest) -> RememberEventResponse:
        """Retain one Reactivity Event pointer in working memory."""
        return cast(
            RememberEventResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__REMEMBER_EVENT__REMEMBER_EVENT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryResolveActorMemoryContextCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_actor_memory_context(
        self, request: ResolveActorMemoryContextRequest
    ) -> ResolveActorMemoryContextResponse:
        """Validate actor/session context through Identity, then resolve usable Memory evidence."""
        return cast(
            ResolveActorMemoryContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT__RESOLVE_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryResolveActorMemoryContextFrameCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_actor_memory_context_frame(
        self, request: ResolveActorMemoryContextFrameRequest
    ) -> ResolveActorMemoryContextFrameResponse:
        """Resolve actor-scoped Memory context into a compact consumer frame."""
        return cast(
            ResolveActorMemoryContextFrameResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME__RESOLVE_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryResolveMemoryContextCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def resolve_memory_context(self, request: ResolveMemoryContextRequest) -> ResolveMemoryContextResponse:
        """Resolve one actor working-memory lane into evidence-labeled context."""
        return cast(
            ResolveMemoryContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__RESOLVE_MEMORY_CONTEXT__RESOLVE_MEMORY_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryValidateMemoryWorkingItemCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def validate_memory_working_item(
        self, request: ValidateMemoryWorkingItemRequest
    ) -> ValidateMemoryWorkingItemResponse:
        """Validate one retained MemoryWorkingItem and return source evidence."""
        return cast(
            ValidateMemoryWorkingItemResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__VALIDATE_MEMORY_WORKING_ITEM__VALIDATE_MEMORY_WORKING_ITEM_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class MemoryWatchActorMemoryContextCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_actor_memory_context(
        self, request: WatchActorMemoryContextRequest
    ) -> WatchActorMemoryContextResponse:
        """Read and stream actor-scoped Memory context snapshots."""
        return cast(
            WatchActorMemoryContextResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_actor_memory_context(
        self, request: WatchActorMemoryContextRequest
    ) -> AsyncIterator[MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent]:
        """Read and stream actor-scoped Memory context snapshots."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT__WATCH_ACTOR_MEMORY_CONTEXT_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent, event)


class MemoryWatchActorMemoryContextFrameCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def watch_actor_memory_context_frame(
        self, request: WatchActorMemoryContextFrameRequest
    ) -> WatchActorMemoryContextFrameResponse:
        """Read and stream actor-scoped Memory consumer frames."""
        return cast(
            WatchActorMemoryContextFrameResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_watch_actor_memory_context_frame(
        self, request: WatchActorMemoryContextFrameRequest
    ) -> AsyncIterator[MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent]:
        """Read and stream actor-scoped Memory consumer frames."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=MEMORY__WATCH_ACTOR_MEMORY_CONTEXT_FRAME__WATCH_ACTOR_MEMORY_CONTEXT_FRAME_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent, event)


class MemoryApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.describe_memory_working = MemoryDescribeMemoryWorkingCapabilityClient(client)
        self.ensure_memory_working = MemoryEnsureMemoryWorkingCapabilityClient(client)
        self.list_memory_working_items = MemoryListMemoryWorkingItemsCapabilityClient(client)
        self.record_resolved_event_meaning = MemoryRecordResolvedEventMeaningCapabilityClient(client)
        self.remember_attention_transition = MemoryRememberAttentionTransitionCapabilityClient(client)
        self.remember_content = MemoryRememberContentCapabilityClient(client)
        self.remember_event = MemoryRememberEventCapabilityClient(client)
        self.resolve_actor_memory_context = MemoryResolveActorMemoryContextCapabilityClient(client)
        self.resolve_actor_memory_context_frame = MemoryResolveActorMemoryContextFrameCapabilityClient(client)
        self.resolve_memory_context = MemoryResolveMemoryContextCapabilityClient(client)
        self.validate_memory_working_item = MemoryValidateMemoryWorkingItemCapabilityClient(client)
        self.watch_actor_memory_context = MemoryWatchActorMemoryContextCapabilityClient(client)
        self.watch_actor_memory_context_frame = MemoryWatchActorMemoryContextFrameCapabilityClient(client)


class AwareMemoryServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.memory = MemoryApiClient(client)


__all__ = [
    "AwareMemoryServiceApiClient",
    "MemoryApiClient",
    "MemoryDescribeMemoryWorkingCapabilityClient",
    "MemoryEnsureMemoryWorkingCapabilityClient",
    "MemoryListMemoryWorkingItemsCapabilityClient",
    "MemoryRecordResolvedEventMeaningCapabilityClient",
    "MemoryRememberAttentionTransitionCapabilityClient",
    "MemoryRememberContentCapabilityClient",
    "MemoryRememberEventCapabilityClient",
    "MemoryResolveActorMemoryContextCapabilityClient",
    "MemoryResolveActorMemoryContextFrameCapabilityClient",
    "MemoryResolveMemoryContextCapabilityClient",
    "MemoryValidateMemoryWorkingItemCapabilityClient",
    "MemoryWatchActorMemoryContextCapabilityClient",
    "MemoryWatchActorMemoryContextFrameCapabilityClient",
    "MemoryWatchActorMemoryContextFrameWatchActorMemoryContextFrameStreamEvent",
    "MemoryWatchActorMemoryContextWatchActorMemoryContextStreamEvent",
]
