from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import RelationshipEvalMode

if TYPE_CHECKING:
    from aware_meta_ontology.class_.class_config_relationship import ClassConfigRelationship
    from aware_reactivity_ontology.condition.condition_config import ConditionConfig


class ConditionConfigRelationshipConfig(ORMModel):
    # Relationships
    nested_condition_config: ConditionConfig | None = Field(default=None, exclude=True)
    class_config_relationship: ClassConfigRelationship | None = Field(default=None, exclude=True)

    # Attributes
    count_threshold: int | None = Field(default=None)
    eval_mode: RelationshipEvalMode = Field(default=RelationshipEvalMode.exists)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_relationship_config"
    )
    nested_condition_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigRelationshipConfig.nested_condition_config"
    )
    class_config_relationship_id: UUID = Field(
        description="Foreign key for ConditionConfigRelationshipConfig.class_config_relationship"
    )

    @classmethod
    async def create_via_condition_config_attribute_config(
        cls,
        condition_config_attribute_config_id: UUID,
        class_config_relationship_id: UUID,
        eval_mode: RelationshipEvalMode = RelationshipEvalMode.exists,
        count_threshold: int | None = None,
    ) -> ConditionConfigRelationshipConfig:
        """Create a relationship payload condition node."""

        payload = {
            "condition_config_attribute_config_id": condition_config_attribute_config_id,
            "class_config_relationship_id": class_config_relationship_id,
            "eval_mode": eval_mode,
            "count_threshold": count_threshold,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_condition_config_attribute_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigRelationshipConfig):
            return value
        return ConditionConfigRelationshipConfig.validate_invocation_value(value)


class ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigInput(BaseModel):
    condition_config_attribute_config_id: UUID = Field(
        description="Foreign key for ConditionConfigAttributeConfig.condition_config_relationship_config"
    )
    class_config_relationship_id: UUID
    eval_mode: RelationshipEvalMode = Field(default=RelationshipEvalMode.exists)
    count_threshold: int | None = Field(default=None)


class ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigOutput(BaseModel):
    value: ConditionConfigRelationshipConfig


FUNCTIONS = {
    "ConditionConfigRelationshipConfig": {
        "create_via_condition_config_attribute_config": {
            "canonical": {
                "name": "create_via_condition_config_attribute_config",
                "description": "Create a relationship payload condition node.",
                "is_constructor": True,
            },
            "input": ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigInput,
            "output": ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigRelationshipConfig",
    "ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigInput",
    "ConditionConfigRelationshipConfigCreateViaConditionConfigAttributeConfigOutput",
    "FUNCTIONS",
]
