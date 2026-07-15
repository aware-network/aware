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
    from aware_experience_ontology.program.program_config_input_config_attribute_config import (
        ProgramConfigInputConfigAttributeConfig,
    )
    from aware_meta_ontology.attribute.attribute import Attribute


class ProgramInputAttribute(ORMModel):
    # Relationships
    config: ProgramConfigInputConfigAttributeConfig | None = Field(default=None, exclude=True)
    attribute: Attribute | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.input_attributes")
    config_id: UUID = Field(description="Foreign key for ProgramInputAttribute.config")
    attribute_id: UUID = Field(description="Foreign key for ProgramInputAttribute.attribute")

    @classmethod
    async def build(cls, program_id: UUID, config_id: UUID, attribute_id: UUID) -> ProgramInputAttribute:
        """Create deterministic input signature association edge for one Program."""

        payload = {"program_id": program_id, "config_id": config_id, "attribute_id": attribute_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramInputAttribute):
            return value
        return ProgramInputAttribute.validate_invocation_value(value)


class ProgramInputAttributeBuildInput(BaseModel):
    program_id: UUID
    config_id: UUID
    attribute_id: UUID


class ProgramInputAttributeBuildOutput(BaseModel):
    value: ProgramInputAttribute


FUNCTIONS = {
    "ProgramInputAttribute": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic input signature association edge for one Program.",
                "is_constructor": True,
            },
            "input": ProgramInputAttributeBuildInput,
            "output": ProgramInputAttributeBuildOutput,
        },
    },
}

__all__ = [
    "ProgramInputAttribute",
    "ProgramInputAttributeBuildInput",
    "ProgramInputAttributeBuildOutput",
    "FUNCTIONS",
]
