from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.invocation.experience_invocation_action_config import ExperienceInvocationActionConfig
from aware_experience_ontology.invocation.experience_invocation_action_target_kind import (
    ExperienceInvocationActionTargetKind,
)
from aware_experience_ontology.invocation.role_config_invocation_action_config import RoleConfigInvocationActionConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import stable_experience_invocation_action_config_id
from aware_meta.runtime.handler_context import (
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def allow_role_config(
    experience_invocation_action_config: ExperienceInvocationActionConfig,
    role_config_id: UUID,
    policy_key: str = "invoke",
    requirement_kind: str = "admitted_actor_role",
    description: str | None = None,
) -> RoleConfigInvocationActionConfig:
    """
    Authorize one Identity RoleConfig to invoke this Experience action config.

    Contract:
    - Experience owns the action-entrypoint policy.
    - Identity owns the concrete RoleConfig and ActorRole truth.
    - Dispatch preflight must prove admitted actor-role evidence against this edge.
    """

    # --- AWARE: LOGIC START allow_role_config
    experience_invocation_action_config_id = experience_invocation_action_config.id
    if experience_invocation_action_config_id is None:
        raise RuntimeError("ExperienceInvocationActionConfig.allow_role_config requires id")

    created = await RoleConfigInvocationActionConfig.build_via_experience_invocation_action_config(
        experience_invocation_action_config_id=experience_invocation_action_config_id,
        role_config_id=role_config_id,
        policy_key=policy_key,
        requirement_kind=requirement_kind,
        description=description,
    )
    if created.experience_invocation_action_config_id != experience_invocation_action_config_id:
        raise RuntimeError(
            "ExperienceInvocationActionConfig.allow_role_config context mismatch "
            + "for created policy: "
            + f"role_config_invocation_action_config_id={created.id}"
        )

    for existing in experience_invocation_action_config.role_policies:
        if existing.id == created.id:
            return existing

    experience_invocation_action_config.role_policies.append(created)
    return created
    # --- AWARE: LOGIC END allow_role_config


async def build_via_projection_experience(
    projection_experience_id: UUID,
    target_kind: ExperienceInvocationActionTargetKind,
    api_capability_endpoint_id: UUID | None = None,
    sdk_operation_id: UUID | None = None,
) -> ExperienceInvocationActionConfig:
    """
    Create one deterministic invocation action config under a ProjectionExperience.

    Contract:
    - Parent `ProjectionExperience` scope is propagated by constructor lowering.
    - `target_kind` discriminates the executable target family.
    - `api` targets must set only `api_capability_endpoint`.
    - `sdk` targets must set only `sdk_operation`.
    - String target refs and renderer action keys are intentionally absent;
      surface wrappers own those higher-level bindings.
    """

    # --- AWARE: LOGIC START build_via_projection_experience
    target_kind_value = (
        target_kind.value
        if isinstance(target_kind, ExperienceInvocationActionTargetKind)
        else str(target_kind or "").strip().casefold()
    )
    if target_kind_value == ExperienceInvocationActionTargetKind.sdk.value:
        if sdk_operation_id is None:
            raise RuntimeError("ExperienceInvocationActionConfig sdk target requires sdk_operation_id")
        if api_capability_endpoint_id is not None:
            raise RuntimeError("ExperienceInvocationActionConfig sdk target cannot set " + "api_capability_endpoint_id")
        entity_id = sdk_operation_id
        normalized_target_kind = ExperienceInvocationActionTargetKind.sdk
    elif target_kind_value == ExperienceInvocationActionTargetKind.api.value:
        if api_capability_endpoint_id is None:
            raise RuntimeError("ExperienceInvocationActionConfig api target requires " + "api_capability_endpoint_id")
        if sdk_operation_id is not None:
            raise RuntimeError("ExperienceInvocationActionConfig api target cannot set sdk_operation_id")
        entity_id = api_capability_endpoint_id
        normalized_target_kind = ExperienceInvocationActionTargetKind.api
    else:
        raise RuntimeError(
            "ExperienceInvocationActionConfig target_kind must be api or sdk: " + f"target_kind={target_kind!r}"
        )

    config_id = stable_experience_invocation_action_config_id(
        projection_experience_id=projection_experience_id,
        target_kind=normalized_target_kind.value,
        entity_id=entity_id,
    )

    session = current_handler_session()
    existing = session.imap_get(ExperienceInvocationActionConfig, config_id)
    if existing is not None:
        if (
            existing.projection_experience_id != projection_experience_id
            or existing.api_capability_endpoint_id != api_capability_endpoint_id
            or existing.sdk_operation_id != sdk_operation_id
            or existing.target_kind != normalized_target_kind
        ):
            raise RuntimeError(
                "ExperienceInvocationActionConfig payload mismatch for existing config: "
                + f"experience_invocation_action_config_id={config_id}"
            )
        return existing

    return ExperienceInvocationActionConfig(
        id=config_id,
        projection_experience_id=projection_experience_id,
        api_capability_endpoint_id=api_capability_endpoint_id,
        sdk_operation_id=sdk_operation_id,
        target_kind=normalized_target_kind,
    )
    # --- AWARE: LOGIC END build_via_projection_experience
