from __future__ import annotations

# --- AWARE: MANAGED_IMPORTS START
# fmt: off
# Standard
from uuid import UUID

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import RelationshipEvalMode
from aware_reactivity_ontology.condition.condition_config_relationship_config import ConditionConfigRelationshipConfig

# fmt: on
# --- AWARE: MANAGED_IMPORTS END

# --- AWARE: USER_IMPORTS START
from aware_reactivity.stable_ids import stable_condition_config_relationship_config_id

# --- AWARE: USER_IMPORTS END


async def create_via_condition_config_attribute_config(
    condition_config_attribute_config_id: UUID,
    class_config_relationship_id: UUID,
    eval_mode: RelationshipEvalMode = RelationshipEvalMode.exists,
    count_threshold: int | None = None,
) -> ConditionConfigRelationshipConfig:
    """
    Create a relationship payload condition node.
    """

    # --- AWARE: LOGIC START create_via_condition_config_attribute_config
    return ConditionConfigRelationshipConfig(
        id=stable_condition_config_relationship_config_id(
            condition_config_attribute_config_id=condition_config_attribute_config_id,
            class_config_relationship_id=class_config_relationship_id,
        ),
        class_config_relationship_id=class_config_relationship_id,
        eval_mode=eval_mode,
        count_threshold=count_threshold,
    )
    # --- AWARE: LOGIC END create_via_condition_config_attribute_config
