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

# Types
from aware_types import JsonObject

if TYPE_CHECKING:
    from aware_experience_ontology.program.program_config_input_config_attribute_config import (
        ProgramConfigInputConfigAttributeConfig,
    )


class ProgramConfigInputConfig(ORMModel):
    """
    Declarative program input configuration unit under a ProgramConfig.
    Contract:
    - Declares runtime-injected symbols.
    - Pure config (no runtime effects).
    """

    # Relationships
    attribute_configs: list[ProgramConfigInputConfigAttributeConfig] = Field(default_factory=list, exclude=True)

    # Attributes
    name: str
    source: str
    required: bool = Field(default=True)
    default_expr: JsonObject | None = Field(default=None)

    # Foreign Keys
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.input_configs")

    async def add_attribute_config(
        self, attribute_config_id: UUID, position: int | None = None
    ) -> ProgramConfigInputConfigAttributeConfig:
        """Attach one typed input signature attribute under this ProgramConfigInputConfig."""

        payload = {"attribute_config_id": attribute_config_id, "position": position}
        result = await invoke_instance(orm_model=self, function_name="add_attribute_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        from aware_experience_ontology.program.program_config_input_config_attribute_config import (
            ProgramConfigInputConfigAttributeConfig,
        )

        if isinstance(value, ProgramConfigInputConfigAttributeConfig):
            return value
        return ProgramConfigInputConfigAttributeConfig.validate_invocation_value(value)

    @classmethod
    async def build_via_program_config(
        cls,
        program_config_id: UUID,
        name: str,
        source: str,
        required: bool = True,
        default_expr: JsonObject | None = None,
    ) -> ProgramConfigInputConfig:
        """Create deterministic ProgramConfigInputConfig under one ProgramConfig."""

        payload = {
            "program_config_id": program_config_id,
            "name": name,
            "source": source,
            "required": required,
            "default_expr": default_expr,
        }
        result = await invoke_constructor(orm_class=cls, function_name="build_via_program_config", payload=payload)
        value = result.get("value") if isinstance(result, dict) and "value" in result else result
        if isinstance(value, ProgramConfigInputConfig):
            return value
        return ProgramConfigInputConfig.validate_invocation_value(value)


class ProgramConfigInputConfigAddAttributeConfigInput(BaseModel):
    attribute_config_id: UUID
    position: int | None = Field(default=None)


class ProgramConfigInputConfigAddAttributeConfigOutput(BaseModel):
    value: ProgramConfigInputConfigAttributeConfig


class ProgramConfigInputConfigBuildViaProgramConfigInput(BaseModel):
    program_config_id: UUID = Field(description="Foreign key for ProgramConfig.input_configs")
    name: str
    source: str
    required: bool = Field(default=True)
    default_expr: JsonObject | None = Field(default=None)


class ProgramConfigInputConfigBuildViaProgramConfigOutput(BaseModel):
    value: ProgramConfigInputConfig


FUNCTIONS = {
    "ProgramConfigInputConfig": {
        "add_attribute_config": {
            "canonical": {
                "name": "add_attribute_config",
                "description": "Attach one typed input signature attribute under this ProgramConfigInputConfig.",
                "is_constructor": False,
            },
            "input": ProgramConfigInputConfigAddAttributeConfigInput,
            "output": ProgramConfigInputConfigAddAttributeConfigOutput,
        },
        "build_via_program_config": {
            "canonical": {
                "name": "build_via_program_config",
                "description": "Create deterministic ProgramConfigInputConfig under one ProgramConfig.",
                "is_constructor": True,
            },
            "input": ProgramConfigInputConfigBuildViaProgramConfigInput,
            "output": ProgramConfigInputConfigBuildViaProgramConfigOutput,
        },
    },
}

__all__ = [
    "ProgramConfigInputConfig",
    "ProgramConfigInputConfigAddAttributeConfigInput",
    "ProgramConfigInputConfigAddAttributeConfigOutput",
    "ProgramConfigInputConfigBuildViaProgramConfigInput",
    "ProgramConfigInputConfigBuildViaProgramConfigOutput",
    "FUNCTIONS",
]
