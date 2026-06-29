from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import (
    ClassSelectionMode,
    ConditionLogicStrategy,
    ConditionOperator,
)
from aware_reactivity_ontology.condition.condition_config_attribute_config import ConditionConfigAttributeConfig
from aware_reactivity_ontology.condition.condition_config_class_config import ConditionConfigClassConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_condition_config_attribute_config_id,
    stable_condition_config_class_config_id,
)

# --- AWARE: USER_IMPORTS END


async def add_attribute_config(
    condition_config_class_config: ConditionConfigClassConfig,
    attribute_config_id: UUID,
    operator: ConditionOperator,
    negate: bool = False,
) -> ConditionConfigAttributeConfig:
    """
    Attach an attribute-level policy node to this class policy node.
    """

    # --- AWARE: LOGIC START add_attribute_config
    class_config_link_id = condition_config_class_config.id
    if class_config_link_id is None:
        raise RuntimeError("ConditionConfigClassConfig.add_attribute_config requires ConditionConfigClassConfig.id")

    expected_id = stable_condition_config_attribute_config_id(
        condition_config_class_config_id=class_config_link_id,
        attribute_config_id=attribute_config_id,
        operator=operator.value,
        negate=negate,
    )
    for existing in condition_config_class_config.condition_config_attribute_configs:
        if existing.id == expected_id:
            return existing

    created = await ConditionConfigAttributeConfig.create_via_condition_config_class_config(
        condition_config_class_config_id=class_config_link_id,
        attribute_config_id=attribute_config_id,
        operator=operator,
        negate=negate,
    )
    condition_config_class_config.condition_config_attribute_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_attribute_config


async def create_via_condition_config(
    condition_config_id: UUID,
    class_config_id: UUID,
    class_selection: ClassSelectionMode = ClassSelectionMode.base_class,
    class_logic: ConditionLogicStrategy = ConditionLogicStrategy.all,
    require_existence: bool = True,
) -> ConditionConfigClassConfig:
    """
    Create a class-level condition policy node.

    Contract:
    - Canonical constructor-owned creation for class policy nodes.
    - Deterministic id scoped by (condition_config_id, class_config_id).
    """

    # --- AWARE: LOGIC START create_via_condition_config
    return ConditionConfigClassConfig(
        id=stable_condition_config_class_config_id(
            condition_config_id=condition_config_id,
            class_config_id=class_config_id,
        ),
        condition_config_id=condition_config_id,
        class_config_id=class_config_id,
        class_selection=class_selection,
        class_logic=class_logic,
        require_existence=require_existence,
    )
    # --- AWARE: LOGIC END create_via_condition_config
