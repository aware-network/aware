from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5
from typing import Protocol

import pytest

from aware_experience.handlers.impl.environment import (
    environment_experience_profile_config as profile_config_handler,
)
from aware_experience.handlers.impl.environment import (
    environment_experience_event as event_handler,
)
from aware_experience.handlers.impl.environment import (
    environment_experience_view_event_transition as transition_handler,
)
from aware_experience.stable_ids import (
    stable_environment_experience_event_id,
    stable_environment_experience_view_event_transition_id,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_experience_view_event_transition import (
    EnvironmentExperienceViewEventTransition,
)


class _HasId(Protocol):
    id: UUID | None


class _Session:
    def __init__(self, existing: _HasId | None = None) -> None:
        self._existing = existing

    def imap_get(self, _model: type[object], object_id: UUID) -> object | None:
        if self._existing is None or self._existing.id != object_id:
            return None
        return self._existing


def _ids() -> tuple[UUID, UUID, UUID, UUID, str, UUID]:
    ns = uuid5(NAMESPACE_URL, "aware://tests/experience/view-event-transition/v1")
    profile_config_id = uuid5(ns, "profile-config")
    source_view_id = uuid5(ns, "identity-admission-view")
    trigger_event_id = uuid5(ns, "identity-admitted-event")
    target_section_graph_binding_id = uuid5(ns, "actor-home-section-graph-binding")
    transition_key = "identity_admission.actor_home"
    transition_id = stable_environment_experience_view_event_transition_id(
        environment_experience_profile_config_id=profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=transition_key,
    )
    return (
        profile_config_id,
        source_view_id,
        trigger_event_id,
        target_section_graph_binding_id,
        transition_key,
        transition_id,
    )


@pytest.mark.asyncio
async def test_view_event_transition_builds_deterministic_section_graph_binding_target(
    monkeypatch,
) -> None:
    (
        profile_config_id,
        source_view_id,
        trigger_event_id,
        target_section_graph_binding_id,
        transition_key,
        transition_id,
    ) = _ids()
    monkeypatch.setattr(
        transition_handler, "current_handler_session", lambda: _Session()
    )

    created = await transition_handler.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=transition_key,
        name="Identity admitted to actor home",
        rationale="Focus actor home after admission completes.",
        idempotency_policy="event_instance_once",
    )

    assert created.id == transition_id
    assert created.environment_experience_profile_config_id == profile_config_id
    assert created.source_view_id == source_view_id
    assert created.trigger_event_id == trigger_event_id
    assert created.target_section_graph_binding_id == target_section_graph_binding_id
    assert created.transition_key == transition_key
    assert "attention" not in EnvironmentExperienceViewEventTransition.model_fields


@pytest.mark.asyncio
async def test_profile_add_view_event_transition_attaches_once(monkeypatch) -> None:
    (
        profile_config_id,
        source_view_id,
        trigger_event_id,
        target_section_graph_binding_id,
        transition_key,
        transition_id,
    ) = _ids()
    created = EnvironmentExperienceViewEventTransition(
        id=transition_id,
        environment_experience_profile_config_id=profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=transition_key,
        name="Identity admitted to actor home",
        rationale="Focus actor home after admission completes.",
        idempotency_policy="event_instance_once",
    )

    async def _build_transition(
        **_kwargs: object,
    ) -> EnvironmentExperienceViewEventTransition:
        return created

    monkeypatch.setattr(
        profile_config_handler.EnvironmentExperienceViewEventTransition,
        "build_via_environment_experience_profile_config",
        staticmethod(_build_transition),
    )
    profile_config = EnvironmentExperienceProfileConfig(
        id=profile_config_id,
        environment_experience_id=uuid5(profile_config_id, "environment-experience"),
        environment_profile_config_id=uuid5(
            profile_config_id,
            "environment-profile-config",
        ),
        key="desktop",
    )

    first = await profile_config_handler.add_view_event_transition(
        environment_experience_profile_config=profile_config,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=transition_key,
    )
    second = await profile_config_handler.add_view_event_transition(
        environment_experience_profile_config=profile_config,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=transition_key,
    )

    assert first is created
    assert second is created
    assert profile_config.view_event_transitions == [created]


@pytest.mark.asyncio
async def test_profile_add_event_attaches_once(monkeypatch) -> None:
    profile_id = uuid5(NAMESPACE_URL, "aware://tests/experience/profile-event")
    event_config_id = uuid5(profile_id, "event-config")
    event_id = stable_environment_experience_event_id(
        environment_experience_profile_config_id=profile_id,
        event_config_id=event_config_id,
    )
    created = EnvironmentExperienceEvent(
        id=event_id,
        environment_experience_profile_config_id=profile_id,
        event_config_id=event_config_id,
    )

    async def _build_event(**_kwargs: object) -> EnvironmentExperienceEvent:
        return created

    monkeypatch.setattr(
        profile_config_handler.EnvironmentExperienceEvent,
        "build_via_environment_experience_profile_config",
        staticmethod(_build_event),
    )
    profile = EnvironmentExperienceProfileConfig(
        id=profile_id,
        environment_experience_id=uuid5(profile_id, "environment-experience"),
        environment_profile_config_id=uuid5(
            profile_id,
            "environment-profile-config",
        ),
        key="desktop",
    )

    first = await profile_config_handler.add_event(
        environment_experience_profile_config=profile,
        event_config_id=event_config_id,
    )
    second = await profile_config_handler.add_event(
        environment_experience_profile_config=profile,
        event_config_id=event_config_id,
    )

    assert first is created
    assert second is created
    assert profile.events == [created]


@pytest.mark.asyncio
async def test_event_builds_deterministic_profile_binding(monkeypatch) -> None:
    profile_id = uuid5(NAMESPACE_URL, "aware://tests/experience/event-build")
    event_config_id = uuid5(profile_id, "event-config")
    expected_id = stable_environment_experience_event_id(
        environment_experience_profile_config_id=profile_id,
        event_config_id=event_config_id,
    )
    monkeypatch.setattr(event_handler, "current_handler_session", lambda: _Session())

    created = await event_handler.build_via_environment_experience_profile_config(
        environment_experience_profile_config_id=profile_id,
        event_config_id=event_config_id,
    )

    assert created.id == expected_id
    assert created.environment_experience_profile_config_id == profile_id
    assert created.event_config_id == event_config_id
