from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_reactivity_service_api.client import (
    ReactivityActionSubscribeLifecycleStreamEvent,
    ReactivityEventSubscribeEventsStreamEvent,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecycleSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityEventSubscriptionResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureResponse,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListRequest,
)
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusRequest,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusResponse,
)


class ReactivitySdkError(RuntimeError):
    pass


class _ReactivityStatusCapabilityClient(Protocol):
    async def get_status(
        self,
        request: ReactivityServiceStatusRequest,
    ) -> ReactivityServiceStatusResponse: ...


class _ReactivityEventCapabilityClient(Protocol):
    async def subscribe_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> ReactivityEventSubscriptionResponse: ...

    def stream_subscribe_events(
        self,
        request: ReactivityEventSubscriptionRequest,
    ) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]: ...


class _ReactivityActionCapabilityClient(Protocol):
    async def resolve_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse: ...

    async def publish_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse: ...

    async def subscribe_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> ReactivityActionLifecycleSubscriptionResponse: ...

    def stream_subscribe_lifecycle(
        self,
        request: ReactivityActionLifecycleSubscriptionRequest,
    ) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]: ...


class _ReactivityPolicyCapabilityClient(Protocol):
    async def ensure_bundle(
        self,
        request: ReactivityPolicyBundleEnsureRequest,
    ) -> ReactivityPolicyBundleEnsureResponse: ...

    async def list_bundles(
        self,
        request: ReactivityPolicyBundleListRequest,
    ) -> ReactivityPolicyBundleListResponse: ...


class _ReactivityApiNamespaceClient(Protocol):
    @property
    def action(self) -> _ReactivityActionCapabilityClient: ...

    @property
    def event(self) -> _ReactivityEventCapabilityClient: ...

    @property
    def policy(self) -> _ReactivityPolicyCapabilityClient: ...

    @property
    def status(self) -> _ReactivityStatusCapabilityClient: ...


class ReactivityGeneratedApiClient(Protocol):
    @property
    def reactivity(self) -> _ReactivityApiNamespaceClient: ...


@dataclass(frozen=True, slots=True)
class ReactivitySdkClient:
    api_client: ReactivityGeneratedApiClient

    async def get_status(
        self,
        *,
        request_id: UUID | None = None,
        subscriber_id: str | None = None,
    ) -> ReactivityServiceStatusResponse:
        response = await self.api_client.reactivity.status.get_status(
            ReactivityServiceStatusRequest(
                request_id=request_id,
                subscriber_id=subscriber_id,
            )
        )
        _raise_if_rejected(response, operation="get_status")
        return response

    async def subscribe_events(
        self,
        *,
        subscriber_id: str,
        event_type_filters: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_filters: Sequence[UUID] = (),
        include_replay: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> ReactivityEventSubscriptionResponse:
        request = build_event_subscription_request(
            subscriber_id=subscriber_id,
            event_type_filters=event_type_filters,
            branch_filters=branch_filters,
            projection_hash_filters=projection_hash_filters,
            object_instance_graph_filters=object_instance_graph_filters,
            include_replay=include_replay,
            resume_after_event_id=resume_after_event_id,
        )
        response = await self.api_client.reactivity.event.subscribe_events(request)
        _raise_if_rejected(response, operation="subscribe_events")
        return response

    def stream_events(
        self,
        *,
        subscriber_id: str,
        event_type_filters: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        object_instance_graph_filters: Sequence[UUID] = (),
        include_replay: bool = True,
        resume_after_event_id: UUID | None = None,
    ) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]:
        request = build_event_subscription_request(
            subscriber_id=subscriber_id,
            event_type_filters=event_type_filters,
            branch_filters=branch_filters,
            projection_hash_filters=projection_hash_filters,
            object_instance_graph_filters=object_instance_graph_filters,
            include_replay=include_replay,
            resume_after_event_id=resume_after_event_id,
        )
        return self.api_client.reactivity.event.stream_subscribe_events(request)

    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse:
        response = await self.api_client.reactivity.action.resolve_intents(request)
        _raise_if_rejected(response, operation="resolve_action_intents")
        return response

    async def publish_action_lifecycle(
        self,
        request: ReactivityActionLifecyclePublishRequest,
    ) -> ReactivityActionLifecyclePublishResponse:
        response = await self.api_client.reactivity.action.publish_lifecycle(request)
        _raise_if_rejected(response, operation="publish_action_lifecycle")
        return response

    async def subscribe_action_lifecycle(
        self,
        *,
        subscriber_id: str,
        event_id_filters: Sequence[UUID] = (),
        action_intent_id_filters: Sequence[UUID] = (),
        action_execution_id_filters: Sequence[UUID] = (),
        action_type_filters: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        include_replay: bool = True,
        resume_after_action_execution_id: UUID | None = None,
    ) -> ReactivityActionLifecycleSubscriptionResponse:
        request = build_action_lifecycle_subscription_request(
            subscriber_id=subscriber_id,
            event_id_filters=event_id_filters,
            action_intent_id_filters=action_intent_id_filters,
            action_execution_id_filters=action_execution_id_filters,
            action_type_filters=action_type_filters,
            branch_filters=branch_filters,
            projection_hash_filters=projection_hash_filters,
            include_replay=include_replay,
            resume_after_action_execution_id=resume_after_action_execution_id,
        )
        response = await self.api_client.reactivity.action.subscribe_lifecycle(request)
        _raise_if_rejected(response, operation="subscribe_action_lifecycle")
        return response

    def stream_action_lifecycle(
        self,
        *,
        subscriber_id: str,
        event_id_filters: Sequence[UUID] = (),
        action_intent_id_filters: Sequence[UUID] = (),
        action_execution_id_filters: Sequence[UUID] = (),
        action_type_filters: Sequence[str] = (),
        branch_filters: Sequence[UUID] = (),
        projection_hash_filters: Sequence[str] = (),
        include_replay: bool = True,
        resume_after_action_execution_id: UUID | None = None,
    ) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]:
        request = build_action_lifecycle_subscription_request(
            subscriber_id=subscriber_id,
            event_id_filters=event_id_filters,
            action_intent_id_filters=action_intent_id_filters,
            action_execution_id_filters=action_execution_id_filters,
            action_type_filters=action_type_filters,
            branch_filters=branch_filters,
            projection_hash_filters=projection_hash_filters,
            include_replay=include_replay,
            resume_after_action_execution_id=resume_after_action_execution_id,
        )
        return self.api_client.reactivity.action.stream_subscribe_lifecycle(request)

    async def ensure_policy_bundle(
        self,
        request: ReactivityPolicyBundleEnsureRequest,
    ) -> ReactivityPolicyBundleEnsureResponse:
        response = await self.api_client.reactivity.policy.ensure_bundle(request)
        _raise_if_rejected(response, operation="ensure_policy_bundle")
        return response

    async def list_policy_bundles(
        self,
        *,
        request_id: UUID | None = None,
        subscriber_id: str | None = None,
        owner_ref: str | None = None,
        policy_key: str | None = None,
    ) -> ReactivityPolicyBundleListResponse:
        response = await self.api_client.reactivity.policy.list_bundles(
            ReactivityPolicyBundleListRequest(
                request_id=request_id,
                subscriber_id=subscriber_id,
                owner_ref=owner_ref,
                policy_key=policy_key,
            )
        )
        _raise_if_rejected(response, operation="list_policy_bundles")
        return response


class AwareReactivitySdk:
    api_client: ReactivityGeneratedApiClient
    reactivity: ReactivitySdkClient

    def __init__(self, api_client: ReactivityGeneratedApiClient) -> None:
        self.api_client = api_client
        self.reactivity = ReactivitySdkClient(api_client=api_client)


def build_event_subscription_request(
    *,
    subscriber_id: str,
    event_type_filters: Sequence[str] = (),
    branch_filters: Sequence[UUID] = (),
    projection_hash_filters: Sequence[str] = (),
    object_instance_graph_filters: Sequence[UUID] = (),
    include_replay: bool = True,
    resume_after_event_id: UUID | None = None,
) -> ReactivityEventSubscriptionRequest:
    return ReactivityEventSubscriptionRequest(
        subscriber_id=subscriber_id,
        event_type_filters=list(event_type_filters),
        branch_filters=list(branch_filters),
        projection_hash_filters=list(projection_hash_filters),
        object_instance_graph_filters=list(object_instance_graph_filters),
        include_replay=include_replay,
        resume_after_event_id=resume_after_event_id,
    )


def build_action_lifecycle_subscription_request(
    *,
    subscriber_id: str,
    event_id_filters: Sequence[UUID] = (),
    action_intent_id_filters: Sequence[UUID] = (),
    action_execution_id_filters: Sequence[UUID] = (),
    action_type_filters: Sequence[str] = (),
    branch_filters: Sequence[UUID] = (),
    projection_hash_filters: Sequence[str] = (),
    include_replay: bool = True,
    resume_after_action_execution_id: UUID | None = None,
) -> ReactivityActionLifecycleSubscriptionRequest:
    return ReactivityActionLifecycleSubscriptionRequest(
        subscriber_id=subscriber_id,
        event_id_filters=list(event_id_filters),
        action_intent_id_filters=list(action_intent_id_filters),
        action_execution_id_filters=list(action_execution_id_filters),
        action_type_filters=list(action_type_filters),
        branch_filters=list(branch_filters),
        projection_hash_filters=list(projection_hash_filters),
        include_replay=include_replay,
        resume_after_action_execution_id=resume_after_action_execution_id,
    )


def _raise_if_rejected(response: object, *, operation: str) -> None:
    error = getattr(response, "error", None)
    accepted = getattr(response, "accepted", True)
    if error is None and accepted is not False:
        return
    details = error or "response was rejected"
    raise ReactivitySdkError(f"Reactivity SDK {operation} failed: {details}")


__all__ = [
    "AwareReactivitySdk",
    "ReactivityGeneratedApiClient",
    "ReactivitySdkClient",
    "ReactivitySdkError",
    "build_action_lifecycle_subscription_request",
    "build_event_subscription_request",
]
