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
from aware_experience.reactivity_transition_supervisor import (
    ExperienceReactivityTransitionSupervisorConfig,
    run_experience_reactivity_transition_supervisor,
)
from aware_experience.section_graph_binding.api_models import (
    ApplyExperienceViewEventTransitionResponse,
)
from aware_reactivity_service_dto.reactivity.action_intent import (
    ReactivityActionIntentResolveRequest,
    ReactivityActionIntentResolveResponse,
)
from aware_reactivity_service_dto.reactivity.bridge_event import (
    ActorReactivityBridgeEvent,
)


def _event(*, event_type: str = "identity.admitted") -> ActorReactivityBridgeEvent:
    event_config_id = stable_event_config_id(name=event_type)
    activation_id = uuid4()
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
        environment_id=uuid4(),
        branch_id=uuid4(),
        projection_hash="identity.projection",
        commit_id=uuid4(),
        object_instance_graph_commit_id=uuid4(),
    )


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


class _FakeReactivitySdk:
    def __init__(self, *, events: tuple[ActorReactivityBridgeEvent, ...]) -> None:
        self.events = events
        self.stream_called = False
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
        self, **kwargs: object
    ) -> AsyncIterator[ActorReactivityBridgeEvent]:
        self.stream_called = True
        self.stream_kwargs = kwargs
        for event in self.events:
            yield event


@pytest.mark.asyncio
async def test_supervisor_loads_specs_streams_events_and_reports_health() -> None:
    event = _event()
    sdk = _FakeReactivitySdk(events=(event,))
    applied_requests: list[object] = []

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

    run = await run_experience_reactivity_transition_supervisor(
        sdk=sdk,
        host_context={"service": "experience"},
        load_specs=_load_specs,
        config=ExperienceReactivityTransitionSupervisorConfig(
            experience_name="aware_control_identity",
            profile_key="os.default",
            subscriber_id="experience.transition.test",
            include_replay=False,
            max_events=1,
        ),
        apply_transition=_apply_transition,
    )

    assert [item.kind for item in run.events] == [
        "started",
        "dispatch",
        "completed",
    ]
    assert run.health.status == "completed"
    assert run.health.catalog_revision == "catalog-rev"
    assert run.health.transition_count == 1
    assert run.health.dispatch_count == 1
    assert run.health.applied_count == 1
    assert run.health.skipped_count == 0
    assert run.health.failed_count == 0
    assert run.health.last_event_id == event.event_id
    assert applied_requests
    assert getattr(applied_requests[0], "profile_key") == "os.default"
    assert sdk.stream_called is True
    assert sdk.stream_kwargs is not None
    assert sdk.stream_kwargs["subscriber_id"] == "experience.transition.test"
    assert sdk.stream_kwargs["event_type_filters"] == ("identity.admitted",)
    assert sdk.stream_kwargs["include_replay"] is False


@pytest.mark.asyncio
async def test_supervisor_completes_without_subscription_when_no_transitions() -> None:
    sdk = _FakeReactivitySdk(events=())

    async def _load_specs() -> ExperienceReactivityViewTransitionSpecResolution:
        return ExperienceReactivityViewTransitionSpecResolution(
            experience_name="aware_control_identity",
            profile_key="os.default",
            catalog_revision="catalog-rev",
            transitions=(),
        )

    run = await run_experience_reactivity_transition_supervisor(
        sdk=sdk,
        host_context=object(),
        load_specs=_load_specs,
        config=ExperienceReactivityTransitionSupervisorConfig(
            experience_name="aware_control_identity",
            profile_key="os.default",
        ),
    )

    assert [item.kind for item in run.events] == ["started", "completed"]
    assert run.health.status == "completed"
    assert run.health.transition_count == 0
    assert run.health.dispatch_count == 0
    assert "No Experience Reactivity view transitions" in (run.health.info or "")
    assert sdk.stream_called is False


@pytest.mark.asyncio
async def test_supervisor_reports_spec_loader_failure() -> None:
    sdk = _FakeReactivitySdk(events=())

    async def _load_specs() -> ExperienceReactivityViewTransitionSpecResolution:
        raise RuntimeError("missing committed transition truth")

    run = await run_experience_reactivity_transition_supervisor(
        sdk=sdk,
        host_context=object(),
        load_specs=_load_specs,
        config=ExperienceReactivityTransitionSupervisorConfig(
            experience_name="aware_control_identity",
            profile_key="os.default",
        ),
    )

    assert [item.kind for item in run.events] == ["failed"]
    assert run.health.status == "failed"
    assert run.health.last_error == "missing committed transition truth"
    assert sdk.stream_called is False
