from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import (
    ConditionOperator,
    EnumMatchMode,
    RelationshipEvalMode,
)
from aware_reactivity_ontology.condition.condition_config_attribute_config import ConditionConfigAttributeConfig
from aware_reactivity_ontology.condition.condition_config_enum_config import ConditionConfigEnumConfig
from aware_reactivity_ontology.condition.condition_config_primitive_config import ConditionConfigPrimitiveConfig
from aware_reactivity_ontology.condition.condition_config_relationship_config import ConditionConfigRelationshipConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_condition_config_attribute_config_id,
    stable_condition_config_relationship_config_id,
)

# --- AWARE: USER_IMPORTS END


async def set_primitive_config(
    condition_config_attribute_config: ConditionConfigAttributeConfig,
    primitive_config_id: UUID,
    primitive_value: str,
    range_min: str | None = None,
    range_max: str | None = None,
) -> ConditionConfigPrimitiveConfig:
    """
    Set primitive payload policy for this attribute condition.
    """

    # --- AWARE: LOGIC START set_primitive_config
    condition_config_attribute_config_id = condition_config_attribute_config.id
    if condition_config_attribute_config_id is None:
        raise RuntimeError(
            "ConditionConfigAttributeConfig.set_primitive_config requires ConditionConfigAttributeConfig.id"
        )

    created = await ConditionConfigPrimitiveConfig.create_via_condition_config_attribute_config(
        condition_config_attribute_config_id=condition_config_attribute_config_id,
        primitive_config_id=primitive_config_id,
        primitive_value=primitive_value,
        range_min=range_min,
        range_max=range_max,
    )
    condition_config_attribute_config.condition_config_primitive_config = created
    return created
    # --- AWARE: LOGIC END set_primitive_config


async def set_enum_config(
    condition_config_attribute_config: ConditionConfigAttributeConfig,
    enum_config_id: UUID,
    enum_option_ids: list[UUID] = [],
    match_mode: EnumMatchMode = EnumMatchMode.any_of,
) -> ConditionConfigEnumConfig:
    """
    Set enum payload policy for this attribute condition.
    """

    # --- AWARE: LOGIC START set_enum_config
    condition_config_attribute_config_id = condition_config_attribute_config.id
    if condition_config_attribute_config_id is None:
        raise RuntimeError("ConditionConfigAttributeConfig.set_enum_config requires ConditionConfigAttributeConfig.id")

    created = await ConditionConfigEnumConfig.create_via_condition_config_attribute_config(
        condition_config_attribute_config_id=condition_config_attribute_config_id,
        enum_config_id=enum_config_id,
        enum_option_ids=list(enum_option_ids),
        match_mode=match_mode,
    )
    condition_config_attribute_config.condition_config_enum_config = created
    return created
    # --- AWARE: LOGIC END set_enum_config


async def set_relationship_config(
    condition_config_attribute_config: ConditionConfigAttributeConfig,
    class_config_relationship_id: UUID,
    eval_mode: RelationshipEvalMode = RelationshipEvalMode.exists,
    count_threshold: int | None = None,
) -> ConditionConfigRelationshipConfig:
    """
    Set relationship payload policy for this attribute condition.
    """

    # --- AWARE: LOGIC START set_relationship_config
    condition_config_attribute_config_id = condition_config_attribute_config.id
    if condition_config_attribute_config_id is None:
        raise RuntimeError(
            "ConditionConfigAttributeConfig.set_relationship_config requires ConditionConfigAttributeConfig.id"
        )

    expected_id = stable_condition_config_relationship_config_id(
        condition_config_attribute_config_id=condition_config_attribute_config_id,
        class_config_relationship_id=class_config_relationship_id,
    )
    existing = condition_config_attribute_config.condition_config_relationship_config
    if existing is not None and existing.id == expected_id:
        return existing

    created = await ConditionConfigRelationshipConfig.create_via_condition_config_attribute_config(
        condition_config_attribute_config_id=condition_config_attribute_config_id,
        class_config_relationship_id=class_config_relationship_id,
        eval_mode=eval_mode,
        count_threshold=count_threshold,
    )
    condition_config_attribute_config.condition_config_relationship_config = created
    return created
    # --- AWARE: LOGIC END set_relationship_config


async def create_via_condition_config_class_config(
    condition_config_class_config_id: UUID, attribute_config_id: UUID, operator: ConditionOperator, negate: bool = False
) -> ConditionConfigAttributeConfig:
    """
    Create an attribute-level condition policy node.
    """

    # --- AWARE: LOGIC START create_via_condition_config_class_config
    return ConditionConfigAttributeConfig(
        id=stable_condition_config_attribute_config_id(
            condition_config_class_config_id=condition_config_class_config_id,
            attribute_config_id=attribute_config_id,
            operator=operator.value,
            negate=negate,
        ),
        condition_config_class_config_id=condition_config_class_config_id,
        attribute_config_id=attribute_config_id,
        operator=operator,
        negate=negate,
    )
    # --- AWARE: LOGIC END create_via_condition_config_class_config
