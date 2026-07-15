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

if TYPE_CHECKING:
    from aware_meta_ontology.primitive.primitive_config import PrimitiveConfig


class ConditionConfigPrimitiveConfig(ORMModel):
    # Relationships
    primitive_config: PrimitiveConfig | None = Field(default=None, exclude=True)

    # Attributes
    primitive_value: str
    range_max: str | None = Field(default=None)
    range_min: str | None = Field(default=None)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_primitive_config"
    )
    primitive_config_id: UUID = Field(description="Foreign key for ConditionConfigPrimitiveConfig.primitive_config")

    @classmethod
    async def create_via_condition_config_attribute_config(
        cls,
        condition_config_attribute_config_id: UUID,
        primitive_config_id: UUID,
        primitive_value: str,
        range_min: str | None = None,
        range_max: str | None = None,
    ) -> ConditionConfigPrimitiveConfig:
        """Create a primitive payload condition node."""

        payload = {
            "condition_config_attribute_config_id": condition_config_attribute_config_id,
            "primitive_config_id": primitive_config_id,
            "primitive_value": primitive_value,
            "range_min": range_min,
            "range_max": range_max,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_condition_config_attribute_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigPrimitiveConfig):
            return value
        return ConditionConfigPrimitiveConfig.validate_invocation_value(value)


class ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigInput(BaseModel):
    condition_config_attribute_config_id: UUID = Field(
        description="Foreign key for ConditionConfigAttributeConfig.condition_config_primitive_config"
    )
    primitive_config_id: UUID
    primitive_value: str
    range_min: str | None = Field(default=None)
    range_max: str | None = Field(default=None)


class ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigOutput(BaseModel):
    value: ConditionConfigPrimitiveConfig


FUNCTIONS = {
    "ConditionConfigPrimitiveConfig": {
        "create_via_condition_config_attribute_config": {
            "canonical": {
                "name": "create_via_condition_config_attribute_config",
                "description": "Create a primitive payload condition node.",
                "is_constructor": True,
            },
            "input": ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigInput,
            "output": ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigPrimitiveConfig",
    "ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigInput",
    "ConditionConfigPrimitiveConfigCreateViaConditionConfigAttributeConfigOutput",
    "FUNCTIONS",
]
