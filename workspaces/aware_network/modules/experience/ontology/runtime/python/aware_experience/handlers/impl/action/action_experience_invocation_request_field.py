from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Experience Ontology
from aware_experience_ontology.action.action_experience_invocation_request_field import (
    ActionExperienceInvocationRequestField,
)

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_experience.stable_ids import (
    stable_action_experience_invocation_request_field_id,
)
from aware_meta.runtime.handler_context import (
    current_handler_index,
    current_handler_session,
)

# --- AWARE: USER_IMPORTS END


async def build_via_action_experience_invocation(
    action_experience_invocation_id: UUID,
    attribute_config_id: UUID,
    source_ref: str,
    required: bool = True,
    position: int | None = None,
) -> ActionExperienceInvocationRequestField:
    """
    Create deterministic request-field composition under one action
    invocation binding.
    """

    # --- AWARE: LOGIC START build_via_action_experience_invocation
    session = current_handler_session()
    request_field_id = stable_action_experience_invocation_request_field_id(
        action_experience_invocation_id=action_experience_invocation_id,
        attribute_config_id=attribute_config_id,
    )
    attribute_config = current_handler_index().attribute_configs_by_id.get(
        attribute_config_id,
    )
    if attribute_config is None:
        raise RuntimeError(
            "ActionExperienceInvocationRequestField.build_via_action_experience_invocation "
            "requires existing AttributeConfig in session: " + f"attribute_config_id={attribute_config_id}"
        )
    existing = session.imap_get(
        ActionExperienceInvocationRequestField,
        request_field_id,
    )
    if existing is not None:
        if (
            existing.action_experience_invocation_id != action_experience_invocation_id
            or existing.attribute_config_id != attribute_config_id
        ):
            raise RuntimeError(
                "ActionExperienceInvocationRequestField.build_via_action_experience_invocation "
                "field mismatch for existing request field: " + f"request_field_id={request_field_id}"
            )
        existing.source_ref = source_ref
        existing.required = required
        existing.position = position
        existing.attribute_config = attribute_config
        return existing

    return ActionExperienceInvocationRequestField(
        id=request_field_id,
        action_experience_invocation_id=action_experience_invocation_id,
        attribute_config_id=attribute_config_id,
        attribute_config=attribute_config,
        source_ref=source_ref,
        required=required,
        position=position,
    )
    # --- AWARE: LOGIC END build_via_action_experience_invocation
