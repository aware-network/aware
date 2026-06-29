# GENERATED CODE - DO NOT MODIFY BY HAND
# Thin typed generated API client wrapper over aware_api.invoker.AwareApiEndpointInvoker.
from __future__ import annotations

from typing import AsyncIterator, cast

from aware_api import AwareApiEndpointInvoker
from ._bindings import API_INTERFACE_SPEC, API_INVOCATION_MANIFEST
from ._bindings import (
    REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF,
    REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF,
    REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF,
    REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF,
    REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF,
    REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF,
    REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF,
)
from aware_reactivity_ontology.action.action_feedback import ActionFeedback
from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.action_terminal import ActionTerminal
from aware_reactivity_service_dto.reactivity.bridge_event import ActorReactivityBridgeEvent
from aware_reactivity_service_dto.reactivity.policy_bundle import (
    ReactivityPolicyBundleEnsureRequest,
    ReactivityPolicyBundleEnsureResponse,
    ReactivityPolicyBundleListRequest,
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityActionLifecyclePublishRequest,
    ReactivityActionLifecyclePublishResponse,
    ReactivityActionLifecycleSubscriptionRequest,
    ReactivityActionLifecycleSubscriptionResponse,
    ReactivityEventSubscriptionRequest,
    ReactivityEventSubscriptionResponse,
    ReactivityServiceStatusRequest,
    ReactivityServiceStatusResponse,
)

ReactivityActionSubscribeLifecycleStreamEvent = (
    ActionTerminal | ActionFeedback | ReactivityActionIntent | ActionExecution
)
ReactivityEventSubscribeEventsStreamEvent = ActorReactivityBridgeEvent


class ReactivityActionCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def publish_lifecycle(
        self, request: ReactivityActionLifecyclePublishRequest
    ) -> ReactivityActionLifecyclePublishResponse:
        """Publish ontology-backed action lifecycle evidence from an action
        service back to Reactivity without making Reactivity the executor."""
        return cast(
            ReactivityActionLifecyclePublishResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__ACTION__PUBLISH_LIFECYCLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def resolve_intents(
        self, request: ReactivityActionIntentResolveRequest
    ) -> ReactivityActionIntentResolveResponse:
        """Resolve actor-subscription-backed action intents for one matched
        Reactivity policy event without fulfilling the actions."""
        return cast(
            ReactivityActionIntentResolveResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__ACTION__RESOLVE_INTENTS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def subscribe_lifecycle(
        self, request: ReactivityActionLifecycleSubscriptionRequest
    ) -> ReactivityActionLifecycleSubscriptionResponse:
        """Subscribe to Reactivity-owned action execution lifecycle events."""
        return cast(
            ReactivityActionLifecycleSubscriptionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_subscribe_lifecycle(
        self, request: ReactivityActionLifecycleSubscriptionRequest
    ) -> AsyncIterator[ReactivityActionSubscribeLifecycleStreamEvent]:
        """Subscribe to Reactivity-owned action execution lifecycle events."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=REACTIVITY__ACTION__SUBSCRIBE_LIFECYCLE_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(ReactivityActionSubscribeLifecycleStreamEvent, event)


class ReactivityEventCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def subscribe_events(
        self, request: ReactivityEventSubscriptionRequest
    ) -> ReactivityEventSubscriptionResponse:
        """Subscribe to Reactivity-owned semantic bridge events."""
        return cast(
            ReactivityEventSubscriptionResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def stream_subscribe_events(
        self, request: ReactivityEventSubscriptionRequest
    ) -> AsyncIterator[ReactivityEventSubscribeEventsStreamEvent]:
        """Subscribe to Reactivity-owned semantic bridge events."""
        async for event in self._client.stream_api_endpoint(
            manifest=API_INVOCATION_MANIFEST,
            endpoint_ref=REACTIVITY__EVENT__SUBSCRIBE_EVENTS_ENDPOINT_REF,
            request_payload=request,
        ):
            yield cast(ReactivityEventSubscribeEventsStreamEvent, event)


class ReactivityPolicyCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def ensure_bundle(self, request: ReactivityPolicyBundleEnsureRequest) -> ReactivityPolicyBundleEnsureResponse:
        """Register or verify a deterministic Reactivity policy bundle."""
        return cast(
            ReactivityPolicyBundleEnsureResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__POLICY__ENSURE_BUNDLE_ENDPOINT_REF,
                request_payload=request,
            ),
        )

    async def list_bundles(self, request: ReactivityPolicyBundleListRequest) -> ReactivityPolicyBundleListResponse:
        """List Reactivity policy bundles known to this service instance."""
        return cast(
            ReactivityPolicyBundleListResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__POLICY__LIST_BUNDLES_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ReactivityStatusCapabilityClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client

    async def get_status(self, request: ReactivityServiceStatusRequest) -> ReactivityServiceStatusResponse:
        """Read Reactivity service runtime status without graph-store access."""
        return cast(
            ReactivityServiceStatusResponse,
            await self._client.invoke_api_endpoint(
                manifest=API_INVOCATION_MANIFEST,
                endpoint_ref=REACTIVITY__STATUS__GET_STATUS_ENDPOINT_REF,
                request_payload=request,
            ),
        )


class ReactivityApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.action = ReactivityActionCapabilityClient(client)
        self.event = ReactivityEventCapabilityClient(client)
        self.policy = ReactivityPolicyCapabilityClient(client)
        self.status = ReactivityStatusCapabilityClient(client)


class AwareReactivityServiceApiClient:
    def __init__(self, client: AwareApiEndpointInvoker) -> None:
        self._client = client
        self.interface_spec = API_INTERFACE_SPEC
        self.invocation_manifest = API_INVOCATION_MANIFEST
        self.reactivity = ReactivityApiClient(client)


__all__ = [
    "AwareReactivityServiceApiClient",
    "ReactivityApiClient",
    "ReactivityActionCapabilityClient",
    "ReactivityEventCapabilityClient",
    "ReactivityPolicyCapabilityClient",
    "ReactivityStatusCapabilityClient",
    "ReactivityActionSubscribeLifecycleStreamEvent",
    "ReactivityEventSubscribeEventsStreamEvent",
]
