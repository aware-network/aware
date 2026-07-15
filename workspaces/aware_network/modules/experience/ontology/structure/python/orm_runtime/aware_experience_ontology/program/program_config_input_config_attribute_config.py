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
    from aware_meta_ontology.attribute.attribute_config import AttributeConfig


class ProgramConfigInputConfigAttributeConfig(ORMModel):
    """
    Signature slot for ProgramConfigInputConfig.
    Contract:
    - Keeps input signatures explicit via AttributeConfig references.
    - Association identity is deterministic from `(input_config_id, attribute_config_id)`.
    """

    # Relationships
    attribute_config: AttributeConfig | None = Field(default=None, exclude=True)

    # Attributes
    position: int | None = Field(default=None)

    # Foreign Keys
    program_config_input_config_id: UUID = Field(
        description="Foreign key for ProgramConfigInputConfig.attribute_configs"
    )
    attribute_config_id: UUID = Field(
        description="Foreign key for ProgramConfigInputConfigAttributeConfig.attribute_config"
    )

    @classmethod
    async def build_via_program_config_input_config(
        cls, program_config_input_config_id: UUID, attribute_config_id: UUID, position: int | None = None
    ) -> ProgramConfigInputConfigAttributeConfig:
        """
        Create deterministic input signature association edge for one
        ProgramConfigInputConfigAttributeConfig.
        """

        payload = {
            "program_config_input_config_id": program_config_input_config_id,
            "attribute_config_id": attribute_config_id,
            "position": position,
        }
        result = await invoke_constructor(
            orm_class=cls, function_name="build_via_program_config_input_config", payload=payload
        )
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigInputConfigAttributeConfig):
            return value
        return ProgramConfigInputConfigAttributeConfig.validate_invocation_value(value)


class ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigInput(BaseModel):
    program_config_input_config_id: UUID = Field(
        description="Foreign key for ProgramConfigInputConfig.attribute_configs"
    )
    attribute_config_id: UUID
    position: int | None = Field(default=None)


class ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigOutput(BaseModel):
    value: ProgramConfigInputConfigAttributeConfig


FUNCTIONS = {
    "ProgramConfigInputConfigAttributeConfig": {
        "build_via_program_config_input_config": {
            "canonical": {
                "name": "build_via_program_config_input_config",
                "description": "Create deterministic input signature association edge for one ProgramConfigInputConfigAttributeConfig.",
                "is_constructor": True,
            },
            "input": ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigInput,
            "output": ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigInputConfigAttributeConfig",
    "ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigInput",
    "ProgramConfigInputConfigAttributeConfigBuildViaProgramConfigInputConfigOutput",
    "FUNCTIONS",
]
