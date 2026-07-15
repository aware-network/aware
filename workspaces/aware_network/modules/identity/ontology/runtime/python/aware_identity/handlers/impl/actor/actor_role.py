from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.actor.actor_role import ActorRole

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_orm.session.change_collector import current_change_collector
from aware_identity_ontology.stable_ids import stable_actor_role_id

# --- AWARE: USER_IMPORTS END


async def delete(actor_role: ActorRole) -> None:
    """
    Delete this ActorRole assignment edge.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is not None:
        collector.record_delete(actor_role)
    # --- AWARE: LOGIC END delete


async def create_via_actor(actor_id: UUID, role_id: UUID) -> ActorRole:
    """
    Create an ActorRole assignment row.

    Contract (v0):
    - Deterministic id from (actor_id, role_id).
    - Idempotent assignment edge between Actor and Role.
    """

    # --- AWARE: LOGIC START create_via_actor
    actor_role_id = stable_actor_role_id(actor_id=actor_id, role_id=role_id)
    actor_role = ActorRole(id=actor_role_id, actor_id=actor_id, role_id=role_id)
    collector = current_change_collector()
    if collector is not None:
        collector.record_create(actor_role)
    return actor_role
    # --- AWARE: LOGIC END create_via_actor
