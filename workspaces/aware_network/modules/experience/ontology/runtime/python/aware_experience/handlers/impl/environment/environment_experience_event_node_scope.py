from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_event_node_scope import (
    EnvironmentExperienceEventNodeScope,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_environment_experience_event_node_scope_id,
)

# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_event(
    environment_experience_event_id: UUID,
    event_config_condition_config_id: UUID,
    projection_experience_node_identity_id: UUID,
    object_instance_graph_branch_id: UUID | None = None,
    event_config_condition_config_scope_id: UUID | None = None,
) -> EnvironmentExperienceEventNodeScope:
    """
    Create one environment-scoped event trigger node binding.

    Contract:
    - Identity is derived from
      `(environment_experience_event_id, event_config_condition_config_id,
      projection_experience_node_identity_id)`.
    - This row says which declared graph-binding node may trigger the event.
    - Lowering must resolve the node identity through
      ProjectionExperienceNodeClassIdentity and create/use a Reactivity
      EventConfigConditionConfigScope whose ClassInstanceIdentity belongs to
      the same ProjectionExperienceOIGI lane.
    - Action request target mapping remains under ActionExperienceInvocation
      request fields; this object owns trigger scope only.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_event
    return EnvironmentExperienceEventNodeScope(
        id=stable_environment_experience_event_node_scope_id(
            environment_experience_event_id=environment_experience_event_id,
            event_config_condition_config_id=event_config_condition_config_id,
            projection_experience_node_identity_id=projection_experience_node_identity_id,
        ),
        environment_experience_event_id=environment_experience_event_id,
        event_config_condition_config_id=event_config_condition_config_id,
        projection_experience_node_identity_id=projection_experience_node_identity_id,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
        event_config_condition_config_scope_id=event_config_condition_config_scope_id,
    )
    # --- AWARE: LOGIC END build_via_environment_experience_event
