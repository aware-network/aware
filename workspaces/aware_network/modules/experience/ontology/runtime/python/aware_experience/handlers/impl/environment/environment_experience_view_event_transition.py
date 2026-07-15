from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_view_event_transition import (
    EnvironmentExperienceViewEventTransition,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_environment_experience_view_event_transition_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID,
    source_view_id: UUID,
    trigger_event_id: UUID,
    target_section_graph_binding_id: UUID,
    transition_key: str,
    name: str | None = None,
    rationale: str | None = None,
    idempotency_policy: str | None = None,
) -> EnvironmentExperienceViewEventTransition:
    """
    Construct one deterministic profile-owned ViewEventTransition.

    Notes:
    - Identity is derived from `(environment_experience_profile_config_id, source_view_id,
      trigger_event_id, target_section_graph_binding_id, transition_key)`.
    - `target_section_graph_binding` is the only transition target rail. Attention focus
      activation is resolved later through that binding.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    normalized_transition_key = (transition_key or "").strip()
    if not normalized_transition_key:
        raise RuntimeError(
            "EnvironmentExperienceViewEventTransition.build_via_environment_experience_profile_config "
            "requires non-empty transition_key"
        )

    transition_id = stable_environment_experience_view_event_transition_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=normalized_transition_key,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceViewEventTransition, transition_id)
    if existing is not None:
        if (
            existing.environment_experience_profile_config_id != environment_experience_profile_config_id
            or existing.source_view_id != source_view_id
            or existing.trigger_event_id != trigger_event_id
            or existing.target_section_graph_binding_id != target_section_graph_binding_id
            or existing.transition_key != normalized_transition_key
        ):
            raise RuntimeError(
                "EnvironmentExperienceViewEventTransition.build_via_environment_experience_profile_config "
                + f"payload mismatch for existing transition: transition_id={transition_id}"
            )
        return existing

    return EnvironmentExperienceViewEventTransition(
        id=transition_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        source_view_id=source_view_id,
        trigger_event_id=trigger_event_id,
        target_section_graph_binding_id=target_section_graph_binding_id,
        transition_key=normalized_transition_key,
        name=name,
        rationale=rationale,
        idempotency_policy=idempotency_policy,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
