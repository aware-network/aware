from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Service Ontology
from aware_service_ontology.service.service_operation_config_role_requirement import (
    ServiceOperationConfigRoleRequirement,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_identity_ontology.role.role_config import RoleConfig
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import stable_service_operation_config_role_requirement_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_operation_config(
    service_operation_config_id: UUID,
    role_config_id: UUID,
    access_scope: str = "operation",
    scope_kind: str = "operation",
    scope_ref: str = "default",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    description: str | None = None,
) -> ServiceOperationConfigRoleRequirement:
    """
    Creates one ActorRole evidence requirement for a ServiceOperationConfig.

    Contract:
    - Role policy remains owned by Identity RoleConfig.
    - ServiceOperationConfig only declares the evidence required before operation/view fulfillment.
    - Runtime gate must resolve this through Identity and fail closed when missing.
    """

    # --- AWARE: LOGIC START build_via_service_operation_config
    access_scope_norm = (access_scope or "").strip() or "operation"
    scope_kind_norm = (scope_kind or "").strip() or "operation"
    scope_ref_norm = (scope_ref or "").strip() or "default"
    requirement_id = stable_service_operation_config_role_requirement_id(
        service_operation_config_id=service_operation_config_id,
        role_config_id=role_config_id,
        access_scope=access_scope_norm,
        scope_kind=scope_kind_norm,
        scope_ref=scope_ref_norm,
    )
    session = current_handler_session()
    _ = session.imap_get(RoleConfig, role_config_id)

    existing = session.imap_get(ServiceOperationConfigRoleRequirement, requirement_id)
    if existing is not None:
        if (
            existing.service_operation_config_id != service_operation_config_id
            or existing.role_config_id != role_config_id
            or (existing.access_scope or "").strip() != access_scope_norm
            or (existing.scope_kind or "").strip() != scope_kind_norm
            or (existing.scope_ref or "").strip() != scope_ref_norm
        ):
            raise RuntimeError(
                "ServiceOperationConfigRoleRequirement payload mismatch for existing requirement: "
                + f"requirement_id={requirement_id}"
            )
        existing.class_instance_identity_required = bool(class_instance_identity_required)
        existing.role_assignment_binding_required = bool(role_assignment_binding_required)
        existing.description = description
        return existing

    return ServiceOperationConfigRoleRequirement(
        id=requirement_id,
        service_operation_config_id=service_operation_config_id,
        role_config_id=role_config_id,
        access_scope=access_scope_norm,
        scope_kind=scope_kind_norm,
        scope_ref=scope_ref_norm,
        class_instance_identity_required=bool(class_instance_identity_required),
        role_assignment_binding_required=bool(role_assignment_binding_required),
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_operation_config
