from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Code
from aware_code.types import JsonObject

# Experience Ontology
from aware_experience_ontology.contract.experience_contract_actor_role_grant import ExperienceContractActorRoleGrant

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
# --- AWARE: USER_IMPORTS END


async def build_via_projection_experience(
    projection_experience_id: UUID,
    grant_key: str,
    actor_config_role_config_id: UUID,
    role_config_id: UUID,
    access_scope: str = "experience",
    participant_kind: str = "actor",
    class_instance_identity_required: bool = False,
    role_assignment_binding_required: bool = True,
    grant_policy_json: JsonObject | None = JsonObject(),
    description: str | None = None,
) -> ExperienceContractActorRoleGrant:
    """
    Create one Experience-owned public actor-role grant.

    Contract:
    - Parent ProjectionExperience scope is propagated by constructor lowering.
    - Stable identity is `(projection_experience_id, grant_key)`.
    - The grant is not a global RoleConfig grant; it is RoleConfig eligibility
      through an Identity ActorConfigRoleConfig.
    - Runtime must reject mismatched actor-config/role-config pairs.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    raise NotImplementedError("AWARE: implement handler logic")
    # --- AWARE: LOGIC END build_via_projection_experience
