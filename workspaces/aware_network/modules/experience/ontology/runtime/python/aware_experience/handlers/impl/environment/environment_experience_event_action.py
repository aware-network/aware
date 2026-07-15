from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.environment.environment_experience_event_action import EnvironmentExperienceEventAction

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_environment_experience_event(
    environment_experience_event_id: UUID, action_experience_id: UUID
) -> EnvironmentExperienceEventAction:
    """
    Create a deterministic EnvironmentExperienceEventAction association edge.

    Notes:
    - Identity is derived from `(environment_experience_event_id, action_experience_id)`.
    """

    # --- AWARE: LOGIC START build_via_environment_experience_event
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_environment_experience_event
