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
from aware_orm.runtime.invocation import (
    invoke_constructor,
    invoke_instance,
)

# Reactivity Ontology
from aware_reactivity_ontology.condition.condition_enums import (
    ConditionOperator,
    EnumMatchMode,
    RelationshipEvalMode,
)

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig
    from aware_reactivity_ontology.condition.condition_config_enum_config import ConditionConfigEnumConfig
    from aware_reactivity_ontology.condition.condition_config_primitive_config import ConditionConfigPrimitiveConfig
    from aware_reactivity_ontology.condition.condition_config_relationship_config import (
        ConditionConfigRelationshipConfig,
    )


class ConditionConfigAttributeConfig(ORMModel):
    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)
    condition_config_enum_config: ConditionConfigEnumConfig | None = Field(default=None)
    condition_config_primitive_config: ConditionConfigPrimitiveConfig | None = Field(default=None)
    condition_config_relationship_config: ConditionConfigRelationshipConfig | None = Field(default=None)

    # Attributes
    operator: ConditionOperator
    negate: bool = Field(default=False)

    # Foreign Keys
    condition_config_class_config_id: UUID = Field(
        description="Foreign key for ConditionConfigClassConfig.condition_config_attribute_configs"
    )
    attribute_config_id: UUID = Field(description="Foreign key for ConditionConfigAttributeConfig.attribute_config")

    async def set_primitive_config(
        self,
        primitive_config_id: UUID,
        primitive_value: str,
        range_min: str | None = None,
        range_max: str | None = None,
    ) -> ConditionConfigPrimitiveConfig:
        """Set primitive payload policy for this attribute condition."""

        payload = {
            "primitive_config_id": primitive_config_id,
            "primitive_value": primitive_value,
            "range_min": range_min,
            "range_max": range_max,
        }
        result = await invoke_instance(orm_model=self, function_name="set_primitive_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_primitive_config import ConditionConfigPrimitiveConfig

        if isinstance(value, ConditionConfigPrimitiveConfig):
            return value
        return ConditionConfigPrimitiveConfig.validate_invocation_value(value)

    async def set_enum_config(
        self, enum_config_id: UUID, enum_option_ids: list[UUID] = [], match_mode: EnumMatchMode = EnumMatchMode.any_of
    ) -> ConditionConfigEnumConfig:
        """Set enum payload policy for this attribute condition."""

        payload = {"enum_config_id": enum_config_id, "enum_option_ids": enum_option_ids, "match_mode": match_mode}
        result = await invoke_instance(orm_model=self, function_name="set_enum_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_enum_config import ConditionConfigEnumConfig

        if isinstance(value, ConditionConfigEnumConfig):
            return value
        return ConditionConfigEnumConfig.validate_invocation_value(value)

    async def set_relationship_config(
        self,
        class_config_relationship_id: UUID,
        eval_mode: RelationshipEvalMode = RelationshipEvalMode.exists,
        count_threshold: int | None = None,
    ) -> ConditionConfigRelationshipConfig:
        """Set relationship payload policy for this attribute condition."""

        payload = {
            "class_config_relationship_id": class_config_relationship_id,
            "eval_mode": eval_mode,
            "count_threshold": count_threshold,
        }
        result = await invoke_instance(orm_model=self, function_name="set_relationship_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_relationship_config import (
            ConditionConfigRelationshipConfig,
        )

        if isinstance(value, ConditionConfigRelationshipConfig):
            return value
        return ConditionConfigRelationshipConfig.validate_invocation_value(value)

    @classmethod
    async def create_via_condition_config_class_config(
        cls,
        condition_config_class_config_id: UUID,
        attribute_config_id: UUID,
        operator: ConditionOperator,
        negate: bool = False,
    ) -> ConditionConfigAttributeConfig:
        """Create an attribute-level condition policy node."""

        payload = {
            "condition_config_class_config_id": condition_config_class_config_id,
            "attribute_config_id": attribute_config_id,
            "operator": operator,
            "negate": negate,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_condition_config_class_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigAttributeConfig):
            return value
        return ConditionConfigAttributeConfig.validate_invocation_value(value)


class ConditionConfigAttributeConfigSetPrimitiveConfigInput(BaseModel):
    primitive_config_id: UUID
    primitive_value: str
    range_min: str | None = Field(default=None)
    range_max: str | None = Field(default=None)


class ConditionConfigAttributeConfigSetPrimitiveConfigOutput(BaseModel):
    value: ConditionConfigPrimitiveConfig


class ConditionConfigAttributeConfigSetEnumConfigInput(BaseModel):
    enum_config_id: UUID
    enum_option_ids: list[UUID] = Field(default_factory=list)
    match_mode: EnumMatchMode = Field(default=EnumMatchMode.any_of)


class ConditionConfigAttributeConfigSetEnumConfigOutput(BaseModel):
    value: ConditionConfigEnumConfig


class ConditionConfigAttributeConfigSetRelationshipConfigInput(BaseModel):
    class_config_relationship_id: UUID
    eval_mode: RelationshipEvalMode = Field(default=RelationshipEvalMode.exists)
    count_threshold: int | None = Field(default=None)


class ConditionConfigAttributeConfigSetRelationshipConfigOutput(BaseModel):
    value: ConditionConfigRelationshipConfig


class ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigInput(BaseModel):
    condition_config_class_config_id: UUID = Field(
        description="Foreign key for ConditionConfigClassConfig.condition_config_attribute_configs"
    )
    attribute_config_id: UUID
    operator: ConditionOperator
    negate: bool = Field(default=False)


class ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigOutput(BaseModel):
    value: ConditionConfigAttributeConfig


FUNCTIONS = {
    "ConditionConfigAttributeConfig": {
        "set_primitive_config": {
            "canonical": {
                "name": "set_primitive_config",
                "description": "Set primitive payload policy for this attribute condition.",
                "is_constructor": False,
            },
            "input": ConditionConfigAttributeConfigSetPrimitiveConfigInput,
            "output": ConditionConfigAttributeConfigSetPrimitiveConfigOutput,
        },
        "set_enum_config": {
            "canonical": {
                "name": "set_enum_config",
                "description": "Set enum payload policy for this attribute condition.",
                "is_constructor": False,
            },
            "input": ConditionConfigAttributeConfigSetEnumConfigInput,
            "output": ConditionConfigAttributeConfigSetEnumConfigOutput,
        },
        "set_relationship_config": {
            "canonical": {
                "name": "set_relationship_config",
                "description": "Set relationship payload policy for this attribute condition.",
                "is_constructor": False,
            },
            "input": ConditionConfigAttributeConfigSetRelationshipConfigInput,
            "output": ConditionConfigAttributeConfigSetRelationshipConfigOutput,
        },
        "create_via_condition_config_class_config": {
            "canonical": {
                "name": "create_via_condition_config_class_config",
                "description": "Create an attribute-level condition policy node.",
                "is_constructor": True,
            },
            "input": ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigInput,
            "output": ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigAttributeConfig",
    "ConditionConfigAttributeConfigSetPrimitiveConfigInput",
    "ConditionConfigAttributeConfigSetPrimitiveConfigOutput",
    "ConditionConfigAttributeConfigSetEnumConfigInput",
    "ConditionConfigAttributeConfigSetEnumConfigOutput",
    "ConditionConfigAttributeConfigSetRelationshipConfigInput",
    "ConditionConfigAttributeConfigSetRelationshipConfigOutput",
    "ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigInput",
    "ConditionConfigAttributeConfigCreateViaConditionConfigClassConfigOutput",
    "FUNCTIONS",
]
