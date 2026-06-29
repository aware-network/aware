from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_config_primitive_config import ConditionConfigPrimitiveConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_condition_config_primitive_config_id

# --- AWARE: USER_IMPORTS END


async def create_via_condition_config_attribute_config(
    condition_config_attribute_config_id: UUID,
    primitive_config_id: UUID,
    primitive_value: str,
    range_min: str | None = None,
    range_max: str | None = None,
) -> ConditionConfigPrimitiveConfig:
    """
    Create a primitive payload condition node.
    """

    # --- AWARE: LOGIC START create_via_condition_config_attribute_config
    return ConditionConfigPrimitiveConfig(
        id=stable_condition_config_primitive_config_id(
            condition_config_attribute_config_id=condition_config_attribute_config_id,
            primitive_config_id=primitive_config_id,
        ),
        primitive_config_id=primitive_config_id,
        primitive_value=primitive_value,
        range_min=range_min,
        range_max=range_max,
    )
    # --- AWARE: LOGIC END create_via_condition_config_attribute_config
