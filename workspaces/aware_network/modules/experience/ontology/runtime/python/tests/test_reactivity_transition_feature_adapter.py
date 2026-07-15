from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from uuid import uuid4

import pytest

from aware_reactivity.stable_ids import stable_event_config_id, stable_event_id

from aware_experience.reactivity_transition_dispatcher import (
    ExperienceReactivityViewTransition,
)
from aware_experience.reactivity_transition_specs import (
    ExperienceReactivityViewTransitionSpecResolution,
)
from aware_experience.section_graph_binding.api_models import (
    ApplyExperienceViewEventTransitionResponse,
)
from aware_experience.supervisor import (
    ExperienceReactivityTransitionDispatchFeatureAdapter,
    ExperienceSessionFeatureLease,
    ExperienceSessionScope,
    REACTIVITY_TRANSITION_DISPATCH_FEATURE,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)


class _FakeReactivitySdk:
    def __init__(self, *, events: tuple[ActorReactivityBridgeEvent, ...]) -> None:
        self.events = events
        self.stream_kwargs: dict[str, object] | None = None

    async def resolve_action_intents(
        self,
        request: ReactivityActionIntentResolveRequest,
    ) -> ReactivityActionIntentResolveResponse:
        return ReactivityActionIntentResolveResponse(
            request_id=request.request_id,
            accepted=True,
            intents=[],
        )

    async def stream_events(
        self,
        **kwargs: object,
    ) -> AsyncIterator[ActorReactivityBridgeEvent]:
        self.stream_kwargs = kwargs
        for event in self.events:
            yield event


def _transition() -> ExperienceReactivityViewTransition:
    return ExperienceReactivityViewTransition(
        experience_name="aware_control_identity",
        profile_key="os.default",
        transition_key="identity_admission.actor_home",
        source_view_ref="aware_control_identity.identity.admission.v1",
        event_type="identity.admitted",
        target_view_ref="aware_control_identity.actor.home.v1",
        target_binding_key="actor.home",
        target_section_key="actor_home",
        target_graph_identity_ref="identity.actor",
    )


@pytest.mark.asyncio
async def test_reactivity_transition_feature_adapter_maps_session_scope_to_supervisor_config() -> (
    None
):
    environment_id = uuid4()
    branch_id = uuid4()
    event_config_id = stable_event_config_id(name="identity.admitted")
    activation_id = uuid4()
    event = ActorReactivityBridgeEvent(
        event_id=stable_event_id(
            config_id=event_config_id,
            activation_id=activation_id,
        ),
        event_config_id=event_config_id,
        activation_id=activation_id,
        event_type="identity.admitted",
        source="environment_service_api_fanout",
        created_at_unix_ms=1_770_000_000_000,
        environment_id=environment_id,
        branch_id=branch_id,
        projection_hash="projection.hash",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    replay_activation_id = uuid4()
    replay_event = ActorReactivityBridgeEvent(
        event_id=stable_event_id(
            config_id=event_config_id,
            activation_id=replay_activation_id,
        ),
        event_config_id=event_config_id,
        activation_id=replay_activation_id,
        event_type="identity.admitted",
        source="environment_service_api_fanout",
        created_at_unix_ms=1_770_000_000_001,
        environment_id=environment_id,
        branch_id=branch_id,
        projection_hash="projection.hash",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )
    sdk = _FakeReactivitySdk(events=(event, replay_event))
    applied_requests: list[object] = []
    lease = ExperienceSessionFeatureLease(
        lease_key="lease-1",
        session_scope=ExperienceSessionScope(
            experience_name="aware_control_identity",
            profile_key="os.default",
            environment_id=environment_id,
            branch_id=branch_id,
            projection_hash="projection.hash",
        ),
        feature_key=REACTIVITY_TRANSITION_DISPATCH_FEATURE,
        config={
            "subscriber_id": "experience.transition.test",
            "include_replay": False,
            "max_events": 1,
        },
    )

    async def _load_specs() -> ExperienceReactivityViewTransitionSpecResolution:
        return ExperienceReactivityViewTransitionSpecResolution(
            experience_name="aware_control_identity",
            profile_key="os.default",
            catalog_revision="catalog-rev",
            transitions=(_transition(),),
        )

    async def _apply_transition(*, request, host_context):  # type: ignore[no-untyped-def]
        assert host_context == {"service": "experience"}
        applied_requests.append(request)
        return cast(ApplyExperienceViewEventTransitionResponse, object())

    adapter = ExperienceReactivityTransitionDispatchFeatureAdapter(
        sdk=sdk,  # type: ignore[arg-type]
        host_context={"service": "experience"},
        load_specs_for_lease=lambda _: _load_specs,
        apply_transition=_apply_transition,
    )

    result = await adapter.run(lease)

    assert result.status == "completed"
    assert len(applied_requests) == 1
    assert getattr(applied_requests[0], "profile_key") == "os.default"
    assert sdk.stream_kwargs is not None
    assert sdk.stream_kwargs["subscriber_id"] == "experience.transition.test"
    assert sdk.stream_kwargs["environment_id_filters"] == (environment_id,)
    assert sdk.stream_kwargs["branch_filters"] == (branch_id,)
    assert sdk.stream_kwargs["projection_hash_filters"] == ("projection.hash",)
    assert sdk.stream_kwargs["include_replay"] is False
