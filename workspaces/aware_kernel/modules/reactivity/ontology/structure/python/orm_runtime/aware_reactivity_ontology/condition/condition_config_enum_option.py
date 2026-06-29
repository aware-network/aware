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
    from aware_meta_ontology.enum.enum_option import EnumOption


class ConditionConfigEnumOption(ORMModel):
    # Relationships
    enum_option: EnumOption | None = Field(default=None, exclude=True)

    # Foreign Keys
    condition_config_enum_config_id: UUID = Field(
        description="Foreign key for ConditionConfigEnumConfig.condition_config_enum_options"
    )
    enum_option_id: UUID = Field(description="Foreign key for ConditionConfigEnumOption.enum_option")

    @classmethod
    async def create_via_condition_config_enum_config(
        cls, condition_config_enum_config_id: UUID, enum_option_id: UUID
    ) -> ConditionConfigEnumOption:
        """Create a deterministic enum option edge for enum condition payloads."""

        payload = {"condition_config_enum_config_id": condition_config_enum_config_id, "enum_option_id": enum_option_id}
        result = await invoke_constructor(
            orm_class=cls, function_name="create_via_condition_config_enum_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ConditionConfigEnumOption):
            return value
        return ConditionConfigEnumOption.validate_invocation_value(value)


class ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigInput(BaseModel):
    condition_config_enum_config_id: UUID = Field(
        description="Foreign key for ConditionConfigEnumConfig.condition_config_enum_options"
    )
    enum_option_id: UUID


class ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigOutput(BaseModel):
    value: ConditionConfigEnumOption


FUNCTIONS = {
    "ConditionConfigEnumOption": {
        "create_via_condition_config_enum_config": {
            "canonical": {
                "name": "create_via_condition_config_enum_config",
                "description": "Create a deterministic enum option edge for enum condition payloads.",
                "is_constructor": True,
            },
            "input": ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigInput,
            "output": ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigOutput,
        },
    },
}

__all__ = [
    "ConditionConfigEnumOption",
    "ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigInput",
    "ConditionConfigEnumOptionCreateViaConditionConfigEnumConfigOutput",
    "FUNCTIONS",
]
