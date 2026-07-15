from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from aware_experience.reactivity_transition_dispatcher import (
    ExperienceReactivityViewTransition,
)
from aware_experience.section_graph_binding.catalog import (
    ExperienceSectionGraphBindingCatalog,
    ExperienceSectionGraphBindingCatalogEntry,
    resolve_section_graph_binding_catalog,
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
from aware_experience_ontology.projection.projection_experience_section_graph_binding import (
    ProjectionExperienceSectionGraphBinding,
)
from aware_experience_ontology.projection.projection_experience_view import (
    ProjectionExperienceView,
)
from aware_reactivity_ontology.event.event_config import EventConfig


class _SessionLike(Protocol):
    def imap_all_objects(self) -> Iterable[object]: ...


@dataclass(frozen=True, slots=True)
class ExperienceReactivityViewTransitionSpecResolution:
    experience_name: str
    profile_key: str | None
    catalog_revision: str
    transitions: tuple[ExperienceReactivityViewTransition, ...]


@dataclass(frozen=True, slots=True)
class _ExperienceObjects:
    experiences: tuple[ProjectionExperience, ...]
    experiences_by_id: dict[UUID, ProjectionExperience]
    profiles_by_id: dict[UUID, EnvironmentExperienceProfile]
    profile_configs_by_id: dict[UUID, EnvironmentExperienceProfileConfig]
    events_by_id: dict[UUID, EnvironmentExperienceEvent]
    event_configs_by_id: dict[UUID, EventConfig]
    views_by_id: dict[UUID, ProjectionExperienceView]
    bindings_by_id: dict[UUID, ProjectionExperienceSectionGraphBinding]
    transitions_by_id: dict[UUID, EnvironmentExperienceViewEventTransition]


def resolve_reactivity_view_transition_specs(
    *,
    session: _SessionLike,
    experience_name: str,
    profile_key: str | None = None,
) -> ExperienceReactivityViewTransitionSpecResolution:
    catalog = resolve_section_graph_binding_catalog(
        session=session,
        experience_name=experience_name,
    )
    objects = _collect_experience_objects(session=session)
    experience = _require_projection_experience(
        objects=objects,
        experience_name=catalog.experience_name,
    )
    if experience.id is None:
        raise ValueError("ProjectionExperience.id is required")

    profiles = _matching_profiles(objects=objects, profile_key=profile_key)
    profile_by_config_id = {profile.profile_config_id: profile for profile in profiles}
    profile_config_ids = frozenset(profile_by_config_id)
    binding_entries_by_id = _binding_entries_by_id(
        catalog=catalog,
        objects=objects,
        experience_id=experience.id,
    )

    resolved: list[ExperienceReactivityViewTransition] = []
    for transition in sorted(
        objects.transitions_by_id.values(),
        key=lambda item: (
            str(item.environment_experience_profile_config_id),
            item.transition_key.strip().casefold(),
            str(item.id),
        ),
    ):
        if (
            transition.environment_experience_profile_config_id
            not in profile_config_ids
        ):
            continue
        profile = profile_by_config_id.get(
            transition.environment_experience_profile_config_id
        )
        if profile is None:
            raise ValueError(
                "EnvironmentExperienceViewEventTransition references missing "
                + "applied profile for profile config: "
                + f"transition_key={transition.transition_key!r} "
                + "profile_config_id="
                + f"{transition.environment_experience_profile_config_id}"
            )
        source_view, source_experience = _require_source_view(
            transition=transition,
            objects=objects,
        )
        event_type = _require_event_type(transition=transition, objects=objects)
        target_entry = binding_entries_by_id.get(
            transition.target_section_graph_binding_id
        )
        if target_entry is None:
            raise ValueError(
                "EnvironmentExperienceViewEventTransition target binding does not "
                "belong to the selected ProjectionExperience: "
                + f"transition_key={transition.transition_key!r} "
                + f"target_section_graph_binding_id={transition.target_section_graph_binding_id}"
            )
        resolved.append(
            ExperienceReactivityViewTransition(
                experience_name=catalog.experience_name,
                transition_key=_required_text(
                    transition.transition_key,
                    label="transition.transition_key",
                ),
                profile_key=_required_text(
                    _profile_key(profile=profile, objects=objects),
                    label="EnvironmentExperienceProfileConfig.key",
                ),
                source_view_ref=f"{source_experience.name}.{source_view.name}",
                event_type=event_type,
                target_view_ref=target_entry.descriptor.view_ref,
                target_binding_key=target_entry.descriptor.binding_key,
                target_section_key=target_entry.descriptor.section_key,
                target_graph_identity_ref=target_entry.descriptor.graph_identity_ref,
                rationale=_optional_text(transition.rationale),
                focus_scope_title=_optional_text(transition.name),
            )
        )

    return ExperienceReactivityViewTransitionSpecResolution(
        experience_name=catalog.experience_name,
        profile_key=_optional_text(profile_key),
        catalog_revision=catalog.catalog_revision,
        transitions=tuple(resolved),
    )


def _collect_experience_objects(*, session: _SessionLike) -> _ExperienceObjects:
    experiences: list[ProjectionExperience] = []
    experiences_by_id: dict[UUID, ProjectionExperience] = {}
    profiles_by_id: dict[UUID, EnvironmentExperienceProfile] = {}
    profile_configs_by_id: dict[UUID, EnvironmentExperienceProfileConfig] = {}
    events_by_id: dict[UUID, EnvironmentExperienceEvent] = {}
    event_configs_by_id: dict[UUID, EventConfig] = {}
    views_by_id: dict[UUID, ProjectionExperienceView] = {}
    bindings_by_id: dict[UUID, ProjectionExperienceSectionGraphBinding] = {}
    transitions_by_id: dict[UUID, EnvironmentExperienceViewEventTransition] = {}

    for obj in session.imap_all_objects():
        if isinstance(obj, ProjectionExperience) and obj.id is not None:
            experiences.append(obj)
            experiences_by_id[obj.id] = obj
        elif isinstance(obj, EnvironmentExperienceProfileConfig) and obj.id is not None:
            profile_configs_by_id[obj.id] = obj
        elif isinstance(obj, EnvironmentExperienceProfile) and obj.id is not None:
            profiles_by_id[obj.id] = obj
        elif isinstance(obj, EnvironmentExperienceEvent) and obj.id is not None:
            events_by_id[obj.id] = obj
        elif isinstance(obj, EventConfig) and obj.id is not None:
            event_configs_by_id[obj.id] = obj
        elif isinstance(obj, ProjectionExperienceView) and obj.id is not None:
            views_by_id[obj.id] = obj
        elif (
            isinstance(obj, ProjectionExperienceSectionGraphBinding)
            and obj.id is not None
        ):
            bindings_by_id[obj.id] = obj
        elif (
            isinstance(obj, EnvironmentExperienceViewEventTransition)
            and obj.id is not None
        ):
            transitions_by_id[obj.id] = obj

    return _ExperienceObjects(
        experiences=tuple(experiences),
        experiences_by_id=experiences_by_id,
        profiles_by_id=profiles_by_id,
        profile_configs_by_id=profile_configs_by_id,
        events_by_id=events_by_id,
        event_configs_by_id=event_configs_by_id,
        views_by_id=views_by_id,
        bindings_by_id=bindings_by_id,
        transitions_by_id=transitions_by_id,
    )


def _require_projection_experience(
    *,
    objects: _ExperienceObjects,
    experience_name: str,
) -> ProjectionExperience:
    normalized = _required_text(experience_name, label="experience_name").casefold()
    matches = [
        experience
        for experience in objects.experiences
        if _required_text(experience.name, label="ProjectionExperience.name").casefold()
        == normalized
    ]
    if not matches:
        raise ValueError(
            "Unknown ProjectionExperience for transition spec resolution: "
            + f"experience_name={experience_name!r}"
        )
    if len(matches) != 1:
        raise ValueError(
            "Ambiguous ProjectionExperience for transition spec resolution: "
            + f"experience_name={experience_name!r}"
        )
    return matches[0]


def _matching_profiles(
    *,
    objects: _ExperienceObjects,
    profile_key: str | None,
) -> tuple[EnvironmentExperienceProfile, ...]:
    normalized_profile_key = _optional_text(profile_key)
    profiles = tuple(objects.profiles_by_id.values())
    if normalized_profile_key is None:
        return profiles
    matches = [
        profile
        for profile in profiles
        if _required_text(
            _profile_key(profile=profile, objects=objects),
            label="EnvironmentExperienceProfileConfig.key",
        ).casefold()
        == normalized_profile_key.casefold()
    ]
    if not matches:
        raise ValueError(
            "Unknown EnvironmentExperienceProfile for transition spec resolution: "
            + f"profile_key={normalized_profile_key!r}"
        )
    if len(matches) != 1:
        raise ValueError(
            "Ambiguous EnvironmentExperienceProfile for transition spec resolution: "
            + f"profile_key={normalized_profile_key!r}"
        )
    return tuple(matches)


def _profile_key(
    *,
    profile: EnvironmentExperienceProfile,
    objects: _ExperienceObjects,
) -> str | None:
    profile_config = profile.profile_config
    if profile_config is None:
        profile_config = objects.profile_configs_by_id.get(profile.profile_config_id)
    if profile_config is None:
        raise ValueError(
            "EnvironmentExperienceProfile references missing profile config: "
            + f"profile_id={profile.id} profile_config_id={profile.profile_config_id}"
        )
    return profile_config.key


def _binding_entries_by_id(
    *,
    catalog: ExperienceSectionGraphBindingCatalog,
    objects: _ExperienceObjects,
    experience_id: UUID,
) -> dict[UUID, ExperienceSectionGraphBindingCatalogEntry]:
    entries_by_id: dict[UUID, ExperienceSectionGraphBindingCatalogEntry] = {}
    for binding in objects.bindings_by_id.values():
        if binding.projection_experience_id != experience_id:
            continue
        entry = catalog.entry_for_binding_key(binding_key=binding.binding_key)
        if entry is None:
            raise ValueError(
                "ProjectionExperienceSectionGraphBinding is missing from catalog: "
                + f"binding_key={binding.binding_key!r}"
            )
        binding_id = binding.id
        if binding_id is None:
            raise ValueError("ProjectionExperienceSectionGraphBinding.id is required")
        entries_by_id[binding_id] = entry
    return entries_by_id


def _require_source_view(
    *,
    transition: EnvironmentExperienceViewEventTransition,
    objects: _ExperienceObjects,
) -> tuple[ProjectionExperienceView, ProjectionExperience]:
    source_view = objects.views_by_id.get(transition.source_view_id)
    if source_view is None:
        raise ValueError(
            "EnvironmentExperienceViewEventTransition references missing source view: "
            + f"transition_key={transition.transition_key!r} "
            + f"source_view_id={transition.source_view_id}"
        )
    source_experience = objects.experiences_by_id.get(
        source_view.projection_experience_id
    )
    if source_experience is None:
        raise ValueError(
            "EnvironmentExperienceViewEventTransition source view references "
            "missing ProjectionExperience: "
            + f"transition_key={transition.transition_key!r} "
            + f"projection_experience_id={source_view.projection_experience_id}"
        )
    return source_view, source_experience


def _require_event_type(
    *,
    transition: EnvironmentExperienceViewEventTransition,
    objects: _ExperienceObjects,
) -> str:
    event = objects.events_by_id.get(transition.trigger_event_id)
    if event is None:
        raise ValueError(
            "EnvironmentExperienceViewEventTransition references missing trigger event: "
            + f"transition_key={transition.transition_key!r} "
            + f"trigger_event_id={transition.trigger_event_id}"
        )
    if (
        event.environment_experience_profile_config_id
        != transition.environment_experience_profile_config_id
    ):
        raise ValueError(
            "EnvironmentExperienceViewEventTransition trigger event profile mismatch: "
            + f"transition_key={transition.transition_key!r}"
        )
    event_config = objects.event_configs_by_id.get(event.event_config_id)
    if event_config is None:
        raise ValueError(
            "EnvironmentExperienceEvent references missing EventConfig: "
            + f"event_config_id={event.event_config_id}"
        )
    return _required_text(event_config.name, label="EventConfig.name")


def _required_text(value: object, *, label: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} is required")
    return normalized


def _optional_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


__all__ = [
    "ExperienceReactivityViewTransitionSpecResolution",
    "resolve_reactivity_view_transition_specs",
]
