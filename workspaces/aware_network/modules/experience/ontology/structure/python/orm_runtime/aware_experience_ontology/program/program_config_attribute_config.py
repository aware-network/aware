from __future__ import annotations

# Standard
from typing import TYPE_CHECKING
from uuid import UUID

# Third-party
from pydantic import (
    BaseModel,
    Field,
)

# Experience Ontology
from aware_experience_ontology.program.program_enums import ProgramAttributeType

# Orm
from aware_orm.models.orm_model import ORMModel
from aware_orm.runtime.invocation import invoke_constructor

if TYPE_CHECKING:
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class ProgramConfigAttributeConfig(ORMModel):
    """
    Program-level typed attribute contract edge.
    Contract:
    - Declares canonical program I/O schema via AttributeConfig references.
    - Type is explicit (`input` / `output`) for future parity with function schema rails.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    position: int | None = Field(default=None)
    required: bool = Field(default=True)
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.attribute_configs")
    attribute_config_id: UUID = Field(description="Foreign key for ProgramConfigAttributeConfig.attribute_config")

    @classmethod
    async def create_via_program_config(
        cls,
        program_config_id: UUID,
        attribute_config_id: UUID,
        type: ProgramAttributeType = ProgramAttributeType.input,
        position: int | None = None,
        required: bool = True,
    ) -> ProgramConfigAttributeConfig:
        """Create deterministic ProgramConfigAttributeConfig association edge."""

        payload = {
            "program_config_id": program_config_id,
            "attribute_config_id": attribute_config_id,
            "type": type,
            "position": position,
            "required": required,
        }
        result = await invoke_constructor(orm_class=cls, function_name="create_via_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigAttributeConfig):
            return value
        return ProgramConfigAttributeConfig.validate_invocation_value(value)


class ProgramConfigAttributeConfigCreateViaProgramConfigInput(BaseModel):
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.attribute_configs")
    attribute_config_id: UUID
    type: ProgramAttributeType = Field(default=ProgramAttributeType.input)
    position: int | None = Field(default=None)
    required: bool = Field(default=True)


class ProgramConfigAttributeConfigCreateViaProgramConfigOutput(BaseModel):
    value: ProgramConfigAttributeConfig


FUNCTIONS = {
    "ProgramConfigAttributeConfig": {
        "create_via_program_config": {
            "canonical": {
                "name": "create_via_program_config",
                "description": "Create deterministic ProgramConfigAttributeConfig association edge.",
                "is_constructor": True,
            },
            "input": ProgramConfigAttributeConfigCreateViaProgramConfigInput,
            "output": ProgramConfigAttributeConfigCreateViaProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigAttributeConfig",
    "ProgramConfigAttributeConfigCreateViaProgramConfigInput",
    "ProgramConfigAttributeConfigCreateViaProgramConfigOutput",
    "FUNCTIONS",
]
