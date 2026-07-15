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
    from aware_experience_ontology.program.program_config_attribute_config import ProgramConfigAttributeConfig
    from aware_meta_ontology.attribute.attribute import Attribute


class ProgramAttribute(ORMModel):
    # Relationships
    config: ProgramConfigAttributeConfig | None = Field(default=None, exclude=True)
    attribute: Attribute | None = Field(default=None, exclude=True)

    # Foreign Keys
    program_id: UUID = Field(description="Foreign key for Program.attributes")
    config_id: UUID = Field(description="Foreign key for ProgramAttribute.config")
    attribute_id: UUID = Field(description="Foreign key for ProgramAttribute.attribute")

    @classmethod
    async def build(cls, program_id: UUID, config_id: UUID, attribute_id: UUID) -> ProgramAttribute:
        """Create deterministic attribute association edge for one Program."""

        payload = {"program_id": program_id, "config_id": config_id, "attribute_id": attribute_id}
        result = await invoke_constructor(orm_class=cls, function_name="build", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramAttribute):
            return value
        return ProgramAttribute.validate_invocation_value(value)


class ProgramAttributeBuildInput(BaseModel):
    program_id: UUID
    config_id: UUID
    attribute_id: UUID


class ProgramAttributeBuildOutput(BaseModel):
    value: ProgramAttribute


FUNCTIONS = {
    "ProgramAttribute": {
        "build": {
            "canonical": {
                "name": "build",
                "description": "Create deterministic attribute association edge for one Program.",
                "is_constructor": True,
            },
            "input": ProgramAttributeBuildInput,
            "output": ProgramAttributeBuildOutput,
        },
    },
}

__all__ = [
    "ProgramAttribute",
    "ProgramAttributeBuildInput",
    "ProgramAttributeBuildOutput",
    "FUNCTIONS",
]
