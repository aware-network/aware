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
from aware_reactivity_ontology.condition.condition_enums import EnumMatchMode

if TYPE_CHECKING:
    from aware_meta_ontology.enum.enum_config import EnumConfig
    from aware_reactivity_ontology.condition.condition_config_enum_option import ConditionConfigEnumOption


class ConditionConfigEnumConfig(ORMModel):
    # Relationships
    condition_config_enum_options: list[ConditionConfigEnumOption] = Field(default_factory=list)
    enum_config: EnumConfig | None = Field(default=None, exclude=True)

    # Attributes
    match_mode: EnumMatchMode = Field(default=EnumMatchMode.any_of)

    # Foreign Keys
    condition_config_attribute_config_id: UUID | None = Field(
        default=None, description="Foreign key for ConditionConfigAttributeConfig.condition_config_enum_config"
    )
    enum_config_id: UUID = Field(description="Foreign key for ConditionConfigEnumConfig.enum_config")

    async def add_enum_option(self, enum_option_id: UUID) -> ConditionConfigEnumOption:
        """Attach one enum option to this enum condition payload node."""

        payload = {"enum_option_id": enum_option_id}
        result = await invoke_instance(orm_model=self, function_name="add_enum_option", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_reactivity_ontology.condition.condition_config_enum_option import ConditionConfigEnumOption

        if isinstance(value, ConditionConfigEnumOption):
            return value
        return ConditionConfigEnumOption.validate_invocation_value(value)

    @classmethod
    async def create_via_condition_config_attribute_config(
        cls,
        condition_config_attribute_config_id: UUID,
        enum_config_id: UUID,
        match_mode: EnumMatchMode = EnumMatchMode.any_of,
        enum_option_ids: list[UUID] = [],
    ) -> ConditionConfigEnumConfig:
        """Create an enum payload condition node and optionally seed enum options."""

        payload = {
            "condition_config_attribute_config_id": condition_config_attribute_config_id,
            "enum_config_id": enum_config_id,
            "match_mode": match_mode,
            "enum_option_ids": enum_option_ids,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_condition_config_attribute_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigEnumConfig):
            return value
        return ConditionConfigEnumConfig.validate_invocation_value(value)


class ConditionConfigEnumConfigAddEnumOptionInput(BaseModel):
    enum_option_id: UUID


class ConditionConfigEnumConfigAddEnumOptionOutput(BaseModel):
    value: ConditionConfigEnumOption


class ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigInput(BaseModel):
    condition_config_attribute_config_id: UUID = Field(
        description="Foreign key for ConditionConfigAttributeConfig.condition_config_enum_config"
    )
    enum_config_id: UUID
    match_mode: EnumMatchMode = Field(default=EnumMatchMode.any_of)
    enum_option_ids: list[UUID] = Field(default_factory=list)


class ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigOutput(BaseModel):
    value: ConditionConfigEnumConfig


FUNCTIONS = {
    "ConditionConfigEnumConfig": {
        "add_enum_option": {
            "canonical": {
                "name": "add_enum_option",
                "description": "Attach one enum option to this enum condition payload node.",
                "is_constructor": False,
            },
            "input": ConditionConfigEnumConfigAddEnumOptionInput,
            "output": ConditionConfigEnumConfigAddEnumOptionOutput,
        },
        "create_via_condition_config_attribute_config": {
            "canonical": {
                "name": "create_via_condition_config_attribute_config",
                "description": "Create an enum payload condition node and optionally seed enum options.",
                "is_constructor": True,
            },
            "input": ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigInput,
            "output": ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigEnumConfig",
    "ConditionConfigEnumConfigAddEnumOptionInput",
    "ConditionConfigEnumConfigAddEnumOptionOutput",
    "ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigInput",
    "ConditionConfigEnumConfigCreateViaConditionConfigAttributeConfigOutput",
    "FUNCTIONS",
]
