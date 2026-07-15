from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import EnumMatchMode
from aware_reactivity_ontology.condition.condition_config_enum_config import ConditionConfigEnumConfig
from aware_reactivity_ontology.condition.condition_config_enum_option import ConditionConfigEnumOption

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_condition_config_enum_config_id,
)

# --- AWARE: USER_IMPORTS END


async def add_enum_option(
    condition_config_enum_config: ConditionConfigEnumConfig, enum_option_id: UUID
) -> ConditionConfigEnumOption:
    """
    Attach one enum option to this enum condition payload node.
    """

    # --- AWARE: LOGIC START add_enum_option
    enum_config_id = condition_config_enum_config.id
    if enum_config_id is None:
        raise RuntimeError("ConditionConfigEnumConfig.add_enum_option requires ConditionConfigEnumConfig.id")

    created = await ConditionConfigEnumOption.create_via_condition_config_enum_config(
        condition_config_enum_config_id=enum_config_id,
        enum_option_id=enum_option_id,
    )
    for existing in condition_config_enum_config.condition_config_enum_options:
        if existing.id == created.id:
            return existing
    condition_config_enum_config.condition_config_enum_options.append(created)
    return created
    # --- AWARE: LOGIC END add_enum_option


async def create_via_condition_config_attribute_config(
    condition_config_attribute_config_id: UUID,
    enum_config_id: UUID,
    match_mode: EnumMatchMode = EnumMatchMode.any_of,
    enum_option_ids: list[UUID] = [],
) -> ConditionConfigEnumConfig:
    """
    Create an enum payload condition node and optionally seed enum options.
    """

    # --- AWARE: LOGIC START create_via_condition_config_attribute_config
    enum_cfg = ConditionConfigEnumConfig(
        id=stable_condition_config_enum_config_id(
            condition_config_attribute_config_id=condition_config_attribute_config_id,
            enum_config_id=enum_config_id,
        ),
        enum_config_id=enum_config_id,
        match_mode=match_mode,
    )
    for enum_option_id in enum_option_ids:
        created = await ConditionConfigEnumOption.create_via_condition_config_enum_config(
            condition_config_enum_config_id=enum_cfg.id,
            enum_option_id=enum_option_id,
        )
        for existing in enum_cfg.condition_config_enum_options:
            if existing.id == created.id:
                break
        else:
            enum_cfg.condition_config_enum_options.append(created)

    return enum_cfg
    # --- AWARE: LOGIC END create_via_condition_config_attribute_config
