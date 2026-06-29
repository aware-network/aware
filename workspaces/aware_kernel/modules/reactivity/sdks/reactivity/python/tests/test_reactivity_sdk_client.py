from __future__ import annotations

from typing import cast
from uuid import uuid4

import pytest

from aware_reactivity_sdk import (
    AwareReactivitySdk,
    ReactivitySdkClient,
    ReactivitySdkError,
    build_action_lifecycle_subscription_request,
    build_event_subscription_request,
)
from aware_reactivity_service_dto.reactivity.action_execution import ActionExecution
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
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
    ReactivityActionLifecycleSubscriptionResponse,
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
    ReactivityPolicyBundleListResponse,
)
from aware_reactivity_service_dto.reactivity.service_operation import (
    ReactivityServiceStatusResponse,
)


class _StatusApi:
    def __init__(self) -> None:
        self.requests = []

    async def get_status(self, request):  # noqa: ANN001, ANN201
        self.requests.append(request)
        return ReactivityServiceStatusResponse(
            request_id=request.request_id,
            active=True,
            info="ready",
        )


class _EventApi:
    def __init__(self, event: ActorReactivityBridgeEvent) -> None:
        self.requests = []
        self.stream_requests = []
        self.event = event

    async def subscribe_events(self, request):  # noqa: ANN001, ANN201
        self.requests.append(request)
        return ReactivityEventSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
        )

    async def stream_subscribe_events(self, request):  # noqa: ANN001, ANN201
        self.stream_requests.append(request)
        yield self.event


class _ActionApi:
    def __init__(self, execution: ActionExecution) -> None:
        self.resolve_requests = []
        self.publish_requests = []
        self.subscription_requests = []
        self.stream_requests = []
        self.execution = execution

    async def resolve_intents(self, request):  # noqa: ANN001, ANN201
        self.resolve_requests.append(request)
        return ReactivityActionIntentResolveResponse(
            request_id=request.request_id,
            accepted=True,
            intents=[],
        )

    async def publish_lifecycle(self, request):  # noqa: ANN001, ANN201
        self.publish_requests.append(request)
        return ReactivityActionLifecyclePublishResponse(
            request_id=request.request_id,
            accepted=True,
            published_count=1,
        )

    async def subscribe_lifecycle(self, request):  # noqa: ANN001, ANN201
        self.subscription_requests.append(request)
        return ReactivityActionLifecycleSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=True,
        )

    async def stream_subscribe_lifecycle(self, request):  # noqa: ANN001, ANN201
        self.stream_requests.append(request)
        yield self.execution


class _PolicyApi:
    def __init__(self) -> None:
        self.ensure_requests = []
        self.list_requests = []

    async def ensure_bundle(self, request):  # noqa: ANN001, ANN201
        self.ensure_requests.append(request)
        return ReactivityPolicyBundleEnsureResponse(
            request_id=request.request_id,
            accepted=True,
        )

    async def list_bundles(self, request):  # noqa: ANN001, ANN201
        self.list_requests.append(request)
        return ReactivityPolicyBundleListResponse(
            request_id=request.request_id,
            accepted=True,
        )


class _ReactivityApi:
    def __init__(self) -> None:
        event_id = uuid4()
        branch_id = uuid4()
        commit_id = uuid4()
        action_intent_id = uuid4()
        self.status = _StatusApi()
        self.event = _EventApi(
            ActorReactivityBridgeEvent(
                event_id=event_id,
                event_type="workspace.commit",
                source="workspace",
                created_at_unix_ms=1,
                branch_id=branch_id,
                projection_hash="projection",
                commit_id=commit_id,
            )
        )
        self.action = _ActionApi(
            ActionExecution(
                action_intent_id=action_intent_id,
                event_id=event_id,
                event_type="workspace.commit",
                source="workspace",
                branch_id=branch_id,
                projection_hash="projection",
                commit_id=commit_id,
            )
        )
        self.policy = _PolicyApi()


class _ApiClient:
    def __init__(self) -> None:
        self.reactivity = _ReactivityApi()


@pytest.mark.asyncio
async def test_reactivity_sdk_routes_through_generated_api() -> None:
    api_client = _ApiClient()
    sdk = ReactivitySdkClient(api_client=api_client)
    branch_id = uuid4()
    event_id = uuid4()
    action_intent_id = uuid4()
    action_execution_id = uuid4()

    status = await sdk.get_status(subscriber_id="operator")
    event_subscription = await sdk.subscribe_events(
        subscriber_id="actor-subscription",
        event_type_filters=["workspace.commit"],
        branch_filters=[branch_id],
        projection_hash_filters=["projection"],
        include_replay=False,
        resume_after_event_id=event_id,
    )
    event_stream = [
        event
        async for event in sdk.stream_events(
            subscriber_id="actor-subscription",
            event_type_filters=["workspace.commit"],
        )
    ]
    action_subscription = await sdk.subscribe_action_lifecycle(
        subscriber_id="actor-subscription",
        event_id_filters=[event_id],
        action_intent_id_filters=[action_intent_id],
        action_execution_id_filters=[action_execution_id],
        action_type_filters=["workspace.verify"],
        branch_filters=[branch_id],
        projection_hash_filters=["projection"],
        include_replay=False,
        resume_after_action_execution_id=action_execution_id,
    )
    action_stream = [
        event
        async for event in sdk.stream_action_lifecycle(
            subscriber_id="actor-subscription",
            action_type_filters=["workspace.verify"],
        )
    ]

    resolve_request = ReactivityActionIntentResolveRequest(
        event_id=event_id,
        event_type="workspace.commit",
        source="workspace",
        branch_id=branch_id,
        projection_hash="projection",
        commit_id=uuid4(),
    )
    resolve_response = await sdk.resolve_action_intents(resolve_request)
    publish_request = ReactivityActionLifecyclePublishRequest(
        publisher_id="workspace",
        execution=cast(ActionExecution, action_stream[0]),
    )
    publish_response = await sdk.publish_action_lifecycle(publish_request)
    ensure_request = ReactivityPolicyBundleEnsureRequest.model_construct(
        request_id=uuid4(),
        bundle=None,
    )
    ensure_response = await sdk.ensure_policy_bundle(ensure_request)
    list_response = await sdk.list_policy_bundles(
        subscriber_id="actor-subscription",
        owner_ref="identity:actor",
        policy_key="workspace",
    )

    assert status.active is True
    assert event_subscription.subscriber_id == "actor-subscription"
    assert action_subscription.subscriber_id == "actor-subscription"
    assert resolve_response.accepted is True
    assert publish_response.published_count == 1
    assert ensure_response.accepted is True
    assert list_response.accepted is True
    assert event_stream[0].event_type == "workspace.commit"
    assert action_stream[0].action_type is None
    assert api_client.reactivity.status.requests[0].subscriber_id == "operator"
    assert api_client.reactivity.event.requests[0].include_replay is False
    assert api_client.reactivity.event.requests[0].branch_filters == [branch_id]
    assert api_client.reactivity.event.stream_requests[0].event_type_filters == [
        "workspace.commit"
    ]
    assert api_client.reactivity.action.subscription_requests[0].action_type_filters == [
        "workspace.verify"
    ]
    assert api_client.reactivity.action.stream_requests[0].action_type_filters == [
        "workspace.verify"
    ]
    assert api_client.reactivity.action.resolve_requests[0] is resolve_request
    assert api_client.reactivity.action.publish_requests[0] is publish_request
    assert api_client.reactivity.policy.ensure_requests[0] is ensure_request
    assert api_client.reactivity.policy.list_requests[0].policy_key == "workspace"


def test_reactivity_sdk_builds_subscription_requests_without_aliasing_inputs() -> None:
    event_types = ["workspace.commit"]
    action_types = ["workspace.verify"]
    event_request = build_event_subscription_request(
        subscriber_id="actor",
        event_type_filters=event_types,
    )
    action_request = build_action_lifecycle_subscription_request(
        subscriber_id="actor",
        action_type_filters=action_types,
    )
    event_types.append("workspace.test")
    action_types.append("workspace.publish")

    assert event_request.event_type_filters == ["workspace.commit"]
    assert action_request.action_type_filters == ["workspace.verify"]


@pytest.mark.asyncio
async def test_reactivity_sdk_raises_on_rejected_response() -> None:
    api_client = _ApiClient()

    async def reject_events(request):  # noqa: ANN001, ANN202
        return ReactivityEventSubscriptionResponse(
            subscriber_id=request.subscriber_id,
            accepted=False,
            error="subscription disabled",
        )

    api_client.reactivity.event.subscribe_events = reject_events
    sdk = AwareReactivitySdk(api_client=api_client)

    with pytest.raises(ReactivitySdkError, match="subscription disabled"):
        await sdk.reactivity.subscribe_events(subscriber_id="actor-subscription")
