from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Identity Ontology
from aware_identity_ontology.role.role import Role
from aware_identity_ontology.role.role_class_instance import RoleClassInstance

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_orm.session.change_collector import current_change_collector
from aware_identity_ontology.stable_ids import stable_role_id

# --- AWARE: USER_IMPORTS END


async def create(
    role_config_id: UUID,
    object_instance_graph_identity_id: UUID,
    object_instance_graph_branch_key: str = "all",
    object_instance_graph_branch_id: UUID | None = None,
) -> Role:
    """
    Create a canonical Role binding scoped to graph identity.

    Contract (v0):
    - Deterministic id from (role_config_id, object_instance_graph_identity_id,
    object_instance_graph_branch_key).
    - `object_instance_graph_branch_id` is an optional reference binding and does not participate in
    identity.
    - Role scope is the lane envelope only (OIGI required, OIGB optional).
    - Concrete object grants are modeled under `RoleClassInstance`.
    """

    # --- AWARE: LOGIC START create
    branch_key = str(object_instance_graph_branch_key).strip().casefold() or "all"
    role_id = stable_role_id(
        role_config_id=role_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
    )
    role = Role(
        id=role_id,
        role_config_id=role_config_id,
        object_instance_graph_identity_id=object_instance_graph_identity_id,
        object_instance_graph_branch_key=branch_key,
        object_instance_graph_branch_id=object_instance_graph_branch_id,
    )
    collector = current_change_collector()
    if collector is not None:
        collector.record_create(role)
    return role
    # --- AWARE: LOGIC END create


async def add_class_instance(
    role: Role, class_instance_identity_id: UUID, role_config_class_config_id: UUID
) -> RoleClassInstance:
    """
    Add one concrete ClassInstanceIdentity grant under this Role.

    Contract:
    - Role remains the lane envelope; `RoleClassInstance` carries object-worldline membership.
    - Capabilities are inherited from the linked `RoleConfigClassConfig`.
    - Idempotent for repeated grants of the same class-instance under the same role.
    """

    # --- AWARE: LOGIC START add_class_instance
    if role.id is None:
        raise ValueError("Role.add_class_instance requires a bound role.id")

    for existing in role.role_class_instances:
        if existing.class_instance_identity_id != class_instance_identity_id:
            continue
        if existing.role_config_class_config_id != role_config_class_config_id:
            raise ValueError(
                "Role.add_class_instance refuses ambiguous policy bindings for the same "
                + "class_instance_identity under one role: "
                + f"role_id={role.id} class_instance_identity_id={class_instance_identity_id} "
                + f"existing_role_config_class_config_id={existing.role_config_class_config_id} "
                + f"requested_role_config_class_config_id={role_config_class_config_id}"
            )
        return existing

    created_grant = await RoleClassInstance.create_via_role(
        role_id=role.id,
        class_instance_identity_id=class_instance_identity_id,
        role_config_class_config_id=role_config_class_config_id,
    )
    role.role_class_instances.append(created_grant)
    return created_grant
    # --- AWARE: LOGIC END add_class_instance


async def remove_class_instance(
    role: Role, class_instance_identity_id: UUID, role_config_class_config_id: UUID
) -> None:
    """
    Remove one concrete ClassInstanceIdentity grant under this Role.

    Contract:
    - This is only honest when the caller has already proven that the enclosing Role
      envelope should no longer expose the target class-instance grant.
    - Missing target grants are a no-op.
    - Ambiguous policy bindings for one class-instance fail closed.
    """

    # --- AWARE: LOGIC START remove_class_instance
    if role.id is None:
        raise ValueError("Role.remove_class_instance requires a bound role.id")

    target: RoleClassInstance | None = None
    for existing in list(role.role_class_instances):
        if existing.class_instance_identity_id != class_instance_identity_id:
            continue
        if existing.role_config_class_config_id != role_config_class_config_id:
            raise ValueError(
                "Role.remove_class_instance refuses ambiguous policy bindings for the same "
                + "class_instance_identity under one role: "
                + f"role_id={role.id} class_instance_identity_id={class_instance_identity_id} "
                + f"existing_role_config_class_config_id={existing.role_config_class_config_id} "
                + f"requested_role_config_class_config_id={role_config_class_config_id}"
            )
        target = existing
        break

    if target is None:
        return

    await target.delete()
    role.role_class_instances[:] = [existing for existing in role.role_class_instances if existing.id != target.id]
    # --- AWARE: LOGIC END remove_class_instance


async def delete(role: Role) -> None:
    """
    Delete an empty Role envelope after all actor-role edges and class-instance grants
    have already been removed.
    """

    # --- AWARE: LOGIC START delete
    if role.role_class_instances:
        raise ValueError("Role.delete requires role_class_instances to be empty before deletion")

    collector = current_change_collector()
    if collector is not None:
        collector.record_delete(role)
    # --- AWARE: LOGIC END delete
