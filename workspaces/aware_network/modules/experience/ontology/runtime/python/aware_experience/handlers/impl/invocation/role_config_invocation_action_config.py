from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.role_config_invocation_action_config import RoleConfigInvocationActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_role_config_invocation_action_config_id
from aware_experience_ontology.invocation.experience_invocation_action_config import (
    ExperienceInvocationActionConfig,
)
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_experience_invocation_action_config(
    experience_invocation_action_config_id: UUID,
    role_config_id: UUID,
    policy_key: str = "invoke",
    requirement_kind: str = "admitted_actor_role",
    description: str | None = None,
) -> RoleConfigInvocationActionConfig:
    """
    Bind one RoleConfig to the parent ExperienceInvocationActionConfig.
    """

    # --- AWARE: LOGIC START build_via_experience_invocation_action_config
    normalized_policy_key = (policy_key or "").strip() or "invoke"
    normalized_requirement_kind = (requirement_kind or "").strip() or "admitted_actor_role"
    normalized_description = (description or "").strip() or None

    session = current_handler_session()
    parent = session.imap_get(
        ExperienceInvocationActionConfig,
        experience_invocation_action_config_id,
    )
    if parent is None:
        raise RuntimeError(
            "RoleConfigInvocationActionConfig requires existing "
            + "ExperienceInvocationActionConfig: "
            + f"experience_invocation_action_config_id={experience_invocation_action_config_id}"
        )

    policy_id = stable_role_config_invocation_action_config_id(
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        role_config_id=role_config_id,
        policy_key=normalized_policy_key,
    )
    existing = session.imap_get(RoleConfigInvocationActionConfig, policy_id)
    if existing is not None:
        if (
            existing.experience_invocation_action_config_id != experience_invocation_action_config_id
            or existing.role_config_id != role_config_id
            or (existing.policy_key or "").strip().casefold() != normalized_policy_key.casefold()
            or (existing.requirement_kind or "").strip() != normalized_requirement_kind
            or existing.description != normalized_description
        ):
            raise RuntimeError(
                "RoleConfigInvocationActionConfig field mismatch for existing policy: "
                + f"role_config_invocation_action_config_id={policy_id}"
            )
        return existing

    return RoleConfigInvocationActionConfig(
        id=policy_id,
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        role_config_id=role_config_id,
        policy_key=normalized_policy_key,
        requirement_kind=normalized_requirement_kind,
        description=normalized_description,
    )
    # --- AWARE: LOGIC END build_via_experience_invocation_action_config
