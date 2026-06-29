from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import (
    ClassSelectionMode,
    ConditionLogicStrategy,
)
from aware_reactivity_ontology.condition.condition_config import ConditionConfig
from aware_reactivity_ontology.condition.condition_config_class_config import ConditionConfigClassConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import (
    stable_condition_config_class_config_id,
    stable_condition_config_id,
)

# --- AWARE: USER_IMPORTS END


async def create(
    name: str,
    description: str,
    logic_strategy: ConditionLogicStrategy = ConditionLogicStrategy.all,
    is_enabled: bool = True,
    is_system: bool = False,
) -> ConditionConfig:
    """
    Create a canonical condition policy root.

    Contract:
    - Constructor-owned creation path for condition policy roots.
    - Initial evaluation flags and logic strategy are persisted at creation time.
    """

    # --- AWARE: LOGIC START create
    return ConditionConfig(
        id=stable_condition_config_id(name=name),
        name=name,
        description=description,
        logic_strategy=logic_strategy,
        is_enabled=is_enabled,
        is_system=is_system,
    )
    # --- AWARE: LOGIC END create


async def add_class_config(
    condition_config: ConditionConfig,
    class_config_id: UUID,
    class_selection: ClassSelectionMode = ClassSelectionMode.base_class,
    class_logic: ConditionLogicStrategy = ConditionLogicStrategy.all,
    require_existence: bool = True,
) -> ConditionConfigClassConfig:
    """
    Attach a class-level policy node to this condition root.

    Contract:
    - Canonical edge creation through the ConditionConfig root.
    - Deterministic id scoped by (condition_config_id, class_config_id).
    """

    # --- AWARE: LOGIC START add_class_config
    condition_config_id = condition_config.id
    if condition_config_id is None:
        raise RuntimeError("ConditionConfig.add_class_config requires ConditionConfig.id")

    expected_id = stable_condition_config_class_config_id(
        condition_config_id=condition_config_id,
        class_config_id=class_config_id,
    )
    for existing in condition_config.condition_config_class_configs:
        if existing.id == expected_id:
            return existing

    created = await ConditionConfigClassConfig.create_via_condition_config(
        condition_config_id=condition_config_id,
        class_config_id=class_config_id,
        class_selection=class_selection,
        class_logic=class_logic,
        require_existence=require_existence,
    )
    condition_config.condition_config_class_configs.append(created)
    return created
    # --- AWARE: LOGIC END add_class_config
