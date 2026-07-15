from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Service Ontology
from aware_service_ontology.service.service_contract_config_actor_role_grant import ServiceContractConfigActorRoleGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from typing import cast

from aware_identity_ontology.role.role_config import RoleConfig
from aware_meta.runtime.handler_context import current_handler_session
from aware_service_ontology.stable_ids import stable_service_contract_config_actor_role_grant_id

# --- AWARE: USER_IMPORTS END


async def build_via_service_contract_config(
    service_contract_config_id: UUID,
    role_config_id: UUID,
    scope_kind: str = "service",
    scope_ref: str = "default",
    access_scope: str = "service",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    grant_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ServiceContractConfigActorRoleGrant:
    """
    Creates one reusable ActorRole grant declaration under a ServiceContractConfig.

    Contract:
    - Parent ServiceContractConfig scope is propagated by constructor lowering.
    - Role policy remains owned by Identity RoleConfig.
    - Concrete ServiceContract activation can materialize/resolve ActorRole evidence through Identity.
    """

    # --- AWARE: LOGIC START build_via_service_contract_config
    access_scope_norm = (access_scope or "").strip() or "service"
    scope_kind_norm = (scope_kind or "").strip() or "service"
    scope_ref_norm = (scope_ref or "").strip() or "default"
    grant_policy = cast(JsonObject, dict(grant_policy_json or {}))
    grant_id = stable_service_contract_config_actor_role_grant_id(
        service_contract_config_id=service_contract_config_id,
        role_config_id=role_config_id,
        scope_kind=scope_kind_norm,
        scope_ref=scope_ref_norm,
    )
    session = current_handler_session()
    _ = session.imap_get(RoleConfig, role_config_id)

    existing = session.imap_get(ServiceContractConfigActorRoleGrant, grant_id)
    if existing is not None:
        if (
            existing.service_contract_config_id != service_contract_config_id
            or existing.role_config_id != role_config_id
            or (existing.scope_kind or "").strip() != scope_kind_norm
            or (existing.scope_ref or "").strip() != scope_ref_norm
        ):
            raise RuntimeError(
                "ServiceContractConfigActorRoleGrant payload mismatch for existing grant: " + f"grant_id={grant_id}"
            )
        existing.access_scope = access_scope_norm
        existing.class_instance_identity_required = bool(class_instance_identity_required)
        existing.role_assignment_binding_required = bool(role_assignment_binding_required)
        existing.grant_policy_json = grant_policy
        existing.description = description
        return existing

    return ServiceContractConfigActorRoleGrant(
        id=grant_id,
        service_contract_config_id=service_contract_config_id,
        role_config_id=role_config_id,
        scope_kind=scope_kind_norm,
        scope_ref=scope_ref_norm,
        access_scope=access_scope_norm,
        class_instance_identity_required=bool(class_instance_identity_required),
        role_assignment_binding_required=bool(role_assignment_binding_required),
        grant_policy_json=grant_policy,
        description=description,
    )
    # --- AWARE: LOGIC END build_via_service_contract_config
