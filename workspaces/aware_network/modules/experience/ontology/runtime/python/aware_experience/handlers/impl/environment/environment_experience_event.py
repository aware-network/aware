from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_event import EnvironmentExperienceEvent
from aware_experience_ontology.environment.environment_experience_event_action import EnvironmentExperienceEventAction
from aware_experience_ontology.environment.environment_experience_event_node_scope import (
    EnvironmentExperienceEventNodeScope,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_environment_experience_event_action_id,
    stable_environment_experience_event_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def add_action_experience(
    environment_experience_event: EnvironmentExperienceEvent, action_experience_id: UUID
) -> EnvironmentExperienceEventAction:
    """
    Attach one environment-scoped action dispatch mapping to this event.
    """

    # --- AWARE: LOGIC START add_action_experience
    event_id = environment_experience_event.id
    if event_id is None:
        raise RuntimeError("EnvironmentExperienceEvent.add_action_experience requires EnvironmentExperienceEvent.id")
    action_edge_id = stable_environment_experience_event_action_id(
        environment_experience_event_id=event_id,
        action_experience_id=action_experience_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceEventAction, action_edge_id)
    if existing is not None:
        if (
            existing.environment_experience_event_id != event_id
            or existing.action_experience_id != action_experience_id
        ):
            raise RuntimeError(
                "EnvironmentExperienceEvent.add_action_experience payload mismatch "
                + f"for existing action edge: event_action_id={action_edge_id}"
            )
        return existing
    created = EnvironmentExperienceEventAction(
        id=action_edge_id,
        environment_experience_event_id=event_id,
        action_experience_id=action_experience_id,
    )
    environment_experience_event.actions.append(created)
    return created
    # --- AWARE: LOGIC END add_action_experience


async def add_node_scope(
    environment_experience_event: EnvironmentExperienceEvent,
    event_config_condition_config_id: UUID,
    projection_experience_node_identity_id: UUID,
    object_instance_graph_branch_id: UUID | None = None,
    event_config_condition_config_scope_id: UUID | None = None,
) -> EnvironmentExperienceEventNodeScope:
    """
    Attach one declared trigger-node scope to this event binding.

    Contract:
    - The node identity must belong to this environment profile's own
      projection experience binding.
    - This is authoring/lowering policy only; Reactivity receives only the
      lowered Meta scope.
    """

    # --- AWARE: LOGIC START add_node_scope
    event_id = environment_experience_event.id
    if event_id is None:
        raise RuntimeError("EnvironmentExperienceEvent.add_node_scope requires " "EnvironmentExperienceEvent.id")
    created = await EnvironmentExperienceEventNodeScope.build_via_environment_experience_event(
        environment_experience_event_id=event_id,
        event_config_condition_config_id=event_config_condition_config_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
    )
    for existing in environment_experience_event.node_scopes:
        if existing.id == created.id:
            return existing

    environment_experience_event.node_scopes.append(created)
    return created
    # --- AWARE: LOGIC END add_node_scope


async def build_via_environment_experience_profile_config(
    environment_experience_profile_config_id: UUID, event_config_id: UUID
) -> EnvironmentExperienceEvent:
    """
    Construct the canonical EnvironmentExperienceEvent for an environment territory.

    Notes:
    - Identity is derived from `(environment_experience_profile_config_id, event_config_id)`.
    - Constructor does not mutate EnvironmentExperienceProfileConfig directly.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_profile_config
    event_id = stable_environment_experience_event_id(
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        event_config_id=event_config_id,
    )
    session = current_handler_session()
    existing = session.imap_get(EnvironmentExperienceEvent, event_id)
    if existing is not None:
        if (
            existing.environment_experience_profile_config_id != environment_experience_profile_config_id
            or existing.event_config_id != event_config_id
        ):
            raise RuntimeError(
                "EnvironmentExperienceEvent.build_via_environment_experience_profile_config "
                + f"payload mismatch for existing event: event_id={event_id}"
            )
        return existing
    return EnvironmentExperienceEvent(
        id=event_id,
        environment_experience_profile_config_id=environment_experience_profile_config_id,
        event_config_id=event_config_id,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_profile_config
