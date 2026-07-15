from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.human.human import Human

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.stable_ids import stable_human_id
from aware_identity_ontology.actor.actor import Actor

# --- AWARE: USER_IMPORTS END


async def create_human(actor_id: UUID) -> Human:
    """
    Create a human bound to an actor.

    v0: used by `Identity.signup` to build the minimal Identity→Human graph
    while preserving the hard mutation boundary (mutate-self-only).
    """

    # --- AWARE: LOGIC START create_human
    actor = Actor.by_id_cached(actor_id)
    if actor is None:
        raise ValueError("Actor not available in write context for Human.create_human " f"(actor_id={actor_id})")

    human_id = stable_human_id(actor_id=actor_id)
    return Human(id=human_id, actor=actor, actor_id=actor_id)
    # --- AWARE: LOGIC END create_human


async def get_display_name(human: Human, p_human_id: UUID) -> str:
    """
    Gets the display name for a human.
    Parameters: p_human_id: The UUID of the human.
    Returns: The human''s display name from their profile
    """

    # --- AWARE: LOGIC START get_display_name
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END get_display_name
