from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.role.role_class_instance import RoleClassInstance

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_orm.session.change_collector import current_change_collector
from aware_identity_ontology.stable_ids import stable_role_class_instance_id

# --- AWARE: USER_IMPORTS END


async def delete(role_class_instance: RoleClassInstance) -> None:
    """
    Delete this concrete class-instance grant membership.
    """

    # --- AWARE: LOGIC START delete
    collector = current_change_collector()
    if collector is not None:
        collector.record_delete(role_class_instance)
    # --- AWARE: LOGIC END delete


async def create_via_role(
    role_id: UUID, class_instance_identity_id: UUID, role_config_class_config_id: UUID
) -> RoleClassInstance:
    """
    Create a concrete class-instance grant membership under one Role.

    Contract (v0):
    - Deterministic id from (`role_id`, `class_instance_identity_id`, `role_config_class_config_id`).
    - `role_config_class_config_id` points to the inherited class-kind capability policy.
    - One Role may include many concrete ClassInstanceIdentity grants.
    """

    # --- AWARE: LOGIC START create_via_role
    role_class_instance_id = stable_role_class_instance_id(
        role_id=role_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_class_config_id=role_config_class_config_id,
    )

    role_class_instance = RoleClassInstance(
        id=role_class_instance_id,
        role_id=role_id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_class_config_id=role_config_class_config_id,
    )
    collector = current_change_collector()
    if collector is not None:
        collector.record_create(role_class_instance)
    return role_class_instance
    # --- AWARE: LOGIC END create_via_role
