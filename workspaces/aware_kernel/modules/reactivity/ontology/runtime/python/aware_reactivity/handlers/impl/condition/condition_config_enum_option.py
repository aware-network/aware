from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_config_enum_option import ConditionConfigEnumOption

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_condition_config_enum_option_id

# --- AWARE: USER_IMPORTS END


async def create_via_condition_config_enum_config(
    condition_config_enum_config_id: UUID, enum_option_id: UUID
) -> ConditionConfigEnumOption:
    """
    Create a deterministic enum option edge for enum condition payloads.
    """

    # --- AWARE: LOGIC START create_via_condition_config_enum_config
    return ConditionConfigEnumOption(
        id=stable_condition_config_enum_option_id(
            condition_config_enum_config_id=condition_config_enum_config_id,
            enum_option_id=enum_option_id,
        ),
        condition_config_enum_config_id=condition_config_enum_config_id,
        enum_option_id=enum_option_id,
    )
    # --- AWARE: LOGIC END create_via_condition_config_enum_config
