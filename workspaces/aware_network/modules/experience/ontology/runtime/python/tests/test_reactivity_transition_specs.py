from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

import pytest

from aware_api_ontology.api.api_view import ApiView
from aware_experience.reactivity_transition_specs import (
    resolve_reactivity_view_transition_specs,
)
from aware_experience_ontology.environment.environment_experience_event import (
    EnvironmentExperienceEvent,
)
from aware_experience_ontology.environment.environment_experience_profile import (
    EnvironmentExperienceProfile,
)
from aware_experience_ontology.environment.environment_experience_profile_config import (
    EnvironmentExperienceProfileConfig,
)
from aware_experience_ontology.environment.environment_experience_view_event_transition import (
    EnvironmentExperienceViewEventTransition,
)
from aware_experience_ontology.projection.projection_experience import (
    ProjectionExperience,
)
from aware_experience_ontology.projection.projection_experience_graph_identity import (
    ProjectionExperienceGraphIdentity,
)
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_reactivity_ontology.event.event_config import EventConfig


class _Session:
    def __init__(self, *objects: object) -> None:
        self._objects = objects

    def imap_all_objects(self) -> Iterable[object]:
        return self._objects


def _fixture_objects() -> dict[str, object]:
    experience_id = uuid4()
    source_view_id = uuid4()
    target_view_id = uuid4()
    source_api_view_id = uuid4()
    target_api_view_id = uuid4()
    target_observable_id = uuid4()
    graph_identity_id = uuid4()
    target_binding_id = uuid4()
    profile_id = uuid4()
    profile_config_id = uuid4()
    event_config_id = uuid4()
    trigger_event_id = uuid4()
    transition_id = uuid4()

    return {
        "experience": ProjectionExperience(
            id=experience_id,
            object_projection_graph_identity_id=uuid4(),
            name="aware_control_identity",
        ),
        "source_api_view": ApiView(
            id=source_api_view_id,
            api_id=uuid4(),
            object_projection_graph_observable_id=uuid4(),
            state_model_id=uuid4(),
            name="identity.admission.v1",
            view_ref="aware_control_identity.identity.admission.v1",
        ),
        "target_api_view": ApiView(
            id=target_api_view_id,
            api_id=uuid4(),
            object_projection_graph_observable_id=target_observable_id,
            state_model_id=uuid4(),
            name="actor.home.v1",
            view_ref="aware_control_identity.actor.home.v1",
        ),
        "source_view": ProjectionExperienceView(
            id=source_view_id,
            projection_experience_id=experience_id,
            api_view_id=source_api_view_id,
            name="identity.admission.v1",
        ),
        "target_view": ProjectionExperienceView(
            id=target_view_id,
            projection_experience_id=experience_id,
            api_view_id=target_api_view_id,
            name="actor.home.v1",
        ),
        "graph_identity": ProjectionExperienceGraphIdentity(
            id=graph_identity_id,
            projection_experience_graph_id=uuid4(),
            projection_experience_node_identity_id=uuid4(),
            key="identity.actor",
        ),
        "target_binding": ProjectionExperienceSectionGraphBinding(
            id=target_binding_id,
            projection_experience_id=experience_id,
            layout_config_section_config_id=uuid4(),
            projection_experience_view_id=target_view_id,
            projection_experience_graph_identity_id=graph_identity_id,
            binding_key="actor.home",
            section_key="actor_home",
        ),
        "profile": EnvironmentExperienceProfile(
            id=profile_id,
            environment_experience_id=uuid4(),
            profile_config_id=profile_config_id,
            environment_profile_id=uuid4(),
            title="Default OS",
        ),
        "profile_config": EnvironmentExperienceProfileConfig(
            id=profile_config_id,
            environment_experience_id=uuid4(),
            environment_profile_config_id=uuid4(),
            key="os.default",
        ),
        "event_config": EventConfig(
            id=event_config_id,
            name="identity.admitted",
            description="Identity admission completed.",
        ),
        "trigger_event": EnvironmentExperienceEvent(
            id=trigger_event_id,
            environment_experience_profile_config_id=profile_config_id,
            event_config_id=event_config_id,
        ),
        "transition": EnvironmentExperienceViewEventTransition(
            id=transition_id,
            environment_experience_profile_config_id=profile_config_id,
            source_view_id=source_view_id,
            trigger_event_id=trigger_event_id,
            target_section_graph_binding_id=target_binding_id,
            transition_key="identity_admission.actor_home",
            name="Actor home",
            rationale="Focus actor home after identity admission.",
        ),
    }


def test_resolve_reactivity_view_transition_specs_from_committed_objects() -> None:
    objects = _fixture_objects()
    session = _Session(*objects.values())

    resolution = resolve_reactivity_view_transition_specs(
        session=session,
        experience_name="aware_control_identity",
        profile_key="os.default",
    )

    assert resolution.experience_name == "aware_control_identity"
    assert resolution.profile_key == "os.default"
    assert len(resolution.catalog_revision) == 64
    assert len(resolution.transitions) == 1
    transition = resolution.transitions[0]
    assert transition.experience_name == "aware_control_identity"
    assert transition.profile_key == "os.default"
    assert transition.transition_key == "identity_admission.actor_home"
    assert transition.source_view_ref == (
        "aware_control_identity.identity.admission.v1"
    )
    assert transition.event_type == "identity.admitted"
    assert transition.action_type is None
    assert transition.target_view_ref == "aware_control_identity.actor.home.v1"
    assert transition.target_binding_key == "actor.home"
    assert transition.target_section_key == "actor_home"
    assert transition.target_graph_identity_ref == "identity.actor"
    assert transition.rationale == "Focus actor home after identity admission."
    assert transition.focus_scope_title == "Actor home"


def test_resolve_reactivity_view_transition_specs_allows_cross_experience_source_view() -> (
    None
):
    objects = _fixture_objects()
    source_experience_id = uuid4()
    source_experience = ProjectionExperience(
        id=source_experience_id,
        object_projection_graph_identity_id=uuid4(),
        name="aware_control_identity",
    )
    target_experience = objects["experience"]
    assert isinstance(target_experience, ProjectionExperience)
    target_experience.name = "aware_actor_home"
    source_view = objects["source_view"]
    assert isinstance(source_view, ProjectionExperienceView)
    source_view.projection_experience_id = source_experience_id
    session = _Session(*objects.values(), source_experience)

    resolution = resolve_reactivity_view_transition_specs(
        session=session,
        experience_name="aware_actor_home",
        profile_key="os.default",
    )

    assert len(resolution.transitions) == 1
    transition = resolution.transitions[0]
    assert transition.experience_name == "aware_actor_home"
    assert transition.source_view_ref == (
        "aware_control_identity.identity.admission.v1"
    )
    assert transition.target_view_ref == "aware_actor_home.actor.home.v1"


def test_resolve_reactivity_view_transition_specs_filters_profile_key() -> None:
    objects = _fixture_objects()
    other_profile_config_id = uuid4()
    other_profile = EnvironmentExperienceProfile(
        id=uuid4(),
        environment_experience_id=uuid4(),
        profile_config_id=other_profile_config_id,
        environment_profile_id=uuid4(),
    )
    other_profile_config = EnvironmentExperienceProfileConfig(
        id=other_profile_config_id,
        environment_experience_id=uuid4(),
        environment_profile_config_id=uuid4(),
        key="mobile.default",
    )
    session = _Session(*objects.values(), other_profile, other_profile_config)

    resolution = resolve_reactivity_view_transition_specs(
        session=session,
        experience_name="aware_control_identity",
        profile_key="mobile.default",
    )

    assert resolution.profile_key == "mobile.default"
    assert resolution.transitions == ()


def test_resolve_reactivity_view_transition_specs_fails_on_missing_event_config() -> (
    None
):
    objects = _fixture_objects()
    without_event_config = [
        value for key, value in objects.items() if key != "event_config"
    ]
    session = _Session(*without_event_config)

    with pytest.raises(ValueError, match="missing EventConfig"):
        resolve_reactivity_view_transition_specs(
            session=session,
            experience_name="aware_control_identity",
            profile_key="os.default",
        )
