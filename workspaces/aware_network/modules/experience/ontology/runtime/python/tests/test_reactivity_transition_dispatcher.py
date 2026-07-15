from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest

from aware_reactivity.stable_ids import (
    stable_action_config_id,
    stable_action_intent_id,
    stable_event_config_id,
    stable_event_id,
)

from aware_experience.reactivity_transition_dispatcher import (
    ExperienceReactivityViewTransition,
    dispatch_reactivity_view_transition_with_sdk,
    stream_reactivity_view_transition_dispatches,
)
from aware_experience.section_graph_binding.api_models import (
    ApplyExperienceViewEventTransitionRequest,
    ApplyExperienceViewEventTransitionResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntent,
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)


def _bridge_event(
    *,
    event_type: str = "identity.admitted",
) -> ActorReactivityBridgeEvent:
    event_config_id = stable_event_config_id(name=event_type)
    activation_id = uuid4()
    branch_id = uuid4()
    return ActorReactivityBridgeEvent(
        event_id=stable_event_id(
            config_id=event_config_id,
            activation_id=activation_id,
        ),
        event_config_id=event_config_id,
        activation_id=activation_id,
        event_type=event_type,
        source="environment_service_api_fanout",
        created_at_unix_ms=1_770_000_000_000,
        branch_id=branch_id,
        projection_hash="identity.projection",
        commit_id=uuid4(),
        event_config_condition_config_id=uuid4(),
        root_object_id=uuid4(),
        object_instance_graph_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
        graph_hash_post="hash-post",
    )


def _action_intent(
    *,
    event: ActorReactivityBridgeEvent,
    action_type: str = "experience.focus.actor_home",
) -> ReactivityActionIntent:
    actor_subscription_id = uuid4()
    action_config_id = stable_action_config_id(name=action_type)
    intent_key = f"{actor_subscription_id}:{action_config_id}"
    return ReactivityActionIntent(
        action_intent_id=stable_action_intent_id(
            event_id=event.event_id,
            config_id=action_config_id,
            intent_key=intent_key,
        ),
        intent_key=intent_key,
        event_id=event.event_id,
        event_config_id=event.event_config_id,
        activation_id=event.activation_id,
        event_type=event.event_type,
        source=event.source,
        branch_id=event.branch_id,
        projection_hash=event.projection_hash,
        commit_id=event.commit_id,
        actor_id=uuid4(),
        actor_subscription_id=actor_subscription_id,
        event_config_condition_config_scope_id=uuid4(),
        event_config_condition_config_id=event.event_config_condition_config_id,
        action_config_id=action_config_id,
        action_type=action_type,
        root_object_id=event.root_object_id,
        object_instance_graph_id=event.object_instance_graph_id,
        object_instance_graph_commit_id=event.object_instance_graph_commit_id,
        object_instance_graph_branch_id=event.branch_id,
        focus_scope_id=uuid4(),
        focus_id=uuid4(),
        graph_hash_post=event.graph_hash_post,
    )


def _transition(
    *,
    event_type: str = "identity.admitted",
    action_type: str | None = "experience.focus.actor_home",
) -> ExperienceReactivityViewTransition:
    return ExperienceReactivityViewTransition(
        experience_name="aware_control_identity",
        profile_key="os.default",
        transition_key="identity_admission.actor_home",
        source_view_ref="aware_control_identity.identity.admission.v1",
        event_type=event_type,
        action_type=action_type,
        target_view_ref="aware_control_identity.actor.home.v1",
        target_binding_key="actor.home",
        target_section_key="actor_home",
        target_graph_identity_ref="identity.actor",
        focus_scope_title="Actor home",
    )


class _FakeReactivitySdk:
    def __init__(
        self,
        *,
        intents: tuple[ReactivityActionIntent, ...] = (),
        events: tuple[ActorReactivityBridgeEvent, ...] = (),
    ) -> None:
        self.intents = intents
        self.events = events
        self.resolve_requests: list[ReactivityActionIntentResolveRequest] = []
        self.stream_kwargs: dict[str, object] | None = None

    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse:
        self.resolve_requests.append(request)
        return ReactivityActionIntentResolveResponse(
            request_id=request.request_id,
            accepted=True,
            intents=list(self.intents),
        )

    async def stream_events(
        self, **kwargs: object
    ) -> AsyncIterator[ActorReactivityBridgeEvent]:
        self.stream_kwargs = kwargs
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_dispatch_reactivity_event_resolves_action_and_applies_transition() -> (
    None
):
    event = _bridge_event()
    intent = _action_intent(event=event)
    sdk = _FakeReactivitySdk(intents=(intent,))
    captured_requests: list[ApplyExperienceViewEventTransitionRequest] = []
    fake_response = cast(ApplyExperienceViewEventTransitionResponse, object())

    async def _apply_transition(*, request, host_context):  # type: ignore[no-untyped-def]
        assert host_context == {"service": "experience"}
        captured_requests.append(request)
        return fake_response

    results = await dispatch_reactivity_view_transition_with_sdk(
        sdk=sdk,
        event=event,
        transitions=(_transition(),),
        host_context={"service": "experience"},
        apply_transition=_apply_transition,
    )

    assert len(results) == 1
    result = results[0]
    assert result.status == "applied"
    assert result.transition_key == "identity_admission.actor_home"
    assert result.action_intent_id == intent.action_intent_id
    assert result.action_type == "experience.focus.actor_home"
    assert result.response is fake_response

    resolve_request = sdk.resolve_requests[0]
    assert resolve_request.event_id == event.event_id
    assert resolve_request.event_type == "identity.admitted"
    assert resolve_request.action_type_filters == ["experience.focus.actor_home"]
    assert resolve_request.object_instance_graph_id == event.object_instance_graph_id
    assert resolve_request.actor_id is None
    assert resolve_request.target_actor_id is None

    request = captured_requests[0]
    assert request.experience_name == "aware_control_identity"
    assert request.profile_key == "os.default"
    assert request.transition_key == "identity_admission.actor_home"
    assert request.source_view_ref == "aware_control_identity.identity.admission.v1"
    assert request.event_id == event.event_id
    assert request.action_intent_id == intent.action_intent_id
    assert request.action_type == "experience.focus.actor_home"
    assert request.target_view_ref is None
    assert request.target_binding_key is None
    assert request.target_section_key is None
    assert request.target_graph_identity_ref is None
    assert request.activation_scope is not None
    assert request.activation_scope.branch_id == event.branch_id
    assert request.activation_scope.state_projection_hash == event.projection_hash
    assert request.activation_scope.focus_scope_id == intent.focus_scope_id
    assert request.focus_scope_title == "Actor home"


@pytest.mark.asyncio
async def test_dispatch_reactivity_event_skips_non_matching_action_type() -> None:
    event = _bridge_event()
    sdk = _FakeReactivitySdk(
        intents=(_action_intent(event=event, action_type="experience.program.other"),)
    )
    applied = False

    async def _apply_transition(*, request, host_context):  # type: ignore[no-untyped-def]
        nonlocal applied
        applied = True
        return object()

    results = await dispatch_reactivity_view_transition_with_sdk(
        sdk=sdk,
        event=event,
        transitions=(_transition(),),
        host_context=object(),
        apply_transition=_apply_transition,
    )

    assert results[0].status == "skipped"
    assert results[0].reason == "no_matching_action_transition"
    assert applied is False


@pytest.mark.asyncio
async def test_stream_reactivity_transition_dispatches_uses_transition_event_filters() -> (
    None
):
    event = _bridge_event()
    intent = _action_intent(event=event)
    sdk = _FakeReactivitySdk(intents=(intent,), events=(event,))
    captured_requests: list[ApplyExperienceViewEventTransitionRequest] = []

    async def _apply_transition(*, request, host_context):  # type: ignore[no-untyped-def]
        captured_requests.append(request)
        return cast(ApplyExperienceViewEventTransitionResponse, object())

    stream = stream_reactivity_view_transition_dispatches(
        sdk=sdk,
        transitions=(
            _transition(event_type="identity.admitted"),
            _transition(event_type="conversation.message.created", action_type=None),
        ),
        host_context=object(),
        subscriber_id="experience.transition.test",
        include_replay=False,
        max_events=1,
        apply_transition=_apply_transition,
    )
    results = [result async for result in stream]

    assert len(results) == 1
    assert results[0].status == "applied"
    assert captured_requests[0].event_id == event.event_id
    assert sdk.stream_kwargs is not None
    assert sdk.stream_kwargs["subscriber_id"] == "experience.transition.test"
    assert sdk.stream_kwargs["include_replay"] is False
    assert sdk.stream_kwargs["event_type_filters"] == (
        "conversation.message.created",
        "identity.admitted",
    )
